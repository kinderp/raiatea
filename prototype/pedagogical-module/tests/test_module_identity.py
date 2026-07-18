from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "module-identity"
sys.path.insert(0, str(BUILD_DIR))

from validate_module_identity import validate_module_identity  # noqa: E402
from validate_module_v2 import ModuleValidationError, load_and_validate  # noqa: E402


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

    def test_schema_requires_revision_and_step_id(self) -> None:
        schema = json.loads(
            (ROOT / "schema" / "module.schema.json").read_text(encoding="utf-8")
        )
        self.assertIn("revision", schema["required"])
        self.assertEqual(
            {"type": "integer", "minimum": 1},
            schema["properties"]["revision"],
        )
        step_schema = schema["properties"]["steps"]["items"]
        self.assertIn("id", step_schema["required"])
        self.assertEqual(
            {"type": "string", "pattern": "^[a-z0-9-]+$"},
            step_schema["properties"]["id"],
        )

    def test_canonical_loader_accepts_valid_identity_fixture(self) -> None:
        loaded = load_and_validate(FIXTURE_DIR / "valid.json")
        self.assertEqual(1, loaded["revision"])
        self.assertEqual(
            ["orient-concept", "apply-concept"],
            [step["id"] for step in loaded["steps"]],
        )

    def test_canonical_loader_rejects_identity_fixtures_with_exact_paths(self) -> None:
        expected = {
            "missing-revision.json": ["$.revision: required field is missing"],
            "missing-step-id.json": ["$.steps[0].id: required field is missing"],
            "malformed-step-id.json": [
                "$.steps[0].id: must contain only lowercase letters, digits, and hyphens"
            ],
            "duplicate-step-id.json": [
                "$.steps[1].id: duplicate step id 'orient-concept'"
            ],
        }
        for fixture_name, expected_issues in expected.items():
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(ModuleValidationError) as raised:
                    load_and_validate(FIXTURE_DIR / fixture_name)
                self.assertEqual(
                    expected_issues,
                    [str(issue) for issue in raised.exception.issues],
                )

    def test_every_canonical_example_has_revision_and_unique_step_ids(self) -> None:
        example_paths = sorted(
            path
            for path in (ROOT / "examples").glob("*.json")
            if not path.name.endswith(".layout.json")
        )
        self.assertGreater(len(example_paths), 0)
        for path in example_paths:
            with self.subTest(example=path.name):
                module = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], validate_module_identity(module))
                self.assertEqual(1, module["revision"])

    def test_learner_evidence_v1_does_not_expose_revision_or_step_ids(self) -> None:
        evidence = json.loads(
            (ROOT / "evidence-examples" / "learner-evidence-export-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("revision", evidence["module"])
        self.assertNotIn("stepId", evidence["module"])
        for step in evidence["progress"]["steps"]:
            self.assertNotIn("id", step)
            self.assertNotIn("stepId", step)


if __name__ == "__main__":
    unittest.main()
