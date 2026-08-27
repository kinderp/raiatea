#!/usr/bin/env python3
"""Closed path-free Provider observation contract for PDF1c Docling extraction."""
from __future__ import annotations

import json
from typing import Any


DOCLING_OBSERVATION_VERSION = "raiatea.pdf1c.docling-observation.0.1.0"
DOCLING_OBSERVATION_MEDIA_TYPE = "application/vnd.raiatea.pdf1c-docling-observation+json"
DOCLING_PROVIDER_ID = "docling"
DOCLING_PROVIDER_VERSION = "2.118.0"
DOCLING_PROFILE = "docling-2.118.0-standard-pdf-native-no-ocr"

_FORBIDDEN_PATH_KEYS = frozenset(
    {
        "path",
        "filepath",
        "file_path",
        "filename",
        "root",
        "relative_path",
        "host_path",
        "workspace_path",
        "location",
        "current_location",
        "location_history",
        "model_root",
        "cache_root",
    }
)

_ACCEPTED_LABELS = frozenset(
    {"title", "section_header", "text", "paragraph", "list_item", "code", "caption", "picture"}
)
_ACCEPTED_SEMANTIC_TYPES = frozenset(
    {"heading", "paragraph", "list_item", "code", "caption", "picture"}
)


class DoclingObservationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingObservationError(message)


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
        raise DoclingObservationError("docling-observation-not-json-safe") from exc


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(keys - actual)
    extra = sorted(actual - keys)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _sha(value: Any, label: str) -> str:
    _require(
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:]),
        f"{label}-invalid",
    )
    return value


def _int(value: Any, label: str, *, minimum: int = 0) -> int:
    _require(
        isinstance(value, int) and not isinstance(value, bool) and value >= minimum,
        f"{label}-invalid",
    )
    return value


def _number(value: Any, label: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label}-invalid")
    return float(value)


def _bbox(value: Any, label: str) -> list[float]:
    _require(isinstance(value, list) and len(value) == 4, f"{label}-invalid")
    result = [_number(item, label) for item in value]
    _require(result[0] <= result[2] and result[1] <= result[3], f"{label}-order-invalid")
    return result


