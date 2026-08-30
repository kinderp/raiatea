#!/usr/bin/env python3
"""Official PDF1c Docling ExtractorPlugin.

The plugin receives one Core-private PDF AssetHandle plus Core-selected provider
installation references. It emits only path-free DoclingObservation evidence;
Raiatea Core owns E-05 normalization and catalog publication.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from prototype.p0_vs1.docling_observation_contract import (
    DOCLING_OBSERVATION_MEDIA_TYPE,
    DOCLING_PROFILE,
    encode_docling_observation_bundle,
)
from prototype.p0_vs1.docling_process_environment import (
    read_docling_provider_paths_from_env,
)
from prototype.p0_vs1.docling_provider_runtime import (
    run_docling_pdf_product as run_docling_pdf,
)
from prototype.p0_vs1.docling_reference import (
    validate_reference_provider_record,
    verify_reference_docling,
)
from prototype.p0_vs1.plugin_io import plugin_read_handle, plugin_write_output
from prototype.p0_vs1.source_contract import PDF_MEDIA_TYPE


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
MANIFEST_PATH = HERE / "manifest.json"
TRANSPORT_ROOT = REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "transport" / "0.1.0"
RUNTIME_VALIDATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "runtime" / "1.0.0" / "validate_runtime.py"
if str(TRANSPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(TRANSPORT_ROOT))

from transport import (  # noqa: E402
    MAX_FRAME_BYTES,
    TransportError,
    decode_frame,
    encode_frame,
    error_message,
    notification_message,
    result_message,
)

_RUNTIME_SPEC = importlib.util.spec_from_file_location(
    "pdf1c_docling_runtime",
    RUNTIME_VALIDATOR_PATH,
)
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
assert _RUNTIME_SPEC.loader is not None
_RUNTIME_SPEC.loader.exec_module(RUNTIME)

SOURCE_REFERENCE_CONTRACT_ID = "raiatea.vs1.source-reference"
SOURCE_REFERENCE_CONTRACT_VERSION = "0.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _handshake(manifest: dict[str, Any], runtime_instance_id: str) -> dict[str, Any]:
    return {
        "record_type": "handshake",
        "identity": {
            "plugin_id": manifest["plugin"]["plugin_id"],
            "plugin_version": manifest["plugin"]["version"],
            "runtime_instance_id": runtime_instance_id,
            "manifest_fingerprint": RUNTIME.canonical_manifest_fingerprint(manifest),
            "runtime_contract_version": "1.0.0",
        },
        "advertised_profiles": [
            {"capability_id": "extract.run", "profile_id": DOCLING_PROFILE}
        ],
        "observed_at": _now(),
    }


def _input_refs(request: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in request.get("inputs", []):
        if (
            isinstance(item, dict)
            and item.get("kind") == "asset-handle"
            and isinstance(item.get("handle"), dict)
        ):
            value = item["handle"].get("handle_id")
            if isinstance(value, str):
                refs.append(value)
        elif (
            isinstance(item, dict)
            and item.get("kind") == "record-ref"
            and isinstance(item.get("record_ref"), dict)
        ):
            value = item["record_ref"].get("ref_id")
            if isinstance(value, str):
                refs.append(value)
    return refs


def _provenance(
    manifest: dict[str, Any],
    runtime_instance_id: str,
    request: dict[str, Any],
    output_refs: list[str],
    started_at: str,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "plugin_id": manifest["plugin"]["plugin_id"],
        "plugin_version": manifest["plugin"]["version"],
        "runtime_instance_id": runtime_instance_id,
        "invocation_id": request["invocation_id"],
        "capability": request["capability"],
        "started_at": started_at,
        "ended_at": _now(),
        "input_refs": _input_refs(request),
        "output_refs": output_refs,
    }
    rights_ref = request.get("runtime_context", {}).get("rights_decision_ref")
    if isinstance(rights_ref, str) and rights_ref:
        value["rights_decision_ref"] = rights_ref
    return value


def _failed(
    manifest: dict[str, Any],
    runtime_instance_id: str,
    request: dict[str, Any],
    *,
    started_at: str,
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "record_type": "invocation-result",
        "invocation_id": request.get("invocation_id"),
        "runtime_instance_id": runtime_instance_id,
        "status": "failed",
        "outputs": [],
        "diagnostic_refs": [],
        "error": {"code": code, "message": message, "retryable": False},
        "provenance": _provenance(
            manifest,
            runtime_instance_id,
            request,
            [],
            started_at,
        ),
    }


def _source_ref_input(request: dict[str, Any]) -> str:
    refs = [
        row.get("record_ref")
        for row in request.get("inputs", [])
        if isinstance(row, dict) and row.get("kind") == "record-ref"
    ]
    if len(refs) != 1 or not isinstance(refs[0], dict):
        raise ValueError("exactly-one-source-reference-record-ref-required")
    ref = refs[0]
    if ref.get("contract_id") != SOURCE_REFERENCE_CONTRACT_ID:
        raise ValueError("source-reference-contract-invalid")
    if ref.get("contract_version") != SOURCE_REFERENCE_CONTRACT_VERSION:
        raise ValueError("source-reference-version-invalid")
    if ref.get("record_kind") != "SourceReferenceRecord":
        raise ValueError("source-reference-kind-invalid")
    ref_id = ref.get("ref_id")
    if not isinstance(ref_id, str) or not ref_id.startswith("source-ref:"):
        raise ValueError("source-reference-id-invalid")
    return ref_id


def _asset_input(request: dict[str, Any]) -> dict[str, Any]:
    assets = [
        row.get("handle")
        for row in request.get("inputs", [])
        if isinstance(row, dict) and row.get("kind") == "asset-handle"
    ]
    if len(assets) != 1 or not isinstance(assets[0], dict):
        raise ValueError("exactly-one-pdf-asset-handle-required")
    handle = assets[0]
    if handle.get("media_type") != PDF_MEDIA_TYPE:
        raise ValueError("pdf-media-type-required")
    return handle


def _output_target(request: dict[str, Any]) -> dict[str, Any]:
    targets = request.get("output_targets")
    if not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict):
        raise ValueError("exactly-one-docling-observation-output-target-required")
    target = targets[0]
    if target.get("media_type") != DOCLING_OBSERVATION_MEDIA_TYPE:
        raise ValueError("docling-observation-media-type-required")
    return target


def _diagnostic(
    runtime_instance_id: str,
    invocation_id: str,
    status: str,
    blocks: int,
    pictures: int,
) -> dict[str, Any]:
    return {
        "record_type": "diagnostic",
        "diagnostic_id": f"diag:{runtime_instance_id}:{invocation_id}:docling-observed",
        "runtime_instance_id": runtime_instance_id,
        "invocation_id": invocation_id,
        "severity": "info" if status == "success" else "warning",
        "code": "pdf-docling-provider-observation-created",
        "message": f"Docling status={status} blocks={blocks} pictures={pictures}",
        "observed_at": _now(),
    }


def _invoke(
    manifest: dict[str, Any],
    runtime_instance_id: str,
    request: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started_at = _now()
    if request.get("capability") != {
        "capability_id": "extract.run",
        "profile_id": DOCLING_PROFILE,
    }:
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="unsupported-extractor-profile",
                message=f"DoclingPdfExtractorPlugin supports only extract.run/{DOCLING_PROFILE}",
            ),
            [],
        )
    rights_ref = request.get("runtime_context", {}).get("rights_decision_ref")
    if not isinstance(rights_ref, str) or not rights_ref.startswith("rights-decision:"):
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="rights-decision-required",
                message="Core PDF Docling extraction rights_decision_ref is required",
            ),
            [],
        )
    try:
        source_ref_id = _source_ref_input(request)
        input_handle = _asset_input(request)
        output_target = _output_target(request)
        fingerprint = input_handle.get("fingerprint")
        if not isinstance(fingerprint, str):
            raise ValueError("source-fingerprint-required")

        # Re-verify the exact provider installation before reading the private
        # source bytes. These paths are Core-selected provider assets, not Source
        # authority and never enter the output observation.
        wheel_path, artifacts_path, cache_root = read_docling_provider_paths_from_env(
            dict(os.environ)
        )
        provider = verify_reference_docling(
            wheel_path=wheel_path,
            artifacts_path=artifacts_path,
        )
        validate_reference_provider_record(provider)

        source_bytes = plugin_read_handle(input_handle)
        bundle = run_docling_pdf(
            source_bytes,
            source_ref_id=source_ref_id,
            source_fingerprint=fingerprint,
            provider=provider,
            artifacts_path=artifacts_path,
            cache_root=cache_root,
        )
        validate_reference_provider_record(bundle["provider"])
        payload = encode_docling_observation_bundle(bundle)
        completed = plugin_write_output(output_target, payload)
    except Exception as exc:
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="pdf-docling-extraction-failed",
                message=type(exc).__name__,
            ),
            [],
        )

    observation = bundle["observation"]
    diagnostic = _diagnostic(
        runtime_instance_id,
        request["invocation_id"],
        observation["status"],
        len(observation["blocks"]),
        len(observation["pictures"]),
    )
    result = {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": runtime_instance_id,
        "status": "completed",
        "outputs": [{"kind": "asset-handle", "handle": completed}],
        "diagnostic_refs": [diagnostic["diagnostic_id"]],
        "provenance": _provenance(
            manifest,
            runtime_instance_id,
            request,
            [completed["handle_id"]],
            started_at,
        ),
    }
    return result, [diagnostic]


def _write(message: dict[str, Any]) -> None:
    sys.stdout.buffer.write(encode_frame(message))
    sys.stdout.buffer.flush()


def main() -> int:
    manifest = _manifest()
    runtime_instance_id = f"runtime:pdf1c:docling:{os.getpid()}"
    handshake = _handshake(manifest, runtime_instance_id)
    handshaken = False
    while True:
        raw = sys.stdin.buffer.readline(MAX_FRAME_BYTES + 1)
        if raw == b"":
            return 0
        try:
            message = decode_frame(raw)
        except TransportError:
            _write(error_message(None, -32700, "Parse error"))
            continue
        if "method" not in message or "id" not in message:
            _write(error_message(message.get("id"), -32600, "Invalid Request"))
            continue
        request_id = message["id"]
        method = message["method"]
        params = message.get("params", {})
        if method == "raiatea.handshake":
            if params != {}:
                _write(error_message(request_id, -32602, "Handshake params must be empty"))
                continue
            _write(result_message(request_id, handshake))
            handshaken = True
            continue
        if not handshaken:
            _write(error_message(request_id, -32001, "Handshake required"))
            continue
        if method != "raiatea.invoke":
            _write(error_message(request_id, -32601, "Method not found"))
            continue
        if not isinstance(params, dict):
            _write(error_message(request_id, -32602, "Invalid invocation params"))
            continue
        try:
            RUNTIME.validate_invocation(params, manifest, handshake)
        except Exception as exc:
            _write(
                error_message(
                    request_id,
                    -32602,
                    f"Invalid Runtime v1 invocation: {exc}",
                )
            )
            continue
        result, diagnostics = _invoke(manifest, runtime_instance_id, params)
        for row in diagnostics:
            _write(notification_message("raiatea.diagnostic", row))
        _write(result_message(request_id, result))


if __name__ == "__main__":
    raise SystemExit(main())
