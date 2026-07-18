#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import string
from dataclasses import dataclass
from typing import Any

import check_evidence_compatibility_v2 as exact_checker
import preview_evidence_migration_v2 as preview_engine
import validate_evidence_export_v2 as evidence_validator
import validate_evidence_migration_manifest as manifest_validator
import validate_module_v2 as module_validator

CONTRACT_VERSION = 1
CONFIRMATION_PREFIX = "raiatea-confirm-v1:"
ELIGIBLE_CLASSIFICATIONS = {"declared-lossless", "declared-partial"}


class EvidenceMigrationApplicationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


@dataclass(frozen=True)
class _PreparedMigration:
    public: dict[str, Any]
    evidence: dict[str, Any]
    candidate: dict[str, Any]


def _prefixed_issue(namespace: str, issue: object) -> str:
    text = str(issue)
    if text.startswith("$"):
        return f"$.{namespace}{text[1:]}"
    return f"$.{namespace}: {text}"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validated_snapshots(
    evidence: Any,
    target_module: Any,
    source_module: Any | None,
    manifest: Any | None,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any] | None,
    dict[str, Any] | None,
]:
    if (source_module is None) != (manifest is None):
        raise EvidenceMigrationApplicationError(
            ["$.migrationContext: sourceModule and manifest must be supplied together"]
        )

    evidence_snapshot = copy.deepcopy(evidence)
    target_snapshot = copy.deepcopy(target_module)
    source_snapshot = copy.deepcopy(source_module)
    manifest_snapshot = copy.deepcopy(manifest)

    issues: list[str] = []
    issues.extend(
        _prefixed_issue("evidence", issue)
        for issue in evidence_validator.validate_evidence_export_v2(evidence_snapshot)
    )
    issues.extend(
        _prefixed_issue("targetModule", issue)
        for issue in module_validator.validate_module(target_snapshot)
    )
    if source_snapshot is not None:
        issues.extend(
            _prefixed_issue("sourceModule", issue)
            for issue in module_validator.validate_module(source_snapshot)
        )
    if manifest_snapshot is not None:
        issues.extend(
            _prefixed_issue("manifest", issue)
            for issue in manifest_validator.validate_migration_manifest(manifest_snapshot)
        )
    if issues:
        raise EvidenceMigrationApplicationError(issues)

    if not isinstance(evidence_snapshot, dict) or not isinstance(target_snapshot, dict):
        raise AssertionError("validated application inputs unexpectedly unavailable")
    if source_snapshot is not None and not isinstance(source_snapshot, dict):
        raise AssertionError("validated source module unexpectedly unavailable")
    if manifest_snapshot is not None and not isinstance(manifest_snapshot, dict):
        raise AssertionError("validated manifest unexpectedly unavailable")
    return evidence_snapshot, target_snapshot, source_snapshot, manifest_snapshot


def _candidate_issues(
    candidate: dict[str, Any], target_module: dict[str, Any]
) -> list[str]:
    structural = evidence_validator.validate_evidence_export_v2(candidate)
    contextual = exact_checker.check_exact_compatibility(target_module, candidate)
    return [
        _prefixed_issue("preview.candidate", issue)
        for issue in structural + contextual
    ]


def _confirmation_projection(
    *,
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    source_module: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
    preview: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contractVersion": CONTRACT_VERSION,
        "evidence": copy.deepcopy(evidence),
        "sourceModule": copy.deepcopy(source_module),
        "targetModule": copy.deepcopy(target_module),
        "manifest": copy.deepcopy(manifest),
        "preview": copy.deepcopy(preview),
    }


