from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import classify_evidence_compatibility_v2 as classifier  # noqa: E402
import validate_evidence_export_v2 as evidence_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class EvidenceCompatibilityPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.target = module_validator.load_and_validate(
            ROOT / "tests" / "fixtures" / "module-identity" / "valid.json"
        )
        cls.evidence = evidence_validator.load_and_validate(
            ROOT / "tests" / "fixtures" / "evidence-v2-contextual" / "exact.json"
        )

    def test_exact_result_has_closed_read_only_preview(self) -> None:
        result = classifier.classify(self.evidence, self.target)
        self.assertEqual("exact", result["classification"])
        self.assertEqual("not-needed", result["manifestStatus"])
        self.assertFalse(result["candidateAvailable"])
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
        evidence = copy.deepcopy(self.evidence)
        evidence["module"]["revision"] = 7
        result = classifier.classify(evidence, self.target)
        self.assertEqual("incompatible", result["classification"])
        self.assertEqual("missing", result["manifestStatus"])
        self.assertFalse(result["candidateAvailable"])
        self.assertIn("non-exact transitions require", result["issues"][0])

    def test_partial_optional_context_is_rejected(self) -> None:
        result = classifier.classify(
            self.evidence,
            self.target,
            source_module=self.target,
        )
        self.assertEqual("incompatible", result["classification"])
        self.assertEqual("missing", result["manifestStatus"])
        self.assertIn("must be supplied together", result["issues"][0])

    def test_classifier_does_not_mutate_inputs(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        target = copy.deepcopy(self.target)
        originals = copy.deepcopy((evidence, target))
        classifier.classify(evidence, target)
        self.assertEqual(originals, (evidence, target))


if __name__ == "__main__":
    unittest.main()
