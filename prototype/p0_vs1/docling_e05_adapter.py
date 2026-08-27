#!/usr/bin/env python3
"""Core-owned PDF1c adapter from DoclingObservation to accepted E-05 records."""
from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1.0"
CHANNEL = "official-local-docling"
ROUTE_PROFILE = "docling-2.118.0-standard-pdf-native-no-ocr"


def _source(source_id: str, fingerprint: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_class": "B-01",
        "fingerprint": fingerprint,
    }


def _present(value: Any, basis: str, *, origin: str = "provider-native") -> dict[str, Any]:
    return {
        "evidence_state": "present",
        "value_state": "populated",
        "origin": origin,
        "basis": basis,
        "channel": CHANNEL,
        "value": value,
    }


def _unknown(basis: str) -> dict[str, Any]:
    return {
        "evidence_state": "unavailable",
        "value_state": "unknown",
        "origin": "unresolved",
        "basis": basis,
        "channel": CHANNEL,
    }


def _diagnostics(warnings: Any) -> list[dict[str, Any]]:
    if not isinstance(warnings, list):
        return []
    rows: list[dict[str, Any]] = []
    for index, warning in enumerate(warnings):
        if isinstance(warning, dict):
            code = str(warning.get("code") or f"DOCLING_WARNING_{index}")
            details = warning.get("details")
            message = code if details is None else f"{code}: {details}"
        else:
            code = f"DOCLING_WARNING_{index}"
            message = str(warning)
        rows.append({"code": code, "severity": "warning", "message": message})
    return rows


def _execution(status: str) -> str:
    if status == "success":
        return "completed"
    # PDF1c intentionally does not promote a partial/degraded Provider run into
    # current normalized content. Its provider evidence remains inspectable as
    # an attempt while completeness stays unresolved.
    if status == "degraded":
        return "unknown"
    if status == "failed":
        return "failed"
    if status == "restricted":
        return "rejected"
    return "unknown"


