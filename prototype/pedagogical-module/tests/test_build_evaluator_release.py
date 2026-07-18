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

import build_evaluator_release  # noqa: E402
import build_pilot  # noqa: E402


class BuildEvaluatorReleaseTests(unittest.TestCase):
    def test_build_creates_closed_versioned_release_with_complete_pilot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            release = build_evaluator_release.build_evaluator_release(parent, "pilot-1.0")

            self.assertEqual(parent / "raiatea-evaluator-pilot-1.0", release)
            manifest = json.loads(
                (release / "release-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                {
                    "format",
                    "contractVersion",
                    "releaseVersion",
                    "entrypoint",
                    "pilotManifest",
                    "files",
                },
                set(manifest),
            )
            self.assertEqual("raiatea-evaluator-release", manifest["format"])
            self.assertEqual(1, manifest["contractVersion"])
            self.assertEqual("pilot-1.0", manifest["releaseVersion"])
            self.assertEqual("pilot/index.html", manifest["entrypoint"])
            self.assertEqual(
                "pilot/pilot-manifest.json", manifest["pilotManifest"]
            )
            self.assertTrue(manifest["files"])
            self.assertTrue(
                all(set(entry) == {"path", "size"} for entry in manifest["files"])
            )
            paths = [entry["path"] for entry in manifest["files"]]
            self.assertEqual(sorted(paths), paths)
            self.assertEqual(len(paths), len(set(paths)))
            self.assertTrue(all(path.startswith("pilot/") for path in paths))
            self.assertIn("pilot/index.html", paths)
            self.assertIn("pilot/pilot-manifest.json", paths)
            self.assertEqual([], build_evaluator_release.validate_release_manifest(manifest))

    def test_release_pilot_payload_is_byte_identical_to_direct_pilot_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            release = build_evaluator_release.build_evaluator_release(parent, "1.0.0")
            direct = parent / "direct-pilot"
            build_pilot.build_pilot(direct)

            release_pilot = release / "pilot"
            release_files = sorted(
                path.relative_to(release_pilot).as_posix()
                for path in release_pilot.rglob("*")
                if path.is_file()
            )
            direct_files = sorted(
                path.relative_to(direct).as_posix()
                for path in direct.rglob("*")
                if path.is_file()
            )
            self.assertEqual(direct_files, release_files)
            for relative in direct_files:
                self.assertEqual(
                    (direct / relative).read_bytes(),
                    (release_pilot / relative).read_bytes(),
                    relative,
                )

    def test_repeated_builds_are_byte_identical_for_same_version(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = build_evaluator_release.build_evaluator_release(
                Path(first_tmp), "candidate-1"
            )
            second = build_evaluator_release.build_evaluator_release(
                Path(second_tmp), "candidate-1"
            )
            first_files = sorted(
                path.relative_to(first).as_posix()
                for path in first.rglob("*")
                if path.is_file()
            )
            second_files = sorted(
                path.relative_to(second).as_posix()
                for path in second.rglob("*")
                if path.is_file()
            )
            self.assertEqual(first_files, second_files)
            for relative in first_files:
                self.assertEqual(
                    (first / relative).read_bytes(),
                    (second / relative).read_bytes(),
                    relative,
                )

    def test_invalid_versions_fail_before_output_or_staging_is_created(self) -> None:
        invalid = (
            "",
            "UPPER",
            ".leading",
            "trailing.",
            "with space",
            "../escape",
            "a/b",
            "a" * 65,
        )
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            for value in invalid:
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        build_evaluator_release.build_evaluator_release(parent, value)
            self.assertEqual([], list(parent.iterdir()))

    def test_manifest_validator_rejects_unknown_missing_unsafe_duplicate_and_unsorted_fields(self) -> None:
        valid = {
            "format": "raiatea-evaluator-release",
            "contractVersion": 1,
            "releaseVersion": "1.0",
            "entrypoint": "pilot/index.html",
            "pilotManifest": "pilot/pilot-manifest.json",
            "files": [
                {"path": "pilot/index.html", "size": 1},
                {"path": "pilot/pilot-manifest.json", "size": 2},
            ],
        }
        self.assertEqual([], build_evaluator_release.validate_release_manifest(valid))

        variants = []
        variants.append({**valid, "extra": True})
        variants.append({key: value for key, value in valid.items() if key != "format"})
        variants.append({**valid, "releaseVersion": "../bad"})
        variants.append({**valid, "entrypoint": "pilot/other.html"})
        variants.append({**valid, "files": [{"path": "../escape", "size": 1}]})
        variants.append({**valid, "files": [{"path": "pilot\\x", "size": 1}]})
        variants.append(
            {
                **valid,
                "files": [
                    {"path": "pilot/index.html", "size": 1},
                    {"path": "pilot/index.html", "size": 1},
                ],
            }
        )
        variants.append(
            {
                **valid,
                "files": [
                    {"path": "pilot/z", "size": 1},
                    {"path": "pilot/a", "size": 1},
                ],
            }
        )
        variants.append({**valid, "files": [{"path": "pilot/a", "size": True}]})
        variants.append({**valid, "files": [{"path": "pilot/a", "size": -1}]})
        variants.append({**valid, "files": [{"path": "pilot/a", "size": 1, "x": 2}]})

        for candidate in variants:
            with self.subTest(candidate=candidate):
                self.assertTrue(
                    build_evaluator_release.validate_release_manifest(candidate)
                )

    def test_inventory_rejects_symlink_without_copying_target(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symbolic links are unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pilot = root / "pilot"
            pilot.mkdir()
            target = root / "secret.txt"
            target.write_text("secret", encoding="utf-8")
            (pilot / "linked.txt").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                build_evaluator_release._inventory(pilot)
            self.assertEqual("secret", target.read_text(encoding="utf-8"))

    def test_existing_output_is_refused_without_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            output = parent / "raiatea-evaluator-1.0"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                build_evaluator_release.build_evaluator_release(parent, "1.0")
            self.assertEqual("unchanged", marker.read_text(encoding="utf-8"))
            self.assertEqual([marker], list(output.iterdir()))

    def test_destination_created_during_install_is_preserved_and_staging_is_cleaned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            output = parent / "raiatea-evaluator-race"
            marker = output / "keep.txt"
            original_install = build_evaluator_release._install_tree_no_replace

            def collide(staged: Path, destination: Path, version: str) -> None:
                destination.mkdir()
                marker.write_text("concurrent", encoding="utf-8")
                original_install(staged, destination, version)

            with mock.patch.object(
                build_evaluator_release,
                "_install_tree_no_replace",
                side_effect=collide,
            ):
                with self.assertRaisesRegex(ValueError, "already exists"):
                    build_evaluator_release.build_evaluator_release(parent, "race")

            self.assertEqual("concurrent", marker.read_text(encoding="utf-8"))
            self.assertEqual([marker], list(output.iterdir()))
            self.assertEqual([], list(parent.glob(".raiatea-evaluator-race.*")))

    def test_pilot_failure_leaves_no_output_or_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            with mock.patch.object(
                build_evaluator_release.build_pilot,
                "build_pilot",
                side_effect=ValueError("pilot failed"),
            ):
                with self.assertRaisesRegex(ValueError, "pilot failed"):
                    build_evaluator_release.build_evaluator_release(parent, "broken")
            self.assertFalse(
                build_evaluator_release._path_lexists(
                    parent / "raiatea-evaluator-broken"
                )
            )
            self.assertEqual([], list(parent.glob(".raiatea-evaluator-broken.*")))

    def test_verification_detects_payload_size_or_inventory_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            release = build_evaluator_release.build_evaluator_release(parent, "verify")
            (release / "pilot" / "index.html").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inventory does not match"):
                build_evaluator_release._verify_release(release, "verify")

    def test_cli_builds_release_and_refuses_same_destination(self) -> None:
        checker = BUILD_DIR / "build_evaluator_release.py"
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            command = [
                sys.executable,
                str(checker),
                "--output-parent",
                str(parent),
                "--release-version",
                "cli-1",
            ]
            first = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(
                str(parent / "raiatea-evaluator-cli-1"), first.stdout.strip()
            )
            second = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            self.assertEqual(1, second.returncode)
            self.assertIn("already exists", second.stdout)


if __name__ == "__main__":
    unittest.main()
