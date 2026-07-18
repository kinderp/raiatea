from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import build_pilot  # noqa: E402


class BuildPilotTests(unittest.TestCase):
    def test_build_creates_closed_canonical_two_module_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            result = build_pilot.build_pilot(output)
            self.assertEqual(output, result)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "self-attention.html").is_file())
            self.assertTrue((output / "query-key-value.html").is_file())

            manifest = json.loads(
                (output / "pilot-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual("raiatea-pilot", manifest["format"])
            self.assertEqual(1, manifest["version"])
            self.assertEqual(
                ["self-attention-orientation", "query-key-value"],
                [module["id"] for module in manifest["modules"]],
            )
            self.assertEqual([1, 1], [module["revision"] for module in manifest["modules"]])
            self.assertEqual([0, 1], [module["order"] for module in manifest["modules"]])
            self.assertIsNone(manifest["modules"][0]["previous"])
            self.assertEqual(
                "query-key-value.html", manifest["modules"][0]["next"]
            )
            self.assertEqual(
                "self-attention.html", manifest["modules"][1]["previous"]
            )
            self.assertIsNone(manifest["modules"][1]["next"])

    def test_launcher_and_module_navigation_use_relative_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            build_pilot.build_pilot(output)
            launcher = (output / "index.html").read_text(encoding="utf-8")
            first = (output / "self-attention.html").read_text(encoding="utf-8")
            second = (output / "query-key-value.html").read_text(encoding="utf-8")

            self.assertIn('href="self-attention.html"', launcher)
            self.assertIn('href="query-key-value.html"', launcher)
            self.assertIn('href="index.html"', first)
            self.assertIn('href="query-key-value.html"', first)
            self.assertIn('href="index.html"', second)
            self.assertIn('href="self-attention.html"', second)
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

    def test_build_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "pilot-one"
            second = Path(temporary) / "pilot-two"
            build_pilot.build_pilot(first)
            build_pilot.build_pilot(second)
            self.assertEqual(
                sorted(path.name for path in first.iterdir()),
                sorted(path.name for path in second.iterdir()),
            )
            for first_path in sorted(first.iterdir(), key=lambda path: path.name):
                self.assertEqual(
                    first_path.read_bytes(),
                    (second / first_path.name).read_bytes(),
                    first_path.name,
                )

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

    def test_destination_created_during_build_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            marker = output / "keep.txt"
            original_install = build_pilot._install_directory_no_replace

            def collide(staged: Path, destination: Path, manifest: dict) -> None:
                destination.mkdir()
                marker.write_text("concurrent", encoding="utf-8")
                original_install(staged, destination, manifest)

            with mock.patch.object(
                build_pilot,
                "_install_directory_no_replace",
                side_effect=collide,
            ):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    build_pilot.build_pilot(output)

            self.assertEqual("concurrent", marker.read_text(encoding="utf-8"))
            self.assertEqual([marker], list(output.iterdir()))
            self.assertEqual([], list(Path(temporary).glob(".pilot-dist.*")))

    def test_invalid_module_leaves_no_output_or_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            invalid = parent / "invalid.json"
            invalid.write_text('{"id":', encoding="utf-8")
            output = parent / "pilot-dist"
            specs = ({"source": invalid, "output": "invalid.html"},)
            with mock.patch.object(build_pilot, "ROUTE_SPECS", specs):
                with self.assertRaises(Exception):
                    build_pilot.build_pilot(output)
            self.assertFalse(build_pilot._path_lexists(output))
            self.assertEqual([], list(parent.glob(".pilot-dist.*")))

    def test_cli_builds_and_refuses_an_existing_destination(self) -> None:
        checker = BUILD_DIR / "build_pilot.py"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            first = subprocess.run(
                [sys.executable, str(checker), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(str(output), first.stdout.strip())

            second = subprocess.run(
                [sys.executable, str(checker), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, second.returncode)
            self.assertIn("already exists", second.stdout)
            self.assertTrue((output / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
