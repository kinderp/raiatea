from __future__ import annotations

import json
from pathlib import Path
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from process_harness import LocalProcessHarness, MAX_STDERR_CAPTURE_BYTES

PLUGIN_ROOT = ROOT.parents[1] / "1.0.0"
MANIFEST_PATH = PLUGIN_ROOT / "examples" / "local-read-only-source.json"
FLOOD_PLUGIN = ROOT / "stderr_flood_plugin.py"


class StderrDrainTests(unittest.TestCase):
    def test_large_stderr_is_drained_without_unbounded_retention_or_deadlock(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        harness = LocalProcessHarness([sys.executable, str(FLOOD_PLUGIN)], manifest)
        outcome: list[BaseException | dict] = []

        def worker() -> None:
            try:
                outcome.append(harness.handshake())
            except BaseException as exc:  # surfaced in the main test thread below
                outcome.append(exc)

        harness.start()
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout=5)
        try:
            if thread.is_alive():
                self.fail("handshake deadlocked while child stderr pipe was under backpressure")
            self.assertTrue(outcome)
            if isinstance(outcome[0], BaseException):
                raise outcome[0]
            self.assertEqual(outcome[0]["record_type"], "handshake")
        finally:
            harness.close()

        retained = len(harness.stderr_text.encode("utf-8"))
        self.assertLessEqual(retained, MAX_STDERR_CAPTURE_BYTES)
        self.assertGreater(retained, 0)
        self.assertTrue(harness.stderr_truncated)
        self.assertEqual(harness.diagnostics, [])


if __name__ == "__main__":
    unittest.main()
