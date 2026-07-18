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

import classify_evidence_compatibility_v2 as classifier  # noqa: E402
import preview_evidence_migration_v2 as preview  # noqa: E402
import validate_evidence_export_v2 as evidence_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class EvidenceCompatibilityPreviewBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.exact_evidence_path = (
            ROOT / "tests" / "fixtures" / "evidence-v2-contextual" / "exact.json"
        )
        cls.exact_target_path = (
            ROOT / "tests" / "fixtures" / "module-identity" / "valid.json"
        )
        cls.source_path = CONTEXT_DIR / "exact-source.json"
        cls.source = module_validator.load_and_validate(cls.source_path)
        cls.exact_evidence = evidence_validator.load_and_validate(
            cls.exact_evidence_path
        )
        cls.exact_target = module_validator.load_and_validate(cls.exact_target_path)

    def test_exact_classification_rejects_incomplete_optional_context(self) -> None:
        with self.assertRaises(preview.EvidenceMigrationPreviewInputError) as raised:
            classifier.classify(
                self.exact_evidence,
                self.exact_target,
                source_module=self.source,
            )
        self.assertEqual(
            ["$.migrationContext: sourceModule and manifest must be supplied together"],
            list(raised.exception.issues),
        )

    def test_non_object_json_fails_under_input_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            array_evidence = temporary_path / "array-evidence.json"
            null_target = temporary_path / "null-target.json"
            array_evidence.write_text("[]", encoding="utf-8")
            null_target.write_text("null", encoding="utf-8")

            with self.assertRaises(preview.EvidenceMigrationPreviewInputError) as evidence:
                preview.load_and_preview(array_evidence, self.exact_target_path)
            self.assertTrue(evidence.exception.issues[0].startswith("$.evidence"))

            with self.assertRaises(preview.EvidenceMigrationPreviewInputError) as target:
                preview.load_and_preview(self.exact_evidence_path, null_target)
            self.assertTrue(target.exception.issues[0].startswith("$.targetModule"))

    def test_canonical_loader_resolves_declarative_layout_targets(self) -> None:
        result = preview.load_and_preview(
            self.exact_evidence_path,
            ROOT / "examples" / "query-key-value.json",
        )
        self.assertEqual("incompatible", result["classification"])
        self.assertIn("different module routes", result["summary"])

    def test_human_preview_states_that_no_mutation_occurred(self) -> None:
        process = subprocess.run(
            [
                sys.executable,
                str(BUILD_DIR / "preview_evidence_migration_v2.py"),
                str(self.exact_evidence_path),
                str(self.exact_target_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertIn(
            "Preview only: no evidence file or learner state was changed.",
            process.stdout,
        )

    def test_generated_candidate_is_exact_target_evidence(self) -> None:
        evidence = evidence_validator.load_and_validate(
            PREVIEW_DIR / "source-current-preserved.json"
        )
        target = module_validator.load_and_validate(CONTEXT_DIR / "exact-target.json")
        source = module_validator.load_and_validate(CONTEXT_DIR / "exact-source.json")
        manifest = json.loads((CONTEXT_DIR / "exact-manifest.json").read_text())
        result = classifier.classify(
            evidence,
            target,
            source_module=source,
            manifest=manifest,
        )
        self.assertTrue(result["candidateAvailable"])
        candidate = result["candidate"]
        self.assertEqual([], evidence_validator.validate_evidence_export_v2(candidate))
        self.assertEqual(target["id"], candidate["module"]["id"])
        self.assertEqual(target["revision"], candidate["module"]["revision"])


if __name__ == "__main__":
    unittest.main()
