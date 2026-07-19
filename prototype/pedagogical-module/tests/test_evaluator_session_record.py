from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "build"
CONTRACTS = ROOT / "contracts"
sys.path.insert(0, str(BUILD))

import evaluator_session_record as session  # noqa: E402


class EvaluatorSessionRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads((CONTRACTS / "evaluator-session-record-v1.json").read_text(encoding="utf-8"))
        cls.matrix = json.loads((CONTRACTS / "desktop-acceptance-matrix-v1.json").read_text(encoding="utf-8"))

    def test_canonical_fixture_is_valid_and_non_identifying(self) -> None:
        self.assertEqual([], session.validate_record(self.fixture))
        text = json.dumps(self.fixture, sort_keys=True).casefold()
        for forbidden in ("timestamp", "email", "learneranswer", "username", "hostname", "accountid"):
            self.assertNotIn(forbidden, text)

    def test_closed_schema_and_canonical_result_keys(self) -> None:
        value = copy.deepcopy(self.fixture)
        value["extra"] = True
        self.assertTrue(any("unsupported field" in issue for issue in session.validate_record(value)))
        value = copy.deepcopy(self.fixture)
        value["results"] = dict(reversed(list(value["results"].items())))
        self.assertTrue(any("canonical sorted result list" in issue for issue in session.validate_record(value)))
        value = copy.deepcopy(self.fixture)
        value["results"]["launchSucceeded"] = "yes"
        self.assertTrue(any("must be boolean" in issue for issue in session.validate_record(value)))

    def test_platform_launcher_pair_is_closed(self) -> None:
        value = copy.deepcopy(self.fixture)
        value["platform"] = "windows"
        self.assertTrue(any("requires powershell" in issue for issue in session.validate_record(value)))
        value["launcher"] = "powershell"
        self.assertEqual([], session.validate_record(value))

    def test_privacy_sensitive_observations_are_rejected(self) -> None:
        samples = (
            "contact teacher@example.org",
            "host 192.168.1.20",
            "saved at C:\\Users\\teacher\\record.json",
            "username was collected",
            "timestamp was automatic",
        )
        for observation in samples:
            with self.subTest(observation=observation):
                value = copy.deepcopy(self.fixture)
                value["observations"] = observation
                self.assertTrue(session.validate_record(value))

    def test_explicit_create_validate_export_delete_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "local" / "session.json"
            exported = root / "export" / "session-copy.json"
            session.create_record(source, "field-pilot-v1", "linux", "posix", "Navigation was clear.")
            original = session.load_record(source)
            self.assertEqual("Navigation was clear.", original["observations"])
            session.export_record(source, exported)
            self.assertEqual(source.read_bytes(), exported.read_bytes())
            session.delete_record(source)
            self.assertFalse(source.exists())
            self.assertTrue(exported.exists())

    def test_outputs_are_no_replace_and_delete_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "session.json"
            path.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                session.create_record(path, "field-pilot-v1", "linux", "posix")
            self.assertEqual("keep", path.read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                session.delete_record(path)
            self.assertTrue(path.exists())

    def test_acceptance_matrix_is_closed_and_complete(self) -> None:
        self.assertEqual("raiatea-desktop-acceptance-matrix", self.matrix["format"])
        self.assertEqual(1, self.matrix["version"])
        rows = self.matrix["rows"]
        self.assertEqual(["linux", "macos", "windows"], [row["platform"] for row in rows])
        self.assertEqual(["ci", "manual-parity", "ci"], [row["execution"] for row in rows])
        expected = list(session.RESULT_KEYS)
        for row in rows:
            self.assertEqual(expected, row["checks"])
        self.assertEqual("posix", rows[0]["launcher"])
        self.assertEqual("posix", rows[1]["launcher"])
        self.assertEqual("powershell", rows[2]["launcher"])

    def test_matrix_matches_existing_desktop_helpers_and_workflows(self) -> None:
        posix = (BUILD / "launch-posix.sh").read_text(encoding="utf-8")
        powershell = (BUILD / "Launch-Raiatea.ps1").read_text(encoding="utf-8")
        linux_workflow = (ROOT.parents[1] / ".github" / "workflows" / "pedagogical-module.yml").read_text(encoding="utf-8")
        windows_workflow = (ROOT.parents[1] / ".github" / "workflows" / "pedagogical-module-windows.yml").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1", posix)
        self.assertIn("127.0.0.1", powershell)
        self.assertIn("release-artifact-consumer", linux_workflow)
        self.assertIn("windows-powershell-acceptance", windows_workflow)
        for forbidden in ("curl http://", "Invoke-RestMethod", "telemetry", "analytics"):
            self.assertNotIn(forbidden, posix + powershell)


if __name__ == "__main__":
    unittest.main()
