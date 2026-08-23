"""Provider-neutral B01-PDF-006 formula benchmark scoring.

Benchmark-only. Visible glyph preservation, source geometry, Provider grouping and
mathematical relations are independent dimensions. Typography/position never
creates superscript or fraction semantics.
"""
from __future__ import annotations
from typing import Any


_COLLECTION_STATES = {"measured", "partial", "not-measured"}


def _compact(value: str) -> str:
    return "".join(value.split())


def _gold_formulas(gold: dict[str, Any]) -> list[dict[str, Any]]:
    value = gold.get("formulas")
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _text_blocks_and_state(
    observation: dict[str, Any],
) -> tuple[list[dict[str, Any]] | None, str]:
    if "formula_text_blocks" in observation:
        blocks = observation.get("formula_text_blocks")
        state = observation.get("formula_text_collection_state")
        if state not in _COLLECTION_STATES:
            state = "measured" if isinstance(blocks, list) else "not-measured"
    else:
        blocks = observation.get("blocks")
        state = "measured" if isinstance(blocks, list) else "not-measured"

    if state == "not-measured" or not isinstance(blocks, list):
        return None, "not-measured"
    if any(not isinstance(block, dict) for block in blocks):
        state = "partial"
    return [block for block in blocks if isinstance(block, dict)], str(state)


def _surface_stream(observation: dict[str, Any]) -> tuple[str | None, str]:
    blocks, state = _text_blocks_and_state(observation)
    if blocks is None:
        return None, state
    return _compact(" ".join(str(block.get("text", "")) for block in blocks)), state


def _expected_surface(formula: dict[str, Any]) -> str:
    tokens = formula.get("tokens") if isinstance(formula.get("tokens"), list) else []
    return _compact(
        "".join(str(token.get("text", "")) for token in tokens if isinstance(token, dict))
    )


