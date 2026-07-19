from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
CONTRACT = ROOT / "contracts" / "launch-preflight-v1.json"
sys.path.insert(0, str(BUILD))

import launch_preflight_contract as launch_contract  # noqa: E402


class LaunchPreflightContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = launch_contract.load_contract(CONTRACT)

    def test_canonical_contract_is_closed_and_valid(self) -> None:
        self.assertEqual([], launch_contract.validate_contract(self.contract))
        self.assertEqual("raiatea-launch-preflight", self.contract["format"])
        self.assertEqual(["linux", "macos", "windows"], self.contract["supportedPlatforms"])
        self.assertEqual("127.0.0.1", self.contract["host"])
        self.assertEqual(8000, self.contract["defaultPort"])
        self.assertEqual(sorted(self.contract["diagnostics"]), self.contract["diagnostics"])

    def test_unknown_missing_and_changed_fields_fail_closed(self) -> None:
        cases = []
        unknown = copy.deepcopy(self.contract)
        unknown["unexpected"] = True
        cases.append(unknown)
        missing = copy.deepcopy(self.contract)
        del missing["host"]
        cases.append(missing)
        remote_host = copy.deepcopy(self.contract)
        remote_host["host"] = "0.0.0.0"
        cases.append(remote_host)
        changed_runtime = copy.deepcopy(self.contract)
        changed_runtime["runtimeCandidates"]["posix"].reverse()
        cases.append(changed_runtime)
        changed_diagnostic = copy.deepcopy(self.contract)
        changed_diagnostic["diagnostics"].append("UNKNOWN")
        cases.append(changed_diagnostic)
        unsafe_file = copy.deepcopy(self.contract)
        unsafe_file["requiredFiles"] = ["../escape"]
        cases.append(unsafe_file)
        for value in cases:
            with self.subTest(value=value):
                self.assertTrue(launch_contract.validate_contract(value))

    def test_port_validation_accepts_only_decimal_contract_range(self) -> None:
        for value, expected in ((1024, 1024), ("8000", 8000), (65535, 65535)):
            with self.subTest(value=value):
                self.assertEqual(expected, launch_contract.validate_port(value, self.contract))
        for value in (True, None, "", "8.0", "８０００", 1023, 65536):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "PORT_INVALID"):
                    launch_contract.validate_port(value, self.contract)

    def test_verified_release_shape_and_identity_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "raiatea-evaluator-field-1"
            (root / "pilot").mkdir(parents=True)
            (root / "RELEASE-NOTES.md").write_text("notes", encoding="utf-8")
            (root / "SHA256SUMS").write_text("checksums", encoding="utf-8")
            (root / "pilot" / "index.html").write_text("index", encoding="utf-8")
            (root / "release-manifest.json").write_text(
                json.dumps(
                    {
                        "format": "raiatea-evaluator-release",
                        "releaseVersion": "field-1",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual("field-1", launch_contract.validate_verified_release(root, self.contract))

            (root / "release-manifest.json").write_text(
                json.dumps(
                    {
                        "format": "raiatea-evaluator-release",
                        "releaseVersion": "other",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "RELEASE_IDENTITY_MISMATCH"):
                launch_contract.validate_verified_release(root, self.contract)

    def test_missing_or_symlink_required_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "raiatea-evaluator-field-1"
            (root / "pilot").mkdir(parents=True)
            for relative in ("RELEASE-NOTES.md", "SHA256SUMS", "release-manifest.json"):
                (root / relative).write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "RELEASE_FILE_UNSAFE"):
                launch_contract.validate_verified_release(root, self.contract)

            target = root / "target.html"
            target.write_text("index", encoding="utf-8")
            try:
                (root / "pilot" / "index.html").symlink_to(target)
            except OSError:
                self.skipTest("symbolic links are unavailable")
            with self.assertRaisesRegex(ValueError, "RELEASE_FILE_UNSAFE"):
                launch_contract.validate_verified_release(root, self.contract)


if __name__ == "__main__":
    unittest.main()
