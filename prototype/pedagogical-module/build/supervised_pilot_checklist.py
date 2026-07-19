#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

FORMAT = "raiatea-supervised-pilot-checklist"
VERSION = 1
PLATFORMS = ("linux", "macos", "windows")
LAUNCHERS = ("posix", "powershell")
PHASES = (
    "releaseVerified",
    "runtimePreflightPassed",
    "privacyBoundaryConfirmed",
    "pilotStarted",
    "supervisionMaintained",
    "pilotStopped",
    "ownedStateCleaned",
    "temporaryCopiesRemoved",
)
STATUSES = ("not-started", "in-progress", "completed", "stopped")
TOP_FIELDS = {"format", "version", "releaseVersion", "platform", "launcher", "phases", "status"}


def _valid_release_version(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 64:
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789.-")
    return value[0].isalnum() and value[-1].isalnum() and set(value) <= allowed and value == value.lower()


def validate_checklist(value: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, dict):
        return ["$: must be an object"]
    for field in sorted(set(value) - TOP_FIELDS):
        issues.append(f"$.{field}: unsupported field")
    for field in sorted(TOP_FIELDS - set(value)):
        issues.append(f"$.{field}: required field missing")
    if TOP_FIELDS - set(value):
        return issues
    if value["format"] != FORMAT:
        issues.append("$.format: unsupported format")
    if value["version"] != VERSION:
        issues.append("$.version: unsupported version")
    if not _valid_release_version(value["releaseVersion"]):
        issues.append("$.releaseVersion: invalid release version")
    if value["platform"] not in PLATFORMS:
        issues.append("$.platform: unsupported platform")
    if value["launcher"] not in LAUNCHERS:
        issues.append("$.launcher: unsupported launcher")
    if value["platform"] == "windows" and value["launcher"] != "powershell":
        issues.append("$.launcher: Windows requires powershell")
    if value["platform"] in {"linux", "macos"} and value["launcher"] != "posix":
        issues.append("$.launcher: Linux and macOS require posix")
    phases = value["phases"]
    if not isinstance(phases, dict) or tuple(phases) != PHASES:
        issues.append("$.phases: keys must equal the canonical phase order")
    else:
        for key, result in phases.items():
            if not isinstance(result, bool):
                issues.append(f"$.phases.{key}: must be boolean")
    status = value["status"]
    if status not in STATUSES:
        issues.append("$.status: unsupported status")
    elif isinstance(phases, dict) and tuple(phases) == PHASES:
        results = tuple(phases.values())
        if status == "not-started" and any(results):
            issues.append("$.status: not-started requires all phases false")
        if status == "in-progress" and (not any(results) or all(results)):
            issues.append("$.status: in-progress requires a partial checklist")
        if status == "completed" and not all(results):
            issues.append("$.status: completed requires every phase true")
        if status == "stopped" and phases["pilotStopped"] is not True:
            issues.append("$.status: stopped requires pilotStopped true")
    return issues


def load_checklist(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("checklist must be one regular JSON file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"checklist is unreadable: {exc}") from exc
    issues = validate_checklist(value)
    if issues:
        raise ValueError("invalid checklist:\n- " + "\n- ".join(issues))
    return value


def write_checklist(path: Path, value: dict[str, Any]) -> Path:
    issues = validate_checklist(value)
    if issues:
        raise ValueError("invalid checklist:\n- " + "\n- ".join(issues))
    if os.path.lexists(os.fspath(path)):
        raise ValueError("checklist output path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("checklist output changed during creation") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a supervised Raiatea pilot checklist")
    parser.add_argument("checklist", type=Path)
    args = parser.parse_args()
    try:
        load_checklist(args.checklist)
    except ValueError as exc:
        print("Supervised pilot checklist validation failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print("Supervised pilot checklist is valid.")


if __name__ == "__main__":
    main()
