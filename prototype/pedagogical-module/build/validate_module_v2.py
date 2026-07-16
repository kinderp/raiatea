#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import validate_module as base

ValidationIssue = base.ValidationIssue
ModuleValidationError = base.ModuleValidationError
raise_for_issues = base.raise_for_issues


def validate_rendered_html(output: str) -> list[ValidationIssue]:
    """Validate generated HTML while ignoring JavaScript template URLs.

    The base validator scans every ``href="#..."`` occurrence in the complete
    self-contained document. This includes JavaScript template literals such as
    ``href="#concept-${escapeHtml(remediation.conceptRef)}"``. That target is
    constructed at runtime, so it is not a broken static HTML reference.
    """
    issues = base.validate_rendered_html(output)
    return [
        issue
        for issue in issues
        if not (
            issue.path == "output"
            and "broken internal reference" in issue.message
            and "${" in issue.message
        )
    ]


def _non_empty(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(ValidationIssue(path, "must be a non-empty string"))


def validate_module(data: Any) -> list[ValidationIssue]:
    issues = list(base.validate_module(data))
    if not isinstance(data, dict):
        return issues

    concept_ids = {
        item.get("id")
        for item in data.get("concepts", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    for step_index, step in enumerate(data.get("steps", [])):
        if not isinstance(step, dict):
            continue
        quiz = step.get("quiz")
        if not isinstance(quiz, dict):
            continue
        remediation = quiz.get("remediation")
        if remediation is None:
            continue

        path = f"$.steps[{step_index}].quiz.remediation"
        if not isinstance(remediation, dict):
            issues.append(ValidationIssue(path, "must be an object"))
            continue

        allowed = {"title", "explanation", "conceptRef", "actionLabel", "retryLabel"}
        unknown = sorted(set(remediation) - allowed)
        for field in unknown:
            issues.append(ValidationIssue(f"{path}.{field}", "field is not supported"))

        for field in ("title", "explanation"):
            if field not in remediation:
                issues.append(ValidationIssue(f"{path}.{field}", "required field is missing"))
            else:
                _non_empty(remediation[field], f"{path}.{field}", issues)

        for field in ("actionLabel", "retryLabel"):
            if field in remediation:
                _non_empty(remediation[field], f"{path}.{field}", issues)

        concept_ref = remediation.get("conceptRef")
        if concept_ref is not None:
            _non_empty(concept_ref, f"{path}.conceptRef", issues)
            if isinstance(concept_ref, str) and concept_ref not in concept_ids:
                issues.append(
                    ValidationIssue(
                        f"{path}.conceptRef",
                        f"unknown concept reference '{concept_ref}'",
                    )
                )

    return issues


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleValidationError(
            [ValidationIssue(str(path), f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")]
        ) from exc
    raise_for_issues(validate_module(data))
    return data


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate a Raiatea pedagogical module")
    parser.add_argument("module", type=Path)
    args = parser.parse_args()

    try:
        load_and_validate(args.module)
    except ModuleValidationError as exc:
        print("Module validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    print(f"Valid module: {args.module}")


if __name__ == "__main__":
    main()
