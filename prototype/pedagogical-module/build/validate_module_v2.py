#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import validate_module as base
from layout_visual import compile_layout
from validate_module_identity import validate_module_identity

ValidationIssue = base.ValidationIssue
ModuleValidationError = base.ModuleValidationError
raise_for_issues = base.raise_for_issues

PROVENANCE_KINDS = {"original", "translation", "adaptation", "derived", "inference"}
TRANSFORMATION_KINDS = {
    "translation",
    "selection",
    "simplification",
    "stepwise-decomposition",
    "interactive-reconstruction",
    "worked-example",
    "derived-calculation",
    "diagnostic-question",
}


def _non_empty(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(ValidationIssue(path, "must be a non-empty string"))


def _identity_issues(data: Any) -> list[ValidationIssue]:
    converted: list[ValidationIssue] = []
    for issue in validate_module_identity(data):
        path, separator, message = issue.partition(": ")
        if not separator:
            converted.append(ValidationIssue("$", issue))
        else:
            converted.append(ValidationIssue(path, message))
    return converted


def _validate_step_provenance(provenance: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(provenance, dict):
        issues.append(ValidationIssue(path, "must be an object"))
        return
    allowed = {
        "kind", "sourceSection", "sourcePages", "sourceFigure",
        "transformations", "derivedValues", "note",
    }
    for field in sorted(set(provenance) - allowed):
        issues.append(ValidationIssue(f"{path}.{field}", "field is not supported"))
    if "kind" not in provenance:
        issues.append(ValidationIssue(f"{path}.kind", "required field is missing"))
    elif provenance.get("kind") not in PROVENANCE_KINDS:
        issues.append(ValidationIssue(f"{path}.kind", f"must be one of {sorted(PROVENANCE_KINDS)}"))
    for field in ("sourceSection", "sourceFigure", "note"):
        if field in provenance:
            _non_empty(provenance[field], f"{path}.{field}", issues)
    pages = provenance.get("sourcePages")
    if pages is not None:
        if not isinstance(pages, list):
            issues.append(ValidationIssue(f"{path}.sourcePages", "must be an array"))
        else:
            for index, page in enumerate(pages):
                if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                    issues.append(ValidationIssue(f"{path}.sourcePages[{index}]", "must be a positive integer"))
    transformations = provenance.get("transformations")
    if transformations is not None:
        if not isinstance(transformations, list) or not transformations:
            issues.append(ValidationIssue(f"{path}.transformations", "must contain at least one transformation"))
        else:
            for index, transformation in enumerate(transformations):
                if transformation not in TRANSFORMATION_KINDS:
                    issues.append(
                        ValidationIssue(
                            f"{path}.transformations[{index}]",
                            f"must be one of {sorted(TRANSFORMATION_KINDS)}",
                        )
                    )
    if "derivedValues" in provenance and not isinstance(provenance["derivedValues"], bool):
        issues.append(ValidationIssue(f"{path}.derivedValues", "must be a boolean"))


def _validate_activity(activity: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(activity, dict):
        issues.append(ValidationIssue(path, "must be an object"))
        return

    allowed = {
        "type", "prompt", "answers", "correctIndex",
        "correctFeedback", "incorrectFeedback",
    }
    for field in sorted(set(activity) - allowed):
        issues.append(ValidationIssue(f"{path}.{field}", "field is not supported"))

    required = (
        "type", "prompt", "answers", "correctIndex",
        "correctFeedback", "incorrectFeedback",
    )
    for field in required:
        if field not in activity:
            issues.append(ValidationIssue(f"{path}.{field}", "required field is missing"))

    if activity.get("type") != "choice":
        issues.append(ValidationIssue(f"{path}.type", "must be choice"))

    for field in ("prompt", "correctFeedback", "incorrectFeedback"):
        _non_empty(activity.get(field), f"{path}.{field}", issues)

    answers = activity.get("answers")
    if not isinstance(answers, list):
        issues.append(ValidationIssue(f"{path}.answers", "must be an array"))
    else:
        if len(answers) < 2:
            issues.append(ValidationIssue(f"{path}.answers", "must contain at least two answers"))
        for index, answer in enumerate(answers):
            _non_empty(answer, f"{path}.answers[{index}]", issues)

    correct_index = activity.get("correctIndex")
    if not isinstance(correct_index, int) or isinstance(correct_index, bool):
        issues.append(ValidationIssue(f"{path}.correctIndex", "must be an integer"))
    elif isinstance(answers, list) and not 0 <= correct_index < len(answers):
        issues.append(
            ValidationIssue(
                f"{path}.correctIndex",
                f"must refer to an answer between 0 and {max(len(answers) - 1, 0)}",
            )
        )


def resolve_module_layout(data: Any, module_path: Path) -> Any:
    """Resolve a module-local declarative layout into canonical primitives.

    The source contract stays compact (`visual.type = layout`), while every
    downstream validator and renderer continues to consume the existing
    `primitives` contract.
    """
    if not isinstance(data, dict):
        return data
    visual = data.get("visual")
    if not isinstance(visual, dict) or visual.get("type") != "layout":
        return data

    allowed = {"type", "source"}
    unknown = sorted(set(visual) - allowed)
    if unknown:
        raise ModuleValidationError([
            ValidationIssue(f"$.visual.{field}", "field is not supported")
            for field in unknown
        ])

    source = visual.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ModuleValidationError([
            ValidationIssue("$.visual.source", "must be a non-empty string")
        ])

    source_path = Path(source)
    has_windows_drive = (
        len(source) >= 3
        and source[0].isalpha()
        and source[1] == ":"
        and source[2] in {"/", "\\"}
    )
    if (
        source_path.is_absolute()
        or has_windows_drive
        or "\\" in source
        or ".." in source_path.parts
        or not source.endswith(".layout.json")
    ):
        raise ModuleValidationError([
            ValidationIssue(
                "$.visual.source",
                "must be a relative *.layout.json path without parent traversal",
            )
        ])

    layout_path = (module_path.parent / source_path).resolve()
    try:
        layout_path.relative_to(module_path.parent.resolve())
    except ValueError as exc:
        raise ModuleValidationError([
            ValidationIssue("$.visual.source", "must stay inside the module directory")
        ]) from exc

    if not layout_path.is_file():
        raise ModuleValidationError([
            ValidationIssue("$.visual.source", f"layout file does not exist: {source}")
        ])

    try:
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleValidationError([
            ValidationIssue(
                "$.visual.source",
                f"invalid layout JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            )
        ]) from exc

    try:
        compiled = compile_layout(layout)
    except (TypeError, ValueError) as exc:
        raise ModuleValidationError([
            ValidationIssue("$.visual.source", f"invalid declarative layout: {exc}")
        ]) from exc

    resolved = json.loads(json.dumps(data))
    resolved["visual"] = compiled
    build_metadata = resolved.get("build")
    if not isinstance(build_metadata, dict):
        build_metadata = {}
        resolved["build"] = build_metadata
    build_metadata["layoutSource"] = source
    return resolved


def validate_module(data: Any) -> list[ValidationIssue]:
    issues = list(base.validate_module(data))
    if not isinstance(data, dict):
        return issues

    issues.extend(_identity_issues(data))

    concept_ids = {
        item.get("id")
        for item in data.get("concepts", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    for step_index, step in enumerate(data.get("steps", [])):
        if not isinstance(step, dict):
            continue

        if "provenance" in step:
            _validate_step_provenance(
                step["provenance"],
                f"$.steps[{step_index}].provenance",
                issues,
            )

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

        allowed = {
            "title", "explanation", "conceptRef",
            "actionLabel", "retryLabel", "activity",
        }
        for field in sorted(set(remediation) - allowed):
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

        if "activity" in remediation:
            _validate_activity(remediation["activity"], f"{path}.activity", issues)

    return issues


def validate_rendered_html(output: str) -> list[ValidationIssue]:
    issues = list(base.validate_rendered_html(output))
    return [
        issue
        for issue in issues
        if not (
            "broken internal reference" in issue.message
            and "${" in issue.message
        )
    ]


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleValidationError(
            [ValidationIssue(str(path), f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")]
        ) from exc
    data = resolve_module_layout(data, path)
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
