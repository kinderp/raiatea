from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-manifest"
sys.path.insert(0, str(BUILD_DIR))

import validate_evidence_migration_manifest as manifest_validator  # noqa: E402


class MigrationManifestDuplicateInventoryTests(unittest.TestCase):
    def test_duplicate_source_and_target_inventories_fail_at_exact_paths(self) -> None:
        expected = {
            "duplicate-source-id.json": [
                "$.source.stepIds[1]: duplicate step ID 'orient'"
            ],
            "duplicate-target-id.json": [
                "$.target.stepIds[1]: duplicate step ID 'orient'"
            ],
        }
        for fixture_name, expected_issues in expected.items():
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(
                    manifest_validator.MigrationManifestValidationError
                ) as raised:
                    manifest_validator.load_and_validate(FIXTURE_DIR / fixture_name)
                self.assertEqual(expected_issues, list(raised.exception.issues))


if __name__ == "__main__":
    unittest.main()
