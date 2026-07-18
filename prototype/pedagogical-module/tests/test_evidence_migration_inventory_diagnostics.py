from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import check_evidence_migration_manifest_context as context_checker  # noqa: E402


class MigrationInventoryDiagnosticTests(unittest.TestCase):
    def test_length_mismatch_reports_missing_and_unknown_ids(self) -> None:
        issue = context_checker._inventory_issue(
            "source",
            ["orient-concept"],
            ["orient-concept", "legacy-practice"],
            endpoint_identity_matches=True,
        )
        self.assertIn("inventory length 1", issue)
        self.assertIn("inventory length 2", issue)
        self.assertIn("missing IDs ['legacy-practice']", issue)
        self.assertIn("unknown IDs []", issue)

    def test_addition_reports_unknown_ids(self) -> None:
        issue = context_checker._inventory_issue(
            "target",
            ["orient-concept", "apply-concept", "unexpected-step"],
            ["orient-concept", "apply-concept"],
            endpoint_identity_matches=True,
        )
        self.assertIn("inventory length 3", issue)
        self.assertIn("inventory length 2", issue)
        self.assertIn("missing IDs []", issue)
        self.assertIn("unknown IDs ['unexpected-step']", issue)

    def test_equal_length_replacement_is_distinct_from_reorder(self) -> None:
        issue = context_checker._inventory_issue(
            "source",
            ["orient-concept", "replacement-step"],
            ["orient-concept", "legacy-practice"],
            endpoint_identity_matches=True,
        )
        self.assertIn("replaces canonical IDs", issue)
        self.assertIn("missing IDs ['legacy-practice']", issue)
        self.assertIn("unknown IDs ['replacement-step']", issue)
        self.assertNotIn("exact canonical IDs", issue)

    def test_pure_reorder_is_reported_without_missing_or_unknown_ids(self) -> None:
        issue = context_checker._inventory_issue(
            "target",
            ["apply-concept", "orient-concept"],
            ["orient-concept", "apply-concept"],
            endpoint_identity_matches=True,
        )
        self.assertIn("contains the exact canonical IDs", issue)
        self.assertIn("different order", issue)
        self.assertNotIn("missing IDs", issue)
        self.assertNotIn("unknown IDs", issue)

    def test_endpoint_identity_mismatch_keeps_conservative_generic_message(self) -> None:
        issue = context_checker._inventory_issue(
            "source",
            ["b", "a"],
            ["a", "b"],
            endpoint_identity_matches=False,
        )
        self.assertEqual(
            "$.manifest.source.stepIds: manifest source step IDs ['b', 'a'] "
            "do not match source module step IDs ['a', 'b']",
            issue,
        )


if __name__ == "__main__":
    unittest.main()
