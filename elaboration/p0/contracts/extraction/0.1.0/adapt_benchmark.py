#!/usr/bin/env python3
"""Benchmark-only demonstrations adapting E-04 mapper shapes into E-05b records.

These helpers are not production Adapters or Plugin SDK code. They demonstrate
that materially different existing benchmark observations can cross the accepted
E-05 boundary without leaking Provider-native schemas into normalized records.
Benchmark gold is deliberately not consulted here.
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "0.1.0"


def _source(source_id: str, source_class: str, fingerprint: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_class": source_class,
        "fingerprint": fingerprint,
    }


def _present(
    value: Any,
    basis: str,
    channel: str,
    *,
    origin: str = "provider-native",
) -> dict[str, Any]:
    return {
        "evidence_state": "measured",
        "value_state": "present",
        "origin": origin,
        "basis": basis,
        "channel": channel,
        "value": value,
    }


def _unknown(basis: str, channel: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "evidence_state": "not-measured",
        "value_state": "unknown",
        "origin": "unresolved",
        "basis": basis,
    }
    if channel:
        result["channel"] = channel
    return result


def _diagnostics(warnings: Any) -> list[dict[str, Any]]:
    if not isinstance(warnings, list):
        return []
    rows: list[dict[str, Any]] = []
    for index, warning in enumerate(warnings):
        if not isinstance(warning, dict):
            rows.append(
                {
                    "code": f"PROVIDER_WARNING_{index}",
                    "severity": "warning",
                    "message": str(warning),
                }
            )
            continue
        rows.append(
            {
                "code": str(warning.get("code") or f"PROVIDER_WARNING_{index}"),
                "severity": "warning",
                "message": str(warning.get("details", "provider warning")),
            }
        )
    return rows


def _execution_from_status(status: str) -> str:
    if status in {"success", "degraded", "partial"}:
        return "completed"
    if status == "failed":
        return "failed"
    if status == "rejected":
        return "rejected"
    if status == "unsupported":
        return "unsupported"
    return "unknown"


def _provider_stage_outcome(status: str, label: str) -> dict[str, Any]:
    return {
        "execution": _execution_from_status(status),
        "assessments": [
            {
                "scope": label,
                "completeness": "unknown",
                "integrity": "unknown",
                "basis": "Provider observation exists, but benchmark gold is not imported as runtime completeness or integrity knowledge",
            }
        ],
        "derivation_basis": "E-05b stage assessment keeps Provider-native status separate from Raiatea stage outcome",
    }


def _normalization_stage(
    *,
    stage_id: str,
    parent_stage_id: str,
    input_refs: list[dict[str, Any]],
    representation_id: str,
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "stage_kind": "normalization",
        "executor": {
            "kind": "raiatea-core",
            "operation_id": "normalize-provider-evidence",
        },
        "parent_stage_id": parent_stage_id,
        "input_refs": input_refs,
        "outcome": {
            "execution": "completed",
            "assessments": [
                {
                    "scope": "normalized-record-structure",
                    "completeness": "unknown",
                    "integrity": "valid",
                    "basis": "Core produced a structurally valid normalized record; source completeness remains unestablished",
                }
            ],
            "derivation_basis": "Raiatea Core normalization over explicit prior ProviderEvidence references",
        },
        "reconciliation_state": "not-applicable",
        "produced": [
            {
                "kind": "normalized-representation",
                "representation_id": representation_id,
            }
        ],
    }


def adapt_poppler_observation(
    observation: dict[str, Any],
    *,
    source_id: str,
    fingerprint: str,
    provider_version: str = "24.02.0",
) -> dict[str, Any]:
    route_id = observation.get("route")
    if route_id not in {"pdftohtml-xml", "pdftotext-bbox-layout"}:
        raise ValueError(f"unsupported Poppler benchmark route: {route_id!r}")

    source_ref = _source(source_id, "B-01", fingerprint)
    provider = {"provider_id": "poppler", "version": provider_version}
    route = {
        "route_profile_id": str(route_id),
        "mode": "native",
        "execution_context": "local",
    }
    status = str(observation.get("status", "unknown"))
    execution = _execution_from_status(status)
    native_status = _present(
        status,
        "E-04 Poppler mapper observation status",
        "benchmark-normalized-view",
        origin="provider-native",
    )
    evidence_id = f"evidence-{source_id}-{route_id}"
    representation_id = f"norm-{source_id}-{route_id}"
    evidence_ref = {
        "kind": "provider-evidence",
        "evidence_id": evidence_id,
        "channel": "benchmark-normalized-view",
    }

    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "source_ref": source_ref,
        "provider": provider,
        "route_profile": route,
        "channel": "benchmark-normalized-view",
        "native_status": native_status,
        "payload_locator": f"benchmark-observation:{route_id}",
        "diagnostics": _diagnostics(observation.get("warnings")),
    }
    raw_fingerprint = observation.get("raw_output_sha256")
    if isinstance(raw_fingerprint, str) and raw_fingerprint:
        evidence["payload_fingerprint"] = f"sha256:{raw_fingerprint}"

    units: list[dict[str, Any]] = []
    for index, block in enumerate(observation.get("blocks", [])):
        if not isinstance(block, dict) or not isinstance(block.get("text"), str):
            continue
        coordinate: dict[str, Any]
        bbox = block.get("bbox_points_bottom_left")
        page_index = block.get("page_index")
        if isinstance(page_index, int) and isinstance(bbox, list) and len(bbox) == 4:
            coordinate = _present(
                {
                    "kind": "pdf-geometric",
                    "page_index": page_index,
                    "bbox_points_bottom_left": bbox,
                },
                "Raiatea benchmark mapper converted attributable Poppler geometry into bottom-left PDF points",
                "benchmark-normalized-view",
                origin="raiatea-aligned",
            )
        else:
            coordinate = _unknown(
                "Poppler mapper did not expose attributable mapped geometry for this block",
                "benchmark-normalized-view",
            )
        units.append(
            {
                "unit_id": f"block-{index}",
                "surface": _present(
                    block["text"],
                    "Poppler mapper emitted text block surface",
                    "benchmark-normalized-view",
                    origin="provider-native",
                ),
                "semantic_role": _unknown(
                    "Poppler benchmark route does not provide Provider-native semantic-role evidence",
                    "benchmark-normalized-view",
                ),
                "coordinate": coordinate,
            }
        )

    representation = {
        "schema_version": SCHEMA_VERSION,
        "representation_id": representation_id,
        "source_ref": source_ref,
        "units": units,
        "relations": [],
        "diagnostics": _diagnostics(observation.get("warnings")),
    }

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
        "outcome": _provider_stage_outcome(status, "provider-evidence-emission"),
        "reconciliation_state": "not-applicable",
        "produced": [evidence_ref],
    }
    stages = [provider_stage]
    produced: list[dict[str, Any]] = [evidence_ref]
    result: dict[str, Any] = {
        "provider_evidence": evidence,
    }

    if execution == "completed":
        normalized_ref = {
            "kind": "normalized-representation",
            "representation_id": representation_id,
        }
        stages.append(
            _normalization_stage(
                stage_id="normalize-1",
                parent_stage_id="native-1",
                input_refs=[evidence_ref],
                representation_id=representation_id,
            )
        )
        produced.append(normalized_ref)
        result["normalized_representation"] = representation

    run = {
        "schema_version": SCHEMA_VERSION,
        "run_id": f"run-{source_id}-{route_id}",
        "source_ref": source_ref,
        "stages": stages,
        "outcome": {
            "execution": execution,
            "assessments": [
                {
                    "scope": "source-text-surface",
                    "completeness": "unknown",
                    "integrity": "unknown",
                    "basis": "adapter has Provider observation only; benchmark gold is not runtime knowledge",
                }
            ],
            "derivation_basis": "E-05b Core orchestration over explicit stage outcomes and produced references",
        },
        "produced": produced,
        "provenance": {
            "started_at": "2026-08-23T00:00:00Z",
            "ended_at": "2026-08-23T00:00:01Z",
            "run_outcome_basis": "Core orchestration over the explicit Provider stage and optional Core normalization stage",
            "provider_native_status_basis": "E-04 Poppler benchmark mapper status",
            "input_fingerprint": fingerprint,
        },
        "diagnostics": _diagnostics(observation.get("warnings")),
    }
    result["run"] = run
    return result


def adapt_direct_epub_observation(
    observation: dict[str, Any],
    *,
    source_id: str,
    fingerprint: str,
    python_version: str,
) -> dict[str, Any]:
    if observation.get("route") != "direct-epub-stdlib":
        raise ValueError(f"unsupported direct EPUB benchmark route: {observation.get('route')!r}")

    source_ref = _source(source_id, "B-02", fingerprint)
    provider = {"provider_id": "python-stdlib", "version": python_version}
    route = {
        "route_profile_id": "direct-epub-stdlib",
        "mode": "package-semantic",
        "execution_context": "local",
    }
    status = str(observation.get("status", "unknown"))
    execution = _execution_from_status(status)
    native_status = _present(
        status,
        "E-04 direct EPUB mapper observation status",
        "benchmark-normalized-view",
        origin="provider-native",
    )
    evidence_id = f"evidence-{source_id}-direct-epub"
    representation_id = f"norm-{source_id}-direct-epub"
    evidence_ref = {
        "kind": "provider-evidence",
        "evidence_id": evidence_id,
        "channel": "benchmark-normalized-view",
    }

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "source_ref": source_ref,
        "provider": provider,
        "route_profile": route,
        "channel": "benchmark-normalized-view",
        "native_status": native_status,
        "payload_locator": "benchmark-observation:direct-epub-stdlib",
        "diagnostics": _diagnostics(observation.get("warnings")),
    }

    resource_order: dict[str, int] = {}
    for index, resource in enumerate(observation.get("resources", [])):
        if isinstance(resource, dict) and isinstance(resource.get("resource"), str):
            resource_order[resource["resource"]] = index

    units: list[dict[str, Any]] = []
    for index, block in enumerate(observation.get("blocks", [])):
        if not isinstance(block, dict) or not isinstance(block.get("text"), str):
            continue
        resource = block.get("resource")
        if isinstance(resource, str) and resource:
            coordinate = _present(
                {
                    "kind": "epub-logical",
                    "resource": resource,
                    "fragment": block.get("fragment"),
                    "spine_index": resource_order.get(resource),
                },
                "direct EPUB mapper supplied package resource and logical fragment",
                "benchmark-normalized-view",
                origin="provider-native",
            )
        else:
            coordinate = _unknown(
                "direct EPUB mapper did not expose a resource for this emitted block",
                "benchmark-normalized-view",
            )
        semantic_value: dict[str, Any] = {"type": block.get("type")}
        if block.get("level") is not None:
            semantic_value["level"] = block.get("level")
        units.append(
            {
                "unit_id": f"block-{index}",
                "surface": _present(
                    block["text"],
                    "direct EPUB mapper emitted XHTML-derived surface text",
                    "benchmark-normalized-view",
                    origin="provider-native",
                ),
                "semantic_role": _present(
                    semantic_value,
                    "direct EPUB mapper classified explicit XHTML element type",
                    "benchmark-normalized-view",
                    origin="provider-native",
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
                "basis": "preserved direct-parser block sequence across EPUB resource order",
            }
        )

    representation = {
        "schema_version": SCHEMA_VERSION,
        "representation_id": representation_id,
        "source_ref": source_ref,
        "units": units,
        "relations": relations,
        "diagnostics": _diagnostics(observation.get("warnings")),
    }

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
        "outcome": _provider_stage_outcome(status, "provider-package-evidence"),
        "reconciliation_state": "not-applicable",
        "produced": [evidence_ref],
    }
    stages = [provider_stage]
    produced: list[dict[str, Any]] = [evidence_ref]
    result: dict[str, Any] = {
        "provider_evidence": evidence,
    }

    if execution == "completed":
        normalized_ref = {
            "kind": "normalized-representation",
            "representation_id": representation_id,
        }
        stages.append(
            _normalization_stage(
                stage_id="normalize-1",
                parent_stage_id="native-1",
                input_refs=[evidence_ref],
                representation_id=representation_id,
            )
        )
        produced.append(normalized_ref)
        result["normalized_representation"] = representation

    run = {
        "schema_version": SCHEMA_VERSION,
        "run_id": f"run-{source_id}-direct-epub",
        "source_ref": source_ref,
        "stages": stages,
        "outcome": {
            "execution": execution,
            "assessments": [
                {
                    "scope": "source-content-and-structure",
                    "completeness": "unknown",
                    "integrity": "unknown",
                    "basis": "adapter preserves emitted package evidence but does not import benchmark gold as runtime truth",
                }
            ],
            "derivation_basis": "E-05b Core orchestration over explicit direct-parser and normalization stages",
        },
        "produced": produced,
        "provenance": {
            "started_at": "2026-08-23T00:00:00Z",
            "ended_at": "2026-08-23T00:00:01Z",
            "run_outcome_basis": "Core orchestration over explicit direct-parser stage outcome and optional normalization stage",
            "provider_native_status_basis": "E-04 direct EPUB benchmark mapper status",
            "input_fingerprint": fingerprint,
        },
        "diagnostics": _diagnostics(observation.get("warnings")),
    }
    result["run"] = run
    return result
