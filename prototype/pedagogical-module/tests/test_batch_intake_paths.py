from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
sys.path.insert(0, str(BUILD))

import evaluator_session_batch_intake as intake  # noqa: E402
import evaluator_session_batch_manifest as batch  # noqa: E402
import evaluator_session_record as record  # noqa: E402


def valid_payload() -> bytes:
    value = {
        "format": record.FORMAT,
        "version": record.VERSION,
        "releaseVersion": "field-pilot-v1",
        "platform": "linux",
        "launcher": "posix",
        "results": {key: False for key in record.RESULT_KEYS},
        "observations": "Clear navigation.",
        "declaration": record.DECLARATION,
    }
    return (json.dumps(value, indent=2) + "\n").encode()


class BatchIntakePathTests(unittest.TestCase):
    def manifest(self, root: Path, relative: str, payload: bytes) -> Path:
        value = batch.build_manifest([(relative, hashlib.sha256(payload).hexdigest())])
        path = root / "batch.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_missing_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = valid_payload()
            manifest = self.manifest(root, "sessions/missing.json", payload)
            with self.assertRaisesRegex(ValueError, "missing or not a regular file"):
                intake.validate_batch_intake(manifest, root)

    def test_symlink_fails_closed_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = valid_payload()
            target = root / "target.json"
            target.write_bytes(payload)
            link = root / "sessions/link.json"
            link.parent.mkdir(parents=True)
            try:
                os.symlink(target, link)
            except OSError:
                self.skipTest("symlinks unavailable")
            manifest = self.manifest(root, "sessions/link.json", payload)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                intake.validate_batch_intake(manifest, root)

    def test_snapshot_is_frozen(self) -> None:
        snapshot = intake.RecordSnapshot(path="sessions/a.json", sha256="0" * 64, value={})
        with self.assertRaises(Exception):
            snapshot.path = "sessions/b.json"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
