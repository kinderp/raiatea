#!/usr/bin/env python3
"""VS1f deterministic authority export and transactional restore service."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
from typing import Any

from prototype.p0_vs1.backup_contract import (
    BackupContractError,
    build_backup,
    canonicalize_authority,
    decode_backup,
    encode_backup,
)
from prototype.p0_vs1.catalog_store import (
    CatalogSnapshot,
    CatalogStateStore,
    CatalogStoreError,
)
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.extraction_service import validate_vs1d_state
from prototype.p0_vs1.reconciliation import (
    ReconciliationError,
    Vs1ObservationScopeRegistry,
    Vs1bReconciliationEngine,
    validate_state as validate_vs1b_state,
)
from prototype.p0_vs1.search_contract import (
    SMART_COLLECTION_VERSION,
    build_smart_collection,
    canonical_json_bytes,
    run_search,
    validate_view,
)
from prototype.p0_vs1.search_service import (
    VS1E_STATE_VERSION,
    SearchServiceError,
    build_search_index,
    current_upstream_basis_fingerprint,
    validate_vs1e_state,
)
from prototype.p0_vs1.source_service import validate_vs1c_state


class BackupServiceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BackupServiceError(message)


def _sanitize_runtime_provenance(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "backup-runtime-provenance-invalid")
    result = deepcopy(value)
    # These refs identify temporary Core/plugin I/O objects whose lifecycle ended
    # with the original invocation. Stable Source/E-05 lineage remains in the
    # catalog records themselves and in the remaining invocation provenance.
    result.pop("input_refs", None)
    result.pop("output_refs", None)
    return result


def _sanitized_vs1c(value: dict[str, Any], scope_ref: str) -> dict[str, Any]:
    result = deepcopy(value)
    result["provenance"] = _sanitize_runtime_provenance(result.get("provenance"))
    validate_vs1c_state(result, scope_ref)
    return result


def _sanitized_vs1d(value: dict[str, Any], scope_ref: str) -> dict[str, Any]:
    result = deepcopy(value)
    for row in result.get("extractions", []):
        _require(isinstance(row, dict), "backup-vs1d-extraction-invalid")
        row["provenance"] = _sanitize_runtime_provenance(row.get("provenance"))
    validate_vs1d_state(result, scope_ref)
    return result


def _authority_views(vs1e: dict[str, Any]) -> list[dict[str, Any]]:
    value = vs1e.get("views")
    _require(isinstance(value, list), "backup-vs1e-views-required")
    rows: list[dict[str, Any]] = []
    for raw in value:
        row = deepcopy(raw)
        validate_view(row)
        rows.append(row)
    return rows


def _authority_smart_rules(vs1e: dict[str, Any]) -> list[dict[str, Any]]:
    value = vs1e.get("smart_collections")
    _require(isinstance(value, list), "backup-vs1e-smart-collections-required")
    rows: list[dict[str, Any]] = []
    for raw in value:
        _require(isinstance(raw, dict), "backup-smart-collection-invalid")
        _require(
            raw.get("collection_version") == SMART_COLLECTION_VERSION,
            "backup-smart-collection-version-unsupported",
        )
        collection_id = raw.get("collection_id")
        rule = raw.get("rule")
        _require(
            isinstance(collection_id, str) and collection_id,
            "backup-smart-collection-id-required",
        )
        _require(isinstance(rule, dict), "backup-smart-collection-rule-required")
        rows.append({"collection_id": collection_id, "rule": deepcopy(rule)})
    return rows


def build_backup_authority(
    catalog_snapshot: CatalogSnapshot,
    scope_ref: str,
) -> dict[str, Any]:
    payload = catalog_snapshot.payload
    _require(isinstance(payload, dict), "backup-catalog-payload-invalid")
    vs1b = payload.get("vs1b")
    vs1c = payload.get("vs1c")
    vs1d = payload.get("vs1d")
    vs1e = payload.get("vs1e")
    _require(isinstance(vs1b, dict), "backup-vs1b-required")
    _require(isinstance(vs1c, dict), "backup-vs1c-required")
    _require(isinstance(vs1d, dict), "backup-vs1d-required")
    _require(isinstance(vs1e, dict), "backup-vs1e-required")

    validate_vs1b_state(vs1b, scope_ref)
    validate_vs1c_state(vs1c, scope_ref)
    validate_vs1d_state(vs1d, scope_ref)
    _require(vs1b["freshness"]["status"] == "fresh", "backup-upstream-not-fresh")
    _require(
        vs1e.get("state_version") == VS1E_STATE_VERSION,
        "backup-vs1e-version-unsupported",
    )
    _require(vs1e.get("scope_ref") == scope_ref, "backup-vs1e-scope-mismatch")

    # Rebuild the derived index from authority instead of trusting the persisted
    # VS1e cache. A stale/tampered cache is not backup truth.
    try:
        build_search_index(catalog_snapshot, scope_ref)
    except SearchServiceError as exc:
        raise BackupServiceError(
            f"backup-upstream-search-basis-invalid:{exc}"
        ) from exc

    authority = {
        "vs1b": deepcopy(vs1b),
        "vs1c": _sanitized_vs1c(vs1c, scope_ref),
        "vs1d": _sanitized_vs1d(vs1d, scope_ref),
        "views": _authority_views(vs1e),
        "smart_rules": _authority_smart_rules(vs1e),
    }
    try:
        return canonicalize_authority(authority, scope_ref)
    except BackupContractError as exc:
        raise BackupServiceError(f"backup-authority-invalid:{exc}") from exc


def _current_present_signature(vs1b: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "entry_id": row["entry_id"],
            "logical_candidate_id": row["logical_candidate_id"],
            "stored_instance_id": row["stored_instance_id"],
            "current_location": row["current_location"],
            "fingerprint": row["fingerprint"],
            "byte_length": row["byte_length"],
            "media_type": row["media_type"],
        }
        for row in vs1b["entries"]
        if row["superseded_by"] is None
        and row["availability"] == "known-present"
    ]
    rows.sort(key=lambda row: row["entry_id"])
    return rows


def _restored_unverified_vs1b(
    value: dict[str, Any],
    scope_ref: str,
) -> dict[str, Any]:
    result = deepcopy(value)
    validate_vs1b_state(result, scope_ref)
    result["freshness"] = {
        "status": "reconcile-required",
        "reason": "restore:physical-source-revalidation-required",
    }
    for row in result["entries"]:
        if row["superseded_by"] is None and row["availability"] == "known-present":
            row["availability"] = "unavailable-or-unknown"
            row["reconciliation_status"] = "restore-unverified"
    validate_vs1b_state(result, scope_ref)
    return result


def _restore_vs1e(
    *,
    reconciled_payload: dict[str, Any],
    authority: dict[str, Any],
    scope_ref: str,
    target_revision: int,
) -> dict[str, Any]:
    synthetic = CatalogSnapshot(
        revision=target_revision,
        payload=deepcopy(reconciled_payload),
    )
    try:
        index = build_search_index(synthetic, scope_ref)
        current_basis = current_upstream_basis_fingerprint(synthetic, scope_ref)
    except SearchServiceError as exc:
        raise BackupServiceError(
            f"restore-upstream-lineage-not-current:{exc}"
        ) from exc

    views: list[dict[str, Any]] = []
    for raw in authority["views"]:
        row = deepcopy(raw)
        validate_view(row)
        views.append(row)
    views.sort(key=lambda row: row["view_id"])

    collections: list[dict[str, Any]] = []
    for raw in authority["smart_rules"]:
        result = run_search(
            index,
            current_upstream_basis_fingerprint=current_basis,
            plan=raw["rule"],
        )
        _require(
            result["freshness"] == "fresh",
            "restore-smart-rule-index-not-fresh",
        )
        collection = build_smart_collection(
            raw["collection_id"],
            raw["rule"],
            current_members=result["source_ids"],
            evaluated_upstream_basis_fingerprint=current_basis,
            evaluated_catalog_revision=target_revision,
        )
        collections.append(collection)
    collections.sort(key=lambda row: row["collection_id"])

    state = {
        "state_version": VS1E_STATE_VERSION,
        "scope_ref": scope_ref,
        "index": index,
        "views": views,
        "smart_collections": collections,
    }
    validate_vs1e_state(state, scope_ref)
    return state


class CatalogBackupService:
    def __init__(
        self,
        store: CatalogStateStore,
        scopes: Vs1ObservationScopeRegistry,
        broker: AssetBroker,
        scope_ref: str,
    ) -> None:
        self._store = store
        self._scopes = scopes
        self._broker = broker
        self._scope_ref = scope_ref
        self._scopes.require_capability(scope_ref, "observe")
        self._scopes.require_capability(scope_ref, "read-for-processing")

    def export_bytes(self) -> bytes:
        snapshot = self._store.load()
        _require(snapshot is not None, "backup-catalog-required")
        authority = build_backup_authority(snapshot, self._scope_ref)
        try:
            backup = build_backup(
                scope_ref=self._scope_ref,
                source_catalog_revision=snapshot.revision,
                authority=authority,
            )
            return encode_backup(backup)
        except BackupContractError as exc:
            raise BackupServiceError(f"backup-encode-failed:{exc}") from exc

    def restore_into_empty_store(
        self,
        raw: bytes,
        target_store: CatalogStateStore,
    ) -> dict[str, Any]:
        try:
            backup = decode_backup(raw)
        except BackupContractError as exc:
            raise BackupServiceError(f"restore-backup-invalid:{exc}") from exc
        _require(
            backup["scope_ref"] == self._scope_ref,
            "restore-backup-scope-mismatch",
        )
        _require(
            target_store.load() is None,
            "restore-target-store-must-be-empty",
        )

        authority = backup["authority"]
        expected_present = _current_present_signature(authority["vs1b"])
        base_payload = {
            "vs1b": _restored_unverified_vs1b(
                authority["vs1b"],
                self._scope_ref,
            ),
            "vs1c": deepcopy(authority["vs1c"]),
            "vs1d": deepcopy(authority["vs1d"]),
        }

        # Work in a throwaway catalog so a failed reconciliation or lineage check
        # cannot partially populate the real restore target.
        with tempfile.TemporaryDirectory(
            prefix="raiatea-vs1f-restore-",
            dir=target_store.path.parent,
        ) as temporary:
            temp_path = Path(temporary).resolve() / "catalog.json"
            temp_store = CatalogStateStore(temp_path)
            temp_store.save(base_payload, expected_revision=0)
            engine = Vs1bReconciliationEngine(
                temp_store,
                self._scopes,
                self._broker,
                self._scope_ref,
            )
            try:
                engine.reconcile_inventory()
            except ReconciliationError as exc:
                raise BackupServiceError(
                    f"restore-physical-reconciliation-failed:{exc}"
                ) from exc
            reconciled = temp_store.load()
            _require(
                reconciled is not None,
                "restore-temporary-catalog-missing",
            )
            validate_vs1b_state(reconciled.payload["vs1b"], self._scope_ref)
            _require(
                _current_present_signature(reconciled.payload["vs1b"])
                == expected_present,
                "restore-physical-source-set-mismatch",
            )

            # The real target will be revision 1 after its single atomic save, so
            # build derived audit revision fields against that final target value.
            final_payload = deepcopy(reconciled.payload)
            final_payload["vs1e"] = _restore_vs1e(
                reconciled_payload=final_payload,
                authority=authority,
                scope_ref=self._scope_ref,
                target_revision=1,
            )
            validate_vs1e_state(final_payload["vs1e"], self._scope_ref)

        # Re-check emptiness after the potentially long physical reconciliation.
        _require(
            target_store.load() is None,
            "restore-target-store-changed-during-restore",
        )
        try:
            saved = target_store.save(final_payload, expected_revision=0)
        except CatalogStoreError as exc:
            raise BackupServiceError(
                "restore-target-store-changed-during-commit"
            ) from exc
        _require(saved.revision == 1, "restore-target-revision-unexpected")
        return {
            "status": "completed",
            "catalog_revision": saved.revision,
            "backup_source_catalog_revision": backup["source_catalog_revision"],
            "authority_sha256": backup["authority_sha256"],
            "restored_source_count": len(expected_present),
            "restored_view_count": len(authority["views"]),
            "restored_smart_rule_count": len(authority["smart_rules"]),
            "reconciled_before_publish": True,
        }
