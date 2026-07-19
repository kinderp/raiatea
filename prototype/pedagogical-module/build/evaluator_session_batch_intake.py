#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import evaluator_session_batch_manifest as batch_manifest
import evaluator_session_record


@dataclass(frozen=True)
class RecordSnapshot:
    path: str
    sha256: str
    value: dict[str, Any]


def _ensure_under_root(root: Path, relative: str) -> Path:
    canonical = batch_manifest.canonical_record_path(relative)
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*canonical.split("/"))
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"record path escapes intake root: {relative}") from exc
    current = root_resolved
    for part in canonical.split("/"):
        current = current / part
        if current.is_symlink():
            raise ValueError(f"record path contains a symbolic link: {relative}")
    if not candidate.is_file():
        raise ValueError(f"record is missing or not a regular file: {relative}")
    return candidate


def _canonical_record_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validate_batch_intake(manifest_path: Path, root: Path) -> tuple[RecordSnapshot, ...]:
    manifest = batch_manifest.load_manifest(manifest_path)
    snapshots: list[RecordSnapshot] = []
    seen_bytes: dict[bytes, str] = {}
    seen_values: dict[bytes, str] = {}

    for entry in manifest["records"]:
        relative = entry["path"]
        record_path = _ensure_under_root(root, relative)
        payload = record_path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"record digest mismatch: {relative}")
        try:
            value = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"record is unreadable JSON: {relative}: {exc}") from exc
        issues = evaluator_session_record.validate_record(value)
        if issues:
            raise ValueError(f"invalid evaluator session record: {relative}:\n- " + "\n- ".join(issues))
        assert isinstance(value, dict)
        canonical_value = _canonical_record_bytes(value)
        if payload in seen_bytes:
            raise ValueError(f"duplicate record bytes: {seen_bytes[payload]} and {relative}")
        if canonical_value in seen_values:
            raise ValueError(f"duplicate record value: {seen_values[canonical_value]} and {relative}")
        seen_bytes[payload] = relative
        seen_values[canonical_value] = relative
        snapshots.append(RecordSnapshot(path=relative, sha256=digest, value=value))

    return tuple(snapshots)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local evaluator-session records against a batch manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        snapshots = validate_batch_intake(args.manifest, args.root)
    except (OSError, ValueError) as exc:
        print("Evaluator-session batch intake failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print(f"Validated {len(snapshots)} evaluator-session records.")


if __name__ == "__main__":
    main()
