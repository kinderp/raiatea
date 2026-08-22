"""Provider-neutral B01-PDF-004 figure/caption benchmark scoring.

This is benchmark-only evidence logic. It deliberately keeps caption text,
figure presence, figure geometry, asset identity and figure-caption association
as independent dimensions. It never infers association or figure identity from
spatial/positional coincidence.
"""

from __future__ import annotations

from typing import Any


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _caption_text(gold_fixture: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    captions = [
        unit
        for unit in gold_fixture.get("reference_units", [])
        if unit.get("type") == "caption" and unit.get("text")
    ]
    if not captions:
        return {"status": "not-applicable", "expected_count": 0, "exact_count": 0, "captions": []}

    blocks = observation.get("blocks")
    if not isinstance(blocks, list):
        return {
            "status": "not-measured",
            "reason": "The measured route exposes no comparable text-block collection.",
            "expected_count": len(captions),
            "exact_count": 0,
            "captions": [],
        }

    normalized_blocks = [
        _normalize_text(str(block.get("text", "")))
        for block in blocks
        if isinstance(block, dict)
    ]
    rows = []
    for caption in captions:
        expected = _normalize_text(str(caption["text"]))
        exact_matches = [index for index, text in enumerate(normalized_blocks) if text == expected]
        rows.append(
            {
                "caption_unit": caption.get("id"),
                "expected_text": expected,
                "exact_match_count": len(exact_matches),
                "exact": len(exact_matches) == 1,
                "ambiguous": len(exact_matches) > 1,
            }
        )
    return {
        "status": "measured",
        "expected_count": len(rows),
        "exact_count": sum(row["exact"] for row in rows),
        "captions": rows,
        "policy": "exact normalized Provider text only; caption role is not inferred from typography or proximity",
    }


def _edge_errors(observed: list[float], expected: list[float]) -> dict[str, Any]:
    signed = [float(observed[index]) - float(expected[index]) for index in range(4)]
    absolute = [abs(value) for value in signed]
    return {
        "signed_edge_error_points": signed,
        "absolute_edge_error_points": absolute,
        "max_absolute_edge_error_points": max(absolute),
        "bbox_exact": all(value == 0.0 for value in absolute),
    }


def _figures(gold_fixture: dict[str, Any], observation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected = gold_fixture.get("figures")
    if not expected:
        na = {"status": "not-applicable", "expected_count": 0}
        return na, na.copy(), na.copy()

    observed = observation.get("figures")
    if not isinstance(observed, list):
        reason = "The measured route exposes no explicit figure collection; absence is not scored as failure."
        return (
            {"status": "not-measured", "reason": reason, "expected_count": len(expected), "observed_count": 0},
            {"status": "not-measured", "reason": reason, "expected_count": len(expected), "evidence_count": 0, "figures": []},
            {"status": "not-measured", "reason": reason, "expected_count": len(expected), "evidence_count": 0, "exact_count": 0, "figures": []},
        )

    presence = {
        "status": "measured",
        "expected_count": len(expected),
        "observed_count": len(observed),
        "count_exact": len(observed) == len(expected),
        "policy": "explicit Provider figure records only",
    }

    # B01-PDF-004 has one authored figure and no general cross-provider figure
    # identity protocol. Geometry/asset evidence may therefore be bound only in
    # the unambiguous 1 expected : 1 observed case. A count mismatch remains a
    # valid presence observation but must not make the first Provider item the
    # first gold item by list position.
    unique_figure_identity = (
        len(expected) == 1
        and len(observed) == 1
        and isinstance(observed[0], dict)
    )

    geometry_rows = []
    identity_rows = []
    for index, gold_figure in enumerate(expected):
        provider_figure = observed[0] if unique_figure_identity and index == 0 else None
        observed_page = provider_figure.get("page_index") if provider_figure else None
        observed_bbox = provider_figure.get("bbox_points_bottom_left") if provider_figure else None
        expected_page = gold_figure.get("page_index")
        expected_bbox = gold_figure.get("region")
        geometry_available = (
            provider_figure is not None
            and observed_page is not None
            and isinstance(observed_bbox, list)
            and len(observed_bbox) == 4
            and isinstance(expected_bbox, list)
            and len(expected_bbox) == 4
        )
        page_exact = geometry_available and observed_page == expected_page
        error = _edge_errors(observed_bbox, expected_bbox) if geometry_available else {}
        geometry_rows.append(
            {
                "gold_figure": gold_figure.get("id"),
                "provider_ref": provider_figure.get("provider_ref") if provider_figure else None,
                "matching_basis": "single-figure-cardinality" if provider_figure else None,
                "evidence_available": geometry_available,
                "page_exact": page_exact if geometry_available else None,
                "expected_page_index": expected_page,
                "observed_page_index": observed_page,
                "gold_region_points_bottom_left": expected_bbox,
                "observed_provider_bbox_points_bottom_left": observed_bbox,
                **error,
            }
        )

        expected_pixel_hash = gold_figure.get("pixel_payload_sha256")
        observed_pixel_hash = provider_figure.get("decoded_pixel_sha256") if provider_figure else None
        identity_available = bool(expected_pixel_hash and observed_pixel_hash)
        identity_rows.append(
            {
                "gold_figure": gold_figure.get("id"),
                "provider_ref": provider_figure.get("provider_ref") if provider_figure else None,
                "matching_basis": "single-figure-cardinality" if provider_figure else None,
                "evidence_available": identity_available,
                "expected_pixel_payload_sha256": expected_pixel_hash,
                "observed_decoded_pixel_sha256": observed_pixel_hash,
                "pixel_identity_exact": (
                    observed_pixel_hash == expected_pixel_hash if identity_available else None
                ),
                "provider_asset_sha256": provider_figure.get("asset_sha256") if provider_figure else None,
                "provider_asset_bytes": provider_figure.get("asset_bytes") if provider_figure else None,
            }
        )

    geometry_evidence = sum(row["evidence_available"] for row in geometry_rows)
    geometry_status = (
        "not-measured"
        if geometry_evidence == 0
        else "measured"
        if geometry_evidence == len(geometry_rows)
        else "partial"
    )
    measured_edge_errors = [
        row["max_absolute_edge_error_points"]
        for row in geometry_rows
        if row.get("evidence_available")
    ]
    geometry = {
        "status": geometry_status,
        "expected_count": len(geometry_rows),
        "evidence_count": geometry_evidence,
        "page_exact_count": sum(row.get("page_exact") is True for row in geometry_rows),
        "bbox_exact_count": sum(row.get("bbox_exact") is True for row in geometry_rows),
        "max_observed_edge_error_points": max(measured_edge_errors) if measured_edge_errors else None,
        "figures": geometry_rows,
        "policy": (
            "record page identity and raw per-edge point errors only after unambiguous figure identity; "
            "no list-position matching, post-hoc tolerance or universal geometry pass threshold"
        ),
    }
    if geometry_status != "measured":
        geometry["reason"] = (
            "Explicit Provider figure geometry is incomplete/unavailable or figure identity is ambiguous."
        )

    identity_evidence = sum(row["evidence_available"] for row in identity_rows)
    identity_status = (
        "not-measured"
        if identity_evidence == 0
        else "measured"
        if identity_evidence == len(identity_rows)
        else "partial"
    )
    identity = {
        "status": identity_status,
        "expected_count": len(identity_rows),
        "evidence_count": identity_evidence,
        "exact_count": sum(row["pixel_identity_exact"] is True for row in identity_rows),
        "figures": identity_rows,
        "policy": (
            "compare decoded pixel payload SHA-256 only after unambiguous figure identity; "
            "Provider-specific encoded bytes remain separate"
        ),
    }
    if identity_status != "measured":
        identity["reason"] = (
            "Comparable decoded pixel evidence is incomplete/unavailable or figure identity is ambiguous."
        )

    return presence, geometry, identity


def _association(gold_fixture: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    expected = gold_fixture.get("figure_caption_relations")
    if not expected:
        return {"status": "not-applicable", "expected_count": 0, "evidence_count": 0, "exact_count": 0, "relations": []}

    observed = observation.get("figure_caption_relations")
    if not isinstance(observed, list):
        return {
            "status": "not-measured",
            "reason": (
                "The Provider exposes no explicit figure-caption relation evidence. "
                "Spatial proximity is deliberately ignored."
            ),
            "expected_count": len(expected),
            "evidence_count": 0,
            "exact_count": 0,
            "relations": [],
            "proximity_inference": False,
        }

    rows = []
    for relation in expected:
        figure_id = relation.get("figure_id")
        caption_unit = relation.get("caption_unit")
        candidates = [
            item
            for item in observed
            if isinstance(item, dict)
            and item.get("gold_figure_id") == figure_id
            and item.get("gold_caption_unit") == caption_unit
            and item.get("provider_relation_source")
        ]
        rows.append(
            {
                "gold_figure_id": figure_id,
                "gold_caption_unit": caption_unit,
                "explicit_candidate_count": len(candidates),
                "exact": len(candidates) == 1,
                "provider_relation_sources": sorted(
                    {str(item["provider_relation_source"]) for item in candidates}
                ),
            }
        )
    evidence_count = sum(row["explicit_candidate_count"] > 0 for row in rows)
    status = "measured" if evidence_count == len(rows) else "partial" if evidence_count else "not-measured"
    result = {
        "status": status,
        "expected_count": len(rows),
        "evidence_count": evidence_count,
        "exact_count": sum(row["exact"] for row in rows),
        "relations": rows,
        "proximity_inference": False,
        "policy": "only explicit Provider-originated relation evidence is creditable",
    }
    if status != "measured":
        result["reason"] = "Explicit Provider relation evidence is incomplete; layout proximity is not substituted."
    return result


def measure_b01_figure_dimensions(
    observation: dict[str, Any],
    gold_fixture: dict[str, Any],
) -> dict[str, Any]:
    presence, geometry, identity = _figures(gold_fixture, observation)
    return {
        "caption_text": _caption_text(gold_fixture, observation),
        "figure_presence": presence,
        "figure_geometry": geometry,
        "asset_identity": identity,
        "figure_caption_association": _association(gold_fixture, observation),
    }
