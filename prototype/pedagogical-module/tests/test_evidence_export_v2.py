from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-v2"
sys.path.insert(0, str(BUILD_DIR))

import validate_evidence_export as v1_validator  # noqa: E402
import validate_evidence_export_v2 as v2_validator  # noqa: E402


class LearnerEvidenceExportV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example_path = (
            ROOT / "evidence-examples" / "learner-evidence-export-v2.json"
        )
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))
        cls.v1_example = json.loads(
            (
                ROOT
                / "evidence-examples"
                / "learner-evidence-export-v1.json"
            ).read_text(encoding="utf-8")
        )
        cls.schema = json.loads(
            (
                ROOT
                / "schema"
                / "learner-evidence-export-v2.schema.json"
            ).read_text(encoding="utf-8")
        )

    def clone_example(self) -> dict:
        return copy.deepcopy(self.example)

    def test_example_and_valid_fixture_match_v2_contract(self) -> None:
        self.assertEqual(
            [], v2_validator.validate_evidence_export_v2(self.clone_example())
        )
        loaded = v2_validator.load_and_validate(self.example_path)
        self.assertEqual(2, loaded["version"])
        self.assertEqual(1, loaded["module"]["revision"])
        fixture = v2_validator.load_and_validate(FIXTURE_DIR / "valid.json")
        self.assertEqual("apply-concept", fixture["progress"]["currentStepId"])

    def test_schema_is_closed_and_carries_canonical_identity(self) -> None:
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(2, self.schema["properties"]["version"]["const"])
        module_schema = self.schema["properties"]["module"]
        self.assertFalse(module_schema["additionalProperties"])
        self.assertIn("revision", module_schema["required"])
        self.assertEqual(
            {"type": "integer", "minimum": 1},
            module_schema["properties"]["revision"],
        )
        progress_schema = self.schema["properties"]["progress"]
        self.assertFalse(progress_schema["additionalProperties"])
        self.assertIn("currentStepId", progress_schema["required"])
        self.assertIn("currentStepIndex", progress_schema["required"])
        step_schema = progress_schema["properties"]["steps"]["items"]
        self.assertFalse(step_schema["additionalProperties"])
        self.assertIn("stepId", step_schema["required"])

    def test_invalid_fixtures_report_expected_fail_closed_paths(self) -> None:
        expected = {
            "unsupported-version.json": ["$.version: must be the integer 2"],
            "invalid-revision.json": [
                "$.module.revision: must be a positive integer"
            ],
            "duplicate-step-id.json": [
                "$.progress.steps[1].stepId: duplicate step id 'orient-concept'"
            ],
            "noncanonical-index.json": [
                "$.progress.steps[0].index: must equal its array position",
                "$.progress.steps[1].index: must equal its array position",
            ],
            "current-step-mismatch.json": [
                "$.progress.currentStepId: must match "
                "$.progress.steps[currentStepIndex].stepId"
            ],
            "additional-field.json": [
                "$.learnerEmail: field is not supported"
            ],
        }
        for fixture_name, expected_issues in expected.items():
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(
                    v2_validator.EvidenceExportV2ValidationError
                ) as raised:
                    v2_validator.load_and_validate(FIXTURE_DIR / fixture_name)
                self.assertEqual(expected_issues, list(raised.exception.issues))

    def test_revision_rejects_boolean_string_fractional_and_non_positive_values(self) -> None:
        for revision in (True, False, "1", 1.5, 0, -1):
            with self.subTest(revision=revision):
                data = self.clone_example()
                data["module"]["revision"] = revision
                self.assertIn(
                    "$.module.revision: must be a positive integer",
                    v2_validator.validate_evidence_export_v2(data),
                )

    def test_unknown_current_step_and_index_mismatch_fail_closed(self) -> None:
        data = self.clone_example()
        data["progress"]["currentStepId"] = "retired-concept"
        data["progress"]["currentStepIndex"] = 0
        issues = v2_validator.validate_evidence_export_v2(data)
        self.assertIn(
            "$.progress.currentStepId: must refer to an exported step", issues
        )
        self.assertIn(
            "$.progress.currentStepId: must match "
            "$.progress.steps[currentStepIndex].stepId",
            issues,
        )

    def test_step_count_and_current_index_must_be_consistent(self) -> None:
        data = self.clone_example()
        data["module"]["stepCount"] = 3
        data["progress"]["currentStepIndex"] = 4
        issues = v2_validator.validate_evidence_export_v2(data)
        self.assertIn(
            "$.progress.steps: length must match $.module.stepCount", issues
        )
        self.assertIn(
            "$.progress.currentStepIndex: must refer to an existing step", issues
        )

    def test_v1_and_v2_validators_do_not_accept_each_others_documents(self) -> None:
        v1_issues = v1_validator.validate_evidence_export(self.clone_example())
        self.assertIn("$.version: must be the integer 1", v1_issues)
        self.assertIn("$.module.revision: field is not supported", v1_issues)
        v2_issues = v2_validator.validate_evidence_export_v2(
            copy.deepcopy(self.v1_example)
        )
        self.assertIn("$.version: must be the integer 2", v2_issues)
        self.assertIn("$.module.revision: required field is missing", v2_issues)
        self.assertIn(
            "$.progress.currentStepId: required field is missing", v2_issues
        )

    def test_validation_is_side_effect_free(self) -> None:
        data = self.clone_example()
        original = copy.deepcopy(data)
        v2_validator.validate_evidence_export_v2(data)
        self.assertEqual(original, data)


if __name__ == "__main__":
    unittest.main()
