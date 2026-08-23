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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def validate(record: dict[str, Any]) -> None:
    _require(record.get("schema_version") == "0.1.0", "unsupported-schema-version")
    _require("success" not in record, "boolean-success-is-forbidden")
    provider = record.get("provider")
    route = record.get("route_profile")
    _require(isinstance(provider, dict) and provider.get("provider_id"), "provider-ref-required")
    _require(isinstance(route, dict) and route.get("route_profile_id"), "route-profile-ref-required")
    _require("route_profile_id" not in provider, "provider-and-route-profile-must-remain-distinct")
    _require("provider_id" not in route, "route-profile-must-not-duplicate-provider-identity")

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
        _require(isinstance(stage.get("provider"), dict), "stage-provider-required")
        _require(isinstance(stage.get("route_profile"), dict), "stage-route-profile-required")
        _validate_evidence(stage.get("provider_status"), "stage-provider-status")
        if stage.get("stage_kind") == "ocr-fallback":
            _require(bool(stage.get("trigger_basis")), "ocr-fallback-trigger-basis-required")
            _require(stage.get("parent_stage_id") in stage_ids, "ocr-fallback-parent-stage-must-precede")
            _require(stage.get("reconciliation_state") in {"resolved", "partial", "unresolved", "not-measured"}, "ocr-reconciliation-state-required")

    for produced in record.get("produced", []):
        _require(produced.get("kind") in {"provider-evidence", "normalized-representation"}, "unknown-produced-ref-kind")


def _validate_evidence(value: Any, label: str) -> None:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    evidence_state = value.get("evidence_state")
    value_state = value.get("value_state")
    _require(evidence_state in {"measured", "partial", "not-measured", "malformed-evidence", "ambiguous", "not-applicable"}, f"{label}-bad-evidence-state")
    _require(value_state in {"present", "explicit-empty", "explicit-mismatch", "unknown"}, f"{label}-bad-value-state")
    _require(bool(value.get("basis")), f"{label}-basis-required")
    if value_state in {"present", "explicit-empty"}:
        _require("value" in value, f"{label}-value-required-for-{value_state}")
    if evidence_state == "not-measured":
        _require(value_state == "unknown", f"{label}-not-measured-must-have-unknown-value")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.records:
        record = json.loads(path.read_text(encoding="utf-8"))
        validate(record)
        print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
