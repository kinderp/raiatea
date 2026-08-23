from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import transport as T
from process_harness import HarnessError, LocalProcessHarness


class TransportDirectionalityTests(unittest.TestCase):
    def test_plugin_initiated_request_is_rejected_not_misread_as_response(self):
        harness = LocalProcessHarness(["unused"], {})
        harness._write_message = lambda message: None  # type: ignore[method-assign]
        harness._read_message = lambda phase: T.request_message("plugin:1", "plugin.unsupported", {})  # type: ignore[method-assign]
        with self.assertRaisesRegex(HarnessError, "plugin-initiated-jsonrpc-request-forbidden"):
            harness.raw_request("raiatea.handshake", {})


if __name__ == "__main__":
    unittest.main()
