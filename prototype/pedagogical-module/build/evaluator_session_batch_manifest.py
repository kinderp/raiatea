#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

FORMAT = "raiatea-evaluator-session-batch-manifest"
VERSION = 1
RECORD_FORMAT = "raiatea-evaluator-session"
RECORD_VERSION = 1
MAX_RECORDS = 1024
TOP_FIELDS = {"format", "version", "records"}
ENTRY_FIELDS = {"path", "sha256", "recordFormat", "recordVersion"}
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def canonical_record_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("record path must be a non-empty string")
    if value.startswith("/") or "\\" in value:
        raise ValueError("record path must be relative POSIX syntax")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("record path contains an unsafe segment")
    canonical = path.as_posix()
    if canonical != value or not canonical.endswith(".json"):
        raise ValueError("record path must be canonical and end in .json")
    return canonical


def validate_manifest(value: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, dict):
        return ["$: must be an object"]
    for field in sorted(set(value) - TOP_FIELDS):
        issues.append(f"$.{field}: unsupported field")
    for field in sorted(TOP_FIELDS - set(value)):
        issues.append(f"$.{field}: required field missing")
    if TOP_FIELDS - set(value):
        return issues
    if value.get("format") != FORMAT:
        issues.append("$.format: unsupported format")
    if value.get("version") != VERSION:
        issues.append("$.version: unsupported version")
    records = value.get("records")
    if not isinstance(records, list) or not records:
        issues.append("$.records: must be a non-empty array")
        return issues
    if len(records) > MAX_RECORDS:
        issues.append(f"$.records: must contain at most {MAX_RECORDS} entries")
    paths: list[str] = []
    digests: list[str] = []
    for index, entry in enumerate(records):
        prefix = f"$.records[{index}]"
        if not isinstance(entry, dict):
            issues.append(f"{prefix}: must be an object")
            continue
        for field in sorted(set(entry) - ENTRY_FIELDS):
            issues.append(f"{prefix}.{field}: unsupported field")
        for field in sorted(ENTRY_FIELDS - set(entry)):
            issues.append(f"{prefix}.{field}: required field missing")
        if ENTRY_FIELDS - set(entry):
            continue
        try:
            paths.append(canonical_record_path(entry["path"]))
        except ValueError as exc:
            issues.append(f"{prefix}.path: {exc}")
        digest = entry["sha256"]
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            issues.append(f"{prefix}.sha256: must be 64 lowercase hexadecimal characters")
        else:
            digests.append(digest)
        if entry["recordFormat"] != RECORD_FORMAT:
            issues.append(f"{prefix}.recordFormat: unsupported record format")
        if entry["recordVersion"] != RECORD_VERSION:
            issues.append(f"{prefix}.recordVersion: unsupported record version")
    if len(paths) != len(set(paths)):
        issues.append("$.records: duplicate paths are forbidden")
    if len(digests) != len(set(digests)):
        issues.append("$.records: duplicate digests are forbidden")
    if paths != sorted(paths):
        issues.append("$.records: paths must be sorted lexicographically")
    return issues


def build_manifest(entries: Iterable[tuple[str, str]]) -> dict[str, Any]:
    records = [
        {
            "path": canonical_record_path(path),
            "sha256": digest,
            "recordFormat": RECORD_FORMAT,
            "recordVersion": RECORD_VERSION,
        }
        for path, digest in entries
    ]
    manifest = {"format": FORMAT, "version": VERSION, "records": records}
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("invalid batch manifest:\n- " + "\n- ".join(issues))
    return manifest


def load_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("batch manifest must be one regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"batch manifest is unreadable: {exc}") from exc
    issues = validate_manifest(value)
    if issues:
        raise ValueError("invalid batch manifest:\n- " + "\n- ".join(issues))
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an evaluator-session batch manifest")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        load_manifest(args.manifest)
    except ValueError as exc:
        print("Batch manifest validation failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print("Evaluator-session batch manifest is valid.")


if __name__ == "__main__":
    main()
