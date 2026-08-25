#!/usr/bin/env python3
"""VS1a internal catalog-state persistence boundary.

The payload is intentionally opaque to this module. Later VS1 increments own the
domain records. Only the internal storage envelope, revision and integrity rules
are defined here.

VS1a has one Core process and one CatalogStateStore owner. The expected-revision
check is an optimistic guard inside that owner; it is not advertised as a
cross-process compare-and-swap primitive. A process-wide/multi-host catalog
writer protocol is deliberately outside VS1a.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
from typing import Any


STORE_VERSION = "raiatea.vs1.catalog-internal.0.1.0"


class CatalogStoreError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CatalogStoreError(message)


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CatalogStoreError("catalog-payload-not-json-safe") from exc


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _is_symlink_or_reparse(path: Path) -> bool:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = int(getattr(info, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return bool(attributes & reparse_flag)


def _assert_parent_safe(path: Path) -> None:
    _require(path.is_absolute(), "catalog-path-must-be-absolute")
    parent = path.parent
    _require(parent.is_dir(), "catalog-parent-must-exist")
    parts = parent.absolute().parts
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        _require(not _is_symlink_or_reparse(current), "catalog-parent-symlink-or-reparse-forbidden")


def _assert_target_not_reparse(path: Path) -> None:
    try:
        if os.path.lexists(os.fspath(path)):
            _require(not _is_symlink_or_reparse(path), "catalog-target-symlink-or-reparse-forbidden")
    except FileNotFoundError:
        return


@dataclass(frozen=True)
class CatalogSnapshot:
    revision: int
    payload: dict[str, Any]


class CatalogStateStore:
    """One-file internal state store owned by one VS1 Core process."""

    def __init__(self, path: Path) -> None:
        _require(isinstance(path, Path) and path.is_absolute(), "catalog-path-must-be-absolute")
        _assert_parent_safe(path)
        _assert_target_not_reparse(path)
        self._path = path
        self._lock = threading.RLock()

    @property
    def path(self) -> Path:
        return self._path

    def _decode(self, raw: bytes) -> CatalogSnapshot:
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CatalogStoreError("catalog-envelope-invalid-json") from exc
        _require(isinstance(value, dict), "catalog-envelope-must-be-object")
        expected = {"store_version", "revision", "payload_sha256", "payload"}
        actual = set(value)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        _require(not missing, f"catalog-envelope-missing-field:{missing[0] if missing else ''}")
        _require(not extra, f"catalog-envelope-unknown-field:{extra[0] if extra else ''}")
        _require(value["store_version"] == STORE_VERSION, "catalog-store-version-unsupported")
        revision = value["revision"]
        _require(isinstance(revision, int) and not isinstance(revision, bool) and revision >= 1, "catalog-revision-invalid")
        payload = value["payload"]
        _require(isinstance(payload, dict), "catalog-payload-must-be-object")
        payload_bytes = _canonical_json(payload)
        _require(value["payload_sha256"] == _sha256(payload_bytes), "catalog-payload-integrity-mismatch")
        canonical = _canonical_json(
            {
                "store_version": STORE_VERSION,
                "revision": revision,
                "payload_sha256": _sha256(payload_bytes),
                "payload": payload,
            }
        )
        _require(raw == canonical, "catalog-envelope-not-canonical")
        return CatalogSnapshot(revision=revision, payload=payload)

    def _load_unlocked(self) -> CatalogSnapshot | None:
        _assert_parent_safe(self._path)
        _assert_target_not_reparse(self._path)
        if not os.path.lexists(os.fspath(self._path)):
            return None
        try:
            raw = self._path.read_bytes()
        except OSError as exc:
            raise CatalogStoreError("catalog-read-failed") from exc
        return self._decode(raw)

    def load(self) -> CatalogSnapshot | None:
        with self._lock:
            return self._load_unlocked()

    def save(self, payload: dict[str, Any], *, expected_revision: int) -> CatalogSnapshot:
        _require(isinstance(payload, dict), "catalog-payload-must-be-object")
        _require(
            isinstance(expected_revision, int)
            and not isinstance(expected_revision, bool)
            and expected_revision >= 0,
            "catalog-expected-revision-invalid",
        )
        with self._lock:
            current = self._load_unlocked()
            current_revision = 0 if current is None else current.revision
            _require(current_revision == expected_revision, "catalog-stale-expected-revision")

            new_revision = current_revision + 1
            payload_bytes = _canonical_json(payload)
            envelope = {
                "store_version": STORE_VERSION,
                "revision": new_revision,
                "payload_sha256": _sha256(payload_bytes),
                "payload": payload,
            }
            encoded = _canonical_json(envelope)

            _assert_parent_safe(self._path)
            _assert_target_not_reparse(self._path)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                dir=self._path.parent,
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb", closefd=True) as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
                _assert_target_not_reparse(self._path)
                os.replace(temporary, self._path)
                if os.name != "nt":
                    parent_fd = os.open(self._path.parent, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(parent_fd)
                    finally:
                        os.close(parent_fd)
            except Exception:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
                raise

            loaded = self._load_unlocked()
            _require(
                loaded is not None and loaded.revision == new_revision,
                "catalog-post-write-verification-failed",
            )
            _require(loaded.payload == payload, "catalog-post-write-payload-mismatch")
            return loaded
