from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location("p0_measure_b02_summary", ROUTES_DIR / "measure_b02.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _report(version: str | None, surveyed: str, blocker: str | None, availability: str = "available"):
    return {
        "environment": {
            "platform_system": "TestOS",
            "platform_release": "1",
            "machine": "test-arch",
            "python_version": "3.test",
        },
        "routes": {
            "pandoc-epub": {
                "availability": availability,
                "version": version,
                "surveyed_version": surveyed,
                "surveyed_version_match": version == surveyed,
                "selection_blocker": blocker,
            }
        },
        "results": [],
    }


class B02SummaryTests(unittest.TestCase):
    def test_summary_uses_dynamic_version_blocker_text(self):
        blocker = "Measured Pandoc version differs from the E-02 surveyed baseline; rerun before selection."
        report = _report("9.9.9", "10.0.0", blocker)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            MODULE._write_summary(report, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn("Pandoc measured: `9.9.9`", text)
        self.assertIn("Pandoc E-02 surveyed: `10.0.0`", text)
        self.assertIn(blocker, text)
        self.assertNotIn("3.1.11.1", text)

    def test_summary_does_not_claim_selection_when_versions_match(self):
        report = _report("10.0.0", "10.0.0", None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            MODULE._write_summary(report, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn("removes only the version-mismatch blocker", text)
        self.assertIn("does not select the route", text)

    def test_summary_reports_unavailable_pandoc(self):
        report = _report(None, "10.0.0", "Pandoc unavailable", availability="unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            MODULE._write_summary(report, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn("Pandoc route selection blocker: Pandoc unavailable", text)


if __name__ == "__main__":
    unittest.main()
