"""Provider-neutral scoring for B01-PDF-007 mixed/defective native text.

Benchmark-only. Native-text preservation, raster-visible text recovery, visible
page coverage, source coordinates, Provider outcome/warnings and the gold-informed
fallback verdict are independent dimensions. The fallback verdict is evidence for
E-05 routing design; it is not a production heuristic or public schema.
"""
from __future__ import annotations

from typing import Any


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _reference_by_id(gold: dict[str, Any]) -> dict[str, dict[str, Any]]:
    units = gold.get("reference_units")
    if not isinstance(units, list):
        return {}
    return {
        str(item["id"]): item
        for item in units
        if isinstance(item, dict) and item.get("id") is not None
    }


def _blocks_and_state(observation: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str]:
    blocks = observation.get("blocks")
    if not isinstance(blocks, list):
        return None, "not-measured"
    state = "partial" if any(not isinstance(item, dict) for item in blocks) else "measured"
    return [item for item in blocks if isinstance(item, dict)], state


def _matches(blocks: list[dict[str, Any]], expected_text: str) -> list[dict[str, Any]]:
    expected = _normalize(expected_text)
    return [
        block
        for block in blocks
        if _normalize(str(block.get("text", ""))) == expected
    ]


def _content_dimension(
    gold: dict[str, Any],
    observation: dict[str, Any],
    unit_ids: list[str],
    dimension_name: str,
) -> dict[str, Any]:
    refs = _reference_by_id(gold)
    expected = [refs[item_id] for item_id in unit_ids if item_id in refs]
    blocks, collection_state = _blocks_and_state(observation)
    if blocks is None:
        return {
            "status": "not-measured",
            "collection_state": "not-measured",
            "expected_count": len(expected),
            "recovered_count": 0,
            "exact_once_count": 0,
            "ambiguous_count": 0,
            "units": [],
            "reason": "The route exposes no trustworthy text-block collection.",
            "dimension": dimension_name,
        }

    rows = []
    for unit in expected:
        candidates = _matches(blocks, str(unit.get("text", "")))
        rows.append(
            {
                "unit_id": unit.get("id"),
                "expected_text": unit.get("text"),
                "occurrences": len(candidates),
                "recovered": len(candidates) >= 1,
                "exact_once": len(candidates) == 1,
                "ambiguous": len(candidates) > 1,
            }
        )
    return {
        "status": "partial" if collection_state == "partial" else "measured",
        "collection_state": collection_state,
        "expected_count": len(rows),
        "recovered_count": sum(row["recovered"] for row in rows),
        "exact_once_count": sum(row["exact_once"] for row in rows),
        "ambiguous_count": sum(row["ambiguous"] for row in rows),
        "units": rows,
        "dimension": dimension_name,
        "policy": "exact normalized visible text evidence only; no OCR or layout inference",
    }


def _bbox_inside(inner: list[float], outer: list[float]) -> bool:
    return (
        float(inner[0]) >= float(outer[0])
        and float(inner[1]) >= float(outer[1])
        and float(inner[2]) <= float(outer[2])
        and float(inner[3]) <= float(outer[3])
    )


def _coordinate_dimension(
    gold: dict[str, Any],
    observation: dict[str, Any],
    unit_ids: list[str],
    dimension_name: str,
) -> dict[str, Any]:
    refs = _reference_by_id(gold)
    expected = [refs[item_id] for item_id in unit_ids if item_id in refs]
    blocks, collection_state = _blocks_and_state(observation)
    if blocks is None:
        return {
            "status": "not-measured",
            "expected_count": len(expected),
            "evidence_count": 0,
            "contained_count": 0,
            "units": [],
            "reason": "The route exposes no trustworthy text-block collection.",
            "dimension": dimension_name,
        }

    rows = []
    for unit in expected:
        candidates = _matches(blocks, str(unit.get("text", "")))
        region = unit.get("region")
        attributable = [
            block
            for block in candidates
            if block.get("page_index") == unit.get("page_index")
            and isinstance(block.get("bbox_points_bottom_left"), list)
            and len(block["bbox_points_bottom_left"]) == 4
        ]
        evidence_available = (
            len(candidates) == 1
            and len(attributable) == 1
            and isinstance(region, list)
            and len(region) == 4
        )
        bbox = attributable[0]["bbox_points_bottom_left"] if evidence_available else None
        rows.append(
            {
                "unit_id": unit.get("id"),
                "evidence_available": evidence_available,
                "candidate_count": len(candidates),
                "expected_page_index": unit.get("page_index"),
                "expected_region_points_bottom_left": region,
                "observed_bbox_points_bottom_left": bbox,
                "bbox_inside_gold_region": _bbox_inside(bbox, region)
                if evidence_available
                else None,
            }
        )

    evidence_count = sum(row["evidence_available"] for row in rows)
    status = (
        "measured"
        if evidence_count == len(rows) and collection_state == "measured"
        else "partial"
        if evidence_count or collection_state == "partial"
        else "not-measured"
    )
    return {
        "status": status,
        "collection_state": collection_state,
        "expected_count": len(rows),
        "evidence_count": evidence_count,
        "contained_count": sum(row["bbox_inside_gold_region"] is True for row in rows),
        "units": rows,
        "dimension": dimension_name,
        "policy": (
            "coordinates require one exact text match with Provider-attributable page/bbox; "
            "image geometry is never substituted for missing OCR-text coordinates"
        ),
    }


