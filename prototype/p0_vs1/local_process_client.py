#!/usr/bin/env python3
"""Narrow Core-side local process client for VS1c.

It reuses the accepted transport/runtime primitives directly. It is not the
proof LocalProcessHarness and it is not a generic runtime extraction.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any, BinaryIO, Sequence


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TRANSPORT_ROOT = (
    REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "transport" / "0.1.0"
)
RUNTIME_VALIDATOR_PATH = (
    REPO_ROOT
    / "elaboration"
    / "p0"
    / "contracts"
    / "plugins"
    / "runtime"
    / "1.0.0"
    / "validate_runtime.py"
)
if str(TRANSPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(TRANSPORT_ROOT))

from transport import (  # noqa: E402
    MAX_FRAME_BYTES,
    TransportError,
    decode_frame,
    encode_frame,
    request_message,
)

_RUNTIME_SPEC = importlib.util.spec_from_file_location(
    "vs1c_runtime_validator", RUNTIME_VALIDATOR_PATH
)
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
assert _RUNTIME_SPEC.loader is not None
_RUNTIME_SPEC.loader.exec_module(RUNTIME)


MAX_STDERR_CAPTURE_BYTES = 64 * 1024
MAX_NOTIFICATIONS_BEFORE_RESPONSE = 64
ALLOWED_EXTRA_ENV_KEYS = frozenset({"RAIATEA_VS1_PLUGIN_IO_BROKER"})
# Only OS/runtime settings needed to launch the same local Python process are
# inherited. Credentials, proxies, cloud tokens and arbitrary user variables do
# not cross the VS1c plugin process boundary.
AMBIENT_ENV_ALLOWLIST = frozenset(
    {
        "SystemRoot",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "HOME",
        "USERPROFILE",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PYTHONUTF8",
        "PYTHONIOENCODING",
    }
)


class LocalPluginProcessError(RuntimeError):
    pass


class LocalPluginProcessExited(LocalPluginProcessError):
    pass


def build_child_environment(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build the bounded environment visible to the official VS1c plugin."""

    supplied = dict(extra_env or {})
    unknown = sorted(set(supplied) - ALLOWED_EXTRA_ENV_KEYS)
    if unknown:
        raise LocalPluginProcessError(
            f"vs1c-plugin-extra-environment-key-forbidden:{unknown[0]}"
        )
    env: dict[str, str] = {}
    for key in AMBIENT_ENV_ALLOWLIST:
        value = os.environ.get(key)
        if isinstance(value, str) and value:
            env[key] = value
    env.update(supplied)
    # Do not inherit an ambient PYTHONPATH/PYTHONHOME or user site-packages. The
    # official product plugin imports only the checked-out Raiatea tree + the
    # interpreter's normal standard environment.
    env["PYTHONPATH"] = os.fspath(REPO_ROOT)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def normalize_product_command(command: Sequence[str]) -> list[str]:
    values = [str(token) for token in command]
    if not values:
        raise LocalPluginProcessError("vs1c-plugin-command-required")
    if values[0] in {"python", "python3"}:
        values[0] = sys.executable
    return values


