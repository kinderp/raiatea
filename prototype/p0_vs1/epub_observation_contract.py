#!/usr/bin/env python3
"""VS1d internal contract for the direct EPUB provider observation.

The official ExtractorPlugin owns parsing and emits this bounded provider-native
observation. Raiatea Core owns the later E-05 normalization step.
"""
from __future__ import annotations

from typing import Any

from prototype.p0_vs1.source_contract import canonical_json_bytes


OBSERVATION_BUNDLE_VERSION = "raiatea.vs1d.direct-epub-observation-bundle.0.1.0"
OBSERVATION_BUNDLE_MEDIA_TYPE = (
    "application/vnd.raiatea.vs1d-direct-epub-observation+json"
)
OBSERVATION_VERSION = "raiatea.vs1d.direct-epub-observation.0.1.0"
EXPECTED_PROVIDER_ID = "python-stdlib"
EXPECTED_ROUTE = "direct-epub-stdlib"
_ALLOWED_STATUSES = frozenset({"unknown", "success", "degraded", "partial", "failed", "rejected", "unsupported"})
_FORBIDDEN_HOST_KEYS = frozenset(
    {
        "path",
        "filepath",
        "file_path",
        "filename",
        "root",
        "relative_path",
        "location",
        "location_history",
        "host_path",
        "filesystem_path",
    }
)


class EpubObservationContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EpubObservationContractError(message)


def _walk_no_host_path(value: Any, *, trail: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            _require(
                normalized not in _FORBIDDEN_HOST_KEYS,
                f"epub-observation-host-path-field-forbidden:{trail}.{key}",
            )
            _walk_no_host_path(child, trail=f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_no_host_path(child, trail=f"{trail}[{index}]")


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def validate_direct_epub_observation(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "epub-observation-must-be-object")
    expected = {
        "observation_version",
        "route",
        "status",
        "warnings",
        "spine",
        "resources",
        "blocks",
        "navigation",
        "links",
        "active_content",
        "duration_seconds",
    }
    _require(set(value) == expected, "epub-observation-shape-invalid")
    _require(
        value["observation_version"] == OBSERVATION_VERSION,
        "epub-observation-version-unsupported",
    )
    _require(value["route"] == EXPECTED_ROUTE, "epub-observation-route-invalid")
    _require(value["status"] in _ALLOWED_STATUSES, "epub-observation-status-invalid")
    for key in ("warnings", "spine", "resources", "blocks", "navigation", "links", "active_content"):
        _require(isinstance(value[key], list), f"epub-observation-{key}-must-be-array")
    duration = value["duration_seconds"]
    _require(
        isinstance(duration, (int, float))
        and not isinstance(duration, bool)
        and duration >= 0,
        "epub-observation-duration-invalid",
    )
    _walk_no_host_path(value)
    canonical_json_bytes(value)
    return value


def build_provider_observation_bundle(
    *,
    source_ref_id: str,
    source_fingerprint: str,
    python_version: str,
    observation: dict[str, Any],
) -> dict[str, Any]:
    _require(
        isinstance(source_ref_id, str) and source_ref_id.startswith("source-ref:"),
        "provider-observation-source-ref-invalid",
    )
    _require(_valid_sha256(source_fingerprint), "provider-observation-fingerprint-invalid")
    _require(isinstance(python_version, str) and python_version, "provider-observation-python-version-required")
    validate_direct_epub_observation(observation)
    bundle = {
        "bundle_version": OBSERVATION_BUNDLE_VERSION,
        "record_kind": "DirectEpubProviderObservationBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": source_fingerprint,
        "provider": {
            "provider_id": EXPECTED_PROVIDER_ID,
            "version": python_version,
        },
        "observation": observation,
    }
    validate_provider_observation_bundle(bundle)
    return bundle


def validate_provider_observation_bundle(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "provider-observation-bundle-must-be-object")
    expected = {
        "bundle_version",
        "record_kind",
        "source_ref_id",
        "source_fingerprint",
        "provider",
        "observation",
    }
    _require(set(value) == expected, "provider-observation-bundle-shape-invalid")
    _require(
        value["bundle_version"] == OBSERVATION_BUNDLE_VERSION,
        "provider-observation-bundle-version-unsupported",
    )
    _require(
        value["record_kind"] == "DirectEpubProviderObservationBundle",
        "provider-observation-bundle-kind-invalid",
    )
    _require(
        isinstance(value["source_ref_id"], str)
        and value["source_ref_id"].startswith("source-ref:"),
        "provider-observation-source-ref-invalid",
    )
    _require(
        _valid_sha256(value["source_fingerprint"]),
        "provider-observation-fingerprint-invalid",
    )
    provider = value["provider"]
    _require(
        isinstance(provider, dict) and set(provider) == {"provider_id", "version"},
        "provider-observation-provider-shape-invalid",
    )
    _require(
        provider["provider_id"] == EXPECTED_PROVIDER_ID,
        "provider-observation-provider-invalid",
    )
    _require(
        isinstance(provider["version"], str) and provider["version"],
        "provider-observation-provider-version-invalid",
    )
    validate_direct_epub_observation(value["observation"])
    _walk_no_host_path(value)
    canonical_json_bytes(value)
    return value


def canonical_provider_observation_bytes(bundle: dict[str, Any]) -> bytes:
    validate_provider_observation_bundle(bundle)
    return canonical_json_bytes(bundle)
