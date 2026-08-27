#!/usr/bin/env python3
"""PDF1b Core-owned rights decision for local Poppler PDF extraction.

Architectural product policy evidence, not legal advice or a legal conclusion.
PDF1b crosses PDF source bytes into a same-host official Poppler extractor and
therefore requires explicit known-permitted processing-rights evidence.
"""
from __future__ import annotations

import hashlib
from typing import Any

from prototype.p0_vs1.core_access import ScopeRegistry
from prototype.p0_vs1.source_contract import canonical_json_bytes


PDF1B_RIGHTS_DECISION_VERSION = "raiatea.pdf1b.rights-decision.0.1.0"
RIGHTS_EVIDENCE_STATES = frozenset(
    {"known-permitted", "known-restricted", "unknown", "requires-review"}
)
POPPLER_PLUGIN_ID = "org.raiatea.pdf1.poppler-extractor"
POPPLER_PROFILE = "pdf-poppler-pdftohtml-xml"


class PdfRightsError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PdfRightsError(message)


def _opaque(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label}-required")
    _require("/" not in value and "\\" not in value, f"{label}-must-be-opaque")
    return value


def _decision_id(basis: dict[str, Any]) -> str:
    return "rights-decision:" + hashlib.sha256(canonical_json_bytes(basis)).hexdigest()


def decide_local_poppler_pdf_extraction(
    scopes: ScopeRegistry,
    scope_id: str,
    *,
    plugin_id: str,
    rights_evidence_state: str,
) -> dict[str, Any]:
    scopes.require_capability(scope_id, "read-for-processing")
    _opaque(scope_id, "pdf-rights-scope-ref")
    _require(plugin_id == POPPLER_PLUGIN_ID, "pdf-rights-plugin-invalid")
    _require(
        rights_evidence_state in RIGHTS_EVIDENCE_STATES,
        "pdf-rights-evidence-state-invalid",
    )
    if rights_evidence_state == "unknown":
        raise PdfRightsError("pdf-extraction-rights-unknown")
    if rights_evidence_state == "requires-review":
        raise PdfRightsError("pdf-extraction-rights-review-required")
    if rights_evidence_state == "known-restricted":
        raise PdfRightsError("pdf-extraction-rights-known-restricted")

    basis = {
        "decision_version": PDF1B_RIGHTS_DECISION_VERSION,
        "scope_ref": scope_id,
        "operation": "extract.run",
        "route_profile": POPPLER_PROFILE,
        "plugin_id": plugin_id,
        "processing_authority": "user-authorized-local-scope",
        "rights_evidence_state": "known-permitted",
        "policy_outcome": "allow-local-byte-processing",
        "data_flow": "verified-pdf-bytes-to-core-private-local-poppler-workspace",
        "retention_policy": "catalog-pdf-provider-and-normalized-evidence",
        "source_bytes_shared": True,
        "source_bytes_destination": "same-host-core-private-workspace",
        "remote_processing": False,
        "redistribution": False,
        "source_filesystem_mutation": False,
        "credentials_supplied": False,
        "access_control_override": False,
        "legal_conclusion": "not-established-by-this-decision",
    }
    decision = {"decision_id": _decision_id(basis), **basis}
    validate_pdf_rights_decision(decision)
    return decision


def validate_pdf_rights_decision(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "pdf-rights-decision-must-be-object")
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
        "legal_conclusion",
    }
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing, f"pdf-rights-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"pdf-rights-unknown-field:{extra[0] if extra else ''}")
    decision_id = _opaque(value["decision_id"], "pdf-rights-decision-id")
    _require(decision_id.startswith("rights-decision:"), "pdf-rights-id-prefix-invalid")
    _require(value["decision_version"] == PDF1B_RIGHTS_DECISION_VERSION, "pdf-rights-version-unsupported")
    _opaque(value["scope_ref"], "pdf-rights-scope-ref")
    _require(value["operation"] == "extract.run", "pdf-rights-operation-invalid")
    _require(value["route_profile"] == POPPLER_PROFILE, "pdf-rights-profile-invalid")
    _require(value["plugin_id"] == POPPLER_PLUGIN_ID, "pdf-rights-plugin-invalid")
    _require(value["processing_authority"] == "user-authorized-local-scope", "pdf-rights-authority-invalid")
    _require(value["rights_evidence_state"] == "known-permitted", "pdf-rights-must-be-known-permitted")
    _require(value["policy_outcome"] == "allow-local-byte-processing", "pdf-rights-policy-invalid")
    _require(
        value["data_flow"] == "verified-pdf-bytes-to-core-private-local-poppler-workspace",
        "pdf-rights-data-flow-invalid",
    )
    _require(value["retention_policy"] == "catalog-pdf-provider-and-normalized-evidence", "pdf-rights-retention-invalid")
    _require(value["source_bytes_shared"] is True, "pdf-rights-source-bytes-required")
    _require(value["source_bytes_destination"] == "same-host-core-private-workspace", "pdf-rights-destination-invalid")
    _require(value["remote_processing"] is False, "pdf-rights-remote-forbidden")
    _require(value["redistribution"] is False, "pdf-rights-redistribution-forbidden")
    _require(value["source_filesystem_mutation"] is False, "pdf-rights-mutation-forbidden")
    _require(value["credentials_supplied"] is False, "pdf-rights-credentials-forbidden")
    _require(value["access_control_override"] is False, "pdf-rights-override-forbidden")
    _require(value["legal_conclusion"] == "not-established-by-this-decision", "pdf-rights-legal-conclusion-invalid")
    basis = dict(value)
    basis.pop("decision_id")
    _require(value["decision_id"] == _decision_id(basis), "pdf-rights-decision-id-mismatch")
    return value
