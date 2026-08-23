"""Conservative scoring for B01 negative PDF/security fixtures.

Benchmark-only: classifies observed route outcomes without treating Provider-specific
exception strings as gold. Negative fixtures never enter normal quality averages.
"""
from __future__ import annotations

from typing import Any

_MALFORMED_TERMS = ("malformed", "corrupt", "xref", "trailer", "data format", "parse", "syntax error")
_ACCESS_TERMS = ("encrypt", "password", "access control", "restricted", "decrypt")


def _text_evidence(observation: dict[str, Any]) -> str:
    parts = [str(observation.get("stderr", "")), str(observation.get("stdout", ""))]
    for warning in observation.get("warnings", []) if isinstance(observation.get("warnings"), list) else []:
        if isinstance(warning, dict):
            parts.extend([str(warning.get("code", "")), str(warning.get("details", ""))])
    return "\n".join(parts).lower()


def _blocks_count(observation: dict[str, Any]) -> int | None:
    blocks = observation.get("blocks")
    return len(blocks) if isinstance(blocks, list) else None


def classify_negative_result(fixture_id: str, observation: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    status = str(observation.get("status", "unknown"))
    text = _text_evidence(observation)
    blocks = _blocks_count(observation)
    warnings = observation.get("warnings") if isinstance(observation.get("warnings"), list) else None
    audit_passed = audit.get("audit_passed") is True
    password_supplied = audit.get("fixture_password_supplied_to_provider") is True
    bypass_requested = audit.get("access_control_bypass_requested") is True

    result: dict[str, Any] = {
        "fixture_id": fixture_id,
        "route": observation.get("route"),
        "provider_status": status,
        "provider_block_count": blocks,
        "warning_collection_available": warnings is not None,
        "warning_count": len(warnings) if warnings is not None else None,
        "invocation_audit_passed": audit_passed,
        "password_supplied_to_provider": password_supplied,
        "access_control_bypass_requested": bypass_requested,
        "security_policy_satisfied": audit_passed and not password_supplied and not bypass_requested,
        "excluded_from_normal_quality_averages": True,
    }

    if fixture_id == "B01-PDF-NEG-001":
        explicit_signal = any(term in text for term in _MALFORMED_TERMS)
        if status in {"failed", "rejected", "unsupported"}:
            outcome = "failed-with-malformed-signal" if explicit_signal else "safe-failure-generic"
            acceptable = True
            false_complete = False
        elif status in {"degraded", "partial"}:
            outcome = "degraded-or-partial"
            acceptable = True
            false_complete = False
        elif status == "success":
            # A generic/unrelated warning does not make the intentional corruption visible.
            outcome = "success-with-malformed-signal" if explicit_signal else "silent-complete-success"
            acceptable = explicit_signal
            false_complete = not explicit_signal
        else:
            outcome = "unknown"
            acceptable = False
            false_complete = False
        result.update({
            "negative_kind": "malformed",
            "explicit_negative_signal": explicit_signal,
            "normalized_outcome": outcome,
            "acceptable_negative_outcome": acceptable,
            "false_complete_success": false_complete,
        })
        return result

    if fixture_id == "B01-PDF-NEG-002":
        explicit_signal = any(term in text for term in _ACCESS_TERMS)
        inaccessible_empty = blocks == 0 if blocks is not None else None
        if status in {"failed", "rejected", "unsupported"}:
            outcome = "restricted-or-password-required" if explicit_signal else "safe-failure-generic"
            acceptable = True
            false_complete = False
        elif status in {"degraded", "partial"}:
            outcome = "degraded-or-partial-restricted" if explicit_signal else "degraded-or-partial"
            acceptable = True
            false_complete = False
        elif status == "success":
            if explicit_signal:
                outcome = "safe-metadata-or-restricted-success"
                acceptable = True
                false_complete = False
            else:
                outcome = "silent-complete-success-with-inaccessible-content"
                acceptable = False
                false_complete = True
        else:
            outcome = "unknown"
            acceptable = False
            false_complete = False
        result.update({
            "negative_kind": "access-controlled",
            "explicit_access_control_signal": explicit_signal,
            "inaccessible_output_empty": inaccessible_empty,
            "normalized_outcome": outcome,
            "acceptable_negative_outcome": acceptable,
            "false_complete_success": false_complete,
        })
        return result

    raise ValueError(f"Unsupported negative fixture: {fixture_id}")


def score_raw_report(report: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in report.get("results", []):
        if not isinstance(row, dict):
            continue
        rows.append(classify_negative_result(
            str(row.get("fixture_id")),
            row.get("observation") if isinstance(row.get("observation"), dict) else {},
            row.get("provider_invocation_audit") if isinstance(row.get("provider_invocation_audit"), dict) else {},
        ))
    return {
        "contract": {
            "name": "raiatea-p0-b01-negative-result",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
            "negative_security_fixtures": True,
            "excluded_from_normal_quality_averages": True,
        },
        "evidence_source_commit": report.get("evidence_source_commit"),
        "provider_family": report.get("provider_family"),
        "results": rows,
        "all_invocation_audits_passed": all(r["invocation_audit_passed"] for r in rows),
        "any_false_complete_success": any(r["false_complete_success"] for r in rows),
    }
