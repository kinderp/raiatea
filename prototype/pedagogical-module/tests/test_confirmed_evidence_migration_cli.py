from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURES = ROOT / "tests" / "fixtures"
CONTEXT = FIXTURES / "evidence-migration-context"
PREVIEW = FIXTURES / "evidence-migration-preview"


class ConfirmedEvidenceMigrationCliTests(unittest.TestCase):
    def test_prepare_and_apply_round_trip(self) -> None:
        cli = BUILD_DIR / "confirm_evidence_migration_v2.py"
        common = [
            str(PREVIEW / "source-current-preserved.json"),
            str(PREVIEW / "lossless-target.json"),
            str(CONTEXT / "exact-source.json"),
            str(PREVIEW / "lossless-manifest.json"),
        ]
        prepared = subprocess.run(
            [sys.executable, str(cli), "prepare", *common, "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, prepared.returncode, prepared.stderr)
        preparation = json.loads(prepared.stdout)
        self.assertFalse(preparation["applied"])
        self.assertTrue(preparation["candidateAvailable"])

        applied = subprocess.run(
            [
                sys.executable,
                str(cli),
                "apply",
                *common,
                "--confirm-digest",
                preparation["confirmationDigest"],
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, applied.returncode, applied.stderr)
        result = json.loads(applied.stdout)
        self.assertTrue(result["applied"])
        self.assertEqual("declared-lossless", result["classification"])
        self.assertEqual(
            preparation["confirmationDigest"], result["confirmationDigest"]
        )

    def test_apply_rejects_missing_digest(self) -> None:
        cli = BUILD_DIR / "confirm_evidence_migration_v2.py"
        result = subprocess.run(
            [
                sys.executable,
                str(cli),
                "apply",
                str(PREVIEW / "source-current-preserved.json"),
                str(PREVIEW / "lossless-target.json"),
                str(CONTEXT / "exact-source.json"),
                str(PREVIEW / "lossless-manifest.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("confirmation digest is required", result.stdout)


if __name__ == "__main__":
    unittest.main()
