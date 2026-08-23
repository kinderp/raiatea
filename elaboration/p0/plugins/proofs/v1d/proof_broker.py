#!/usr/bin/env python3
"""Proof-only v1d mapping from opaque Core ids to local test paths.

This module is deliberately not a Plugin API contract or production handle
broker. Public runtime records contain only workspace/handle/lease ids.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUNTIME_ROOT = HERE / ".proof-runtime"
FIXTURE_ROOT = RUNTIME_ROOT / "fixtures"
OUTPUT_ROOT = RUNTIME_ROOT / "outputs"
BROKER_PATH = RUNTIME_ROOT / "broker.json"


class ProofBrokerError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProofBrokerError(message)


def _load() -> dict[str, Any]:
    try:
        value = json.loads(BROKER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofBrokerError("proof-broker-unavailable") from exc
    _require(isinstance(value, dict) and value.get("proof_only") is True, "proof-broker-marker-required")
    return value


def _confined(root: Path, relative: Any, label: str) -> Path:
    _require(isinstance(relative, str) and relative, f"{label}-relative-path-required")
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ProofBrokerError(f"{label}-scope-escape") from exc
    return candidate


def resolve_workspace(workspace_scope_id: str) -> Path:
    value = _load()
    scopes = value.get("workspace_scopes")
    _require(isinstance(scopes, dict), "proof-workspace-map-required")
    relative = scopes.get(workspace_scope_id)
    path = _confined(FIXTURE_ROOT, relative, "workspace")
    _require(path.is_dir(), "proof-workspace-not-directory")
    return path


def resolve_read_handle(handle: dict[str, Any]) -> Path:
    _require(isinstance(handle, dict), "proof-read-handle-required")
    _require(handle.get("access") == "read", "proof-read-handle-access-required")
    handle_id = handle.get("handle_id")
    lease_id = handle.get("lease_id")
    _require(isinstance(handle_id, str) and handle_id, "proof-read-handle-id-required")
    value = _load()
    rows = value.get("read_handles")
    _require(isinstance(rows, dict) and isinstance(rows.get(handle_id), dict), "proof-read-handle-unknown")
    row = rows[handle_id]
    _require(row.get("lease_id") == lease_id, "proof-read-handle-lease-mismatch")
    path = _confined(FIXTURE_ROOT, row.get("relative_path"), "read-handle")
    _require(path.is_file(), "proof-read-handle-file-missing")
    return path


def resolve_output_target(handle: dict[str, Any]) -> Path:
    _require(isinstance(handle, dict), "proof-output-target-required")
    _require(handle.get("access") == "write-once-output", "proof-output-target-access-required")
    handle_id = handle.get("handle_id")
    lease_id = handle.get("lease_id")
    _require(isinstance(handle_id, str) and handle_id, "proof-output-target-id-required")
    value = _load()
    rows = value.get("output_handles")
    _require(isinstance(rows, dict) and isinstance(rows.get(handle_id), dict), "proof-output-target-unknown")
    row = rows[handle_id]
    _require(row.get("lease_id") == lease_id, "proof-output-target-lease-mismatch")
    path = _confined(OUTPUT_ROOT, row.get("relative_path"), "output-target")
    _require(path.parent.is_dir(), "proof-output-parent-missing")
    _require(not path.exists(), "proof-output-target-already-exists")
    return path


def write_output_target(handle: dict[str, Any], payload: bytes) -> dict[str, Any]:
    path = resolve_output_target(handle)
    maximum = handle.get("max_byte_length")
    if maximum is not None:
        _require(isinstance(maximum, int) and maximum >= 0, "proof-output-max-bytes-invalid")
        _require(len(payload) <= maximum, "proof-output-exceeds-core-byte-budget")
    with path.open("xb") as stream:
        stream.write(payload)
    result = {
        "handle_id": handle["handle_id"],
        "lease_id": handle["lease_id"],
        "access": "write-once-output",
        "byte_length": len(payload),
        "fingerprint": "sha256:" + hashlib.sha256(payload).hexdigest(),
    }
    for key in ("media_type", "expires_at"):
        if key in handle:
            result[key] = handle[key]
    return result


def proof_record_refs_from_bundle(bundle: dict[str, Any]) -> list[str]:
    refs = bundle.get("record_refs")
    _require(isinstance(refs, list), "proof-bundle-record-refs-required")
    values: list[str] = []
    for row in refs:
        _require(isinstance(row, dict) and isinstance(row.get("ref_id"), str), "proof-bundle-record-ref-invalid")
        values.append(row["ref_id"])
    return values
