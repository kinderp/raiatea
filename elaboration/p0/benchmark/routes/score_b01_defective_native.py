"""Provider-neutral scoring for B01-PDF-007 mixed/defective native text.

Benchmark-only. Native-text preservation, raster-visible text recovery, visible
page coverage, source coordinates, Provider outcome/warnings and the gold-informed
fallback verdict are independent dimensions. The fallback verdict is evidence for
E-05 routing design; it is not a production heuristic or public schema.

Raster-region alignment is also kept separate from exact text recovery. It may
show that an OCR route produced a plausible but imperfect surface (for example
all expected tokens in the wrong order) without granting exact recovery credit.
"""
from __future__ import annotations

from collections import Counter
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


def _bbox_area(box: list[float]) -> float:
    return max(0.0, float(box[2]) - float(box[0])) * max(
        0.0, float(box[3]) - float(box[1])
    )


def _intersection_area(a: list[float], b: list[float]) -> float:
    left = max(float(a[0]), float(b[0]))
    bottom = max(float(a[1]), float(b[1]))
    right = min(float(a[2]), float(b[2]))
    top = min(float(a[3]), float(b[3]))
    return max(0.0, right - left) * max(0.0, top - bottom)


def _raster_region_alignment(
    gold: dict[str, Any], observation: dict[str, Any], unit_ids: list[str]
) -> dict[str, Any]:
    """Record OCR-like text in authored raster regions without granting exact credit.

    Geometry is used only as inspectable benchmark alignment against authored gold.
    It is never promoted into a production routing heuristic and does not turn a
    wrong text sequence into an exact recovery.
    """
    refs = _reference_by_id(gold)
    expected_units = [refs[item_id] for item_id in unit_ids if item_id in refs]
    blocks, collection_state = _blocks_and_state(observation)
    if blocks is None:
        return {
            "status": "not-measured",
            "collection_state": "not-measured",
            "expected_count": len(expected_units),
            "candidate_count": 0,
            "units": [],
            "reason": "The route exposes no trustworthy text-block collection.",
        }

    units: list[dict[str, Any]] = []
    total_candidates = 0
    exact_candidates = 0
    token_multiset_exact = 0
    partial_candidates = 0
    for unit in expected_units:
        region = unit.get("region")
        expected_text = _normalize(str(unit.get("text", "")))
        expected_tokens = expected_text.split()
        expected_counter = Counter(expected_tokens)
        rows: list[dict[str, Any]] = []
        if isinstance(region, list) and len(region) == 4:
            gold_area = _bbox_area(region)
            for block in blocks:
                bbox = block.get("bbox_points_bottom_left")
                if block.get("page_index") != unit.get("page_index"):
                    continue
                if not isinstance(bbox, list) or len(bbox) != 4:
                    continue
                intersection = _intersection_area(bbox, region)
                if intersection <= 0.0:
                    continue
                text = _normalize(str(block.get("text", "")))
                observed_tokens = text.split()
                observed_counter = Counter(observed_tokens)
                shared = sum((expected_counter & observed_counter).values())
                exact = text == expected_text
                multiset_exact = observed_counter == expected_counter
                order_exact = observed_tokens == expected_tokens
                partial_surface = not exact and shared > 0
                rows.append(
                    {
                        "observed_text": text,
                        "observed_bbox_points_bottom_left": bbox,
                        "intersection_area_points2": intersection,
                        "intersection_over_gold_region": (
                            intersection / gold_area if gold_area > 0.0 else None
                        ),
                        "exact_text": exact,
                        "token_order_exact": order_exact,
                        "token_multiset_exact": multiset_exact,
                        "shared_token_count": shared,
                        "expected_token_count": len(expected_tokens),
                        "observed_token_count": len(observed_tokens),
                        "partial_surface_evidence": partial_surface,
                    }
                )
        total_candidates += len(rows)
        exact_candidates += sum(row["exact_text"] for row in rows)
        token_multiset_exact += sum(row["token_multiset_exact"] for row in rows)
        partial_candidates += sum(row["partial_surface_evidence"] for row in rows)
        units.append(
            {
                "unit_id": unit.get("id"),
                "expected_text": expected_text,
                "expected_region_points_bottom_left": region,
                "candidate_count": len(rows),
                "candidates": rows,
            }
        )

    return {
        "status": "partial" if collection_state == "partial" else "measured",
        "collection_state": collection_state,
        "expected_count": len(expected_units),
        "candidate_count": total_candidates,
        "exact_candidate_count": exact_candidates,
        "token_multiset_exact_candidate_count": token_multiset_exact,
        "partial_surface_candidate_count": partial_candidates,
        "units": units,
        "policy": (
            "benchmark-only authored-region alignment; spatial overlap may expose partial OCR "
            "surface evidence but never grants exact text recovery or production fallback semantics"
        ),
        "production_routing_heuristic": False,
    }


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


