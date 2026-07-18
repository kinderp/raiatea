#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

FORMAT = "raiatea-learner-evidence"
VERSION = 2
ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
TOP_LEVEL_FIELDS = {"format", "version", "module", "progress"}
MODULE_FIELDS = {"id", "revision", "title", "language", "stepCount", "source"}
SOURCE_FIELDS = {"title", "chapter", "section", "figure", "pages"}
PROGRESS_FIELDS = {"currentStepId", "currentStepIndex", "steps"}
STEP_FIELDS = {
    "index",
    "stepId",
    "title",
    "attempts",
    "correct",
    "usedRemediation",
    "activityCompleted",
}


class EvidenceExportV2ValidationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _exact_fields(
    value: dict[str, Any],
    required: set[str],
    allowed: set[str],
    path: str,
    issues: list[str],
) -> None:
    for field in sorted(required - set(value)):
        issues.append(f"{path}.{field}: required field is missing")
    for field in sorted(set(value) - allowed):
        issues.append(f"{path}.{field}: field is not supported")


def _non_empty_string(value: Any, path: str, issues: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{path}: must be a non-empty string")
        return False
    return True


def _canonical_id(value: Any, path: str, issues: list[str]) -> bool:
    if not _non_empty_string(value, path, issues):
        return False
    if not ID_PATTERN.fullmatch(value):
        issues.append(
            f"{path}: must contain only lowercase letters, digits, and hyphens"
        )
        return False
    return True


def _positive_integer(value: Any, path: str, issues: list[str]) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        issues.append(f"{path}: must be a positive integer")
        return False
    return True


def _non_negative_integer(value: Any, path: str, issues: list[str]) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        issues.append(f"{path}: must be a non-negative integer")
        return False
    return True


def _validate_source(source: Any, path: str, issues: list[str]) -> None:
    if not isinstance(source, dict):
        issues.append(f"{path}: must be an object")
        return
    _exact_fields(source, set(), SOURCE_FIELDS, path, issues)
    for field in ("title", "chapter", "section", "figure"):
        if field in source:
            _non_empty_string(source[field], f"{path}.{field}", issues)
    if "pages" not in source:
        return
    pages = source["pages"]
    if not isinstance(pages, list) or not pages:
        issues.append(f"{path}.pages: must contain at least one page")
        return
    for index, page in enumerate(pages):
        if not isinstance(page, int) or isinstance(page, bool) or page < 1:
            issues.append(f"{path}.pages[{index}]: must be a positive integer")


def validate_evidence_export_v2(data: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["$: must be an object"]

    _exact_fields(data, TOP_LEVEL_FIELDS, TOP_LEVEL_FIELDS, "$", issues)
    if data.get("format") != FORMAT:
        issues.append(f"$.format: must be {FORMAT}")
    version = data.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version != VERSION:
        issues.append(f"$.version: must be the integer {VERSION}")

    module = data.get("module")
    step_count: int | None = None
    if not isinstance(module, dict):
        issues.append("$.module: must be an object")
    else:
        _exact_fields(
            module,
            {"id", "revision", "title", "language", "stepCount"},
            MODULE_FIELDS,
            "$.module",
            issues,
        )
        _canonical_id(module.get("id"), "$.module.id", issues)
        if _positive_integer(module.get("revision"), "$.module.revision", issues):
            pass
        for field in ("title", "language"):
            _non_empty_string(module.get(field), f"$.module.{field}", issues)
        if _positive_integer(module.get("stepCount"), "$.module.stepCount", issues):
            step_count = module["stepCount"]
        if "source" in module:
            _validate_source(module["source"], "$.module.source", issues)

    progress = data.get("progress")
    if not isinstance(progress, dict):
        issues.append("$.progress: must be an object")
        return issues

    _exact_fields(progress, PROGRESS_FIELDS, PROGRESS_FIELDS, "$.progress", issues)
    current_step_id = progress.get("currentStepId")
    current_id_valid = _canonical_id(
        current_step_id, "$.progress.currentStepId", issues
    )
    current_step_index = progress.get("currentStepIndex")
    current_index_valid = _non_negative_integer(
        current_step_index, "$.progress.currentStepIndex", issues
    )

    steps = progress.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append("$.progress.steps: must contain at least one step")
        return issues

    if step_count is not None and len(steps) != step_count:
        issues.append("$.progress.steps: length must match $.module.stepCount")
    if current_index_valid and current_step_index >= len(steps):
        issues.append("$.progress.currentStepIndex: must refer to an existing step")
        current_index_valid = False

    seen_step_ids: set[str] = set()
    exported_step_ids: set[str] = set()
    step_ids_by_position: list[str | None] = []
    for position, item in enumerate(steps):
        path = f"$.progress.steps[{position}]"
        step_id_for_position: str | None = None
        if not isinstance(item, dict):
            issues.append(f"{path}: must be an object")
            step_ids_by_position.append(None)
            continue

        _exact_fields(item, STEP_FIELDS, STEP_FIELDS, path, issues)
        index = item.get("index")
        if _non_negative_integer(index, f"{path}.index", issues) and index != position:
            issues.append(f"{path}.index: must equal its array position")

        step_id = item.get("stepId")
        if _canonical_id(step_id, f"{path}.stepId", issues):
            step_id_for_position = step_id
            exported_step_ids.add(step_id)
            if step_id in seen_step_ids:
                issues.append(f"{path}.stepId: duplicate step id '{step_id}'")
            else:
                seen_step_ids.add(step_id)
        step_ids_by_position.append(step_id_for_position)

        _non_empty_string(item.get("title"), f"{path}.title", issues)
        _non_negative_integer(item.get("attempts"), f"{path}.attempts", issues)
        for field in ("correct", "usedRemediation", "activityCompleted"):
            if not isinstance(item.get(field), bool):
                issues.append(f"{path}.{field}: must be a boolean")

    if current_id_valid and current_step_id not in exported_step_ids:
        issues.append("$.progress.currentStepId: must refer to an exported step")
    if current_id_valid and current_index_valid:
        indexed_step_id = step_ids_by_position[current_step_index]
        if indexed_step_id is not None and indexed_step_id != current_step_id:
            issues.append(
                "$.progress.currentStepId: must match "
                "$.progress.steps[currentStepIndex].stepId"
            )

    return issues


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceExportV2ValidationError(
            [f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
        ) from exc
    issues = validate_evidence_export_v2(data)
    if issues:
        raise EvidenceExportV2ValidationError(issues)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a Raiatea learner evidence v2 export"
    )
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    try:
        load_and_validate(args.export)
    except EvidenceExportV2ValidationError as exc:
        print("Evidence v2 validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    print(f"Valid evidence v2 export: {args.export}")


if __name__ == "__main__":
    main()
