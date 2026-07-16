#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
PLACEHOLDER_PATTERN = re.compile(r"{{\s*[^{}]+\s*}}")
HTML_ID_PATTERN = re.compile(r'\bid=["\']([^"\']+)["\']')
INTERNAL_HREF_PATTERN = re.compile(r'href=["\']#([^"\']+)["\']')
EXTERNAL_RESOURCE_PATTERN = re.compile(
    r"(?:src|href)=[\"'](?:https?:)?//|@import\s+url\(|url\([\"']?(?:https?:)?//",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class ModuleValidationError(ValueError):
    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("\n".join(str(issue) for issue in self.issues))


def _expect_type(
    value: Any,
    expected: type | tuple[type, ...],
    path: str,
    issues: list[ValidationIssue],
) -> bool:
    if not isinstance(value, expected):
        expected_name = (
            ", ".join(item.__name__ for item in expected)
            if isinstance(expected, tuple)
            else expected.__name__
        )
        issues.append(ValidationIssue(path, f"expected {expected_name}"))
        return False
    return True


def _require_keys(
    obj: dict[str, Any],
    keys: Iterable[str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    for key in keys:
        if key not in obj:
            issues.append(ValidationIssue(f"{path}.{key}", "required field is missing"))


def _validate_quiz(quiz: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not _expect_type(quiz, dict, path, issues):
        return
    required = (
        "question",
        "answers",
        "correctIndex",
        "correctFeedback",
        "incorrectFeedback",
    )
    _require_keys(quiz, required, path, issues)
    answers = quiz.get("answers")
    if _expect_type(answers, list, f"{path}.answers", issues):
        if len(answers) < 2:
            issues.append(ValidationIssue(f"{path}.answers", "must contain at least two answers"))
        for index, answer in enumerate(answers):
            if not isinstance(answer, str) or not answer.strip():
                issues.append(
                    ValidationIssue(f"{path}.answers[{index}]", "must be a non-empty string")
                )
    correct_index = quiz.get("correctIndex")
    if not isinstance(correct_index, int):
        issues.append(ValidationIssue(f"{path}.correctIndex", "must be an integer"))
    elif isinstance(answers, list) and not 0 <= correct_index < len(answers):
        issues.append(
            ValidationIssue(
                f"{path}.correctIndex",
                f"must refer to an answer between 0 and {max(len(answers) - 1, 0)}",
            )
        )


def validate_module(data: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _expect_type(data, dict, "$", issues):
        return issues

    required = (
        "id",
        "title",
        "language",
        "route",
        "prerequisites",
        "steps",
        "concepts",
        "next",
    )
    _require_keys(data, required, "$", issues)

    module_id = data.get("id")
    if not isinstance(module_id, str) or not ID_PATTERN.fullmatch(module_id):
        issues.append(
            ValidationIssue("$.id", "must contain only lowercase letters, digits, and hyphens")
        )

    for field in ("title", "language"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(ValidationIssue(f"$.{field}", "must be a non-empty string"))

    route = data.get("route")
    if _expect_type(route, dict, "$.route", issues):
        _require_keys(route, ("summary", "previous"), "$.route", issues)
        if not isinstance(route.get("summary"), str) or not route.get("summary", "").strip():
            issues.append(ValidationIssue("$.route.summary", "must be a non-empty string"))
        previous = route.get("previous")
        if _expect_type(previous, list, "$.route.previous", issues):
            for index, item in enumerate(previous):
                if not isinstance(item, str) or not item.strip():
                    issues.append(
                        ValidationIssue(f"$.route.previous[{index}]", "must be a non-empty string")
                    )

    prerequisites = data.get("prerequisites")
    concept_refs: list[tuple[str, str]] = []
    if _expect_type(prerequisites, list, "$.prerequisites", issues):
        for index, prerequisite in enumerate(prerequisites):
            path = f"$.prerequisites[{index}]"
            if not _expect_type(prerequisite, dict, path, issues):
                continue
            _require_keys(prerequisite, ("concept", "level", "summary"), path, issues)
            if prerequisite.get("level") not in {"required", "useful", "optional"}:
                issues.append(
                    ValidationIssue(f"{path}.level", "must be required, useful, or optional")
                )
            concept_ref = prerequisite.get("conceptRef")
            if concept_ref is not None:
                if isinstance(concept_ref, str) and concept_ref:
                    concept_refs.append((f"{path}.conceptRef", concept_ref))
                else:
                    issues.append(ValidationIssue(f"{path}.conceptRef", "must be a non-empty string"))

    visual = data.get("visual", {})
    visual_markup = ""
    visual_ids: set[str] = set()
    if _expect_type(visual, dict, "$.visual", issues):
        _require_keys(visual, ("type", "markup"), "$.visual", issues)
        if visual.get("type") not in {"svg", "html"}:
            issues.append(ValidationIssue("$.visual.type", "must be svg or html"))
        if isinstance(visual.get("markup"), str):
            visual_markup = visual["markup"]
            visual_ids = set(HTML_ID_PATTERN.findall(visual_markup))
        else:
            issues.append(ValidationIssue("$.visual.markup", "must be a string"))

    steps = data.get("steps")
    if _expect_type(steps, list, "$.steps", issues):
        if not steps:
            issues.append(ValidationIssue("$.steps", "must contain at least one step"))
        for index, step in enumerate(steps):
            path = f"$.steps[{index}]"
            if not _expect_type(step, dict, path, issues):
                continue
            _require_keys(step, ("title", "explanation", "goal", "observe", "quiz"), path, issues)
            for field in ("title", "explanation", "goal", "observe"):
                if not isinstance(step.get(field), str) or not step.get(field, "").strip():
                    issues.append(ValidationIssue(f"{path}.{field}", "must be a non-empty string"))
            _validate_quiz(step.get("quiz"), f"{path}.quiz", issues)
            for field in ("activeNodes", "animatedFlows"):
                refs = step.get(field, [])
                if not _expect_type(refs, list, f"{path}.{field}", issues):
                    continue
                for ref_index, ref in enumerate(refs):
                    ref_path = f"{path}.{field}[{ref_index}]"
                    if not isinstance(ref, str) or not ref:
                        issues.append(ValidationIssue(ref_path, "must be a non-empty string"))
                    elif ref not in visual_ids:
                        issues.append(
                            ValidationIssue(ref_path, f"visual element id '{ref}' does not exist")
                        )

    concepts = data.get("concepts")
    concept_ids: set[str] = set()
    if _expect_type(concepts, list, "$.concepts", issues):
        for index, concept in enumerate(concepts):
            path = f"$.concepts[{index}]"
            if not _expect_type(concept, dict, path, issues):
                continue
            _require_keys(concept, ("id", "label", "definition"), path, issues)
            concept_id = concept.get("id")
            if not isinstance(concept_id, str) or not ID_PATTERN.fullmatch(concept_id):
                issues.append(ValidationIssue(f"{path}.id", "must be a lowercase hyphenated id"))
            elif concept_id in concept_ids:
                issues.append(ValidationIssue(f"{path}.id", f"duplicate concept id '{concept_id}'"))
            else:
                concept_ids.add(concept_id)
            for field in ("label", "definition"):
                if not isinstance(concept.get(field), str) or not concept.get(field, "").strip():
                    issues.append(ValidationIssue(f"{path}.{field}", "must be a non-empty string"))

    for path, concept_ref in concept_refs:
        normalized_ref = concept_ref.removeprefix("concept-")
        if normalized_ref not in concept_ids:
            issues.append(ValidationIssue(path, f"unknown concept reference '{concept_ref}'"))

    next_section = data.get("next")
    if _expect_type(next_section, dict, "$.next", issues):
        _require_keys(next_section, ("summary", "items"), "$.next", issues)
        items = next_section.get("items")
        if _expect_type(items, list, "$.next.items", issues):
            if not items:
                issues.append(ValidationIssue("$.next.items", "must contain at least one next step"))

    # Check concept links included in authored HTML fragments.
    html_fragments: list[str] = [visual_markup]
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                html_fragments.extend(
                    value
                    for key in ("explanation", "goal", "observe")
                    if isinstance((value := step.get(key)), str)
                )
    for target in INTERNAL_HREF_PATTERN.findall("\n".join(html_fragments)):
        if target.startswith("concept-") and target.removeprefix("concept-") not in concept_ids:
            issues.append(ValidationIssue("$.steps", f"internal concept link '#{target}' has no card"))

    return issues


def validate_rendered_html(output: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    placeholders = sorted(set(PLACEHOLDER_PATTERN.findall(output)))
    for placeholder in placeholders:
        issues.append(ValidationIssue("output", f"unresolved placeholder {placeholder}"))

    html_ids = HTML_ID_PATTERN.findall(output)
    duplicate_ids = sorted({item for item in html_ids if html_ids.count(item) > 1})
    for duplicate_id in duplicate_ids:
        issues.append(ValidationIssue("output", f"duplicate HTML id '{duplicate_id}'"))

    id_set = set(html_ids)
    for target in sorted(set(INTERNAL_HREF_PATTERN.findall(output))):
        if target not in id_set:
            issues.append(ValidationIssue("output", f"broken internal reference '#{target}'"))

    if EXTERNAL_RESOURCE_PATTERN.search(output):
        issues.append(
            ValidationIssue(
                "output",
                "contains an external resource; generated modules must remain self-contained",
            )
        )
    if "window.RAIATEA_MODULE" not in output:
        issues.append(ValidationIssue("output", "embedded module data is missing"))
    if "<!doctype html>" not in output.lower():
        issues.append(ValidationIssue("output", "HTML doctype is missing"))
    return issues


def raise_for_issues(issues: Iterable[ValidationIssue]) -> None:
    collected = list(issues)
    if collected:
        raise ModuleValidationError(collected)


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
