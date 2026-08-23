#!/usr/bin/env python3
"""Verify the pinned Docling-managed RapidOCR payload used by B01-PDF-007.

The verifier is dependency-light and fail-closed: the observed file set, sizes,
SHA-256 values and canonical manifest digest must match the committed lock before
a RapidOCR measurement can be treated as reference evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def payload_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files: list[dict[str, Any]] = []
    if not root.is_dir():
        return {
            "root": str(root),
            "exists": False,
            "file_count": 0,
            "bytes": 0,
            "files": [],
            "manifest_sha256": None,
        }
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "root": str(root),
        "exists": True,
        "file_count": len(files),
        "bytes": sum(item["bytes"] for item in files),
        "files": files,
        "manifest_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def verify(lock: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    expected_files = lock.get("files") if isinstance(lock.get("files"), list) else []
    observed_files = observed.get("files") if isinstance(observed.get("files"), list) else []
    files_match = observed_files == expected_files
    checks = {
        "exists": observed.get("exists") is True,
        "file_count": observed.get("file_count") == lock.get("file_count"),
        "bytes": observed.get("bytes") == lock.get("bytes"),
        "files": files_match,
        "manifest_sha256": observed.get("manifest_sha256") == lock.get("manifest_sha256"),
    }
    return {
        "contract": {
            "name": "raiatea-p0-rapidocr-reference-verification",
            "version": "0.1.0",
            "scope": "benchmark-reference-only",
        },
        "profile_id": lock.get("profile_id"),
        "checks": checks,
        "verified": all(checks.values()),
        "expected_manifest_sha256": lock.get("manifest_sha256"),
        "observed_manifest_sha256": observed.get("manifest_sha256"),
        "expected_file_count": lock.get("file_count"),
        "observed_file_count": observed.get("file_count"),
        "expected_bytes": lock.get("bytes"),
        "observed_bytes": observed.get("bytes"),
        "observed": observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    result = verify(lock, payload_manifest(args.root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
