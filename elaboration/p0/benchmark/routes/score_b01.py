"""Provider-neutral scoring helpers for the minimal B-01 PDF benchmark subset."""

from __future__ import annotations

from typing import Any


def _find_unique_block(
    observation: dict[str, Any], text: str
) -> tuple[dict[str, Any] | None, str]:
    matches = [
        block for block in observation.get("blocks", []) if block.get("text") == text
    ]
    if len(matches) == 1:
        return matches[0], "unique"
    if not matches:
        return None, "missing"
    return None, "ambiguous-duplicate-text"


def _bbox_inside(inner: list[float], outer: list[float]) -> bool:
    """Strict containment in the broad E-04 gold reference region.

    Current E-03/E-04 gold regions intentionally bound expected source regions
    rather than defining tight glyph rectangles. No universal IoU threshold is
    introduced here.
    """
    return (
        inner[0] >= outer[0]
        and inner[1] >= outer[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )


def _measure_coordinates(
    reference_units: list[dict[str, Any]],
    matched_blocks: dict[str, dict[str, Any]],
    match_states: dict[str, str],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    evidence_count = 0
    for unit in reference_units:
        expected_page = unit.get("page_index")
        expected_region = unit.get("region")
        if expected_page is None or expected_region is None:
            continue
        block = matched_blocks.get(unit["id"])
        observed_bbox = block.get("bbox_points_bottom_left") if block else None
        observed_page = block.get("page_index") if block else None
        has_geometry = observed_bbox is not None
        has_page = observed_page is not None
        if has_geometry:
            evidence_count += 1
        page_exact = has_page and observed_page == expected_page
        contained = (
            has_geometry
            and page_exact
            and _bbox_inside(observed_bbox, expected_region)
        )
        rows.append(
            {
                "reference_unit": unit.get("id"),
                "match_state": match_states.get(unit["id"], "missing"),
                "geometry_available": has_geometry,
                "page_available": has_page,
                "page_exact": page_exact if has_page else None,
                "bbox_inside_gold_region": contained if has_geometry and has_page else None,
                "expected_page_index": expected_page,
                "observed_page_index": observed_page,
                "gold_region_points_bottom_left": expected_region,
                "observed_bbox_points_bottom_left": observed_bbox,
            }
        )

    if not rows:
        return {
            "status": "not-applicable",
            "reason": "Gold contains no coordinate-bearing reference units for this fixture.",
            "units": [],
        }
    if evidence_count == 0:
        return {
            "status": "not-measured",
            "reason": (
                "The measured route exposes no source geometry for matched "
                "coordinate-bearing reference units; absence is not scored as zero fidelity."
            ),
            "geometry_evidence_count": 0,
            "expected_count": len(rows),
            "units": rows,
        }

    contained_count = sum(row["bbox_inside_gold_region"] is True for row in rows)
    status = "measured" if evidence_count == len(rows) else "partial"
    result = {
        "status": status,
        "comparison": (
            "page-exact plus strict containment of observed text bbox inside broad "
            "gold reference region; no universal IoU threshold"
        ),
        "geometry_evidence_count": evidence_count,
        "contained_count": contained_count,
        "expected_count": len(rows),
        "units": rows,
    }
    if status == "partial":
        result["reason"] = (
            "Only part of the matched reference set exposes source geometry; "
            "missing geometry remains unmeasured rather than being counted as failure."
        )
    return result


def _measure_hierarchy(
    reference_units: list[dict[str, Any]],
    matched_blocks: dict[str, dict[str, Any]],
    match_states: dict[str, str],
) -> dict[str, Any]:
    comparable = [
        unit for unit in reference_units if unit.get("type") in {"heading", "paragraph", "code", "list-item"}
    ]
    semantic_evidence = [
        unit
        for unit in comparable
        if matched_blocks.get(unit.get("id")) is not None
        and matched_blocks[unit["id"]].get("semantic_type") is not None
    ]
    if not semantic_evidence:
        return {
            "status": "not-measured",
            "reason": (
                "The measured route exposes no explicit Provider-neutral semantic "
                "type for matched reference units. Visual/font cues are never used "
                "as implicit hierarchy evidence."
            ),
            "semantic_evidence_count": 0,
            "expected_count": len(comparable),
            "units": [],
        }

    rows: list[dict[str, Any]] = []
    for unit in comparable:
        block = matched_blocks.get(unit.get("id"))
        observed_type = block.get("semantic_type") if block else None
        has_semantics = observed_type is not None
        expected_type = unit.get("type")
        type_exact = has_semantics and observed_type == expected_type
        rows.append(
            {
                "reference_unit": unit.get("id"),
                "match_state": match_states.get(unit.get("id"), "missing"),
                "semantic_evidence_available": has_semantics,
                "expected_type": expected_type,
                "observed_type": observed_type,
                "type_exact": type_exact if has_semantics else None,
                "observed_level": block.get("semantic_level") if block else None,
            }
        )

    status = "measured" if len(semantic_evidence) == len(comparable) else "partial"
    result = {
        "status": status,
        "semantic_evidence_count": len(semantic_evidence),
        "expected_count": len(comparable),
        "type_exact_count": sum(row["type_exact"] is True for row in rows),
        "units": rows,
    }
    if status == "partial":
        result["reason"] = (
            "Only part of the matched reference set exposes explicit semantic types; "
            "missing semantics remain unmeasured."
        )
    return result


def measure_b01_fixture(
    fixture_id: str,
    observation: dict[str, Any],
    gold_fixture: dict[str, Any],
) -> dict[str, Any]:
    """Measure current B-01 dimensions independently; never compute a total score."""
    reference_units = gold_fixture.get("reference_units", [])
    dimensions: dict[str, Any] = {}

    text_rows: list[dict[str, Any]] = []
    matched_blocks: dict[str, dict[str, Any]] = {}
    match_states: dict[str, str] = {}
    for unit in reference_units:
        block, match_state = _find_unique_block(observation, unit.get("text", ""))
        match_states[unit["id"]] = match_state
        if block is not None:
            matched_blocks[unit["id"]] = block
        text_rows.append(
            {
                "reference_unit": unit.get("id"),
                "match_state": match_state,
                "exact_text": block is not None,
            }
        )

    dimensions["content_text"] = {
        "status": "measured",
        "matched_units": sum(row["exact_text"] for row in text_rows),
        "expected_units": len(text_rows),
        "units": text_rows,
    }
    dimensions["source_coordinates"] = _measure_coordinates(
        reference_units, matched_blocks, match_states
    )

    text_by_id = {
        unit["id"]: unit.get("text")
        for unit in reference_units
        if unit.get("id") and unit.get("text")
    }
    relevant_texts = set(text_by_id.values())
    observed_sequence = [
        block.get("text")
        for block in observation.get("blocks", [])
        if block.get("text") in relevant_texts
    ]
    positions: dict[str, int] = {}
    duplicate_observed_texts: set[str] = set()
    for index, text in enumerate(observed_sequence):
        if text in positions:
            duplicate_observed_texts.add(text)
        else:
            positions[text] = index

    edge_rows = []
    for before_id, after_id in gold_fixture.get("reading_order", []):
        before_text = text_by_id.get(before_id)
        after_text = text_by_id.get(after_id)
        ambiguous = (
            before_text in duplicate_observed_texts or after_text in duplicate_observed_texts
        )
        satisfied = (
            not ambiguous
            and before_text in positions
            and after_text in positions
            and positions[before_text] < positions[after_text]
        )
        edge_rows.append(
            {
                "before": before_id,
                "after": after_id,
                "satisfied": satisfied,
                "ambiguous_duplicate_text": ambiguous,
            }
        )
    dimensions["reading_order"] = {
        "status": "measured",
        "satisfied_edges": sum(row["satisfied"] for row in edge_rows),
        "expected_edges": len(edge_rows),
        "observed_reference_text_sequence": observed_sequence,
        "edges": edge_rows,
    }

    dimensions["hierarchy"] = _measure_hierarchy(
        reference_units, matched_blocks, match_states
    )

    return {
        "fixture_id": fixture_id,
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "warnings": observation.get("warnings", []),
        "dimensions": dimensions,
        "duration_seconds": observation.get("duration_seconds"),
        "timing_semantics": "single-run-observation-not-performance-claim",
        "raw_output_sha256": observation.get("raw_output_sha256"),
        "raw_output_bytes": observation.get("raw_output_bytes"),
        "generated_files": observation.get("generated_files", []),
        "side_effect_files": observation.get("side_effect_files", []),
    }
