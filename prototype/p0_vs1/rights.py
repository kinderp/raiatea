#!/usr/bin/env python3
"""VS1c Core-owned rights/policy decision for local reference-only discovery.

This is an architectural policy record, not legal advice or a legal conclusion.
It deliberately preserves rights-evidence uncertainty instead of converting
mere possession/access into permission.
"""
from __future__ import annotations

import hashlib
from typing import Any

from prototype.p0_vs1.core_access import ScopeRegistry
from prototype.p0_vs1.source_contract import canonical_json_bytes


RIGHTS_DECISION_VERSION = "raiatea.vs1c.rights-decision.0.1.0"
RIGHTS_EVIDENCE_STATES = frozenset(
    {"known-permitted", "known-restricted", "unknown", "requires-review"}
)


class RightsDecisionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RightsDecisionError(message)


def _opaque(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label}-required")
    _require("/" not in value and "\\" not in value, f"{label}-must-be-opaque")
    return value


def _decision_id(basis: dict[str, Any]) -> str:
    return "rights-decision:" + hashlib.sha256(canonical_json_bytes(basis)).hexdigest()


def decide_local_reference_discovery(
    scopes: ScopeRegistry,
    scope_id: str,
    *,
    plugin_id: str,
    rights_evidence_state: str,
) -> dict[str, Any]:
    """Return a narrow allow decision or fail closed for review/restriction.

    `unknown` remains explicitly unknown. The policy permits only a local,
    reference-only metadata flow because no source bytes or redistribution cross
    this VS1c boundary. That policy choice is not a statement that processing
    rights are legally known-permitted.
    """

    scopes.require_capability(scope_id, "observe")
    _opaque(scope_id, "rights-scope-ref")
    _require(isinstance(plugin_id, str) and plugin_id, "rights-plugin-id-required")
    _require(rights_evidence_state in RIGHTS_EVIDENCE_STATES, "rights-evidence-state-invalid")

    if rights_evidence_state == "known-restricted":
        raise RightsDecisionError("source-discovery-rights-known-restricted")
    if rights_evidence_state == "requires-review":
        raise RightsDecisionError("source-discovery-rights-review-required")

    policy_outcome = (
        "allow-local-reference-only"
        if rights_evidence_state == "known-permitted"
        else "allow-local-reference-only-with-unknown-rights-evidence"
    )
    basis = {
        "decision_version": RIGHTS_DECISION_VERSION,
        "scope_ref": scope_id,
        "operation": "source.discover",
        "route_profile": "local-catalog-read-only",
        "plugin_id": plugin_id,
        "processing_authority": "user-authorized-local-scope",
        "rights_evidence_state": rights_evidence_state,
        "policy_outcome": policy_outcome,
        "data_flow": "local-control-plane-metadata-to-local-official-plugin",
        "retention_policy": "reference-only",
        "source_bytes_shared": False,
        "redistribution": False,
        "legal_conclusion": "not-established-by-this-decision",
    }
    decision = {"decision_id": _decision_id(basis), **basis}
    validate_rights_decision(decision)
    return decision


def validate_rights_decision(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "rights-decision-must-be-object")
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
        "redistribution",
        "legal_conclusion",
    }
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing, f"rights-decision-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"rights-decision-unknown-field:{extra[0] if extra else ''}")
    decision_id = _opaque(value["decision_id"], "rights-decision-id")
    _require(decision_id.startswith("rights-decision:"), "rights-decision-id-prefix-invalid")
    _require(value["decision_version"] == RIGHTS_DECISION_VERSION, "rights-decision-version-unsupported")
    _opaque(value["scope_ref"], "rights-scope-ref")
    _require(value["operation"] == "source.discover", "rights-operation-invalid")
    _require(value["route_profile"] == "local-catalog-read-only", "rights-route-profile-invalid")
    _require(isinstance(value["plugin_id"], str) and value["plugin_id"], "rights-plugin-id-required")
    _require(value["processing_authority"] == "user-authorized-local-scope", "rights-processing-authority-invalid")
    _require(value["rights_evidence_state"] in RIGHTS_EVIDENCE_STATES, "rights-evidence-state-invalid")
    _require(value["rights_evidence_state"] not in {"known-restricted", "requires-review"}, "rights-decision-must-fail-closed")
    expected_outcome = (
        "allow-local-reference-only"
        if value["rights_evidence_state"] == "known-permitted"
        else "allow-local-reference-only-with-unknown-rights-evidence"
    )
    _require(value["policy_outcome"] == expected_outcome, "rights-policy-outcome-invalid")
    _require(
        value["data_flow"] == "local-control-plane-metadata-to-local-official-plugin",
        "rights-data-flow-invalid",
    )
    _require(value["retention_policy"] == "reference-only", "rights-retention-policy-invalid")
    _require(value["source_bytes_shared"] is False, "rights-source-bytes-must-not-be-shared")
    _require(value["redistribution"] is False, "rights-redistribution-must-be-false")
    _require(value["legal_conclusion"] == "not-established-by-this-decision", "rights-legal-conclusion-invalid")

    basis = dict(value)
    basis.pop("decision_id")
    _require(value["decision_id"] == _decision_id(basis), "rights-decision-id-mismatch")
    return value
