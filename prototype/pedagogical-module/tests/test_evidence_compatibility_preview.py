from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
MIGRATION_CONTEXT_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-context"
PREVIEW_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-preview"
sys.path.insert(0, str(BUILD_DIR))

import check_evidence_compatibility as v1_checker  # noqa: E402
import check_evidence_compatibility_v2 as exact_checker  # noqa: E402
import classify_evidence_compatibility_v2 as classifier  # noqa: E402
import preview_evidence_migration_v2 as preview  # noqa: E402
import validate_evidence_export_v2 as evidence_validator  # noqa: E402
import validate_evidence_migration_manifest as manifest_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class EvidenceCompatibilityPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.exact_target_path = (
            ROOT / "tests" / "fixtures" / "module-identity" / "valid.json"
        )
        cls.exact_evidence_path = (
            ROOT / "tests" / "fixtures" / "evidence-v2-contextual" / "exact.json"
        )
        cls.source_path = MIGRATION_CONTEXT_DIR / "exact-source.json"
        cls.partial_target_path = MIGRATION_CONTEXT_DIR / "exact-target.json"
        cls.partial_manifest_path = MIGRATION_CONTEXT_DIR / "exact-manifest.json"
        cls.preserved_evidence_path = PREVIEW_DIR / "source-current-preserved.json"
        cls.retired_evidence_path = PREVIEW_DIR / "source-current-retired.json"
        cls.lossless_target_path = PREVIEW_DIR / "lossless-target.json"
        cls.lossless_manifest_path = PREVIEW_DIR / "lossless-manifest.json"

        cls.exact_target = module_validator.load_and_validate(cls.exact_target_path)
        cls.exact_evidence = evidence_validator.load_and_validate(
            cls.exact_evidence_path
        )
        cls.source = module_validator.load_and_validate(cls.source_path)
        cls.partial_target = module_validator.load_and_validate(
            cls.partial_target_path
        )
        cls.partial_manifest = manifest_validator.load_and_validate(
            cls.partial_manifest_path
        )
        cls.preserved_evidence = evidence_validator.load_and_validate(
            cls.preserved_evidence_path
        )
        cls.retired_evidence = evidence_validator.load_and_validate(
            cls.retired_evidence_path
        )
        cls.lossless_target = module_validator.load_and_validate(
            cls.lossless_target_path
        )
        cls.lossless_manifest = manifest_validator.load_and_validate(
            cls.lossless_manifest_path
        )

    def test_exact_result_has_closed_read_only_preview(self) -> None:
        result = classifier.classify(self.exact_evidence, self.exact_target)
        self.assertEqual(
            {
                "classification",
                "source",
                "target",
                "manifestStatus",
                "summary",
                "issues",
                "steps",
                "currentPosition",
                "candidateAvailable",
                "candidate",
            },
            set(result),
        )
        self.assertEqual("exact", result["classification"])
        self.assertEqual("not-needed", result["manifestStatus"])
        self.assertFalse(result["candidateAvailable"])
        self.assertIsNone(result["candidate"])
        self.assertEqual([], result["issues"])
        self.assertEqual("unchanged", result["currentPosition"]["status"])
        self.assertEqual(
            ["orient-concept", "apply-concept"],
            [entry["stepId"] for entry in result["steps"]],
        )
        self.assertTrue(
            all(entry["status"] == "preserved" for entry in result["steps"])
        )
        self.assertTrue(
            all(
                entry["evidenceDisposition"] == "copied"
                for entry in result["steps"]
            )
        )

    def test_non_exact_without_context_is_incompatible(self) -> None:
        result = classifier.classify(self.preserved_evidence, self.partial_target)
        self.assertEqual("incompatible", result["classification"])
        self.assertEqual("missing", result["manifestStatus"])
        self.assertFalse(result["candidateAvailable"])
        self.assertIn("direct migration manifest is required", result["issues"][0])

    def test_partial_optional_context_is_an_input_error(self) -> None:
        with self.assertRaises(preview.EvidenceMigrationPreviewInputError) as raised:
            classifier.classify(
                self.preserved_evidence,
                self.partial_target,
                source_module=self.source,
            )
        self.assertEqual(
            ["$.migrationContext: sourceModule and manifest must be supplied together"],
            list(raised.exception.issues),
        )

    def test_declared_partial_preview_with_preserved_current_builds_candidate(self) -> None:
        result = classifier.classify(
            self.preserved_evidence,
            self.partial_target,
            source_module=self.source,
            manifest=self.partial_manifest,
        )
        self.assertEqual("declared-partial", result["classification"])
        self.assertEqual("applicable", result["manifestStatus"])
        self.assertEqual("remapped", result["currentPosition"]["status"])
        self.assertEqual(0, result["currentPosition"]["targetIndex"])
        self.assertTrue(result["candidateAvailable"])
        self.assertEqual(
            ["orient-concept", "apply-concept", "new-enrichment", "legacy-practice"],
            [entry["stepId"] for entry in result["steps"]],
        )
        self.assertEqual(
            ["preserved", "introduced", "introduced", "retired"],
            [entry["status"] for entry in result["steps"]],
        )
        self.assertEqual(
            ["copied", "empty", "empty", "historical-only"],
            [entry["evidenceDisposition"] for entry in result["steps"]],
        )
        candidate = result["candidate"]
        self.assertEqual([], evidence_validator.validate_evidence_export_v2(candidate))
        self.assertEqual(
            [], exact_checker.check_exact_compatibility(self.partial_target, candidate)
        )
        self.assertEqual(2, candidate["progress"]["steps"][0]["attempts"])
        self.assertEqual(0, candidate["progress"]["steps"][1]["attempts"])
        self.assertFalse(candidate["progress"]["steps"][1]["correct"])
        self.assertNotIn(
            "legacy-practice",
            [step["stepId"] for step in candidate["progress"]["steps"]],
        )

    def test_declared_partial_with_retired_current_is_unresolved(self) -> None:
        result = classifier.classify(
            self.retired_evidence,
            self.partial_target,
            source_module=self.source,
            manifest=self.partial_manifest,
        )
        self.assertEqual("declared-partial", result["classification"])
        self.assertEqual("unresolved-retired", result["currentPosition"]["status"])
        self.assertEqual("legacy-practice", result["currentPosition"]["sourceStepId"])
        self.assertIsNone(result["currentPosition"]["targetStepId"])
        self.assertFalse(result["candidateAvailable"])
        self.assertIsNone(result["candidate"])

    def test_declared_lossless_reorder_remaps_current_by_stable_id(self) -> None:
        result = classifier.classify(
            self.preserved_evidence,
            self.lossless_target,
            source_module=self.source,
            manifest=self.lossless_manifest,
        )
        self.assertEqual("declared-lossless", result["classification"])
        self.assertEqual("remapped", result["currentPosition"]["status"])
        self.assertEqual("orient-concept", result["currentPosition"]["targetStepId"])
        self.assertEqual(1, result["currentPosition"]["targetIndex"])
        self.assertEqual(
            ["legacy-practice", "orient-concept"],
            [entry["stepId"] for entry in result["steps"]],
        )
        self.assertTrue(result["candidateAvailable"])
        candidate = result["candidate"]
        self.assertEqual([], evidence_validator.validate_evidence_export_v2(candidate))
        self.assertEqual(
            [], exact_checker.check_exact_compatibility(self.lossless_target, candidate)
        )
        self.assertEqual(
            ["legacy-practice", "orient-concept"],
            [step["stepId"] for step in candidate["progress"]["steps"]],
        )
        self.assertEqual(1, candidate["progress"]["currentStepIndex"])

    def test_cross_route_and_source_mismatch_fail_closed(self) -> None:
        cross_route = copy.deepcopy(self.partial_target)
        cross_route["id"] = "different-route"
        result = classifier.classify(self.preserved_evidence, cross_route)
        self.assertEqual("incompatible", result["classification"])
        self.assertIn("different module routes", result["summary"])

        mismatched_evidence = copy.deepcopy(self.preserved_evidence)
        mismatched_evidence["module"]["revision"] = 9
        source_result = classifier.classify(
            mismatched_evidence,
            self.partial_target,
            source_module=self.source,
            manifest=self.partial_manifest,
        )
        self.assertEqual("incompatible", source_result["classification"])
        self.assertEqual("mismatched", source_result["manifestStatus"])
        self.assertTrue(
            source_result["issues"][0].startswith("$.sourceContext.module.revision")
        )

    def test_contextually_mismatched_manifest_fails_closed(self) -> None:
        result = classifier.classify(
            self.preserved_evidence,
            self.partial_target,
            source_module=self.source,
            manifest=self.lossless_manifest,
        )
        self.assertEqual("incompatible", result["classification"])
        self.assertEqual("mismatched", result["manifestStatus"])
        self.assertTrue(
            any(issue.startswith("$.manifest.target.revision") for issue in result["issues"])
        )

    def test_classifier_does_not_mutate_inputs(self) -> None:
        values = tuple(
            copy.deepcopy(value)
            for value in (
                self.preserved_evidence,
                self.partial_target,
                self.source,
                self.partial_manifest,
            )
        )
        originals = copy.deepcopy(values)
        classifier.classify(
            values[0], values[1], source_module=values[2], manifest=values[3]
        )
        self.assertEqual(originals, values)

    def test_loader_classifies_unsupported_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            unsupported_evidence = copy.deepcopy(self.preserved_evidence)
            unsupported_evidence["version"] = 7
            evidence_path = temporary_path / "unsupported-evidence.json"
            evidence_path.write_text(json.dumps(unsupported_evidence), encoding="utf-8")
            result = preview.load_and_preview(evidence_path, self.partial_target_path)
            self.assertEqual("unsupported", result["classification"])
            self.assertEqual("not-needed", result["manifestStatus"])

        result = preview.load_and_preview(
            self.preserved_evidence_path,
            self.partial_target_path,
            source_module_path=self.source_path,
            manifest_path=MIGRATION_CONTEXT_DIR / "unsupported-version.json",
        )
        self.assertEqual("unsupported", result["classification"])
        self.assertEqual("unsupported", result["manifestStatus"])

    def test_loader_namespaces_malformed_and_structural_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            malformed_path = temporary_path / "malformed.json"
            malformed_path.write_text('{"format":', encoding="utf-8")
            with self.assertRaises(preview.EvidenceMigrationPreviewInputError) as malformed:
                preview.load_and_preview(malformed_path, self.partial_target_path)
            self.assertTrue(malformed.exception.issues[0].startswith("$.evidence: invalid JSON"))

            invalid_evidence = copy.deepcopy(self.preserved_evidence)
            del invalid_evidence["module"]["revision"]
            invalid_path = temporary_path / "invalid.json"
            invalid_path.write_text(json.dumps(invalid_evidence), encoding="utf-8")
            with self.assertRaises(preview.EvidenceMigrationPreviewInputError) as invalid:
                preview.load_and_preview(invalid_path, self.partial_target_path)
            self.assertIn(
                "$.evidence.module.revision: required field is missing",
                invalid.exception.issues,
            )

    def test_cli_human_json_and_exit_codes(self) -> None:
        checker = BUILD_DIR / "preview_evidence_migration_v2.py"
        exact = subprocess.run(
            [sys.executable, str(checker), str(self.exact_evidence_path), str(self.exact_target_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, exact.returncode, exact.stderr)
        self.assertIn("Classification: exact", exact.stdout)
        self.assertIn("Candidate available: false", exact.stdout)

        partial = subprocess.run(
            [
                sys.executable,
                str(checker),
                str(self.preserved_evidence_path),
                str(self.partial_target_path),
                "--source",
                str(self.source_path),
                "--manifest",
                str(self.partial_manifest_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, partial.returncode, partial.stderr)
        payload = json.loads(partial.stdout)
        self.assertEqual("declared-partial", payload["classification"])
        self.assertTrue(payload["candidateAvailable"])

        incompatible = subprocess.run(
            [
                sys.executable,
                str(checker),
                str(self.preserved_evidence_path),
                str(self.partial_target_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, incompatible.returncode)
        self.assertIn("Classification: incompatible", incompatible.stdout)

    def test_existing_v1_v2_and_manifest_contracts_remain_green(self) -> None:
        v1_module = module_validator.load_and_validate(
            ROOT / "examples" / "self-attention.json"
        )
        v1_evidence = v1_checker.evidence_validator.load_and_validate(
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        self.assertEqual([], v1_checker.check_compatibility(v1_module, v1_evidence))
        self.assertEqual(
            [], exact_checker.check_exact_compatibility(self.exact_target, self.exact_evidence)
        )
        self.assertEqual(
            [], manifest_validator.validate_migration_manifest(self.partial_manifest)
        )


if __name__ == "__main__":
    unittest.main()
