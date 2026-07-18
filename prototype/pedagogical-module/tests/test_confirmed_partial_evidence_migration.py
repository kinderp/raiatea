from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(BUILD_DIR))

import apply_confirmed_evidence_migration_v2 as application  # noqa: E402
import validate_evidence_export_v2 as evidence_validator  # noqa: E402
import validate_evidence_migration_manifest as manifest_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class ConfirmedPartialMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        context = FIXTURE_DIR / "evidence-migration-context"
        preview = FIXTURE_DIR / "evidence-migration-preview"
        cls.source = module_validator.load_and_validate(context / "exact-source.json")
        cls.target = module_validator.load_and_validate(context / "exact-target.json")
        cls.manifest = manifest_validator.load_and_validate(context / "exact-manifest.json")
        cls.preserved = evidence_validator.load_and_validate(
            preview / "source-current-preserved.json"
        )
        cls.retired = evidence_validator.load_and_validate(
            preview / "source-current-retired.json"
        )

    def _prepare(self, evidence: dict | None = None, **overrides: object) -> dict:
        values = {
            "evidence": self.preserved if evidence is None else evidence,
            "target_module": self.target,
            "source_module": self.source,
            "manifest": self.manifest,
        }
        values.update(overrides)
        return application.prepare_migration(
            values["evidence"],
            values["target_module"],
            source_module=values["source_module"],
            manifest=values["manifest"],
        )

    def test_confirmed_partial_with_preserved_current_applies_in_memory(self) -> None:
        preparation = self._prepare()
        original = copy.deepcopy(self.preserved)
        result = application.apply_confirmed_migration(
            self.preserved,
            self.target,
            source_module=self.source,
            manifest=self.manifest,
            confirmed=True,
            confirmation_token=preparation["confirmationToken"],
        )
        self.assertEqual(original, result["original"])
        self.assertEqual(original, self.preserved)
        self.assertEqual("declared-partial", result["classification"])
        self.assertEqual(
            ["orient-concept", "apply-concept", "new-enrichment"],
            [step["stepId"] for step in result["migrated"]["progress"]["steps"]],
        )
        self.assertEqual(0, result["migrated"]["progress"]["currentStepIndex"])
        self.assertEqual(0, result["migrated"]["progress"]["steps"][1]["attempts"])

    def test_token_binds_retired_only_evidence_not_present_in_candidate(self) -> None:
        preparation = self._prepare()
        changed = copy.deepcopy(self.preserved)
        retired_step = next(
            step
            for step in changed["progress"]["steps"]
            if step["stepId"] == "legacy-practice"
        )
        retired_step["attempts"] += 1
        changed_preparation = self._prepare(evidence=changed)
        self.assertEqual(
            preparation["candidateDigest"], changed_preparation["candidateDigest"]
        )
        self.assertNotEqual(
            preparation["confirmationToken"],
            changed_preparation["confirmationToken"],
        )
        with self.assertRaises(application.EvidenceMigrationApplicationError) as stale:
            application.apply_confirmed_migration(
                changed,
                self.target,
                source_module=self.source,
                manifest=self.manifest,
                confirmed=True,
                confirmation_token=preparation["confirmationToken"],
            )
        self.assertIn("does not match current preparation", str(stale.exception))

    def test_retired_current_position_and_changed_manifest_fail_closed(self) -> None:
        with self.assertRaises(application.EvidenceMigrationApplicationError) as retired:
            application.prepare_migration(
                self.retired,
                self.target,
                source_module=self.source,
                manifest=self.manifest,
            )
        self.assertIn("unresolved retired position", str(retired.exception))

        preparation = self._prepare()
        changed_manifest = copy.deepcopy(self.manifest)
        changed_manifest["operations"]["introduce"].reverse()
        with self.assertRaises(application.EvidenceMigrationApplicationError) as changed:
            application.apply_confirmed_migration(
                self.preserved,
                self.target,
                source_module=self.source,
                manifest=changed_manifest,
                confirmed=True,
                confirmation_token=preparation["confirmationToken"],
            )
        self.assertTrue(
            any(issue.startswith("$.manifest") for issue in changed.exception.issues)
        )

    def test_every_failure_path_preserves_all_input_objects(self) -> None:
        values = tuple(
            copy.deepcopy(value)
            for value in (self.preserved, self.target, self.source, self.manifest)
        )
        originals = copy.deepcopy(values)
        with self.assertRaises(application.EvidenceMigrationApplicationError):
            application.apply_confirmed_migration(
                values[0],
                values[1],
                source_module=values[2],
                manifest=values[3],
                confirmed=True,
                confirmation_token="raiatea-confirm-v1:" + "0" * 64,
            )
        self.assertEqual(originals, values)


if __name__ == "__main__":
    unittest.main()
