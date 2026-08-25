#!/usr/bin/env python3
"""VS1b adapter from Alfred Event Model v0 JSONL into Raiatea observations.

The adapter is intentionally bound to the accepted Alfred evidence snapshot and
consumes the actual JSONL v0 shape emitted by that snapshot. It does not parse
text logs and it does not make normalized-raw records a second catalog truth
path.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from prototype.p0_vs1.core_access import ScopeRegistry


ALFRED_EVIDENCE_REVISION = "9e0e59e4232b8b173f1ae44a409c7d06f72f6c02"
ALFRED_SCHEMA_VERSION = 0


class AlfredObservationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AlfredObservationError(message)


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AlfredObservationError("alfred-record-not-json-safe") from exc


def _require_exact_keys(value: Any, allowed: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    extra = sorted(set(value) - allowed)
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _optional_positive_int(value: Any, label: str) -> int | None:
    if value is None:
        return None
    _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{label}-invalid")
    return value


def _optional_int(value: Any, label: str) -> int | None:
    if value is None:
        return None
    _require(isinstance(value, int) and not isinstance(value, bool), f"{label}-invalid")
    return value


def _optional_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    _require(isinstance(value, str) and value != "", f"{label}-invalid")
    return value


_TOP_LEVEL_FIELDS = {
    "schema_version",
    "seq",
    "ts_ns",
    "layer",
    "category",
    "type",
    "source",
    "raw_mask",
    "cookie",
    "pid",
    "backend",
    "path",
    "old_path",
    "new_path",
    "identity",
    "os_error",
    "watch",
    "recovery",
    "workspace",
    "ledger",
}
_IDENTITY_FIELDS = {"device_id", "inode_id"}
_OS_ERROR_FIELDS = {"code", "name", "message"}
_WATCH_FIELDS = {
    "watch_id",
    "state",
    "reason",
    "error",
    "event_mask",
    "event_name",
    "retry_after_ns",
    "retry_count",
}
_RECOVERY_FIELDS = {
    "directories_seen",
    "directories_watched",
    "directories_missing",
    "detail_path",
    "related_watch_id",
    "result_code",
    "pending_count",
    "children_count",
    "watches_count",
    "delay_ms",
}
_WORKSPACE_FIELDS = {"root", "id"}
_LEDGER_FIELDS = {"session_id"}

_SINGLE_PATH_SEMANTIC = {
    "FILE_CREATED": "location-appeared",
    "DIR_CREATED": "location-appeared",
    "FILE_READY": "content-ready",
    "FILE_MODIFIED": "location-content-changed",
    "FILE_DELETED": "location-disappeared-observed",
    "DIR_DELETED": "location-disappeared-observed",
}
_TRANSITION_SEMANTIC = {
    "FILE_RENAMED",
    "DIR_RENAMED",
    "FILE_MOVED",
    "DIR_MOVED",
    "FILE_RELOCATED",
    "DIR_RELOCATED",
}
_RAW_TYPES = {
    "RAW_CREATE",
    "RAW_DELETE",
    "RAW_MODIFY",
    "RAW_ATTRIB",
    "RAW_CLOSE_WRITE",
    "RAW_MOVED_FROM",
    "RAW_MOVED_TO",
    "RAW_OVERFLOW",
}
_WATCH_TYPES = {
    "WATCH_ADDED",
    "WATCH_REMOVED",
    "WATCH_STALE",
    "WATCH_STALE_EVENT_DROPPED",
}
_RECOVERY_TYPES = {
    "WATCH_RESYNC_BEGIN",
    "WATCH_RESYNC_SCAN_FAILED",
    "WATCH_RESYNC_SCAN_DONE",
    "WATCH_RESYNC_SCAN_CLASS",
    "WATCH_RESYNC_SCAN_MISSING",
    "WATCH_RESYNC_REINSTALLED",
    "WATCH_RESYNC_REINSTALL_FAILED",
    "WATCH_RESYNC_ROLLBACK",
    "WATCH_RESYNC_FAILED",
    "WATCH_RESYNC_END",
    "WATCH_LOST_QUEUED",
    "WATCH_LOST_QUEUE_SKIPPED",
    "WATCH_LOST_QUEUE_FAILED",
    "WATCH_LOST_SCAN_BEGIN",
    "WATCH_LOST_FOUND",
    "WATCH_LOST_PREFIX_UPDATED",
    "WATCH_LOST_COVERAGE_DONE",
    "WATCH_LOST_COVERAGE_MISSING",
    "WATCH_LOST_COVERAGE_CLASS",
    "WATCH_LOST_REINSTALLED",
    "WATCH_LOST_REINSTALL_FAILED",
    "WATCH_LOST_ROLLBACK",
    "WATCH_LOST_NOT_FOUND",
    "WATCH_LOST_RECOVERY_FAILED",
    "WATCH_LOST_RECOVERY_END",
    "WATCH_LOST_RETRY_SCHEDULED",
    "WATCH_LOST_RECOVERY_GAVE_UP",
}
_RECOVERY_END_TYPES = {"WATCH_RESYNC_END", "WATCH_LOST_RECOVERY_END"}
_NO_GAP_DIAGNOSTICS = {
    "WATCH_ADDED",
    "WATCH_RESYNC_SCAN_DONE",
    "WATCH_RESYNC_SCAN_CLASS",
    "WATCH_RESYNC_REINSTALLED",
    "WATCH_LOST_SCAN_BEGIN",
    "WATCH_LOST_COVERAGE_DONE",
    "WATCH_LOST_COVERAGE_CLASS",
    "WATCH_LOST_REINSTALLED",
}


def _validate_identity(value: Any) -> dict[str, int] | None:
    if value is None:
        return None
    record = _require_exact_keys(value, _IDENTITY_FIELDS, "alfred-identity")
    _require(set(record) == _IDENTITY_FIELDS, "alfred-identity-must-be-complete")
    device = _optional_positive_int(record.get("device_id"), "alfred-identity-device-id")
    inode = _optional_positive_int(record.get("inode_id"), "alfred-identity-inode-id")
    assert device is not None and inode is not None
    return {"device_id": device, "inode_id": inode}


def _validate_os_error(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    record = _require_exact_keys(value, _OS_ERROR_FIELDS, "alfred-os-error")
    result: dict[str, Any] = {}
    if "code" in record:
        result["code"] = _optional_int(record["code"], "alfred-os-error-code")
    for key in ("name", "message"):
        if key in record:
            result[key] = _optional_text(record[key], f"alfred-os-error-{key}")
    return result


def _validate_watch(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    record = _require_exact_keys(value, _WATCH_FIELDS, "alfred-watch")
    result: dict[str, Any] = {}
    for key in ("watch_id", "retry_count", "retry_after_ns"):
        if key in record:
            result[key] = _optional_positive_int(record[key], f"alfred-watch-{key}")
    for key in ("state", "reason", "error", "event_mask", "event_name"):
        if key in record:
            result[key] = _optional_text(record[key], f"alfred-watch-{key}")
    return result


def _validate_recovery(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    record = _require_exact_keys(value, _RECOVERY_FIELDS, "alfred-recovery")
    result: dict[str, Any] = {}
    positive = {
        "directories_seen",
        "directories_watched",
        "directories_missing",
        "pending_count",
        "children_count",
        "watches_count",
        "delay_ms",
    }
    for key in positive:
        if key in record:
            result[key] = _optional_positive_int(record[key], f"alfred-recovery-{key}")
    for key in ("related_watch_id", "result_code"):
        if key in record:
            result[key] = _optional_int(record[key], f"alfred-recovery-{key}")
    if "detail_path" in record:
        result["detail_path"] = _optional_text(record["detail_path"], "alfred-recovery-detail-path")
    return result


def _validate_session_payload(record: dict[str, Any]) -> None:
    if "workspace" in record:
        workspace = _require_exact_keys(record["workspace"], _WORKSPACE_FIELDS, "alfred-workspace")
        for key, value in workspace.items():
            _optional_text(value, f"alfred-workspace-{key}")
    if "ledger" in record:
        ledger = _require_exact_keys(record["ledger"], _LEDGER_FIELDS, "alfred-ledger")
        for key, value in ledger.items():
            _optional_text(value, f"alfred-ledger-{key.replace('_', '-')}")


def validate_alfred_record(value: Any) -> dict[str, Any]:
    record = _require_exact_keys(value, _TOP_LEVEL_FIELDS, "alfred-record")
    _require(record.get("schema_version") == ALFRED_SCHEMA_VERSION, "alfred-schema-version-unsupported")
    layer = record.get("layer")
    category = record.get("category")
    event_type = record.get("type")
    _require(isinstance(layer, str) and layer, "alfred-layer-required")
    _require(isinstance(category, str) and category, "alfred-category-required")
    _require(isinstance(event_type, str) and event_type, "alfred-type-required")

    if "seq" in record:
        _optional_positive_int(record["seq"], "alfred-seq")
    if "ts_ns" in record:
        _optional_positive_int(record["ts_ns"], "alfred-ts-ns")
    for key in ("source", "raw_mask", "cookie"):
        if key in record:
            _optional_positive_int(record[key], f"alfred-{key.replace('_', '-')}")
    if "pid" in record:
        _optional_int(record["pid"], "alfred-pid")
    if "backend" in record:
        _optional_text(record["backend"], "alfred-backend")

    _validate_identity(record.get("identity"))
    _validate_os_error(record.get("os_error"))
    _validate_watch(record.get("watch"))
    _validate_recovery(record.get("recovery"))

    if layer == "semantic" and category == "filesystem":
        if event_type in _SINGLE_PATH_SEMANTIC:
            _require(isinstance(record.get("path"), str) and record["path"], "alfred-semantic-path-required")
            _require("old_path" not in record and "new_path" not in record, "alfred-semantic-path-alias-forbidden")
        elif event_type in _TRANSITION_SEMANTIC:
            _require(isinstance(record.get("old_path"), str) and record["old_path"], "alfred-semantic-old-path-required")
            _require(isinstance(record.get("new_path"), str) and record["new_path"], "alfred-semantic-new-path-required")
            _require("path" not in record, "alfred-semantic-transition-path-forbidden")
        elif event_type == "OVERFLOW":
            _require(
                "path" not in record and "old_path" not in record and "new_path" not in record,
                "alfred-overflow-path-forbidden",
            )
        else:
            raise AlfredObservationError("alfred-semantic-type-unsupported")
        _require("workspace" not in record and "ledger" not in record, "alfred-session-payload-forbidden")
    elif layer == "normalized_raw" and category == "filesystem":
        _require(event_type in _RAW_TYPES, "alfred-raw-type-unsupported")
        _require("workspace" not in record and "ledger" not in record, "alfred-session-payload-forbidden")
    elif layer == "diagnostic" and category == "watch":
        _require(event_type in _WATCH_TYPES, "alfred-watch-type-unsupported")
        _require("workspace" not in record and "ledger" not in record, "alfred-session-payload-forbidden")
    elif layer == "diagnostic" and category == "recovery":
        _require(event_type in _RECOVERY_TYPES, "alfred-recovery-type-unsupported")
        _require("workspace" not in record and "ledger" not in record, "alfred-session-payload-forbidden")
    elif layer == "diagnostic" and category == "lifecycle" and event_type == "SESSION_CONTEXT":
        _validate_session_payload(record)
        _require(
            "path" not in record and "old_path" not in record and "new_path" not in record,
            "alfred-session-path-forbidden",
        )
    else:
        raise AlfredObservationError("alfred-record-tuple-unsupported")

    return record


class AlfredObservationAdapter:
    def __init__(
        self,
        scopes: ScopeRegistry,
        *,
        alfred_revision: str = ALFRED_EVIDENCE_REVISION,
    ) -> None:
        _require(isinstance(alfred_revision, str) and len(alfred_revision) == 40, "alfred-revision-invalid")
        _require(all(char in "0123456789abcdef" for char in alfred_revision), "alfred-revision-invalid")
        self._scopes = scopes
        self._alfred_revision = alfred_revision

    def parse_jsonl(self, line: str) -> dict[str, Any]:
        _require(isinstance(line, str) and line != "", "alfred-jsonl-line-required")
        _require("\n" not in line and "\r" not in line, "alfred-jsonl-must-be-one-frame")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AlfredObservationError("alfred-jsonl-invalid") from exc
        return validate_alfred_record(value)

    def _record_id(self, scope_id: str, record: dict[str, Any]) -> str:
        digest = hashlib.sha256()
        digest.update(b"raiatea-alfred-observation-v0\0")
        digest.update(scope_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(self._alfred_revision.encode("ascii"))
        digest.update(b"\0")
        digest.update(_canonical_bytes(record))
        return "alfred-record:" + digest.hexdigest()

    def _relative_location(self, scope_id: str, value: str) -> str:
        try:
            return self._scopes.observation_relative_path(scope_id, value)
        except Exception as exc:
            if isinstance(exc, AlfredObservationError):
                raise
            raise AlfredObservationError("alfred-path-outside-bound-scope") from exc

    def adapt(self, scope_id: str, record: dict[str, Any]) -> dict[str, Any]:
        record = validate_alfred_record(record)
        source_record_id = self._record_id(scope_id, record)
        layer = record["layer"]
        category = record["category"]
        event_type = record["type"]
        base: dict[str, Any] = {
            "source_record_id": source_record_id,
            "source_seq": record.get("seq"),
            "source_ts_ns": record.get("ts_ns"),
            "source_layer": layer,
            "source_category": category,
            "source_type": event_type,
            "observer": {
                "system": "alfred",
                "alfred_revision": self._alfred_revision,
                "record_schema_version": ALFRED_SCHEMA_VERSION,
                "backend": record.get("backend"),
            },
            "authoritative_catalog_evidence": False,
            "observation": None,
        }

        if layer == "normalized_raw":
            return base
        if layer == "diagnostic" and category == "lifecycle":
            return base

        observation: dict[str, Any] = {
            "observation_id": "observation:" + source_record_id.split(":", 1)[1],
            "scope_ref": scope_id,
            "source_record_id": source_record_id,
            "kind": None,
            "confidence": "observed" if layer == "semantic" else "uncertain",
            "freshness_effect": "reconcile-required",
            "filesystem_identity": _validate_identity(record.get("identity")),
        }

        if layer == "semantic":
            base["authoritative_catalog_evidence"] = True
            if event_type in _SINGLE_PATH_SEMANTIC:
                observation["kind"] = _SINGLE_PATH_SEMANTIC[event_type]
                observation["location"] = self._relative_location(scope_id, record["path"])
            elif event_type in _TRANSITION_SEMANTIC:
                observation["kind"] = "location-transition"
                observation["old_location"] = self._relative_location(scope_id, record["old_path"])
                observation["new_location"] = self._relative_location(scope_id, record["new_path"])
            else:
                observation["kind"] = "observation-incomplete"
                observation["confidence"] = "uncertain"
        else:
            observation["kind"] = "observer-health"
            observation["diagnostic_type"] = event_type
            if "path" in record:
                observation["location"] = self._relative_location(scope_id, record["path"])
            if record.get("watch") is not None:
                observation["watch"] = _validate_watch(record.get("watch"))
            if record.get("recovery") is not None:
                observation["recovery"] = _validate_recovery(record.get("recovery"))
            if record.get("os_error") is not None:
                observation["os_error"] = _validate_os_error(record.get("os_error"))
            if event_type in _RECOVERY_END_TYPES:
                observation["freshness_effect"] = "observer-recovered-reconcile-still-required"
            elif event_type in _NO_GAP_DIAGNOSTICS:
                observation["freshness_effect"] = "observer-health-only"

        base["observation"] = observation
        return base

    def adapt_jsonl(self, scope_id: str, line: str) -> dict[str, Any]:
        return self.adapt(scope_id, self.parse_jsonl(line))
