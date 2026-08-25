#!/usr/bin/env python3
"""VS1a Core-owned filesystem authority and opaque AssetHandle broker.

This module consumes the accepted Plugin Runtime v1b handle semantics. It does
not define a second public Plugin API contract and never exposes host paths in
public handle records.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import ctypes
import hashlib
import os
from pathlib import Path
import secrets
import stat
from typing import Callable, Iterable


class CoreAccessError(ValueError):
    pass


_ALLOWED_SCOPE_CAPABILITIES = frozenset({"observe", "read-for-processing"})
_MUTATION_CAPABILITIES = frozenset({"write", "move", "delete", "organize"})
_READ_HANDLE_KEYS = frozenset(
    {"handle_id", "lease_id", "access", "media_type", "byte_length", "fingerprint", "expires_at"}
)
_OUTPUT_TARGET_KEYS = frozenset(
    {"handle_id", "lease_id", "access", "media_type", "max_byte_length", "expires_at"}
)
_COMPLETED_OUTPUT_KEYS = frozenset(
    {"handle_id", "lease_id", "access", "media_type", "byte_length", "fingerprint", "expires_at"}
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CoreAccessError(message)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(value: datetime) -> str:
    _require(value.tzinfo is not None and value.utcoffset() is not None, "timestamp-timezone-required")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: object, label: str) -> datetime:
    _require(isinstance(value, str) and value, f"{label}-required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CoreAccessError(f"{label}-invalid") from exc
    _require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{label}-timezone-required")
    return parsed.astimezone(timezone.utc)


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _is_symlink_or_reparse(path: Path) -> bool:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = int(getattr(info, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return bool(attributes & reparse_flag)


def _assert_no_reparse_components(path: Path, label: str) -> Path:
    _require(path.is_absolute(), f"{label}-must-be-absolute")
    absolute = path.absolute()
    parts = absolute.parts
    _require(bool(parts), f"{label}-invalid")
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        try:
            _require(not _is_symlink_or_reparse(current), f"{label}-symlink-or-reparse-forbidden")
        except FileNotFoundError as exc:
            raise CoreAccessError(f"{label}-missing") from exc
    return absolute.resolve(strict=True)


def _relative_parts(value: object) -> tuple[str, ...]:
    _require(isinstance(value, str) and value, "asset-relative-path-required")
    _require("\x00" not in value, "asset-relative-path-nul-forbidden")
    _require("\\" not in value, "asset-relative-path-backslash-forbidden")
    _require(":" not in value, "asset-relative-path-colon-forbidden")
    _require(not value.startswith("/"), "asset-relative-path-must-not-be-absolute")
    parts = value.split("/")
    _require(all(part not in {"", ".", ".."} for part in parts), "asset-relative-path-component-forbidden")
    return tuple(parts)


def _require_exact_public_keys(
    value: dict[str, object], expected: frozenset[str], label: str
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")


@dataclass(frozen=True)
class _ScopeState:
    scope_id: str
    root: Path
    canonical_root: str
    capabilities: tuple[str, ...]
    posix_root_fd: int | None


class ScopeRegistry:
    """Core-only authority registry.

    External callers can reference an existing scope id through higher-level
    operations, but this object is the only VS1a surface that binds a root path.
    """

    def __init__(self) -> None:
        self._scopes: dict[str, _ScopeState] = {}
        self._closed = False

    def register_scope(
        self,
        scope_id: str,
        root: Path,
        capabilities: Iterable[str] = ("observe", "read-for-processing"),
    ) -> None:
        _require(not self._closed, "scope-registry-closed")
        _require(isinstance(scope_id, str) and scope_id, "scope-id-required")
        _require(scope_id not in self._scopes, "scope-id-already-registered")
        _require(isinstance(root, Path) and root.is_absolute(), "scope-root-must-be-absolute")
        canonical = _assert_no_reparse_components(root, "scope-root")
        _require(canonical.is_dir(), "scope-root-must-be-directory")

        normalized = tuple(sorted(set(capabilities)))
        _require(bool(normalized), "scope-capability-required")
        unsupported = sorted(set(normalized) - _ALLOWED_SCOPE_CAPABILITIES)
        _require(not unsupported, f"scope-capability-forbidden:{unsupported[0] if unsupported else ''}")

        root_fd: int | None = None
        if os.name != "nt":
            _require(hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"), "platform-nofollow-directory-required")
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            try:
                root_fd = os.open(canonical, flags)
            except OSError as exc:
                raise CoreAccessError("scope-root-open-failed") from exc

        self._scopes[scope_id] = _ScopeState(
            scope_id=scope_id,
            root=canonical,
            canonical_root=str(canonical),
            capabilities=normalized,
            posix_root_fd=root_fd,
        )

    def public_scope(self, scope_id: str) -> dict[str, object]:
        scope = self._get(scope_id)
        return {"scope_id": scope.scope_id, "capabilities": list(scope.capabilities)}

    def _get(self, scope_id: str) -> _ScopeState:
        _require(not self._closed, "scope-registry-closed")
        scope = self._scopes.get(scope_id)
        _require(scope is not None, "unknown-scope-id")
        return scope

    def require_capability(self, scope_id: str, capability: str) -> _ScopeState:
        _require(capability not in _MUTATION_CAPABILITIES, "scope-mutation-capability-forbidden")
        scope = self._get(scope_id)
        _require(capability in scope.capabilities, "scope-capability-not-granted")
        return scope

    def close(self) -> None:
        if self._closed:
            return
        for scope in self._scopes.values():
            if scope.posix_root_fd is not None:
                os.close(scope.posix_root_fd)
        self._closed = True

    def __enter__(self) -> "ScopeRegistry":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


@dataclass(frozen=True)
class _ReadLease:
    scope_id: str
    relative_parts: tuple[str, ...]
    handle_id: str
    lease_id: str
    media_type: str
    byte_length: int
    fingerprint: str
    expires_at: datetime


@dataclass
class _OutputLease:
    handle_id: str
    lease_id: str
    media_type: str
    max_byte_length: int
    expires_at: datetime
    filename: str
    completed: bool = False
    completed_byte_length: int | None = None
    completed_fingerprint: str | None = None


def _read_posix(scope: _ScopeState, parts: tuple[str, ...]) -> bytes:
    _require(scope.posix_root_fd is not None, "posix-root-fd-required")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    current_fd = os.dup(scope.posix_root_fd)
    file_fd: int | None = None
    try:
        for component in parts[:-1]:
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | nofollow | cloexec,
                    dir_fd=current_fd,
                )
            except OSError as exc:
                raise CoreAccessError("asset-path-component-open-failed") from exc
            os.close(current_fd)
            current_fd = next_fd
        try:
            file_fd = os.open(parts[-1], os.O_RDONLY | nofollow | cloexec, dir_fd=current_fd)
        except OSError as exc:
            raise CoreAccessError("asset-file-open-failed") from exc
        info = os.fstat(file_fd)
        _require(stat.S_ISREG(info.st_mode), "asset-must-be-regular-file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 64 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(current_fd)


def _strip_windows_device_prefix(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def _windows_handle_final_path(handle: object) -> str:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = kernel32.GetFinalPathNameByHandleW
    function.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    function.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    length = function(handle, buffer, len(buffer), 0)
    if length == 0 or length >= len(buffer):
        raise CoreAccessError("windows-final-path-unavailable")
    return _strip_windows_device_prefix(buffer.value)


def _windows_handle_attributes(handle: object) -> int:
    from ctypes import wintypes

    class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
        _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = kernel32.GetFileInformationByHandleEx
    function.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    function.restype = wintypes.BOOL
    info = FILE_ATTRIBUTE_TAG_INFO()
    if not function(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
        raise CoreAccessError("windows-file-attributes-unavailable")
    return int(info.FileAttributes)


def _windows_path_inside(root: str, candidate: str) -> bool:
    root_norm = os.path.normcase(os.path.normpath(root))
    candidate_norm = os.path.normcase(os.path.normpath(candidate))
    try:
        return os.path.commonpath([root_norm, candidate_norm]) == root_norm
    except ValueError:
        return False


def _read_windows(scope: _ScopeState, parts: tuple[str, ...]) -> bytes:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    read_file = kernel32.ReadFile
    read_file.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    read_file.restype = wintypes.BOOL

    candidate = scope.root.joinpath(*parts)
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    invalid = ctypes.c_void_p(-1).value

    handle = create_file(
        str(candidate),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if handle == invalid:
        raise CoreAccessError("asset-file-open-failed")
    try:
        attributes = _windows_handle_attributes(handle)
        _require(not (attributes & FILE_ATTRIBUTE_REPARSE_POINT), "asset-symlink-or-reparse-forbidden")
        _require(not (attributes & FILE_ATTRIBUTE_DIRECTORY), "asset-must-be-regular-file")
        final_path = _windows_handle_final_path(handle)
        _require(_windows_path_inside(scope.canonical_root, final_path), "asset-scope-escape")

        chunks: list[bytes] = []
        while True:
            buffer = ctypes.create_string_buffer(64 * 1024)
            read = wintypes.DWORD()
            if not read_file(handle, buffer, len(buffer), ctypes.byref(read), None):
                raise CoreAccessError("asset-file-read-failed")
            if read.value == 0:
                break
            chunks.append(buffer.raw[: read.value])
        return b"".join(chunks)
    finally:
        close_handle(handle)


def _safe_read(scope: _ScopeState, parts: tuple[str, ...]) -> bytes:
    return _read_windows(scope, parts) if os.name == "nt" else _read_posix(scope, parts)


class AssetBroker:
    def __init__(
        self,
        scopes: ScopeRegistry,
        output_root: Path,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        _require(isinstance(output_root, Path) and output_root.is_absolute(), "output-root-must-be-absolute")
        canonical = _assert_no_reparse_components(output_root, "output-root")
        _require(canonical.is_dir(), "output-root-must-be-directory")
        self._scopes = scopes
        self._output_root = canonical
        self._clock = clock
        self._reads: dict[str, _ReadLease] = {}
        self._outputs: dict[str, _OutputLease] = {}
        self._output_root_fd: int | None = None
        if os.name != "nt":
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            try:
                self._output_root_fd = os.open(canonical, flags)
            except OSError as exc:
                raise CoreAccessError("output-root-open-failed") from exc

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}:{secrets.token_urlsafe(18)}"

    def _expiry(self, ttl_seconds: int) -> datetime:
        _require(isinstance(ttl_seconds, int) and ttl_seconds > 0, "lease-ttl-invalid")
        now = self._clock()
        _require(now.tzinfo is not None and now.utcoffset() is not None, "clock-timezone-required")
        return now.astimezone(timezone.utc) + timedelta(seconds=ttl_seconds)

    def issue_read_handle(
        self,
        scope_id: str,
        relative_path: str,
        *,
        media_type: str,
        ttl_seconds: int = 300,
    ) -> dict[str, object]:
        _require(isinstance(media_type, str) and media_type, "media-type-required")
        scope = self._scopes.require_capability(scope_id, "read-for-processing")
        parts = _relative_parts(relative_path)
        payload = _safe_read(scope, parts)
        handle_id = self._new_id("asset")
        lease_id = self._new_id("lease")
        expiry = self._expiry(ttl_seconds)
        lease = _ReadLease(
            scope_id=scope_id,
            relative_parts=parts,
            handle_id=handle_id,
            lease_id=lease_id,
            media_type=media_type,
            byte_length=len(payload),
            fingerprint=_sha256(payload),
            expires_at=expiry,
        )
        self._reads[handle_id] = lease
        public: dict[str, object] = {
            "handle_id": handle_id,
            "lease_id": lease_id,
            "access": "read",
            "media_type": media_type,
            "byte_length": lease.byte_length,
            "fingerprint": lease.fingerprint,
            "expires_at": _iso_utc(expiry),
        }
        _require_exact_public_keys(public, _READ_HANDLE_KEYS, "read-handle")
        return public

    def read_asset(self, public_handle: dict[str, object]) -> bytes:
        _require(isinstance(public_handle, dict), "read-handle-required")
        _require_exact_public_keys(public_handle, _READ_HANDLE_KEYS, "read-handle")
        handle_id = public_handle.get("handle_id")
        _require(isinstance(handle_id, str) and handle_id, "read-handle-id-required")
        lease = self._reads.get(handle_id)
        _require(lease is not None, "read-handle-unknown")
        _require(public_handle.get("lease_id") == lease.lease_id, "read-handle-lease-mismatch")
        _require(public_handle.get("access") == "read", "read-handle-access-required")
        _require(public_handle.get("media_type") == lease.media_type, "read-handle-media-type-mismatch")
        _require(public_handle.get("byte_length") == lease.byte_length, "read-handle-byte-length-mismatch")
        _require(public_handle.get("fingerprint") == lease.fingerprint, "read-handle-fingerprint-mismatch")
        _require(
            _parse_timestamp(public_handle.get("expires_at"), "read-handle-expires-at") == lease.expires_at,
            "read-handle-expiry-mismatch",
        )
        _require(self._clock().astimezone(timezone.utc) <= lease.expires_at, "read-handle-expired")

        scope = self._scopes.require_capability(lease.scope_id, "read-for-processing")
        payload = _safe_read(scope, lease.relative_parts)
        _require(len(payload) == lease.byte_length, "asset-content-changed")
        _require(_sha256(payload) == lease.fingerprint, "asset-content-changed")
        return payload

    def issue_output_target(
        self,
        *,
        media_type: str,
        max_byte_length: int,
        ttl_seconds: int = 300,
    ) -> dict[str, object]:
        _require(isinstance(media_type, str) and media_type, "media-type-required")
        _require(isinstance(max_byte_length, int) and max_byte_length >= 0, "output-max-byte-length-invalid")
        handle_id = self._new_id("output")
        lease_id = self._new_id("lease")
        expiry = self._expiry(ttl_seconds)
        filename = hashlib.sha256(handle_id.encode("utf-8")).hexdigest() + ".bin"
        self._outputs[handle_id] = _OutputLease(
            handle_id=handle_id,
            lease_id=lease_id,
            media_type=media_type,
            max_byte_length=max_byte_length,
            expires_at=expiry,
            filename=filename,
        )
        public: dict[str, object] = {
            "handle_id": handle_id,
            "lease_id": lease_id,
            "access": "write-once-output",
            "media_type": media_type,
            "max_byte_length": max_byte_length,
            "expires_at": _iso_utc(expiry),
        }
        _require_exact_public_keys(public, _OUTPUT_TARGET_KEYS, "output-target")
        return public

    def _write_output_bytes(self, filename: str, payload: bytes) -> None:
        if os.name != "nt":
            _require(self._output_root_fd is not None, "output-root-fd-required")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            try:
                descriptor = os.open(filename, flags, 0o600, dir_fd=self._output_root_fd)
            except OSError as exc:
                raise CoreAccessError("output-create-failed") from exc
            try:
                view = memoryview(payload)
                offset = 0
                while offset < len(view):
                    offset += os.write(descriptor, view[offset:])
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            return

        candidate = self._output_root / filename
        try:
            descriptor = os.open(
                candidate,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                0o600,
            )
        except OSError as exc:
            raise CoreAccessError("output-create-failed") from exc
        try:
            final = candidate.resolve(strict=True)
            _require(_windows_path_inside(str(self._output_root), str(final)), "output-scope-escape")
            _require(not _is_symlink_or_reparse(final), "output-symlink-or-reparse-forbidden")
            view = memoryview(payload)
            offset = 0
            while offset < len(view):
                offset += os.write(descriptor, view[offset:])
            os.fsync(descriptor)
        except Exception:
            try:
                os.close(descriptor)
            finally:
                try:
                    candidate.unlink()
                except OSError:
                    pass
            raise
        else:
            os.close(descriptor)

    def write_output(self, public_target: dict[str, object], payload: bytes) -> dict[str, object]:
        _require(isinstance(public_target, dict), "output-target-required")
        _require_exact_public_keys(public_target, _OUTPUT_TARGET_KEYS, "output-target")
        _require(isinstance(payload, bytes), "output-payload-must-be-bytes")
        handle_id = public_target.get("handle_id")
        _require(isinstance(handle_id, str) and handle_id, "output-target-id-required")
        lease = self._outputs.get(handle_id)
        _require(lease is not None, "output-target-unknown")
        _require(not lease.completed, "output-target-already-written")
        _require(public_target.get("lease_id") == lease.lease_id, "output-target-lease-mismatch")
        _require(public_target.get("access") == "write-once-output", "output-target-access-required")
        _require(public_target.get("media_type") == lease.media_type, "output-target-media-type-mismatch")
        _require(public_target.get("max_byte_length") == lease.max_byte_length, "output-target-byte-budget-mismatch")
        _require(
            _parse_timestamp(public_target.get("expires_at"), "output-target-expires-at") == lease.expires_at,
            "output-target-expiry-mismatch",
        )
        _require(self._clock().astimezone(timezone.utc) <= lease.expires_at, "output-target-expired")
        _require(len(payload) <= lease.max_byte_length, "output-exceeds-core-byte-budget")

        self._write_output_bytes(lease.filename, payload)
        lease.completed = True
        lease.completed_byte_length = len(payload)
        lease.completed_fingerprint = _sha256(payload)
        completed: dict[str, object] = {
            "handle_id": lease.handle_id,
            "lease_id": lease.lease_id,
            "access": "write-once-output",
            "media_type": lease.media_type,
            "byte_length": lease.completed_byte_length,
            "fingerprint": lease.completed_fingerprint,
            "expires_at": _iso_utc(lease.expires_at),
        }
        _require_exact_public_keys(completed, _COMPLETED_OUTPUT_KEYS, "completed-output")
        return completed

    def _safe_read_output(self, lease: _OutputLease) -> bytes:
        output_scope = _ScopeState(
            scope_id="__core-output__",
            root=self._output_root,
            canonical_root=str(self._output_root),
            capabilities=(),
            posix_root_fd=self._output_root_fd,
        )
        return _safe_read(output_scope, (lease.filename,))

    def read_completed_output(self, handle_id: str, lease_id: str) -> bytes:
        lease = self._outputs.get(handle_id)
        _require(lease is not None and lease.completed, "completed-output-unknown")
        _require(lease.lease_id == lease_id, "completed-output-lease-mismatch")
        _require(lease.completed_byte_length is not None, "completed-output-byte-length-missing")
        _require(lease.completed_fingerprint is not None, "completed-output-fingerprint-missing")
        payload = self._safe_read_output(lease)
        _require(len(payload) == lease.completed_byte_length, "completed-output-content-changed")
        _require(_sha256(payload) == lease.completed_fingerprint, "completed-output-content-changed")
        return payload

    def close(self) -> None:
        if self._output_root_fd is not None:
            os.close(self._output_root_fd)
            self._output_root_fd = None

    def __enter__(self) -> "AssetBroker":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