def _walk_no_host_path(value: Any, trail: str = "observation") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            _require(
                normalized not in _FORBIDDEN_PATH_KEYS,
                f"docling-host-path-field-forbidden:{trail}.{key}",
            )
            _walk_no_host_path(child, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_no_host_path(child, f"{trail}[{index}]")


def _validate_coordinate(value: Any, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    row = _exact(value, {"page_index", "bbox_points_bottom_left"}, label)
    _int(row["page_index"], f"{label}-page-index")
    _bbox(row["bbox_points_bottom_left"], f"{label}-bbox")
    return row


def _validate_warning(value: Any, index: int) -> dict[str, Any]:
    row = _exact(value, {"code", "details"}, f"docling-warning-{index}")
    _require(isinstance(row["code"], str) and row["code"], "docling-warning-code-invalid")
    _require(
        row["details"] is None or isinstance(row["details"], (str, int, float, bool, list, dict)),
        "docling-warning-details-invalid",
    )
    return row


def _validate_block(value: Any, index: int) -> dict[str, Any]:
    row = _exact(
        value,
        {
            "provider_ref",
            "text",
            "provider_label",
            "semantic_type",
            "semantic_level",
            "coordinate",
            "provenance_source",
        },
        f"docling-block-{index}",
    )
    _require(isinstance(row["provider_ref"], str) and row["provider_ref"], "docling-block-ref-invalid")
    _require(isinstance(row["text"], str) and row["text"], "docling-block-text-invalid")
    label = row["provider_label"]
    _require(isinstance(label, str) and label, "docling-block-label-invalid")
    semantic = row["semantic_type"]
    _require(semantic is None or semantic in _ACCEPTED_SEMANTIC_TYPES, "docling-block-semantic-type-invalid")
    if label not in _ACCEPTED_LABELS:
        _require(semantic is None, "docling-unmapped-label-cannot-have-semantic-type")
    level = row["semantic_level"]
    _require(level is None or (isinstance(level, int) and not isinstance(level, bool) and level >= 1), "docling-block-semantic-level-invalid")
    if level is not None:
        _require(semantic == "heading", "docling-semantic-level-requires-heading")
    _validate_coordinate(row["coordinate"], f"docling-block-{index}-coordinate")
    _require(
        row["provenance_source"] in {"docling-text-provenance", "docling-lossless-item"},
        "docling-block-provenance-source-invalid",
    )
    return row


def _validate_picture(value: Any, index: int) -> dict[str, Any]:
    row = _exact(
        value,
        {"provider_ref", "provider_label", "coordinate", "provenance_source"},
        f"docling-picture-{index}",
    )
    _require(isinstance(row["provider_ref"], str) and row["provider_ref"], "docling-picture-ref-invalid")
    _require(row["provider_label"] == "picture", "docling-picture-label-invalid")
    _validate_coordinate(row["coordinate"], f"docling-picture-{index}-coordinate")
    _require(row["provenance_source"] == "docling-picture-item", "docling-picture-source-invalid")
    return row


def _validate_caption_relation(value: Any, index: int) -> dict[str, Any]:
    row = _exact(
        value,
        {"relation_id", "picture_ref", "caption_ref", "relation_source"},
        f"docling-caption-relation-{index}",
    )
    for key in ("relation_id", "picture_ref", "caption_ref"):
        _require(isinstance(row[key], str) and row[key], f"docling-caption-relation-{key}-invalid")
    _require(
        row["relation_source"] == "docling-picture.captions-explicit-ref",
        "docling-caption-relation-source-invalid",
    )
    return row


def validate_docling_observation_bundle(value: Any) -> dict[str, Any]:
    bundle = _exact(
        value,
        {
            "bundle_version",
            "record_kind",
            "source_ref_id",
            "source_fingerprint",
            "provider",
            "route_profile",
            "observation",
        },
        "docling-observation-bundle",
    )
    _require(bundle["bundle_version"] == DOCLING_OBSERVATION_VERSION, "docling-observation-version-unsupported")
    _require(bundle["record_kind"] == "DoclingObservationBundle", "docling-observation-kind-invalid")
    _require(
        isinstance(bundle["source_ref_id"], str) and bundle["source_ref_id"].startswith("source-ref:"),
        "docling-source-ref-invalid",
    )
    _sha(bundle["source_fingerprint"], "docling-source-fingerprint")
    provider = _exact(
        bundle["provider"],
        {"provider_id", "version", "wheel_sha256", "environment_freeze_sha256", "model_payload_sha256"},
        "docling-provider",
    )
    _require(provider["provider_id"] == DOCLING_PROVIDER_ID, "docling-provider-id-invalid")
    _require(provider["version"] == DOCLING_PROVIDER_VERSION, "docling-provider-version-invalid")
    _sha(provider["wheel_sha256"], "docling-wheel-sha")
    _sha(provider["environment_freeze_sha256"], "docling-environment-freeze-sha")
    _sha(provider["model_payload_sha256"], "docling-model-payload-sha")
    _require(bundle["route_profile"] == DOCLING_PROFILE, "docling-profile-invalid")

    observation = _exact(
        bundle["observation"],
        {"status", "warnings", "blocks", "pictures", "picture_caption_relations", "raw_document_sha256"},
        "docling-observation",
    )
    _require(observation["status"] in {"success", "failed", "restricted", "unknown"}, "docling-status-invalid")
    _require(isinstance(observation["warnings"], list), "docling-warnings-invalid")
    for index, row in enumerate(observation["warnings"]):
        _validate_warning(row, index)
    for field, validator in (
        ("blocks", _validate_block),
        ("pictures", _validate_picture),
        ("picture_caption_relations", _validate_caption_relation),
    ):
        rows = observation[field]
        _require(isinstance(rows, list), f"docling-{field}-invalid")
        for index, row in enumerate(rows):
            validator(row, index)

    block_refs = [row["provider_ref"] for row in observation["blocks"]]
    picture_refs = [row["provider_ref"] for row in observation["pictures"]]
    _require(block_refs == sorted(block_refs), "docling-blocks-not-canonical")
    _require(picture_refs == sorted(picture_refs), "docling-pictures-not-canonical")
    relation_ids = [row["relation_id"] for row in observation["picture_caption_relations"]]
    _require(relation_ids == sorted(relation_ids), "docling-caption-relations-not-canonical")
    known_caption_refs = set(block_refs)
    known_picture_refs = set(picture_refs)
    for relation in observation["picture_caption_relations"]:
        _require(relation["picture_ref"] in known_picture_refs, "docling-caption-relation-picture-unknown")
        _require(relation["caption_ref"] in known_caption_refs, "docling-caption-relation-caption-unknown")

    _sha(observation["raw_document_sha256"], "docling-raw-document-sha")
    if observation["status"] != "success":
        _require(not observation["blocks"], "docling-non-success-blocks-forbidden")
        _require(not observation["pictures"], "docling-non-success-pictures-forbidden")
        _require(not observation["picture_caption_relations"], "docling-non-success-relations-forbidden")
    _walk_no_host_path(bundle)
    canonical_json_bytes(bundle)
    return bundle


def encode_docling_observation_bundle(value: dict[str, Any]) -> bytes:
    validate_docling_observation_bundle(value)
    return canonical_json_bytes(value)
