from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import build_pilot  # noqa: E402


class PilotExportWalkthroughTests(unittest.TestCase):
    def test_launcher_contains_static_accessible_walkthrough(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot"
            build_pilot.build_pilot(output)
            launcher = (output / "index.html").read_text(encoding="utf-8")

            self.assertIn('id="evidence-walkthrough-title"', launcher)
            self.assertIn("Come leggere il riepilogo ed esportare le evidenze", launcher)
            self.assertIn("Riepilogo del percorso", launcher)
            self.assertIn("Esporta evidenze JSON", launcher)
            self.assertIn("&lt;module-id&gt;-evidence-v1.json", launcher)
            self.assertIn("non sono un voto o un mastery score", launcher)
            self.assertIn("non crea ancora un portfolio", launcher)
            self.assertIn('href="self-attention.html"', launcher)
            self.assertIn('href="query-key-value.html"', launcher)

    def test_walkthrough_adds_no_new_route_export_or_identity_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot"
            build_pilot.build_pilot(output)
            manifest = (output / "pilot-manifest.json").read_text(encoding="utf-8")
            launcher = (output / "index.html").read_text(encoding="utf-8")

            for forbidden in (
                "portfolioExport",
                "routeEvidence",
                "learnerName",
                "email",
                "timestamp",
                "analytics",
                "telemetry",
                "cloud",
            ):
                self.assertNotIn(forbidden, manifest)
            self.assertNotIn("download=", launcher)
            self.assertNotIn("fetch(", launcher)


if __name__ == "__main__":
    unittest.main()
