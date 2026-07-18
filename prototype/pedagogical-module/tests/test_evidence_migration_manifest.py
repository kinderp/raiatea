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
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-manifest"
sys.path.insert(0, str(BUILD_DIR))

import check_evidence_compatibility as v1_checker  # noqa: E402
import check_evidence_compatibility_v2 as v2_checker  # noqa: E402
import validate_evidence_export_v2 as v2_validator  # noqa: E402
import validate_evidence_migration_manifest as manifest_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class LearnerEvidenceMigrationManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example_path = (
            ROOT
            / "evidence-examples"
            / "learner-evidence-migration-manifest-v1.json"
        )
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))
        cls.schema = json.loads(
            (
                ROOT
                / "schema"
                / "learner-evidence-migration-manifest-v1.schema.json"
            ).read_text(encoding="utf-8")
        )

    def clone_example(self) -> dict:
        return copy.deepcopy(self.example)

    def test_example_and_valid_fixture_pass(self) -> None:
        self.assertEqual(
            [], manifest_validator.validate_migration_manifest(self.clone_example())
        )
        loaded = manifest_validator.load_and_validate(self.example_path)
        self.assertEqual(1, loaded["version"])
        fixture = manifest_validator.load_and_validate(FIXTURE_DIR / "valid.json")
        self.assertEqual("fixture-module", fixture["source"]["moduleId"])

    def test_schema_is_closed_and_uses_only_initial_operations(self) -> None:
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(
            "raiatea-learner-evidence-migration",
            self.schema["properties"]["format"]["const"],
        )
        self.assertEqual(1, self.schema["properties"]["version"]["const"])
        endpoint = self.schema["$defs"]["endpoint"]
        self.assertFalse(endpoint["additionalProperties"])
        self.assertTrue(endpoint["properties"]["stepIds"]["uniqueItems"])
        operations = self.schema["properties"]["operations"]
        self.assertFalse(operations["additionalProperties"])
        self.assertEqual(
            {"preserve", "retire", "introduce"},
            set(operations["required"]),
        )
        preserve = operations["properties"]["preserve"]["items"]
        self.assertFalse(preserve["additionalProperties"])
        self.assertEqual(
            {"sourceStepId", "targetStepId"}, set(preserve["required"])
        )

    def test_invalid_fixtures_report_deterministic_reasons(self) -> None:
        expected = {
            "same-revision.json": [
                "$.target.revision: must differ from $.source.revision"
            ],
            "cross-module.json": [
                "$.target.moduleId: must match $.source.moduleId"
            ],
            "fan-out.json": [
                "$.operations.preserve: source step ID 'source-step' is preserved more than once",
                "$.operations: source step ID 'source-step' is covered more than once",
            ],
            "fan-in.json": [
                "$.operations.preserve: target step ID 'target-step' is preserved more than once",
                "$.operations: target step ID 'target-step' is covered more than once",
            ],
            "missing-coverage.json": [
                "$.operations: source step ID 'legacy' is not covered",
                "$.operations: target step ID 'new-step' is not covered",
            ],
            "unsupported-operation.json": [
                "$.operations.merge: field is not supported",
                "$.operations: source step ID 'source-a' is not covered",
                "$.operations: source step ID 'source-b' is not covered",
                "$.operations: target step ID 'target-step' is not covered",
            ],
            "additional-field.json": [
                "$.learnerEmail: field is not supported"
            ],
            "malformed-id.json": [
                "$.source.stepIds[0]: must contain only lowercase letters, digits, and hyphens",
                "$.operations.preserve[0].sourceStepId: must contain only lowercase letters, digits, and hyphens",
                "$.operations: target step ID 'target-step' is not covered",
            ],
            "noncanonical-order.json": [
                "$.operations.preserve: entries must follow $.source.stepIds order"
            ],
        }
        for fixture_name, expected_issues in expected.items():
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(
                    manifest_validator.MigrationManifestValidationError
                ) as raised:
                    manifest_validator.load_and_validate(FIXTURE_DIR / fixture_name)
                self.assertEqual(expected_issues, list(raised.exception.issues))

    def test_revisions_reject_boolean_string_fractional_and_non_positive_values(self) -> None:
        for field in ("source", "target"):
            for revision in (True, False, "1", 1.5, 0, -1):
                with self.subTest(field=field, revision=revision):
                    data = self.clone_example()
                    data[field]["revision"] = revision
                    self.assertIn(
                        f"$.{field}.revision: must be a positive integer",
                        manifest_validator.validate_migration_manifest(data),
                    )

    def test_duplicate_inventory_and_cross_operation_coverage_fail_closed(self) -> None:
        data = self.clone_example()
        data["source"]["stepIds"].append("orient-concept")
        data["operations"]["retire"].append("orient-concept")
        issues = manifest_validator.validate_migration_manifest(data)
        self.assertIn(
            "$.source.stepIds[3]: duplicate step ID 'orient-concept'", issues
        )
        self.assertIn(
            "$.operations: source step ID 'orient-concept' is covered more than once",
            issues,
        )

    def test_unknown_references_fail_closed(self) -> None:
        data = self.clone_example()
        data["operations"]["preserve"][0]["sourceStepId"] = "unknown-source"
        data["operations"]["introduce"][0] = "unknown-target"
        issues = manifest_validator.validate_migration_manifest(data)
        self.assertIn(
            "$.operations.preserve[0].sourceStepId: unknown source step ID 'unknown-source'",
            issues,
        )
        self.assertIn(
            "$.operations.introduce[0]: unknown target step ID 'unknown-target'",
            issues,
        )

    def test_validation_is_side_effect_free(self) -> None:
        data = self.clone_example()
        original = copy.deepcopy(data)
        manifest_validator.validate_migration_manifest(data)
        self.assertEqual(original, data)

    def test_malformed_json_and_cli_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            malformed = Path(directory) / "manifest.json"
            malformed.write_text('{"format":', encoding="utf-8")
            with self.assertRaises(
                manifest_validator.MigrationManifestValidationError
            ) as raised:
                manifest_validator.load_and_validate(malformed)
            self.assertIn("invalid JSON", raised.exception.issues[0])

        validator = BUILD_DIR / "validate_evidence_migration_manifest.py"
        success = subprocess.run(
            [sys.executable, str(validator), str(FIXTURE_DIR / "valid.json")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, success.returncode, success.stderr)
        self.assertIn("Valid migration manifest", success.stdout)

        failure = subprocess.run(
            [
                sys.executable,
                str(validator),
                str(FIXTURE_DIR / "same-revision.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, failure.returncode)
        self.assertIn("must differ from $.source.revision", failure.stdout)
        for forbidden in ("older", "newer", "previous", "next", "higher", "lower"):
            self.assertNotIn(forbidden, failure.stdout.lower())

    def test_existing_evidence_contracts_remain_green(self) -> None:
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
            ROOT
            / "tests"
            / "fixtures"
            / "evidence-v2-contextual"
            / "exact.json"
        )
        self.assertEqual(
            [], v2_checker.check_exact_compatibility(v2_module, v2_evidence)
        )


if __name__ == "__main__":
    unittest.main()
