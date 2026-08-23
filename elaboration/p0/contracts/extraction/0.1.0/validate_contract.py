#!/usr/bin/env python3
"""Dependency-light semantic conformance checks for the E-05b candidate contract.

This does not replace JSON Schema validation. It enforces cross-field invariants
that JSON Schema alone should not be forced to encode prematurely.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    pass


EVIDENCE_STATES = {
    "measured",
    "partial",
    "not-measured",
    "malformed-evidence",
    "ambiguous",
    "not-applicable",
}
VALUE_STATES = {"present", "explicit-empty", "explicit-mismatch", "unknown"}
EXECUTION_STATES = {
    "not-started",
    "completed",
    "failed",
    "restricted",
    "rejected",
    "unsupported",
    "cancelled",
    "timeout",
    "unknown",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _validate_schema_version(record: dict[str, Any]) -> None:
    _require(record.get("schema_version") == "0.1.0", "unsupported-schema-version")


def _validate_provider_route(provider: Any, route: Any, label: str = "record") -> None:
    _require(isinstance(provider, dict) and provider.get("provider_id"), f"{label}-provider-ref-required")
    _require(isinstance(route, dict) and route.get("route_profile_id"), f"{label}-route-profile-ref-required")
    _require("route_profile_id" not in provider, f"{label}-provider-and-route-profile-must-remain-distinct")
    _require("provider_id" not in route, f"{label}-route-profile-must-not-duplicate-provider-identity")


def _validate_evidence(value: Any, label: str) -> None:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    evidence_state = value.get("evidence_state")
    value_state = value.get("value_state")
    _require(evidence_state in EVIDENCE_STATES, f"{label}-bad-evidence-state")
    _require(value_state in VALUE_STATES, f"{label}-bad-value-state")
    _require(bool(value.get("basis")), f"{label}-basis-required")
    if value_state in {"present", "explicit-empty"}:
        _require("value" in value, f"{label}-value-required-for-{value_state}")
    if evidence_state == "not-measured":
        _require(value_state == "unknown", f"{label}-not-measured-must-have-unknown-value")


def _validate_coordinate(value: Any, label: str) -> None:
    _validate_evidence(value, label)
    value_state = value.get("value_state")
    if value_state == "explicit-empty":
        _require(value.get("value") is None, f"{label}-explicit-empty-must-use-null")
        return
    if value_state != "present":
        return
    coordinate = value.get("value")
    _require(isinstance(coordinate, dict), f"{label}-present-coordinate-must-be-object")
    kind = coordinate.get("kind")
    if kind == "pdf-geometric":
        _require(isinstance(coordinate.get("page_index"), int), f"{label}-pdf-page-index-required")
        bbox = coordinate.get("bbox_points_bottom_left")
        _require(isinstance(bbox, list) and len(bbox) == 4, f"{label}-pdf-bbox-required")
        _require("resource" not in coordinate and "fragment" not in coordinate, f"{label}-pdf-must-not-use-epub-fields")
    elif kind == "epub-logical":
        _require(bool(coordinate.get("resource")), f"{label}-epub-resource-required")
        _require("page_index" not in coordinate and "bbox_points_bottom_left" not in coordinate, f"{label}-epub-must-not-use-pdf-fields")
    else:
        raise ContractError(f"{label}-unknown-coordinate-kind")


def _validate_outcome(value: Any, label: str) -> None:
    _require(isinstance(value, dict), f"{label}-required")
    _require("success" not in value, f"{label}-must-not-be-boolean")
    _require("produced" not in value, f"{label}-must-not-own-produced-refs")
    _require("rights" not in value and "policy" not in value, f"{label}-must-not-own-policy")
    _require(value.get("execution") in EXECUTION_STATES, f"{label}-bad-execution-state")
    _require(bool(value.get("derivation_basis")), f"{label}-derivation-basis-required")
    assessments = value.get("assessments")
    _require(isinstance(assessments, list) and assessments, f"{label}-scoped-assessments-required")
    for index, assessment in enumerate(assessments):
        _require(isinstance(assessment, dict), f"{label}-assessment-{index}-must-be-object")
        _require(bool(assessment.get("scope")), f"{label}-assessment-{index}-scope-required")
        _require(bool(assessment.get("basis")), f"{label}-assessment-{index}-basis-required")
        _require("completeness" in assessment and "integrity" in assessment, f"{label}-assessment-{index}-states-required")


def _ref_key(value: Any, label: str) -> tuple[str, str, str | None]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    kind = value.get("kind")
    if kind == "provider-evidence":
        evidence_id = value.get("evidence_id")
        channel = value.get("channel")
        _require(isinstance(evidence_id, str) and evidence_id, f"{label}-evidence-id-required")
        _require(isinstance(channel, str) and channel, f"{label}-channel-required")
        return (kind, evidence_id, channel)
    if kind == "normalized-representation":
        representation_id = value.get("representation_id")
        _require(isinstance(representation_id, str) and representation_id, f"{label}-representation-id-required")
        return (kind, representation_id, None)
    raise ContractError(f"{label}-unknown-kind")


def _validate_stage_executor(stage: dict[str, Any], index: int) -> str:
    executor = stage.get("executor")
    _require(isinstance(executor, dict), f"stage-{index}-executor-required")
    kind = executor.get("kind")
    if kind == "provider":
        _validate_provider_route(executor.get("provider"), executor.get("route_profile"), f"stage-{index}")
        _require("provider_status" in stage, f"stage-{index}-provider-status-required")
        _validate_evidence(stage.get("provider_status"), f"stage-{index}-provider-status")
        _require(stage.get("stage_kind") not in {"normalization", "alignment"}, f"stage-{index}-provider-cannot-own-core-normalization")
        return kind
    if kind == "raiatea-core":
        _require(bool(executor.get("operation_id")), f"stage-{index}-core-operation-id-required")
        _require("provider" not in executor and "route_profile" not in executor, f"stage-{index}-core-executor-must-not-own-provider")
        _require("provider_status" not in stage, f"stage-{index}-core-stage-must-not-have-provider-status")
        return kind
    raise ContractError(f"stage-{index}-unknown-executor-kind")


def validate(record: dict[str, Any]) -> None:
    """Validate a ProcessingRunRecord and its orchestration/lineage invariants."""
    _validate_schema_version(record)
    _require("success" not in record, "boolean-success-is-forbidden")
    _require("provider" not in record and "route_profile" not in record, "run-must-not-own-provider-route-identity")
    _validate_outcome(record.get("outcome"), "processing-outcome")

    stages = record.get("stages")
    _require(isinstance(stages, list), "processing-stages-required")
    stage_ids: set[str] = set()
    produced_by_stage: dict[tuple[str, str, str | None], tuple[int, str, str]] = {}
    available_before_stage: set[tuple[str, str, str | None]] = set()

    for index, stage in enumerate(stages):
        _require(isinstance(stage, dict), f"stage-{index}-must-be-object")
        stage_id = stage.get("stage_id")
        stage_kind = stage.get("stage_kind")
        _require(isinstance(stage_id, str) and stage_id, f"stage-{index}-id-required")
        _require(stage_id not in stage_ids, "stage-id-must-be-unique")
        _require(isinstance(stage_kind, str) and stage_kind, f"stage-{index}-kind-required")

        parent = stage.get("parent_stage_id")
        if parent is not None:
            _require(parent in stage_ids, f"stage-{index}-parent-stage-must-precede")

        executor_kind = _validate_stage_executor(stage, index)
        _validate_outcome(stage.get("outcome"), f"stage-{index}-outcome")

        if stage_kind == "ocr-fallback":
            _require(executor_kind == "provider", f"stage-{index}-ocr-fallback-must-be-provider-backed")
            _require(bool(stage.get("trigger_basis")), "ocr-fallback-trigger-basis-required")
            _require(parent in stage_ids, "ocr-fallback-parent-stage-must-precede")
            _require(
                stage.get("reconciliation_state") in {"resolved", "partial", "unresolved", "not-measured"},
                "ocr-reconciliation-state-required",
            )

        inputs = stage.get("input_refs")
        _require(isinstance(inputs, list), f"stage-{index}-input-refs-required")
        input_keys: list[tuple[str, str, str | None]] = []
        for input_index, item in enumerate(inputs):
            key = _ref_key(item, f"stage-{index}-input-{input_index}")
            _require(key in available_before_stage, f"stage-{index}-input-must-reference-prior-produced-output")
            input_keys.append(key)

        outputs = stage.get("produced")
        _require(isinstance(outputs, list), f"stage-{index}-produced-required")
        stage_output_keys: list[tuple[str, str, str | None]] = []
        for output_index, item in enumerate(outputs):
            key = _ref_key(item, f"stage-{index}-output-{output_index}")
            _require(key not in produced_by_stage, "produced-ref-must-have-single-stage-producer")
            if key[0] == "normalized-representation":
                _require(stage_kind in {"normalization", "alignment"}, f"stage-{index}-normalized-output-requires-normalization-or-alignment")
                _require(executor_kind == "raiatea-core", f"stage-{index}-normalized-output-requires-core-executor")
                _require(bool(input_keys), f"stage-{index}-normalized-output-requires-input-lineage")
            produced_by_stage[key] = (index, stage_id, stage_kind)
            stage_output_keys.append(key)

        stage_ids.add(stage_id)
        available_before_stage.update(stage_output_keys)

    root_produced = record.get("produced")
    _require(isinstance(root_produced, list), "run-produced-required")
    root_keys: set[tuple[str, str, str | None]] = set()
    for index, item in enumerate(root_produced):
        key = _ref_key(item, f"run-produced-{index}")
        _require(key not in root_keys, "run-produced-ref-must-be-unique")
        _require(key in produced_by_stage, "run-produced-ref-must-have-stage-producer")
        root_keys.add(key)
    if not stages:
        _require(not root_produced, "run-without-stages-cannot-have-produced-refs")

    provenance = record.get("provenance")
    _require(isinstance(provenance, dict), "provenance-required")
    _require(bool(provenance.get("run_outcome_basis")), "provenance-run-outcome-basis-required")


def validate_provider_evidence(record: dict[str, Any]) -> None:
    _validate_schema_version(record)
    _require(bool(record.get("evidence_id")), "provider-evidence-id-required")
    _validate_provider_route(record.get("provider"), record.get("route_profile"), "provider-evidence")
    _require(bool(record.get("channel")), "provider-evidence-channel-required")
    _validate_evidence(record.get("native_status"), "provider-evidence-native-status")
    _require("rights" not in record and "policy" not in record, "provider-evidence-must-not-own-policy")
    for index, group in enumerate(record.get("groupings", [])):
        _require(isinstance(group, dict), f"provider-group-{index}-must-be-object")
        _require(group.get("semantic_interpretation") is False, f"provider-group-{index}-must-remain-nonsemantic")
        _require(bool(group.get("provider_ref")), f"provider-group-{index}-provider-ref-required")
        _require(bool(group.get("basis")), f"provider-group-{index}-basis-required")


def validate_representation(record: dict[str, Any]) -> None:
    _validate_schema_version(record)
    _require(bool(record.get("representation_id")), "representation-id-required")
    _require("provider" not in record and "route_profile" not in record, "normalized-representation-must-not-own-provider-identity")
    _require("rights" not in record and "policy" not in record, "normalized-representation-must-not-own-policy")
    units = record.get("units")
    _require(isinstance(units, list), "normalized-units-required")
    unit_ids: set[str] = set()
    for index, unit in enumerate(units):
        _require(isinstance(unit, dict), f"unit-{index}-must-be-object")
        unit_id = unit.get("unit_id")
        _require(isinstance(unit_id, str) and unit_id, f"unit-{index}-id-required")
        _require(unit_id not in unit_ids, "content-unit-id-must-be-unique")
        unit_ids.add(unit_id)
        _validate_evidence(unit.get("surface"), f"unit-{index}-surface")
        if "semantic_role" in unit:
            _validate_evidence(unit["semantic_role"], f"unit-{index}-semantic-role")
        if "coordinate" in unit:
            _validate_coordinate(unit["coordinate"], f"unit-{index}-coordinate")
    relations = record.get("relations")
    _require(isinstance(relations, list), "normalized-relations-required")
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        _require(isinstance(relation, dict), f"relation-{index}-must-be-object")
        relation_id = relation.get("relation_id")
        _require(isinstance(relation_id, str) and relation_id, f"relation-{index}-id-required")
        _require(relation_id not in relation_ids, "relation-id-must-be-unique")
        relation_ids.add(relation_id)
        _require(relation.get("evidence_origin") in {"provider-explicit", "raiatea-derived"}, f"relation-{index}-bad-origin")
        _require(bool(relation.get("basis")), f"relation-{index}-basis-required")


def validate_any(record: dict[str, Any]) -> str:
    if "run_id" in record:
        validate(record)
        return "processing-run"
    if "representation_id" in record:
        validate_representation(record)
        return "normalized-representation"
    if "evidence_id" in record:
        validate_provider_evidence(record)
        return "provider-evidence"
    raise ContractError("unknown-contract-record-kind")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.records:
        record = json.loads(path.read_text(encoding="utf-8"))
        kind = validate_any(record)
        print(f"PASS {kind} {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