class LocalPluginProcessClient:
    def __init__(
        self,
        command: Sequence[str],
        manifest: dict[str, Any],
        *,
        extra_env: dict[str, str] | None = None,
    ) -> None:
        self.command = normalize_product_command(command)
        self.manifest = manifest
        self.extra_env = dict(extra_env or {})
        self.process: subprocess.Popen[bytes] | None = None
        self.handshake_record: dict[str, Any] | None = None
        self.diagnostics: list[dict[str, Any]] = []
        self._rpc_counter = 0
        self._seen_response_ids: set[str | int | None] = set()
        self._stderr_capture = bytearray()
        self._stderr_thread: threading.Thread | None = None
        self.stderr_truncated = False

    @property
    def stderr_text(self) -> str:
        return bytes(self._stderr_capture).decode("utf-8", errors="replace")

    def _drain_stderr(self, pipe: BinaryIO) -> None:
        while True:
            try:
                chunk = pipe.read(8192)
            except (OSError, ValueError):
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
            raise LocalPluginProcessError("vs1c-plugin-process-already-started")
        env = build_child_environment(self.extra_env)
        self.process = subprocess.Popen(
            self.command,
            cwd=REPO_ROOT,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if self.process.stderr is None:
            raise LocalPluginProcessError("vs1c-plugin-stderr-unavailable")
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            args=(self.process.stderr,),
            name="raiatea-vs1c-plugin-stderr",
            daemon=True,
        )
        self._stderr_thread.start()

    def _require_process(self) -> subprocess.Popen[bytes]:
        if self.process is None:
            raise LocalPluginProcessError("vs1c-plugin-process-not-started")
        return self.process

    def _next_id(self) -> str:
        self._rpc_counter += 1
        return f"vs1c-rpc:{self._rpc_counter}"

    def _write(self, message: dict[str, Any]) -> None:
        process = self._require_process()
        if process.stdin is None:
            raise LocalPluginProcessError("vs1c-plugin-stdin-unavailable")
        if process.poll() is not None:
            raise LocalPluginProcessExited(
                f"vs1c-plugin-exited-before-write:{process.returncode}"
            )
        try:
            process.stdin.write(encode_frame(message))
            process.stdin.flush()
        except BrokenPipeError as exc:
            raise LocalPluginProcessExited(
                f"vs1c-plugin-broken-pipe:{process.poll()}"
            ) from exc

    def _read(self) -> dict[str, Any]:
        process = self._require_process()
        if process.stdout is None:
            raise LocalPluginProcessError("vs1c-plugin-stdout-unavailable")
        raw = process.stdout.readline(MAX_FRAME_BYTES + 1)
        if raw == b"":
            returncode = process.poll()
            if returncode is None:
                try:
                    returncode = process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    pass
            raise LocalPluginProcessExited(
                f"vs1c-plugin-exited-before-response:{returncode}"
            )
        try:
            return decode_frame(raw)
        except TransportError as exc:
            raise LocalPluginProcessError(
                f"vs1c-plugin-frame-invalid:{exc}"
            ) from exc

    def _notification(self, message: dict[str, Any]) -> None:
        if message.get("method") != "raiatea.diagnostic":
            raise LocalPluginProcessError("vs1c-plugin-notification-unsupported")
        value = message.get("params")
        if not isinstance(value, dict) or value.get("record_type") != "diagnostic":
            raise LocalPluginProcessError("vs1c-plugin-diagnostic-invalid")
        if self.handshake_record is not None:
            runtime_id = self.handshake_record["identity"]["runtime_instance_id"]
            if value.get("runtime_instance_id") != runtime_id:
                raise LocalPluginProcessError(
                    "vs1c-plugin-diagnostic-runtime-mismatch"
                )
        self.diagnostics.append(value)

    def _request(self, method: str, params: dict[str, Any]) -> Any:
        request_id = self._next_id()
        self._write(request_message(request_id, method, params))
        notifications = 0
        while True:
            message = self._read()
            if "method" in message:
                if "id" in message:
                    raise LocalPluginProcessError(
                        "vs1c-plugin-initiated-request-forbidden"
                    )
                notifications += 1
                if notifications > MAX_NOTIFICATIONS_BEFORE_RESPONSE:
                    raise LocalPluginProcessError(
                        "vs1c-plugin-too-many-notifications"
                    )
                self._notification(message)
                continue
            response_id = message.get("id")
            if response_id in self._seen_response_ids:
                raise LocalPluginProcessError(
                    "vs1c-plugin-duplicate-response-id"
                )
            if response_id != request_id:
                raise LocalPluginProcessError(
                    "vs1c-plugin-unexpected-response-id"
                )
            self._seen_response_ids.add(response_id)
            if "error" in message:
                error = message["error"]
                code = error.get("code") if isinstance(error, dict) else None
                text = error.get("message") if isinstance(error, dict) else None
                raise LocalPluginProcessError(
                    f"vs1c-plugin-remote-protocol-error:{code}:{text}"
                )
            return message.get("result")

    def handshake(self) -> dict[str, Any]:
        if self.process is None:
            self.start()
        result = self._request("raiatea.handshake", {})
        if not isinstance(result, dict):
            raise LocalPluginProcessError(
                "vs1c-plugin-handshake-result-invalid"
            )
        try:
            RUNTIME.validate_handshake(result, self.manifest)
        except Exception as exc:
            raise LocalPluginProcessError(
                f"vs1c-plugin-handshake-contract-invalid:{exc}"
            ) from exc
        self.handshake_record = result
        return result

    def invoke(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.handshake_record is None:
            raise LocalPluginProcessError(
                "vs1c-plugin-invoke-before-handshake"
            )
        try:
            RUNTIME.validate_invocation(
                request, self.manifest, self.handshake_record
            )
        except Exception as exc:
            raise LocalPluginProcessError(
                f"vs1c-plugin-invocation-contract-invalid:{exc}"
            ) from exc
        result = self._request("raiatea.invoke", request)
        if not isinstance(result, dict):
            raise LocalPluginProcessError("vs1c-plugin-result-invalid")
        try:
            RUNTIME.validate_result(result, request, self.manifest, set())
        except Exception as exc:
            raise LocalPluginProcessError(
                f"vs1c-plugin-result-contract-invalid:{exc}"
            ) from exc
        return result

    def close(self) -> None:
        process = self.process
        if process is None:
            return
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
        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=2)
        for pipe in (process.stdout, process.stderr):
            if pipe is not None and not pipe.closed:
                try:
                    pipe.close()
                except OSError:
                    pass
        self._stderr_thread = None
        self.process = None

    def __enter__(self) -> "LocalPluginProcessClient":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
