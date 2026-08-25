#!/usr/bin/env python3
"""Core-owned E-05 adapter for the official direct EPUB provider observation.

The ExtractorPlugin emits provider-native observation evidence. This module runs
inside Raiatea Core and owns the normalized representation/stage semantics.
"""
from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1.0"
CHANNEL = "official-local-extractor"


def _source(source_id: str, fingerprint: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_class": "B-02",
        "fingerprint": fingerprint,
    }


def _present(
    value: Any,
    basis: str,
    *,
    origin: str = "provider-native",
) -> dict[str, Any]:
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


def _provider_stage_outcome(status: str) -> dict[str, Any]:
    return {
        "execution": _execution_from_status(status),
        "assessments": [
            {
                "scope": "provider-package-evidence",
                "completeness": "unknown",
                "integrity": "unknown",
                "basis": (
                    "The official local parser emitted provider evidence; no gold "
                    "or external completeness oracle is treated as runtime truth"
                ),
            }
        ],
        "derivation_basis": (
            "E-05 stage assessment preserves the parser-native status separately "
            "from Raiatea normalization"
        ),
    }


def _normalization_stage(
    evidence_ref: dict[str, Any],
    representation_id: str,
) -> dict[str, Any]:
    return {
        "stage_id": "normalize-1",
        "stage_kind": "normalization",
        "executor": {
            "kind": "raiatea-core",
            "operation_id": "normalize-provider-evidence",
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
                        "Raiatea Core produced a structurally valid normalized "
                        "representation; source completeness remains unestablished"
                    ),
                }
            ],
            "derivation_basis": (
                "Raiatea Core normalization over explicit ProviderEvidence references"
            ),
        },
        "reconciliation_state": "not-applicable",
        "produced": [
            {
                "kind": "normalized-representation",
                "representation_id": representation_id,
            }
        ],
    }


def adapt_direct_epub_observation(
    observation: dict[str, Any],
    *,
    source_id: str,
    fingerprint: str,
    python_version: str,
    started_at: str,
    ended_at: str,
) -> dict[str, Any]:
    if observation.get("route") != "direct-epub-stdlib":
        raise ValueError("unsupported-product-direct-epub-route")

    source_ref = _source(source_id, fingerprint)
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
        "Official local direct EPUB parser observation status at the E-05 boundary",
        origin="provider-native",
    )
    evidence_id = f"evidence-{source_id}-direct-epub"
    representation_id = f"norm-{source_id}-direct-epub"
    evidence_ref = {
        "kind": "provider-evidence",
        "evidence_id": evidence_id,
        "channel": CHANNEL,
    }

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "source_ref": source_ref,
        "provider": provider,
        "route_profile": route,
        "channel": CHANNEL,
        "native_status": native_status,
        "payload_locator": "plugin-observation:direct-epub-stdlib",
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
                "Official direct EPUB parser supplied package resource and logical fragment",
                origin="provider-native",
            )
        else:
            coordinate = _unknown(
                "Official direct EPUB parser did not expose a resource for this block"
            )
        semantic_value: dict[str, Any] = {"type": block.get("type")}
        if block.get("level") is not None:
            semantic_value["level"] = block.get("level")
        units.append(
            {
                "unit_id": f"block-{index}",
                "surface": _present(
                    block["text"],
                    "Official direct EPUB parser emitted XHTML-derived surface text",
                    origin="provider-native",
                ),
                "semantic_role": _present(
                    semantic_value,
                    "Official direct EPUB parser classified the explicit XHTML element type",
                    origin="provider-native",
                ),
                "coordinate": coordinate,
            }
        )

    relations = [
        {
            "relation_id": f"reading-order-{index}",
            "kind": "reading-order-next",
            "from_ref": units[index]["unit_id"],
            "to_ref": units[index + 1]["unit_id"],
            "evidence_origin": "raiatea-derived",
            "basis": "Preserved parser block sequence across EPUB spine resource order",
        }
        for index in range(len(units) - 1)
    ]
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
        "outcome": _provider_stage_outcome(status),
        "reconciliation_state": "not-applicable",
        "produced": [evidence_ref],
    }
    stages = [provider_stage]
    produced: list[dict[str, Any]] = [evidence_ref]
    result: dict[str, Any] = {"provider_evidence": evidence}

    if execution == "completed":
        normalized_ref = {
            "kind": "normalized-representation",
            "representation_id": representation_id,
        }
        stages.append(_normalization_stage(evidence_ref, representation_id))
        produced.append(normalized_ref)
        result["normalized_representation"] = representation

    result["run"] = {
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
                    "basis": (
                        "The official extractor preserves emitted package evidence; "
                        "no benchmark gold or external oracle is imported as runtime truth"
                    ),
                }
            ],
            "derivation_basis": (
                "E-05 Core orchestration over explicit local parser and Core normalization stages"
            ),
        },
        "produced": produced,
        "provenance": {
            "started_at": started_at,
            "ended_at": ended_at,
            "run_outcome_basis": (
                "Core orchestration over the explicit official parser stage outcome "
                "and optional Core normalization stage"
            ),
            "provider_native_status_basis": (
                "Official local direct EPUB parser observation status"
            ),
            "input_fingerprint": fingerprint,
        },
        "diagnostics": _diagnostics(observation.get("warnings")),
    }
    return result