def _formula_surface_content(
    gold: dict[str, Any], observation: dict[str, Any]
) -> dict[str, Any]:
    formulas = _gold_formulas(gold)
    stream, collection_state = _surface_stream(observation)
    if stream is None:
        return {
            "status": "not-measured",
            "expected_count": len(formulas),
            "exact_once_count": 0,
            "formulas": [],
            "reason": "No trustworthy comparable Provider text collection.",
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
        "status": "partial" if collection_state == "partial" else "measured",
        "collection_state": collection_state,
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
    stream, collection_state = _surface_stream(observation)
    if stream is None:
        return {
            "status": "not-measured",
            "expected_edges": max(0, len(formulas) - 1),
            "satisfied_edges": 0,
            "reason": "No trustworthy comparable Provider text collection.",
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
        "status": (
            "partial"
            if collection_state == "partial" or ambiguous
            else "measured"
        ),
        "collection_state": collection_state,
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
    blocks, collection_state = _text_blocks_and_state(observation)
    formulas = _gold_formulas(gold)
    tokens = [
        (formula, token)
        for formula in formulas
        for token in (formula.get("tokens") or [])
        if isinstance(token, dict)
    ]
    if blocks is None:
        return {
            "status": "not-measured",
            "expected_count": len(tokens),
            "evidence_count": 0,
            "tokens": [],
            "reason": "No trustworthy Provider text-block collection.",
        }

    rows = []
    for formula, token in tokens:
        text = _compact(str(token.get("text", "")))
        region = token.get("region")
        page = formula.get("page_index")
        candidates = []
        for block in blocks:
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
    derived_status = (
        "measured"
        if evidence_count == len(rows)
        else "partial"
        if evidence_count
        else "not-measured"
    )
    if collection_state == "partial" and derived_status == "measured":
        derived_status = "partial"
    return {
        "status": derived_status,
        "collection_state": collection_state,
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


def _relation_signature(formula_id: Any, relation: dict[str, Any]) -> tuple[Any, ...] | None:
    kind = relation.get("kind")
    if kind == "superscript":
        return (
            formula_id,
            kind,
            relation.get("base_token"),
            relation.get("script_token"),
        )
    if kind == "fraction":
        numerator = relation.get("numerator_tokens")
        denominator = relation.get("denominator_tokens")
        if not isinstance(numerator, list) or not isinstance(denominator, list):
            return None
        return (formula_id, kind, tuple(numerator), tuple(denominator))
    return None


def _explicit_math(gold: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    expected: list[tuple[Any, dict[str, Any]]] = []
    for formula in _gold_formulas(gold):
        relations = formula.get("relations") if isinstance(formula.get("relations"), list) else []
        for relation in relations:
            if isinstance(relation, dict):
                expected.append((formula.get("id"), relation))

    observed = observation.get("math_relations")
    collection_state = observation.get("math_relation_collection_state")
    if collection_state not in _COLLECTION_STATES:
        collection_state = "measured" if isinstance(observed, list) else "not-measured"

    if collection_state == "not-measured" or not isinstance(observed, list):
        return {
            "status": "not-measured",
            "expected_count": len(expected),
            "observed_count": None,
            "evidence_count": 0,
            "exact_count": 0,
            "relations": [],
            "reason": (
                "The measured route exposes no explicit mathematical relation collection; "
                "typography, vertical offset and drawn lines are deliberately ignored."
            ),
            "visual_inference": False,
        }

    attributable_observed: list[dict[str, Any]] = []
    observed_signatures: list[tuple[Any, ...] | None] = []
    malformed_observed_count = 0
    for item in observed:
        if (
            not isinstance(item, dict)
            or not item.get("provider_relation_source")
            or item.get("formula_id") is None
            or not isinstance(item.get("kind"), str)
        ):
            malformed_observed_count += 1
            continue
        signature = _relation_signature(item.get("formula_id"), item)
        if item.get("kind") in {"superscript", "fraction"} and signature is None:
            malformed_observed_count += 1
            continue
        attributable_observed.append(item)
        observed_signatures.append(signature)

    effective_collection_state = (
        "partial"
        if collection_state == "partial" or malformed_observed_count
        else "measured"
    )

    rows = []
    matched_observed_indexes: set[int] = set()
    for formula_id, relation in expected:
        expected_signature = _relation_signature(formula_id, relation)
        matching_indexes = [
            index
            for index, signature in enumerate(observed_signatures)
            if signature is not None and signature == expected_signature
        ]
        matched_observed_indexes.update(matching_indexes)
        rows.append(
            {
                "formula_id": formula_id,
                "kind": relation.get("kind"),
                "explicit_candidate_count": len(matching_indexes),
                "exact": len(matching_indexes) == 1,
            }
        )

    evidence_count = sum(row["explicit_candidate_count"] > 0 for row in rows)
    exact_count = sum(row["exact"] for row in rows)
    ambiguous_count = sum(row["explicit_candidate_count"] > 1 for row in rows)
    unmatched_observed_count = len(attributable_observed) - len(matched_observed_indexes)

    if effective_collection_state == "partial":
        status = "partial"
    elif exact_count == len(rows) and ambiguous_count == 0:
        status = "measured"
    elif evidence_count:
        status = "partial"
    else:
        # A trustworthy explicit empty or mismatching relation collection is still
        # measured evidence; it must not collapse into "not-measured".
        status = "measured"

    return {
        "status": status,
        "collection_state": effective_collection_state,
        "expected_count": len(rows),
        "observed_count": len(attributable_observed),
        "evidence_count": evidence_count,
        "exact_count": exact_count,
        "ambiguous_expected_count": ambiguous_count,
        "unmatched_observed_count": unmatched_observed_count,
        "malformed_observed_count": malformed_observed_count,
        "explicit_empty": len(observed) == 0,
        "relations": rows,
        "visual_inference": False,
        "policy": (
            "only Provider-attributed explicit relation fields are compared; "
            "authored geometry and visual layout never create math semantics"
        ),
    }


def _provider_group_diagnostic(observation: dict[str, Any]) -> dict[str, Any]:
    groups = observation.get("provider_formula_groups")
    collection_state = observation.get("provider_group_collection_state")
    if collection_state not in _COLLECTION_STATES:
        collection_state = "measured" if isinstance(groups, list) else "not-measured"

    if collection_state == "not-measured" or not isinstance(groups, list):
        return {
            "status": "not-measured",
            "collection_state": "not-measured",
            "observed_count": None,
            "groups": [],
        }

    malformed_group_count = sum(not isinstance(group, dict) for group in groups)
    if malformed_group_count:
        collection_state = "partial"
    valid_groups = [group for group in groups if isinstance(group, dict)]

    return {
        "status": "partial" if collection_state == "partial" else "observed-nonsemantic",
        "collection_state": collection_state,
        "semantic_interpretation": "nonsemantic",
        "observed_count": len(valid_groups),
        "malformed_group_count": malformed_group_count,
        "groups": valid_groups,
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
