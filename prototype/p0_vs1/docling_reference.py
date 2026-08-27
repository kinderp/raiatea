#!/usr/bin/env python3
"""PDF1c product verifier for the exact accepted local Docling reference.

This module copies only the dependency-light verification semantics from the
accepted benchmark evidence. Product runtime does not import benchmark route or
adapter modules.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
from typing import Any


DOCLING_VERSION = "2.118.0"
DOCLING_WHEEL_SHA256 = "fd4962c9a54229bae1eb9b49f7fadb7e7b8affabf7e4fba1aac8cb335f558c8f"
ENVIRONMENT_FREEZE_SHA256 = "54625595793321bdcb4f7b5763122b2c403ce1f4ecbd6d7837ab619a96c39456"
MODEL_PAYLOAD_SHA256 = "c9afe973808a41c359c1f270f063097972985c096468089b206031395f8a885e"
MODEL_FILE_COUNT = 11
MODEL_BYTES = 342987978
PYTHON_VERSION = "3.12.14"
PLATFORM_SYSTEM = "Linux"
PLATFORM_MACHINE = "x86_64"
OS_ID = "ubuntu"
OS_VERSION_ID = "24.04"

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_CONSTRAINTS = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "locks" / "docling-2.118.0-python312-linux-x86_64.txt"
DEFAULT_MODEL_LOCK = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "locks" / "docling-2.118.0-layout-model-payload.json"


class DoclingReferenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingReferenceError(message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_name(spec: str) -> str:
    return spec.split("==", 1)[0].strip().lower()


def load_constraints(path: Path = DEFAULT_CONSTRAINTS) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DoclingReferenceError("docling-constraints-unavailable") from exc
    entries: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        _require("==" in line, "docling-constraint-entry-unsupported")
        entries.append(line)
    return sorted(entries, key=_package_name)


def freeze_sha256(entries: list[str]) -> str:
    return hashlib.sha256(("\n".join(entries) + "\n").encode("utf-8")).hexdigest()


def installed_freeze(expected_entries: list[str]) -> list[str]:
    """Return versions only for the accepted constrained package set.

    Packaging/admin tools such as pip or setuptools are intentionally outside
    the accepted Docling dependency freeze unless they appear in the constraints
    lock. This mirrors the accepted benchmark verifier semantics.
    """
    entries: list[str] = []
    for name in sorted({_package_name(spec) for spec in expected_entries}):
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise DoclingReferenceError(
                f"docling-reference-package-missing:{name}"
            ) from exc
        entries.append(f"{name}=={version}")
    return sorted(entries, key=_package_name)


def _is_ephemeral_model_cache(relative: Path) -> bool:
    return ".cache" in relative.parts


def model_payload_manifest(root: Path) -> dict[str, Any]:
    resolved = root.resolve()
    _require(resolved.is_dir(), "docling-model-root-unavailable")
    files: list[dict[str, Any]] = []
    for path in sorted(candidate for candidate in resolved.rglob("*") if candidate.is_file()):
        relative = path.relative_to(resolved)
        if _is_ephemeral_model_cache(relative):
            continue
        files.append(
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "file_count": len(files),
        "bytes": sum(item["bytes"] for item in files),
        "files": files,
        "payload_manifest_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    result: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        result[key] = raw.strip().strip('"')
    return result


def current_platform_facts() -> dict[str, str]:
    os_release = _os_release()
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "os_id": os_release.get("ID", ""),
        "os_version_id": os_release.get("VERSION_ID", ""),
    }


def _load_model_lock(path: Path = DEFAULT_MODEL_LOCK) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DoclingReferenceError("docling-model-lock-unavailable") from exc
    _require(isinstance(value, dict), "docling-model-lock-invalid")
    _require(value.get("docling_version") == DOCLING_VERSION, "docling-model-lock-version-mismatch")
    _require(value.get("download_component") == "layout", "docling-model-lock-component-mismatch")
    _require(value.get("file_count") == MODEL_FILE_COUNT, "docling-model-lock-file-count-mismatch")
    _require(value.get("bytes") == MODEL_BYTES, "docling-model-lock-byte-count-mismatch")
    _require(value.get("payload_manifest_sha256") == MODEL_PAYLOAD_SHA256, "docling-model-lock-manifest-mismatch")
    _require(isinstance(value.get("files"), list), "docling-model-lock-files-invalid")
    return value


def _verify_platform(facts: dict[str, str]) -> None:
    _require(facts.get("system") == PLATFORM_SYSTEM, "docling-reference-platform-system-mismatch")
    _require(facts.get("machine") == PLATFORM_MACHINE, "docling-reference-platform-machine-mismatch")
    _require(facts.get("python_version") == PYTHON_VERSION, "docling-reference-python-version-mismatch")
    _require(facts.get("os_id") == OS_ID, "docling-reference-os-id-mismatch")
    _require(facts.get("os_version_id") == OS_VERSION_ID, "docling-reference-os-version-mismatch")


def verify_reference_docling(
    *,
    wheel_path: Path,
    artifacts_path: Path,
    constraints_path: Path = DEFAULT_CONSTRAINTS,
    model_lock_path: Path = DEFAULT_MODEL_LOCK,
    observed_freeze: list[str] | None = None,
    platform_facts: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Verify the exact product-accepted Docling reference before byte processing.

    `wheel_path` and `artifacts_path` are Core-selected local installation inputs,
    not user Source authority. The returned public provider record contains no
    host paths.
    """
    _verify_platform(platform_facts or current_platform_facts())

    wheel = wheel_path.resolve()
    _require(wheel.is_file(), "docling-reference-wheel-unavailable")
    _require(_sha256_file(wheel) == DOCLING_WHEEL_SHA256, "docling-reference-wheel-fingerprint-mismatch")

    expected_freeze = load_constraints(constraints_path)
    _require(freeze_sha256(expected_freeze) == ENVIRONMENT_FREEZE_SHA256, "docling-reference-constraints-drift")
    actual_freeze = (
        installed_freeze(expected_freeze)
        if observed_freeze is None
        else sorted(observed_freeze, key=_package_name)
    )
    _require(actual_freeze == expected_freeze, "docling-reference-environment-mismatch")
    try:
        installed_version = importlib.metadata.version("docling")
    except importlib.metadata.PackageNotFoundError as exc:
        raise DoclingReferenceError("docling-reference-package-unavailable") from exc
    _require(installed_version == DOCLING_VERSION, "docling-reference-package-version-mismatch")

    model_lock = _load_model_lock(model_lock_path)
    observed_model = model_payload_manifest(artifacts_path)
    _require(observed_model["file_count"] == MODEL_FILE_COUNT, "docling-reference-model-file-count-mismatch")
    _require(observed_model["bytes"] == MODEL_BYTES, "docling-reference-model-byte-count-mismatch")
    _require(observed_model["files"] == model_lock["files"], "docling-reference-model-files-mismatch")
    _require(observed_model["payload_manifest_sha256"] == MODEL_PAYLOAD_SHA256, "docling-reference-model-manifest-mismatch")

    return {
        "provider_id": "docling",
        "version": DOCLING_VERSION,
        "wheel_sha256": "sha256:" + DOCLING_WHEEL_SHA256,
        "environment_freeze_sha256": "sha256:" + ENVIRONMENT_FREEZE_SHA256,
        "model_payload_sha256": "sha256:" + MODEL_PAYLOAD_SHA256,
    }


def validate_reference_provider_record(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "docling-provider-record-must-be-object")
    _require(
        set(value)
        == {"provider_id", "version", "wheel_sha256", "environment_freeze_sha256", "model_payload_sha256"},
        "docling-provider-record-shape-invalid",
    )
    _require(value["provider_id"] == "docling", "docling-provider-record-id-invalid")
    _require(value["version"] == DOCLING_VERSION, "docling-provider-record-version-invalid")
    _require(value["wheel_sha256"] == "sha256:" + DOCLING_WHEEL_SHA256, "docling-provider-record-wheel-invalid")
    _require(
        value["environment_freeze_sha256"] == "sha256:" + ENVIRONMENT_FREEZE_SHA256,
        "docling-provider-record-environment-invalid",
    )
    _require(
        value["model_payload_sha256"] == "sha256:" + MODEL_PAYLOAD_SHA256,
        "docling-provider-record-model-invalid",
    )
    return value
