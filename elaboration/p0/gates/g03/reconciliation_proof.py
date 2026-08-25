#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
from typing import Iterable


class ReconciliationProofError(ValueError):
    pass


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class StoredInstanceEvidence:
    """Proof-only state. This is not a production catalog schema."""

    logical_id: str
    instance_id: str
    current_location: str
    fingerprint: str
    filesystem_identity: str | None
    location_history: tuple[str, ...] = ()
    availability: str = "known-present"


@dataclass(frozen=True)
class ReconciliationOutcome:
    kind: str
    logical_id: str | None
    instance_ids: tuple[str, ...]
    evidence_basis: tuple[str, ...]
    destructive: bool = False
    requires_review: bool = False


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ReconciliationProofError(f"{label}-required")


def validate_instance(value: StoredInstanceEvidence) -> None:
    _require_text(value.logical_id, "logical-id")
    _require_text(value.instance_id, "instance-id")
    _require_text(value.current_location, "current-location")
    if not value.fingerprint.startswith("sha256:") or len(value.fingerprint) != 71:
        raise ReconciliationProofError("fingerprint-invalid")
    if value.availability not in {
        "known-present",
        "unavailable-or-unknown",
        "confirmed-missing-at-location",
    }:
        raise ReconciliationProofError("availability-invalid")


def exact_duplicate_evidence(
    left: StoredInstanceEvidence,
    right: StoredInstanceEvidence,
) -> ReconciliationOutcome:
    validate_instance(left)
    validate_instance(right)
    if left.instance_id == right.instance_id:
        raise ReconciliationProofError("duplicate-comparison-requires-distinct-instances")
    if left.fingerprint != right.fingerprint:
        return ReconciliationOutcome(
            kind="not-exact-duplicate",
            logical_id=None,
            instance_ids=(left.instance_id, right.instance_id),
            evidence_basis=("sha256-differs",),
        )
    return ReconciliationOutcome(
        kind="exact-duplicate-distinct-instances",
        logical_id=None,
        instance_ids=(left.instance_id, right.instance_id),
        evidence_basis=("sha256-equal", "stored-instance-ids-distinct"),
        destructive=False,
        requires_review=False,
    )


def location_transition(
    existing: StoredInstanceEvidence,
    *,
    old_location: str,
    new_location: str,
    observed_fingerprint: str,
    observed_filesystem_identity: str | None,
) -> tuple[StoredInstanceEvidence, ReconciliationOutcome]:
    """Model a conservative rename/move candidate.

    A matching prior path plus compatible byte/fs evidence is enough for this bounded
    proof to preserve the *candidate* logical identity and location history. The
    outcome deliberately does not create authority to mutate anything.
    """

    validate_instance(existing)
    _require_text(old_location, "old-location")
    _require_text(new_location, "new-location")
    if old_location != existing.current_location:
        raise ReconciliationProofError("transition-old-location-mismatch")
    if observed_fingerprint != existing.fingerprint:
        raise ReconciliationProofError("transition-fingerprint-mismatch")
    if (
        existing.filesystem_identity is not None
        and observed_filesystem_identity is not None
        and observed_filesystem_identity != existing.filesystem_identity
    ):
        raise ReconciliationProofError("transition-filesystem-identity-mismatch")

    basis = ["old-location-matches", "sha256-equal"]
    if existing.filesystem_identity and observed_filesystem_identity:
        basis.append("filesystem-identity-equal")
    else:
        basis.append("filesystem-identity-not-required-as-universal-identity")

    history = existing.location_history + (existing.current_location,)
    updated = replace(
        existing,
        current_location=new_location,
        location_history=history,
        filesystem_identity=observed_filesystem_identity or existing.filesystem_identity,
        availability="known-present",
    )
    return updated, ReconciliationOutcome(
        kind="preserve-logical-identity-candidate",
        logical_id=existing.logical_id,
        instance_ids=(existing.instance_id,),
        evidence_basis=tuple(basis),
        destructive=False,
    )


def same_path_changed_bytes(
    existing: StoredInstanceEvidence,
    *,
    observed_fingerprint: str,
) -> ReconciliationOutcome:
    validate_instance(existing)
    if observed_fingerprint == existing.fingerprint:
        return ReconciliationOutcome(
            kind="content-unchanged-by-fingerprint",
            logical_id=existing.logical_id,
            instance_ids=(existing.instance_id,),
            evidence_basis=("same-location", "sha256-equal"),
        )
    return ReconciliationOutcome(
        kind="content-version-reconciliation-required",
        logical_id=existing.logical_id,
        instance_ids=(existing.instance_id,),
        evidence_basis=("same-location", "sha256-changed", "path-is-not-content-identity"),
        destructive=False,
        requires_review=True,
    )


