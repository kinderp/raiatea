from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_b01_negative_raw", ROUTES / "measure_b01_negative_raw.py"
)
RAW = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RAW)


class B01NegativeRawRunnerTests(unittest.TestCase):
    def test_normal_poppler_options_pass_without_password_or_bypass(self):
        audit = RAW.audit_provider_invocation(
            {
                "command_options": [
                    "-xml",
                    "-hidden",
                    "-q",
                    "/controlled/input.pdf",
                    "/controlled/out",
                ]
            }
        )
        self.assertTrue(audit["audit_passed"])
        self.assertFalse(audit["fixture_password_supplied_to_provider"])
        self.assertFalse(audit["access_control_bypass_requested"])
        self.assertEqual(audit["forbidden_option_hits"], [])

    def test_nodrm_is_rejected(self):
        audit = RAW.audit_provider_invocation(
            {"command_options": ["-xml", "-nodrm", "input.pdf", "out"]}
        )
        self.assertFalse(audit["audit_passed"])
        self.assertEqual(audit["forbidden_option_hits"], ["-nodrm"])

    def test_password_options_are_rejected(self):
        for option in (
            "--password=fixture",
            "--password-file=/tmp/pw",
            "--decrypt",
            "--remove-restrictions",
        ):
            with self.subTest(option=option):
                audit = RAW.audit_provider_invocation(
                    {"command_options": [option, "input.pdf"]}
                )
                self.assertFalse(audit["audit_passed"])
                self.assertIn(option, audit["forbidden_option_hits"])

    def test_docling_normal_route_options_do_not_create_bypass(self):
        audit = RAW.audit_provider_invocation(
            {
                "route_options": {
                    "do_ocr": False,
                    "enable_remote_services": False,
                    "allow_external_plugins": False,
                    "hf_hub_offline": True,
                    "transformers_offline": True,
                }
            }
        )
        self.assertTrue(audit["audit_passed"])
        self.assertFalse(audit["fixture_password_supplied_to_provider"])

    def test_generator_password_namespace_is_not_provider_namespace(self):
        observation = {
            "command_options": ["-bbox-layout", "input.pdf", "out.html"],
            "generator_evidence": {
                "fixture_password_supplied_to_generator_only": True,
                "commands_redacted": [["qpdf", "--encrypt", "<fixture-generator-password>"]],
            },
        }
        audit = RAW.audit_provider_invocation(observation)
        self.assertTrue(audit["audit_passed"])
        self.assertFalse(audit["fixture_password_supplied_to_provider"])


if __name__ == "__main__":
    unittest.main()
