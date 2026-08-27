#!/usr/bin/env python3
"""Core-owned PDF1c child-environment builder for the official Docling plugin."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


BROKER_ENV = "RAIATEA_VS1_PLUGIN_IO_BROKER"
WHEEL_ENV = "RAIATEA_PDF1C_DOCLING_WHEEL"
ARTIFACTS_ENV = "RAIATEA_PDF1C_DOCLING_ARTIFACTS"
CACHE_ENV = "RAIATEA_PDF1C_DOCLING_CACHE_ROOT"


class DoclingProcessEnvironmentError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingProcessEnvironmentError(message)


def _absolute_existing(path: Path, *, kind: str) -> Path:
    _require(isinstance(path, Path), f"docling-{kind}-path-required")
    _require(path.is_absolute(), f"docling-{kind}-path-must-be-absolute")
    resolved = path.resolve(strict=True)
    _require(not path.is_symlink(), f"docling-{kind}-path-symlink-forbidden")
    return resolved


def build_docling_extra_env(
    broker_env: dict[str, str],
    *,
    wheel_path: Path,
    artifacts_path: Path,
    cache_root: Path,
) -> dict[str, str]:
    _require(isinstance(broker_env, dict), "docling-broker-environment-required")
    _require(set(broker_env) == {BROKER_ENV}, "docling-broker-environment-shape-invalid")
    broker = broker_env.get(BROKER_ENV)
    _require(isinstance(broker, str) and broker, "docling-broker-reference-required")

    wheel = _absolute_existing(wheel_path, kind="wheel")
    _require(wheel.is_file(), "docling-wheel-path-not-file")
    artifacts = _absolute_existing(artifacts_path, kind="artifacts")
    _require(artifacts.is_dir(), "docling-artifacts-path-not-directory")

    _require(isinstance(cache_root, Path), "docling-cache-path-required")
    _require(cache_root.is_absolute(), "docling-cache-path-must-be-absolute")
    cache_root.mkdir(parents=True, exist_ok=True)
    _require(not cache_root.is_symlink(), "docling-cache-path-symlink-forbidden")
    cache = cache_root.resolve(strict=True)
    _require(cache.is_dir(), "docling-cache-path-not-directory")

    # No environment entry is inherited from the caller here; this builder
    # returns only Core-selected provider-installation references plus the
    # already-issued private Plugin I/O broker.
    return {
        BROKER_ENV: broker,
        WHEEL_ENV: os.fspath(wheel),
        ARTIFACTS_ENV: os.fspath(artifacts),
        CACHE_ENV: os.fspath(cache),
    }


def read_docling_provider_paths_from_env(environment: dict[str, str]) -> tuple[Path, Path, Path]:
    _require(isinstance(environment, dict), "docling-child-environment-invalid")
    values: list[Path] = []
    for key, label in (
        (WHEEL_ENV, "wheel"),
        (ARTIFACTS_ENV, "artifacts"),
        (CACHE_ENV, "cache"),
    ):
        value = environment.get(key)
        _require(isinstance(value, str) and value, f"docling-child-{label}-reference-required")
        path = Path(value)
        _require(path.is_absolute(), f"docling-child-{label}-reference-must-be-absolute")
        values.append(path)
    return values[0], values[1], values[2]


__all__ = [
    "ARTIFACTS_ENV",
    "BROKER_ENV",
    "CACHE_ENV",
    "DoclingProcessEnvironmentError",
    "WHEEL_ENV",
    "build_docling_extra_env",
    "read_docling_provider_paths_from_env",
]
