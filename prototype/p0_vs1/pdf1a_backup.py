#!/usr/bin/env python3
"""PDF1a restore adapter using the mixed EPUB+PDF physical inventory.

The backup format and authority model remain the accepted VS1f contract. Only
the physical reconciliation engine used during restore is broadened to the
PDF1a supported local media set.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
from typing import Any

from prototype.p0_vs1.backup_contract import BackupContractError, decode_backup
from prototype.p0_vs1.backup_service import (
    BackupServiceError,
    CatalogBackupService,
    _current_present_signature,
    _restore_vs1e,
    _restored_unverified_vs1b,
)
from prototype.p0_vs1.catalog_store import CatalogStateStore, CatalogStoreError
from prototype.p0_vs1.pdf1a import MixedDocumentReconciliationEngine
from prototype.p0_vs1.reconciliation import ReconciliationError, validate_state as validate_vs1b_state
from prototype.p0_vs1.search_service import validate_vs1e_state


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BackupServiceError(message)


class MixedCatalogBackupService(CatalogBackupService):
    """VS1f backup semantics with PDF1a physical restore admission."""

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

        with tempfile.TemporaryDirectory(
            prefix="raiatea-pdf1a-restore-",
            dir=target_store.path.parent,
        ) as temporary:
            temp_path = Path(temporary).resolve() / "catalog.json"
            temp_store = CatalogStateStore(temp_path)
            temp_store.save(base_payload, expected_revision=0)
            engine = MixedDocumentReconciliationEngine(
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

            final_payload = deepcopy(reconciled.payload)
            final_payload["vs1e"] = _restore_vs1e(
                reconciled_payload=final_payload,
                authority=authority,
                scope_ref=self._scope_ref,
                target_revision=1,
            )
            validate_vs1e_state(final_payload["vs1e"], self._scope_ref)

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
            "supported_media_types": ["application/epub+zip", "application/pdf"],
        }
