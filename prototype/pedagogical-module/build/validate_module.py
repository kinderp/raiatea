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
PRIMITIVE_KINDS = {
    "box",
    "vector",
    "token-row",
    "matrix",
    "weighted-sum",
    "text",
    "edge",
}
PRIMITIVE_TONES = {"neutral", "input", "process", "attention", "output", "warning"}


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


def _expect_type(value: Any, expected: type | tuple[type, ...], path: str, issues: list[ValidationIssue]) -> bool:
    if not isinstance(value, expected):
        name = ", ".join(t.__name__ for t in expected) if isinstance(expected, tuple) else expected.__name__
        issues.append(ValidationIssue(path, f"expected {name}"))
        return False
    return True


def _require_keys(obj: dict[str, Any], keys: Iterable[str], path: str, issues: list[ValidationIssue]) -> None:
    for key in keys:
        if key not in obj:
            issues.append(ValidationIssue(f"{path}.{key}", "required field is missing"))


def _non_empty_string(value: Any, path: str, issues: list[ValidationIssue]) -> bool:
    if not isinstance(value, str) or not value.strip():
        issues.append(ValidationIssue(path, "must be a non-empty string"))
        return False
    return True


def _valid_identifier(value: Any, path: str, issues: list[ValidationIssue]) -> bool:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        issues.append(ValidationIssue(path, "must contain only lowercase letters, digits, and hyphens"))
        return False
    return True


def _number(value: Any, path: str, issues: list[ValidationIssue]) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        issues.append(ValidationIssue(path, "must be a number"))
        return False
    return True


def _positive_number(value: Any, path: str, issues: list[ValidationIssue]) -> bool:
    if not _number(value, path, issues):
        return False
    if value <= 0:
        issues.append(ValidationIssue(path, "must be a positive number"))
        return False
    return True


