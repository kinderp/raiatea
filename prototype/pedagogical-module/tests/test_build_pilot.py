from __future__ import annotations

import json
import os
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
    def test_build_creates_closed_canonical_dashboard_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            self.assertEqual(output, build_pilot.build_pilot(output))
            expected = {
                "index.html",
                "self-attention.html",
                "query-key-value.html",
                "pilot-manifest.json",
                "pilot-dashboard.js",
            }
            self.assertEqual(expected, {path.name for path in output.iterdir()})
            manifest = json.loads((output / "pilot-manifest.json").read_text())
            self.assertEqual({"format", "version", "modules"}, set(manifest))
            self.assertEqual("raiatea-pilot", manifest["format"])
            self.assertEqual(1, manifest["version"])
            self.assertTrue(all(set(module) == {
                "id", "revision", "title", "stepCount", "order", "file", "previous", "next"
            } for module in manifest["modules"]))
            self.assertEqual(
                ["self-attention-orientation", "query-key-value"],
                [module["id"] for module in manifest["modules"]],
            )
            self.assertTrue(all(module["stepCount"] > 0 for module in manifest["modules"]))

    def test_launcher_contains_static_fallback_and_dashboard_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            build_pilot.build_pilot(output)
            launcher = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="self-attention.html"', launcher)
            self.assertIn('href="query-key-value.html"', launcher)
            self.assertIn('data-pilot-status', launcher)
            self.assertIn('data-pilot-recommendation', launcher)
            self.assertIn('src="pilot-dashboard.js"', launcher)
            self.assertIn('window.RAIATEA_PILOT=', launcher)
            self.assertNotIn(str(output.resolve()), launcher)

    def test_manifest_and_dashboard_assets_exclude_personal_runtime_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            build_pilot.build_pilot(output)
            public = (
                (output / "pilot-manifest.json").read_text(encoding="utf-8")
                + (output / "index.html").read_text(encoding="utf-8")
            )
            for forbidden in (
                "email", "timestamp", "analytics", "telemetry", "diagnosis", str(output.resolve())
            ):
                self.assertNotIn(forbidden, public)

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
            for path in first.iterdir():
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes())

    def test_existing_output_and_dangling_symlink_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            output = parent / "pilot-dist"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                build_pilot.build_pilot(output)
            self.assertEqual("unchanged", marker.read_text(encoding="utf-8"))

            if hasattr(os, "symlink"):
                link = parent / "pilot-link"
                link.symlink_to(parent / "missing", target_is_directory=True)
                with self.assertRaisesRegex(ValueError, "already exists"):
                    build_pilot.build_pilot(link)
                self.assertTrue(link.is_symlink())

    def test_destination_created_during_build_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "pilot-dist"
            marker = output / "keep.txt"
            original_install = build_pilot._install_directory_no_replace

            def collide(staged: Path, destination: Path, manifest: dict) -> None:
                destination.mkdir()
                marker.write_text("concurrent", encoding="utf-8")
                original_install(staged, destination, manifest)

            with mock.patch.object(build_pilot, "_install_directory_no_replace", side_effect=collide):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    build_pilot.build_pilot(output)
            self.assertEqual("concurrent", marker.read_text(encoding="utf-8"))
            self.assertEqual([], list(Path(temporary).glob(".pilot-dist.*")))

    def test_invalid_module_leaves_no_output_or_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            invalid = parent / "invalid.json"
            invalid.write_text('{"id":', encoding="utf-8")
            output = parent / "pilot-dist"
            with mock.patch.object(
                build_pilot,
                "ROUTE_SPECS",
                ({"source": invalid, "output": "invalid.html"},),
            ):
                with self.assertRaises(ValueError):
                    build_pilot.build_pilot(output)
            self.assertFalse(build_pilot._path_lexists(output))
            self.assertEqual([], list(parent.glob(".pilot-dist.*")))

    def test_cli_builds_and_refuses_existing_destination(self) -> None:
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
            second = subprocess.run(
                [sys.executable, str(checker), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(1, second.returncode)
            self.assertIn("already exists", second.stdout)


if __name__ == "__main__":
    unittest.main()
