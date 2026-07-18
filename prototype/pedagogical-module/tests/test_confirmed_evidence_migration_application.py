from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(BUILD_DIR))

import apply_confirmed_evidence_migration_v2 as application  # noqa: E402
import check_evidence_compatibility_v2 as exact_checker  # noqa: E402
import validate_evidence_export_v2 as evidence_validator  # noqa: E402
import validate_evidence_migration_manifest as manifest_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class ConfirmedEvidenceMigrationApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        migration_context = FIXTURE_DIR / "evidence-migration-context"
        migration_preview = FIXTURE_DIR / "evidence-migration-preview"
        cls.source = module_validator.load_and_validate(
            migration_context / "exact-source.json"
        )
        cls.lossless_target = module_validator.load_and_validate(
            migration_preview / "lossless-target.json"
        )
        cls.lossless_manifest = manifest_validator.load_and_validate(
            migration_preview / "lossless-manifest.json"
        )
        cls.evidence = evidence_validator.load_and_validate(
            migration_preview / "source-current-preserved.json"
        )
        cls.exact_target = module_validator.load_and_validate(
            FIXTURE_DIR / "module-identity" / "valid.json"
        )
        cls.exact_evidence = evidence_validator.load_and_validate(
            FIXTURE_DIR / "evidence-v2-contextual" / "exact.json"
        )

    def _prepare(self, **overrides: object) -> dict:
        values = {
            "evidence": self.evidence,
            "target_module": self.lossless_target,
            "source_module": self.source,
            "manifest": self.lossless_manifest,
        }
        values.update(overrides)
        return application.prepare_migration(
            values["evidence"],
            values["target_module"],
            source_module=values["source_module"],
            manifest=values["manifest"],
        )

    def test_prepare_and_confirmed_lossless_application_are_closed_and_independent(self) -> None:
        original_before = copy.deepcopy(self.evidence)
        preparation = self._prepare()
        self.assertEqual(
            {
                "contractVersion",
                "applicable",
                "classification",
                "source",
                "target",
                "manifestStatus",
                "currentPosition",
                "candidateDigest",
                "confirmationToken",
                "summary",
            },
            set(preparation),
        )
        self.assertEqual(1, preparation["contractVersion"])
        self.assertTrue(preparation["applicable"])
        self.assertEqual("declared-lossless", preparation["classification"])
        self.assertTrue(
            preparation["confirmationToken"].startswith("raiatea-confirm-v1:")
        )
        self.assertEqual(
            len("raiatea-confirm-v1:") + 64,
            len(preparation["confirmationToken"]),
        )
        self.assertTrue(preparation["candidateDigest"].startswith("sha256:"))

        result = application.apply_confirmed_migration(
            self.evidence,
            self.lossless_target,
            source_module=self.source,
            manifest=self.lossless_manifest,
            confirmed=True,
            confirmation_token=preparation["confirmationToken"],
        )
        self.assertEqual(
            {
                "contractVersion",
                "applied",
                "source",
                "target",
                "classification",
                "manifestStatus",
                "candidateDigest",
                "confirmationToken",
                "original",
                "migrated",
                "summary",
            },
            set(result),
        )
        self.assertTrue(result["applied"])
        self.assertEqual(original_before, self.evidence)
        self.assertEqual(original_before, result["original"])
        self.assertIsNot(result["original"], self.evidence)
        self.assertEqual(
            [], evidence_validator.validate_evidence_export_v2(result["migrated"])
        )
        self.assertEqual(
            [],
            exact_checker.check_exact_compatibility(
                self.lossless_target, result["migrated"]
            ),
        )

        result["original"]["progress"]["steps"][0]["attempts"] += 99
        result["migrated"]["progress"]["steps"][0]["attempts"] += 99
        result["source"]["revision"] = 999
        self.assertEqual(original_before, self.evidence)
        second = self._prepare()
        self.assertEqual(preparation, second)

    def test_token_is_deterministic_and_binds_complete_source_and_target_modules(self) -> None:
        first = self._prepare()
        repeated = self._prepare(
            evidence=copy.deepcopy(self.evidence),
            target_module=copy.deepcopy(self.lossless_target),
            source_module=copy.deepcopy(self.source),
            manifest=copy.deepcopy(self.lossless_manifest),
        )
        self.assertEqual(first, repeated)

        changed_source = copy.deepcopy(self.source)
        changed_source["route"]["summary"] += " Changed after preparation."
        source_preparation = self._prepare(source_module=changed_source)
        self.assertNotEqual(
            first["confirmationToken"], source_preparation["confirmationToken"]
        )

        changed_target = copy.deepcopy(self.lossless_target)
        changed_target["route"]["summary"] += " Changed after preparation."
        target_preparation = self._prepare(target_module=changed_target)
        self.assertNotEqual(
            first["confirmationToken"], target_preparation["confirmationToken"]
        )
        self.assertEqual(first["candidateDigest"], target_preparation["candidateDigest"])

    def test_confirmation_shape_staleness_and_malformed_inputs_fail_closed(self) -> None:
        preparation = self._prepare()
        original = copy.deepcopy(self.evidence)
        cases = (
            {"confirmed": False, "confirmation_token": preparation["confirmationToken"]},
            {"confirmed": True, "confirmation_token": None},
            {"confirmed": True, "confirmation_token": "0" * 64},
            {"confirmed": True, "confirmation_token": "raiatea-confirm-v1:not-hex"},
        )
        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(application.EvidenceMigrationApplicationError):
                    application.apply_confirmed_migration(
                        self.evidence,
                        self.lossless_target,
                        source_module=self.source,
                        manifest=self.lossless_manifest,
                        **values,
                    )
                self.assertEqual(original, self.evidence)

        changed_source = copy.deepcopy(self.source)
        changed_source["route"]["summary"] += " Stale source."
        with self.assertRaises(application.EvidenceMigrationApplicationError) as stale:
            application.apply_confirmed_migration(
                self.evidence,
                self.lossless_target,
                source_module=changed_source,
                manifest=self.lossless_manifest,
                confirmed=True,
                confirmation_token=preparation["confirmationToken"],
            )
        self.assertIn("does not match current preparation", str(stale.exception))

        with self.assertRaises(application.EvidenceMigrationApplicationError) as malformed:
            application.prepare_migration(
                {},
                self.lossless_target,
                source_module=self.source,
                manifest=self.lossless_manifest,
            )
        self.assertTrue(malformed.exception.issues[0].startswith("$.evidence"))

        with self.assertRaises(application.EvidenceMigrationApplicationError) as partial:
            application.prepare_migration(
                self.evidence,
                self.lossless_target,
                source_module=self.source,
                manifest=None,
            )
        self.assertEqual(
            ["$.migrationContext: sourceModule and manifest must be supplied together"],
            list(partial.exception.issues),
        )

    def test_exact_and_incompatible_results_are_refused_without_mutation(self) -> None:
        original = copy.deepcopy(self.exact_evidence)
        with self.assertRaises(application.EvidenceMigrationApplicationError) as exact:
            application.prepare_migration(self.exact_evidence, self.exact_target)
        self.assertIn("requires no migration", str(exact.exception))
        self.assertEqual(original, self.exact_evidence)

        different_route = copy.deepcopy(self.lossless_target)
        different_route["id"] = "different-route"
        with self.assertRaises(application.EvidenceMigrationApplicationError) as incompatible:
            application.prepare_migration(
                self.evidence,
                different_route,
                source_module=self.source,
                manifest=self.lossless_manifest,
            )
        self.assertIn("only declared-lossless or declared-partial", str(incompatible.exception))

    def test_public_results_exclude_operational_and_identity_metadata(self) -> None:
        preparation = self._prepare()
        result = application.apply_confirmed_migration(
            self.evidence,
            self.lossless_target,
            source_module=self.source,
            manifest=self.lossless_manifest,
            confirmed=True,
            confirmation_token=preparation["confirmationToken"],
        )
        serialized = json.dumps(result, sort_keys=True).lower()
        for forbidden in (
            "timestamp",
            "pathname",
            "filesystem",
            "browserstorage",
            "localstorage",
            "learnername",
            "accountid",
            "telemetry",
            "analytics",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
