#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from typing import Any

from elaboration.p0.plugins.proofs.v1d import proof_broker as BROKER
from elaboration.p0.plugins.proofs.v1d import proof_protocol as P

MANIFEST_PATH = P.REPO_ROOT / "elaboration" / "p0" / "plugins" / "proofs" / "v1e" / "manifest.json"
TRANSFORM_VALIDATOR_PATH = P.REPO_ROOT / "elaboration" / "p0" / "contracts" / "transformations" / "0.1.0" / "validate_transformation.py"

_SPEC = importlib.util.spec_from_file_location("v1e_transform_validator", TRANSFORM_VALIDATOR_PATH)
T = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(T)

CONTRACT_ID = "raiatea.transformation.record"
CONTRACT_VERSION = "0.1.0"
MEDIA_TYPE = "text/plain; charset=utf-8"


def _record_ref(ref_id: str, record_kind: str) -> dict[str, Any]:
    return {
        "ref_id": ref_id,
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "record_kind": record_kind,
    }


def _normalize_newlines(payload: bytes) -> bytes:
    text = payload.decode("utf-8", errors="strict")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _artifact_ref(artifact_id: str, handle: dict[str, Any], payload: bytes) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "handle_id": str(handle["handle_id"]),
        "fingerprint": T.sha256_bytes(payload),
        "media_type": MEDIA_TYPE,
        "byte_length": len(payload),
    }


