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
    if value.get("value_state") != "present":
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


def validate(record: dict[str, Any]) -> None:
    """Validate a ProcessingRunRecord."""
    _validate_schema_version(record)
    _require("success" not in record, "boolean-success-is-forbidden")
    _validate_provider_route(record.get("provider"), record.get("route_profile"))

    outcome = record.get("outcome")
    _require(isinstance(outcome, dict), "processing-outcome-required")
    _require("success" not in outcome, "processing-outcome-must-not-be-boolean")
    _require("produced" not in outcome, "produced-refs-must-live-outside-processing-outcome")
    _require("rights" not in outcome and "policy" not in outcome, "processing-outcome-must-not-own-policy")
    assessments = outcome.get("assessments")
    _require(isinstance(assessments, list) and assessments, "scoped-assessments-required")
    for index, assessment in enumerate(assessments):
        _require(isinstance(assessment, dict), f"assessment-{index}-must-be-object")
        _require(bool(assessment.get("scope")), f"assessment-{index}-scope-required")
        _require(bool(assessment.get("basis")), f"assessment-{index}-basis-required")
        _require("completeness" in assessment and "integrity" in assessment, f"assessment-{index}-states-required")

    stages = record.get("stages")
    _require(isinstance(stages, list) and stages, "processing-stages-required")
    stage_ids: set[str] = set()
    for stage in stages:
        _require(isinstance(stage, dict), "stage-must-be-object")
        stage_id = stage.get("stage_id")
        _require(isinstance(stage_id, str) and stage_id, "stage-id-required")
        _require(stage_id not in stage_ids, "stage-id-must-be-unique")
        stage_ids.add(stage_id)
        _validate_provider_route(stage.get("provider"), stage.get("route_profile"), "stage")
        _validate_evidence(stage.get("provider_status"), "stage-provider-status")
        if stage.get("stage_kind") == "ocr-fallback":
            _require(bool(stage.get("trigger_basis")), "ocr-fallback-trigger-basis-required")
            _require(stage.get("parent_stage_id") in stage_ids, "ocr-fallback-parent-stage-must-precede")
            _require(
                stage.get("reconciliation_state") in {"resolved", "partial", "unresolved", "not-measured"},
                "ocr-reconciliation-state-required",
            )

    for produced in record.get("produced", []):
        _require(isinstance(produced, dict), "produced-ref-must-be-object")
        _require(produced.get("kind") in {"provider-evidence", "normalized-representation"}, "unknown-produced-ref-kind")


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
