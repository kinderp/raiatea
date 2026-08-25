#!/usr/bin/env python3
"""VS1c private Core/plugin I/O broker for one local process invocation.

This is deliberately slice-specific. It brokers only Core-owned temporary
DiscoverySnapshot inputs and write-once SourceReferenceBundle outputs. It is not
an extracted generic Module Runtime and it never maps a handle to the user's
source filesystem.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import tempfile
from typing import Any


BROKER_VERSION = "raiatea.vs1c.plugin-io.0.1.0"
BROKER_ENV = "RAIATEA_VS1_PLUGIN_IO_BROKER"
READ_HANDLE_KEYS = frozenset(
    {"handle_id", "lease_id", "access", "media_type", "byte_length", "fingerprint", "expires_at"}
)
OUTPUT_TARGET_KEYS = frozenset(
    {"handle_id", "lease_id", "access", "media_type", "max_byte_length", "expires_at"}
)
COMPLETED_OUTPUT_KEYS = frozenset(
    {"handle_id", "lease_id", "access", "media_type", "byte_length", "fingerprint", "expires_at"}
)


class PluginIOError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PluginIOError(message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any, label: str) -> datetime:
    _require(isinstance(value, str) and value, f"{label}-required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PluginIOError(f"{label}-invalid") from exc
    _require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{label}-timezone-required")
    return parsed.astimezone(timezone.utc)


def _sha(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _valid_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PluginIOError("plugin-io-record-not-json-safe") from exc


def _exact_keys(value: Any, expected: frozenset[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _is_reparse(path: Path) -> bool:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = int(getattr(info, "st_file_attributes", 0))
    flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return bool(attributes & flag)


def _safe_private_file(root: Path, area: str, filename: str) -> Path:
    _require(area in {"inputs", "outputs"}, "plugin-io-area-invalid")
    _require(isinstance(filename, str) and filename and "/" not in filename and "\\" not in filename, "plugin-io-filename-invalid")
    area_path = root / area
    _require(area_path.is_dir() and not _is_reparse(area_path), "plugin-io-area-invalid")
    candidate = area_path / filename
    return candidate


def _load_broker_from_environment() -> tuple[Path, dict[str, Any]]:
    raw_path = os.environ.get(BROKER_ENV)
    _require(isinstance(raw_path, str) and raw_path, "plugin-io-broker-environment-required")
    broker_path = Path(raw_path)
    _require(broker_path.is_absolute(), "plugin-io-broker-path-must-be-absolute")
    _require(broker_path.is_file() and not _is_reparse(broker_path), "plugin-io-broker-file-invalid")
    try:
        value = json.loads(broker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PluginIOError("plugin-io-broker-unavailable") from exc
    _require(isinstance(value, dict), "plugin-io-broker-must-be-object")
    _require(set(value) == {"broker_version", "read_handles", "output_handles"}, "plugin-io-broker-shape-invalid")
    _require(value["broker_version"] == BROKER_VERSION, "plugin-io-broker-version-unsupported")
    _require(isinstance(value["read_handles"], dict), "plugin-io-read-map-invalid")
    _require(isinstance(value["output_handles"], dict), "plugin-io-output-map-invalid")
    root = broker_path.parent
    _require(root.is_dir() and not _is_reparse(root), "plugin-io-root-invalid")
    return root, value


def plugin_read_handle(public_handle: dict[str, Any]) -> bytes:
    handle = _exact_keys(public_handle, READ_HANDLE_KEYS, "plugin-read-handle")
    _require(handle["access"] == "read", "plugin-read-handle-access-invalid")
    root, broker = _load_broker_from_environment()
    handle_id = handle["handle_id"]
    _require(isinstance(handle_id, str) and handle_id, "plugin-read-handle-id-required")
    row = broker["read_handles"].get(handle_id)
    _require(isinstance(row, dict), "plugin-read-handle-unknown")
    expected = {"lease_id", "filename", "media_type", "byte_length", "fingerprint", "expires_at"}
    _require(set(row) == expected, "plugin-read-broker-row-invalid")
    for key in ("lease_id", "media_type", "byte_length", "fingerprint", "expires_at"):
        _require(handle[key] == row[key], f"plugin-read-handle-{key}-mismatch")
    _require(_parse_timestamp(row["expires_at"], "plugin-read-expires-at") >= _now(), "plugin-read-handle-expired")
    path = _safe_private_file(root, "inputs", row["filename"])
    _require(path.is_file() and not _is_reparse(path), "plugin-read-input-file-invalid")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise PluginIOError("plugin-read-input-failed") from exc
    _require(len(payload) == row["byte_length"], "plugin-read-input-length-mismatch")
    _require(_sha(payload) == row["fingerprint"], "plugin-read-input-fingerprint-mismatch")
    return payload


def plugin_write_output(public_target: dict[str, Any], payload: bytes) -> dict[str, Any]:
    target = _exact_keys(public_target, OUTPUT_TARGET_KEYS, "plugin-output-target")
    _require(target["access"] == "write-once-output", "plugin-output-target-access-invalid")
    _require(isinstance(payload, bytes), "plugin-output-payload-must-be-bytes")
    root, broker = _load_broker_from_environment()
    handle_id = target["handle_id"]
    _require(isinstance(handle_id, str) and handle_id, "plugin-output-target-id-required")
    row = broker["output_handles"].get(handle_id)
    _require(isinstance(row, dict), "plugin-output-target-unknown")
    expected = {"lease_id", "filename", "media_type", "max_byte_length", "expires_at"}
    _require(set(row) == expected, "plugin-output-broker-row-invalid")
    for key in ("lease_id", "media_type", "max_byte_length", "expires_at"):
        _require(target[key] == row[key], f"plugin-output-target-{key}-mismatch")
    _require(_parse_timestamp(row["expires_at"], "plugin-output-expires-at") >= _now(), "plugin-output-target-expired")
    _require(
        isinstance(row["max_byte_length"], int)
        and not isinstance(row["max_byte_length"], bool)
        and row["max_byte_length"] >= 0,
        "plugin-output-byte-budget-invalid",
    )
    _require(len(payload) <= row["max_byte_length"], "plugin-output-byte-budget-exceeded")
    path = _safe_private_file(root, "outputs", row["filename"])
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    if os.name != "nt":
        flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PluginIOError("plugin-output-create-failed") from exc
    try:
        view = memoryview(payload)
        written = 0
        while written < len(view):
            count = os.write(descriptor, view[written:])
            _require(count > 0, "plugin-output-write-stalled")
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    completed = {
        "handle_id": handle_id,
        "lease_id": row["lease_id"],
        "access": "write-once-output",
        "media_type": row["media_type"],
        "byte_length": len(payload),
        "fingerprint": _sha(payload),
        "expires_at": row["expires_at"],
    }
    _exact_keys(completed, COMPLETED_OUTPUT_KEYS, "plugin-completed-output")
    return completed


class Vs1PluginIO:
    """Core-owned temporary I/O workspace for exactly one plugin session."""

    def __init__(self, *, parent: Path | None = None) -> None:
        if parent is not None:
            _require(parent.is_absolute() and parent.is_dir() and not _is_reparse(parent), "plugin-io-parent-invalid")
        self._temporary = tempfile.TemporaryDirectory(
            prefix="raiatea-vs1c-plugin-io-",
            dir=os.fspath(parent) if parent is not None else None,
        )
        self.root = Path(self._temporary.name).resolve()
        self.inputs = self.root / "inputs"
        self.outputs = self.root / "outputs"
        self.inputs.mkdir()
        self.outputs.mkdir()
        self.broker_path = self.root / "broker.json"
        self._read_rows: dict[str, dict[str, Any]] = {}
        self._output_rows: dict[str, dict[str, Any]] = {}
        self._frozen = False
        self._broker_fingerprint: str | None = None
        self._closed = False

    def _require_open(self) -> None:
        _require(not self._closed, "plugin-io-closed")

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}:{secrets.token_urlsafe(18)}"

    def _expiry(self, ttl_seconds: int) -> str:
        _require(isinstance(ttl_seconds, int) and not isinstance(ttl_seconds, bool) and ttl_seconds > 0, "plugin-io-ttl-invalid")
        return _iso(_now() + timedelta(seconds=ttl_seconds))

    def _write_broker(self) -> bytes:
        value = {
            "broker_version": BROKER_VERSION,
            "read_handles": self._read_rows,
            "output_handles": self._output_rows,
        }
        encoded = _canonical(value)
        temporary = self.root / ".broker.tmp"
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.broker_path)
        return encoded

    def add_input(self, payload: bytes, *, media_type: str, ttl_seconds: int = 300) -> dict[str, Any]:
        self._require_open()
        _require(not self._frozen, "plugin-io-already-frozen")
        _require(isinstance(payload, bytes), "plugin-io-input-must-be-bytes")
        _require(isinstance(media_type, str) and media_type, "plugin-io-input-media-type-required")
        handle_id = self._new_id("plugin-input")
        lease_id = self._new_id("lease")
        filename = hashlib.sha256(handle_id.encode("utf-8")).hexdigest() + ".bin"
        path = _safe_private_file(self.root, "inputs", filename)
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        expiry = self._expiry(ttl_seconds)
        fingerprint = _sha(payload)
        self._read_rows[handle_id] = {
            "lease_id": lease_id,
            "filename": filename,
            "media_type": media_type,
            "byte_length": len(payload),
            "fingerprint": fingerprint,
            "expires_at": expiry,
        }
        return {
            "handle_id": handle_id,
            "lease_id": lease_id,
            "access": "read",
            "media_type": media_type,
            "byte_length": len(payload),
            "fingerprint": fingerprint,
            "expires_at": expiry,
        }

    def issue_output(self, *, media_type: str, max_byte_length: int, ttl_seconds: int = 300) -> dict[str, Any]:
        self._require_open()
        _require(not self._frozen, "plugin-io-already-frozen")
        _require(isinstance(media_type, str) and media_type, "plugin-io-output-media-type-required")
        _require(
            isinstance(max_byte_length, int)
            and not isinstance(max_byte_length, bool)
            and max_byte_length >= 0,
            "plugin-io-output-byte-budget-invalid",
        )
        handle_id = self._new_id("plugin-output")
        lease_id = self._new_id("lease")
        filename = hashlib.sha256(handle_id.encode("utf-8")).hexdigest() + ".bin"
        expiry = self._expiry(ttl_seconds)
        self._output_rows[handle_id] = {
            "lease_id": lease_id,
            "filename": filename,
            "media_type": media_type,
            "max_byte_length": max_byte_length,
            "expires_at": expiry,
        }
        return {
            "handle_id": handle_id,
            "lease_id": lease_id,
            "access": "write-once-output",
            "media_type": media_type,
            "max_byte_length": max_byte_length,
            "expires_at": expiry,
        }

    def freeze(self) -> dict[str, str]:
        self._require_open()
        if not self._frozen:
            encoded = self._write_broker()
            self._broker_fingerprint = _sha(encoded)
            try:
                self.broker_path.chmod(0o400)
            except OSError:
                pass
            self._frozen = True
        return {BROKER_ENV: os.fspath(self.broker_path)}

    def verify_broker_unchanged(self) -> None:
        self._require_open()
        _require(self._frozen and self._broker_fingerprint is not None, "plugin-io-not-frozen")
        try:
            payload = self.broker_path.read_bytes()
        except OSError as exc:
            raise PluginIOError("plugin-io-broker-postrun-unavailable") from exc
        _require(_sha(payload) == self._broker_fingerprint, "plugin-io-broker-mutated")

    def read_completed_output(
        self,
        target: dict[str, Any],
        completed: dict[str, Any],
    ) -> bytes:
        self._require_open()
        _exact_keys(target, OUTPUT_TARGET_KEYS, "core-output-target")
        result = _exact_keys(completed, COMPLETED_OUTPUT_KEYS, "core-completed-output")
        handle_id = target["handle_id"]
        _require(result["handle_id"] == handle_id, "core-completed-output-handle-mismatch")
        row = self._output_rows.get(handle_id)
        _require(isinstance(row, dict), "core-output-target-unknown")
        for key in ("lease_id", "media_type", "expires_at"):
            _require(result[key] == target[key] == row[key], f"core-completed-output-{key}-mismatch")
        _require(target["max_byte_length"] == row["max_byte_length"], "core-output-target-budget-mismatch")
        _require(
            isinstance(result["byte_length"], int)
            and not isinstance(result["byte_length"], bool)
            and 0 <= result["byte_length"] <= row["max_byte_length"],
            "core-completed-output-length-invalid",
        )
        _require(_valid_sha(result["fingerprint"]), "core-completed-output-fingerprint-invalid")
        path = _safe_private_file(self.root, "outputs", row["filename"])
        _require(path.is_file() and not _is_reparse(path), "core-completed-output-file-invalid")
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise PluginIOError("core-completed-output-read-failed") from exc
        _require(len(payload) == result["byte_length"], "core-completed-output-length-mismatch")
        _require(_sha(payload) == result["fingerprint"], "core-completed-output-fingerprint-mismatch")
        return payload

    def close(self) -> None:
        if self._closed:
            return
        self._temporary.cleanup()
        self._closed = True

    def __enter__(self) -> "Vs1PluginIO":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
