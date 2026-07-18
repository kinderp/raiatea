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
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-context"
sys.path.insert(0, str(BUILD_DIR))

import check_evidence_compatibility as v1_checker  # noqa: E402
import check_evidence_compatibility_v2 as v2_checker  # noqa: E402
import check_evidence_migration_manifest_context as context_checker  # noqa: E402
import validate_evidence_export_v2 as v2_validator  # noqa: E402
import validate_evidence_migration_manifest as manifest_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class MigrationManifestContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_path = FIXTURE_DIR / "exact-source.json"
        cls.target_path = FIXTURE_DIR / "exact-target.json"
        cls.manifest_path = FIXTURE_DIR / "exact-manifest.json"
        cls.source = module_validator.load_and_validate(cls.source_path)
        cls.target = module_validator.load_and_validate(cls.target_path)
        cls.manifest = manifest_validator.load_and_validate(cls.manifest_path)

    def test_exact_triplet_is_contextually_valid(self) -> None:
        self.assertEqual(
            [],
            context_checker.check_manifest_context(
                self.source, self.target, self.manifest
            ),
        )
        source, target, manifest = context_checker.load_and_check(
            self.source_path, self.target_path, self.manifest_path
        )
        self.assertEqual(1, source["revision"])
        self.assertEqual(2, target["revision"])
        self.assertEqual("migration-context-fixture", manifest["source"]["moduleId"])

    def test_all_contextual_mismatches_use_fixed_order(self) -> None:
        manifest = manifest_validator.load_and_validate(
            FIXTURE_DIR / "all-endpoint-mismatches.json"
        )
        expected = [
            "$.manifest.source.moduleId: manifest source module ID 'other-route' does not match source module ID 'migration-context-fixture'",
            "$.manifest.source.revision: manifest source revision '9' does not match source module revision '1'",
            "$.manifest.source.stepIds: manifest source step IDs ['legacy-practice', 'orient-concept'] do not match source module step IDs ['orient-concept', 'legacy-practice']",
            "$.manifest.target.moduleId: manifest target module ID 'other-route' does not match target module ID 'migration-context-fixture'",
            "$.manifest.target.revision: manifest target revision '10' does not match target module revision '2'",
            "$.manifest.target.stepIds: manifest target step IDs ['new-enrichment', 'apply-concept', 'orient-concept'] do not match target module step IDs ['orient-concept', 'apply-concept', 'new-enrichment']",
        ]
        self.assertEqual(
            expected,
            context_checker.check_manifest_context(self.source, self.target, manifest),
        )

    def test_inventory_omission_addition_and_reorder_are_exact_mismatches(self) -> None:
        cases = {
            "source-inventory-omission.json": "$.manifest.source.stepIds:",
            "source-inventory-addition.json": "$.manifest.source.stepIds:",
            "target-inventory-omission.json": "$.manifest.target.stepIds:",
            "target-inventory-addition.json": "$.manifest.target.stepIds:",
            "inventory-reorder.json": "$.manifest.source.stepIds:",
        }
        for fixture_name, first_prefix in cases.items():
            with self.subTest(fixture=fixture_name):
                manifest = manifest_validator.load_and_validate(FIXTURE_DIR / fixture_name)
                issues = context_checker.check_manifest_context(
                    self.source, self.target, manifest
                )
                self.assertTrue(issues[0].startswith(first_prefix))
                if fixture_name == "inventory-reorder.json":
                    self.assertEqual(2, len(issues))
                    self.assertTrue(issues[1].startswith("$.manifest.target.stepIds:"))
                else:
                    self.assertEqual(1, len(issues))

    def test_explanatory_module_fields_are_not_contextual_keys(self) -> None:
        source = copy.deepcopy(self.source)
        target = copy.deepcopy(self.target)
        source["title"] = "Different source title"
        source["language"] = "it"
        source["steps"][0]["title"] = "Different source step title"
        target["title"] = "Different target title"
        target["visual"]["markup"] = "<svg id=\"different-visual\"></svg>"
        target["steps"][1]["explanation"] = "<p>Different explanation.</p>"
        self.assertEqual(
            [], context_checker.check_manifest_context(source, target, self.manifest)
        )

    def test_structural_failures_are_namespaced_before_contextual_comparison(self) -> None:
        invalid_module = (
            ROOT / "tests" / "fixtures" / "module-identity" / "missing-revision.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            unsupported_manifest = Path(directory) / "unsupported-manifest.json"
            data = copy.deepcopy(self.manifest)
            data["version"] = 2
            unsupported_manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(
                context_checker.MigrationManifestInputValidationError
            ) as raised:
                context_checker.load_and_check(
                    invalid_module, invalid_module, unsupported_manifest
                )
        issues = list(raised.exception.issues)
        self.assertTrue(issues[0].startswith("$.sourceModule.revision:"))
        self.assertTrue(issues[1].startswith("$.targetModule.revision:"))
        self.assertTrue(issues[2].startswith("$.manifest.version:"))

    def test_malformed_json_is_reported_under_each_input_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            malformed = Path(directory) / "malformed.json"
            malformed.write_text('{"id":', encoding="utf-8")
            with self.assertRaises(
                context_checker.MigrationManifestInputValidationError
            ) as raised:
                context_checker.load_and_check(malformed, malformed, malformed)
        issues = list(raised.exception.issues)
        self.assertEqual(3, len(issues))
        self.assertTrue(issues[0].startswith("$.sourceModule:"))
        self.assertTrue(issues[1].startswith("$.targetModule:"))
        self.assertTrue(issues[2].startswith("$.manifest:"))
        self.assertTrue(all("invalid JSON" in issue for issue in issues))

    def test_contextual_check_is_side_effect_free(self) -> None:
        source = copy.deepcopy(self.source)
        target = copy.deepcopy(self.target)
        manifest = copy.deepcopy(self.manifest)
        originals = (copy.deepcopy(source), copy.deepcopy(target), copy.deepcopy(manifest))
        context_checker.check_manifest_context(source, target, manifest)
        self.assertEqual(originals, (source, target, manifest))

    def test_cli_success_and_failure_do_not_infer_revision_order(self) -> None:
        checker = BUILD_DIR / "check_evidence_migration_manifest_context.py"
        success = subprocess.run(
            [sys.executable, str(checker), str(self.source_path), str(self.target_path), str(self.manifest_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, success.returncode, success.stderr)
        self.assertIn("Contextually valid migration manifest", success.stdout)

        failure = subprocess.run(
            [
                sys.executable,
                str(checker),
                str(self.source_path),
                str(self.target_path),
                str(FIXTURE_DIR / "all-endpoint-mismatches.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, failure.returncode)
        self.assertIn("does not match", failure.stdout)
        for forbidden in ("older", "newer", "previous", "next", "higher", "lower"):
            self.assertNotIn(forbidden, failure.stdout.lower())

    def test_existing_evidence_and_manifest_contracts_remain_green(self) -> None:
        v1_module = module_validator.load_and_validate(
            ROOT / "examples" / "self-attention.json"
        )
        v1_evidence = v1_checker.evidence_validator.load_and_validate(
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        self.assertEqual([], v1_checker.check_compatibility(v1_module, v1_evidence))

        v2_module = module_validator.load_and_validate(
            ROOT / "tests" / "fixtures" / "module-identity" / "valid.json"
        )
        v2_evidence = v2_validator.load_and_validate(
            ROOT / "tests" / "fixtures" / "evidence-v2-contextual" / "exact.json"
        )
        self.assertEqual([], v2_checker.check_exact_compatibility(v2_module, v2_evidence))
        self.assertEqual(
            [], manifest_validator.validate_migration_manifest(copy.deepcopy(self.manifest))
        )


if __name__ == "__main__":
    unittest.main()