def invoke(manifest: dict[str, Any], request: dict[str, Any], runtime_instance_id: str):
    started = P.now()
    capability = request.get("capability", {})
    if capability != {"capability_id": "transform.run", "profile_id": "normalize-newlines-v1"}:
        return P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "unknown-capability-profile",
            "v1e proof supports only transform.run/normalize-newlines-v1",
            started_at=started,
        ), []

    inputs = request.get("inputs", [])
    if not isinstance(inputs, list) or len(inputs) != 1 or not isinstance(inputs[0], dict):
        return P.failed_result(
            manifest, runtime_instance_id, request, "invalid-input-handle",
            "newline proof requires exactly one AssetHandle input", started_at=started,
        ), []
    handle = inputs[0].get("handle") if inputs[0].get("kind") == "asset-handle" else None
    if not isinstance(handle, dict) or handle.get("media_type") != MEDIA_TYPE:
        return P.failed_result(
            manifest, runtime_instance_id, request, "invalid-input-handle",
            f"newline proof requires media_type {MEDIA_TYPE}", started_at=started,
        ), []

    parameters = request.get("parameters", {})
    input_artifact_id = parameters.get("input_artifact_id") if isinstance(parameters, dict) else None
    output_artifact_id = parameters.get("output_artifact_id") if isinstance(parameters, dict) else None
    if not isinstance(input_artifact_id, str) or not input_artifact_id or not isinstance(output_artifact_id, str) or not output_artifact_id:
        return P.failed_result(
            manifest, runtime_instance_id, request, "output-contract-violation",
            "Core must provide input_artifact_id and output_artifact_id", started_at=started,
        ), []
    if input_artifact_id == output_artifact_id:
        return P.failed_result(
            manifest, runtime_instance_id, request, "output-contract-violation",
            "derived artifact identity must differ from input", started_at=started,
        ), []

    targets = request.get("output_targets", [])
    if not isinstance(targets, list) or len(targets) != 2:
        return P.failed_result(
            manifest, runtime_instance_id, request, "output-contract-violation",
            "newline proof requires Core-issued data and record-bundle output targets", started_at=started,
        ), []

    try:
        input_path = BROKER.resolve_read_handle(handle)
        input_bytes = input_path.read_bytes()
    except (BROKER.ProofBrokerError, OSError) as exc:
        return P.failed_result(
            manifest, runtime_instance_id, request, "invalid-input-handle", str(exc), started_at=started,
        ), []

    if "byte_length" in handle and handle.get("byte_length") != len(input_bytes):
        return P.failed_result(
            manifest, runtime_instance_id, request, "invalid-input-handle",
            "input byte_length does not match resolved bytes", started_at=started,
        ), []
    if "fingerprint" in handle and handle.get("fingerprint") != T.sha256_bytes(input_bytes):
        return P.failed_result(
            manifest, runtime_instance_id, request, "invalid-input-handle",
            "input fingerprint does not match resolved bytes", started_at=started,
        ), []

    try:
        output_bytes = _normalize_newlines(input_bytes)
    except UnicodeDecodeError:
        return P.failed_result(
            manifest, runtime_instance_id, request, "provider-tool-failure",
            "input is not valid UTF-8", started_at=started,
        ), []

    try:
        data_handle = BROKER.write_output_target(targets[0], output_bytes)
    except BROKER.ProofBrokerError as exc:
        return P.failed_result(
            manifest, runtime_instance_id, request, "output-contract-violation", str(exc), started_at=started,
        ), []

    input_ref = _artifact_ref(input_artifact_id, handle, input_bytes)
    output_ref = _artifact_ref(output_artifact_id, data_handle, output_bytes)
    transformation_id = f"transform:{request['invocation_id']}"
    transformation = {
        "schema_version": "0.1.0",
        "record_kind": "TransformationRecord",
        "transformation_id": transformation_id,
        "invocation_id": request["invocation_id"],
        "operation": {
            "plugin_id": manifest["plugin"]["plugin_id"],
            "plugin_version": manifest["plugin"]["version"],
            "capability_id": "transform.run",
            "profile_id": "normalize-newlines-v1",
            "operation_id": "normalize-newlines",
            "operation_version": "1",
        },
        "input_artifact": input_ref,
        "output_artifact": output_ref,
        "parameters": {},
        "deterministic": True,
        "started_at": started,
        "ended_at": P.now(),
    }
    rights = request.get("runtime_context", {}).get("rights_decision_ref")
    if isinstance(rights, str) and rights:
        transformation["rights_decision_ref"] = rights
    derived = {
        "schema_version": "0.1.0",
        "record_kind": "DerivedArtifactRecord",
        "artifact": output_ref,
        "derivation": {
            "relationship": "derived-from",
            "source_artifact": input_ref,
            "transformation_id": transformation_id,
        },
    }
    T.validate_pair(transformation, derived)
    T.validate_bytes(input_ref, input_bytes, "input")
    T.validate_bytes(output_ref, output_bytes, "output")

    transformation_ref = _record_ref(transformation_id, "TransformationRecord")
    derived_ref = _record_ref(output_artifact_id, "DerivedArtifactRecord")
    bundle = {
        "proof_contract": "raiatea.v1e.transformation-record-bundle",
        "version": "0.1.0",
        "proof_only": True,
        "record_refs": [transformation_ref, derived_ref],
        "records": {
            transformation_ref["ref_id"]: transformation,
            derived_ref["ref_id"]: derived,
        },
    }
    bundle_bytes = (json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    try:
        bundle_handle = BROKER.write_output_target(targets[1], bundle_bytes)
    except BROKER.ProofBrokerError as exc:
        return P.failed_result(
            manifest, runtime_instance_id, request, "output-contract-violation", str(exc), started_at=started,
        ), []

    outputs: list[dict[str, Any]] = [
        {"kind": "asset-handle", "handle": data_handle},
        {"kind": "asset-handle", "handle": bundle_handle},
        {"kind": "record-ref", "record_ref": transformation_ref},
        {"kind": "record-ref", "record_ref": derived_ref},
    ]
    output_refs = [data_handle["handle_id"], bundle_handle["handle_id"], transformation_ref["ref_id"], derived_ref["ref_id"]]
    diag = P.diagnostic(
        runtime_instance_id,
        request["invocation_id"],
        "newline-transform-proof-completed",
        f"normalized {len(input_bytes)} input bytes into {len(output_bytes)} derived bytes",
    )
    result = {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": runtime_instance_id,
        "status": "completed",
        "outputs": outputs,
        "diagnostic_refs": [diag["diagnostic_id"]],
        "provenance": P.provenance(manifest, runtime_instance_id, request, output_refs, started),
    }
    return result, [diag]


def main() -> int:
    return P.run_process(MANIFEST_PATH, "runtime:v1e:transformer", invoke)


if __name__ == "__main__":
    raise SystemExit(main())
