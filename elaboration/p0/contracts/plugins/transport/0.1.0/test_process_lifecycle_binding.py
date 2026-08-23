from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process_harness import LocalProcessHarness, ProcessExited

PLUGIN_ROOT = ROOT.parents[1] / "1.0.0"
MANIFEST_PATH = PLUGIN_ROOT / "examples" / "local-read-only-source.json"
SYNTHETIC = ROOT / "synthetic_plugin.py"


def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def command(mode: str) -> list[str]:
    return [sys.executable, str(SYNTHETIC), "--mode", mode]


def invocation(handshake: dict) -> dict:
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:lifecycle:1",
        "idempotency_key": "idem:lifecycle:1",
        "runtime_instance_id": handshake["identity"]["runtime_instance_id"],
        "capability": {"capability_id": "source.discover", "profile_id": "local-read-only"},
        "inputs": [],
        "output_targets": [],
        "runtime_context": {"workspace_scope_id": "workspace:lifecycle", "secret_leases": []},
        "deadline_at": "2026-08-23T20:16:00Z",
        "parameters": {},
    }


class ProcessLifecycleBindingTests(unittest.TestCase):
    def test_pre_handshake_crash_stays_process_attempt_evidence(self):
        harness = LocalProcessHarness(command("crash-startup"), manifest())
        try:
            harness.start()
            with self.assertRaises(ProcessExited):
                harness.handshake()
        finally:
            harness.close()
        self.assertEqual(harness.lifecycle_events, [])
        self.assertTrue(any(row["event"] == "process-exited-before-handshake" for row in harness.process_events))

    def test_post_handshake_crash_maps_to_runtime_failed_transition(self):
        harness = LocalProcessHarness(command("crash-invoke"), manifest())
        try:
            harness.start()
            hs = harness.handshake()
            with self.assertRaises(ProcessExited):
                harness.invoke(invocation(hs))
        finally:
            harness.close()
        transitions = [(row["from"], row["to"]) for row in harness.lifecycle_events]
        self.assertEqual(transitions[0], ("starting", "ready"))
        self.assertIn(("ready", "failed"), transitions)

    def test_normal_core_shutdown_records_stopping_and_stopped(self):
        harness = LocalProcessHarness(command("normal"), manifest())
        harness.start()
        harness.handshake()
        harness.close()
        transitions = [(row["from"], row["to"]) for row in harness.lifecycle_events]
        self.assertEqual(
            transitions,
            [("starting", "ready"), ("ready", "stopping"), ("stopping", "stopped")],
        )


if __name__ == "__main__":
    unittest.main()
