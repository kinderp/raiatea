#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

FORMAT = "raiatea-pilot-incident"
VERSION = 1
SEVERITIES = ("low", "medium", "high", "critical")
CATEGORIES = ("accessibility", "content", "privacy-boundary", "runtime", "supervision")
ACTIONS = ("continue-supervision", "pause-activity", "stop-pilot", "verify-cleanup")
RESOLUTIONS = ("open", "mitigated", "closed")
TOP_FIELDS = {"format", "version", "releaseVersion", "checklistSha256", "severity", "category", "unsafeRuntime", "stopRequired", "actions", "resolution"}


def _valid_release(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 64 and value == value.lower() and value[0].isalnum() and value[-1].isalnum() and set(value) <= set("abcdefghijklmnopqrstuvwxyz0123456789.-")


def _valid_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def required_stop(severity: str, category: str, unsafe_runtime: bool) -> bool:
    return severity == "critical" or category == "privacy-boundary" or unsafe_runtime


def validate_incident(value: object) -> list[str]:
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
    if not _valid_release(value["releaseVersion"]):
        issues.append("$.releaseVersion: invalid release version")
    if not _valid_digest(value["checklistSha256"]):
        issues.append("$.checklistSha256: must be lowercase SHA-256")
    if value["severity"] not in SEVERITIES:
        issues.append("$.severity: unsupported severity")
    if value["category"] not in CATEGORIES:
        issues.append("$.category: unsupported category")
    if not isinstance(value["unsafeRuntime"], bool):
        issues.append("$.unsafeRuntime: must be boolean")
    if not isinstance(value["stopRequired"], bool):
        issues.append("$.stopRequired: must be boolean")
    actions = value["actions"]
    if not isinstance(actions, list) or tuple(actions) != tuple(sorted(set(actions))):
        issues.append("$.actions: must be a sorted unique array")
    elif any(action not in ACTIONS for action in actions):
        issues.append("$.actions: contains unsupported action")
    if value["resolution"] not in RESOLUTIONS:
        issues.append("$.resolution: unsupported resolution")
    if value["severity"] in SEVERITIES and value["category"] in CATEGORIES and isinstance(value["unsafeRuntime"], bool) and isinstance(value["stopRequired"], bool):
        expected = required_stop(value["severity"], value["category"], value["unsafeRuntime"])
        if value["stopRequired"] != expected:
            issues.append("$.stopRequired: does not match canonical stop criteria")
        if expected and isinstance(actions, list) and "stop-pilot" not in actions:
            issues.append("$.actions: stop-required incidents must include stop-pilot")
    return issues


def load_incident(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("incident record must be one regular JSON file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"incident record is unreadable: {exc}") from exc
    issues = validate_incident(value)
    if issues:
        raise ValueError("invalid incident record:\n- " + "\n- ".join(issues))
    return value


def _write_no_replace(path: Path, value: dict[str, Any]) -> Path:
    issues = validate_incident(value)
    if issues:
        raise ValueError("invalid incident record:\n- " + "\n- ".join(issues))
    if os.path.lexists(os.fspath(path)):
        raise ValueError("incident output path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError as exc:
        raise ValueError("incident output changed during creation") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return path


def create_incident(path: Path, release_version: str, checklist_sha256: str, severity: str, category: str, unsafe_runtime: bool = False) -> Path:
    stop = required_stop(severity, category, unsafe_runtime)
    actions = ["stop-pilot", "verify-cleanup"] if stop else ["continue-supervision"]
    value = {"format": FORMAT, "version": VERSION, "releaseVersion": release_version, "checklistSha256": checklist_sha256, "severity": severity, "category": category, "unsafeRuntime": unsafe_runtime, "stopRequired": stop, "actions": sorted(actions), "resolution": "open"}
    return _write_no_replace(path, value)


def export_incident(source: Path, destination: Path) -> Path:
    return _write_no_replace(destination, load_incident(source))


def delete_incident(path: Path) -> None:
    load_incident(path)
    path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage one local supervised-pilot incident record")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("path", type=Path)
    create.add_argument("--release-version", required=True)
    create.add_argument("--checklist-sha256", required=True)
    create.add_argument("--severity", required=True, choices=SEVERITIES)
    create.add_argument("--category", required=True, choices=CATEGORIES)
    create.add_argument("--unsafe-runtime", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("path", type=Path)
    export = sub.add_parser("export")
    export.add_argument("source", type=Path)
    export.add_argument("destination", type=Path)
    delete = sub.add_parser("delete")
    delete.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create":
            print(create_incident(args.path, args.release_version, args.checklist_sha256, args.severity, args.category, args.unsafe_runtime))
        elif args.command == "validate":
            load_incident(args.path)
            print("Pilot incident record is valid.")
        elif args.command == "export":
            print(export_incident(args.source, args.destination))
        else:
            delete_incident(args.path)
            print("Pilot incident record deleted.")
    except (OSError, ValueError) as exc:
        print("Pilot incident operation failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
