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


def measure_b01_fixture(
    fixture_id: str,
    observation: dict[str, Any],
    gold_fixture: dict[str, Any],
) -> dict[str, Any]:
    """Measure current B-01 dimensions independently; never compute a total score."""
    reference_units = gold_fixture.get("reference_units", [])
    dimensions: dict[str, Any] = {}

    text_rows: list[dict[str, Any]] = []
    coordinate_rows: list[dict[str, Any]] = []
    matched_blocks: dict[str, dict[str, Any]] = {}
    for unit in reference_units:
        block, match_state = _find_unique_block(observation, unit.get("text", ""))
        if block is not None:
            matched_blocks[unit["id"]] = block
        text_rows.append(
            {
                "reference_unit": unit.get("id"),
                "match_state": match_state,
                "exact_text": block is not None,
            }
        )

        expected_page = unit.get("page_index")
        expected_region = unit.get("region")
        if expected_page is None or expected_region is None:
            continue
        observed_bbox = block.get("bbox_points_bottom_left") if block else None
        observed_page = block.get("page_index") if block else None
        page_exact = block is not None and observed_page == expected_page
        contained = (
            bool(block)
            and page_exact
            and observed_bbox is not None
            and _bbox_inside(observed_bbox, expected_region)
        )
        coordinate_rows.append(
            {
                "reference_unit": unit.get("id"),
                "match_state": match_state,
                "page_exact": page_exact,
                "bbox_inside_gold_region": contained,
                "expected_page_index": expected_page,
                "observed_page_index": observed_page,
                "gold_region_points_bottom_left": expected_region,
                "observed_bbox_points_bottom_left": observed_bbox,
            }
        )

    dimensions["content_text"] = {
        "status": "measured",
        "matched_units": sum(row["exact_text"] for row in text_rows),
        "expected_units": len(text_rows),
        "units": text_rows,
    }
    dimensions["source_coordinates"] = {
        "status": "measured",
        "comparison": "page-exact plus strict containment of observed text bbox inside broad gold reference region; no universal IoU threshold",
        "contained_count": sum(row["bbox_inside_gold_region"] for row in coordinate_rows),
        "expected_count": len(coordinate_rows),
        "units": coordinate_rows,
    }

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

    dimensions["hierarchy"] = {
        "status": "not-measured",
        "reason": (
            "The Poppler control outputs used in this child expose text/layout "
            "but not Provider-neutral heading/paragraph semantics. Font-size or "
            "visual cues are not promoted to hierarchy gold."
        ),
    }

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
