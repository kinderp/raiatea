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

import build_evaluator_archive as archive  # noqa: E402
import build_synthesis_kit_archive as synthesis  # noqa: E402


class SynthesisKitBuildTests(unittest.TestCase):
    def test_reproducible_archive_and_example(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = synthesis.build_synthesis_kit_archive(root / "first", "kit-v1")
            second = synthesis.build_synthesis_kit_archive(root / "second", "kit-v1")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            release = archive.verify_evaluator_archive(first, root / "verified")
            required = (
                "evaluator_session_record.py",
                "evaluator_session_batch_manifest.py",
                "evaluator_session_batch_intake.py",
                "evaluator_session_aggregate.py",
                "SYNTHESIS-KIT.md",
                "synthesis-example/batch-manifest.json",
                "synthesis-example/themes.json",
                "synthesis-example/aggregate.json",
            )
            checksum_pairs = archive._parse_checksums((release / "SHA256SUMS").read_text(encoding="ascii"))
            checksums = {path: digest for digest, path in checksum_pairs}
            for relative in required:
                path = release / relative
                self.assertTrue(path.is_file(), relative)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), checksums[relative])
            aggregate = json.loads((release / "synthesis-example/aggregate.json").read_text(encoding="utf-8"))
            self.assertEqual(2, aggregate["recordCount"])

    def test_existing_output_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "raiatea-evaluator-existing.tar"
            output.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                synthesis.build_synthesis_kit_archive(root, "existing")
            self.assertEqual("keep", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