def _validate_quiz(quiz: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not _expect_type(quiz, dict, path, issues):
        return
    required = ("question", "answers", "correctIndex", "correctFeedback", "incorrectFeedback")
    _require_keys(quiz, required, path, issues)
    for field in ("question", "correctFeedback", "incorrectFeedback"):
        _non_empty_string(quiz.get(field), f"{path}.{field}", issues)
    answers = quiz.get("answers")
    if _expect_type(answers, list, f"{path}.answers", issues):
        if len(answers) < 2:
            issues.append(ValidationIssue(f"{path}.answers", "must contain at least two answers"))
        for index, answer in enumerate(answers):
            _non_empty_string(answer, f"{path}.answers[{index}]", issues)
    correct_index = quiz.get("correctIndex")
    if not isinstance(correct_index, int) or isinstance(correct_index, bool):
        issues.append(ValidationIssue(f"{path}.correctIndex", "must be an integer"))
    elif isinstance(answers, list) and not 0 <= correct_index < len(answers):
        issues.append(
            ValidationIssue(
                f"{path}.correctIndex",
                f"must refer to an answer between 0 and {max(len(answers) - 1, 0)}",
            )
        )


def _validate_tone(primitive: dict[str, Any], path: str, issues: list[ValidationIssue]) -> None:
    if "tone" in primitive and primitive["tone"] not in PRIMITIVE_TONES:
        issues.append(ValidationIssue(f"{path}.tone", f"must be one of {sorted(PRIMITIVE_TONES)}"))


def _validate_coordinates(primitive: dict[str, Any], path: str, issues: list[ValidationIssue]) -> None:
    for coordinate in ("x", "y"):
        _number(primitive.get(coordinate), f"{path}.{coordinate}", issues)


def _validate_matrix(values: Any, path: str, issues: list[ValidationIssue]) -> tuple[int, int]:
    if not _expect_type(values, list, path, issues) or not values:
        issues.append(ValidationIssue(path, "must contain at least one row"))
        return 0, 0
    expected_columns: int | None = None
    for row_index, row in enumerate(values):
        row_path = f"{path}[{row_index}]"
        if not _expect_type(row, list, row_path, issues) or not row:
            issues.append(ValidationIssue(row_path, "must contain at least one value"))
            continue
        if expected_columns is None:
            expected_columns = len(row)
        elif len(row) != expected_columns:
            issues.append(ValidationIssue(row_path, "all matrix rows must have the same length"))
    return len(values), expected_columns or 0


def _validate_primitive(
    primitive: Any,
    path: str,
    issues: list[ValidationIssue],
    primitive_ids: set[str],
    primitive_kinds: dict[str, str],
) -> None:
    if not _expect_type(primitive, dict, path, issues):
        return
    _require_keys(primitive, ("kind", "id"), path, issues)
    kind = primitive.get("kind")
    if kind not in PRIMITIVE_KINDS:
        issues.append(ValidationIssue(f"{path}.kind", f"must be one of {sorted(PRIMITIVE_KINDS)}"))
        return
    primitive_id = primitive.get("id")
    if _valid_identifier(primitive_id, f"{path}.id", issues):
        if primitive_id in primitive_ids:
            issues.append(ValidationIssue(f"{path}.id", f"duplicate primitive id '{primitive_id}'"))
        else:
            primitive_ids.add(primitive_id)
            primitive_kinds[primitive_id] = kind

    if kind != "edge":
        _require_keys(primitive, ("x", "y"), path, issues)
        _validate_coordinates(primitive, path, issues)

    if kind == "box":
        _require_keys(primitive, ("title",), path, issues)
        _non_empty_string(primitive.get("title"), f"{path}.title", issues)
        for field in ("width", "height"):
            if field in primitive:
                _positive_number(primitive[field], f"{path}.{field}", issues)
        _validate_tone(primitive, path, issues)

    elif kind == "vector":
        _require_keys(primitive, ("values",), path, issues)
        values = primitive.get("values")
        if _expect_type(values, list, f"{path}.values", issues) and not values:
            issues.append(ValidationIssue(f"{path}.values", "must contain at least one value"))
        if "cellWidth" in primitive:
            _positive_number(primitive["cellWidth"], f"{path}.cellWidth", issues)
        _validate_tone(primitive, path, issues)

    elif kind == "token-row":
        _require_keys(primitive, ("tokens",), path, issues)
        tokens = primitive.get("tokens")
        if _expect_type(tokens, list, f"{path}.tokens", issues):
            if not tokens:
                issues.append(ValidationIssue(f"{path}.tokens", "must contain at least one token"))
            for index, token in enumerate(tokens):
                _non_empty_string(token, f"{path}.tokens[{index}]", issues)
        active_index = primitive.get("activeIndex")
        if active_index is not None:
            if not isinstance(active_index, int) or isinstance(active_index, bool):
                issues.append(ValidationIssue(f"{path}.activeIndex", "must be an integer"))
            elif isinstance(tokens, list) and not 0 <= active_index < len(tokens):
                issues.append(ValidationIssue(f"{path}.activeIndex", "must refer to an existing token"))
        if "cellWidth" in primitive:
            _positive_number(primitive["cellWidth"], f"{path}.cellWidth", issues)

    elif kind == "matrix":
        _require_keys(primitive, ("values",), path, issues)
        rows, columns = _validate_matrix(primitive.get("values"), f"{path}.values", issues)
        for field, expected in (("rowLabels", rows), ("columnLabels", columns)):
            labels = primitive.get(field)
            if labels is not None:
                if _expect_type(labels, list, f"{path}.{field}", issues):
                    if len(labels) != expected:
                        issues.append(ValidationIssue(f"{path}.{field}", f"must contain {expected} labels"))
                    for index, label in enumerate(labels):
                        _non_empty_string(label, f"{path}.{field}[{index}]", issues)
        for field, limit in (("highlightRow", rows), ("highlightColumn", columns)):
            value = primitive.get(field)
            if value is not None:
                if not isinstance(value, int) or isinstance(value, bool):
                    issues.append(ValidationIssue(f"{path}.{field}", "must be an integer"))
                elif not 0 <= value < limit:
                    issues.append(ValidationIssue(f"{path}.{field}", "must refer to an existing matrix index"))
        for field in ("cellWidth", "cellHeight"):
            if field in primitive:
                _positive_number(primitive[field], f"{path}.{field}", issues)
        _validate_tone(primitive, path, issues)

    elif kind == "weighted-sum":
        _require_keys(primitive, ("terms", "result"), path, issues)
        terms = primitive.get("terms")
        if _expect_type(terms, list, f"{path}.terms", issues):
            if not terms:
                issues.append(ValidationIssue(f"{path}.terms", "must contain at least one term"))
            for index, term in enumerate(terms):
                term_path = f"{path}.terms[{index}]"
                if not _expect_type(term, dict, term_path, issues):
                    continue
                _require_keys(term, ("weight", "label"), term_path, issues)
                _non_empty_string(term.get("label"), f"{term_path}.label", issues)
        result = primitive.get("result")
        if _expect_type(result, list, f"{path}.result", issues) and not result:
            issues.append(ValidationIssue(f"{path}.result", "must contain at least one value"))
        _validate_tone(primitive, path, issues)

    elif kind == "text":
        _require_keys(primitive, ("text",), path, issues)
        _non_empty_string(primitive.get("text"), f"{path}.text", issues)

    elif kind == "edge":
        _require_keys(primitive, ("path",), path, issues)
        _non_empty_string(primitive.get("path"), f"{path}.path", issues)
        for coordinate in ("labelX", "labelY"):
            if coordinate in primitive:
                _number(primitive[coordinate], f"{path}.{coordinate}", issues)


def _validate_visual(visual: Any, issues: list[ValidationIssue]) -> tuple[str, set[str], dict[str, str]]:
    visual_markup = ""
    visual_ids: set[str] = set()
    primitive_kinds: dict[str, str] = {}
    if not _expect_type(visual, dict, "$.visual", issues):
        return visual_markup, visual_ids, primitive_kinds
    _require_keys(visual, ("type",), "$.visual", issues)
    visual_type = visual.get("type")
    if visual_type in {"svg", "html"}:
        _require_keys(visual, ("markup",), "$.visual", issues)
        markup = visual.get("markup")
        if isinstance(markup, str) and markup.strip():
            visual_markup = markup
            visual_ids = set(HTML_ID_PATTERN.findall(markup))
        else:
            issues.append(ValidationIssue("$.visual.markup", "must be a non-empty string"))
    elif visual_type == "primitives":
        for dimension in ("width", "height"):
            if dimension in visual:
                _positive_number(visual[dimension], f"$.visual.{dimension}", issues)
        items = visual.get("items")
        if not _expect_type(items, list, "$.visual.items", issues):
            return visual_markup, visual_ids, primitive_kinds
        if not items:
            issues.append(ValidationIssue("$.visual.items", "must contain at least one primitive"))
        for index, primitive in enumerate(items):
            _validate_primitive(primitive, f"$.visual.items[{index}]", issues, visual_ids, primitive_kinds)
    else:
        issues.append(ValidationIssue("$.visual.type", "must be svg, html, or primitives"))
    return visual_markup, visual_ids, primitive_kinds


def validate_module(data: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _expect_type(data, dict, "$", issues):
        return issues
    required = ("id", "title", "language", "route", "prerequisites", "visual", "steps", "concepts", "next")
    _require_keys(data, required, "$", issues)
    _valid_identifier(data.get("id"), "$.id", issues)
    for field in ("title", "language"):
        _non_empty_string(data.get(field), f"$.{field}", issues)

    route = data.get("route")
    if _expect_type(route, dict, "$.route", issues):
        _require_keys(route, ("summary", "previous"), "$.route", issues)
        _non_empty_string(route.get("summary"), "$.route.summary", issues)
        previous = route.get("previous")
        if _expect_type(previous, list, "$.route.previous", issues):
            for index, item in enumerate(previous):
                _non_empty_string(item, f"$.route.previous[{index}]", issues)

    prerequisites = data.get("prerequisites")
    concept_refs: list[tuple[str, str]] = []
    if _expect_type(prerequisites, list, "$.prerequisites", issues):
        for index, prerequisite in enumerate(prerequisites):
            path = f"$.prerequisites[{index}]"
            if not _expect_type(prerequisite, dict, path, issues):
                continue
            _require_keys(prerequisite, ("concept", "level", "summary"), path, issues)
            _non_empty_string(prerequisite.get("concept"), f"{path}.concept", issues)
            _non_empty_string(prerequisite.get("summary"), f"{path}.summary", issues)
            if prerequisite.get("level") not in {"required", "useful", "optional"}:
                issues.append(ValidationIssue(f"{path}.level", "must be required, useful, or optional"))
            concept_ref = prerequisite.get("conceptRef")
            if concept_ref is not None:
                if isinstance(concept_ref, str) and concept_ref:
                    concept_refs.append((f"{path}.conceptRef", concept_ref))
                else:
                    issues.append(ValidationIssue(f"{path}.conceptRef", "must be a non-empty string"))

    visual_markup, visual_ids, primitive_kinds = _validate_visual(data.get("visual"), issues)

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
                _non_empty_string(step.get(field), f"{path}.{field}", issues)
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
                        issues.append(ValidationIssue(ref_path, f"visual element id '{ref}' does not exist"))
                    elif field == "animatedFlows" and primitive_kinds and primitive_kinds.get(ref) != "edge":
                        issues.append(ValidationIssue(ref_path, "animatedFlows may reference only edge primitives"))

    concepts = data.get("concepts")
    concept_ids: set[str] = set()
    if _expect_type(concepts, list, "$.concepts", issues):
        for index, concept in enumerate(concepts):
            path = f"$.concepts[{index}]"
            if not _expect_type(concept, dict, path, issues):
                continue
            _require_keys(concept, ("id", "label", "definition"), path, issues)
            concept_id = concept.get("id")
            if _valid_identifier(concept_id, f"{path}.id", issues):
                if concept_id in concept_ids:
                    issues.append(ValidationIssue(f"{path}.id", f"duplicate concept id '{concept_id}'"))
                else:
                    concept_ids.add(concept_id)
            for field in ("label", "definition"):
                _non_empty_string(concept.get(field), f"{path}.{field}", issues)

    for path, concept_ref in concept_refs:
        normalized_ref = concept_ref.removeprefix("concept-")
        if normalized_ref not in concept_ids:
            issues.append(ValidationIssue(path, f"unknown concept reference '{concept_ref}'"))

    next_section = data.get("next")
    if _expect_type(next_section, dict, "$.next", issues):
        _require_keys(next_section, ("summary", "items"), "$.next", issues)
        _non_empty_string(next_section.get("summary"), "$.next.summary", issues)
        items = next_section.get("items")
        if _expect_type(items, list, "$.next.items", issues):
            if not items:
                issues.append(ValidationIssue("$.next.items", "must contain at least one next step"))
            for index, item in enumerate(items):
                _non_empty_string(item, f"$.next.items[{index}]", issues)

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
    for placeholder in sorted(set(PLACEHOLDER_PATTERN.findall(output))):
        issues.append(ValidationIssue("output", f"unresolved placeholder {placeholder}"))
    html_ids = HTML_ID_PATTERN.findall(output)
    for duplicate_id in sorted({item for item in html_ids if html_ids.count(item) > 1}):
        issues.append(ValidationIssue("output", f"duplicate HTML id '{duplicate_id}'"))
    id_set = set(html_ids)
    for target in sorted(set(INTERNAL_HREF_PATTERN.findall(output))):
        if target not in id_set:
            issues.append(ValidationIssue("output", f"broken internal reference '#{target}'"))
    if EXTERNAL_RESOURCE_PATTERN.search(output):
        issues.append(ValidationIssue("output", "contains an external resource; generated modules must remain self-contained"))
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
