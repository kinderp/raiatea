#!/usr/bin/env python3
"""Verify the pinned Docling E-04e reference environment and model payload.

This verifier is dependency-light and intentionally separate from the measured
Docling route. It distinguishes stable model payload files from ephemeral
Hugging Face download/cache metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_name(spec: str) -> str:
    return spec.split("==", 1)[0].strip().lower()


def load_constraints(path: Path) -> list[str]:
    entries = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"unsupported constraint entry: {line}")
        entries.append(line)
    return sorted(entries, key=_package_name)


def installed_freeze() -> list[str]:
    entries = []
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            entries.append(f"{name}=={dist.version}")
    return sorted(entries, key=_package_name)


def freeze_sha256(entries: list[str]) -> str:
    return hashlib.sha256(("\n".join(entries) + "\n").encode("utf-8")).hexdigest()


def _is_ephemeral_model_cache(relative: Path) -> bool:
    return ".cache" in relative.parts


def model_payload_manifest(root: Path) -> dict[str, Any]:
    resolved = root.resolve()
    files: list[dict[str, Any]] = []
    if resolved.is_dir():
        for path in sorted(candidate for candidate in resolved.rglob("*") if candidate.is_file()):
            relative_path = path.relative_to(resolved)
            if _is_ephemeral_model_cache(relative_path):
                continue
            files.append(
                {
                    "path": relative_path.as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "root": str(resolved),
        "file_count": len(files),
        "bytes": sum(item["bytes"] for item in files),
        "files": files,
        "payload_manifest_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def verify_reference(
    constraints_path: Path,
    model_lock_path: Path,
    artifacts_path: Path,
) -> dict[str, Any]:
    expected_freeze = load_constraints(constraints_path)
    observed_freeze = installed_freeze()
    expected_set = set(expected_freeze)
    observed_set = set(observed_freeze)

    model_lock = json.loads(model_lock_path.read_text(encoding="utf-8"))
    observed_model = model_payload_manifest(artifacts_path)
    expected_files = model_lock.get("files", [])

    environment_match = observed_freeze == expected_freeze
    model_match = (
        observed_model["files"] == expected_files
        and observed_model["payload_manifest_sha256"]
        == model_lock.get("payload_manifest_sha256")
    )

    return {
        "contract": {
            "name": "raiatea-p0-docling-reference-verification",
            "version": "0.1.0",
            "scope": "benchmark-reference-only",
        },
        "environment": {
            "match": environment_match,
            "expected_count": len(expected_freeze),
            "observed_count": len(observed_freeze),
            "expected_sha256": freeze_sha256(expected_freeze),
            "observed_sha256": freeze_sha256(observed_freeze),
            "missing": sorted(expected_set - observed_set, key=str.lower),
            "unexpected": sorted(observed_set - expected_set, key=str.lower),
        },
        "model_payload": {
            "match": model_match,
            "expected_file_count": model_lock.get("file_count"),
            "observed_file_count": observed_model["file_count"],
            "expected_bytes": model_lock.get("bytes"),
            "observed_bytes": observed_model["bytes"],
            "expected_manifest_sha256": model_lock.get("payload_manifest_sha256"),
            "observed_manifest_sha256": observed_model["payload_manifest_sha256"],
            "observed_files": observed_model["files"],
        },
        "verified": environment_match and model_match,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--constraints", type=Path, required=True)
    parser.add_argument("--model-lock", type=Path, required=True)
    parser.add_argument("--artifacts-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = verify_reference(
        args.constraints.resolve(),
        args.model_lock.resolve(),
        args.artifacts_path.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
