from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
sys.path.insert(0, str(BUILD))

import evaluator_session_aggregate as aggregate  # noqa: E402
import evaluator_session_batch_intake as intake  # noqa: E402
import evaluator_session_batch_manifest as batch  # noqa: E402
import evaluator_session_record as record  # noqa: E402


class EvaluatorSessionAggregateTests(unittest.TestCase):
    def snapshot(self, digest: str, platform: str, launcher: str, truth: bool) -> intake.RecordSnapshot:
        value = {
            "format": record.FORMAT,
            "version": record.VERSION,
            "releaseVersion": "field-pilot-v1",
            "platform": platform,
            "launcher": launcher,
            "results": {key: truth for key in record.RESULT_KEYS},
            "observations": "",
            "declaration": record.DECLARATION,
        }
        return intake.RecordSnapshot(path=f"sessions/{digest[0]}.json", sha256=digest, value=value)

    def test_deterministic_counts_and_provenance(self) -> None:
        one = self.snapshot("1" * 64, "linux", "posix", True)
        two = self.snapshot("2" * 64, "windows", "powershell", False)
        value = aggregate.build_aggregate((two, one), {one.sha256: ["navigation"], two.sha256: ["stability"]})
        self.assertEqual([one.sha256, two.sha256], value["inputSha256"])
        self.assertEqual(2, value["recordCount"])
        self.assertEqual(1, value["platformCounts"]["linux"])
        self.assertEqual(1, value["platformCounts"]["windows"])
        self.assertEqual({"false": 1, "true": 1}, value["resultCounts"][record.RESULT_KEYS[0]])
        self.assertEqual(1, value["themeCounts"]["navigation"])
        self.assertEqual([], aggregate.validate_aggregate(value))
        self.assertEqual(value, aggregate.build_aggregate((one, two), {two.sha256: ["stability"], one.sha256: ["navigation"]}))

    def test_theme_assignments_are_closed_sorted_and_known(self) -> None:
        item = self.snapshot("1" * 64, "linux", "posix", True)
        for themes, message in (
            ({item.sha256: ["unknown"]}, "unsupported theme"),
            ({item.sha256: ["navigation", "navigation"]}, "sorted and unique"),
            ({"2" * 64: ["navigation"]}, "unknown digest"),
        ):
            with self.subTest(themes=themes):
                with self.assertRaisesRegex(ValueError, message):
                    aggregate.build_aggregate((item,), themes)

    def test_schema_is_closed_and_result_counts_must_sum(self) -> None:
        item = self.snapshot("1" * 64, "linux", "posix", True)
        value = aggregate.build_aggregate((item,))
        value["extra"] = True
        self.assertTrue(any("unsupported field" in issue for issue in aggregate.validate_aggregate(value)))
        value = aggregate.build_aggregate((item,))
        value["resultCounts"][record.RESULT_KEYS[0]]["true"] = 2
        self.assertTrue(any("sum to recordCount" in issue for issue in aggregate.validate_aggregate(value)))

    def test_write_is_no_replace(self) -> None:
        item = self.snapshot("1" * 64, "linux", "posix", True)
        value = aggregate.build_aggregate((item,))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "summary.json"
            aggregate.write_aggregate(path, value)
            original = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "already exists"):
                aggregate.write_aggregate(path, value)
            self.assertEqual(original, path.read_bytes())

    def test_cli_end_to_end_preserves_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sessions = root / "sessions"
            sessions.mkdir()
            record_path = sessions / "a.json"
            record.create_record(record_path, "field-pilot-v1", "linux", "posix")
            payload = record_path.read_bytes()
            manifest_value = batch.build_manifest([("sessions/a.json", hashlib.sha256(payload).hexdigest())])
            manifest = root / "batch.json"
            manifest.write_text(json.dumps(manifest_value), encoding="utf-8")
            themes = root / "themes.json"
            digest = hashlib.sha256(payload).hexdigest()
            themes.write_text(json.dumps({digest: ["navigation"]}), encoding="utf-8")
            output = root / "summary.json"
            before = payload, manifest.read_bytes(), themes.read_bytes()
            result = subprocess.run(
                [sys.executable, str(BUILD / "evaluator_session_aggregate.py"), str(manifest), "--root", str(root), "--output", str(output), "--themes", str(themes)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertTrue(output.is_file())
            self.assertEqual(before, (record_path.read_bytes(), manifest.read_bytes(), themes.read_bytes()))


if __name__ == "__main__":
    unittest.main()
