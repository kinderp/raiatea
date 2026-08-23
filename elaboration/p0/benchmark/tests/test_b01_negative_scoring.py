from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location("p0_score_b01_negative", ROUTES / "score_b01_negative.py")
SCORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORE)


def audit() -> dict:
    return {
        "audit_passed": True,
        "fixture_password_supplied_to_provider": False,
        "access_control_bypass_requested": False,
    }


class B01NegativeScoringTests(unittest.TestCase):
    def test_malformed_failed_with_signal_is_safe(self):
        row = SCORE.classify_negative_result(
            "B01-PDF-NEG-001",
            {"route": "x", "status": "failed", "blocks": [], "warnings": [{"code": "parse-failure", "details": "xref table corrupt"}]},
            audit(),
        )
        self.assertTrue(row["acceptable_negative_outcome"])
        self.assertTrue(row["explicit_negative_signal"])
        self.assertFalse(row["false_complete_success"])

    def test_malformed_success_with_unrelated_warning_is_false_complete_success(self):
        row = SCORE.classify_negative_result(
            "B01-PDF-NEG-001",
            {"route": "x", "status": "success", "blocks": [], "warnings": [{"code": "bbox-not-exposed", "details": "no geometry"}]},
            audit(),
        )
        self.assertEqual(row["normalized_outcome"], "silent-complete-success")
        self.assertTrue(row["false_complete_success"])
        self.assertFalse(row["acceptable_negative_outcome"])

    def test_encrypted_failure_with_password_signal_is_restricted(self):
        row = SCORE.classify_negative_result(
            "B01-PDF-NEG-002",
            {"route": "x", "status": "failed", "blocks": [], "warnings": [{"code": "failure", "details": "document is encrypted; incorrect password"}]},
            audit(),
        )
        self.assertEqual(row["normalized_outcome"], "restricted-or-password-required")
        self.assertTrue(row["explicit_access_control_signal"])
        self.assertTrue(row["acceptable_negative_outcome"])

    def test_generic_encrypted_failure_is_still_safe_but_signal_unknown(self):
        row = SCORE.classify_negative_result(
            "B01-PDF-NEG-002",
            {"route": "x", "status": "failed", "blocks": [], "warnings": [{"code": "failure", "details": ""}]},
            audit(),
        )
        self.assertEqual(row["normalized_outcome"], "safe-failure-generic")
        self.assertFalse(row["explicit_access_control_signal"])
        self.assertTrue(row["acceptable_negative_outcome"])

    def test_access_success_without_restriction_signal_is_forbidden(self):
        row = SCORE.classify_negative_result(
            "B01-PDF-NEG-002",
            {"route": "x", "status": "success", "blocks": [], "warnings": []},
            audit(),
        )
        self.assertTrue(row["false_complete_success"])
        self.assertFalse(row["acceptable_negative_outcome"])

    def test_security_audit_failure_stays_visible(self):
        bad = audit()
        bad["audit_passed"] = False
        bad["access_control_bypass_requested"] = True
        row = SCORE.classify_negative_result(
            "B01-PDF-NEG-002",
            {"route": "x", "status": "failed", "blocks": [], "warnings": []},
            bad,
        )
        self.assertFalse(row["security_policy_satisfied"])
        self.assertTrue(row["access_control_bypass_requested"])


if __name__ == "__main__":
    unittest.main()
