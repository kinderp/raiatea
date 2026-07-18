from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
CONTEXT_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-context"
PREVIEW_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-preview"
sys.path.insert(0, str(BUILD_DIR))

import preview_evidence_migration_v2 as preview  # noqa: E402


class EvidenceCompatibilityPreviewLoaderTests(unittest.TestCase):
    def test_loader_resolves_declarative_target_layout_before_classification(self) -> None:
        result = preview.load_and_preview(
            ROOT / "tests" / "fixtures" / "evidence-v2-contextual" / "exact.json",
            ROOT / "examples" / "query-key-value.json",
        )
        self.assertEqual("incompatible", result["classification"])
        self.assertIn("different module routes", result["summary"])

    def test_non_object_evidence_is_namespaced_structural_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_path = Path(temporary) / "array.json"
            evidence_path.write_text("[]", encoding="utf-8")
            with self.assertRaises(
                preview.EvidenceMigrationPreviewInputError
            ) as raised:
                preview.load_and_preview(
                    evidence_path,
                    CONTEXT_DIR / "exact-target.json",
                )
        self.assertEqual(["$.evidence: must be an object"], list(raised.exception.issues))

    def test_malformed_inputs_accumulate_in_fixed_namespace_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            evidence_path = temporary_path / "evidence.json"
            source_path = temporary_path / "source.json"
            manifest_path = temporary_path / "manifest.json"
            evidence_path.write_text('{"format":', encoding="utf-8")
            source_path.write_text('{"id":', encoding="utf-8")
            manifest_path.write_text('{"version":', encoding="utf-8")
            with self.assertRaises(
                preview.EvidenceMigrationPreviewInputError
            ) as raised:
                preview.load_and_preview(
                    evidence_path,
                    CONTEXT_DIR / "exact-target.json",
                    source_module_path=source_path,
                    manifest_path=manifest_path,
                )
        self.assertEqual(3, len(raised.exception.issues))
        self.assertTrue(raised.exception.issues[0].startswith("$.evidence:"))
        self.assertTrue(raised.exception.issues[1].startswith("$.sourceModule:"))
        self.assertTrue(raised.exception.issues[2].startswith("$.manifest:"))

    def test_cli_emits_machine_readable_partial_preview(self) -> None:
        command = [
            sys.executable,
            str(BUILD_DIR / "preview_evidence_migration_v2.py"),
            str(PREVIEW_DIR / "source-current-preserved.json"),
            str(CONTEXT_DIR / "exact-target.json"),
            "--source",
            str(CONTEXT_DIR / "exact-source.json"),
            "--manifest",
            str(CONTEXT_DIR / "exact-manifest.json"),
            "--json",
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("declared-partial", payload["classification"])
        self.assertEqual("applicable", payload["manifestStatus"])
        self.assertTrue(payload["candidateAvailable"])

    def test_cli_exits_nonzero_for_unsupported_manifest_version(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(BUILD_DIR / "preview_evidence_migration_v2.py"),
                str(PREVIEW_DIR / "source-current-preserved.json"),
                str(CONTEXT_DIR / "exact-target.json"),
                "--source",
                str(CONTEXT_DIR / "exact-source.json"),
                "--manifest",
                str(CONTEXT_DIR / "unsupported-version.json"),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, result.returncode)
        payload = json.loads(result.stdout)
        self.assertEqual("unsupported", payload["classification"])
        self.assertEqual("unsupported", payload["manifestStatus"])


if __name__ == "__main__":
    unittest.main()
