from __future__ import annotations

import copy
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-v2-contextual"
MODULE_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "module-identity"
MODULE_PATH = MODULE_FIXTURE_DIR / "valid.json"
INVALID_MODULE_PATH = MODULE_FIXTURE_DIR / "missing-revision.json"
sys.path.insert(0, str(BUILD_DIR))

import check_evidence_compatibility as v1_checker  # noqa: E402
import check_evidence_compatibility_v2 as v2_checker  # noqa: E402
import validate_evidence_export_v2 as v2_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class LearnerEvidenceV2ExactCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = module_validator.load_and_validate(MODULE_PATH)
        cls.exact = v2_validator.load_and_validate(FIXTURE_DIR / "exact.json")

    def test_exact_fixture_and_explanatory_metadata_drift_are_compatible(self) -> None:
        module, evidence = v2_checker.load_and_check(
            MODULE_PATH, FIXTURE_DIR / "exact.json"
        )
        self.assertEqual("identity-fixture", module["id"])
        self.assertEqual(1, evidence["module"]["revision"])
        self.assertEqual(
            [],
            v2_checker.check_exact_compatibility(
                self.module,
                v2_validator.load_and_validate(
                    FIXTURE_DIR / "explanatory-metadata-drift.json"
                ),
            ),
        )

    def test_contextual_fixtures_report_all_exact_mismatches(self) -> None:
        expected = {
            "module-id-mismatch.json": [
                "$.module.id: exported module ID 'other-fixture' does not match canonical module ID 'identity-fixture'"
            ],
            "revision-mismatch.json": [
                "$.module.revision: exported module revision '7' does not match canonical module revision '1'"
            ],
            "step-count-mismatch.json": [
                "$.module.stepCount: exported step count 1 does not match canonical module step count 2",
                "$.progress.steps: exported step sequence length 1 does not match canonical module step sequence length 2",
                "$.progress.steps: canonical step ID 'apply-concept' is missing from the exported step sequence",
            ],
            "extra-step-current.json": [
                "$.module.stepCount: exported step count 3 does not match canonical module step count 2",
                "$.progress.steps: exported step sequence length 3 does not match canonical module step sequence length 2",
                "$.progress.steps[2].stepId: exported step ID 'extra-concept' is not present in the canonical module revision",
                "$.progress.currentStepIndex: exported current step index 2 does not refer to an active canonical step",
            ],
            "reordered-step-ids.json": [
                "$.progress.steps[0].stepId: exported step ID 'apply-concept' does not match canonical step ID 'orient-concept' at this route position",
                "$.progress.steps[1].stepId: exported step ID 'orient-concept' does not match canonical step ID 'apply-concept' at this route position",
                "$.progress.currentStepId: exported current step ID 'apply-concept' does not match canonical step ID 'orient-concept' at currentStepIndex 0",
            ],
            "replaced-step-id.json": [
                "$.progress.steps[1].stepId: exported step ID 'replacement-concept' is not present in the canonical module revision",
                "$.progress.steps: canonical step ID 'apply-concept' is missing from the exported step sequence",
                "$.progress.currentStepId: exported current step ID 'replacement-concept' does not match canonical step ID 'apply-concept' at currentStepIndex 1",
            ],
        }
        for fixture_name, expected_issues in expected.items():
            with self.subTest(fixture=fixture_name):
                evidence = v2_validator.load_and_validate(FIXTURE_DIR / fixture_name)
                self.assertEqual(
                    expected_issues,
                    v2_checker.check_exact_compatibility(self.module, evidence),
                )
                with self.assertRaises(v2_checker.EvidenceV2CompatibilityError) as raised:
                    v2_checker.load_and_check(MODULE_PATH, FIXTURE_DIR / fixture_name)
                self.assertEqual(expected_issues, list(raised.exception.issues))

    def test_structural_failures_stop_before_contextual_comparison(self) -> None:
        invalid_evidence = (
            ROOT
            / "tests"
            / "fixtures"
            / "evidence-v2"
            / "unsupported-version.json"
        )
        with self.assertRaises(v2_validator.EvidenceExportV2ValidationError):
            v2_checker.load_and_check(MODULE_PATH, invalid_evidence)
        with self.assertRaises(module_validator.ModuleValidationError):
            v2_checker.load_and_check(
                INVALID_MODULE_PATH, FIXTURE_DIR / "exact.json"
            )

    def test_titles_language_and_source_are_not_compatibility_keys(self) -> None:
        evidence = copy.deepcopy(self.exact)
        evidence["module"]["title"] = "Different explanatory module title"
        evidence["module"]["language"] = "it"
        evidence["module"]["source"] = {"title": "Different source", "pages": [99]}
        evidence["progress"]["steps"][0]["title"] = "Different step snapshot"
        evidence["progress"]["steps"][1]["title"] = "Another snapshot"
        self.assertEqual([], v2_checker.check_exact_compatibility(self.module, evidence))

    def test_check_is_side_effect_free(self) -> None:
        module = copy.deepcopy(self.module)
        evidence = copy.deepcopy(self.exact)
        original_module = copy.deepcopy(module)
        original_evidence = copy.deepcopy(evidence)
        v2_checker.check_exact_compatibility(module, evidence)
        self.assertEqual(original_module, module)
        self.assertEqual(original_evidence, evidence)

    def test_v1_compatibility_contract_remains_unchanged(self) -> None:
        v1_module = module_validator.load_and_validate(
            ROOT / "examples" / "self-attention.json"
        )
        v1_evidence = v1_checker.evidence_validator.load_and_validate(
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        self.assertEqual([], v1_checker.check_compatibility(v1_module, v1_evidence))

    def test_cli_returns_success_for_exact_and_failure_for_mismatch(self) -> None:
        checker = BUILD_DIR / "check_evidence_compatibility_v2.py"
        success = subprocess.run(
            [sys.executable, str(checker), str(MODULE_PATH), str(FIXTURE_DIR / "exact.json")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, success.returncode, success.stderr)
        self.assertIn("Exact compatible evidence v2", success.stdout)

        failure = subprocess.run(
            [
                sys.executable,
                str(checker),
                str(MODULE_PATH),
                str(FIXTURE_DIR / "revision-mismatch.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, failure.returncode)
        self.assertIn("does not match canonical module revision", failure.stdout)
        for forbidden in ("older", "newer", "previous", "next", "higher", "lower"):
            self.assertNotIn(forbidden, failure.stdout.lower())


if __name__ == "__main__":
    unittest.main()
