#!/usr/bin/env python3
"""PDF1c Core-owned rights decision for local Docling PDF extraction.

Architectural product policy evidence, not legal advice or a legal conclusion.
The decision is intentionally route-specific and precedes any Docling provider
preparation, model verification or source-byte processing.
"""
from __future__ import annotations

import hashlib
from typing import Any

from prototype.p0_vs1.core_access import ScopeRegistry
from prototype.p0_vs1.docling_observation_contract import DOCLING_PROFILE
from prototype.p0_vs1.source_contract import canonical_json_bytes


PDF1C_RIGHTS_DECISION_VERSION = "raiatea.pdf1c.rights-decision.0.1.0"
RIGHTS_EVIDENCE_STATES = frozenset(
    {"known-permitted", "known-restricted", "unknown", "requires-review"}
)
DOCLING_PLUGIN_ID = "org.raiatea.pdf1.docling-extractor"


class DoclingPdfRightsError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingPdfRightsError(message)


def _opaque(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label}-required")
    _require("/" not in value and "\\" not in value, f"{label}-must-be-opaque")
    return value


def _decision_id(basis: dict[str, Any]) -> str:
    return "rights-decision:" + hashlib.sha256(canonical_json_bytes(basis)).hexdigest()


def decide_local_docling_pdf_extraction(
    scopes: ScopeRegistry,
    scope_id: str,
    *,
    plugin_id: str,
    rights_evidence_state: str,
) -> dict[str, Any]:
    scopes.require_capability(scope_id, "read-for-processing")
    _opaque(scope_id, "docling-rights-scope-ref")
    _require(plugin_id == DOCLING_PLUGIN_ID, "docling-rights-plugin-invalid")
    _require(
        rights_evidence_state in RIGHTS_EVIDENCE_STATES,
        "docling-rights-evidence-state-invalid",
    )
    if rights_evidence_state == "unknown":
        raise DoclingPdfRightsError("pdf-docling-extraction-rights-unknown")
    if rights_evidence_state == "requires-review":
        raise DoclingPdfRightsError("pdf-docling-extraction-rights-review-required")
    if rights_evidence_state == "known-restricted":
        raise DoclingPdfRightsError("pdf-docling-extraction-rights-known-restricted")

    basis = {
        "decision_version": PDF1C_RIGHTS_DECISION_VERSION,
        "scope_ref": scope_id,
        "operation": "extract.run",
        "route_profile": DOCLING_PROFILE,
        "plugin_id": plugin_id,
        "processing_authority": "user-authorized-local-scope",
        "rights_evidence_state": "known-permitted",
        "policy_outcome": "allow-local-byte-processing",
        "data_flow": "verified-pdf-bytes-to-core-private-local-docling-workspace",
        "retention_policy": "catalog-pdf-provider-and-normalized-evidence",
        "source_bytes_shared": True,
        "source_bytes_destination": "same-host-core-private-workspace",
        "remote_processing": False,
        "redistribution": False,
        "source_filesystem_mutation": False,
        "credentials_supplied": False,
        "access_control_override": False,
        "external_plugins": False,
        "ocr": False,
        "legal_conclusion": "not-established-by-this-decision",
    }
    decision = {"decision_id": _decision_id(basis), **basis}
    validate_docling_pdf_rights_decision(decision)
    return decision


def validate_docling_pdf_rights_decision(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "docling-rights-decision-must-be-object")
    expected = {
        "decision_id",
        "decision_version",
        "scope_ref",
        "operation",
        "route_profile",
        "plugin_id",
        "processing_authority",
        "rights_evidence_state",
        "policy_outcome",
        "data_flow",
        "retention_policy",
        "source_bytes_shared",
        "source_bytes_destination",
        "remote_processing",
        "redistribution",
        "source_filesystem_mutation",
        "credentials_supplied",
        "access_control_override",
        "external_plugins",
        "ocr",
        "legal_conclusion",
    }
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing, f"docling-rights-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"docling-rights-unknown-field:{extra[0] if extra else ''}")
    decision_id = _opaque(value["decision_id"], "docling-rights-decision-id")
    _require(decision_id.startswith("rights-decision:"), "docling-rights-id-prefix-invalid")
    _require(value["decision_version"] == PDF1C_RIGHTS_DECISION_VERSION, "docling-rights-version-unsupported")
    _opaque(value["scope_ref"], "docling-rights-scope-ref")
    _require(value["operation"] == "extract.run", "docling-rights-operation-invalid")
    _require(value["route_profile"] == DOCLING_PROFILE, "docling-rights-profile-invalid")
    _require(value["plugin_id"] == DOCLING_PLUGIN_ID, "docling-rights-plugin-invalid")
    _require(value["processing_authority"] == "user-authorized-local-scope", "docling-rights-authority-invalid")
    _require(value["rights_evidence_state"] == "known-permitted", "docling-rights-must-be-known-permitted")
    _require(value["policy_outcome"] == "allow-local-byte-processing", "docling-rights-policy-invalid")
    _require(
        value["data_flow"] == "verified-pdf-bytes-to-core-private-local-docling-workspace",
        "docling-rights-data-flow-invalid",
    )
    _require(value["retention_policy"] == "catalog-pdf-provider-and-normalized-evidence", "docling-rights-retention-invalid")
    _require(value["source_bytes_shared"] is True, "docling-rights-source-bytes-required")
    _require(value["source_bytes_destination"] == "same-host-core-private-workspace", "docling-rights-destination-invalid")
    _require(value["remote_processing"] is False, "docling-rights-remote-forbidden")
    _require(value["redistribution"] is False, "docling-rights-redistribution-forbidden")
    _require(value["source_filesystem_mutation"] is False, "docling-rights-mutation-forbidden")
    _require(value["credentials_supplied"] is False, "docling-rights-credentials-forbidden")
    _require(value["access_control_override"] is False, "docling-rights-override-forbidden")
    _require(value["external_plugins"] is False, "docling-rights-external-plugins-forbidden")
    _require(value["ocr"] is False, "docling-rights-ocr-forbidden")
    _require(value["legal_conclusion"] == "not-established-by-this-decision", "docling-rights-legal-conclusion-invalid")
    basis = dict(value)
    basis.pop("decision_id")
    _require(value["decision_id"] == _decision_id(basis), "docling-rights-decision-id-mismatch")
    return value
