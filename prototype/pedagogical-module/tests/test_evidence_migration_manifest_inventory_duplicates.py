from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-manifest"
sys.path.insert(0, str(BUILD_DIR))

import validate_evidence_migration_manifest as manifest_validator  # noqa: E402


class LearnerEvidenceMigrationManifestInventoryDuplicateTests(unittest.TestCase):
    def test_duplicate_source_inventory_reports_only_the_exact_duplicate_path(self) -> None:
        with self.assertRaises(
            manifest_validator.MigrationManifestValidationError
        ) as raised:
            manifest_validator.load_and_validate(
                FIXTURE_DIR / "duplicate-source-id.json"
            )
        self.assertEqual(
            ["$.source.stepIds[1]: duplicate step ID 'orient'"],
            list(raised.exception.issues),
        )

    def test_duplicate_target_inventory_reports_only_the_exact_duplicate_path(self) -> None:
        with self.assertRaises(
            manifest_validator.MigrationManifestValidationError
        ) as raised:
            manifest_validator.load_and_validate(
                FIXTURE_DIR / "duplicate-target-id.json"
            )
        self.assertEqual(
            ["$.target.stepIds[1]: duplicate step ID 'orient'"],
            list(raised.exception.issues),
        )


if __name__ == "__main__":
    unittest.main()
