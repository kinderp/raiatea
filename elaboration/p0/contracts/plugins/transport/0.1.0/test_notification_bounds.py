from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process_harness import HarnessError, LocalProcessHarness, MAX_NOTIFICATIONS_BEFORE_RESPONSE

PLUGIN_ROOT = ROOT.parents[1] / "1.0.0"
MANIFEST_PATH = PLUGIN_ROOT / "examples" / "local-read-only-source.json"
FLOOD_PLUGIN = ROOT / "diagnostic_flood_plugin.py"


def invocation(handshake: dict) -> dict:
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:diag-flood:1",
        "idempotency_key": "idem:diag-flood:1",
        "runtime_instance_id": handshake["identity"]["runtime_instance_id"],
        "capability": {"capability_id": "source.discover", "profile_id": "local-read-only"},
        "inputs": [],
        "output_targets": [],
        "runtime_context": {"workspace_scope_id": "workspace:diag-flood", "secret_leases": []},
        "deadline_at": "2026-08-23T20:16:00Z",
        "parameters": {},
    }


class NotificationBoundsTests(unittest.TestCase):
    def test_too_many_notifications_before_response_fail_closed(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        with LocalProcessHarness([sys.executable, str(FLOOD_PLUGIN)], manifest) as harness:
            hs = harness.handshake()
            with self.assertRaisesRegex(HarnessError, "too-many-notifications-before-response"):
                harness.invoke(invocation(hs))
            self.assertEqual(len(harness.diagnostics), MAX_NOTIFICATIONS_BEFORE_RESPONSE)


if __name__ == "__main__":
    unittest.main()
