"""Provider-neutral B01-PDF-006 formula benchmark scoring.

Benchmark-only. Visible glyph preservation, source geometry, Provider grouping and
mathematical relations are independent dimensions. Typography/position never
creates superscript or fraction semantics.
"""
from __future__ import annotations
from typing import Any


def _compact(value: str) -> str:
    return "".join(value.split())


def _gold_formulas(gold: dict[str, Any]) -> list[dict[str, Any]]:
    value = gold.get("formulas")
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _surface_stream(observation: dict[str, Any]) -> str | None:
    blocks = observation.get("formula_text_blocks")
    if not isinstance(blocks, list):
        blocks = observation.get("blocks")
    if not isinstance(blocks, list):
        return None
    return _compact(
        " ".join(
            str(block.get("text", ""))
            for block in blocks
            if isinstance(block, dict)
        )
    )


def _expected_surface(formula: dict[str, Any]) -> str:
    tokens = formula.get("tokens") if isinstance(formula.get("tokens"), list) else []
    return _compact(
        "".join(str(token.get("text", "")) for token in tokens if isinstance(token, dict))
    )


def _formula_surface_content(
    gold: dict[str, Any], observation: dict[str, Any]
) -> dict[str, Any]:
    formulas = _gold_formulas(gold)
    stream = _surface_stream(observation)
    if stream is None:
        return {
            "status": "not-measured",
            "expected_count": len(formulas),
            "exact_once_count": 0,
            "formulas": [],
            "reason": "No comparable Provider text stream.",
        }
    rows = []
    for formula in formulas:
        expected = _expected_surface(formula)
        count = stream.count(expected) if expected else 0
        rows.append(
            {
                "formula_id": formula.get("id"),
                "expected_compact_surface": expected,
                "occurrences": count,
                "exact_once": count == 1,
            }
        )
    return {
        "status": "measured",
        "expected_count": len(rows),
        "exact_once_count": sum(row["exact_once"] for row in rows),
        "formulas": rows,
        "policy": (
            "whitespace-insensitive visible-glyph sequence only; no mathematical "
            "semantics inferred"
        ),
    }


