#!/usr/bin/env python3
"""VS1d Core-owned rights/policy decision for local EPUB extraction.

This is an architectural product policy record, not legal advice or a legal
conclusion. Unlike VS1c reference-only discovery, VS1d crosses source bytes into
an official local extractor process and therefore requires known-permitted
processing-rights evidence for the promoted first slice.
"""
from __future__ import annotations

import hashlib
from typing import Any

from prototype.p0_vs1.core_access import ScopeRegistry
from prototype.p0_vs1.source_contract import canonical_json_bytes


EXTRACTION_RIGHTS_DECISION_VERSION = "raiatea.vs1d.extraction-rights-decision.0.1.0"
RIGHTS_EVIDENCE_STATES = frozenset(
    {"known-permitted", "known-restricted", "unknown", "requires-review"}
)
OFFICIAL_EXTRACTOR_PLUGIN_ID = "org.raiatea.vs1.direct-epub-extractor"
EXTRACTION_PROFILE = "epub-direct-stdlib"


class ExtractionRightsError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionRightsError(message)


def _opaque(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label}-required")
    _require("/" not in value and "\\" not in value, f"{label}-must-be-opaque")
    return value


def _decision_id(basis: dict[str, Any]) -> str:
    return "rights-decision:" + hashlib.sha256(canonical_json_bytes(basis)).hexdigest()


def decide_local_epub_extraction(
    scopes: ScopeRegistry,
    scope_id: str,
    *,
    plugin_id: str,
    rights_evidence_state: str,
) -> dict[str, Any]:
    """Create the narrow VS1d allow decision or fail closed."""

    scopes.require_capability(scope_id, "read-for-processing")
    _opaque(scope_id, "extraction-rights-scope-ref")
    _require(plugin_id == OFFICIAL_EXTRACTOR_PLUGIN_ID, "extraction-rights-plugin-invalid")
    _require(
        rights_evidence_state in RIGHTS_EVIDENCE_STATES,
        "extraction-rights-evidence-state-invalid",
    )
    if rights_evidence_state == "unknown":
        raise ExtractionRightsError("epub-extraction-rights-unknown")
    if rights_evidence_state == "requires-review":
        raise ExtractionRightsError("epub-extraction-rights-review-required")
    if rights_evidence_state == "known-restricted":
        raise ExtractionRightsError("epub-extraction-rights-known-restricted")

    basis = {
        "decision_version": EXTRACTION_RIGHTS_DECISION_VERSION,
        "scope_ref": scope_id,
        "operation": "extract.run",
        "route_profile": EXTRACTION_PROFILE,
        "plugin_id": plugin_id,
        "processing_authority": "user-authorized-local-scope",
        "rights_evidence_state": "known-permitted",
        "policy_outcome": "allow-local-byte-processing",
        "data_flow": "verified-source-bytes-to-core-private-local-extractor-workspace",
        "retention_policy": "catalog-extraction-records",
        "source_bytes_shared": True,
        "source_bytes_destination": "same-host-core-private-workspace",
        "remote_processing": False,
        "redistribution": False,
        "source_filesystem_mutation": False,
        "legal_conclusion": "not-established-by-this-decision",
    }
    decision = {"decision_id": _decision_id(basis), **basis}
    validate_extraction_rights_decision(decision)
    return decision


def validate_extraction_rights_decision(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "extraction-rights-decision-must-be-object")
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
        "legal_conclusion",
    }
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing, f"extraction-rights-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"extraction-rights-unknown-field:{extra[0] if extra else ''}")
    decision_id = _opaque(value["decision_id"], "extraction-rights-decision-id")
    _require(decision_id.startswith("rights-decision:"), "extraction-rights-decision-id-prefix-invalid")
    _require(
        value["decision_version"] == EXTRACTION_RIGHTS_DECISION_VERSION,
        "extraction-rights-version-unsupported",
    )
    _opaque(value["scope_ref"], "extraction-rights-scope-ref")
    _require(value["operation"] == "extract.run", "extraction-rights-operation-invalid")
    _require(value["route_profile"] == EXTRACTION_PROFILE, "extraction-rights-profile-invalid")
    _require(value["plugin_id"] == OFFICIAL_EXTRACTOR_PLUGIN_ID, "extraction-rights-plugin-invalid")
    _require(
        value["processing_authority"] == "user-authorized-local-scope",
        "extraction-rights-authority-invalid",
    )
    _require(
        value["rights_evidence_state"] == "known-permitted",
        "extraction-rights-must-be-known-permitted",
    )
    _require(
        value["policy_outcome"] == "allow-local-byte-processing",
        "extraction-rights-policy-outcome-invalid",
    )
    _require(
        value["data_flow"]
        == "verified-source-bytes-to-core-private-local-extractor-workspace",
        "extraction-rights-data-flow-invalid",
    )
    _require(
        value["retention_policy"] == "catalog-extraction-records",
        "extraction-rights-retention-invalid",
    )
    _require(value["source_bytes_shared"] is True, "extraction-rights-source-bytes-required")
    _require(
        value["source_bytes_destination"] == "same-host-core-private-workspace",
        "extraction-rights-source-destination-invalid",
    )
    _require(value["remote_processing"] is False, "extraction-rights-remote-processing-forbidden")
    _require(value["redistribution"] is False, "extraction-rights-redistribution-forbidden")
    _require(
        value["source_filesystem_mutation"] is False,
        "extraction-rights-source-mutation-forbidden",
    )
    _require(
        value["legal_conclusion"] == "not-established-by-this-decision",
        "extraction-rights-legal-conclusion-invalid",
    )
    basis = dict(value)
    basis.pop("decision_id")
    _require(value["decision_id"] == _decision_id(basis), "extraction-rights-decision-id-mismatch")
    return value
