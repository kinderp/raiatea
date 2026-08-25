#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class TransformationContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TransformationContractError(message)


def _require_only_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unexpected = sorted(set(value) - allowed)
    _require(not unexpected, f"{label}-unexpected-field:{unexpected[0] if unexpected else ''}")


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_artifact_ref(value: Any, label: str) -> None:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    for forbidden in (
        "lease_id", "expires_at",
        "path", "host_path", "filesystem_path",
        "rights", "rights_grant", "authorized",
    ):
        _require(forbidden not in value, f"{label}-forbidden-field:{forbidden}")
    _require_only_keys(
        value,
        {"artifact_id", "handle_id", "fingerprint", "media_type", "byte_length"},
        label,
    )
    for key in ("artifact_id", "handle_id", "fingerprint", "media_type"):
        _require(isinstance(value.get(key), str) and value.get(key), f"{label}-{key}-required")
    _require(isinstance(value.get("byte_length"), int) and value["byte_length"] >= 0, f"{label}-byte-length-invalid")
    _require(str(value["fingerprint"]).startswith("sha256:") and len(value["fingerprint"]) == 71, f"{label}-fingerprint-invalid")


def validate_transformation(record: dict[str, Any]) -> None:
    _require("rights" not in record and "rights_grant" not in record and "authorized" not in record, "transformation-record-must-not-own-rights-authority")
    _require_only_keys(
        record,
        {
            "schema_version", "record_kind", "transformation_id", "invocation_id", "operation",
            "input_artifact", "output_artifact", "parameters", "deterministic", "started_at",
            "ended_at", "rights_decision_ref",
        },
        "transformation-record",
    )
    _require(record.get("schema_version") == "0.1.0", "unsupported-schema-version")
    _require(record.get("record_kind") == "TransformationRecord", "transformation-record-kind-required")
    _require(isinstance(record.get("transformation_id"), str) and record["transformation_id"], "transformation-id-required")
    _require(isinstance(record.get("invocation_id"), str) and record["invocation_id"], "invocation-id-required")
    operation = record.get("operation")
    _require(isinstance(operation, dict), "operation-required")
    _require_only_keys(
        operation,
        {"plugin_id", "plugin_version", "capability_id", "profile_id", "operation_id", "operation_version"},
        "operation",
    )
    _require(operation.get("capability_id") == "transform.run", "operation-capability-must-be-transform-run")
    for key in ("plugin_id", "plugin_version", "profile_id", "operation_id", "operation_version"):
        _require(isinstance(operation.get(key), str) and operation[key], f"operation-{key}-required")
    _validate_artifact_ref(record.get("input_artifact"), "input-artifact")
    _validate_artifact_ref(record.get("output_artifact"), "output-artifact")
    input_artifact = record["input_artifact"]
    output_artifact = record["output_artifact"]
    _require(input_artifact["artifact_id"] != output_artifact["artifact_id"], "derived-artifact-identity-must-differ-from-input")
    _require(input_artifact["handle_id"] != output_artifact["handle_id"], "derived-artifact-handle-must-differ-from-input")
    _require(isinstance(record.get("parameters"), dict), "parameters-must-be-object")
    _require(record.get("deterministic") is True, "proof-transformation-must-be-deterministic")
    _require(isinstance(record.get("started_at"), str) and record["started_at"], "started-at-required")
    _require(isinstance(record.get("ended_at"), str) and record["ended_at"], "ended-at-required")
    if "rights_decision_ref" in record:
        _require(isinstance(record["rights_decision_ref"], str) and record["rights_decision_ref"], "rights-decision-ref-invalid")


def validate_derived_artifact(record: dict[str, Any]) -> None:
    _require_only_keys(record, {"schema_version", "record_kind", "artifact", "derivation"}, "derived-artifact-record")
    _require(record.get("schema_version") == "0.1.0", "unsupported-schema-version")
    _require(record.get("record_kind") == "DerivedArtifactRecord", "derived-artifact-record-kind-required")
    _validate_artifact_ref(record.get("artifact"), "derived-artifact")
    derivation = record.get("derivation")
    _require(isinstance(derivation, dict), "derivation-required")
    _require_only_keys(derivation, {"relationship", "source_artifact", "transformation_id"}, "derivation")
    _require(derivation.get("relationship") == "derived-from", "derived-from-relationship-required")
    _validate_artifact_ref(derivation.get("source_artifact"), "source-artifact")
    _require(isinstance(derivation.get("transformation_id"), str) and derivation["transformation_id"], "derivation-transformation-id-required")
    _require(record["artifact"]["artifact_id"] != derivation["source_artifact"]["artifact_id"], "derived-artifact-identity-must-differ-from-input")
    _require(record["artifact"]["handle_id"] != derivation["source_artifact"]["handle_id"], "derived-artifact-handle-must-differ-from-input")


def validate_pair(transformation: dict[str, Any], derived: dict[str, Any]) -> None:
    validate_transformation(transformation)
    validate_derived_artifact(derived)
    _require(derived["derivation"]["transformation_id"] == transformation["transformation_id"], "lineage-transformation-id-mismatch")
    _require(derived["derivation"]["source_artifact"] == transformation["input_artifact"], "lineage-source-artifact-mismatch")
    _require(derived["artifact"] == transformation["output_artifact"], "lineage-output-artifact-mismatch")


def validate_bytes(artifact_ref: dict[str, Any], payload: bytes, label: str) -> None:
    _validate_artifact_ref(artifact_ref, label)
    _require(artifact_ref["byte_length"] == len(payload), f"{label}-byte-length-mismatch")
    _require(artifact_ref["fingerprint"] == sha256_bytes(payload), f"{label}-fingerprint-mismatch")


def validate_any(record: dict[str, Any]) -> str:
    kind = record.get("record_kind")
    if kind == "TransformationRecord":
        validate_transformation(record)
        return "transformation"
    if kind == "DerivedArtifactRecord":
        validate_derived_artifact(record)
        return "derived-artifact"
    raise TransformationContractError("unknown-transformation-record-kind")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.records:
        value = json.loads(path.read_text(encoding="utf-8"))
        print("PASS", validate_any(value), path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
