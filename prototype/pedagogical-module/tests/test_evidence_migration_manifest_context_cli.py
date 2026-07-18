from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-context"
MODULE_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "module-identity"


class MigrationManifestContextCliTests(unittest.TestCase):
    def test_structural_failure_uses_distinct_heading_and_namespaced_path(self) -> None:
        checker = BUILD_DIR / "check_evidence_migration_manifest_context.py"
        result = subprocess.run(
            [
                sys.executable,
                str(checker),
                str(MODULE_FIXTURE_DIR / "missing-revision.json"),
                str(FIXTURE_DIR / "exact-target.json"),
                str(FIXTURE_DIR / "unsupported-version.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn(
            "Migration manifest contextual input validation failed:", result.stdout
        )
        self.assertIn("$.sourceModule.revision:", result.stdout)
        self.assertIn("$.manifest.version:", result.stdout)
        self.assertNotIn(
            "Migration manifest does not match the supplied canonical revisions:",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
