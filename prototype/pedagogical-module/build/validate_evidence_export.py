#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORMAT = "raiatea-learner-evidence"
VERSION = 1
TOP_LEVEL_FIELDS = {"format", "version", "module", "progress"}
MODULE_FIELDS = {"id", "title", "language", "stepCount", "source"}
SOURCE_FIELDS = {"title", "chapter", "section", "figure", "pages"}
PROGRESS_FIELDS = {"currentStep", "steps"}
STEP_FIELDS = {
    "index",
    "title",
    "attempts",
    "correct",
    "usedRemediation",
    "activityCompleted",
}


class EvidenceExportValidationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _exact_fields(
    value: dict[str, Any], required: set[str], allowed: set[str], path: str, issues: list[str]
) -> None:
    for field in sorted(required - set(value)):
        issues.append(f"{path}.{field}: required field is missing")
    for field in sorted(set(value) - allowed):
        issues.append(f"{path}.{field}: field is not supported")


def _non_empty_string(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{path}: must be a non-empty string")


def _non_negative_integer(value: Any, path: str, issues: list[str]) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        issues.append(f"{path}: must be a non-negative integer")
        return False
    return True


def validate_evidence_export(data: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["$: must be an object"]

    _exact_fields(data, TOP_LEVEL_FIELDS, TOP_LEVEL_FIELDS, "$", issues)
    if data.get("format") != FORMAT:
        issues.append(f"$.format: must be {FORMAT}")
    if data.get("version") != VERSION:
        issues.append(f"$.version: must be {VERSION}")

    module = data.get("module")
    step_count: int | None = None
    if not isinstance(module, dict):
        issues.append("$.module: must be an object")
    else:
        _exact_fields(
            module,
            {"id", "title", "language", "stepCount"},
            MODULE_FIELDS,
            "$.module",
            issues,
        )
        for field in ("id", "title", "language"):
            _non_empty_string(module.get(field), f"$.module.{field}", issues)
        if _non_negative_integer(module.get("stepCount"), "$.module.stepCount", issues):
            if module["stepCount"] < 1:
                issues.append("$.module.stepCount: must be at least 1")
            else:
                step_count = module["stepCount"]

        source = module.get("source")
        if source is not None:
            if not isinstance(source, dict):
                issues.append("$.module.source: must be an object")
            else:
                _exact_fields(source, set(), SOURCE_FIELDS, "$.module.source", issues)
                for field in ("title", "chapter", "section", "figure"):
                    if field in source:
                        _non_empty_string(source[field], f"$.module.source.{field}", issues)
                if "pages" in source:
                    pages = source["pages"]
                    if not isinstance(pages, list) or not pages:
                        issues.append("$.module.source.pages: must contain at least one page")
                    else:
                        for index, page in enumerate(pages):
                            if (
                                not isinstance(page, int)
                                or isinstance(page, bool)
                                or page < 1
                            ):
                                issues.append(
                                    f"$.module.source.pages[{index}]: must be a positive integer"
                                )

    progress = data.get("progress")
    if not isinstance(progress, dict):
        issues.append("$.progress: must be an object")
    else:
        _exact_fields(progress, PROGRESS_FIELDS, PROGRESS_FIELDS, "$.progress", issues)
        current_step = progress.get("currentStep")
        if _non_negative_integer(current_step, "$.progress.currentStep", issues):
            if step_count is not None and current_step >= step_count:
                issues.append("$.progress.currentStep: must refer to an existing step")

        steps = progress.get("steps")
        if not isinstance(steps, list) or not steps:
            issues.append("$.progress.steps: must contain at least one step")
        else:
            if step_count is not None and len(steps) != step_count:
                issues.append(
                    "$.progress.steps: length must match $.module.stepCount"
                )
            for position, item in enumerate(steps):
                path = f"$.progress.steps[{position}]"
                if not isinstance(item, dict):
                    issues.append(f"{path}: must be an object")
                    continue
                _exact_fields(item, STEP_FIELDS, STEP_FIELDS, path, issues)
                index = item.get("index")
                if _non_negative_integer(index, f"{path}.index", issues) and index != position:
                    issues.append(f"{path}.index: must equal its array position")
                _non_empty_string(item.get("title"), f"{path}.title", issues)
                _non_negative_integer(item.get("attempts"), f"{path}.attempts", issues)
                for field in ("correct", "usedRemediation", "activityCompleted"):
                    if not isinstance(item.get(field), bool):
                        issues.append(f"{path}.{field}: must be a boolean")

    return issues


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceExportValidationError(
            [f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
        ) from exc
    issues = validate_evidence_export(data)
    if issues:
        raise EvidenceExportValidationError(issues)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a Raiatea learner evidence export")
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    try:
        load_and_validate(args.export)
    except EvidenceExportValidationError as exc:
        print("Evidence export validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    print(f"Valid evidence export: {args.export}")


if __name__ == "__main__":
    main()
