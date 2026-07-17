from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import validate_evidence_export as validator  # noqa: E402


class LearnerEvidenceExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example_path = (
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))
        cls.schema = json.loads(
            (ROOT / "schema" / "learner-evidence-export-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def clone_example(self) -> dict:
        return json.loads(json.dumps(self.example))

    def test_example_matches_export_contract(self) -> None:
        self.assertEqual([], validator.validate_evidence_export(self.clone_example()))
        loaded = validator.load_and_validate(self.example_path)
        self.assertEqual("raiatea-learner-evidence", loaded["format"])
        self.assertEqual(1, loaded["version"])

    def test_schema_keeps_contract_closed_and_versioned(self) -> None:
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(
            "raiatea-learner-evidence",
            self.schema["properties"]["format"]["const"],
        )
        self.assertEqual(1, self.schema["properties"]["version"]["const"])
        self.assertFalse(
            self.schema["properties"]["module"]["additionalProperties"]
        )
        self.assertFalse(
            self.schema["properties"]["progress"]["additionalProperties"]
        )
        step_schema = self.schema["properties"]["progress"]["properties"]["steps"][
            "items"
        ]
        self.assertFalse(step_schema["additionalProperties"])

    def test_unrelated_or_identity_fields_are_rejected(self) -> None:
        data = self.clone_example()
        data["learnerEmail"] = "learner@example.test"
        data["module"]["readingSettings"] = {"theme": "dark"}
        issues = "\n".join(validator.validate_evidence_export(data))
        self.assertIn("$.learnerEmail: field is not supported", issues)
        self.assertIn("$.module.readingSettings: field is not supported", issues)

    def test_version_must_be_integer_one(self) -> None:
        data = self.clone_example()
        data["version"] = True
        self.assertIn(
            "$.version: must be the integer 1",
            validator.validate_evidence_export(data),
        )

    def test_module_id_must_match_schema_pattern(self) -> None:
        data = self.clone_example()
        data["module"]["id"] = "Self Attention/Student"
        issues = "\n".join(validator.validate_evidence_export(data))
        self.assertIn(
            "module.id: must contain only lowercase letters, digits, and hyphens",
            issues,
        )

    def test_progress_must_match_module_step_count(self) -> None:
        data = self.clone_example()
        data["module"]["stepCount"] = 3
        data["progress"]["currentStep"] = 3
        issues = "\n".join(validator.validate_evidence_export(data))
        self.assertIn("currentStep: must refer to an existing step", issues)
        self.assertIn("length must match $.module.stepCount", issues)

    def test_step_fields_are_typed_and_indexed(self) -> None:
        data = self.clone_example()
        data["progress"]["steps"][0]["index"] = 2
        data["progress"]["steps"][0]["attempts"] = -1
        data["progress"]["steps"][0]["correct"] = 1
        issues = "\n".join(validator.validate_evidence_export(data))
        self.assertIn("index: must equal its array position", issues)
        self.assertIn("attempts: must be a non-negative integer", issues)
        self.assertIn("correct: must be a boolean", issues)


if __name__ == "__main__":
    unittest.main()
