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


class ConfirmedEvidenceMigrationTokenContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        context = FIXTURE_DIR / "evidence-migration-context"
        preview = FIXTURE_DIR / "evidence-migration-preview"
        cls.source = module_validator.load_and_validate(context / "exact-source.json")
        cls.target = module_validator.load_and_validate(preview / "lossless-target.json")
        cls.manifest = manifest_validator.load_and_validate(
            preview / "lossless-manifest.json"
        )
        cls.evidence = evidence_validator.load_and_validate(
            preview / "source-current-preserved.json"
        )

    def test_uppercase_hex_confirmation_is_malformed_and_side_effect_free(self) -> None:
        preparation = application.prepare_migration(
            self.evidence,
            self.target,
            source_module=self.source,
            manifest=self.manifest,
        )
        uppercase_token = preparation["confirmationToken"].upper()
        originals = tuple(
            copy.deepcopy(value)
            for value in (self.evidence, self.target, self.source, self.manifest)
        )

        with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
            application.apply_confirmed_migration(
                self.evidence,
                self.target,
                source_module=self.source,
                manifest=self.manifest,
                confirmed=True,
                confirmation_token=uppercase_token,
            )

        self.assertEqual(
            ["$.confirmation.token: malformed confirmation token"],
            list(raised.exception.issues),
        )
        self.assertEqual(
            originals,
            (self.evidence, self.target, self.source, self.manifest),
        )

    def test_unsupported_evidence_version_is_refused_before_classification(self) -> None:
        unsupported = copy.deepcopy(self.evidence)
        unsupported["version"] = 99
        original = copy.deepcopy(unsupported)

        with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
            application.prepare_migration(
                unsupported,
                self.target,
                source_module=self.source,
                manifest=self.manifest,
            )

        self.assertTrue(
            any(issue.startswith("$.evidence.version") for issue in raised.exception.issues)
        )
        self.assertEqual(original, unsupported)


if __name__ == "__main__":
    unittest.main()
