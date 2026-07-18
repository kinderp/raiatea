from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-context"
sys.path.insert(0, str(BUILD_DIR))

import check_evidence_migration_manifest_context as context_checker  # noqa: E402
import validate_evidence_migration_manifest as manifest_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class MigrationManifestRevisionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = module_validator.load_and_validate(
            FIXTURE_DIR / "exact-source.json"
        )
        cls.target = module_validator.load_and_validate(
            FIXTURE_DIR / "exact-target.json"
        )
        cls.manifest = manifest_validator.load_and_validate(
            FIXTURE_DIR / "exact-manifest.json"
        )

    def test_target_revision_mismatch_reports_exact_manifest_path(self) -> None:
        mismatched_target = module_validator.load_and_validate(
            FIXTURE_DIR / "target-revision-mismatch.json"
        )
        self.assertEqual(
            [
                "$.manifest.target.revision: manifest target revision '2' "
                "does not match target module revision '11'"
            ],
            context_checker.check_manifest_context(
                self.source, mismatched_target, self.manifest
            ),
        )

    def test_revision_values_are_compared_only_by_exact_equality(self) -> None:
        source = dict(self.source)
        target = dict(self.target)
        manifest = {
            **self.manifest,
            "source": {**self.manifest["source"], "revision": 40},
            "target": {**self.manifest["target"], "revision": 3},
        }
        source["revision"] = 40
        target["revision"] = 3

        self.assertEqual(
            [], context_checker.check_manifest_context(source, target, manifest)
        )


if __name__ == "__main__":
    unittest.main()
