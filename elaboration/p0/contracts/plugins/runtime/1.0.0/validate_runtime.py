#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class RuntimeContractError(ValueError):
    pass


ALLOWED_TRANSITIONS = {
    "starting": {"ready", "incompatible", "failed", "quarantined", "stopping"},
    "ready": {"stopping", "failed", "quarantined"},
    "stopping": {"stopped", "failed", "quarantined"},
    "stopped": set(),
    "failed": set(),
    "incompatible": set(),
    "quarantined": set(),
}

FORBIDDEN_PARAMETER_KEYS = {
    "path", "filepath", "file_path", "filename", "content", "bytes", "data",
    "blob", "base64", "secret", "password", "token", "credential", "api_key",
}
MAX_PARAMETERS_JSON_BYTES = 64 * 1024


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeContractError(message)


def canonical_manifest_fingerprint(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def manifest_profiles(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for capability in manifest.get("capabilities", []):
        if not isinstance(capability, dict):
            continue
        capability_id = capability.get("capability_id")
        for profile in capability.get("profiles", []):
            if isinstance(capability_id, str) and isinstance(profile, dict) and isinstance(profile.get("profile_id"), str):
                result.add((capability_id, profile["profile_id"]))
    return result


def validate_handshake(handshake: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require(handshake.get("record_type") == "handshake", "handshake-record-type-required")
    identity = handshake.get("identity")
    _require(isinstance(identity, dict), "handshake-identity-required")
    plugin = manifest.get("plugin")
    _require(isinstance(plugin, dict), "validated-manifest-plugin-required")
    _require(identity.get("plugin_id") == plugin.get("plugin_id"), "handshake-plugin-id-mismatch")
    _require(identity.get("plugin_version") == plugin.get("version"), "handshake-plugin-version-mismatch")
    _require(identity.get("manifest_fingerprint") == canonical_manifest_fingerprint(manifest), "handshake-manifest-fingerprint-mismatch")
    _require(identity.get("runtime_contract_version") == "1.0.0", "runtime-contract-incompatible")

    declared = manifest_profiles(manifest)
    advertised: set[tuple[str, str]] = set()
    for row in handshake.get("advertised_profiles", []):
        _require(isinstance(row, dict), "handshake-profile-must-be-object")
        key = (row.get("capability_id"), row.get("profile_id"))
        _require(all(isinstance(part, str) and part for part in key), "handshake-profile-invalid")
        _require(key not in advertised, "handshake-duplicate-profile")
        advertised.add(key)  # type: ignore[arg-type]
    _require(advertised <= declared, "runtime-broadens-manifest-capabilities")


def validate_transition(record: dict[str, Any]) -> None:
    _require(record.get("record_type") == "lifecycle-transition", "lifecycle-record-type-required")
    source = record.get("from")
    target = record.get("to")
    _require(source in ALLOWED_TRANSITIONS, "unknown-lifecycle-source")
    _require(target in ALLOWED_TRANSITIONS[source], f"illegal-lifecycle-transition:{source}->{target}")


def _scan_parameters(value: Any, key: str | None = None) -> None:
    if key is not None:
        normalized = key.strip().lower().replace("-", "_")
        _require(normalized not in FORBIDDEN_PARAMETER_KEYS, f"control-plane-parameter-key-forbidden:{key}")
    if isinstance(value, dict):
        for child_key, child in value.items():
            _require(isinstance(child_key, str), "parameter-key-must-be-string")
            _scan_parameters(child, child_key)
    elif isinstance(value, list):
        for child in value:
            _scan_parameters(child)
    elif isinstance(value, str):
        _require(len(value.encode("utf-8")) <= 8192, "control-plane-parameter-string-too-large")
    else:
        _require(value is None or isinstance(value, (bool, int, float)), "unsupported-parameter-value")


def validate_invocation(request: dict[str, Any], manifest: dict[str, Any], handshake: dict[str, Any]) -> None:
    _require(request.get("record_type") == "invocation-request", "invocation-record-type-required")
    identity = handshake.get("identity", {})
    _require(request.get("runtime_instance_id") == identity.get("runtime_instance_id"), "invocation-runtime-instance-mismatch")
    capability = request.get("capability")
    _require(isinstance(capability, dict), "invocation-capability-required")
    key = (capability.get("capability_id"), capability.get("profile_id"))
    _require(key in manifest_profiles(manifest), "invocation-profile-not-in-manifest")
    advertised = {(row.get("capability_id"), row.get("profile_id")) for row in handshake.get("advertised_profiles", []) if isinstance(row, dict)}
    _require(key in advertised, "invocation-profile-not-advertised-by-runtime")

    parameters = request.get("parameters")
    _require(isinstance(parameters, dict), "invocation-parameters-must-be-object")
    encoded = json.dumps(parameters, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    _require(len(encoded) <= MAX_PARAMETERS_JSON_BYTES, "control-plane-parameters-too-large")
    _scan_parameters(parameters)

    for item in request.get("inputs", []):
        _require(isinstance(item, dict), "invocation-input-must-be-object")
        _require(item.get("kind") in {"asset-handle", "record-ref"}, "inline-or-unknown-input-forbidden")
        _require("path" not in item and "content" not in item and "data" not in item, "inline-path-or-content-forbidden")

    runtime_context = request.get("runtime_context")
    _require(isinstance(runtime_context, dict), "runtime-context-required")
    _require("rights_grant" not in runtime_context and "authorized" not in runtime_context, "runtime-cannot-claim-rights-grant")
    for lease in runtime_context.get("secret_leases", []):
        _require(isinstance(lease, dict), "secret-lease-ref-invalid")
        _require(set(lease) <= {"secret_name", "lease_id"}, "secret-lease-must-not-contain-value")


def validate_result(result: dict[str, Any], request: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require(result.get("record_type") == "invocation-result", "result-record-type-required")
    _require(result.get("invocation_id") == request.get("invocation_id"), "result-invocation-id-mismatch")
    _require(result.get("runtime_instance_id") == request.get("runtime_instance_id"), "result-runtime-instance-mismatch")
    status = result.get("status")
    error = result.get("error")
    if status == "completed":
        _require(error is None, "completed-result-must-not-have-error")
    else:
        _require(isinstance(error, dict), "noncompleted-result-requires-error")
    if status == "cancelled":
        _require(error.get("code") == "cancelled", "cancelled-status-requires-cancelled-error")
    if status == "timeout":
        _require(error.get("code") == "timeout", "timeout-status-requires-timeout-error")

    provenance = result.get("provenance")
    _require(isinstance(provenance, dict), "result-provenance-required")
    plugin = manifest.get("plugin", {})
    _require(provenance.get("plugin_id") == plugin.get("plugin_id"), "provenance-plugin-id-mismatch")
    _require(provenance.get("plugin_version") == plugin.get("version"), "provenance-plugin-version-mismatch")
    _require(provenance.get("runtime_instance_id") == request.get("runtime_instance_id"), "provenance-runtime-instance-mismatch")
    _require(provenance.get("invocation_id") == request.get("invocation_id"), "provenance-invocation-id-mismatch")
    _require(provenance.get("capability") == request.get("capability"), "provenance-capability-mismatch")

    output_ids: list[str] = []
    for output in result.get("outputs", []):
        _require(isinstance(output, dict), "output-must-be-object")
        if output.get("kind") == "asset-handle":
            handle = output.get("handle")
            _require(isinstance(handle, dict), "output-handle-required")
            _require(handle.get("access") == "write-once-output", "output-asset-handle-must-be-write-once")
            output_ids.append(str(handle.get("handle_id")))
        elif output.get("kind") == "record-ref":
            ref = output.get("record_ref")
            _require(isinstance(ref, dict), "output-record-ref-required")
            output_ids.append(str(ref.get("ref_id")))
        else:
            raise RuntimeContractError("inline-or-unknown-output-forbidden")
    _require(provenance.get("output_refs") == output_ids, "provenance-output-refs-mismatch")

    capability = request.get("capability", {})
    if str(capability.get("capability_id", "")).startswith("extract."):
        for output in result.get("outputs", []):
            if output.get("kind") == "record-ref":
                ref = output.get("record_ref", {})
                _require(
                    ref.get("contract_id") == "raiatea.extraction.processing-run",
                    "extractor-record-output-must-reference-e05",
                )


def validate_diagnostic_no_secret_values(diagnostic: dict[str, Any], secret_values: set[str]) -> None:
    message = diagnostic.get("message")
    _require(isinstance(message, str), "diagnostic-message-required")
    for secret in secret_values:
        if secret:
            _require(secret not in message, "diagnostic-contains-secret-value")
