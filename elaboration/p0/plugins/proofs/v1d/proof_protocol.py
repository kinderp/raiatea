#!/usr/bin/env python3
"""Shared proof-plugin process loop over accepted v1c candidate transport.

This module is proof code only. It imports the accepted transport/runtime layers
rather than redefining framing or runtime semantics.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
TRANSPORT_ROOT = REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "transport" / "0.1.0"
RUNTIME_VALIDATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "runtime" / "1.0.0" / "validate_runtime.py"
if str(TRANSPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(TRANSPORT_ROOT))

from transport import (  # noqa: E402
    MAX_FRAME_BYTES,
    TransportError,
    decode_frame,
    error_message,
    notification_message,
    result_message,
    encode_frame,
)

_RUNTIME_SPEC = importlib.util.spec_from_file_location("v1d_runtime_validator", RUNTIME_VALIDATOR_PATH)
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
assert _RUNTIME_SPEC.loader is not None
_RUNTIME_SPEC.loader.exec_module(RUNTIME)

InvokeHandler = Callable[[dict[str, Any], dict[str, Any], str], tuple[dict[str, Any], list[dict[str, Any]]]]


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def handshake_record(manifest: dict[str, Any], runtime_instance_id: str) -> dict[str, Any]:
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
            {"capability_id": capability["capability_id"], "profile_id": profile["profile_id"]}
            for capability in manifest["capabilities"]
            for profile in capability["profiles"]
        ],
        "observed_at": now(),
    }


def input_ref_ids(request: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in request.get("inputs", []):
        if not isinstance(item, dict):
            continue
        if item.get("kind") == "asset-handle" and isinstance(item.get("handle"), dict):
            refs.append(str(item["handle"].get("handle_id")))
        elif item.get("kind") == "record-ref" and isinstance(item.get("record_ref"), dict):
            refs.append(str(item["record_ref"].get("ref_id")))
    return refs


def provenance(
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
        "ended_at": now(),
        "input_refs": input_ref_ids(request),
        "output_refs": output_refs,
    }
    rights = request.get("runtime_context", {}).get("rights_decision_ref")
    if isinstance(rights, str) and rights:
        value["rights_decision_ref"] = rights
    return value


def diagnostic(runtime_instance_id: str, invocation_id: str, code: str, message: str, severity: str = "info") -> dict[str, Any]:
    return {
        "record_type": "diagnostic",
        "diagnostic_id": f"diag:{runtime_instance_id}:{invocation_id}:{code}",
        "runtime_instance_id": runtime_instance_id,
        "invocation_id": invocation_id,
        "severity": severity,
        "code": code,
        "message": message,
        "observed_at": now(),
    }


def failed_result(
    manifest: dict[str, Any],
    runtime_instance_id: str,
    request: dict[str, Any],
    code: str,
    message: str,
    *,
    started_at: str,
    retryable: bool = False,
    diagnostic_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": runtime_instance_id,
        "status": "failed",
        "outputs": [],
        "diagnostic_refs": diagnostic_refs or [],
        "error": {"code": code, "message": message, "retryable": retryable},
        "provenance": provenance(manifest, runtime_instance_id, request, [], started_at),
    }


def write_message(message: dict[str, Any]) -> None:
    sys.stdout.buffer.write(encode_frame(message))
    sys.stdout.buffer.flush()


def run_process(manifest_path: Path, runtime_prefix: str, invoke_handler: InvokeHandler) -> int:
    manifest = load_manifest(manifest_path)
    runtime_instance_id = f"{runtime_prefix}:{os.getpid()}"
    hs = handshake_record(manifest, runtime_instance_id)
    handshaken = False

    while True:
        raw = sys.stdin.buffer.readline(MAX_FRAME_BYTES + 1)
        if raw == b"":
            return 0
        try:
            message = decode_frame(raw)
        except TransportError:
            write_message(error_message(None, -32700, "Parse error"))
            continue

        if "method" not in message or "id" not in message:
            write_message(error_message(message.get("id"), -32600, "Invalid Request"))
            continue

        request_id = message["id"]
        method = message["method"]
        params = message.get("params", {})

        if method == "raiatea.handshake":
            if params != {}:
                write_message(error_message(request_id, -32602, "Handshake params must be empty"))
                continue
            write_message(result_message(request_id, hs))
            handshaken = True
            continue

        if not handshaken:
            write_message(error_message(request_id, -32001, "Handshake required"))
            continue

        if method == "raiatea.cancel":
            if not isinstance(params, dict) or params.get("record_type") != "cancel-request":
                write_message(error_message(request_id, -32602, "Invalid cancel request"))
                continue
            write_message(
                result_message(
                    request_id,
                    {
                        "record_type": "cancel-ack",
                        "invocation_id": params.get("invocation_id"),
                        "acknowledged": True,
                        "observed_at": now(),
                    },
                )
            )
            continue

        if method != "raiatea.invoke":
            write_message(error_message(request_id, -32601, "Method not found"))
            continue

        if not isinstance(params, dict):
            write_message(error_message(request_id, -32602, "Invalid invocation params"))
            continue

        try:
            RUNTIME.validate_invocation(params, manifest, hs)
        except Exception as exc:
            write_message(error_message(request_id, -32602, f"Invalid v1b invocation: {exc}"))
            continue

        parameters = params.get("parameters", {})
        if isinstance(parameters, dict) and parameters.get("proof_fault") == "crash":
            os._exit(72)

        try:
            result, diagnostics = invoke_handler(manifest, params, runtime_instance_id)
        except Exception as exc:
            started = now()
            result = failed_result(
                manifest,
                runtime_instance_id,
                params,
                "plugin-internal-failure",
                f"proof plugin internal failure: {type(exc).__name__}",
                started_at=started,
            )
            diagnostics = [
                diagnostic(
                    runtime_instance_id,
                    params.get("invocation_id", "unknown"),
                    "proof-plugin-internal-failure",
                    type(exc).__name__,
                    "error",
                )
            ]

        for row in diagnostics:
            write_message(notification_message("raiatea.diagnostic", row))
        write_message(result_message(request_id, result))
