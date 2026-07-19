#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

FORMAT = "raiatea-launch-preflight"
VERSION = 1
TOP_FIELDS = {
    "format",
    "version",
    "supportedPlatforms",
    "pythonMinimum",
    "runtimeCandidates",
    "host",
    "defaultPort",
    "minPort",
    "maxPort",
    "requiredFiles",
    "state",
    "diagnostics",
}
PYTHON_FIELDS = {"major", "minor"}
RUNTIME_FIELDS = {"posix", "windows"}
STATE_FIELDS = {"directory", "filename", "marker"}
SUPPORTED_PLATFORMS = ["linux", "macos", "windows"]
REQUIRED_FILES = [
    "RELEASE-NOTES.md",
    "SHA256SUMS",
    "pilot/index.html",
    "release-manifest.json",
]
DIAGNOSTICS = [
    "PORT_IN_USE",
    "PORT_INVALID",
    "PYTHON_NOT_FOUND",
    "PYTHON_UNSUPPORTED",
    "RELEASE_FILE_UNSAFE",
    "RELEASE_IDENTITY_MISMATCH",
    "RELEASE_NOT_FOUND",
    "SERVER_NOT_READY",
    "SERVER_START_FAILED",
    "STATE_ALREADY_EXISTS",
    "STATE_FOREIGN_PROCESS",
    "STATE_STALE",
    "STOP_FAILED",
]


def _closed_fields(value: object, expected: set[str], prefix: str, issues: list[str]) -> bool:
    if not isinstance(value, dict):
        issues.append(f"{prefix}: must be an object")
        return False
    for field in sorted(set(value) - expected):
        issues.append(f"{prefix}.{field}: unsupported field")
    for field in sorted(expected - set(value)):
        issues.append(f"{prefix}.{field}: required field missing")
    return not (set(value) - expected or expected - set(value))


def _canonical_relative_path(value: object, prefix: str, issues: list[str]) -> str | None:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        issues.append(f"{prefix}: must be a canonical relative POSIX path")
        return None
    path = PurePosixPath(value)
    if path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        issues.append(f"{prefix}: must be a canonical relative POSIX path")
        return None
    return value


def validate_contract(value: object) -> list[str]:
    issues: list[str] = []
    if not _closed_fields(value, TOP_FIELDS, "$", issues):
        return issues
    assert isinstance(value, dict)

    if value["format"] != FORMAT:
        issues.append("$.format: unsupported format")
    if value["version"] != VERSION:
        issues.append("$.version: unsupported version")
    if value["supportedPlatforms"] != SUPPORTED_PLATFORMS:
        issues.append("$.supportedPlatforms: must equal the canonical ordered platform list")

    python_minimum = value["pythonMinimum"]
    if _closed_fields(python_minimum, PYTHON_FIELDS, "$.pythonMinimum", issues):
        assert isinstance(python_minimum, dict)
        if python_minimum["major"] != 3 or python_minimum["minor"] != 10:
            issues.append("$.pythonMinimum: must equal Python 3.10")

    candidates = value["runtimeCandidates"]
    if _closed_fields(candidates, RUNTIME_FIELDS, "$.runtimeCandidates", issues):
        assert isinstance(candidates, dict)
        if candidates["posix"] != ["python3", "python"]:
            issues.append("$.runtimeCandidates.posix: unsupported candidate order")
        if candidates["windows"] != ["py -3", "python"]:
            issues.append("$.runtimeCandidates.windows: unsupported candidate order")

    if value["host"] != "127.0.0.1":
        issues.append("$.host: must equal 127.0.0.1")
    for field in ("defaultPort", "minPort", "maxPort"):
        number = value[field]
        if not isinstance(number, int) or isinstance(number, bool):
            issues.append(f"$.{field}: must be an integer")
    if not issues_for_port_fields(value):
        if value["minPort"] != 1024 or value["maxPort"] != 65535:
            issues.append("$.minPort/$.maxPort: unsupported port range")
        if not value["minPort"] <= value["defaultPort"] <= value["maxPort"]:
            issues.append("$.defaultPort: must be inside the configured range")

    files = value["requiredFiles"]
    if files != REQUIRED_FILES:
        issues.append("$.requiredFiles: must equal the canonical sorted file list")
    elif any(_canonical_relative_path(path, "$.requiredFiles", issues) is None for path in files):
        pass

    state = value["state"]
    if _closed_fields(state, STATE_FIELDS, "$.state", issues):
        assert isinstance(state, dict)
        expected_state = {
            "directory": ".raiatea-runtime",
            "filename": "server-state.json",
            "marker": "raiatea-launch-state-v1",
        }
        if state != expected_state:
            issues.append("$.state: unsupported runtime state contract")

    if value["diagnostics"] != DIAGNOSTICS:
        issues.append("$.diagnostics: must equal the canonical sorted diagnostic list")
    return issues


def issues_for_port_fields(value: dict[str, Any]) -> bool:
    return any(
        not isinstance(value.get(field), int) or isinstance(value.get(field), bool)
        for field in ("defaultPort", "minPort", "maxPort")
    )


def validate_port(value: object, contract: dict[str, Any]) -> int:
    if isinstance(value, bool):
        raise ValueError("PORT_INVALID")
    if isinstance(value, str):
        if not value.isascii() or not value.isdecimal():
            raise ValueError("PORT_INVALID")
        value = int(value)
    if not isinstance(value, int):
        raise ValueError("PORT_INVALID")
    if not contract["minPort"] <= value <= contract["maxPort"]:
        raise ValueError("PORT_INVALID")
    return value


def load_contract(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid launch preflight contract: {exc}") from exc
    issues = validate_contract(value)
    if issues:
        raise ValueError("invalid launch preflight contract:\n- " + "\n- ".join(issues))
    assert isinstance(value, dict)
    return value


def validate_verified_release(directory: Path, contract: dict[str, Any]) -> str:
    if not os.path.lexists(os.fspath(directory)) or not directory.is_dir() or directory.is_symlink():
        raise ValueError("RELEASE_NOT_FOUND")
    prefix = "raiatea-evaluator-"
    if not directory.name.startswith(prefix) or directory.name == prefix:
        raise ValueError("RELEASE_IDENTITY_MISMATCH")
    version = directory.name.removeprefix(prefix)
    manifest_path = directory / "release-manifest.json"
    for relative in contract["requiredFiles"]:
        target = directory / PurePosixPath(relative)
        if target.is_symlink() or not target.is_file():
            raise ValueError("RELEASE_FILE_UNSAFE")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("RELEASE_IDENTITY_MISMATCH") from exc
    if manifest.get("format") != "raiatea-evaluator-release" or manifest.get("releaseVersion") != version:
        raise ValueError("RELEASE_IDENTITY_MISMATCH")
    return version


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate the Raiatea launch preflight contract")
    parser.add_argument("contract", type=Path)
    parser.add_argument("--release", type=Path)
    parser.add_argument("--port")
    args = parser.parse_args()
    try:
        contract = load_contract(args.contract)
        if args.release is not None:
            validate_verified_release(args.release, contract)
        if args.port is not None:
            validate_port(args.port, contract)
    except ValueError as exc:
        print(exc)
        raise SystemExit(1) from exc
    print("Launch preflight contract is valid.")


if __name__ == "__main__":
    main()
