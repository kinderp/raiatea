from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import build_pilot  # noqa: E402


class BuildPilotTests(unittest.TestCase):
    def test_build_creates_closed_two_module_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            result = build_pilot.build_pilot(output)
            self.assertEqual(output, result)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "query-key-value.html").is_file())
            self.assertTrue((output / "self-attention.html").is_file())

            manifest = json.loads(
                (output / "pilot-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual("raiatea-pilot", manifest["format"])
            self.assertEqual(1, manifest["version"])
            self.assertEqual(
                ["query-key-value", "self-attention"],
                [module["id"] for module in manifest["modules"]],
            )
            self.assertEqual(
                [0, 1], [module["order"] for module in manifest["modules"]]
            )
            self.assertIsNone(manifest["modules"][0]["previous"])
            self.assertEqual(
                "self-attention.html", manifest["modules"][0]["next"]
            )
            self.assertEqual(
                "query-key-value.html", manifest["modules"][1]["previous"]
            )
            self.assertIsNone(manifest["modules"][1]["next"])

    def test_launcher_and_module_navigation_use_relative_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            build_pilot.build_pilot(output)
            launcher = (output / "index.html").read_text(encoding="utf-8")
            first = (output / "query-key-value.html").read_text(encoding="utf-8")
            second = (output / "self-attention.html").read_text(encoding="utf-8")

            self.assertIn('href="query-key-value.html"', launcher)
            self.assertIn('href="self-attention.html"', launcher)
            self.assertIn('href="index.html"', first)
            self.assertIn('href="self-attention.html"', first)
            self.assertIn('href="index.html"', second)
            self.assertIn('href="query-key-value.html"', second)
            self.assertNotIn(str(output.resolve()), launcher + first + second)

    def test_manifest_excludes_runtime_and_personal_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            build_pilot.build_pilot(output)
            manifest_text = (output / "pilot-manifest.json").read_text(
                encoding="utf-8"
            )
            for forbidden in (
                "learner",
                "email",
                "timestamp",
                "analytics",
                "telemetry",
                "localStorage",
                str(output.resolve()),
            ):
                self.assertNotIn(forbidden, manifest_text)

    def test_existing_output_is_refused_without_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                build_pilot.build_pilot(output)
            self.assertEqual("unchanged", marker.read_text(encoding="utf-8"))
            self.assertEqual([marker], list(output.iterdir()))


if __name__ == "__main__":
    unittest.main()
