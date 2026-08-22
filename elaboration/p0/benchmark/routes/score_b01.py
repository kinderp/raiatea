"""Provider-neutral scoring helpers for the minimal B-01 PDF benchmark subset."""

from __future__ import annotations

from typing import Any


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _align_reference_units(
    observation: dict[str, Any],
    reference_units: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, tuple[int, int]],
]:
    """Align reference text to Provider blocks without Provider-specific rules.

    Exact block equality is preferred. If segmentation differs, a reference unit
    may align to one unique exact substring inside one Provider block. Ambiguous
    repeated occurrences are never guessed. Positions are ``(block_index,
    character_offset)`` so reading order can still be evaluated when a Provider
    merges several reference units into one block.
    """
    blocks = observation.get("blocks", [])
    normalized_blocks = [
        _normalize_text(str(block.get("text", ""))) for block in blocks
    ]
    matched: dict[str, dict[str, Any]] = {}
    states: dict[str, str] = {}
    positions: dict[str, tuple[int, int]] = {}

    for unit in reference_units:
        unit_id = unit.get("id")
        if not unit_id:
            continue
        needle = _normalize_text(str(unit.get("text", "")))
        if not needle:
            states[unit_id] = "missing-reference-text"
            continue

        exact = [index for index, value in enumerate(normalized_blocks) if value == needle]
        if len(exact) == 1:
            index = exact[0]
            matched[unit_id] = blocks[index]
            states[unit_id] = "exact-block"
            positions[unit_id] = (index, 0)
            continue
        if len(exact) > 1:
            states[unit_id] = "ambiguous-duplicate-text"
            continue

        occurrences: list[tuple[int, int]] = []
        for index, value in enumerate(normalized_blocks):
            start = 0
            while True:
                offset = value.find(needle, start)
                if offset < 0:
                    break
                occurrences.append((index, offset))
                start = offset + max(1, len(needle))
        if len(occurrences) == 1:
            index, offset = occurrences[0]
            matched[unit_id] = blocks[index]
            states[unit_id] = "substring-in-provider-block"
            positions[unit_id] = (index, offset)
        elif not occurrences:
            states[unit_id] = "missing"
        else:
            states[unit_id] = "ambiguous-substring"

    return matched, states, positions


def _bbox_inside(inner: list[float], outer: list[float]) -> bool:
    """Strict containment in the broad E-04 gold reference region."""
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
    provider_geometry_count = 0
    for unit in reference_units:
        unit_id = unit.get("id")
        expected_page = unit.get("page_index")
        expected_region = unit.get("region")
        if expected_page is None or expected_region is None:
            continue
        block = matched_blocks.get(unit_id)
        state = match_states.get(unit_id, "missing")
        observed_bbox = block.get("bbox_points_bottom_left") if block else None
        observed_page = block.get("page_index") if block else None
        provider_has_geometry = observed_bbox is not None
        if provider_has_geometry:
            provider_geometry_count += 1

        # A bbox attached to an aggregate Provider block is not unit-specific
        # geometry. Preserve it as observable Provider evidence but do not award
        # coordinate fidelity to each substring aligned inside that block.
        unit_geometry = provider_has_geometry and state == "exact-block"
        has_page = observed_page is not None
        if unit_geometry:
            evidence_count += 1
        page_exact = has_page and observed_page == expected_page
        contained = (
            unit_geometry
            and page_exact
            and _bbox_inside(observed_bbox, expected_region)
        )
        rows.append(
            {
                "reference_unit": unit_id,
                "match_state": state,
                "provider_geometry_available": provider_has_geometry,
                "unit_geometry_attributable": unit_geometry,
                "page_available": has_page,
                "page_exact": page_exact if has_page else None,
                "bbox_inside_gold_region": contained if unit_geometry and has_page else None,
                "expected_page_index": expected_page,
                "observed_page_index": observed_page,
                "gold_region_points_bottom_left": expected_region,
                "observed_provider_bbox_points_bottom_left": observed_bbox,
            }
        )

    if not rows:
        return {
            "status": "not-applicable",
            "reason": "Gold contains no coordinate-bearing reference units for this fixture.",
            "units": [],
        }
    if evidence_count == 0:
        reason = (
            "The measured route exposes no source geometry attributable to individual "
            "matched reference units; absence or aggregate-block geometry is not scored "
            "as zero fidelity."
        )
        return {
            "status": "not-measured",
            "reason": reason,
            "geometry_evidence_count": 0,
            "provider_geometry_observed_count": provider_geometry_count,
            "expected_count": len(rows),
            "units": rows,
        }

    contained_count = sum(row["bbox_inside_gold_region"] is True for row in rows)
    status = "measured" if evidence_count == len(rows) else "partial"
    result = {
        "status": status,
        "comparison": (
            "page-exact plus strict containment of unit-attributable observed text bbox "
            "inside broad gold reference region; aggregate-block bboxes are not copied "
            "onto substring-aligned reference units; no universal IoU threshold"
        ),
        "geometry_evidence_count": evidence_count,
        "provider_geometry_observed_count": provider_geometry_count,
        "contained_count": contained_count,
        "expected_count": len(rows),
        "units": rows,
    }
    if status == "partial":
        result["reason"] = (
            "Only part of the aligned reference set exposes unit-attributable source "
            "geometry; missing or aggregate geometry remains unmeasured."
        )
    return result


