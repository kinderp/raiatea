from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

from validate_module_identity import validate_module_identity  # noqa: E402


class CanonicalModuleIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = {
            "id": "example-module",
            "revision": 1,
            "steps": [
                {"id": "orient-concept"},
                {"id": "apply-concept"},
            ],
        }

    def test_valid_revision_and_unique_step_ids(self) -> None:
        self.assertEqual([], validate_module_identity(self.module))

    def test_missing_revision_is_rejected(self) -> None:
        module = copy.deepcopy(self.module)
        del module["revision"]
        self.assertEqual(
            ["$.revision: required field is missing"],
            validate_module_identity(module),
        )

    def test_boolean_zero_negative_and_fractional_revisions_are_rejected(self) -> None:
        for revision in (True, False, 0, -1, 1.5):
            with self.subTest(revision=revision):
                module = copy.deepcopy(self.module)
                module["revision"] = revision
                self.assertIn(
                    "$.revision: must be a positive integer",
                    validate_module_identity(module),
                )

    def test_missing_and_malformed_step_ids_report_exact_paths(self) -> None:
        module = copy.deepcopy(self.module)
        del module["steps"][0]["id"]
        module["steps"][1]["id"] = "Bad_ID"
        self.assertEqual(
            [
                "$.steps[0].id: required field is missing",
                "$.steps[1].id: must contain only lowercase letters, digits, and hyphens",
            ],
            validate_module_identity(module),
        )

    def test_duplicate_step_ids_are_rejected(self) -> None:
        module = copy.deepcopy(self.module)
        module["steps"][1]["id"] = module["steps"][0]["id"]
        self.assertEqual(
            ["$.steps[1].id: duplicate step id 'orient-concept'"],
            validate_module_identity(module),
        )

    def test_validation_is_side_effect_free(self) -> None:
        original = copy.deepcopy(self.module)
        validate_module_identity(self.module)
        self.assertEqual(original, self.module)


if __name__ == "__main__":
    unittest.main()
