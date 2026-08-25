#!/usr/bin/env python3
"""Official VS1d direct EPUB ExtractorPlugin.

The plugin receives a Core-private EPUB scratch copy through an opaque AssetHandle
and emits accepted E-05 records in a Core-issued write-once bundle. It never sees
the user's source root or original source path.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from typing import Any

from prototype.p0_vs1.extraction_contract import (
    EXTRACTION_BUNDLE_MEDIA_TYPE,
    build_extraction_bundle,
    canonical_extraction_bundle_bytes,
)
from prototype.p0_vs1.plugin_io import plugin_read_handle, plugin_write_output
from prototype.p0_vs1.plugins.direct_epub.e05_adapter import adapt_direct_epub_observation
from prototype.p0_vs1.plugins.direct_epub.route import parse_direct_epub
from prototype.p0_vs1.source_contract import EPUB_MEDIA_TYPE


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

_RUNTIME_SPEC = importlib.util.spec_from_file_location("vs1d_direct_epub_runtime", RUNTIME_VALIDATOR_PATH)
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
assert _RUNTIME_SPEC.loader is not None
_RUNTIME_SPEC.loader.exec_module(RUNTIME)


SOURCE_REFERENCE_CONTRACT_ID = "raiatea.vs1.source-reference"
SOURCE_REFERENCE_CONTRACT_VERSION = "0.1.0"
E05_CONTRACT_ID = "raiatea.extraction.processing-run"
E05_VERSION = "0.1.0"


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
            {"capability_id": "extract.run", "profile_id": "epub-direct-stdlib"}
        ],
        "observed_at": _now(),
    }


def _input_refs(request: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in request.get("inputs", []):
        if isinstance(item, dict) and item.get("kind") == "asset-handle" and isinstance(item.get("handle"), dict):
            handle_id = item["handle"].get("handle_id")
            if isinstance(handle_id, str):
                refs.append(handle_id)
        elif isinstance(item, dict) and item.get("kind") == "record-ref" and isinstance(item.get("record_ref"), dict):
            ref_id = item["record_ref"].get("ref_id")
            if isinstance(ref_id, str):
                refs.append(ref_id)
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
        "provenance": _provenance(manifest, runtime_instance_id, request, [], started_at),
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
        raise ValueError("exactly-one-epub-asset-handle-required")
    handle = assets[0]
    if handle.get("media_type") != EPUB_MEDIA_TYPE:
        raise ValueError("epub-media-type-required")
    return handle


def _output_target(request: dict[str, Any]) -> dict[str, Any]:
    targets = request.get("output_targets")
    if not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict):
        raise ValueError("exactly-one-extraction-output-target-required")
    target = targets[0]
    if target.get("media_type") != EXTRACTION_BUNDLE_MEDIA_TYPE:
        raise ValueError("extraction-bundle-media-type-required")
    return target


def _extract(source_ref_id: str, source_bytes: bytes, fingerprint: str) -> dict[str, Any]:
    extraction_started_at = _now()
    with tempfile.TemporaryDirectory(prefix="raiatea-vs1d-epub-plugin-") as temporary:
        path = Path(temporary) / "source.epub"
        path.write_bytes(source_bytes)
        observation = parse_direct_epub(path)
    extraction_ended_at = _now()
    return adapt_direct_epub_observation(
        observation,
        source_id=source_ref_id,
        fingerprint=fingerprint,
        python_version=platform.python_version(),
        started_at=extraction_started_at,
        ended_at=extraction_ended_at,
    )


def _diagnostic(runtime_instance_id: str, invocation_id: str, units: int) -> dict[str, Any]:
    return {
        "record_type": "diagnostic",
        "diagnostic_id": f"diag:{runtime_instance_id}:{invocation_id}:epub-extracted",
        "runtime_instance_id": runtime_instance_id,
        "invocation_id": invocation_id,
        "severity": "info",
        "code": "epub-direct-extraction-completed",
        "message": f"direct EPUB extraction produced {units} normalized units",
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
        "profile_id": "epub-direct-stdlib",
    }:
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="unsupported-extractor-profile",
                message="DirectEpubExtractorPlugin supports only extract.run/epub-direct-stdlib",
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
                message="Core extraction rights_decision_ref is required",
            ),
            [],
        )

    try:
        source_ref_id = _source_ref_input(request)
        input_handle = _asset_input(request)
        output_target = _output_target(request)
        source_bytes = plugin_read_handle(input_handle)
        fingerprint = input_handle.get("fingerprint")
        if not isinstance(fingerprint, str):
            raise ValueError("source-fingerprint-required")
        adapted = _extract(source_ref_id, source_bytes, fingerprint)
        bundle = build_extraction_bundle(
            source_ref_id=source_ref_id,
            source_fingerprint=fingerprint,
            adapted=adapted,
        )
        payload = canonical_extraction_bundle_bytes(bundle)
        completed = plugin_write_output(output_target, payload)
    except Exception as exc:
        # Provider/parser failures are converted into one bounded Runtime failure.
        # Only the exception type crosses the plugin boundary; local paths/details
        # are deliberately not reflected into the public error string.
        return (
            _failed(
                manifest,
                runtime_instance_id,
                request,
                started_at=started_at,
                code="epub-extraction-failed",
                message=type(exc).__name__,
            ),
            [],
        )

    refs = bundle["record_refs"]
    outputs: list[dict[str, Any]] = [{"kind": "asset-handle", "handle": completed}]
    outputs.extend({"kind": "record-ref", "record_ref": ref} for ref in refs)
    output_refs = [completed["handle_id"]] + [ref["ref_id"] for ref in refs]
    representation = next(
        (
            bundle["records"][ref["ref_id"]]
            for ref in refs
            if ref["record_kind"] == "NormalizedRepresentationRecord"
        ),
        None,
    )
    unit_count = len(representation.get("units", [])) if isinstance(representation, dict) else 0
    diagnostic = _diagnostic(runtime_instance_id, request["invocation_id"], unit_count)
    result = {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": runtime_instance_id,
        "status": "completed",
        "outputs": outputs,
        "diagnostic_refs": [diagnostic["diagnostic_id"]],
        "provenance": _provenance(
            manifest,
            runtime_instance_id,
            request,
            output_refs,
            started_at,
        ),
    }
    return result, [diagnostic]


def _write(message: dict[str, Any]) -> None:
    sys.stdout.buffer.write(encode_frame(message))
    sys.stdout.buffer.flush()


def main() -> int:
    manifest = _manifest()
    runtime_instance_id = f"runtime:vs1d:direct-epub:{os.getpid()}"
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
            _write(error_message(request_id, -32602, f"Invalid Runtime v1 invocation: {exc}"))
            continue

        result, diagnostics = _invoke(manifest, runtime_instance_id, params)
        for row in diagnostics:
            _write(notification_message("raiatea.diagnostic", row))
        _write(result_message(request_id, result))


if __name__ == "__main__":
    raise SystemExit(main())
