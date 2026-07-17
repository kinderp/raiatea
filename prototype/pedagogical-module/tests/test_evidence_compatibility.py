from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import check_evidence_compatibility as compatibility  # noqa: E402
import validate_evidence_export as evidence_validator  # noqa: E402


class LearnerEvidenceCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module_path = ROOT / "examples" / "self-attention.json"
        cls.evidence_path = (
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        cls.module = json.loads(cls.module_path.read_text(encoding="utf-8"))
        cls.evidence = json.loads(cls.evidence_path.read_text(encoding="utf-8"))

    def test_merged_example_is_compatible_with_current_module(self) -> None:
        module, evidence = compatibility.load_and_check(
            self.module_path, self.evidence_path
        )
        self.assertEqual("self-attention-orientation", module["id"])
        self.assertEqual([], compatibility.check_compatibility(module, evidence))

    def test_wrong_module_id_is_incompatible(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["module"]["id"] = "another-module"
        issues = compatibility.check_compatibility(self.module, evidence)
        self.assertEqual(1, len(issues))
        self.assertIn("does not match current module ID", issues[0])

    def test_step_count_and_sequence_length_must_match(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["module"]["stepCount"] = 3
        evidence["progress"]["currentStep"] = 0
        evidence["progress"]["steps"] = evidence["progress"]["steps"][:3]
        self.assertEqual([], evidence_validator.validate_evidence_export(evidence))
        issues = "\n".join(
            compatibility.check_compatibility(self.module, evidence)
        )
        self.assertIn("exported step count 3", issues)
        self.assertIn("exported step sequence length 3", issues)

    def test_ordered_step_titles_are_compatibility_keys(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["progress"]["steps"][1]["title"] = "Titolo cambiato"
        issues = compatibility.check_compatibility(self.module, evidence)
        self.assertEqual(1, len(issues))
        self.assertIn("$.progress.steps[1].title", issues[0])
        self.assertIn("Dal testo agli embedding", issues[0])

    def test_source_metadata_does_not_determine_compatibility(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["module"]["source"] = {
            "title": "Catalog record updated",
            "pages": [999],
        }
        self.assertEqual([], evidence_validator.validate_evidence_export(evidence))
        self.assertEqual(
            [], compatibility.check_compatibility(self.module, evidence)
        )

    def test_structural_validation_runs_before_compatibility(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["learnerEmail"] = "learner@example.test"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-evidence.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaises(evidence_validator.EvidenceExportValidationError):
                compatibility.load_and_check(self.module_path, path)


if __name__ == "__main__":
    unittest.main()
