#!/usr/bin/env python3
"""Core-side conformance harness for the provisional local process transport."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any, BinaryIO, Sequence

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transport import (  # noqa: E402
    MAX_FRAME_BYTES,
    TransportError,
    decode_frame,
    encode_frame,
    request_message,
)

RUNTIME_VALIDATOR_PATH = ROOT.parents[1] / "runtime" / "1.0.0" / "validate_runtime.py"
_RUNTIME_SPEC = importlib.util.spec_from_file_location("raiatea_v1b_runtime_validator", RUNTIME_VALIDATOR_PATH)
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
assert _RUNTIME_SPEC.loader is not None
_RUNTIME_SPEC.loader.exec_module(RUNTIME)

MAX_STDERR_CAPTURE_BYTES = 64 * 1024
MAX_NOTIFICATIONS_BEFORE_RESPONSE = 64


class HarnessError(RuntimeError):
    pass


class ProcessExited(HarnessError):
    def __init__(self, returncode: int | None, phase: str):
        super().__init__(f"plugin-process-exited:{phase}:returncode={returncode}")
        self.returncode = returncode
        self.phase = phase


class RemoteProtocolError(HarnessError):
    def __init__(self, code: int, message: str):
        super().__init__(f"jsonrpc-remote-error:{code}:{message}")
        self.code = code
        self.remote_message = message


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LocalProcessHarness:
    """Small synchronous protocol harness with bounded concurrent stderr draining."""

    def __init__(self, command: Sequence[str], manifest: dict[str, Any]):
        self.command = [str(item) for item in command]
        self.manifest = manifest
        self.process: subprocess.Popen[bytes] | None = None
        self.handshake_record: dict[str, Any] | None = None
        self.diagnostics: list[dict[str, Any]] = []
        self.process_events: list[dict[str, Any]] = []
        self.lifecycle_events: list[dict[str, Any]] = []
        self._runtime_state: str | None = None
        self._rpc_counter = 0
        self._seen_response_ids: set[str | int | None] = set()
        self.last_transport_id: str | int | None = None
        self._stderr_capture = bytearray()
        self.stderr_truncated = False
        self._stderr_thread: threading.Thread | None = None

    def _drain_stderr(self, pipe: BinaryIO) -> None:
        while True:
            try:
                chunk = pipe.read(8192)
            except OSError:
                return
            if not chunk:
                return
            remaining = MAX_STDERR_CAPTURE_BYTES - len(self._stderr_capture)
            if remaining > 0:
                self._stderr_capture.extend(chunk[:remaining])
            if len(chunk) > max(remaining, 0):
                self.stderr_truncated = True

    def start(self) -> None:
        if self.process is not None:
            raise HarnessError("plugin-process-already-started")
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if self.process.stderr is None:
            raise HarnessError("plugin-stderr-unavailable")
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            args=(self.process.stderr,),
            name="raiatea-plugin-stderr-drain",
            daemon=True,
        )
        self._stderr_thread.start()
        self.process_events.append({"event": "process-started", "observed_at": _now()})

    def _require_process(self) -> subprocess.Popen[bytes]:
        if self.process is None:
            raise HarnessError("plugin-process-not-started")
        return self.process

    def _transition(self, target: str, basis: str) -> None:
        if self.handshake_record is None or self._runtime_state is None:
            raise HarnessError("runtime-lifecycle-before-validated-handshake")
        record = {
            "record_type": "lifecycle-transition",
            "runtime_instance_id": self.handshake_record["identity"]["runtime_instance_id"],
            "from": self._runtime_state,
            "to": target,
            "basis": basis,
            "observed_at": _now(),
        }
        try:
            RUNTIME.validate_transition(record)
        except Exception as exc:
            raise HarnessError(f"generated-lifecycle-transition-invalid:{exc}") from exc
        self.lifecycle_events.append(record)
        self._runtime_state = target

    def _record_process_exit(self, returncode: int | None, phase: str) -> None:
        if self.handshake_record is None:
            self.process_events.append(
                {
                    "event": "process-exited-before-handshake",
                    "returncode": returncode,
                    "phase": phase,
                    "observed_at": _now(),
                }
            )
            return
        if self._runtime_state in {"starting", "ready", "stopping"}:
            self._transition("failed", f"child process exited during {phase}; returncode={returncode}")

    def _next_rpc_id(self) -> str:
        self._rpc_counter += 1
        return f"rpc:{self._rpc_counter}"

    def _write_message(self, message: dict[str, Any]) -> None:
        process = self._require_process()
        if process.stdin is None:
            raise HarnessError("plugin-stdin-unavailable")
        if process.poll() is not None:
            self._record_process_exit(process.returncode, "before-write")
            raise ProcessExited(process.returncode, "before-write")
        frame = encode_frame(message)
        try:
            process.stdin.write(frame)
            process.stdin.flush()
        except BrokenPipeError as exc:
            returncode = process.poll()
            self._record_process_exit(returncode, "write")
            raise ProcessExited(returncode, "write") from exc

    def _read_message(self, phase: str) -> dict[str, Any]:
        process = self._require_process()
        if process.stdout is None:
            raise HarnessError("plugin-stdout-unavailable")
        raw = process.stdout.readline(MAX_FRAME_BYTES + 1)
        if raw == b"":
            returncode = process.poll()
            if returncode is None:
                try:
                    returncode = process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    pass
            self._record_process_exit(returncode, phase)
            raise ProcessExited(returncode, phase)
        try:
            return decode_frame(raw)
        except TransportError as exc:
            raise HarnessError(f"protocol-frame-invalid:{exc}") from exc

    def _handle_notification(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        if method != "raiatea.diagnostic":
            raise HarnessError(f"unsupported-jsonrpc-notification:{method}")
        diagnostic = message.get("params")
        if not isinstance(diagnostic, dict) or diagnostic.get("record_type") != "diagnostic":
            raise HarnessError("invalid-runtime-diagnostic-notification")
        if self.handshake_record is not None:
            runtime_id = self.handshake_record["identity"]["runtime_instance_id"]
            if diagnostic.get("runtime_instance_id") != runtime_id:
                raise HarnessError("diagnostic-runtime-instance-mismatch")
        self.diagnostics.append(diagnostic)

    def _request(self, method: str, params: dict[str, Any]) -> Any:
        request_id = self._next_rpc_id()
        self.last_transport_id = request_id
        self._write_message(request_message(request_id, method, params))
        notifications = 0
        while True:
            message = self._read_message(method)
            if "method" in message and "id" not in message:
                notifications += 1
                if notifications > MAX_NOTIFICATIONS_BEFORE_RESPONSE:
                    raise HarnessError("too-many-notifications-before-response")
                self._handle_notification(message)
                continue

            response_id = message.get("id")
            if response_id in self._seen_response_ids:
                raise HarnessError(f"duplicate-jsonrpc-response-id:{response_id}")
            if response_id != request_id:
                raise HarnessError(f"unexpected-jsonrpc-response-id:{response_id}:expected={request_id}")
            self._seen_response_ids.add(response_id)

            if "error" in message:
                error = message["error"]
                raise RemoteProtocolError(error["code"], error["message"])
            return message.get("result")

    def raw_request(self, method: str, params: dict[str, Any]) -> Any:
        """Transport-only request used by negative conformance tests."""
        return self._request(method, params)

    def handshake(self) -> dict[str, Any]:
        if self.process is None:
            self.start()
        result = self._request("raiatea.handshake", {})
        if not isinstance(result, dict):
            raise HarnessError("handshake-result-must-be-runtime-record")
        try:
            RUNTIME.validate_handshake(result, self.manifest)
        except Exception as exc:
            raise HarnessError(f"handshake-runtime-contract-invalid:{exc}") from exc
        self.handshake_record = result
        self._runtime_state = "starting"
        self._transition("ready", "validated runtime handshake over candidate transport")
        return result

    def invoke(self, request: dict[str, Any], *, secret_values: set[str] | None = None) -> dict[str, Any]:
        if self.handshake_record is None:
            raise HarnessError("invoke-before-handshake")
        if self._runtime_state != "ready":
            raise HarnessError(f"invoke-runtime-not-ready:{self._runtime_state}")
        try:
            RUNTIME.validate_invocation(request, self.manifest, self.handshake_record)
        except Exception as exc:
            raise HarnessError(f"invocation-runtime-contract-invalid:{exc}") from exc
        invocation_id = request.get("invocation_id")
        result = self._request("raiatea.invoke", request)
        if self.last_transport_id == invocation_id:
            raise HarnessError("transport-id-must-not-equal-invocation-id")
        if not isinstance(result, dict):
            raise HarnessError("invoke-result-must-be-runtime-record")
        try:
            RUNTIME.validate_result(result, request, self.manifest, secret_values or set())
        except Exception as exc:
            raise HarnessError(f"result-runtime-contract-invalid:{exc}") from exc
        return result

    def cancel(self, cancel_request: dict[str, Any]) -> dict[str, Any]:
        if self.handshake_record is None:
            raise HarnessError("cancel-before-handshake")
        if self._runtime_state != "ready":
            raise HarnessError(f"cancel-runtime-not-ready:{self._runtime_state}")
        if cancel_request.get("record_type") != "cancel-request":
            raise HarnessError("invalid-cancel-request-record")
        result = self._request("raiatea.cancel", cancel_request)
        if not isinstance(result, dict) or result.get("record_type") != "cancel-ack":
            raise HarnessError("invalid-cancel-ack-record")
        if result.get("invocation_id") != cancel_request.get("invocation_id"):
            raise HarnessError("cancel-ack-invocation-mismatch")
        return result

    def close(self) -> None:
        process = self.process
        if process is None:
            return
        if self.handshake_record is not None and self._runtime_state == "ready":
            self._transition("stopping", "Core requested synthetic harness shutdown")
        try:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
        except OSError:
            pass
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        if self.handshake_record is not None and self._runtime_state == "stopping":
            self._transition("stopped", "child process terminated after Core shutdown request")
        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=2)
        self.process = None

    @property
    def stderr_text(self) -> str:
        return bytes(self._stderr_capture).decode("utf-8", errors="replace")

    def __enter__(self) -> "LocalProcessHarness":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
