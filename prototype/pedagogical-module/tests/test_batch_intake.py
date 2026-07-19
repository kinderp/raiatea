from __future__ import annotations

import hashlib
import json
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


class BatchIntakeTests(unittest.TestCase):
    def make_record(self, path: Path, text: str) -> bytes:
        value = {
            "format": record.FORMAT,
            "version": record.VERSION,
            "releaseVersion": "field-pilot-v1",
            "platform": "linux",
            "launcher": "posix",
            "results": {key: False for key in record.RESULT_KEYS},
            "observations": text,
            "declaration": record.DECLARATION,
        }
        payload = (json.dumps(value, indent=2) + "\n").encode()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return payload

    def make_manifest(self, root: Path, entries: list[tuple[str, bytes]]) -> Path:
        value = batch.build_manifest((name, hashlib.sha256(data).hexdigest()) for name, data in entries)
        path = root / "batch.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_success_and_input_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            one = self.make_record(root / "sessions/a.json", "Clear navigation.")
            two = self.make_record(root / "sessions/b.json", "Useful remediation.")
            manifest = self.make_manifest(root, [("sessions/a.json", one), ("sessions/b.json", two)])
            before = one, two, manifest.read_bytes()
            snapshots = intake.validate_batch_intake(manifest, root)
            self.assertEqual(("sessions/a.json", "sessions/b.json"), tuple(item.path for item in snapshots))
            self.assertEqual(before, ((root / "sessions/a.json").read_bytes(), (root / "sessions/b.json").read_bytes(), manifest.read_bytes()))

    def test_digest_and_record_validation_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = self.make_record(root / "sessions/a.json", "Clear navigation.")
            manifest = self.make_manifest(root, [("sessions/a.json", data)])
            (root / "sessions/a.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                intake.validate_batch_intake(manifest, root)
            broken = b"{bad json"
            (root / "sessions/a.json").write_bytes(broken)
            manifest = self.make_manifest(root, [("sessions/a.json", broken)])
            with self.assertRaisesRegex(ValueError, "unreadable JSON"):
                intake.validate_batch_intake(manifest, root)

    def test_duplicate_semantic_values_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.make_record(root / "sessions/a.json", "Clear navigation.")
            value = json.loads(first)
            second = (json.dumps(value, separators=(",", ":")) + "\n").encode()
            (root / "sessions/b.json").write_bytes(second)
            manifest = self.make_manifest(root, [("sessions/a.json", first), ("sessions/b.json", second)])
            with self.assertRaisesRegex(ValueError, "duplicate record value"):
                intake.validate_batch_intake(manifest, root)


if __name__ == "__main__":
    unittest.main()
