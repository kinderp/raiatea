from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
CONTRACTS = ROOT / "contracts"
sys.path.insert(0, str(BUILD))

import evaluator_session_batch_manifest as batch  # noqa: E402


class EvaluatorSessionBatchManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_path = CONTRACTS / "evaluator-session-batch-manifest-v1.json"
        cls.fixture = json.loads(cls.fixture_path.read_text(encoding="utf-8"))

    def test_canonical_fixture_is_valid(self) -> None:
        self.assertEqual([], batch.validate_manifest(self.fixture))
        loaded = batch.load_manifest(self.fixture_path)
        self.assertEqual(self.fixture, loaded)

    def test_closed_fields_and_supported_versions(self) -> None:
        value = copy.deepcopy(self.fixture)
        value["extra"] = True
        self.assertTrue(any("unsupported field" in issue for issue in batch.validate_manifest(value)))
        value = copy.deepcopy(self.fixture)
        value["version"] = 2
        self.assertTrue(any("unsupported version" in issue for issue in batch.validate_manifest(value)))
        value = copy.deepcopy(self.fixture)
        value["records"][0]["recordVersion"] = 2
        self.assertTrue(any("record version" in issue for issue in batch.validate_manifest(value)))

    def test_paths_are_canonical_relative_json_paths(self) -> None:
        samples = ("/absolute.json", "..\\escape.json", "a/../b.json", "./record.json", "record.txt")
        for sample in samples:
            with self.subTest(sample=sample):
                value = copy.deepcopy(self.fixture)
                value["records"][0]["path"] = sample
                self.assertTrue(batch.validate_manifest(value))

    def test_digests_are_lowercase_sha256(self) -> None:
        for digest in ("a" * 63, "A" * 64, "g" * 64, 123):
            with self.subTest(digest=digest):
                value = copy.deepcopy(self.fixture)
                value["records"][0]["sha256"] = digest
                self.assertTrue(any("sha256" in issue for issue in batch.validate_manifest(value)))

    def test_order_and_duplicates_fail_closed(self) -> None:
        value = copy.deepcopy(self.fixture)
        value["records"].reverse()
        self.assertTrue(any("sorted" in issue for issue in batch.validate_manifest(value)))
        value = copy.deepcopy(self.fixture)
        value["records"][1]["path"] = value["records"][0]["path"]
        self.assertTrue(any("duplicate paths" in issue for issue in batch.validate_manifest(value)))
        value = copy.deepcopy(self.fixture)
        value["records"][1]["sha256"] = value["records"][0]["sha256"]
        self.assertTrue(any("duplicate digests" in issue for issue in batch.validate_manifest(value)))

    def test_builder_is_deterministic_and_does_not_read_records(self) -> None:
        entries = (("sessions/a.json", "a" * 64), ("sessions/b.json", "b" * 64))
        first = batch.build_manifest(entries)
        second = batch.build_manifest(entries)
        self.assertEqual(first, second)
        self.assertEqual(["sessions/a.json", "sessions/b.json"], [entry["path"] for entry in first["records"]])

    def test_cli_accepts_fixture_and_rejects_invalid_manifest(self) -> None:
        command = [sys.executable, str(BUILD / "evaluator_session_batch_manifest.py")]
        valid = subprocess.run(command + [str(self.fixture_path)], capture_output=True, text=True, check=False)
        self.assertEqual(0, valid.returncode, valid.stderr)
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "invalid.json"
            invalid.write_text("{}", encoding="utf-8")
            result = subprocess.run(command + [str(invalid)], capture_output=True, text=True, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("validation failed", result.stdout.casefold())


if __name__ == "__main__":
    unittest.main()
