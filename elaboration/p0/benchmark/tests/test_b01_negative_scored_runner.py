from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
if str(ROUTES) not in sys.path:
    sys.path.insert(0, str(ROUTES))

SPEC = importlib.util.spec_from_file_location(
    "p0_measure_b01_negative_scored",
    ROUTES / "measure_b01_negative_scored.py",
)
SCORED = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORED)


class B01NegativeScoredRunnerTests(unittest.TestCase):
    def test_cli_stdout_is_one_valid_scored_json_document(self):
        raw_report = {
            "evidence_source_commit": "deadbeef",
            "provider_family": "poppler",
            "results": [
                {
                    "fixture_id": "B01-PDF-NEG-001",
                    "observation": {
                        "route": "synthetic-poppler",
                        "status": "failed",
                        "blocks": [],
                        "warnings": [
                            {"code": "parse-failure", "details": "xref corrupt"}
                        ],
                    },
                    "provider_invocation_audit": {
                        "audit_passed": True,
                        "fixture_password_supplied_to_provider": False,
                        "access_control_bypass_requested": False,
                    },
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            stdout = io.StringIO()
            argv = [
                "measure_b01_negative_scored.py",
                "poppler",
                "--output",
                str(out),
                "--evidence-source-commit",
                "deadbeef",
            ]
            with patch.object(SCORED.raw, "run", return_value=raw_report), patch.object(
                sys, "argv", argv
            ), redirect_stdout(stdout):
                self.assertEqual(SCORED.main(), 0)

            emitted = json.loads(stdout.getvalue())
            persisted = json.loads(
                (out / "b01-negative-poppler-scored.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(emitted, persisted)
            self.assertEqual(emitted["provider_family"], "poppler")
            self.assertTrue(emitted["all_invocation_audits_passed"])
            self.assertFalse(emitted["any_false_complete_success"])


if __name__ == "__main__":
    unittest.main()
