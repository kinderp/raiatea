#!/usr/bin/env python3
"""Official VS1c LocalSourcePlugin.

The plugin never scans the user's filesystem. It receives one Core-built,
path-free DiscoverySnapshot through an opaque handle and returns a deterministic
SourceReferenceBundle through a Core-issued write-once output target.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from prototype.p0_vs1.plugin_io import PluginIOError, plugin_read_handle, plugin_write_output
from prototype.p0_vs1.source_contract import (
    SourceContractError,
    build_source_reference_bundle,
    canonical_json_bytes,
    validate_discovery_snapshot,
)


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
MANIFEST_PATH = HERE / "manifest.json"
TRANSPORT_ROOT = REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "transport" / "0.1.0"
RUNTIME_VALIDATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "runtime" / "1.0.0" / "validate_runtime.py"
if str(TRANSPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(TRANSPORT_ROOT))

from transport import (  # noqa: E402
    MAX_FRAME_BYTES,
    TransportError,
    decode_frame,
    encode_frame,
    error_message,
    notification_message,
    result_message,
)

_RUNTIME_SPEC = importlib.util.spec_from_file_location("vs1c_local_source_runtime", RUNTIME_VALIDATOR_PATH)
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
assert _RUNTIME_SPEC.loader is not None
_RUNTIME_SPEC.loader.exec_module(RUNTIME)


SNAPSHOT_MEDIA_TYPE = "application/vnd.raiatea.vs1c-discovery-snapshot+json"
BUNDLE_MEDIA_TYPE = "application/vnd.raiatea.vs1c-source-reference-bundle+json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _handshake(manifest: dict[str, Any], runtime_instance_id: str) -> dict[str, Any]:
    return {
        "record_type": "handshake",
        "identity": {
            "plugin_id": manifest["plugin"]["plugin_id"],
            "plugin_version": manifest["plugin"]["version"],
            "runtime_instance_id": runtime_instance_id,
            "manifest_fingerprint": RUNTIME.canonical_manifest_fingerprint(manifest),
            "runtime_contract_version": "1.0.0",
        },
        "advertised_profiles": [
            {"capability_id": "source.discover", "profile_id": "local-catalog-read-only"}
        ],
        "observed_at": _now(),
    }


def _input_refs(request: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in request.get("inputs", []):
        if isinstance(item, dict) and item.get("kind") == "asset-handle" and isinstance(item.get("handle"), dict):
            handle_id = item["handle"].get("handle_id")
            if isinstance(handle_id, str):
                refs.append(handle_id)
        elif isinstance(item, dict) and item.get("kind") == "record-ref" and isinstance(item.get("record_ref"), dict):
            ref_id = item["record_ref"].get("ref_id")
            if isinstance(ref_id, str):
                refs.append(ref_id)
    return refs


def _provenance(
    manifest: dict[str, Any],
    runtime_instance_id: str,
    request: dict[str, Any],
    output_refs: list[str],
    started_at: str,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "plugin_id": manifest["plugin"]["plugin_id"],
        "plugin_version": manifest["plugin"]["version"],
        "runtime_instance_id": runtime_instance_id,
        "invocation_id": request["invocation_id"],
        "capability": request["capability"],
        "started_at": started_at,
        "ended_at": _now(),
        "input_refs": _input_refs(request),
        "output_refs": output_refs,
    }
    rights_ref = request.get("runtime_context", {}).get("rights_decision_ref")
    if isinstance(rights_ref, str) and rights_ref:
        value["rights_decision_ref"] = rights_ref
    return value


def _diagnostic(runtime_instance_id: str, invocation_id: str, count: int) -> dict[str, Any]:
    return {
        "record_type": "diagnostic",
        "diagnostic_id": f"diag:{runtime_instance_id}:{invocation_id}:source-discovered",
        "runtime_instance_id": runtime_instance_id,
        "invocation_id": invocation_id,
        "severity": "info",
        "code": "source-reference-bundle-created",
        "message": f"created {count} path-free local catalog source references",
        "observed_at": _now(),
    }


def _failed(
    manifest: dict[str, Any],
    runtime_instance_id: str,
    request: dict[str, Any],
    *,
    started_at: str,
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "record_type": "invocation-result",
        "invocation_id": request.get("invocation_id"),
        "runtime_instance_id": runtime_instance_id,
        "status": "failed",
        "outputs": [],
        "diagnostic_refs": [],
        "error": {"code": code, "message": message, "retryable": False},
        "provenance": _provenance(manifest, runtime_instance_id, request, [], started_at),
    }


def _invoke(
    manifest: dict[str, Any],
    runtime_instance_id: str,
    request: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started_at = _now()
    if request.get("capability") != {
        "capability_id": "source.discover",
        "profile_id": "local-catalog-read-only",
    }:
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="unsupported-source-profile",
                message="LocalSourcePlugin supports only source.discover/local-catalog-read-only",
            ),
            [],
        )

    rights_ref = request.get("runtime_context", {}).get("rights_decision_ref")
    if not isinstance(rights_ref, str) or not rights_ref.startswith("rights-decision:"):
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="rights-decision-required",
                message="Core rights_decision_ref is required",
            ),
            [],
        )

    inputs = request.get("inputs")
    targets = request.get("output_targets")
    if not isinstance(inputs, list) or len(inputs) != 1 or not isinstance(inputs[0], dict):
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="invalid-discovery-input",
                message="exactly one DiscoverySnapshot input handle is required",
            ),
            [],
        )
    if inputs[0].get("kind") != "asset-handle" or not isinstance(inputs[0].get("handle"), dict):
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="invalid-discovery-input",
                message="DiscoverySnapshot must use an asset handle",
            ),
            [],
        )
    input_handle = inputs[0]["handle"]
    if input_handle.get("media_type") != SNAPSHOT_MEDIA_TYPE:
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="invalid-discovery-input",
                message="DiscoverySnapshot media type is required",
            ),
            [],
        )
    if not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict):
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="invalid-source-output-target",
                message="exactly one SourceReferenceBundle output target is required",
            ),
            [],
        )
    output_target = targets[0]
    if output_target.get("media_type") != BUNDLE_MEDIA_TYPE:
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="invalid-source-output-target",
                message="SourceReferenceBundle media type is required",
            ),
            [],
        )

    try:
        snapshot_bytes = plugin_read_handle(input_handle)
        snapshot = json.loads(snapshot_bytes.decode("utf-8"))
        validate_discovery_snapshot(snapshot)
        bundle = build_source_reference_bundle(snapshot)
        payload = canonical_json_bytes(bundle)
        completed = plugin_write_output(output_target, payload)
    except (PluginIOError, SourceContractError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="source-discovery-contract-failure",
                message=type(exc).__name__,
            ),
            [],
        )

    refs = bundle["record_refs"]
    outputs: list[dict[str, Any]] = [{"kind": "asset-handle", "handle": completed}]
    outputs.extend({"kind": "record-ref", "record_ref": ref} for ref in refs)
    output_refs = [completed["handle_id"]] + [ref["ref_id"] for ref in refs]
    diagnostic = _diagnostic(runtime_instance_id, request["invocation_id"], len(refs))
    result = {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": runtime_instance_id,
        "status": "completed",
        "outputs": outputs,
        "diagnostic_refs": [diagnostic["diagnostic_id"]],
        "provenance": _provenance(
            manifest,
            runtime_instance_id,
            request,
            output_refs,
            started_at,
        ),
    }
    return result, [diagnostic]


def _write(message: dict[str, Any]) -> None:
    sys.stdout.buffer.write(encode_frame(message))
    sys.stdout.buffer.flush()


def main() -> int:
    manifest = _manifest()
    runtime_instance_id = f"runtime:vs1c:local-source:{os.getpid()}"
    handshake = _handshake(manifest, runtime_instance_id)
    handshaken = False

    while True:
        raw = sys.stdin.buffer.readline(MAX_FRAME_BYTES + 1)
        if raw == b"":
            return 0
        try:
            message = decode_frame(raw)
        except TransportError:
            _write(error_message(None, -32700, "Parse error"))
            continue
        if "method" not in message or "id" not in message:
            _write(error_message(message.get("id"), -32600, "Invalid Request"))
            continue
        request_id = message["id"]
        method = message["method"]
        params = message.get("params", {})

        if method == "raiatea.handshake":
            if params != {}:
                _write(error_message(request_id, -32602, "Handshake params must be empty"))
                continue
            _write(result_message(request_id, handshake))
            handshaken = True
            continue

        if not handshaken:
            _write(error_message(request_id, -32001, "Handshake required"))
            continue
        if method != "raiatea.invoke":
            _write(error_message(request_id, -32601, "Method not found"))
            continue
        if not isinstance(params, dict):
            _write(error_message(request_id, -32602, "Invalid invocation params"))
            continue
        try:
            RUNTIME.validate_invocation(params, manifest, handshake)
        except Exception as exc:
            _write(error_message(request_id, -32602, f"Invalid Runtime v1 invocation: {exc}"))
            continue

        result, diagnostics = _invoke(manifest, runtime_instance_id, params)
        for row in diagnostics:
            _write(notification_message("raiatea.diagnostic", row))
        _write(result_message(request_id, result))


if __name__ == "__main__":
    raise SystemExit(main())
