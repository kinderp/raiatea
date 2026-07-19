from __future__ import annotations

import hashlib
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
sys.path.insert(0, str(BUILD))

import build_desktop_evaluator_archive as desktop_builder  # noqa: E402
import build_evaluator_archive as archive_builder  # noqa: E402


class WindowsPowerShellHelperTests(unittest.TestCase):
    def test_scripts_are_closed_and_avoid_machine_wide_changes(self) -> None:
        launch = (BUILD / "Launch-Raiatea.ps1").read_text(encoding="utf-8")
        stop = (BUILD / "Stop-Raiatea.ps1").read_text(encoding="utf-8")
        for required in ("127.0.0.1", "PYTHON_NOT_FOUND", "PORT_IN_USE", "STATE_ALREADY_EXISTS", "pilot/index.html"):
            self.assertIn(required, launch)
        for required in ("STATE_STALE", "STATE_FOREIGN_PROCESS", "STOP_FAILED", "Win32_Process"):
            self.assertIn(required, stop)
        forbidden = ("Set-ExecutionPolicy", "New-Service", "Register-ScheduledTask", "New-NetFirewallRule", "HKLM:", "Invoke-RestMethod")
        for value in forbidden:
            self.assertNotIn(value, launch + stop)

    def test_desktop_archive_is_reproducible_and_covers_all_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = desktop_builder.build_desktop_evaluator_archive(root / "first", "desktop-1")
            second = desktop_builder.build_desktop_evaluator_archive(root / "second", "desktop-1")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            release = archive_builder.verify_evaluator_archive(first, root / "verified")
            entries = {
                path: digest
                for digest, path in archive_builder._parse_checksums(
                    (release / "SHA256SUMS").read_text(encoding="ascii")
                )
            }
            for relative in (
                "launch-posix.sh", "stop-posix.sh", "POSIX-LAUNCH.md",
                "Launch-Raiatea.ps1", "Stop-Raiatea.ps1", "WINDOWS-LAUNCH.md",
            ):
                self.assertTrue((release / relative).is_file())
                self.assertEqual(entries[relative], hashlib.sha256((release / relative).read_bytes()).hexdigest())
            with tarfile.open(first, "r:") as source:
                names = [member.name for member in source.getmembers()]
            self.assertTrue(any(name.endswith("Launch-Raiatea.ps1") for name in names))

    def test_existing_output_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "raiatea-evaluator-existing.tar"
            output.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                desktop_builder.build_desktop_evaluator_archive(root, "existing")
            self.assertEqual("keep", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
