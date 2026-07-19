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
    pass
