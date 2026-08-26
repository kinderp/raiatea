#!/usr/bin/env python3
"""PDF1a mixed local document inventory and Source discovery.

This increment deliberately reuses the accepted VS1 reconciliation and Source
plugin boundaries. It adds PDF admission to the same catalog; it does not define
a parallel PDF identity model and it performs no PDF extraction.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import stat
from typing import Any

from prototype.p0_vs1.catalog_store import CatalogStoreError
from prototype.p0_vs1.core_access import AssetBroker, CoreAccessError
from prototype.p0_vs1.local_process_client import LocalPluginProcessClient, LocalPluginProcessError
from prototype.p0_vs1.plugin_io import PluginIOError, Vs1PluginIO
from prototype.p0_vs1.reconciliation import (
    ReconciliationError,
    Vs1ObservationScopeRegistry,
    Vs1bReconciliationEngine,
    _is_symlink_or_reparse_stat,
    _reconcile_entries,
    validate_state as validate_vs1b_state,
)
from prototype.p0_vs1.rights import RightsDecisionError, decide_local_reference_discovery
from prototype.p0_vs1.source_contract import (
    DISCOVERY_SNAPSHOT_VERSION,
    EPUB_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    SUPPORTED_SOURCE_MEDIA_TYPES,
    SourceContractError,
    canonical_json_bytes,
    discovery_snapshot_fingerprint,
    sha256_ref,
    validate_discovery_snapshot,
)
from prototype.p0_vs1.source_service import (
    BUNDLE_MEDIA_TYPE,
    MAX_BUNDLE_BYTES,
    SNAPSHOT_MEDIA_TYPE,
    SourceDiscoveryError,
    _discovery_basis_fingerprint,
    _find_completed_asset,
    _invocation_request,
    _load_manifest,
    _validate_plugin_result_against_snapshot,
    _vs1c_state,
)


_EXTENSION_MEDIA = {
    ".epub": EPUB_MEDIA_TYPE,
    ".pdf": PDF_MEDIA_TYPE,
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReconciliationError(message)


def media_type_for_name(name: str) -> str | None:
    if not isinstance(name, str) or not name:
        return None
    return _EXTENSION_MEDIA.get(Path(name).suffix.casefold())


def _inventory_item(
    broker: AssetBroker,
    scope_id: str,
    relative: str,
    media_type: str,
) -> dict[str, Any]:
    try:
        handle = broker.issue_read_handle(
            scope_id,
            relative,
            media_type=media_type,
        )
    except CoreAccessError as exc:
        raise ReconciliationError("inventory-safe-read-failed") from exc
    if handle.get("media_type") != media_type:
        raise ReconciliationError("inventory-handle-media-type-invalid")
    fingerprint = handle.get("fingerprint")
    byte_length = handle.get("byte_length")
    if not (
        isinstance(fingerprint, str)
        and fingerprint.startswith("sha256:")
        and len(fingerprint) == 71
    ):
        raise ReconciliationError("inventory-handle-fingerprint-invalid")
    if not (
        isinstance(byte_length, int)
        and not isinstance(byte_length, bool)
        and byte_length >= 0
    ):
        raise ReconciliationError("inventory-handle-byte-length-invalid")
    return {
        "location": relative,
        "fingerprint": fingerprint,
        "byte_length": byte_length,
        "media_type": media_type,
    }


def _scan_posix(
    scopes: Vs1ObservationScopeRegistry,
    broker: AssetBroker,
    scope_id: str,
) -> list[dict[str, Any]]:
    _, root_fd = scopes._inventory_root(scope_id)
    _require(root_fd is not None, "inventory-posix-root-fd-required")
    stack: list[tuple[tuple[str, ...], int]] = [((), os.dup(root_fd))]
    discovered: list[dict[str, Any]] = []
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    try:
        while stack:
            relative_parts, directory_fd = stack.pop()
            try:
                with os.scandir(directory_fd) as iterator:
                    entries = sorted(iterator, key=lambda entry: entry.name.casefold())
                for entry in entries:
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        raise ReconciliationError("inventory-entry-stat-failed") from exc
                    if _is_symlink_or_reparse_stat(info):
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        try:
                            child_fd = os.open(
                                entry.name,
                                os.O_RDONLY | os.O_DIRECTORY | nofollow | cloexec,
                                dir_fd=directory_fd,
                            )
                        except OSError as exc:
                            raise ReconciliationError("inventory-directory-open-failed") from exc
                        stack.append((relative_parts + (entry.name,), child_fd))
                        continue
                    if not stat.S_ISREG(info.st_mode):
                        continue
                    media_type = media_type_for_name(entry.name)
                    if media_type is None:
                        continue
                    relative = "/".join(relative_parts + (entry.name,))
                    discovered.append(
                        _inventory_item(broker, scope_id, relative, media_type)
                    )
            finally:
                os.close(directory_fd)
    except Exception:
        for _, directory_fd in stack:
            try:
                os.close(directory_fd)
            except OSError:
                pass
        raise
    discovered.sort(key=lambda item: item["location"])
    return discovered


def _scan_path(
    scopes: Vs1ObservationScopeRegistry,
    broker: AssetBroker,
    scope_id: str,
) -> list[dict[str, Any]]:
    root, _ = scopes._inventory_root(scope_id)
    stack = [root]
    discovered: list[dict[str, Any]] = []
    while stack:
        directory = stack.pop()
        try:
            directory_info = os.lstat(directory)
        except OSError as exc:
            raise ReconciliationError("inventory-directory-stat-failed") from exc
        _require(
            not _is_symlink_or_reparse_stat(directory_info),
            "inventory-directory-reparse-forbidden",
        )
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name.casefold())
        except OSError as exc:
            raise ReconciliationError("inventory-directory-scan-failed") from exc
        for entry in entries:
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ReconciliationError("inventory-entry-stat-failed") from exc
            if _is_symlink_or_reparse_stat(info):
                continue
            entry_path = Path(entry.path)
            if stat.S_ISDIR(info.st_mode):
                stack.append(entry_path)
                continue
            if not stat.S_ISREG(info.st_mode):
                continue
            media_type = media_type_for_name(entry.name)
            if media_type is None:
                continue
            try:
                relative = entry_path.relative_to(root).as_posix()
            except ValueError as exc:
                raise ReconciliationError("inventory-location-outside-scope") from exc
            discovered.append(_inventory_item(broker, scope_id, relative, media_type))
    discovered.sort(key=lambda item: item["location"])
    return discovered


def scan_supported_document_inventory(
    scopes: Vs1ObservationScopeRegistry,
    broker: AssetBroker,
    scope_id: str,
) -> list[dict[str, Any]]:
    """Return the bounded EPUB+PDF inventory in deterministic Location order."""

    return (
        _scan_path(scopes, broker, scope_id)
        if os.name == "nt"
        else _scan_posix(scopes, broker, scope_id)
    )


class MixedDocumentReconciliationEngine(Vs1bReconciliationEngine):
    """VS1 reconciliation engine with PDF1a mixed-document inventory admission."""

    def reconcile_inventory(self) -> dict[str, Any]:
        revision, payload, state = self._load()
        inventory = scan_supported_document_inventory(
            self._scopes,
            self._broker,
            self._scope_id,
        )
        _reconcile_entries(state, inventory)
        state["freshness"] = {
            "status": "fresh",
            "reason": "bounded-inventory-complete",
        }
        state["stream"]["last_reconciled_seq"] = state["stream"]["last_seq"]
        validate_vs1b_state(state, self._scope_id)
        payload["vs1b"] = state
        try:
            saved = self._store.save(payload, expected_revision=revision)
        except CatalogStoreError as exc:
            raise ReconciliationError("inventory-state-changed-during-scan") from exc
        return {
            "revision": saved.revision,
            "inventory_count": len(inventory),
            "freshness": deepcopy(state["freshness"]),
            "last_reconciled_seq": state["stream"]["last_reconciled_seq"],
        }


def _active_mixed_discovery_items(vs1b: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in vs1b["entries"]:
        if entry["superseded_by"] is not None or entry["availability"] != "known-present":
            continue
        if entry["reconciliation_status"] != "verified-by-inventory":
            raise SourceDiscoveryError("source-discovery-entry-not-inventory-verified")
        if entry["media_type"] not in SUPPORTED_SOURCE_MEDIA_TYPES:
            raise SourceDiscoveryError("source-discovery-entry-media-type-invalid")
        items.append(
            {
                "catalog_entry_ref": entry["entry_id"],
                "stored_instance_ref": entry["stored_instance_id"],
                "logical_candidate_ref": entry["logical_candidate_id"],
                "media_type": entry["media_type"],
                "byte_length": entry["byte_length"],
                "fingerprint": entry["fingerprint"],
            }
        )
    items.sort(key=lambda row: row["catalog_entry_ref"])
    return items


def build_mixed_discovery_snapshot(
    catalog_snapshot: Any,
    scope_id: str,
) -> dict[str, Any]:
    if catalog_snapshot is None:
        raise SourceDiscoveryError("source-discovery-catalog-required")
    revision = getattr(catalog_snapshot, "revision", None)
    payload = getattr(catalog_snapshot, "payload", None)
    if not isinstance(revision, int) or revision < 1:
        raise SourceDiscoveryError("source-discovery-catalog-revision-invalid")
    if not isinstance(payload, dict):
        raise SourceDiscoveryError("source-discovery-catalog-payload-invalid")
    vs1b = payload.get("vs1b")
    if not isinstance(vs1b, dict):
        raise SourceDiscoveryError("source-discovery-vs1b-state-required")
    try:
        validate_vs1b_state(vs1b, scope_id)
    except Exception as exc:
        raise SourceDiscoveryError(f"source-discovery-vs1b-state-invalid:{exc}") from exc
    if vs1b["freshness"]["status"] != "fresh":
        raise SourceDiscoveryError("source-discovery-catalog-not-fresh")
    items = _active_mixed_discovery_items(vs1b)
    snapshot = {
        "snapshot_version": DISCOVERY_SNAPSHOT_VERSION,
        "scope_ref": scope_id,
        "catalog_revision": revision,
        "vs1b_state_fingerprint": _discovery_basis_fingerprint(
            scope_id,
            vs1b,
            items,
        ),
        "freshness": "fresh",
        "items": items,
    }
    try:
        validate_discovery_snapshot(snapshot)
    except SourceContractError as exc:
        raise SourceDiscoveryError(f"source-discovery-snapshot-invalid:{exc}") from exc
    return snapshot


class MixedLocalSourceDiscoveryService:
    """Reuse the accepted LocalSourcePlugin over a mixed EPUB+PDF snapshot."""

    def __init__(
        self,
        store: Any,
        scopes: Vs1ObservationScopeRegistry,
        scope_id: str,
        *,
        manifest_path: Path | None = None,
    ) -> None:
        from prototype.p0_vs1.source_service import DEFAULT_MANIFEST_PATH

        self._store = store
        self._scopes = scopes
        self._scope_id = scope_id
        self._manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
        self._scopes.require_capability(scope_id, "observe")

    def discover(self, *, rights_evidence_state: str) -> dict[str, Any]:
        catalog_snapshot = self._store.load()
        snapshot = build_mixed_discovery_snapshot(catalog_snapshot, self._scope_id)
        manifest = _load_manifest(self._manifest_path)
        try:
            rights_decision = decide_local_reference_discovery(
                self._scopes,
                self._scope_id,
                plugin_id=manifest["plugin"]["plugin_id"],
                rights_evidence_state=rights_evidence_state,
            )
        except RightsDecisionError as exc:
            raise SourceDiscoveryError(str(exc)) from exc

        snapshot_bytes = canonical_json_bytes(snapshot)
        with Vs1PluginIO() as plugin_io:
            input_handle = plugin_io.add_input(
                snapshot_bytes,
                media_type=SNAPSHOT_MEDIA_TYPE,
                ttl_seconds=120,
            )
            output_target = plugin_io.issue_output(
                media_type=BUNDLE_MEDIA_TYPE,
                max_byte_length=MAX_BUNDLE_BYTES,
                ttl_seconds=120,
            )
            environment = plugin_io.freeze()
            command = manifest["entrypoint"]["command"]
            try:
                with LocalPluginProcessClient(
                    command,
                    manifest,
                    extra_env=environment,
                ) as client:
                    handshake = client.handshake()
                    request = _invocation_request(
                        handshake["identity"]["runtime_instance_id"],
                        self._scope_id,
                        rights_decision["decision_id"],
                        input_handle,
                        output_target,
                        discovery_snapshot_fingerprint(snapshot),
                    )
                    result = client.invoke(request)
                plugin_io.verify_broker_unchanged()
            except (LocalPluginProcessError, PluginIOError) as exc:
                raise SourceDiscoveryError(
                    f"source-plugin-execution-failed:{exc}"
                ) from exc

            if result.get("status") != "completed":
                raise SourceDiscoveryError("source-plugin-result-not-completed")
            completed = _find_completed_asset(result, output_target["handle_id"])
            try:
                bundle_bytes = plugin_io.read_completed_output(
                    output_target,
                    completed,
                )
            except PluginIOError as exc:
                raise SourceDiscoveryError(
                    f"source-plugin-output-invalid:{exc}"
                ) from exc

        import json

        try:
            bundle = json.loads(bundle_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceDiscoveryError("source-plugin-bundle-json-invalid") from exc
        if canonical_json_bytes(bundle) != bundle_bytes:
            raise SourceDiscoveryError("source-plugin-bundle-not-canonical")
        records = _validate_plugin_result_against_snapshot(
            snapshot,
            bundle,
            result,
            rights_decision["decision_id"],
        )

        payload = deepcopy(catalog_snapshot.payload)
        payload["vs1c"] = _vs1c_state(
            scope_id=self._scope_id,
            catalog_basis_revision=catalog_snapshot.revision,
            snapshot=snapshot,
            rights_decision=rights_decision,
            manifest=manifest,
            result=result,
            records=records,
        )
        try:
            saved = self._store.save(
                payload,
                expected_revision=catalog_snapshot.revision,
            )
        except CatalogStoreError as exc:
            raise SourceDiscoveryError(
                "source-discovery-catalog-changed-during-plugin-run"
            ) from exc
        return {
            "status": "completed",
            "catalog_revision": saved.revision,
            "catalog_basis_revision": catalog_snapshot.revision,
            "snapshot_fingerprint": discovery_snapshot_fingerprint(snapshot),
            "rights_decision_ref": rights_decision["decision_id"],
            "source_reference_count": len(records),
            "source_refs": [record["source_ref_id"] for record in records],
        }
