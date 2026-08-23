from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = BENCH_DIR / "b01_pdf_negative_fixtures.py"
SPEC = importlib.util.spec_from_file_location("p0_b01_negative_fixtures", MODULE_PATH)
NEG = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(NEG)


class B01NegativePdfFixtureTests(unittest.TestCase):
    def setUp(self):
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "b01-pdf-negative-gold.json").read_text(
                encoding="utf-8"
            )
        )

    def test_valid_generator_source_identity_is_stable(self):
        source = NEG.build_valid_source_pdf()
        self.assertEqual(len(source), 613)
        self.assertEqual(
            hashlib.sha256(source).hexdigest(),
            "e66b63241563a4122883e9534b73fe9f71e4036a8e50648267db7fb09b5a8293",
        )
        self.assertTrue(source.endswith(b"%%EOF\n"))

    def test_neg001_is_deterministic_inert_truncation(self):
        first = NEG.build_malformed_pdf()
        second = NEG.build_malformed_pdf()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 376)
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            "803cdada146c89d6a86169351ed7a4b0a46c0afe99f5b08ea25f813d0c8d630d",
        )
        self.assertTrue(first.startswith(b"%PDF-1.4"))
        self.assertNotIn(b"endstream", first)
        self.assertNotIn(b"xref\n", first)
        self.assertNotIn(b"trailer\n", first)
        self.assertNotIn(b"startxref", first)
        self.assertNotIn(b"%%EOF", first)
        self.assertNotIn(b"/JavaScript", first)
        self.assertNotIn(b"/JS", first)
        self.assertNotIn(b"/Launch", first)
        self.assertNotIn(b"/EmbeddedFile", first)
        self.assertNotIn(b"/URI", first)

    def test_neg001_gold_matches_generator_and_is_excluded_from_quality_average(self):
        fixture = self.gold["fixtures"][NEG.NEG_MALFORMED_ID]
        payload = NEG.build_malformed_pdf()
        self.assertEqual(fixture["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(fixture["bytes"], len(payload))
        self.assertTrue(fixture["quality_dimensions_excluded"])
        self.assertEqual(fixture["forbidden_interpretation"], "silent-complete-success")

    def test_neg002_gold_is_pending_qpdf_gate_before_provider_measurement(self):
        fixture = self.gold["fixtures"][NEG.NEG_ACCESS_CONTROLLED_ID]
        self.assertIsNone(fixture["sha256"])
        self.assertIsNone(fixture["bytes"])
        self.assertIn("pending-qpdf-reproducibility", fixture["identity_state"])
        self.assertFalse(fixture["access_control"]["provider_password_supplied"])
        self.assertFalse(fixture["access_control"]["bypass_allowed"])
        self.assertTrue(fixture["quality_dimensions_excluded"])

    def test_qpdf_command_is_fixture_generation_only(self):
        command = NEG.access_controlled_qpdf_command(
            "/usr/bin/qpdf", Path("source.pdf"), Path("protected.pdf")
        )
        self.assertEqual(command[0], "/usr/bin/qpdf")
        self.assertIn("--static-id", command)
        self.assertIn("--static-aes-iv", command)
        self.assertIn("--encrypt", command)
        self.assertIn(NEG.FIXTURE_USER_PASSWORD, command)
        self.assertIn(NEG.FIXTURE_OWNER_PASSWORD, command)
        self.assertIn("128", command)
        self.assertIn("--use-aes=y", command)
        self.assertNotIn("256", command)
        self.assertNotIn("--decrypt", command)
        self.assertNotIn("--remove-restrictions", command)
        self.assertNotIn("-nodrm", command)

    def test_gold_forbids_password_and_bypass_on_measured_provider_routes(self):
        fixture = self.gold["fixtures"][NEG.NEG_ACCESS_CONTROLLED_ID]
        forbidden = set(fixture["forbidden_provider_options_or_behaviors"])
        self.assertIn("-nodrm", forbidden)
        self.assertIn("--password", forbidden)
        self.assertIn("--password-file", forbidden)
        self.assertIn("--decrypt", forbidden)
        self.assertIn("--remove-restrictions", forbidden)
        self.assertFalse(self.gold["measurement_policy"]["access_control_bypass"])
        self.assertFalse(
            self.gold["measurement_policy"]["credential_or_password_supplied_to_provider"]
        )

    def test_negative_fixtures_are_outside_normal_quality_averages(self):
        self.assertTrue(
            self.gold["contract"]["excluded_from_normal_quality_averages"]
        )
        for fixture in self.gold["fixtures"].values():
            self.assertTrue(fixture["quality_dimensions_excluded"])


if __name__ == "__main__":
    unittest.main()
