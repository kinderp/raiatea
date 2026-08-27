#!/usr/bin/env python3
"""Closed path-free provider observation contract for PDF1b Poppler extraction."""
from __future__ import annotations

import json
from typing import Any


POPPLER_OBSERVATION_VERSION = "raiatea.pdf1b.poppler-observation.0.1.0"
POPPLER_OBSERVATION_MEDIA_TYPE = "application/vnd.raiatea.pdf1b-poppler-observation+json"
POPPLER_PROFILE = "pdf-poppler-pdftohtml-xml"
POPPLER_PROVIDER_ID = "poppler"
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
    }
)


class PopplerObservationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PopplerObservationError(message)


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
        raise PopplerObservationError("poppler-observation-not-json-safe") from exc


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(keys - actual)
    extra = sorted(actual - keys)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _sha(value: Any, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    _require(
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:]),
        f"{label}-invalid",
    )
    return value


def _nonnegative_int(value: Any, label: str) -> int:
    _require(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0,
        f"{label}-invalid",
    )
    return value


def _number(value: Any, label: str) -> float:
    _require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{label}-invalid",
    )
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
                f"poppler-host-path-field-forbidden:{trail}.{key}",
            )
            _walk_no_host_path(child, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_no_host_path(child, f"{trail}[{index}]")


def _validate_executable(value: Any, label: str) -> dict[str, Any]:
    row = _exact(value, {"version", "sha256"}, label)
    _require(isinstance(row["version"], str) and row["version"], f"{label}-version-invalid")
    _sha(row["sha256"], f"{label}-sha256")
    return row


def _validate_warning(value: Any, index: int) -> dict[str, Any]:
    row = _exact(value, {"code", "details"}, f"poppler-warning-{index}")
    _require(isinstance(row["code"], str) and row["code"], "poppler-warning-code-invalid")
    _require(
        row["details"] is None or isinstance(row["details"], (str, int, float, bool, list, dict)),
        "poppler-warning-details-invalid",
    )
    return row


def _validate_page(value: Any, index: int) -> dict[str, Any]:
    row = _exact(
        value,
        {"page_index", "width_points", "height_points"},
        f"poppler-page-{index}",
    )
    _nonnegative_int(row["page_index"], "poppler-page-index")
    _require(_number(row["width_points"], "poppler-page-width") > 0, "poppler-page-width-positive-required")
    _require(_number(row["height_points"], "poppler-page-height") > 0, "poppler-page-height-positive-required")
    return row


def _validate_block(value: Any, index: int) -> dict[str, Any]:
    row = _exact(
        value,
        {"block_id", "text", "page_index", "bbox_points_bottom_left"},
        f"poppler-block-{index}",
    )
    _require(isinstance(row["block_id"], str) and row["block_id"], "poppler-block-id-invalid")
    _require(isinstance(row["text"], str) and row["text"], "poppler-block-text-invalid")
    _nonnegative_int(row["page_index"], "poppler-block-page-index")
    _bbox(row["bbox_points_bottom_left"], "poppler-block-bbox")
    return row


def _validate_link(value: Any, index: int) -> dict[str, Any]:
    row = _exact(
        value,
        {"link_id", "kind", "target", "from_text", "page_index", "provider_source"},
        f"poppler-link-{index}",
    )
    _require(isinstance(row["link_id"], str) and row["link_id"], "poppler-link-id-invalid")
    _require(row["kind"] in {"uri", "other"}, "poppler-link-kind-invalid")
    _require(isinstance(row["target"], str) and row["target"], "poppler-link-target-invalid")
    _require(isinstance(row["from_text"], str), "poppler-link-text-invalid")
    _nonnegative_int(row["page_index"], "poppler-link-page-index")
    _require(row["provider_source"] == "pdftohtml-explicit-anchor", "poppler-link-source-invalid")
    return row


def _validate_figure(value: Any, index: int) -> dict[str, Any]:
    allowed = {
        "provider_ref",
        "provider_source",
        "page_index",
        "bbox_points_bottom_left",
        "asset_sha256",
        "asset_bytes",
        "pixel_width",
        "pixel_height",
        "decoded_pixel_sha256",
        "decode_warning",
    }
    _require(isinstance(value, dict), f"poppler-figure-{index}-must-be-object")
    _require(set(value).issubset(allowed), f"poppler-figure-{index}-unknown-field")
    required = {
        "provider_ref",
        "provider_source",
        "page_index",
        "bbox_points_bottom_left",
        "asset_sha256",
        "asset_bytes",
        "decoded_pixel_sha256",
        "decode_warning",
    }
    _require(required.issubset(value), f"poppler-figure-{index}-missing-field")
    _require(isinstance(value["provider_ref"], str) and value["provider_ref"], "poppler-figure-ref-invalid")
    _require(value["provider_source"] == "pdftohtml-explicit-image-element", "poppler-figure-source-invalid")
    _nonnegative_int(value["page_index"], "poppler-figure-page-index")
    _bbox(value["bbox_points_bottom_left"], "poppler-figure-bbox")
    _sha(value["asset_sha256"], "poppler-figure-asset-sha")
    _nonnegative_int(value["asset_bytes"], "poppler-figure-asset-bytes")
    _sha(value["decoded_pixel_sha256"], "poppler-figure-pixel-sha", nullable=True)
    _require(
        value["decode_warning"] is None or isinstance(value["decode_warning"], str),
        "poppler-figure-decode-warning-invalid",
    )
    has_pixels = value["decoded_pixel_sha256"] is not None
    if has_pixels:
        _require("pixel_width" in value and "pixel_height" in value, "poppler-figure-pixel-size-required")
        _require(_nonnegative_int(value["pixel_width"], "poppler-figure-pixel-width") > 0, "poppler-figure-pixel-width-positive-required")
        _require(_nonnegative_int(value["pixel_height"], "poppler-figure-pixel-height") > 0, "poppler-figure-pixel-height-positive-required")
    else:
        _require("pixel_width" not in value and "pixel_height" not in value, "poppler-figure-pixel-size-forbidden")
    return value


def validate_poppler_observation_bundle(value: Any) -> dict[str, Any]:
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
        "poppler-observation-bundle",
    )
    _require(bundle["bundle_version"] == POPPLER_OBSERVATION_VERSION, "poppler-observation-version-unsupported")
    _require(bundle["record_kind"] == "PopplerObservationBundle", "poppler-observation-kind-invalid")
    _require(isinstance(bundle["source_ref_id"], str) and bundle["source_ref_id"].startswith("source-ref:"), "poppler-source-ref-invalid")
    _sha(bundle["source_fingerprint"], "poppler-source-fingerprint")
    provider = _exact(bundle["provider"], {"provider_id", "version", "executables"}, "poppler-provider")
    _require(provider["provider_id"] == POPPLER_PROVIDER_ID, "poppler-provider-id-invalid")
    _require(isinstance(provider["version"], str) and provider["version"], "poppler-provider-version-invalid")
    executables = _exact(provider["executables"], {"pdftohtml", "pdfinfo"}, "poppler-executables")
    _validate_executable(executables["pdftohtml"], "poppler-pdftohtml")
    _validate_executable(executables["pdfinfo"], "poppler-pdfinfo")
    _require(bundle["route_profile"] == POPPLER_PROFILE, "poppler-profile-invalid")

    observation = _exact(
        bundle["observation"],
        {"status", "warnings", "pages", "blocks", "links", "figures", "raw_xml_sha256"},
        "poppler-observation",
    )
    _require(observation["status"] in {"success", "failed", "restricted", "unknown"}, "poppler-status-invalid")
    _require(isinstance(observation["warnings"], list), "poppler-warnings-invalid")
    for index, row in enumerate(observation["warnings"]):
        _validate_warning(row, index)
    for field, validator in (
        ("pages", _validate_page),
        ("blocks", _validate_block),
        ("links", _validate_link),
        ("figures", _validate_figure),
    ):
        rows = observation[field]
        _require(isinstance(rows, list), f"poppler-{field}-invalid")
        for index, row in enumerate(rows):
            validator(row, index)
    page_ids = [row["page_index"] for row in observation["pages"]]
    _require(page_ids == list(range(len(page_ids))), "poppler-pages-not-canonical")
    _require(
        [row["block_id"] for row in observation["blocks"]]
        == sorted(row["block_id"] for row in observation["blocks"]),
        "poppler-blocks-not-canonical",
    )
    _require(
        [row["link_id"] for row in observation["links"]]
        == sorted(row["link_id"] for row in observation["links"]),
        "poppler-links-not-canonical",
    )
    _require(
        [row["provider_ref"] for row in observation["figures"]]
        == sorted(row["provider_ref"] for row in observation["figures"]),
        "poppler-figures-not-canonical",
    )
    _sha(observation["raw_xml_sha256"], "poppler-raw-xml-sha", nullable=True)
    if observation["status"] != "success":
        _require(not observation["blocks"], "poppler-failed-observation-blocks-forbidden")
        _require(not observation["links"], "poppler-failed-observation-links-forbidden")
        _require(not observation["figures"], "poppler-failed-observation-figures-forbidden")
    _walk_no_host_path(bundle)
    canonical_json_bytes(bundle)
    return bundle


def encode_poppler_observation_bundle(value: dict[str, Any]) -> bytes:
    validate_poppler_observation_bundle(value)
    return canonical_json_bytes(value)