def copy_candidate(
    source: StoredInstanceEvidence,
    *,
    copied_instance_id: str,
    copied_location: str,
    copied_fingerprint: str,
    copied_filesystem_identity: str | None,
) -> tuple[StoredInstanceEvidence, ReconciliationOutcome]:
    validate_instance(source)
    _require_text(copied_instance_id, "copied-instance-id")
    _require_text(copied_location, "copied-location")
    if copied_instance_id == source.instance_id:
        raise ReconciliationProofError("copy-requires-distinct-instance-id")

    copy = StoredInstanceEvidence(
        logical_id=f"candidate:{copied_instance_id}",
        instance_id=copied_instance_id,
        current_location=copied_location,
        fingerprint=copied_fingerprint,
        filesystem_identity=copied_filesystem_identity,
    )
    validate_instance(copy)
    if copied_fingerprint != source.fingerprint:
        return copy, ReconciliationOutcome(
            kind="copy-bytes-differ",
            logical_id=None,
            instance_ids=(source.instance_id, copy.instance_id),
            evidence_basis=("sha256-differs", "stored-instance-ids-distinct"),
        )
    return copy, ReconciliationOutcome(
        kind="exact-duplicate-copy-candidate",
        logical_id=None,
        instance_ids=(source.instance_id, copy.instance_id),
        evidence_basis=(
            "sha256-equal",
            "stored-instance-ids-distinct",
            "locations-distinct",
            "copy-does-not-authorize-destructive-merge",
        ),
        destructive=False,
        requires_review=False,
    )


def ambiguous_copy_delete(
    deleted: StoredInstanceEvidence,
    candidates: Iterable[StoredInstanceEvidence],
) -> ReconciliationOutcome:
    validate_instance(deleted)
    matches = []
    for candidate in candidates:
        validate_instance(candidate)
        if candidate.fingerprint == deleted.fingerprint:
            matches.append(candidate)

    if len(matches) != 1:
        return ReconciliationOutcome(
            kind="ambiguous-unresolved",
            logical_id=deleted.logical_id,
            instance_ids=(deleted.instance_id, *(item.instance_id for item in matches)),
            evidence_basis=(
                "copy-delete-transition-not-proven",
                f"exact-byte-candidate-count:{len(matches)}",
                "list-order-and-path-similarity-forbidden-as-tie-breakers",
            ),
            destructive=False,
            requires_review=True,
        )

    candidate = matches[0]
    if (
        deleted.filesystem_identity is not None
        and candidate.filesystem_identity is not None
        and candidate.filesystem_identity == deleted.filesystem_identity
    ):
        return ReconciliationOutcome(
            kind="location-transition-candidate",
            logical_id=deleted.logical_id,
            instance_ids=(deleted.instance_id, candidate.instance_id),
            evidence_basis=("sha256-equal", "filesystem-identity-equal"),
            destructive=False,
            requires_review=False,
        )

    return ReconciliationOutcome(
        kind="ambiguous-unresolved",
        logical_id=deleted.logical_id,
        instance_ids=(deleted.instance_id, candidate.instance_id),
        evidence_basis=(
            "sha256-equal",
            "filesystem-identity-does-not-prove-continuity",
            "copy-vs-cross-filesystem-move-unresolved",
        ),
        destructive=False,
        requires_review=True,
    )


def mark_scope_unavailable(
    instances: Iterable[StoredInstanceEvidence],
) -> tuple[StoredInstanceEvidence, ...]:
    result = []
    for instance in instances:
        validate_instance(instance)
        result.append(replace(instance, availability="unavailable-or-unknown"))
    return tuple(result)


def observe_location_delete(
    existing: StoredInstanceEvidence,
    *,
    location: str,
) -> tuple[StoredInstanceEvidence, ReconciliationOutcome]:
    validate_instance(existing)
    if location != existing.current_location:
        raise ReconciliationProofError("delete-location-mismatch")
    updated = replace(existing, availability="confirmed-missing-at-location")
    return updated, ReconciliationOutcome(
        kind="location-disappeared-observed",
        logical_id=existing.logical_id,
        instance_ids=(existing.instance_id,),
        evidence_basis=("filesystem-delete-observation", "logical-history-retained"),
        destructive=False,
        requires_review=False,
    )