def adapt_docling_observation(
    observation: dict[str, Any],
    *,
    source_id: str,
    fingerprint: str,
    provider_version: str,
    provider_observation_fingerprint: str,
    started_at: str,
    ended_at: str,
) -> dict[str, Any]:
    status = str(observation.get("status", "unknown"))
    execution = _execution(status)
    source_ref = _source(source_id, fingerprint)
    provider = {"provider_id": "docling", "version": provider_version}
    route = {
        "route_profile_id": ROUTE_PROFILE,
        "mode": "native-semantic-no-ocr",
        "execution_context": "local",
    }
    native_status = _present(
        status,
        "official Docling ProviderObservation status retained at the Core E-05 boundary",
    )
    evidence_id = f"evidence-{source_id}-pdf-docling-native-no-ocr"
    representation_id = f"norm-{source_id}-pdf-docling-native-no-ocr"
    run_id = f"run-{source_id}-pdf-docling-native-no-ocr"
    evidence_ref = {
        "kind": "provider-evidence",
        "evidence_id": evidence_id,
        "channel": CHANNEL,
    }
    diagnostics = _diagnostics(observation.get("warnings"))

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "source_ref": source_ref,
        "provider": provider,
        "route_profile": route,
        "channel": CHANNEL,
        "native_status": native_status,
        "payload_locator": f"catalog-provider-observation:{source_id}:pdf-docling-native-no-ocr",
        "payload_fingerprint": provider_observation_fingerprint,
        "diagnostics": diagnostics,
    }

    units: list[dict[str, Any]] = []
    for block in observation.get("blocks", []):
        if not isinstance(block, dict) or not isinstance(block.get("text"), str):
            continue
        coordinate_value = block.get("coordinate")
        if isinstance(coordinate_value, dict):
            page_index = coordinate_value.get("page_index")
            bbox = coordinate_value.get("bbox_points_bottom_left")
        else:
            page_index = None
            bbox = None
        coordinate = (
            _present(
                {
                    "kind": "pdf-geometric",
                    "page_index": page_index,
                    "bbox_points_bottom_left": bbox,
                },
                "Docling supplied attributable page provenance and the official product parser mapped its explicit bbox into bottom-left PDF points",
                origin="raiatea-aligned",
            )
            if isinstance(page_index, int) and isinstance(bbox, list) and len(bbox) == 4
            else _unknown(
                "Docling did not expose attributable PDF geometry for this body-order block"
            )
        )
        semantic_type = block.get("semantic_type")
        if isinstance(semantic_type, str) and semantic_type:
            semantic_value: dict[str, Any] = {"type": semantic_type}
            semantic_level = block.get("semantic_level")
            if isinstance(semantic_level, int) and not isinstance(semantic_level, bool):
                semantic_value["level"] = semantic_level
            semantic_role = _present(
                semantic_value,
                "Raiatea Core preserves the explicit Docling provider label mapping; typography/layout is not used to invent semantics",
                origin="provider-native",
            )
        else:
            semantic_role = _unknown(
                "Docling provider label was absent or not in the accepted PDF1c semantic mapping"
            )
        units.append(
            {
                "unit_id": f"block-{len(units)}",
                "surface": _present(
                    block["text"],
                    "Docling lossless observation emitted this body-order text surface",
                ),
                "semantic_role": semantic_role,
                "coordinate": coordinate,
            }
        )

    body_order_source = observation.get("body_order_source")
    relations = [
        {
            "relation_id": f"reading-order-{index}",
            "kind": "reading-order-next",
            "from_ref": units[index]["unit_id"],
            "to_ref": units[index + 1]["unit_id"],
            "evidence_origin": "raiatea-derived",
            "basis": (
                "Preserved Docling provider body-order sequence from "
                f"{body_order_source}; no cross-Provider alignment or stronger semantic order is asserted"
            ),
        }
        for index in range(len(units) - 1)
    ]

    provider_stage = {
        "stage_id": "native-1",
        "stage_kind": "native-extraction",
        "executor": {
            "kind": "provider",
            "provider": provider,
            "route_profile": route,
        },
        "input_refs": [],
        "provider_status": native_status,
        "outcome": {
            "execution": execution,
            "assessments": [
                {
                    "scope": "provider-observation-emission",
                    "completeness": "unknown",
                    "integrity": "unknown",
                    "basis": (
                        "Provider status is retained separately; successful Docling conversion "
                        "does not establish document completeness or semantic correctness"
                    ),
                }
            ],
            "derivation_basis": (
                "Core maps the explicit Docling observation status without importing benchmark gold"
            ),
        },
        "reconciliation_state": "not-applicable",
        "produced": [evidence_ref],
    }
    stages = [provider_stage]
    produced: list[dict[str, Any]] = [evidence_ref]
    result: dict[str, Any] = {"provider_evidence": evidence}

    if execution == "completed":
        representation = {
            "schema_version": SCHEMA_VERSION,
            "representation_id": representation_id,
            "source_ref": source_ref,
            "units": units,
            "relations": relations,
            "diagnostics": diagnostics,
        }
        normalized_ref = {
            "kind": "normalized-representation",
            "representation_id": representation_id,
        }
        stages.append(
            {
                "stage_id": "normalize-1",
                "stage_kind": "normalization",
                "executor": {
                    "kind": "raiatea-core",
                    "operation_id": "normalize-docling-pdf-evidence",
                },
                "parent_stage_id": "native-1",
                "input_refs": [evidence_ref],
                "outcome": {
                    "execution": "completed",
                    "assessments": [
                        {
                            "scope": "normalized-record-structure",
                            "completeness": "unknown",
                            "integrity": "valid",
                            "basis": (
                                "Core produced a structurally valid normalized PDF representation; "
                                "Provider semantic correctness and document completeness remain unestablished"
                            ),
                        }
                    ],
                    "derivation_basis": (
                        "Raiatea Core normalization over explicit Docling ProviderEvidence only"
                    ),
                },
                "reconciliation_state": "not-applicable",
                "produced": [normalized_ref],
            }
        )
        produced.append(normalized_ref)
        result["normalized_representation"] = representation

    result["run"] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "source_ref": source_ref,
        "stages": stages,
        "outcome": {
            "execution": execution,
            "assessments": [
                {
                    "scope": "source-text-and-semantic-structure",
                    "completeness": "unknown",
                    "integrity": "unknown",
                    "basis": (
                        "PDF1c retains Docling body/semantic evidence but does not use benchmark gold, "
                        "Poppler evidence or an external completeness oracle as runtime truth"
                    ),
                }
            ],
            "derivation_basis": (
                "Core orchestration over the independent Docling Provider stage and optional Core normalization stage"
            ),
        },
        "produced": produced,
        "provenance": {
            "started_at": started_at,
            "ended_at": ended_at,
            "run_outcome_basis": (
                "Core orchestration over the current Docling ProviderObservation and normalization policy"
            ),
            "provider_native_status_basis": (
                "official local Docling native/no-OCR ProviderObservation"
            ),
            "input_fingerprint": fingerprint,
        },
        "diagnostics": diagnostics,
    }
    return result


__all__ = ["adapt_docling_observation"]