def _prepare_internal(
    evidence: Any,
    target_module: Any,
    *,
    source_module: Any | None,
    manifest: Any | None,
) -> _PreparedMigration:
    (
        evidence_snapshot,
        target_snapshot,
        source_snapshot,
        manifest_snapshot,
    ) = _validated_snapshots(evidence, target_module, source_module, manifest)

    try:
        preview = preview_engine.classify_preview(
            evidence_snapshot,
            target_snapshot,
            source_module=source_snapshot,
            manifest=manifest_snapshot,
        )
    except preview_engine.EvidenceMigrationPreviewInputError as exc:
        raise EvidenceMigrationApplicationError(list(exc.issues)) from exc

    classification = preview["classification"]
    if classification == "exact":
        raise EvidenceMigrationApplicationError(
            ["$.preview.classification: exact evidence requires no migration"]
        )
    if classification not in ELIGIBLE_CLASSIFICATIONS:
        issues = [
            "$.preview.classification: only declared-lossless or "
            "declared-partial results may be applied"
        ]
        issues.extend(
            _prefixed_issue("preview", issue) for issue in preview.get("issues", [])
        )
        raise EvidenceMigrationApplicationError(issues)

    current_position = preview.get("currentPosition")
    if (
        isinstance(current_position, dict)
        and current_position.get("status") == "unresolved-retired"
    ):
        raise EvidenceMigrationApplicationError(
            ["$.preview.currentPosition: unresolved retired position cannot be applied"]
        )

    candidate = preview.get("candidate")
    if not preview.get("candidateAvailable") or not isinstance(candidate, dict):
        raise EvidenceMigrationApplicationError(
            ["$.preview.candidateAvailable: a complete candidate is required"]
        )
    candidate_snapshot = copy.deepcopy(candidate)
    candidate_issues = _candidate_issues(candidate_snapshot, target_snapshot)
    if candidate_issues:
        raise EvidenceMigrationApplicationError(candidate_issues)

    preview_snapshot = copy.deepcopy(preview)
    projection = _confirmation_projection(
        evidence=evidence_snapshot,
        target_module=target_snapshot,
        source_module=source_snapshot,
        manifest=manifest_snapshot,
        preview=preview_snapshot,
    )
    token = CONFIRMATION_PREFIX + hashlib.sha256(
        _canonical_bytes(projection)
    ).hexdigest()
    public = {
        "contractVersion": CONTRACT_VERSION,
        "applicable": True,
        "classification": classification,
        "source": copy.deepcopy(preview_snapshot["source"]),
        "target": copy.deepcopy(preview_snapshot["target"]),
        "manifestStatus": preview_snapshot["manifestStatus"],
        "currentPosition": copy.deepcopy(preview_snapshot["currentPosition"]),
        "candidateDigest": _sha256(candidate_snapshot),
        "confirmationToken": token,
        "summary": (
            "Migration prepared in memory; explicit exact-token confirmation is required."
        ),
    }
    return _PreparedMigration(
        public=public,
        evidence=evidence_snapshot,
        candidate=candidate_snapshot,
    )


def prepare_migration(
    evidence: Any,
    target_module: Any,
    *,
    source_module: Any | None = None,
    manifest: Any | None = None,
) -> dict[str, Any]:
    """Validate and prepare one eligible migration without mutating inputs."""
    return copy.deepcopy(
        _prepare_internal(
            evidence,
            target_module,
            source_module=source_module,
            manifest=manifest,
        ).public
    )


def _valid_confirmation_token(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith(CONFIRMATION_PREFIX):
        return False
    digest = value[len(CONFIRMATION_PREFIX) :]
    return len(digest) == 64 and all(character in string.hexdigits for character in digest)


def apply_confirmed_migration(
    evidence: Any,
    target_module: Any,
    *,
    source_module: Any | None = None,
    manifest: Any | None = None,
    confirmed: bool,
    confirmation_token: str | None,
) -> dict[str, Any]:
    """Recompute, revalidate, and apply one migration entirely in memory."""
    if confirmed is not True:
        raise EvidenceMigrationApplicationError(
            ["$.confirmation.confirmed: explicit confirmation is required"]
        )
    if not _valid_confirmation_token(confirmation_token):
        raise EvidenceMigrationApplicationError(
            ["$.confirmation.token: malformed confirmation token"]
        )

    prepared = _prepare_internal(
        evidence,
        target_module,
        source_module=source_module,
        manifest=manifest,
    )
    expected_token = prepared.public["confirmationToken"]
    assert isinstance(confirmation_token, str)
    if not hmac.compare_digest(confirmation_token, expected_token):
        raise EvidenceMigrationApplicationError(
            ["$.confirmation.token: confirmation does not match current preparation"]
        )

    return {
        "contractVersion": CONTRACT_VERSION,
        "applied": True,
        "source": copy.deepcopy(prepared.public["source"]),
        "target": copy.deepcopy(prepared.public["target"]),
        "classification": prepared.public["classification"],
        "manifestStatus": prepared.public["manifestStatus"],
        "candidateDigest": prepared.public["candidateDigest"],
        "confirmationToken": expected_token,
        "original": copy.deepcopy(prepared.evidence),
        "migrated": copy.deepcopy(prepared.candidate),
        "summary": "Confirmed migration applied in memory; original preserved separately.",
    }
