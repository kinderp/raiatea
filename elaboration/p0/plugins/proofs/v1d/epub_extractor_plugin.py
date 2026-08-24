#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
from typing import Any

from . import proof_broker as BROKER
from . import proof_protocol as P

MANIFEST_PATH = P.HERE / "manifests" / "direct-epub-extractor-proof.json"
EPUB_ROUTE_PATH = P.REPO_ROOT / "elaboration" / "p0" / "benchmark" / "routes" / "epub_routes.py"
E05_ADAPTER_PATH = P.REPO_ROOT / "elaboration" / "p0" / "contracts" / "extraction" / "0.1.0" / "adapt_benchmark.py"

_ROUTE_SPEC = importlib.util.spec_from_file_location("v1d_epub_routes", EPUB_ROUTE_PATH)
EPUB_ROUTE = importlib.util.module_from_spec(_ROUTE_SPEC)
assert _ROUTE_SPEC.loader is not None
_ROUTE_SPEC.loader.exec_module(EPUB_ROUTE)

_ADAPTER_SPEC = importlib.util.spec_from_file_location("v1d_e05_adapter", E05_ADAPTER_PATH)
E05_ADAPTER = importlib.util.module_from_spec(_ADAPTER_SPEC)
assert _ADAPTER_SPEC.loader is not None
_ADAPTER_SPEC.loader.exec_module(E05_ADAPTER)

E05_CONTRACT_ID = "raiatea.extraction.processing-run"
E05_VERSION = "0.1.0"


def _fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _record_ref(ref_id: str, record_kind: str) -> dict[str, Any]:
    return {
        "ref_id": ref_id,
        "contract_id": E05_CONTRACT_ID,
        "contract_version": E05_VERSION,
        "record_kind": record_kind,
    }


def _adapt(path: Path) -> dict[str, Any]:
    observation = EPUB_ROUTE.parse_direct_epub(path)
    return E05_ADAPTER.adapt_direct_epub_observation(
        observation,
        source_id="B02-EPUB-001-v1d-proof",
        fingerprint=_fingerprint(path),
        python_version=platform.python_version(),
    )


def invoke(manifest: dict[str, Any], request: dict[str, Any], runtime_instance_id: str):
    started = P.now()
    capability = request.get("capability", {})
    if capability != {"capability_id": "extract.run", "profile_id": "epub-direct-stdlib"}:
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "unknown-capability-profile",
            "v1d EPUB proof supports only extract.run/epub-direct-stdlib",
            started_at=started,
        )
        return result, []

    inputs = request.get("inputs", [])
    if not isinstance(inputs, list) or len(inputs) != 1 or not isinstance(inputs[0], dict):
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "invalid-input-handle",
            "EPUB proof requires exactly one AssetHandle input",
            started_at=started,
        )
        return result, []
    item = inputs[0]
    handle = item.get("handle") if item.get("kind") == "asset-handle" else None
    if not isinstance(handle, dict):
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "invalid-input-handle",
            "EPUB proof input must be an AssetHandle",
            started_at=started,
        )
        return result, []
    if handle.get("media_type") != "application/epub+zip":
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "invalid-input-handle",
            "EPUB proof requires media_type application/epub+zip",
            started_at=started,
        )
        return result, []

    try:
        path = BROKER.resolve_read_handle(handle)
    except BROKER.ProofBrokerError as exc:
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "invalid-input-handle",
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
            "EPUB proof requires exactly one Core-issued output target",
            started_at=started,
        )
        return result, []

    try:
        adapted = _adapt(path)
    except Exception as exc:
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "provider-tool-failure",
            f"direct EPUB proof route failed: {type(exc).__name__}",
            started_at=started,
        )
        return result, []

    run = adapted.get("run")
    evidence = adapted.get("provider_evidence")
    normalized = adapted.get("normalized_representation")
    if not isinstance(run, dict) or not isinstance(evidence, dict):
        result = P.failed_result(
            manifest,
            runtime_instance_id,
            request,
            "output-contract-violation",
            "E-05 adapter did not produce required run/provider evidence records",
            started_at=started,
        )
        return result, []

    refs = [
        _record_ref(str(run["run_id"]), "ProcessingRunRecord"),
        _record_ref(str(evidence["evidence_id"]), "ProviderEvidenceRecord"),
    ]
    records: dict[str, Any] = {
        refs[0]["ref_id"]: run,
        refs[1]["ref_id"]: evidence,
    }
    if isinstance(normalized, dict):
        normalized_ref = _record_ref(str(normalized["representation_id"]), "NormalizedRepresentationRecord")
        refs.append(normalized_ref)
        records[normalized_ref["ref_id"]] = normalized

    bundle = {
        "proof_contract": "raiatea.v1d.e05-record-bundle",
        "version": "0.1.0",
        "proof_only": True,
        "provider_native_schema_exposed": False,
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
        "epub-direct-proof-completed",
        f"direct stdlib EPUB route produced {len(refs)} E-05 record references",
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
    return P.run_process(MANIFEST_PATH, "runtime:v1d:epub", invoke)


if __name__ == "__main__":
    raise SystemExit(main())