def _measure_hierarchy(
    reference_units: list[dict[str, Any]],
    matched_blocks: dict[str, dict[str, Any]],
    match_states: dict[str, str],
) -> dict[str, Any]:
    comparable = [
        unit
        for unit in reference_units
        if unit.get("type") in {"heading", "paragraph", "code", "list-item"}
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
                "type for aligned reference units. Visual/font cues are never used "
                "as implicit hierarchy evidence."
            ),
            "semantic_evidence_count": 0,
            "expected_count": len(comparable),
            "type_exact_count": 0,
            "segmentation_exact_count": 0,
            "units": [],
        }

    rows: list[dict[str, Any]] = []
    for unit in comparable:
        unit_id = unit.get("id")
        block = matched_blocks.get(unit_id)
        observed_type = block.get("semantic_type") if block else None
        has_semantics = observed_type is not None
        expected_type = unit.get("type")
        type_exact = has_semantics and observed_type == expected_type
        segmentation_exact = match_states.get(unit_id) == "exact-block"
        rows.append(
            {
                "reference_unit": unit_id,
                "match_state": match_states.get(unit_id, "missing"),
                "semantic_evidence_available": has_semantics,
                "expected_type": expected_type,
                "observed_type": observed_type,
                "type_exact": type_exact if has_semantics else None,
                "segmentation_exact": segmentation_exact if block else None,
                "observed_level": block.get("semantic_level") if block else None,
            }
        )

    status = "measured" if len(semantic_evidence) == len(comparable) else "partial"
    result = {
        "status": status,
        "semantic_evidence_count": len(semantic_evidence),
        "expected_count": len(comparable),
        "type_exact_count": sum(row["type_exact"] is True for row in rows),
        "segmentation_exact_count": sum(
            row["segmentation_exact"] is True for row in rows
        ),
        "units": rows,
    }
    if status == "partial":
        result["reason"] = (
            "Only part of the aligned reference set exposes explicit semantic types; "
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

    matched_blocks, match_states, positions = _align_reference_units(
        observation, reference_units
    )
    text_rows: list[dict[str, Any]] = []
    for unit in reference_units:
        unit_id = unit.get("id")
        state = match_states.get(unit_id, "missing")
        content_preserved = state in {"exact-block", "substring-in-provider-block"}
        text_rows.append(
            {
                "reference_unit": unit_id,
                "match_state": state,
                "content_preserved": content_preserved,
                "segmentation_exact": state == "exact-block",
            }
        )

    dimensions["content_text"] = {
        "status": "measured",
        "matched_units": sum(row["content_preserved"] for row in text_rows),
        "exact_block_units": sum(row["segmentation_exact"] for row in text_rows),
        "expected_units": len(text_rows),
        "units": text_rows,
        "alignment_policy": (
            "exact Provider block preferred; otherwise one unique normalized exact "
            "reference substring within one Provider block; repeated/ambiguous "
            "occurrences are never guessed"
        ),
    }
    dimensions["source_coordinates"] = _measure_coordinates(
        reference_units, matched_blocks, match_states
    )

    text_by_id = {
        unit["id"]: _normalize_text(str(unit.get("text", "")))
        for unit in reference_units
        if unit.get("id") and unit.get("text")
    }
    edge_rows = []
    for before_id, after_id in gold_fixture.get("reading_order", []):
        before_position = positions.get(before_id)
        after_position = positions.get(after_id)
        before_state = match_states.get(before_id, "missing")
        after_state = match_states.get(after_id, "missing")
        ambiguous = before_state.startswith("ambiguous") or after_state.startswith(
            "ambiguous"
        )
        ambiguous_duplicate_text = (
            before_state == "ambiguous-duplicate-text"
            or after_state == "ambiguous-duplicate-text"
        )
        satisfied = (
            not ambiguous
            and before_position is not None
            and after_position is not None
            and before_position < after_position
        )
        edge_rows.append(
            {
                "before": before_id,
                "after": after_id,
                "satisfied": satisfied,
                "ambiguous_alignment": ambiguous,
                # Compatibility field retained for canonical Poppler evidence/tests.
                # Newer scorers additionally expose the broader ambiguous_alignment.
                "ambiguous_duplicate_text": ambiguous_duplicate_text,
                "before_position": before_position,
                "after_position": after_position,
            }
        )
    ordered_ids = [
        unit_id for unit_id, _ in sorted(positions.items(), key=lambda item: item[1])
    ]
    dimensions["reading_order"] = {
        "status": "measured",
        "satisfied_edges": sum(row["satisfied"] for row in edge_rows),
        "expected_edges": len(edge_rows),
        "observed_reference_unit_order": ordered_ids,
        "observed_reference_text_sequence": [
            text_by_id[unit_id] for unit_id in ordered_ids if unit_id in text_by_id
        ],
        "edges": edge_rows,
        "alignment_policy": "Provider block index then unique substring character offset",
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
