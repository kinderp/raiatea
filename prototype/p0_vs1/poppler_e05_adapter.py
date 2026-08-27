#!/usr/bin/env python3
"""Core-owned PDF1b adapter from PopplerObservation to accepted E-05 records."""
from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1.0"
CHANNEL = "official-local-poppler"


def _source(source_id: str, fingerprint: str) -> dict[str, Any]:
    return {"source_id": source_id, "source_class": "B-01", "fingerprint": fingerprint}


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
            code = str(warning.get("code") or f"POPPLER_WARNING_{index}")
            details = warning.get("details")
            message = code if details is None else f"{code}: {details}"
        else:
            code = f"POPPLER_WARNING_{index}"
            message = str(warning)
        rows.append({"code": code, "severity": "warning", "message": message})
    return rows


def _execution(status: str) -> str:
    if status == "success":
        return "completed"
    if status == "failed":
        return "failed"
    if status == "restricted":
        return "rejected"
    return "unknown"


def adapt_poppler_observation(
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
    provider = {"provider_id": "poppler", "version": provider_version}
    route = {
        "route_profile_id": "pdf-poppler-pdftohtml-xml",
        "mode": "native",
        "execution_context": "local",
    }
    native_status = _present(
        status,
        "official Poppler provider observation status retained at the Core E-05 boundary",
    )
    evidence_id = f"evidence-{source_id}-pdf-poppler-pdftohtml-xml"
    representation_id = f"norm-{source_id}-pdf-poppler-pdftohtml-xml"
    run_id = f"run-{source_id}-pdf-poppler-pdftohtml-xml"
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
        "payload_locator": f"catalog-provider-observation:{source_id}:pdf-poppler-pdftohtml-xml",
        "payload_fingerprint": provider_observation_fingerprint,
        "diagnostics": diagnostics,
    }

    units: list[dict[str, Any]] = []
    for index, block in enumerate(observation.get("blocks", [])):
        if not isinstance(block, dict) or not isinstance(block.get("text"), str):
            continue
        page_index = block.get("page_index")
        bbox = block.get("bbox_points_bottom_left")
        coordinate = (
            _present(
                {
                    "kind": "pdf-geometric",
                    "page_index": page_index,
                    "bbox_points_bottom_left": bbox,
                },
                "Poppler pdftohtml block supplied page evidence and Core mapped the explicit box into bottom-left PDF points",
                origin="raiatea-aligned",
            )
            if isinstance(page_index, int) and isinstance(bbox, list) and len(bbox) == 4
            else _unknown("Poppler observation did not expose attributable PDF geometry for this block")
        )
        units.append(
            {
                "unit_id": f"block-{index}",
                "surface": _present(
                    block["text"],
                    "Poppler pdftohtml emitted this text surface",
                ),
                "semantic_role": _unknown(
                    "PDF1b Poppler route does not infer heading/list/table/formula semantics from typography or geometry"
                ),
                "coordinate": coordinate,
            }
        )

    relations: list[dict[str, Any]] = []
    for index in range(len(units) - 1):
        relations.append(
            {
                "relation_id": f"reading-order-{index}",
                "kind": "reading-order-next",
                "from_ref": units[index]["unit_id"],
                "to_ref": units[index + 1]["unit_id"],
                "evidence_origin": "raiatea-derived",
                "basis": "preserved Poppler pdftohtml block sequence; no stronger semantic reading-order claim is added",
            }
        )

    provider_stage = {
        "stage_id": "native-1",
        "stage_kind": "native-extraction",
        "executor": {"kind": "provider", "provider": provider, "route_profile": route},
        "input_refs": [],
        "provider_status": native_status,
        "outcome": {
            "execution": execution,
            "assessments": [
                {
                    "scope": "provider-observation-emission",
                    "completeness": "unknown",
                    "integrity": "unknown",
                    "basis": "provider status is retained separately; no benchmark gold is runtime knowledge",
                }
            ],
            "derivation_basis": "Core maps the explicit Poppler observation status without promoting success to completeness",
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
                "executor": {"kind": "raiatea-core", "operation_id": "normalize-poppler-pdf-evidence"},
                "parent_stage_id": "native-1",
                "input_refs": [evidence_ref],
                "outcome": {
                    "execution": "completed",
                    "assessments": [
                        {
                            "scope": "normalized-record-structure",
                            "completeness": "unknown",
                            "integrity": "valid",
                            "basis": "Core produced a structurally valid normalized PDF representation; document completeness remains unestablished",
                        }
                    ],
                    "derivation_basis": "Raiatea Core normalization over explicit Poppler ProviderEvidence",
                },
                "reconciliation_state": "not-applicable",
                "produced": [normalized_ref],
            }
        )
        produced.append(normalized_ref)
        result["normalized_representation"] = representation

    run = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "source_ref": source_ref,
        "stages": stages,
        "outcome": {
            "execution": execution,
            "assessments": [
                {
                    "scope": "source-text-surface",
                    "completeness": "unknown",
                    "integrity": "unknown",
                    "basis": "PDF1b has Provider observation only; successful Poppler execution does not establish visible-page completeness or document integrity",
                }
            ],
            "derivation_basis": "Core orchestration over explicit Poppler stage outcome and optional Core normalization stage",
        },
        "produced": produced,
        "provenance": {
            "started_at": started_at,
            "ended_at": ended_at,
            "run_outcome_basis": "Core orchestration over the current Poppler provider observation and Core normalization policy",
            "provider_native_status_basis": "official local Poppler observation",
            "input_fingerprint": fingerprint,
        },
        "diagnostics": diagnostics,
    }
    result["run"] = run
    return result
