#!/usr/bin/env python3
"""VS1f canonical authority-backup contract.

The backup carries authoritative catalog knowledge, not document bytes or
recomputable search/member caches.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from prototype.p0_vs1.extraction_service import validate_vs1d_state
from prototype.p0_vs1.reconciliation import validate_state as validate_vs1b_state
from prototype.p0_vs1.search_contract import normalize_query_plan, validate_view
from prototype.p0_vs1.source_service import validate_vs1c_state


BACKUP_VERSION = "raiatea.vs1f.catalog-authority-backup.0.1.0"
BACKUP_RECORD_KIND = "CatalogAuthorityBackup"
_FORBIDDEN_TRANSIENT_KEYS = frozenset(
    {
        "handle_id",
        "lease_id",
        "expires_at",
        "secret_leases",
        "broker_path",
        "workspace_path",
        "source_bytes",
        "document_bytes",
    }
)
_FORBIDDEN_TRANSIENT_VALUE_PREFIXES = (
    "plugin-input:",
    "plugin-output:",
    "lease:",
)


class BackupContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BackupContractError(message)


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BackupContractError("backup-record-not-json-safe") from exc


def sha256_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _opaque(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label}-required")
    _require("/" not in value and "\\" not in value, f"{label}-must-be-opaque")
    return value


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(keys - actual)
    extra = sorted(actual - keys)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _assert_no_transient_authority(value: Any, *, trail: str = "authority") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            _require(
                normalized not in _FORBIDDEN_TRANSIENT_KEYS,
                f"backup-transient-authority-forbidden:{trail}.{key}",
            )
            _assert_no_transient_authority(child, trail=f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_transient_authority(child, trail=f"{trail}[{index}]")
    elif isinstance(value, str):
        _require(
            not value.startswith(_FORBIDDEN_TRANSIENT_VALUE_PREFIXES),
            f"backup-transient-reference-forbidden:{trail}",
        )


def _canonical_vs1b(value: dict[str, Any], scope_ref: str) -> dict[str, Any]:
    result = deepcopy(value)
    validate_vs1b_state(result, scope_ref)
    result["entries"] = sorted(result["entries"], key=lambda row: row["entry_id"])
    validate_vs1b_state(result, scope_ref)
    return result


def _canonical_vs1c(value: dict[str, Any], scope_ref: str) -> dict[str, Any]:
    result = deepcopy(value)
    validate_vs1c_state(result, scope_ref)
    result["source_references"] = sorted(
        result["source_references"], key=lambda row: row["source_ref_id"]
    )
    validate_vs1c_state(result, scope_ref)
    return result


def _canonical_vs1d(value: dict[str, Any], scope_ref: str) -> dict[str, Any]:
    result = deepcopy(value)
    validate_vs1d_state(result, scope_ref)
    result["extractions"] = sorted(
        result["extractions"], key=lambda row: row["source_ref_id"]
    )
    validate_vs1d_state(result, scope_ref)
    return result


def _canonical_views(value: Any) -> list[dict[str, Any]]:
    _require(isinstance(value, list), "backup-views-must-be-array")
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for raw in value:
        row = deepcopy(raw)
        validate_view(row)
        _require(row["view_id"] not in ids, "backup-view-id-duplicate")
        ids.add(row["view_id"])
        rows.append(row)
    rows.sort(key=lambda row: row["view_id"])
    return rows


def _canonical_smart_rules(value: Any) -> list[dict[str, Any]]:
    _require(isinstance(value, list), "backup-smart-rules-must-be-array")
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, raw in enumerate(value):
        row = _exact(raw, {"collection_id", "rule"}, f"backup-smart-rule-{index}")
        collection_id = _opaque(row["collection_id"], "backup-smart-collection-id")
        _require(collection_id not in ids, "backup-smart-collection-id-duplicate")
        ids.add(collection_id)
        rows.append(
            {
                "collection_id": collection_id,
                "rule": normalize_query_plan(row["rule"]),
            }
        )
    rows.sort(key=lambda row: row["collection_id"])
    return rows


def canonicalize_authority(value: Any, scope_ref: str) -> dict[str, Any]:
    authority = _exact(
        value,
        {"vs1b", "vs1c", "vs1d", "views", "smart_rules"},
        "backup-authority",
    )
    _opaque(scope_ref, "backup-scope-ref")
    result = {
        "vs1b": _canonical_vs1b(authority["vs1b"], scope_ref),
        "vs1c": _canonical_vs1c(authority["vs1c"], scope_ref),
        "vs1d": _canonical_vs1d(authority["vs1d"], scope_ref),
        "views": _canonical_views(authority["views"]),
        "smart_rules": _canonical_smart_rules(authority["smart_rules"]),
    }
    _require(result["vs1b"]["scope_id"] == scope_ref, "backup-vs1b-scope-mismatch")
    _require(result["vs1c"]["scope_ref"] == scope_ref, "backup-vs1c-scope-mismatch")
    _require(result["vs1d"]["scope_ref"] == scope_ref, "backup-vs1d-scope-mismatch")
    _assert_no_transient_authority(result)
    canonical_json_bytes(result)
    return result


def build_backup(
    *,
    scope_ref: str,
    source_catalog_revision: int,
    authority: dict[str, Any],
) -> dict[str, Any]:
    _opaque(scope_ref, "backup-scope-ref")
    _require(
        isinstance(source_catalog_revision, int)
        and not isinstance(source_catalog_revision, bool)
        and source_catalog_revision >= 1,
        "backup-source-catalog-revision-invalid",
    )
    canonical_authority = canonicalize_authority(authority, scope_ref)
    envelope = {
        "backup_version": BACKUP_VERSION,
        "record_kind": BACKUP_RECORD_KIND,
        "scope_ref": scope_ref,
        "source_catalog_revision": source_catalog_revision,
        "authority_sha256": sha256_ref(canonical_authority),
        "authority": canonical_authority,
    }
    validate_backup(envelope)
    return envelope


def validate_backup(value: Any) -> dict[str, Any]:
    envelope = _exact(
        value,
        {
            "backup_version",
            "record_kind",
            "scope_ref",
            "source_catalog_revision",
            "authority_sha256",
            "authority",
        },
        "catalog-backup",
    )
    _require(envelope["backup_version"] == BACKUP_VERSION, "backup-version-unsupported")
    _require(envelope["record_kind"] == BACKUP_RECORD_KIND, "backup-record-kind-invalid")
    scope_ref = _opaque(envelope["scope_ref"], "backup-scope-ref")
    _require(
        isinstance(envelope["source_catalog_revision"], int)
        and not isinstance(envelope["source_catalog_revision"], bool)
        and envelope["source_catalog_revision"] >= 1,
        "backup-source-catalog-revision-invalid",
    )
    _require(_valid_sha256(envelope["authority_sha256"]), "backup-authority-sha-invalid")
    authority = canonicalize_authority(envelope["authority"], scope_ref)
    _require(authority == envelope["authority"], "backup-authority-not-canonical")
    _require(
        envelope["authority_sha256"] == sha256_ref(authority),
        "backup-authority-integrity-mismatch",
    )
    return envelope


def encode_backup(value: dict[str, Any]) -> bytes:
    validate_backup(value)
    return canonical_json_bytes(value)


def decode_backup(raw: bytes) -> dict[str, Any]:
    _require(isinstance(raw, bytes) and raw, "backup-bytes-required")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupContractError("backup-json-invalid") from exc
    validate_backup(value)
    _require(raw == canonical_json_bytes(value), "backup-envelope-not-canonical")
    return value
