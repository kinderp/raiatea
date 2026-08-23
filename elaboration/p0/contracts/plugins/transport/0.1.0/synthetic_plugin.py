#!/usr/bin/env python3
"""Synthetic transport-only plugin process for v1c conformance tests.

This is test equipment, not an architecture proof SourcePlugin.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transport import (  # noqa: E402
    MAX_FRAME_BYTES,
    TransportError,
    decode_frame,
    encode_frame,
    error_message,
    notification_message,
    result_message,
)

PLUGIN_ROOT = ROOT.parents[1] / "1.0.0"
MANIFEST_PATH = PLUGIN_ROOT / "examples" / "local-read-only-source.json"
RUNTIME_VALIDATOR_PATH = ROOT.parents[1] / "runtime" / "1.0.0" / "validate_runtime.py"
_RUNTIME_SPEC = importlib.util.spec_from_file_location("synthetic_runtime_validator", RUNTIME_VALIDATOR_PATH)
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
assert _RUNTIME_SPEC.loader is not None
_RUNTIME_SPEC.loader.exec_module(RUNTIME)

OBSERVED_AT = "2026-08-23T20:15:00Z"
STARTED_AT = "2026-08-23T20:15:01Z"
ENDED_AT = "2026-08-23T20:15:02Z"
RUNTIME_ID = "runtime:synthetic:transport:1"


def _write(message: dict[str, Any]) -> None:
    sys.stdout.buffer.write(encode_frame(message))
    sys.stdout.buffer.flush()


def _write_raw(message: dict[str, Any] | bytes) -> None:
    if isinstance(message, bytes):
        payload = message
    else:
        payload = json.dumps(message, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if not payload.endswith(b"\n"):
        payload += b"\n"
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def _input_refs(request: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in request.get("inputs", []):
        if not isinstance(item, dict):
            continue
        if item.get("kind") == "asset-handle" and isinstance(item.get("handle"), dict):
            refs.append(str(item["handle"].get("handle_id")))
        elif item.get("kind") == "record-ref" and isinstance(item.get("record_ref"), dict):
            refs.append(str(item["record_ref"].get("ref_id")))
    return refs


def _handshake(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "handshake",
        "identity": {
            "plugin_id": manifest["plugin"]["plugin_id"],
            "plugin_version": manifest["plugin"]["version"],
            "runtime_instance_id": RUNTIME_ID,
            "manifest_fingerprint": RUNTIME.canonical_manifest_fingerprint(manifest),
            "runtime_contract_version": "1.0.0",
        },
        "advertised_profiles": [
            {"capability_id": capability["capability_id"], "profile_id": profile["profile_id"]}
            for capability in manifest["capabilities"]
            for profile in capability["profiles"]
        ],
        "observed_at": OBSERVED_AT,
    }


def _provenance(manifest: dict[str, Any], request: dict[str, Any], output_refs: list[str]) -> dict[str, Any]:
    value = {
        "plugin_id": manifest["plugin"]["plugin_id"],
        "plugin_version": manifest["plugin"]["version"],
        "runtime_instance_id": RUNTIME_ID,
        "invocation_id": request["invocation_id"],
        "capability": request["capability"],
        "started_at": STARTED_AT,
        "ended_at": ENDED_AT,
        "input_refs": _input_refs(request),
        "output_refs": output_refs,
    }
    rights = request.get("runtime_context", {}).get("rights_decision_ref")
    if isinstance(rights, str) and rights:
        value["rights_decision_ref"] = rights
    return value


def _invocation_result(manifest: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    parameters = request.get("parameters", {})
    if isinstance(parameters, dict) and parameters.get("fail") is True:
        return {
            "record_type": "invocation-result",
            "invocation_id": request["invocation_id"],
            "runtime_instance_id": RUNTIME_ID,
            "status": "failed",
            "outputs": [],
            "diagnostic_refs": [],
            "error": {
                "code": "plugin-internal-failure",
                "message": "synthetic requested failure",
                "retryable": False,
            },
            "provenance": _provenance(manifest, request, []),
        }

    output_ref = {
        "kind": "record-ref",
        "record_ref": {
            "ref_id": f"source-ref:{request['invocation_id']}",
            "contract_id": "raiatea.source-reference",
            "contract_version": "0.1.0",
            "record_kind": "SourceReference",
        },
    }
    ref_id = output_ref["record_ref"]["ref_id"]
    return {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": RUNTIME_ID,
        "status": "completed",
        "outputs": [output_ref],
        "diagnostic_refs": [],
        "provenance": _provenance(manifest, request, [ref_id]),
    }


def _diagnostic(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "diagnostic",
        "diagnostic_id": f"diag:{request['invocation_id']}",
        "runtime_instance_id": RUNTIME_ID,
        "invocation_id": request["invocation_id"],
        "severity": "info",
        "code": "synthetic-progress",
        "message": "synthetic transport diagnostic",
        "observed_at": STARTED_AT,
    }


def run(mode: str) -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if mode == "crash-startup":
        return 70
    if mode == "noise-startup":
        sys.stdout.write("synthetic stdout noise\n")
        sys.stdout.flush()
    if mode == "stderr-diagnostic":
        sys.stderr.write(json.dumps(_diagnostic({"invocation_id": "stderr-only"})) + "\n")
        sys.stderr.flush()

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
            record = _handshake(manifest)
            response = result_message(request_id, record)
            if mode == "bad-version":
                bad = dict(response)
                bad["jsonrpc"] = "1.0"
                _write_raw(bad)
            else:
                _write(response)
                if mode == "duplicate-response":
                    _write(response)
            handshaken = True
            continue

        if not handshaken:
            _write(error_message(request_id, -32001, "Handshake required"))
            continue

        if method == "raiatea.invoke":
            if mode == "crash-invoke":
                os._exit(71)
            if mode == "protocol-error-invoke":
                _write(error_message(request_id, -32050, "Synthetic protocol misuse"))
                continue
            if not isinstance(params, dict):
                _write(error_message(request_id, -32602, "Invalid params"))
                continue
            parameters = params.get("parameters", {})
            if isinstance(parameters, dict) and parameters.get("emit_diagnostic") is True:
                _write(notification_message("raiatea.diagnostic", _diagnostic(params)))
            result = _invocation_result(manifest, params)
            if mode == "invalid-runtime-result":
                result["provenance"].pop("plugin_id", None)
            _write(result_message(request_id, result))
            continue

        if method == "raiatea.cancel":
            if not isinstance(params, dict):
                _write(error_message(request_id, -32602, "Invalid params"))
                continue
            if mode == "bad-cancel-ack":
                _write(result_message(request_id, {"record_type": "wrong-ack", "invocation_id": params.get("invocation_id")}))
                continue
            ack = {
                "record_type": "cancel-ack",
                "invocation_id": params.get("invocation_id"),
                "acknowledged": True,
                "observed_at": ENDED_AT,
            }
            _write(result_message(request_id, ack))
            continue

        _write(error_message(request_id, -32601, "Method not found"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        default="normal",
        choices=[
            "normal",
            "noise-startup",
            "bad-version",
            "duplicate-response",
            "stderr-diagnostic",
            "crash-startup",
            "crash-invoke",
            "protocol-error-invoke",
            "invalid-runtime-result",
            "bad-cancel-ack",
        ],
    )
    args = parser.parse_args()
    return run(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