def _display_order(gold: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    formulas = _gold_formulas(gold)
    stream = _surface_stream(observation)
    if stream is None:
        return {
            "status": "not-measured",
            "expected_edges": max(0, len(formulas) - 1),
            "satisfied_edges": 0,
            "reason": "No comparable Provider text stream.",
        }

    positions: dict[str, int] = {}
    ambiguous: list[str] = []
    for formula in formulas:
        expected = _expected_surface(formula)
        first = stream.find(expected)
        last = stream.rfind(expected)
        formula_id = str(formula.get("id"))
        if first >= 0 and first == last:
            positions[formula_id] = first
        else:
            ambiguous.append(formula_id)

    order = (
        gold.get("formula_display_order")
        if isinstance(gold.get("formula_display_order"), list)
        else [formula.get("id") for formula in formulas]
    )
    edges = []
    for before, after in zip(order, order[1:]):
        satisfied = (
            str(before) in positions
            and str(after) in positions
            and positions[str(before)] < positions[str(after)]
        )
        edges.append({"before": before, "after": after, "satisfied": satisfied})
    return {
        "status": "measured" if not ambiguous else "partial",
        "expected_edges": len(edges),
        "satisfied_edges": sum(row["satisfied"] for row in edges),
        "edges": edges,
        "ambiguous_or_missing_formulas": ambiguous,
        "policy": "order of uniquely preserved compact glyph sequences only",
    }


def _bbox_errors(observed: list[float], expected: list[float]) -> dict[str, Any]:
    signed = [float(observed[index]) - float(expected[index]) for index in range(4)]
    absolute = [abs(value) for value in signed]
    return {
        "signed_edge_error_points": signed,
        "absolute_edge_error_points": absolute,
        "max_absolute_edge_error_points": max(absolute),
        "bbox_exact": all(value == 0.0 for value in absolute),
    }


def _center_in(box: list[float], region: list[float]) -> bool:
    center_x = (float(box[0]) + float(box[2])) / 2
    center_y = (float(box[1]) + float(box[3])) / 2
    return (
        float(region[0]) <= center_x <= float(region[2])
        and float(region[1]) <= center_y <= float(region[3])
    )


def _token_geometry(gold: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    blocks = observation.get("formula_text_blocks")
    if not isinstance(blocks, list):
        blocks = observation.get("blocks")
    formulas = _gold_formulas(gold)
    tokens = [
        (formula, token)
        for formula in formulas
        for token in (formula.get("tokens") or [])
        if isinstance(token, dict)
    ]
    if not isinstance(blocks, list):
        return {
            "status": "not-measured",
            "expected_count": len(tokens),
            "evidence_count": 0,
            "tokens": [],
            "reason": "No Provider text blocks.",
        }

    rows = []
    for formula, token in tokens:
        text = _compact(str(token.get("text", "")))
        region = token.get("region")
        page = formula.get("page_index")
        candidates = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if _compact(str(block.get("text", ""))) != text:
                continue
            bbox = block.get("bbox_points_bottom_left")
            if (
                block.get("page_index") != page
                or not isinstance(bbox, list)
                or len(bbox) != 4
            ):
                continue
            if isinstance(region, list) and len(region) == 4 and _center_in(bbox, region):
                candidates.append(block)

        if len(candidates) == 1 and isinstance(region, list) and len(region) == 4:
            observed_bbox = candidates[0]["bbox_points_bottom_left"]
            rows.append(
                {
                    "token_id": token.get("id"),
                    "formula_id": formula.get("id"),
                    "text": token.get("text"),
                    "evidence_available": True,
                    "observed_bbox_points_bottom_left": observed_bbox,
                    "expected_bbox_points_bottom_left": region,
                    **_bbox_errors(observed_bbox, region),
                }
            )
        else:
            rows.append(
                {
                    "token_id": token.get("id"),
                    "formula_id": formula.get("id"),
                    "text": token.get("text"),
                    "evidence_available": False,
                    "candidate_count": len(candidates),
                }
            )

    evidence_count = sum(row["evidence_available"] for row in rows)
    errors = [
        row["max_absolute_edge_error_points"]
        for row in rows
        if row["evidence_available"]
    ]
    return {
        "status": (
            "measured"
            if evidence_count == len(rows)
            else "partial"
            if evidence_count
            else "not-measured"
        ),
        "expected_count": len(rows),
        "evidence_count": evidence_count,
        "bbox_exact_count": sum(row.get("bbox_exact") is True for row in rows),
        "max_observed_edge_error_points": max(errors) if errors else None,
        "tokens": rows,
        "policy": (
            "geometry binds only already-explicit exact glyph blocks; geometry never "
            "creates superscript/fraction semantics"
        ),
    }


def _explicit_math(gold: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    expected = []
    for formula in _gold_formulas(gold):
        relations = formula.get("relations") if isinstance(formula.get("relations"), list) else []
        for relation in relations:
            if isinstance(relation, dict):
                expected.append((formula.get("id"), relation))

    observed = observation.get("math_relations")
    if not isinstance(observed, list):
        return {
            "status": "not-measured",
            "expected_count": len(expected),
            "evidence_count": 0,
            "exact_count": 0,
            "relations": [],
            "reason": (
                "The measured route exposes no explicit mathematical relation collection; "
                "typography, vertical offset and drawn lines are deliberately ignored."
            ),
            "visual_inference": False,
        }

    rows = []
    for formula_id, relation in expected:
        matches = [
            item
            for item in observed
            if isinstance(item, dict)
            and item.get("formula_id") == formula_id
            and item.get("kind") == relation.get("kind")
            and item.get("gold_relation_key") == relation
        ]
        rows.append(
            {
                "formula_id": formula_id,
                "kind": relation.get("kind"),
                "explicit_candidate_count": len(matches),
                "exact": len(matches) == 1,
            }
        )
    evidence_count = sum(row["explicit_candidate_count"] > 0 for row in rows)
    return {
        "status": (
            "measured"
            if evidence_count == len(rows)
            else "partial"
            if evidence_count
            else "not-measured"
        ),
        "expected_count": len(rows),
        "evidence_count": evidence_count,
        "exact_count": sum(row["exact"] for row in rows),
        "relations": rows,
        "visual_inference": False,
    }


def _provider_group_diagnostic(observation: dict[str, Any]) -> dict[str, Any]:
    groups = observation.get("provider_formula_groups")
    if not isinstance(groups, list):
        return {"status": "not-measured", "observed_count": None, "groups": []}
    return {
        "status": "observed-nonsemantic",
        "observed_count": len(groups),
        "groups": groups,
        "policy": (
            "Provider grouping is retained diagnostically but is not promoted to formula "
            "semantics unless the Provider labels/encodes it explicitly as mathematics"
        ),
    }


def measure_b01_formula_dimensions(
    observation: dict[str, Any], gold_fixture: dict[str, Any]
) -> dict[str, Any]:
    return {
        "formula_surface_content": _formula_surface_content(gold_fixture, observation),
        "formula_display_order": _display_order(gold_fixture, observation),
        "token_geometry": _token_geometry(gold_fixture, observation),
        "explicit_math_relations": _explicit_math(gold_fixture, observation),
        "provider_group_diagnostic": _provider_group_diagnostic(observation),
    }
