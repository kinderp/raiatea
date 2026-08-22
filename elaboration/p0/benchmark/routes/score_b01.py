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


def _normalize_level(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _heading_level_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    level_rows = [row for row in rows if row.get("expected_level") is not None]
    if not level_rows:
        return {
            "status": "not-applicable",
            "expected_count": 0,
            "evidence_count": 0,
            "exact_count": 0,
            "units": [],
        }

    evidence_count = sum(row.get("level_evidence_available") is True for row in level_rows)
    exact_count = sum(row.get("level_exact") is True for row in level_rows)
    if evidence_count == 0:
        status = "not-measured"
        reason = (
            "Gold declares heading levels, but the measured route exposes no explicit "
            "heading-level evidence for the aligned units. Typography is not used as a fallback."
        )
    elif evidence_count == len(level_rows):
        status = "measured"
        reason = None
    else:
        status = "partial"
        reason = "Only part of the gold heading set exposes explicit heading-level evidence."

    result = {
        "status": status,
        "expected_count": len(level_rows),
        "evidence_count": evidence_count,
        "exact_count": exact_count,
        "units": [
            {
                "reference_unit": row["reference_unit"],
                "expected_level": row["expected_level"],
                "observed_level": row["observed_level"],
                "level_evidence_available": row["level_evidence_available"],
                "level_exact": row["level_exact"],
            }
            for row in level_rows
        ],
    }
    if reason:
        result["reason"] = reason
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
        empty_rows = [
            {
                "reference_unit": unit.get("id"),
                "expected_level": _normalize_level(unit.get("level")),
                "observed_level": None,
                "level_evidence_available": False,
                "level_exact": None,
            }
            for unit in comparable
        ]
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
            "heading_levels": _heading_level_summary(empty_rows),
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
        expected_level = _normalize_level(unit.get("level"))
        observed_level = _normalize_level(block.get("semantic_level")) if block else None
        level_evidence_available = (
            expected_level is not None
            and observed_type == "heading"
            and observed_level is not None
        )
        level_exact = (
            observed_level == expected_level if level_evidence_available else None
        )
        rows.append(
            {
                "reference_unit": unit_id,
                "match_state": match_states.get(unit_id, "missing"),
                "semantic_evidence_available": has_semantics,
                "expected_type": expected_type,
                "observed_type": observed_type,
                "type_exact": type_exact if has_semantics else None,
                "segmentation_exact": segmentation_exact if block else None,
                "expected_level": expected_level,
                "observed_level": observed_level,
                "level_evidence_available": level_evidence_available,
                "level_exact": level_exact,
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
        "heading_levels": _heading_level_summary(rows),
        "units": rows,
    }
    if status == "partial":
        result["reason"] = (
            "Only part of the aligned reference set exposes explicit semantic types; "
            "missing semantics remain unmeasured."
        )
    return result


def _measure_links(
    gold_fixture: dict[str, Any],
    observation: dict[str, Any],
    reference_units: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_links = gold_fixture.get("links")
    if not expected_links:
        return {
            "status": "not-applicable",
            "expected_count": 0,
            "target_exact_count": 0,
            "association_evidence_count": 0,
            "association_exact_count": 0,
            "links": [],
        }

    observed_links = observation.get("links")
    if observed_links is None:
        return {
            "status": "not-measured",
            "reason": "Gold declares links, but the measured route exposes no link collection.",
            "expected_count": len(expected_links),
            "target_exact_count": 0,
            "association_evidence_count": 0,
            "association_exact_count": 0,
            "links": [],
        }
    if not isinstance(observed_links, list):
        return {
            "status": "not-measured",
            "reason": "Provider link evidence exists in an unsupported benchmark observation shape.",
            "expected_count": len(expected_links),
            "target_exact_count": 0,
            "association_evidence_count": 0,
            "association_exact_count": 0,
            "links": [],
        }

    text_by_id = {
        unit.get("id"): _normalize_text(str(unit.get("text", "")))
        for unit in reference_units
        if unit.get("id")
    }
    rows: list[dict[str, Any]] = []
    for expected in expected_links:
        kind = expected.get("kind")
        target = expected.get("target")
        from_unit = expected.get("from_unit")
        from_text = text_by_id.get(from_unit)
        candidates = [
            item
            for item in observed_links
            if isinstance(item, dict)
            and item.get("kind") == kind
            and item.get("target") == target
        ]
        target_exact = bool(candidates)
        association_evidence = False
        association_exact = False
        for candidate in candidates:
            observed_from_unit = candidate.get("from_unit")
            observed_from_text = candidate.get("from_text")
            if observed_from_unit is not None:
                association_evidence = True
                if observed_from_unit == from_unit:
                    association_exact = True
                    break
            if observed_from_text is not None:
                association_evidence = True
                if _normalize_text(str(observed_from_text)) == from_text:
                    association_exact = True
                    break
        rows.append(
            {
                "link_id": expected.get("id"),
                "kind": kind,
                "expected_target": target,
                "from_unit": from_unit,
                "target_exact": target_exact,
                "association_evidence_available": association_evidence,
                "association_exact": association_exact if association_evidence else None,
                "candidate_count": len(candidates),
            }
        )

    target_exact_count = sum(row["target_exact"] for row in rows)
    association_evidence_count = sum(
        row["association_evidence_available"] for row in rows
    )
    association_exact_count = sum(row["association_exact"] is True for row in rows)
    if target_exact_count == 0 and association_evidence_count == 0:
        status = "measured"
    elif association_evidence_count == len(rows):
        status = "measured"
    else:
        status = "partial"
    result = {
        "status": status,
        "expected_count": len(rows),
        "target_exact_count": target_exact_count,
        "association_evidence_count": association_evidence_count,
        "association_exact_count": association_exact_count,
        "links": rows,
    }
    if status == "partial":
        result["reason"] = (
            "Target evidence is available for at least one gold link, but source-association "
            "evidence is incomplete; missing association is not guessed from layout."
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
    dimensions["links"] = _measure_links(
        gold_fixture, observation, reference_units
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
