#!/usr/bin/env python3
"""VS1c internal DiscoverySnapshot and SourceReference contracts.

These records are intentionally private to the first vertical slice. They make
Core/plugin behavior executable without freezing a public Catalog or Source API.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


DISCOVERY_SNAPSHOT_VERSION = "raiatea.vs1c.discovery-snapshot.0.1.0"
SOURCE_REFERENCE_VERSION = "raiatea.vs1c.source-reference.0.1.0"
SOURCE_BUNDLE_VERSION = "raiatea.vs1c.source-reference-bundle.0.1.0"
SOURCE_REFERENCE_CONTRACT_ID = "raiatea.vs1.source-reference"
SOURCE_REFERENCE_CONTRACT_VERSION = "0.1.0"
EPUB_MEDIA_TYPE = "application/epub+zip"


class SourceContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceContractError(message)


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
        raise SourceContractError("source-record-not-json-safe") from exc


def sha256_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _require_ref(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label}-required")
    _require("/" not in value and "\\" not in value, f"{label}-must-be-opaque")
    return value


def validate_discovery_item(value: Any) -> dict[str, Any]:
    item = _require_exact_keys(
        value,
        {
            "catalog_entry_ref",
            "stored_instance_ref",
            "logical_candidate_ref",
            "media_type",
            "byte_length",
            "fingerprint",
        },
        "discovery-item",
    )
    _require_ref(item["catalog_entry_ref"], "catalog-entry-ref")
    _require_ref(item["stored_instance_ref"], "stored-instance-ref")
    _require_ref(item["logical_candidate_ref"], "logical-candidate-ref")
    _require(item["media_type"] == EPUB_MEDIA_TYPE, "discovery-item-media-type-unsupported")
    _require(
        isinstance(item["byte_length"], int)
        and not isinstance(item["byte_length"], bool)
        and item["byte_length"] >= 0,
        "discovery-item-byte-length-invalid",
    )
    _require(_valid_sha256(item["fingerprint"]), "discovery-item-fingerprint-invalid")
    return item


def validate_discovery_snapshot(value: Any) -> dict[str, Any]:
    snapshot = _require_exact_keys(
        value,
        {
            "snapshot_version",
            "scope_ref",
            "catalog_revision",
            "vs1b_state_fingerprint",
            "freshness",
            "items",
        },
        "discovery-snapshot",
    )
    _require(snapshot["snapshot_version"] == DISCOVERY_SNAPSHOT_VERSION, "discovery-snapshot-version-unsupported")
    _require_ref(snapshot["scope_ref"], "discovery-scope-ref")
    _require(
        isinstance(snapshot["catalog_revision"], int)
        and not isinstance(snapshot["catalog_revision"], bool)
        and snapshot["catalog_revision"] >= 1,
        "discovery-catalog-revision-invalid",
    )
    _require(_valid_sha256(snapshot["vs1b_state_fingerprint"]), "discovery-state-fingerprint-invalid")
    _require(snapshot["freshness"] == "fresh", "discovery-snapshot-must-be-fresh")
    items = snapshot["items"]
    _require(isinstance(items, list), "discovery-items-must-be-array")
    seen_entries: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in items:
        item = validate_discovery_item(row)
        entry_ref = item["catalog_entry_ref"]
        _require(entry_ref not in seen_entries, "discovery-catalog-entry-duplicate")
        seen_entries.add(entry_ref)
        normalized.append(item)
    expected_order = sorted(normalized, key=lambda row: row["catalog_entry_ref"])
    _require(normalized == expected_order, "discovery-items-not-canonical-order")
    return snapshot


def discovery_snapshot_fingerprint(snapshot: dict[str, Any]) -> str:
    validate_discovery_snapshot(snapshot)
    return sha256_ref(snapshot)


def deterministic_source_ref_id(scope_ref: str, item: dict[str, Any]) -> str:
    _require_ref(scope_ref, "source-ref-scope")
    validate_discovery_item(item)
    basis = {
        "version": SOURCE_REFERENCE_VERSION,
        "scope_ref": scope_ref,
        "catalog_entry_ref": item["catalog_entry_ref"],
        "stored_instance_ref": item["stored_instance_ref"],
        "fingerprint": item["fingerprint"],
    }
    return "source-ref:" + hashlib.sha256(canonical_json_bytes(basis)).hexdigest()


def build_source_reference(scope_ref: str, item: dict[str, Any]) -> dict[str, Any]:
    validate_discovery_item(item)
    record = {
        "record_version": SOURCE_REFERENCE_VERSION,
        "record_kind": "SourceReferenceRecord",
        "source_ref_id": deterministic_source_ref_id(scope_ref, item),
        "source_class": "local-user-authorized-catalog-reference",
        "catalog_entry_ref": item["catalog_entry_ref"],
        "stored_instance_ref": item["stored_instance_ref"],
        "logical_candidate_ref": item["logical_candidate_ref"],
        "media_type": item["media_type"],
        "byte_length": item["byte_length"],
        "fingerprint": item["fingerprint"],
        "location_exposed": False,
    }
    validate_source_reference(record)
    return record


def validate_source_reference(value: Any) -> dict[str, Any]:
    record = _require_exact_keys(
        value,
        {
            "record_version",
            "record_kind",
            "source_ref_id",
            "source_class",
            "catalog_entry_ref",
            "stored_instance_ref",
            "logical_candidate_ref",
            "media_type",
            "byte_length",
            "fingerprint",
            "location_exposed",
        },
        "source-reference",
    )
    _require(record["record_version"] == SOURCE_REFERENCE_VERSION, "source-reference-version-unsupported")
    _require(record["record_kind"] == "SourceReferenceRecord", "source-reference-kind-invalid")
    source_ref_id = _require_ref(record["source_ref_id"], "source-ref-id")
    _require(source_ref_id.startswith("source-ref:"), "source-ref-id-prefix-invalid")
    _require(record["source_class"] == "local-user-authorized-catalog-reference", "source-reference-class-invalid")
    for key in ("catalog_entry_ref", "stored_instance_ref", "logical_candidate_ref"):
        _require_ref(record[key], f"source-reference-{key}")
    _require(record["media_type"] == EPUB_MEDIA_TYPE, "source-reference-media-type-unsupported")
    _require(
        isinstance(record["byte_length"], int)
        and not isinstance(record["byte_length"], bool)
        and record["byte_length"] >= 0,
        "source-reference-byte-length-invalid",
    )
    _require(_valid_sha256(record["fingerprint"]), "source-reference-fingerprint-invalid")
    _require(record["location_exposed"] is False, "source-reference-location-must-not-be-exposed")
    return record


def build_source_reference_bundle(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_discovery_snapshot(snapshot)
    records = [build_source_reference(snapshot["scope_ref"], item) for item in snapshot["items"]]
    records.sort(key=lambda row: row["source_ref_id"])
    record_map = {row["source_ref_id"]: row for row in records}
    refs = [
        {
            "ref_id": row["source_ref_id"],
            "contract_id": SOURCE_REFERENCE_CONTRACT_ID,
            "contract_version": SOURCE_REFERENCE_CONTRACT_VERSION,
            "record_kind": "SourceReferenceRecord",
        }
        for row in records
    ]
    bundle = {
        "bundle_version": SOURCE_BUNDLE_VERSION,
        "record_kind": "SourceReferenceBundle",
        "scope_ref": snapshot["scope_ref"],
        "snapshot_fingerprint": discovery_snapshot_fingerprint(snapshot),
        "location_exposed": False,
        "record_refs": refs,
        "records": record_map,
    }
    validate_source_reference_bundle(bundle)
    return bundle


def validate_source_reference_bundle(value: Any) -> dict[str, Any]:
    bundle = _require_exact_keys(
        value,
        {
            "bundle_version",
            "record_kind",
            "scope_ref",
            "snapshot_fingerprint",
            "location_exposed",
            "record_refs",
            "records",
        },
        "source-reference-bundle",
    )
    _require(bundle["bundle_version"] == SOURCE_BUNDLE_VERSION, "source-bundle-version-unsupported")
    _require(bundle["record_kind"] == "SourceReferenceBundle", "source-bundle-kind-invalid")
    _require_ref(bundle["scope_ref"], "source-bundle-scope-ref")
    _require(_valid_sha256(bundle["snapshot_fingerprint"]), "source-bundle-snapshot-fingerprint-invalid")
    _require(bundle["location_exposed"] is False, "source-bundle-location-must-not-be-exposed")
    refs = bundle["record_refs"]
    records = bundle["records"]
    _require(isinstance(refs, list), "source-bundle-record-refs-must-be-array")
    _require(isinstance(records, dict), "source-bundle-records-must-be-object")
    seen: set[str] = set()
    ref_ids: list[str] = []
    for ref in refs:
        row = _require_exact_keys(
            ref,
            {"ref_id", "contract_id", "contract_version", "record_kind"},
            "source-record-ref",
        )
        ref_id = _require_ref(row["ref_id"], "source-record-ref-id")
        _require(ref_id not in seen, "source-record-ref-duplicate")
        seen.add(ref_id)
        ref_ids.append(ref_id)
        _require(row["contract_id"] == SOURCE_REFERENCE_CONTRACT_ID, "source-record-ref-contract-invalid")
        _require(row["contract_version"] == SOURCE_REFERENCE_CONTRACT_VERSION, "source-record-ref-version-invalid")
        _require(row["record_kind"] == "SourceReferenceRecord", "source-record-ref-kind-invalid")
    _require(ref_ids == sorted(ref_ids), "source-record-refs-not-canonical-order")
    _require(set(records) == set(ref_ids), "source-bundle-record-map-mismatch")
    for ref_id in ref_ids:
        record = validate_source_reference(records[ref_id])
        _require(record["source_ref_id"] == ref_id, "source-bundle-record-id-mismatch")
    return bundle
