from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
REPO_ROOT = ROOT.parents[2]
RIGHTS_OVERLAY = ROOT / "manifests" / "redistribution-rights.json"
FIXTURE_MANIFEST = ROOT / "manifests" / "fixtures.json"
LICENSING = ROOT / "LICENSING.md"
NOTICE = ROOT / "NOTICE.md"

EXPECTED_FIXTURES = {
    "B01-PDF-001",
    "B01-PDF-002",
    "B01-PDF-003",
    "B01-PDF-004",
    "B01-PDF-005",
    "B01-PDF-006",
    "B01-PDF-007",
    "B01-PDF-NEG-001",
    "B01-PDF-NEG-002",
    "B02-EPUB-001",
    "B02-EPUB-002",
    "B02-EPUB-NEG-001",
    "B02-EPUB-NEG-002",
}

EXPECTED_GENERATORS = {
    "elaboration/p0/benchmark/generate_fixtures.py",
    "elaboration/p0/benchmark/b01_pdf_007_fixture.py",
    "elaboration/p0/benchmark/b01_pdf_negative_fixtures.py",
}


class BenchmarkLicensingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rights = json.loads(RIGHTS_OVERLAY.read_text(encoding="utf-8"))
        cls.historical = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
        cls.licensing_text = LICENSING.read_text(encoding="utf-8")
        cls.notice_text = NOTICE.read_text(encoding="utf-8")

    def test_decision_is_benchmark_scoped_and_pinned_to_issue_131(self) -> None:
        contract = self.rights["contract"]
        self.assertEqual(contract["name"], "raiatea-p0-benchmark-redistribution-rights")
        self.assertEqual(contract["version"], "1.0.0")
        self.assertEqual(contract["decision_issue"], 131)
        self.assertEqual(contract["decision_date"], "2026-08-25")
        self.assertFalse(contract["repository_wide_license_decision"])
        self.assertIn("benchmark-only", self.licensing_text)
        self.assertIn("does not license the Raiatea repository as a whole", self.licensing_text)

    def test_fixture_and_gold_policy_is_cc_by_4(self) -> None:
        policy = self.rights["policy"]
        self.assertEqual(policy["fixture_and_gold_license"], "CC-BY-4.0")
        self.assertTrue(policy["attribution_required"])
        self.assertIn("Raiatea P0 Benchmark", policy["attribution"])
        self.assertEqual(self.rights["gold_reference_data"]["license"], "CC-BY-4.0")
        self.assertTrue(self.rights["gold_reference_data"]["public_rights_safe"])
        self.assertTrue(self.rights["gold_reference_data"]["attribution_required"])
        self.assertIn("CC BY 4.0", self.notice_text)

    def test_all_current_project_fixture_ids_have_explicit_cc_by_rights(self) -> None:
        records = self.rights["fixtures"]
        ids = [record["id"] for record in records]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), EXPECTED_FIXTURES)
        for record in records:
            with self.subTest(fixture=record["id"]):
                self.assertEqual(record["redistribution"], "CC-BY-4.0")
                self.assertTrue(record["public_rights_safe"])
                self.assertTrue(record["attribution_required"])
                self.assertEqual(record["remote_provider"], "denied")

    def test_generator_license_is_apache_only_for_exact_declared_paths(self) -> None:
        policy = self.rights["policy"]
        self.assertEqual(policy["generator_code_license"], "Apache-2.0")
        self.assertEqual(set(policy["generator_paths"]), EXPECTED_GENERATORS)
        self.assertIn("Apache-2.0", self.licensing_text)
        self.assertIn("Apache License 2.0", self.notice_text)
        for relative in EXPECTED_GENERATORS:
            self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_remote_provider_remains_denied(self) -> None:
        self.assertEqual(self.rights["policy"]["remote_provider"], "denied")
        self.assertIn("does not authorize externally hosted Provider processing", self.rights["policy"]["remote_provider_note"])
        self.assertIn("Remote/hosted Provider processing is not authorized", self.notice_text)

    def test_historical_manifest_is_preserved_not_rewritten_as_current_policy(self) -> None:
        boundary = self.rights["historical_evidence_boundary"]
        self.assertTrue(boundary["preserve_pinned_manifests"])
        self.assertEqual(self.historical["rights_gate"]["redistribution"], "not-established")
        self.assertIn("historical", boundary["note"].lower())
        self.assertIn("supersedes", boundary["note"].lower())

    def test_gold_and_fixture_manifest_paths_are_explicitly_covered(self) -> None:
        covered = set(self.rights["gold_reference_data"]["covered_paths"])
        self.assertEqual(
            covered,
            {
                "elaboration/p0/benchmark/manifests/gold.json",
                "elaboration/p0/benchmark/manifests/fixtures.json",
            },
        )

    def test_third_party_and_repository_scope_exclusions_remain_visible(self) -> None:
        exclusions = "\n".join(self.rights["explicit_exclusions"])
        self.assertIn("Raiatea Core", exclusions)
        self.assertIn("third-party", exclusions.lower())
        self.assertIn("private/non-distributable", exclusions)
        self.assertIn("Provider routes and scorers", exclusions)
        self.assertIn("does not license", self.licensing_text)


if __name__ == "__main__":
    unittest.main()
