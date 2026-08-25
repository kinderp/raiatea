#!/usr/bin/env python3
"""VS1b bounded EPUB inventory and conservative reconciliation state.

This is an internal vertical-slice state model. It is intentionally not a public
Catalog schema and it does not perform filesystem mutation.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import secrets
import stat
from typing import Any

from prototype.p0_vs1.alfred_observation import AlfredObservationAdapter
from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker, CoreAccessError, ScopeRegistry


VS1B_STATE_VERSION = "raiatea.vs1b.reconciliation.0.1.0"
EPUB_MEDIA_TYPE = "application/epub+zip"
MAX_RECENT_RECORD_IDS = 512
MAX_OBSERVATION_LOG = 256


class ReconciliationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReconciliationError(message)


def _is_symlink_or_reparse_stat(info: os.stat_result) -> bool:
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = int(getattr(info, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return bool(attributes & reparse_flag)


def _path_inside(root: str, candidate: str) -> bool:
    root_norm = os.path.normcase(os.path.normpath(root))
    candidate_norm = os.path.normcase(os.path.normpath(candidate))
    try:
        return os.path.commonpath([root_norm, candidate_norm]) == root_norm
    except ValueError:
        return False


class Vs1ObservationScopeRegistry(ScopeRegistry):
    """VS1b internal extension of the accepted Core-owned scope registry.

    It adds observation-path translation and internal inventory root access only;
    registration/authority semantics remain inherited unchanged from VS1a.
    """

    def observation_relative_path(self, scope_id: str, observed_path: str) -> str:
        scope = self.require_capability(scope_id, "observe")
        _require(isinstance(observed_path, str) and observed_path, "observation-path-required")
        _require("\x00" not in observed_path, "observation-path-nul-forbidden")
        candidate = Path(observed_path)
        _require(candidate.is_absolute(), "observation-path-must-be-absolute")
        _require(".." not in candidate.parts, "observation-path-traversal-forbidden")
        normalized = os.path.normpath(os.fspath(candidate))
        _require(_path_inside(scope.canonical_root, normalized), "observation-path-outside-scope")
        relative = os.path.relpath(normalized, scope.canonical_root)
        if relative == ".":
            return "."
        result = Path(relative).as_posix()
        _require(result not in {"", ".", ".."} and not result.startswith("../"), "observation-relative-path-invalid")
        return result

    def _inventory_root(self, scope_id: str) -> tuple[Path, int | None]:
        scope = self.require_capability(scope_id, "read-for-processing")
        return scope.root, scope.posix_root_fd


def _scan_posix_epubs(
    scopes: Vs1ObservationScopeRegistry,
    broker: AssetBroker,
    scope_id: str,
) -> list[dict[str, Any]]:
    root, root_fd = scopes._inventory_root(scope_id)
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
                    if not stat.S_ISREG(info.st_mode) or not entry.name.lower().endswith(".epub"):
                        continue
                    relative = "/".join(relative_parts + (entry.name,))
                    try:
                        handle = broker.issue_read_handle(
                            scope_id,
                            relative,
                            media_type=EPUB_MEDIA_TYPE,
                        )
                    except CoreAccessError as exc:
                        raise ReconciliationError("inventory-safe-read-failed") from exc
                    discovered.append(
                        {
                            "location": relative,
                            "fingerprint": handle["fingerprint"],
                            "byte_length": handle["byte_length"],
                            "media_type": handle["media_type"],
                        }
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


def _scan_path_epubs(
    scopes: Vs1ObservationScopeRegistry,
    broker: AssetBroker,
    scope_id: str,
) -> list[dict[str, Any]]:
    """Path-based contract scan used on non-POSIX CI.

    Live Alfred observation remains Linux/inotify only. The final content read is
    still authorized through the VS1a Windows opened-handle broker, while this
    traversal rejects reparse entries and fails if a scanned directory changes
    into a reparse point during the scan.
    """

    root, _ = scopes._inventory_root(scope_id)
    stack = [root]
    discovered: list[dict[str, Any]] = []
    while stack:
        directory = stack.pop()
        try:
            directory_info = os.lstat(directory)
        except OSError as exc:
            raise ReconciliationError("inventory-directory-stat-failed") from exc
        _require(not _is_symlink_or_reparse_stat(directory_info), "inventory-directory-reparse-forbidden")
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
            if not stat.S_ISREG(info.st_mode) or not entry.name.lower().endswith(".epub"):
                continue
            try:
                relative = entry_path.relative_to(root).as_posix()
            except ValueError as exc:
                raise ReconciliationError("inventory-location-outside-scope") from exc
            try:
                handle = broker.issue_read_handle(
                    scope_id,
                    relative,
                    media_type=EPUB_MEDIA_TYPE,
                )
            except CoreAccessError as exc:
                raise ReconciliationError("inventory-safe-read-failed") from exc
            discovered.append(
                {
                    "location": relative,
                    "fingerprint": handle["fingerprint"],
                    "byte_length": handle["byte_length"],
                    "media_type": handle["media_type"],
                }
            )
    discovered.sort(key=lambda item: item["location"])
    return discovered


def scan_epub_inventory(
    scopes: Vs1ObservationScopeRegistry,
    broker: AssetBroker,
    scope_id: str,
) -> list[dict[str, Any]]:
    return (
        _scan_path_epubs(scopes, broker, scope_id)
        if os.name == "nt"
        else _scan_posix_epubs(scopes, broker, scope_id)
    )


def _new_id(prefix: str) -> str:
    return f"{prefix}:{secrets.token_urlsafe(18)}"


def _initial_state(scope_id: str) -> dict[str, Any]:
    return {
        "state_version": VS1B_STATE_VERSION,
        "scope_id": scope_id,
        "freshness": {"status": "unknown", "reason": "not-reconciled"},
        "stream": {
            "last_seq": None,
            "last_reconciled_seq": None,
            "recent_record_ids": [],
            "history_compacted": False,
        },
        "observation_log": [],
        "observation_log_compacted": False,
        "entries": [],
    }


def _validate_entry(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "vs1b-entry-must-be-object")
    expected = {
        "entry_id",
        "logical_candidate_id",
        "stored_instance_id",
        "current_location",
        "location_history",
        "fingerprint",
        "byte_length",
        "media_type",
        "availability",
        "filesystem_identity",
        "reconciliation_status",
        "superseded_by",
    }
    _require(set(value) == expected, "vs1b-entry-shape-invalid")
    for key in ("entry_id", "logical_candidate_id", "stored_instance_id", "current_location", "fingerprint", "media_type", "reconciliation_status"):
        _require(isinstance(value[key], str) and value[key], f"vs1b-entry-{key}-invalid")
    _require(isinstance(value["location_history"], list) and all(isinstance(item, str) for item in value["location_history"]), "vs1b-entry-history-invalid")
    _require(isinstance(value["byte_length"], int) and not isinstance(value["byte_length"], bool) and value["byte_length"] >= 0, "vs1b-entry-byte-length-invalid")
    _require(value["availability"] in {"known-present", "unavailable-or-unknown", "confirmed-missing-at-location"}, "vs1b-entry-availability-invalid")
    identity = value["filesystem_identity"]
    if identity is not None:
        _require(isinstance(identity, dict) and set(identity) == {"device_id", "inode_id"}, "vs1b-entry-identity-invalid")
    superseded = value["superseded_by"]
    _require(superseded is None or (isinstance(superseded, str) and superseded), "vs1b-entry-superseded-invalid")
    return value


def validate_state(value: Any, scope_id: str) -> dict[str, Any]:
    _require(isinstance(value, dict), "vs1b-state-must-be-object")
    expected = {
        "state_version",
        "scope_id",
        "freshness",
        "stream",
        "observation_log",
        "observation_log_compacted",
        "entries",
    }
    _require(set(value) == expected, "vs1b-state-shape-invalid")
    _require(value["state_version"] == VS1B_STATE_VERSION, "vs1b-state-version-unsupported")
    _require(value["scope_id"] == scope_id, "vs1b-state-scope-mismatch")
    freshness = value["freshness"]
    _require(isinstance(freshness, dict) and set(freshness) == {"status", "reason"}, "vs1b-freshness-shape-invalid")
    _require(freshness["status"] in {"unknown", "reconcile-required", "fresh"}, "vs1b-freshness-status-invalid")
    _require(isinstance(freshness["reason"], str) and freshness["reason"], "vs1b-freshness-reason-invalid")
    stream = value["stream"]
    _require(
        isinstance(stream, dict)
        and set(stream) == {"last_seq", "last_reconciled_seq", "recent_record_ids", "history_compacted"},
        "vs1b-stream-shape-invalid",
    )
    for key in ("last_seq", "last_reconciled_seq"):
        seq = stream[key]
        _require(seq is None or (isinstance(seq, int) and not isinstance(seq, bool) and seq > 0), f"vs1b-stream-{key}-invalid")
    recent = stream["recent_record_ids"]
    _require(isinstance(recent, list) and len(recent) <= MAX_RECENT_RECORD_IDS, "vs1b-stream-recent-invalid")
    _require(len(recent) == len(set(recent)) and all(isinstance(item, str) and item for item in recent), "vs1b-stream-recent-invalid")
    _require(isinstance(stream["history_compacted"], bool), "vs1b-stream-compacted-invalid")
    log = value["observation_log"]
    _require(isinstance(log, list) and len(log) <= MAX_OBSERVATION_LOG, "vs1b-observation-log-invalid")
    _require(isinstance(value["observation_log_compacted"], bool), "vs1b-observation-log-compacted-invalid")
    entries = value["entries"]
    _require(isinstance(entries, list), "vs1b-entries-invalid")
    seen_entry_ids: set[str] = set()
    seen_instance_ids: set[str] = set()
    for entry in entries:
        record = _validate_entry(entry)
        _require(record["entry_id"] not in seen_entry_ids, "vs1b-entry-id-duplicate")
        _require(record["stored_instance_id"] not in seen_instance_ids, "vs1b-instance-id-duplicate")
        seen_entry_ids.add(record["entry_id"])
        seen_instance_ids.add(record["stored_instance_id"])
    return value


def _freshness_required(state: dict[str, Any], reason: str) -> None:
    state["freshness"] = {"status": "reconcile-required", "reason": reason}


def _remember_source_record(state: dict[str, Any], source_record_id: str) -> None:
    recent = state["stream"]["recent_record_ids"]
    if source_record_id in recent:
        return
    recent.append(source_record_id)
    if len(recent) > MAX_RECENT_RECORD_IDS:
        del recent[0]
        state["stream"]["history_compacted"] = True


def _append_observation(
    state: dict[str, Any],
    adapted: dict[str, Any],
    disposition: str,
) -> None:
    observation = adapted.get("observation")
    if observation is None:
        return
    state["observation_log"].append(
        {
            "source_record_id": adapted["source_record_id"],
            "source_seq": adapted.get("source_seq"),
            "source_ts_ns": adapted.get("source_ts_ns"),
            "source_type": adapted["source_type"],
            "disposition": disposition,
            "observation": observation,
        }
    )
    if len(state["observation_log"]) > MAX_OBSERVATION_LOG:
        del state["observation_log"][0]
        state["observation_log_compacted"] = True


def _active_entries_at(state: dict[str, Any], location: str) -> list[dict[str, Any]]:
    return [
        entry
        for entry in state["entries"]
        if entry["current_location"] == location
        and entry["superseded_by"] is None
        and entry["availability"] != "confirmed-missing-at-location"
    ]


def _location_is_within(location: str, prefix: str) -> bool:
    if prefix == ".":
        return True
    return location == prefix or location.startswith(prefix.rstrip("/") + "/")


def _apply_observation(state: dict[str, Any], adapted: dict[str, Any]) -> None:
    observation = adapted.get("observation")
    if observation is None:
        return
    effect = observation["freshness_effect"]
    if effect in {"reconcile-required", "observer-recovered-reconcile-still-required"}:
        _freshness_required(state, f"alfred:{adapted['source_type']}")

    kind = observation["kind"]
    if kind == "location-transition":
        old_location = observation["old_location"]
        new_location = observation["new_location"]
        old_matches = _active_entries_at(state, old_location)
        new_matches = _active_entries_at(state, new_location)
        if len(old_matches) != 1 or new_matches:
            _freshness_required(state, "alfred:location-transition-ambiguous")
            return
        entry = old_matches[0]
        if old_location not in entry["location_history"]:
            entry["location_history"].append(old_location)
        entry["current_location"] = new_location
        entry["availability"] = "unavailable-or-unknown"
        entry["reconciliation_status"] = "transition-unverified"
        if observation.get("filesystem_identity") is not None:
            entry["filesystem_identity"] = deepcopy(observation["filesystem_identity"])
        return

    if kind == "location-disappeared-observed":
        location = observation["location"]
        is_directory = adapted["source_type"].startswith("DIR_")
        for entry in state["entries"]:
            if entry["superseded_by"] is not None:
                continue
            if (
                entry["current_location"] == location
                or (is_directory and _location_is_within(entry["current_location"], location))
            ):
                entry["availability"] = "confirmed-missing-at-location"
                entry["reconciliation_status"] = "delete-observed"
        return

    if kind == "location-content-changed":
        for entry in _active_entries_at(state, observation["location"]):
            entry["reconciliation_status"] = "content-change-unverified"
        return

    if kind == "observer-health":
        diagnostic_type = observation.get("diagnostic_type")
        if diagnostic_type in {
            "WATCH_STALE",
            "WATCH_STALE_EVENT_DROPPED",
            "WATCH_LOST_QUEUED",
            "WATCH_LOST_NOT_FOUND",
            "WATCH_LOST_RECOVERY_GAVE_UP",
            "WATCH_LOST_RECOVERY_FAILED",
        }:
            location = observation.get("location")
            for entry in state["entries"]:
                if entry["superseded_by"] is not None:
                    continue
                if location is None or _location_is_within(entry["current_location"], location):
                    entry["availability"] = "unavailable-or-unknown"
                    entry["reconciliation_status"] = "observer-coverage-uncertain"


def _new_entry(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "entry_id": _new_id("entry"),
        "logical_candidate_id": _new_id("logical-candidate"),
        "stored_instance_id": _new_id("stored-instance"),
        "current_location": item["location"],
        "location_history": [],
        "fingerprint": item["fingerprint"],
        "byte_length": item["byte_length"],
        "media_type": item["media_type"],
        "availability": "known-present",
        "filesystem_identity": None,
        "reconciliation_status": "verified-by-inventory",
        "superseded_by": None,
    }


def _reconcile_entries(state: dict[str, Any], inventory: list[dict[str, Any]]) -> None:
    seen_active_entry_ids: set[str] = set()
    for item in inventory:
        matches = _active_entries_at(state, item["location"])
        if len(matches) > 1:
            raise ReconciliationError("inventory-active-location-ambiguous")
        if not matches:
            entry = _new_entry(item)
            state["entries"].append(entry)
            seen_active_entry_ids.add(entry["entry_id"])
            continue

        existing = matches[0]
        if existing["fingerprint"] == item["fingerprint"]:
            existing["byte_length"] = item["byte_length"]
            existing["media_type"] = item["media_type"]
            existing["availability"] = "known-present"
            existing["reconciliation_status"] = "verified-by-inventory"
            seen_active_entry_ids.add(existing["entry_id"])
            continue

        replacement = _new_entry(item)
        existing["availability"] = "confirmed-missing-at-location"
        existing["reconciliation_status"] = "content-replaced-at-location-unresolved"
        existing["superseded_by"] = replacement["entry_id"]
        state["entries"].append(replacement)
        seen_active_entry_ids.add(replacement["entry_id"])

    for entry in state["entries"]:
        if entry["superseded_by"] is not None:
            continue
        if entry["entry_id"] not in seen_active_entry_ids and entry["availability"] != "confirmed-missing-at-location":
            entry["availability"] = "confirmed-missing-at-location"
            entry["reconciliation_status"] = "missing-after-bounded-inventory"

    state["entries"].sort(key=lambda entry: (entry["current_location"], entry["entry_id"]))


class Vs1bReconciliationEngine:
    def __init__(
        self,
        store: CatalogStateStore,
        scopes: Vs1ObservationScopeRegistry,
        broker: AssetBroker,
        scope_id: str,
        adapter: AlfredObservationAdapter | None = None,
    ) -> None:
        self._store = store
        self._scopes = scopes
        self._broker = broker
        self._scope_id = scope_id
        self._scopes.require_capability(scope_id, "observe")
        self._scopes.require_capability(scope_id, "read-for-processing")
        self._adapter = adapter or AlfredObservationAdapter(scopes)

    def _load(self) -> tuple[int, dict[str, Any], dict[str, Any]]:
        snapshot = self._store.load()
        revision = 0 if snapshot is None else snapshot.revision
        payload: dict[str, Any] = {} if snapshot is None else deepcopy(snapshot.payload)
        state = payload.get("vs1b")
        if state is None:
            state = _initial_state(self._scope_id)
        validate_state(state, self._scope_id)
        return revision, payload, state

    def current_state(self) -> dict[str, Any]:
        _, _, state = self._load()
        return deepcopy(state)

    def consume_jsonl(self, line: str) -> dict[str, Any]:
        # Parse/adapt before loading or modifying persisted state. Malformed or
        # out-of-scope input therefore cannot advance the checkpoint.
        adapted = self._adapter.adapt_jsonl(self._scope_id, line)
        revision, payload, state = self._load()
        source_record_id = adapted["source_record_id"]
        recent = state["stream"]["recent_record_ids"]
        if source_record_id in recent:
            return {"status": "duplicate", "source_record_id": source_record_id, "revision": revision}

        seq = adapted.get("source_seq")
        last_seq = state["stream"]["last_seq"]
        apply_record = True
        disposition = "applied"

        if seq is None:
            _freshness_required(state, "alfred:sequence-unavailable")
            apply_record = False
            disposition = "continuity-unproven-not-applied"
        elif last_seq is None:
            state["stream"]["last_seq"] = seq
            _freshness_required(state, "alfred:stream-baseline-unproven")
            apply_record = False
            disposition = "baseline-unproven-not-applied"
        elif seq == last_seq + 1:
            state["stream"]["last_seq"] = seq
        elif seq > last_seq + 1:
            state["stream"]["last_seq"] = seq
            _freshness_required(state, "alfred:sequence-gap")
            disposition = "applied-after-gap"
        else:
            _freshness_required(state, "alfred:old-or-out-of-order-record")
            apply_record = False
            disposition = "old-or-out-of-order-not-applied"

        _remember_source_record(state, source_record_id)
        _append_observation(state, adapted, disposition)
        if apply_record:
            _apply_observation(state, adapted)

        validate_state(state, self._scope_id)
        payload["vs1b"] = state
        saved = self._store.save(payload, expected_revision=revision)
        return {
            "status": disposition,
            "source_record_id": source_record_id,
            "revision": saved.revision,
            "freshness": deepcopy(state["freshness"]),
        }

    def reconcile_inventory(self) -> dict[str, Any]:
        # Do not mutate persisted state until the full bounded scan succeeds.
        inventory = scan_epub_inventory(self._scopes, self._broker, self._scope_id)
        revision, payload, state = self._load()
        _reconcile_entries(state, inventory)
        state["freshness"] = {"status": "fresh", "reason": "bounded-inventory-complete"}
        state["stream"]["last_reconciled_seq"] = state["stream"]["last_seq"]
        validate_state(state, self._scope_id)
        payload["vs1b"] = state
        saved = self._store.save(payload, expected_revision=revision)
        return {
            "revision": saved.revision,
            "inventory_count": len(inventory),
            "freshness": deepcopy(state["freshness"]),
            "last_reconciled_seq": state["stream"]["last_reconciled_seq"],
        }
