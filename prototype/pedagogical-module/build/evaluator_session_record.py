#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

FORMAT = "raiatea-evaluator-session"
VERSION = 1
DECLARATION = "local-only, optional, non-identifying evaluator observation"
PLATFORMS = ("linux", "macos", "windows")
LAUNCHERS = ("posix", "powershell")
RESULT_KEYS = (
    "archiveVerified",
    "helpersChecksummed",
    "invalidPortRejected",
    "launchSucceeded",
    "noMachineWideChanges",
    "releaseIdentityValidated",
    "stateCleanupSucceeded",
    "stopSucceeded",
)
TOP_FIELDS = {"format", "version", "releaseVersion", "platform", "launcher", "results", "observations", "declaration"}
SENSITIVE_KEY_PARTS = (
    "name", "email", "account", "learner", "answer", "browser", "storage", "ip", "host",
    "user", "path", "time", "date", "analytics", "telemetry", "device", "machine", "ticket",
)
EMAIL_RE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
IP_RE = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:[\\/]")
POSIX_PATH_RE = re.compile(r"(?:^|\s)/(?:[^\s/]+/)*[^\s/]*")


def _path_lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _validate_release_version(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?", value))


def _privacy_issues(text: str, prefix: str) -> list[str]:
    issues: list[str] = []
    if len(text) > 1000:
        issues.append(f"{prefix}: must contain at most 1000 characters")
    if len(text.encode("utf-8")) > 2000:
        issues.append(f"{prefix}: must contain at most 2000 UTF-8 bytes")
    if EMAIL_RE.search(text):
        issues.append(f"{prefix}: email-like values are forbidden")
    if IP_RE.search(text):
        issues.append(f"{prefix}: IP-address-like values are forbidden")
    if WINDOWS_PATH_RE.search(text) or POSIX_PATH_RE.search(text):
        issues.append(f"{prefix}: absolute path-like values are forbidden")
    lowered = text.casefold()
    for word in ("username", "hostname", "account id", "learner id", "student name", "timestamp"):
        if word in lowered:
            issues.append(f"{prefix}: privacy-sensitive wording is forbidden: {word}")
    return issues


def validate_record(value: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, dict):
        return ["$: must be an object"]
    unknown = sorted(set(value) - TOP_FIELDS)
    missing = sorted(TOP_FIELDS - set(value))
    issues.extend(f"$.{field}: unsupported field" for field in unknown)
    issues.extend(f"$.{field}: required field missing" for field in missing)
    if missing:
        return issues
    for key in value:
        lowered = key.casefold()
        if any(part in lowered for part in SENSITIVE_KEY_PARTS):
            issues.append(f"$.{key}: privacy-sensitive field name is forbidden")
    if value["format"] != FORMAT:
        issues.append("$.format: unsupported format")
    if value["version"] != VERSION:
        issues.append("$.version: unsupported version")
    if not _validate_release_version(value["releaseVersion"]):
        issues.append("$.releaseVersion: invalid release version")
    if value["platform"] not in PLATFORMS:
        issues.append("$.platform: unsupported platform")
    if value["launcher"] not in LAUNCHERS:
        issues.append("$.launcher: unsupported launcher")
    if value["platform"] == "windows" and value["launcher"] != "powershell":
        issues.append("$.launcher: Windows requires powershell")
    if value["platform"] in {"linux", "macos"} and value["launcher"] != "posix":
        issues.append("$.launcher: Linux and macOS require posix")
    results = value["results"]
    if not isinstance(results, dict):
        issues.append("$.results: must be an object")
    else:
        if tuple(results) != RESULT_KEYS:
            issues.append("$.results: keys must equal the canonical sorted result list")
        for key, result in results.items():
            if key not in RESULT_KEYS:
                issues.append(f"$.results.{key}: unsupported result")
            if not isinstance(result, bool):
                issues.append(f"$.results.{key}: must be boolean")
    observations = value["observations"]
    if not isinstance(observations, str):
        issues.append("$.observations: must be a string")
    else:
        issues.extend(_privacy_issues(observations, "$.observations"))
    if value["declaration"] != DECLARATION:
        issues.append("$.declaration: must equal the canonical local-only declaration")
    return issues


def load_record(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid evaluator session record: {exc}") from exc
    issues = validate_record(value)
    if issues:
        raise ValueError("invalid evaluator session record:\n- " + "\n- ".join(issues))
    assert isinstance(value, dict)
    return value


def create_record(path: Path, release_version: str, platform: str, launcher: str, observations: str = "") -> Path:
    if _path_lexists(path):
        raise ValueError("session record output path already exists")
    value = {
        "format": FORMAT,
        "version": VERSION,
        "releaseVersion": release_version,
        "platform": platform,
        "launcher": launcher,
        "results": {key: False for key in RESULT_KEYS},
        "observations": observations,
        "declaration": DECLARATION,
    }
    issues = validate_record(value)
    if issues:
        raise ValueError("invalid evaluator session record:\n- " + "\n- ".join(issues))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)[1])
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("session record output changed during creation") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return path


def export_record(source: Path, destination: Path) -> Path:
    value = load_record(source)
    if _path_lexists(destination):
        raise ValueError("session record export path already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary = Path(tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)[1])
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        try:
            os.link(temporary, destination, follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("session record export changed during creation") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def delete_record(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError("session record is missing or unsafe")
    load_record(path)
    path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage one local Raiatea evaluator session record")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("path", type=Path)
    create.add_argument("--release-version", required=True)
    create.add_argument("--platform", required=True, choices=PLATFORMS)
    create.add_argument("--launcher", required=True, choices=LAUNCHERS)
    create.add_argument("--observations", default="")
    validate = subparsers.add_parser("validate")
    validate.add_argument("path", type=Path)
    export = subparsers.add_parser("export")
    export.add_argument("source", type=Path)
    export.add_argument("destination", type=Path)
    delete = subparsers.add_parser("delete")
    delete.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create":
            result = create_record(args.path, args.release_version, args.platform, args.launcher, args.observations)
            print(result)
        elif args.command == "validate":
            load_record(args.path)
            print("Evaluator session record is valid.")
        elif args.command == "export":
            print(export_record(args.source, args.destination))
        else:
            delete_record(args.path)
            print("Evaluator session record deleted.")
    except (OSError, ValueError) as exc:
        print("Evaluator session record operation failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
