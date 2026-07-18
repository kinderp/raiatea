#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import check_evidence_compatibility_v2 as exact_checker


def _identity(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "moduleId": document["id"],
        "revision": document["revision"],
    }


def _evidence_identity(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "moduleId": evidence["module"]["id"],
        "revision": evidence["module"]["revision"],
    }


def _exact_preview(
    target_module: dict[str, Any], evidence: dict[str, Any]
) -> list[dict[str, Any]]:
    evidence_by_id = {
        step["stepId"]: step for step in evidence["progress"]["steps"]
    }
    preview: list[dict[str, Any]] = []
    for target_index, target_step in enumerate(target_module["steps"]):
        source = evidence_by_id[target_step["id"]]
        preview.append(
            {
                "stepId": target_step["id"],
                "sourceIndex": source["index"],
                "targetIndex": target_index,
                "sourceTitle": source["title"],
                "targetTitle": target_step["title"],
                "status": "preserved",
                "evidenceDisposition": "copied",
                "evidence": {
                    "attempts": source["attempts"],
                    "correct": source["correct"],
                    "usedRemediation": source["usedRemediation"],
                    "activityCompleted": source["activityCompleted"],
                },
            }
        )
    return preview


def classify(
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    *,
    source_module: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify validated inputs without mutation or persistence."""
    if (source_module is None) != (manifest is None):
        return {
            "classification": "incompatible",
            "source": _evidence_identity(evidence),
            "target": _identity(target_module),
            "manifestStatus": "missing",
            "steps": [],
            "currentPosition": {"status": "invalid"},
            "candidateAvailable": False,
            "summary": "A non-exact transition requires both sourceModule and manifest.",
            "issues": [
                "$.migrationContext: sourceModule and manifest must be supplied together"
            ],
        }

    exact_issues = exact_checker.check_exact_compatibility(target_module, evidence)
    if not exact_issues:
        current = evidence["progress"]
        return {
            "classification": "exact",
            "source": _evidence_identity(evidence),
            "target": _identity(target_module),
            "manifestStatus": "not-needed",
            "steps": _exact_preview(target_module, evidence),
            "currentPosition": {
                "status": "unchanged",
                "stepId": current["currentStepId"],
                "sourceIndex": current["currentStepIndex"],
                "targetIndex": current["currentStepIndex"],
            },
            "candidateAvailable": False,
            "summary": "Evidence already exactly matches the requested target revision.",
            "issues": [],
        }

    if source_module is None:
        return {
            "classification": "incompatible",
            "source": _evidence_identity(evidence),
            "target": _identity(target_module),
            "manifestStatus": "missing",
            "steps": [],
            "currentPosition": {"status": "invalid"},
            "candidateAvailable": False,
            "summary": "Evidence is not an exact target match and no direct migration context was supplied.",
            "issues": [
                "$.migrationContext: non-exact transitions require one exact sourceModule and one direct manifest"
            ],
        }

    return {
        "classification": "unsupported",
        "source": _evidence_identity(evidence),
        "target": _identity(target_module),
        "manifestStatus": "unsupported",
        "steps": [],
        "currentPosition": {"status": "invalid"},
        "candidateAvailable": False,
        "summary": "Manifest interpretation is not implemented in this classifier increment yet.",
        "issues": ["$.manifest: declared migration preview is not implemented yet"],
    }