def _visible_page_coverage(
    gold: dict[str, Any],
    native: dict[str, Any],
    raster: dict[str, Any],
) -> dict[str, Any]:
    refs = _reference_by_id(gold)
    expected_count = len(refs)
    if native.get("status") == "not-measured" or raster.get("status") == "not-measured":
        return {
            "status": "not-measured",
            "expected_count": expected_count,
            "recovered_count": None,
            "coverage_fraction": None,
            "reason": "Visible-page coverage requires trustworthy native and raster-visible content measurements.",
        }
    recovered_count = int(native.get("recovered_count", 0)) + int(
        raster.get("recovered_count", 0)
    )
    status = (
        "partial"
        if native.get("status") == "partial" or raster.get("status") == "partial"
        else "measured"
    )
    return {
        "status": status,
        "expected_count": expected_count,
        "recovered_count": recovered_count,
        "missing_count": expected_count - recovered_count,
        "coverage_fraction": f"{recovered_count}/{expected_count}",
        "complete": recovered_count == expected_count,
        "policy": "gold-known authored visible Source units; no universal completeness score",
    }


def _provider_outcome(observation: dict[str, Any]) -> dict[str, Any]:
    warnings = observation.get("warnings")
    warning_collection_state = "measured" if isinstance(warnings, list) else "not-measured"
    return {
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "warning_collection_state": warning_collection_state,
        "warning_count": len(warnings) if isinstance(warnings, list) else None,
        "warnings": warnings if isinstance(warnings, list) else None,
        "explicit_completeness_state": observation.get("completeness_state"),
        "explicit_completeness_state_available": "completeness_state" in observation,
        "policy": "Provider status/warnings are evidence but do not prove authored visible-page completeness",
    }


def _fallback_verdict(
    native: dict[str, Any],
    raster: dict[str, Any],
    coverage: dict[str, Any],
    provider_outcome: dict[str, Any],
) -> dict[str, Any]:
    if (
        native.get("status") == "not-measured"
        or raster.get("status") == "not-measured"
        or coverage.get("status") == "not-measured"
    ):
        return {
            "status": "not-measured",
            "required": None,
            "reason": "Insufficient benchmark evidence to decide whether the authored raster-visible target is missing.",
            "scope": "benchmark-only-gold-informed",
        }

    raster_missing = int(raster.get("recovered_count", 0)) < int(raster.get("expected_count", 0))
    required = raster_missing
    nominal_success_gap = (
        provider_outcome.get("route_status") == "success"
        and coverage.get("complete") is False
    )
    return {
        "status": "partial"
        if native.get("status") == "partial" or raster.get("status") == "partial"
        else "measured",
        "required": required,
        "raster_visible_target_missing": raster_missing,
        "nominal_provider_success_with_material_visible_gap": nominal_success_gap,
        "reason": (
            "Gold-known raster-visible Source content is absent from the measured text evidence."
            if required
            else "All gold-known raster-visible Source content is present in the measured text evidence."
        ),
        "scope": "benchmark-only-gold-informed",
        "production_routing_heuristic": False,
        "policy": (
            "This verdict demonstrates the routing requirement for E-05; production fallback "
            "must later use inspectable runtime evidence rather than hidden access to benchmark gold."
        ),
    }


def measure_b01_defective_native_dimensions(
    observation: dict[str, Any], gold: dict[str, Any]
) -> dict[str, Any]:
    native_ids = [str(item) for item in gold.get("native_text_layer_units", [])]
    raster_ids = [str(item) for item in gold.get("raster_visible_units", [])]

    native_content = _content_dimension(
        gold, observation, native_ids, "native_text_content"
    )
    raster_content = _content_dimension(
        gold, observation, raster_ids, "raster_visible_text_content"
    )
    native_coordinates = _coordinate_dimension(
        gold, observation, native_ids, "native_text_coordinates"
    )
    raster_coordinates = _coordinate_dimension(
        gold, observation, raster_ids, "raster_visible_text_coordinates"
    )
    coverage = _visible_page_coverage(gold, native_content, raster_content)
    outcome = _provider_outcome(observation)
    fallback = _fallback_verdict(native_content, raster_content, coverage, outcome)

    return {
        "native_text_content": native_content,
        "raster_visible_text_content": raster_content,
        "visible_page_coverage": coverage,
        "native_text_coordinates": native_coordinates,
        "raster_visible_text_coordinates": raster_coordinates,
        "provider_outcome": outcome,
        "benchmark_fallback_verdict": fallback,
    }
