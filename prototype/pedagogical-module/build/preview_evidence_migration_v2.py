#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import check_evidence_compatibility_v2 as exact_checker
import check_evidence_migration_manifest_context as manifest_context_checker
import validate_evidence_export_v2 as evidence_validator
import validate_evidence_migration_manifest as manifest_validator
import validate_module_v2 as module_validator

SUPPORTED_CLASSIFICATIONS = {
    "exact",
    "declared-lossless",
    "declared-partial",
    "incompatible",
    "unsupported",
}
SUCCESS_CLASSIFICATIONS = {"exact", "declared-lossless", "declared-partial"}


class EvidenceMigrationPreviewInputError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _prefixed_issue(namespace: str, issue: object) -> str:
    text = str(issue)
    if text.startswith("$"):
        return f"$.{namespace}{text[1:]}"
    return f"$.{namespace}: {text}"


def _identity_from_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    module = evidence.get("module")
    if not isinstance(module, dict):
        module = {}
    return {"moduleId": module.get("id"), "revision": module.get("revision")}


def _identity_from_module(module: dict[str, Any]) -> dict[str, Any]:
    return {"moduleId": module.get("id"), "revision": module.get("revision")}


def _result(
    *,
    classification: str,
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    manifest_status: str,
    summary: str,
    issues: list[str] | None = None,
    steps: list[dict[str, Any]] | None = None,
    current_position: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if classification not in SUPPORTED_CLASSIFICATIONS:
        raise ValueError(f"unknown classification: {classification}")
    return {
        "classification": classification,
        "source": _identity_from_evidence(evidence),
        "target": _identity_from_module(target_module),
        "manifestStatus": manifest_status,
        "summary": summary,
        "issues": list(issues or []),
        "steps": list(steps or []),
        "currentPosition": current_position,
        "candidateAvailable": candidate is not None,
        "candidate": candidate,
    }


def _evidence_step_map(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step["stepId"]: step for step in evidence["progress"]["steps"]}


def _source_step_map(
    source_module: dict[str, Any],
) -> dict[str, tuple[int, dict[str, Any]]]:
    return {
        step["id"]: (index, step)
        for index, step in enumerate(source_module["steps"])
    }


def _target_step_map(
    target_module: dict[str, Any],
) -> dict[str, tuple[int, dict[str, Any]]]:
    return {
        step["id"]: (index, step)
        for index, step in enumerate(target_module["steps"])
    }


def _evidence_snapshot(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "attempts": step["attempts"],
        "correct": step["correct"],
        "usedRemediation": step["usedRemediation"],
        "activityCompleted": step["activityCompleted"],
    }


def _candidate_step(
    target_index: int,
    target_step: dict[str, Any],
    source_evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    if source_evidence is None:
        snapshot = {
            "attempts": 0,
            "correct": False,
            "usedRemediation": False,
            "activityCompleted": False,
        }
    else:
        snapshot = _evidence_snapshot(source_evidence)
    return {
        "index": target_index,
        "stepId": target_step["id"],
        "title": target_step["title"],
        **snapshot,
    }


def _build_candidate(
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    preserved_ids: set[str],
    current_target_id: str,
    current_target_index: int,
) -> dict[str, Any]:
    evidence_steps = _evidence_step_map(evidence)
    target_steps = [
        _candidate_step(
            index,
            step,
            evidence_steps.get(step["id"]) if step["id"] in preserved_ids else None,
        )
        for index, step in enumerate(target_module["steps"])
    ]
    candidate = {
        "format": evidence_validator.FORMAT,
        "version": evidence_validator.VERSION,
        "module": {
            "id": target_module["id"],
            "revision": target_module["revision"],
            "title": target_module["title"],
            "language": target_module["language"],
            "stepCount": len(target_steps),
        },
        "progress": {
            "currentStepId": current_target_id,
            "currentStepIndex": current_target_index,
            "steps": target_steps,
        },
    }
    structural_issues = evidence_validator.validate_evidence_export_v2(candidate)
    contextual_issues = exact_checker.check_exact_compatibility(target_module, candidate)
    if structural_issues or contextual_issues:
        raise AssertionError(
            "internal candidate invariant failed: "
            + "; ".join(structural_issues + contextual_issues)
        )
    return candidate


def _exact_preview(
    evidence: dict[str, Any], target_module: dict[str, Any]
) -> dict[str, Any]:
    evidence_steps = _evidence_step_map(evidence)
    steps: list[dict[str, Any]] = []
    for index, target_step in enumerate(target_module["steps"]):
        source_step = evidence_steps[target_step["id"]]
        steps.append(
            {
                "stepId": target_step["id"],
                "sourceIndex": source_step["index"],
                "targetIndex": index,
                "sourceTitle": source_step["title"],
                "targetTitle": target_step["title"],
                "status": "preserved",
                "evidenceDisposition": "copied",
                "evidence": _evidence_snapshot(source_step),
            }
        )
    current = evidence["progress"]
    return _result(
        classification="exact",
        evidence=evidence,
        target_module=target_module,
        manifest_status="not-needed",
        summary="Evidence already exactly matches the requested canonical revision.",
        steps=steps,
        current_position={
            "status": "unchanged",
            "sourceStepId": current["currentStepId"],
            "sourceIndex": current["currentStepIndex"],
            "targetStepId": current["currentStepId"],
            "targetIndex": current["currentStepIndex"],
        },
    )


def classify_preview(
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    source_module: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify and preview one direct migration without mutating inputs."""
    if (source_module is None) != (manifest is None):
        raise EvidenceMigrationPreviewInputError(
            ["$.migrationContext: sourceModule and manifest must be supplied together"]
        )

    exact_issues = exact_checker.check_exact_compatibility(target_module, evidence)
    if not exact_issues:
        return _exact_preview(evidence, target_module)

    if evidence["module"]["id"] != target_module["id"]:
        return _result(
            classification="incompatible",
            evidence=evidence,
            target_module=target_module,
            manifest_status="mismatched" if manifest is not None else "missing",
            summary="Evidence and target belong to different module routes.",
            issues=[exact_issues[0]],
        )

    if source_module is None or manifest is None:
        return _result(
            classification="incompatible",
            evidence=evidence,
            target_module=target_module,
            manifest_status="missing",
            summary="A non-exact transition requires one direct source and manifest context.",
            issues=["$.manifest: direct migration manifest is required"],
        )

    source_issues = exact_checker.check_exact_compatibility(source_module, evidence)
    if source_issues:
        return _result(
            classification="incompatible",
            evidence=evidence,
            target_module=target_module,
            manifest_status="mismatched",
            summary="Evidence does not exactly match the supplied source revision.",
            issues=[_prefixed_issue("sourceContext", issue) for issue in source_issues],
        )

    context_issues = manifest_context_checker.check_manifest_context(
        source_module, target_module, manifest
    )
    if context_issues:
        return _result(
            classification="incompatible",
            evidence=evidence,
            target_module=target_module,
            manifest_status="mismatched",
            summary="The manifest does not bind the supplied source and target revisions.",
            issues=context_issues,
        )

    operations = manifest["operations"]
    preserved_ids = {
        entry["sourceStepId"] for entry in operations["preserve"]
    }
    retired_ids = set(operations["retire"])
    introduced_ids = set(operations["introduce"])
    evidence_steps = _evidence_step_map(evidence)
    source_steps = _source_step_map(source_module)
    target_steps = _target_step_map(target_module)

    preview_steps: list[dict[str, Any]] = []
    for target_index, target_step in enumerate(target_module["steps"]):
        step_id = target_step["id"]
        if step_id in preserved_ids:
            source_index, source_step = source_steps[step_id]
            source_evidence = evidence_steps[step_id]
            preview_steps.append(
                {
                    "stepId": step_id,
                    "sourceIndex": source_index,
                    "targetIndex": target_index,
                    "sourceTitle": source_step["title"],
                    "targetTitle": target_step["title"],
                    "status": "preserved",
                    "evidenceDisposition": "copied",
                    "evidence": _evidence_snapshot(source_evidence),
                }
            )
        elif step_id in introduced_ids:
            preview_steps.append(
                {
                    "stepId": step_id,
                    "sourceIndex": None,
                    "targetIndex": target_index,
                    "sourceTitle": None,
                    "targetTitle": target_step["title"],
                    "status": "introduced",
                    "evidenceDisposition": "empty",
                    "evidence": {
                        "attempts": 0,
                        "correct": False,
                        "usedRemediation": False,
                        "activityCompleted": False,
                    },
                }
            )

    for source_index, source_step in enumerate(source_module["steps"]):
        step_id = source_step["id"]
        if step_id not in retired_ids:
            continue
        source_evidence = evidence_steps[step_id]
        preview_steps.append(
            {
                "stepId": step_id,
                "sourceIndex": source_index,
                "targetIndex": None,
                "sourceTitle": source_step["title"],
                "targetTitle": None,
                "status": "retired",
                "evidenceDisposition": "historical-only",
                "evidence": _evidence_snapshot(source_evidence),
            }
        )

    current_id = evidence["progress"]["currentStepId"]
    current_source_index = evidence["progress"]["currentStepIndex"]
    candidate: dict[str, Any] | None = None
    if current_id in preserved_ids:
        current_target_index = target_steps[current_id][0]
        current_position = {
            "status": "remapped",
            "sourceStepId": current_id,
            "sourceIndex": current_source_index,
            "targetStepId": current_id,
            "targetIndex": current_target_index,
        }
        candidate = _build_candidate(
            evidence,
            target_module,
            preserved_ids,
            current_id,
            current_target_index,
        )
    elif current_id in retired_ids:
        current_position = {
            "status": "unresolved-retired",
            "sourceStepId": current_id,
            "sourceIndex": current_source_index,
            "targetStepId": None,
            "targetIndex": None,
        }
    else:
        return _result(
            classification="incompatible",
            evidence=evidence,
            target_module=target_module,
            manifest_status="mismatched",
            summary="The manifest does not account for the evidence current step.",
            issues=[
                "$.progress.currentStepId: current step is neither preserved nor retired"
            ],
        )

    if not retired_ids and not introduced_ids:
        classification = "declared-lossless"
        summary = "The direct authored manifest preserves every allowlisted observation."
    else:
        classification = "declared-partial"
        summary = (
            "The direct authored manifest preserves some observations and explicitly "
            "marks introduced or retired responsibilities."
        )

    return _result(
        classification=classification,
        evidence=evidence,
        target_module=target_module,
        manifest_status="applicable",
        summary=summary,
        steps=preview_steps,
        current_position=current_position,
        candidate=candidate,
    )


def _load_json(path: Path, namespace: str) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [
            f"$.{namespace}: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ]


def _unsupported_result(
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    *,
    manifest_status: str,
    issues: list[str],
) -> dict[str, Any]:
    return _result(
        classification="unsupported",
        evidence=evidence,
        target_module=target_module,
        manifest_status=manifest_status,
        summary="The requested evidence or manifest feature is unsupported.",
        issues=issues,
    )


def _declares_unsupported_evidence(raw: Any) -> bool:
    if not isinstance(raw, dict):
        return False
    return (
        ("format" in raw and raw.get("format") != evidence_validator.FORMAT)
        or ("version" in raw and raw.get("version") != evidence_validator.VERSION)
    )


def _declares_unsupported_manifest(raw: Any) -> bool:
    if not isinstance(raw, dict):
        return False
    if "format" in raw and raw.get("format") != manifest_validator.FORMAT:
        return True
    if "version" in raw and raw.get("version") != manifest_validator.VERSION:
        return True
    operations = raw.get("operations")
    if isinstance(operations, dict):
        return not set(operations).issubset(manifest_validator.OPERATION_FIELDS)
    return False


def load_and_preview(
    evidence_path: Path,
    target_module_path: Path,
    source_module_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    if (source_module_path is None) != (manifest_path is None):
        raise EvidenceMigrationPreviewInputError(
            ["$.migrationContext: --source and --manifest must be supplied together"]
        )

    raw_evidence, evidence_read_issues = _load_json(evidence_path, "evidence")
    raw_target, target_read_issues = _load_json(target_module_path, "targetModule")
    raw_source: Any | None = None
    raw_manifest: Any | None = None
    source_read_issues: list[str] = []
    manifest_read_issues: list[str] = []
    if source_module_path is not None and manifest_path is not None:
        raw_source, source_read_issues = _load_json(source_module_path, "sourceModule")
        raw_manifest, manifest_read_issues = _load_json(manifest_path, "manifest")

    read_issues = (
        evidence_read_issues
        + target_read_issues
        + source_read_issues
        + manifest_read_issues
    )
    if read_issues:
        raise EvidenceMigrationPreviewInputError(read_issues)

    evidence_for_result = raw_evidence if isinstance(raw_evidence, dict) else {}
    target_for_result = raw_target if isinstance(raw_target, dict) else {}
    if _declares_unsupported_evidence(raw_evidence):
        return _unsupported_result(
            evidence_for_result,
            target_for_result,
            manifest_status="not-needed" if raw_manifest is None else "unsupported",
            issues=["$.evidence: unsupported learner-evidence format or version"],
        )
    if _declares_unsupported_manifest(raw_manifest):
        return _unsupported_result(
            evidence_for_result,
            target_for_result,
            manifest_status="unsupported",
            issues=["$.manifest: unsupported manifest format, version, or operation"],
        )

    input_issues: list[str] = []
    evidence: dict[str, Any] | None = None
    target_module: dict[str, Any] | None = None
    source_module: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None

    try:
        evidence = evidence_validator.load_and_validate(evidence_path)
    except evidence_validator.EvidenceExportV2ValidationError as exc:
        input_issues.extend(_prefixed_issue("evidence", issue) for issue in exc.issues)

    try:
        target_module = module_validator.load_and_validate(target_module_path)
    except module_validator.ModuleValidationError as exc:
        input_issues.extend(
            _prefixed_issue("targetModule", issue) for issue in exc.issues
        )

    if source_module_path is not None and manifest_path is not None:
        try:
            source_module = module_validator.load_and_validate(source_module_path)
        except module_validator.ModuleValidationError as exc:
            input_issues.extend(
                _prefixed_issue("sourceModule", issue) for issue in exc.issues
            )
        try:
            manifest = manifest_validator.load_and_validate(manifest_path)
        except manifest_validator.MigrationManifestValidationError as exc:
            input_issues.extend(
                _prefixed_issue("manifest", issue) for issue in exc.issues
            )

    if input_issues:
        raise EvidenceMigrationPreviewInputError(input_issues)

    assert evidence is not None
    assert target_module is not None
    return classify_preview(
        evidence,
        target_module,
        source_module=source_module,
        manifest=manifest,
    )


def _print_human(result: dict[str, Any]) -> None:
    print(f"Classification: {result['classification']}")
    print(
        "Identity: "
        f"{result['source']['moduleId']} revision {result['source']['revision']} -> "
        f"{result['target']['moduleId']} revision {result['target']['revision']}"
    )
    print(f"Manifest: {result['manifestStatus']}")
    print(result["summary"])
    for issue in result["issues"]:
        print(f"- {issue}")
    for step in result["steps"]:
        print(
            f"- {step['status']}: {step['stepId']} "
            f"({step['evidenceDisposition']})"
        )
    if result["currentPosition"] is not None:
        print(f"Current position: {result['currentPosition']['status']}")
    print(f"Candidate available: {str(result['candidateAvailable']).lower()}")
    print("Preview only: no evidence file or learner state was changed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Classify one learner-evidence v2 document against an exact target "
            "module revision and generate a read-only direct-migration preview"
        )
    )
    parser.add_argument("evidence", type=Path)
    parser.add_argument("target_module", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        result = load_and_preview(
            args.evidence,
            args.target_module,
            source_module_path=args.source,
            manifest_path=args.manifest,
        )
    except EvidenceMigrationPreviewInputError as exc:
        print("Evidence migration preview input validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        _print_human(result)

    if result["classification"] not in SUCCESS_CLASSIFICATIONS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
