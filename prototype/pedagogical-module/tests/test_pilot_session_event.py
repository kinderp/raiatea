from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "build" / "pilot_incident_record.py"
SPEC = importlib.util.spec_from_file_location("pilot_event_module", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
FIXTURE = ROOT / "contracts" / "pilot-session-event-v1.json"


class PilotSessionEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.value = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_and_stop_rules(self) -> None:
        self.assertEqual([], module.validate_incident(self.value))
        self.assertTrue(module.required_stop("critical", "runtime", False))
        self.assertTrue(module.required_stop("low", "privacy-boundary", False))
        self.assertTrue(module.required_stop("low", "runtime", True))
        self.assertFalse(module.required_stop("high", "runtime", False))

    def test_inconsistent_values_fail_closed(self) -> None:
        value = copy.deepcopy(self.value)
        value["stopRequired"] = False
        self.assertTrue(module.validate_incident(value))
        value = copy.deepcopy(self.value)
        value["actions"] = ["verify-cleanup"]
        self.assertTrue(module.validate_incident(value))
        value = copy.deepcopy(self.value)
        value["extra"] = True
        self.assertTrue(module.validate_incident(value))

    def test_malformed_action_arrays_are_rejected(self) -> None:
        samples = (["stop-pilot", "stop-pilot"], ["verify-cleanup", "stop-pilot"], [7], "stop-pilot")
        for sample in samples:
            value = copy.deepcopy(self.value)
            value["actions"] = sample
            self.assertTrue(module.validate_incident(value))
