from __future__ import annotations

import copy
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
CONTEXT_FIXTURE_DIR = (
    ROOT / "tests" / "fixtures" / "evidence-migration-manifest-context"
)
MODULE_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "module-identity"
SOURCE_MODULE_PATH = MODULE_FIXTURE_DIR / "valid.json"
TARGET_MODULE_PATH = CONTEXT_FIXTURE_DIR / "target-module.json"
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
        cls.source_module = module_validator.load_and_validate(SOURCE_MODULE_PATH)
        cls.target_module = module_validator.load_and_validate(TARGET_MODULE_PATH)
        cls.exact_manifest = manifest_validator.load_and_validate(
            CONTEXT_FIXTURE_DIR / "exact.json"
        )

    def test_exact_fixture_passes(self) -> None:
        source, target, manifest = context_checker.load_and_check(
            SOURCE_MODULE_PATH,
            TARGET_MODULE_PATH,
            CONTEXT_FIXTURE_DIR / "exact.json",
        )
        self.assertEqual("identity-fixture", source["id"])
        self.assertEqual(2, target["revision"])
        self.assertEqual(1, manifest["source"]["revision"])

    def test_explanatory_module_fields_are_not_context_keys(self) -> None:
        source = copy.deepcopy(self.source_module)
        target = copy.deepcopy(self.target_module)
        source["title"] = "Different source title"
        source["language"] = "it"
        target["title"] = "Different target title"
        target["steps"][0]["title"] = "Different step snapshot"
        self.assertEqual(
            [],
            context_checker.check_manifest_context(
                source, target, copy.deepcopy(self.exact_manifest)
            ),
        )

    def test_contextual_fixtures_report_exact_reasons(self) -> None:
        expected = {
            "source-revision-mismatch.json": [
                "$.source.revision: manifest source revision '7' does not match supplied source module revision '1'"
            ],
            "source-inventory-reordered.json": [
                "$.source.stepIds[0]: manifest source step ID 'apply-concept' does not match canonical source step ID 'orient-concept' at this route position",
                "$.source.stepIds[1]: manifest source step ID 'orient-concept' does not match canonical source step ID 'apply-concept' at this route position",
            ],
            "target-inventory-extra.json": [
                "$.target.stepIds: manifest target inventory length 3 does not match canonical target step count 2",
                "$.target.stepIds[2]: manifest target step ID 'extra-concept' is not present in the canonical target revision",
            ],
        }
        for fixture_name, expected_issues in expected.items():
            with self.subTest(fixture=fixture_name):
                manifest = manifest_validator.load_and_validate(
                    CONTEXT_FIXTURE_DIR / fixture_name
                )
                self.assertEqual(
                    expected_issues,
                    context_checker.check_manifest_context(
                        self.source_module,
                        self.target_module,
                        manifest,
                    ),
                )
                with self.assertRaises(
                    context_checker.MigrationManifestContextError
                ) as raised:
                    context_checker.load_and_check(
                        SOURCE_MODULE_PATH,
                        TARGET_MODULE_PATH,
                        CONTEXT_FIXTURE_DIR / fixture_name,
                    )
                self.assertEqual(expected_issues, list(raised.exception.issues))

    def test_supplied_module_identity_and_revision_mismatches_fail_closed(self) -> None:
        target = copy.deepcopy(self.target_module)
        target["id"] = "other-module"
        target["revision"] = self.source_module["revision"]
        issues = context_checker.check_manifest_context(
            self.source_module, target, copy.deepcopy(self.exact_manifest)
        )
        self.assertEqual(
            [
                "$.target.moduleId: supplied target module ID 'other-module' does not match supplied source module ID 'identity-fixture'",
                "$.target.revision: supplied target module revision must differ from supplied source module revision",
                "$.target.moduleId: manifest target module ID 'identity-fixture' does not match supplied target module ID 'other-module'",
                "$.target.revision: manifest target revision '2' does not match supplied target module revision '1'",
            ],
            issues,
        )

    def test_missing_and_replaced_inventory_ids_are_distinguished(self) -> None:
        manifest = copy.deepcopy(self.exact_manifest)
        manifest["target"]["stepIds"] = ["apply-concept", "replacement-concept"]
        issues = context_checker.check_manifest_context(
            self.source_module, self.target_module, manifest
        )
        self.assertEqual(
            [
                "$.target.stepIds[1]: manifest target step ID 'replacement-concept' is not present in the canonical target revision",
                "$.target.stepIds: canonical target step ID 'enrichment-concept' is missing from the manifest inventory",
            ],
            issues,
        )

    def test_structural_failures_stop_before_contextual_comparison(self) -> None:
        with self.assertRaises(module_validator.ModuleValidationError):
            context_checker.load_and_check(
                MODULE_FIXTURE_DIR / "missing-revision.json",
                TARGET_MODULE_PATH,
                CONTEXT_FIXTURE_DIR / "exact.json",
            )
        with self.assertRaises(module_validator.ModuleValidationError):
            context_checker.load_and_check(
                SOURCE_MODULE_PATH,
                MODULE_FIXTURE_DIR / "missing-step-id.json",
                CONTEXT_FIXTURE_DIR / "exact.json",
            )
        with self.assertRaises(manifest_validator.MigrationManifestValidationError):
            context_checker.load_and_check(
                SOURCE_MODULE_PATH,
                TARGET_MODULE_PATH,
                ROOT
                / "tests"
                / "fixtures"
                / "evidence-migration-manifest"
                / "same-revision.json",
            )

    def test_context_check_is_side_effect_free(self) -> None:
        source = copy.deepcopy(self.source_module)
        target = copy.deepcopy(self.target_module)
        manifest = copy.deepcopy(self.exact_manifest)
        original_source = copy.deepcopy(source)
        original_target = copy.deepcopy(target)
        original_manifest = copy.deepcopy(manifest)
        context_checker.check_manifest_context(source, target, manifest)
        self.assertEqual(original_source, source)
        self.assertEqual(original_target, target)
        self.assertEqual(original_manifest, manifest)

    def test_cli_success_failure_and_revision_opacity(self) -> None:
        checker = BUILD_DIR / "check_evidence_migration_manifest_context.py"
        success = subprocess.run(
            [
                sys.executable,
                str(checker),
                str(SOURCE_MODULE_PATH),
                str(TARGET_MODULE_PATH),
                str(CONTEXT_FIXTURE_DIR / "exact.json"),
            ],
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
                str(SOURCE_MODULE_PATH),
                str(TARGET_MODULE_PATH),
                str(CONTEXT_FIXTURE_DIR / "source-revision-mismatch.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, failure.returncode)
        self.assertIn("does not match supplied source module revision", failure.stdout)
        for forbidden in ("older", "newer", "previous", "next", "higher", "lower"):
            self.assertNotIn(forbidden, failure.stdout.lower())

    def test_existing_contracts_remain_green(self) -> None:
        v1_module = module_validator.load_and_validate(
            ROOT / "examples" / "self-attention.json"
        )
        v1_evidence = v1_checker.evidence_validator.load_and_validate(
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        self.assertEqual([], v1_checker.check_compatibility(v1_module, v1_evidence))

        v2_module = module_validator.load_and_validate(SOURCE_MODULE_PATH)
        v2_evidence = v2_validator.load_and_validate(
            ROOT
            / "tests"
            / "fixtures"
            / "evidence-v2-contextual"
            / "exact.json"
        )
        self.assertEqual(
            [], v2_checker.check_exact_compatibility(v2_module, v2_evidence)
        )

        standalone_manifest = manifest_validator.load_and_validate(
            ROOT
            / "tests"
            / "fixtures"
            / "evidence-migration-manifest"
            / "valid.json"
        )
        self.assertEqual("fixture-module", standalone_manifest["source"]["moduleId"])


if __name__ == "__main__":
    unittest.main()