def _native_ocr_reconciliation(observation: dict[str, Any]) -> dict[str, Any]:
    """Measure overlap only when Provider evidence attributes blocks to native/OCR stages."""
    blocks, collection_state = _blocks_and_state(observation)
    if blocks is None:
        return {
            "status": "not-measured",
            "reason": "No trustworthy text-block collection is available for reconciliation evidence.",
            "destructive_merge_allowed": False,
        }

    attributed: list[tuple[str, str]] = []
    unattributed = 0
    for block in blocks:
        stage = block.get("extraction_stage")
        if stage not in {"native", "ocr"}:
            unattributed += 1
            continue
        attributed.append((str(stage), _normalize(str(block.get("text", "")))))

    if not attributed:
        return {
            "status": "not-measured",
            "collection_state": collection_state,
            "reason": (
                "The measured Provider-normalized blocks do not attribute text to native vs OCR "
                "stages; overlap/dedup identity therefore cannot be claimed."
            ),
            "attributed_block_count": 0,
            "unattributed_block_count": len(blocks),
            "destructive_merge_allowed": False,
            "policy": "unknown provenance never becomes an implicit no-overlap result",
        }

    native_texts = {text for stage, text in attributed if stage == "native"}
    ocr_texts = {text for stage, text in attributed if stage == "ocr"}
    overlap = sorted(native_texts & ocr_texts)
    status = "partial" if unattributed or collection_state == "partial" else "measured"
    return {
        "status": status,
        "collection_state": collection_state,
        "attributed_block_count": len(attributed),
        "unattributed_block_count": unattributed,
        "native_distinct_text_count": len(native_texts),
        "ocr_distinct_text_count": len(ocr_texts),
        "exact_text_overlap_count": len(overlap),
        "exact_text_overlap": overlap,
        "destructive_merge_allowed": False,
        "policy": "overlap remains inspectable evidence; no irreversible merge is performed",
    }


def _fallback_verdict(
    native: dict[str, Any],
    raster: dict[str, Any],
    coverage: dict[str, Any],
    provider_outcome: dict[str, Any],
    raster_alignment: dict[str, Any],
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
    partial_surface = int(raster_alignment.get("partial_surface_candidate_count", 0)) > 0
    token_set_exact_order_mismatch = (
        int(raster_alignment.get("token_multiset_exact_candidate_count", 0)) > 0
        and int(raster_alignment.get("exact_candidate_count", 0)) == 0
    )
    return {
        "status": "partial"
        if native.get("status") == "partial"
        or raster.get("status") == "partial"
        or raster_alignment.get("status") == "partial"
        else "measured",
        "required": required,
        "raster_visible_target_missing": raster_missing,
        "raster_region_partial_surface_evidence": partial_surface,
        "raster_region_token_set_exact_order_mismatch": token_set_exact_order_mismatch,
        "nominal_provider_success_with_material_visible_gap": nominal_success_gap,
        "reason": (
            "Exact gold text is absent, but the authored raster region contains partial OCR surface evidence."
            if required and partial_surface
            else "Gold-known raster-visible Source content is absent from the measured text evidence."
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
    raster_alignment = _raster_region_alignment(gold, observation, raster_ids)
    native_coordinates = _coordinate_dimension(
        gold, observation, native_ids, "native_text_coordinates"
    )
    raster_coordinates = _coordinate_dimension(
        gold, observation, raster_ids, "raster_visible_text_coordinates"
    )
    coverage = _visible_page_coverage(gold, native_content, raster_content)
    outcome = _provider_outcome(observation)
    reconciliation = _native_ocr_reconciliation(observation)
    fallback = _fallback_verdict(
        native_content, raster_content, coverage, outcome, raster_alignment
    )

    return {
        "native_text_content": native_content,
        "raster_visible_text_content": raster_content,
        "raster_region_alignment": raster_alignment,
        "visible_page_coverage": coverage,
        "native_text_coordinates": native_coordinates,
        "raster_visible_text_coordinates": raster_coordinates,
        "provider_outcome": outcome,
        "native_ocr_reconciliation": reconciliation,
        "benchmark_fallback_verdict": fallback,
    }
