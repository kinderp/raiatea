from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "build"))

import supervised_pilot_checklist as checklist  # noqa: E402


class SupervisedPilotChecklistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_path = ROOT / "contracts" / "supervised-pilot-checklist-v1.json"
        cls.fixture = json.loads(cls.fixture_path.read_text(encoding="utf-8"))

    def test_canonical_fixture_is_valid(self) -> None:
        self.assertEqual([], checklist.validate_checklist(self.fixture))
        self.assertEqual(self.fixture, checklist.load_checklist(self.fixture_path))

    def test_fields_and_phase_order_are_closed(self) -> None:
        value = copy.deepcopy(self.fixture)
        value["extra"] = True
        self.assertTrue(any("unsupported field" in item for item in checklist.validate_checklist(value)))
        value = copy.deepcopy(self.fixture)
        value["phases"] = dict(reversed(list(value["phases"].items())))
        self.assertTrue(any("canonical phase order" in item for item in checklist.validate_checklist(value)))

    def test_platform_launcher_pairing_is_enforced(self) -> None:
        value = copy.deepcopy(self.fixture)
        value["platform"] = "windows"
        self.assertTrue(any("powershell" in item for item in checklist.validate_checklist(value)))
        value["launcher"] = "powershell"
        self.assertEqual([], checklist.validate_checklist(value))

    def test_completion_and_stop_rules_fail_closed(self) -> None:
        value = copy.deepcopy(self.fixture)
        value["phases"]["temporaryCopiesRemoved"] = False
        self.assertTrue(any("completed requires" in item for item in checklist.validate_checklist(value)))
        value["status"] = "stopped"
        value["phases"]["pilotStopped"] = False
        self.assertTrue(any("pilotStopped" in item for item in checklist.validate_checklist(value)))

    def test_privacy_fields_are_not_supported(self) -> None:
        for field in ("learnerName", "classId", "timestamp", "observations", "device"):
            value = copy.deepcopy(self.fixture)
            value[field] = "forbidden"
            with self.subTest(field=field):
                self.assertTrue(checklist.validate_checklist(value))

    def test_no_replace_write_and_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "checklist.json"
            checklist.write_checklist(target, self.fixture)
            self.assertEqual(self.fixture, checklist.load_checklist(target))
            with self.assertRaisesRegex(ValueError, "already exists"):
                checklist.write_checklist(target, self.fixture)


if __name__ == "__main__":
    unittest.main()
