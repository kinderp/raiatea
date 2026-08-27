#!/usr/bin/env python3
"""PDF1c exact-reference environment verification for the pinned Docling route."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import sys
from typing import Any


DOCLING_VERSION = "2.118.0"
DOCLING_WHEEL_SHA256 = "fd4962c9a54229bae1eb9b49f7fadb7e7b8affabf7e4fba1aac8cb335f558c8f"
DOCLING_ENVIRONMENT_FREEZE_SHA256 = "54625595793321bdcb4f7b5763122b2c403ce1f4ecbd6d7837ab619a96c39456"
DOCLING_MODEL_PAYLOAD_SHA256 = "c9afe973808a41c359c1f270f063097972985c096468089b206031395f8a885e"
DOCLING_MODEL_FILE_COUNT = 11
DOCLING_MODEL_BYTES = 342_987_978
DOCLING_REFERENCE_OS = "ubuntu-24.04"
DOCLING_REFERENCE_PYTHON = "3.12.14"
DOCLING_REFERENCE_ARCH = "x86_64"

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MODEL_LOCK_PATH = (
    REPO_ROOT
    / "elaboration"
    / "p0"
    / "benchmark"
    / "locks"
    / "docling-2.118.0-layout-model-payload.json"
)


class DoclingEnvironmentError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingEnvironmentError(message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise DoclingEnvironmentError("docling-model-file-read-failed") from exc
    return digest.hexdigest()


def load_model_lock() -> dict[str, Any]:
    try:
        value = json.loads(MODEL_LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DoclingEnvironmentError("docling-model-lock-unavailable") from exc
    _require(isinstance(value, dict), "docling-model-lock-invalid")
    _require(value.get("docling_version") == DOCLING_VERSION, "docling-model-lock-version-mismatch")
    _require(value.get("file_count") == DOCLING_MODEL_FILE_COUNT, "docling-model-lock-file-count-mismatch")
    _require(value.get("bytes") == DOCLING_MODEL_BYTES, "docling-model-lock-byte-count-mismatch")
    _require(value.get("payload_manifest_sha256") == DOCLING_MODEL_PAYLOAD_SHA256, "docling-model-lock-manifest-mismatch")
    files = value.get("files")
    _require(isinstance(files, list) and len(files) == DOCLING_MODEL_FILE_COUNT, "docling-model-lock-files-invalid")
    return value


def verify_model_payload(model_root: Path) -> dict[str, Any]:
    """Verify the Core-selected local model payload exactly against the accepted lock."""
    root = Path(model_root).resolve()
    _require(root.is_dir(), "docling-model-root-required")
    lock = load_model_lock()
    expected_paths: set[str] = set()
    total_bytes = 0
    for row in lock["files"]:
        _require(isinstance(row, dict), "docling-model-lock-file-invalid")
        relative = row.get("path")
        expected_bytes = row.get("bytes")
        expected_sha = row.get("sha256")
        _require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), "docling-model-lock-relative-path-invalid")
        _require(".." not in Path(relative).parts, "docling-model-lock-traversal-forbidden")
        _require(isinstance(expected_bytes, int) and expected_bytes >= 0, "docling-model-lock-size-invalid")
        _require(isinstance(expected_sha, str) and len(expected_sha) == 64, "docling-model-lock-sha-invalid")
        candidate = root / relative
        _require(candidate.is_file() and not candidate.is_symlink(), "docling-model-file-missing-or-unsafe")
        try:
            actual_size = candidate.stat().st_size
        except OSError as exc:
            raise DoclingEnvironmentError("docling-model-file-stat-failed") from exc
        _require(actual_size == expected_bytes, "docling-model-file-size-mismatch")
        _require(_sha256_file(candidate) == expected_sha, "docling-model-file-sha-mismatch")
        expected_paths.add(Path(relative).as_posix())
        total_bytes += actual_size

    _require(total_bytes == DOCLING_MODEL_BYTES, "docling-model-total-bytes-mismatch")
    return {
        "model_payload_sha256": DOCLING_MODEL_PAYLOAD_SHA256,
        "file_count": DOCLING_MODEL_FILE_COUNT,
        "bytes": total_bytes,
        "verified_paths": sorted(expected_paths),
    }


def validate_reference_environment_record(value: Any) -> dict[str, Any]:
    expected_keys = {
        "docling_version",
        "wheel_sha256",
        "environment_freeze_sha256",
        "model_payload_sha256",
        "platform",
        "python_version",
        "architecture",
        "remote_services_enabled",
        "external_plugins_enabled",
        "ocr_enabled",
        "table_structure_enabled",
        "code_enrichment_enabled",
        "formula_enrichment_enabled",
        "picture_classification_enabled",
        "picture_description_enabled",
        "chart_extraction_enabled",
    }
    _require(isinstance(value, dict) and set(value) == expected_keys, "docling-environment-record-shape-invalid")
    _require(value["docling_version"] == DOCLING_VERSION, "docling-environment-version-mismatch")
    _require(value["wheel_sha256"] == DOCLING_WHEEL_SHA256, "docling-environment-wheel-mismatch")
    _require(value["environment_freeze_sha256"] == DOCLING_ENVIRONMENT_FREEZE_SHA256, "docling-environment-freeze-mismatch")
    _require(value["model_payload_sha256"] == DOCLING_MODEL_PAYLOAD_SHA256, "docling-environment-model-mismatch")
    _require(value["platform"] == DOCLING_REFERENCE_OS, "docling-environment-platform-unsupported")
    _require(value["python_version"] == DOCLING_REFERENCE_PYTHON, "docling-environment-python-unsupported")
    _require(value["architecture"] == DOCLING_REFERENCE_ARCH, "docling-environment-architecture-unsupported")
    for key in (
        "remote_services_enabled",
        "external_plugins_enabled",
        "ocr_enabled",
        "table_structure_enabled",
        "code_enrichment_enabled",
        "formula_enrichment_enabled",
        "picture_classification_enabled",
        "picture_description_enabled",
        "chart_extraction_enabled",
    ):
        _require(value[key] is False, f"docling-environment-feature-must-be-disabled:{key}")
    return value


def reference_environment_record() -> dict[str, Any]:
    return {
        "docling_version": DOCLING_VERSION,
        "wheel_sha256": DOCLING_WHEEL_SHA256,
        "environment_freeze_sha256": DOCLING_ENVIRONMENT_FREEZE_SHA256,
        "model_payload_sha256": DOCLING_MODEL_PAYLOAD_SHA256,
        "platform": DOCLING_REFERENCE_OS,
        "python_version": DOCLING_REFERENCE_PYTHON,
        "architecture": DOCLING_REFERENCE_ARCH,
        "remote_services_enabled": False,
        "external_plugins_enabled": False,
        "ocr_enabled": False,
        "table_structure_enabled": False,
        "code_enrichment_enabled": False,
        "formula_enrichment_enabled": False,
        "picture_classification_enabled": False,
        "picture_description_enabled": False,
        "chart_extraction_enabled": False,
    }


def assert_reference_host() -> None:
    """Bound real-provider claims to the exact measured host class."""
    _require(sys.version.split()[0] == DOCLING_REFERENCE_PYTHON, "docling-host-python-unsupported")
    _require(platform.machine().lower() in {"x86_64", "amd64"}, "docling-host-architecture-unsupported")
    # The exact Ubuntu image is established by the CI job declaration; runtime
    # code deliberately does not infer distro identity from mutable host files.
