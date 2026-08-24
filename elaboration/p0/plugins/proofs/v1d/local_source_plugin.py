#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Any

from . import proof_broker as BROKER
from . import proof_protocol as P

MANIFEST_PATH = P.HERE / "manifests" / "local-read-only-source-proof.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _discover_records(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    refs: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if path.is_symlink():
            raise BROKER.ProofBrokerError("source-proof-symlink-forbidden")
        if not path.is_file():
            continue
        digest = _sha256(path)
        source_id = "proof-source:" + digest[:24]
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        record = {
            "proof_record_version": "0.1.0",
            "record_kind": "SourceReferenceProof",
            "source_id": source_id,
            "source_class": "local-user-authorized-proof-file",
            "logical_name": path.name,
            "media_type": media_type,
            "byte_length": path.stat().st_size,
            "fingerprint": "sha256:" + digest,
            "location_exposed": False,
            "proof_only": True,
        }
        ref = {
            "ref_id": source_id,
            "contract_id": "raiatea.plugin-proof.source-reference",
            "contract_version": "0.1.0",
            "record_kind": "SourceReferenceProof",
        }
        records.append(record)
        refs.append(ref)
    return records, refs


def invoke(manifest: dict[str, Any], request: dict[str, Any], runtime_instance_id: str):
    started = P.now()
    capability = request.get("capability", {})
    if capability != {"capability_id": "source.discover", "profile_id": "local-read-only"}:
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "unknown-capability-profile",
            "v1d source proof supports only source.discover/local-read-only",
            started_at=started,
        )
        return result, []

    workspace_scope_id = request.get("runtime_context", {}).get("workspace_scope_id")
    if not isinstance(workspace_scope_id, str):
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "unauthorized-runtime-request",
            "workspace scope is required",
            started_at=started,
        )
        return result, []

    try:
        root = BROKER.resolve_workspace(workspace_scope_id)
        records, refs = _discover_records(root)
    except BROKER.ProofBrokerError as exc:
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "unauthorized-runtime-request",
            str(exc),
            started_at=started,
        )
        return result, []

    targets = request.get("output_targets", [])
    if not isinstance(targets, list) or len(targets) != 1:
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "invalid-input-handle",
            "source proof requires exactly one Core-issued output target",
            started_at=started,
        )
        return result, []

    bundle = {
        "proof_contract": "raiatea.v1d.source-reference-bundle",
        "version": "0.1.0",
        "proof_only": True,
        "location_exposed": False,
        "record_refs": refs,
        "records": records,
    }
    payload = (json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    try:
        output_handle = BROKER.write_output_target(targets[0], payload)
    except BROKER.ProofBrokerError as exc:
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "output-contract-violation",
            str(exc),
            started_at=started,
        )
        return result, []

    outputs: list[dict[str, Any]] = [{"kind": "asset-handle", "handle": output_handle}]
    outputs.extend({"kind": "record-ref", "record_ref": row} for row in refs)
    output_refs = [output_handle["handle_id"]] + [row["ref_id"] for row in refs]
    diag = P.diagnostic(
        runtime_instance_id,
        request["invocation_id"],
        "source-proof-discovered",
        f"discovered {len(records)} project-created proof files without exposing host paths",
    )
    result = {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": runtime_instance_id,
        "status": "completed",
        "outputs": outputs,
        "diagnostic_refs": [diag["diagnostic_id"]],
        "provenance": P.provenance(manifest, runtime_instance_id, request, output_refs, started),
    }
    return result, [diag]


def main() -> int:
    return P.run_process(MANIFEST_PATH, "runtime:v1d:source", invoke)


if __name__ == "__main__":
    raise SystemExit(main())
