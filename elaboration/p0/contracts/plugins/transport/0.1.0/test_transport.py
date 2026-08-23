from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import transport as T
from process_harness import HarnessError, LocalProcessHarness, ProcessExited, RemoteProtocolError

PLUGIN_ROOT = ROOT.parents[1] / "1.0.0"
MANIFEST_PATH = PLUGIN_ROOT / "examples" / "local-read-only-source.json"
SYNTHETIC = ROOT / "synthetic_plugin.py"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def command(mode: str = "normal") -> list[str]:
    return [sys.executable, str(SYNTHETIC), "--mode", mode]


def invocation(handshake: dict, *, parameters: dict | None = None) -> dict:
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:transport:1",
        "idempotency_key": "idem:transport:1",
        "runtime_instance_id": handshake["identity"]["runtime_instance_id"],
        "capability": {"capability_id": "source.discover", "profile_id": "local-read-only"},
        "inputs": [],
        "output_targets": [],
        "runtime_context": {
            "workspace_scope_id": "workspace:transport",
            "rights_decision_ref": "rights:transport:1",
            "secret_leases": [],
        },
        "deadline_at": "2026-08-23T20:16:00Z",
        "parameters": parameters or {},
    }


class FramingTests(unittest.TestCase):
    def test_request_roundtrip(self):
        message = T.request_message("rpc:1", "raiatea.handshake", {"runtime_contract_version": "1.0.0"})
        self.assertEqual(T.decode_frame(T.encode_frame(message)), message)

    def test_crlf_frame_is_accepted(self):
        message = T.request_message("rpc:1", "x", {})
        frame = T.encode_frame(message)[:-1] + b"\r\n"
        self.assertEqual(T.decode_frame(frame), message)

    def test_malformed_json_fails(self):
        with self.assertRaisesRegex(T.TransportError, "malformed-json-frame"):
            T.decode_frame(b"{not-json}\n")

    def test_missing_newline_fails(self):
        with self.assertRaisesRegex(T.TransportError, "jsonrpc-frame-missing-newline"):
            T.decode_frame(b'{"jsonrpc":"2.0"}')

    def test_oversized_frame_fails_before_json_decode(self):
        frame = b"x" * T.MAX_FRAME_BYTES + b"\n"
        with self.assertRaisesRegex(T.TransportError, "jsonrpc-frame-too-large"):
            T.decode_frame(frame)

    def test_unsupported_jsonrpc_version_fails(self):
        raw = json.dumps({"jsonrpc": "1.0", "id": "x", "result": {}}).encode() + b"\n"
        with self.assertRaisesRegex(T.TransportError, "unsupported-jsonrpc-version"):
            T.decode_frame(raw)

    def test_inline_base64_field_is_forbidden(self):
        with self.assertRaisesRegex(T.TransportError, "inline-large-payload-field-forbidden"):
            T.request_message("rpc:1", "raiatea.invoke", {"base64": "AAAA"})

    def test_jsonrpc_error_is_protocol_only(self):
        with self.assertRaisesRegex(T.TransportError, "jsonrpc-error-is-protocol-only"):
            T.validate_message({
                "jsonrpc": "2.0",
                "id": "rpc:1",
                "error": {"code": -32000, "message": "x", "data": {"runtime_error": "wrong-layer"}},
            })


class ProcessHarnessTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest()

    def test_positive_handshake_and_source_invocation(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            hs = harness.handshake()
            req = invocation(hs)
            result = harness.invoke(req)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["outputs"][0]["record_ref"]["record_kind"], "SourceReference")
            self.assertNotEqual(harness.last_transport_id, req["invocation_id"])

    def test_runtime_failure_remains_runtime_result_not_jsonrpc_error(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            hs = harness.handshake()
            result = harness.invoke(invocation(hs, parameters={"fail": True}))
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"]["code"], "plugin-internal-failure")

    def test_jsonrpc_error_cannot_masquerade_as_runtime_result(self):
        with LocalProcessHarness(command("protocol-error-invoke"), self.manifest) as harness:
            hs = harness.handshake()
            with self.assertRaisesRegex(RemoteProtocolError, "Synthetic protocol misuse"):
                harness.invoke(invocation(hs))

    def test_invalid_v1b_runtime_result_is_rejected_after_transport_decode(self):
        with LocalProcessHarness(command("invalid-runtime-result"), self.manifest) as harness:
            hs = harness.handshake()
            with self.assertRaisesRegex(HarnessError, "result-runtime-contract-invalid:provenance-plugin-id-mismatch"):
                harness.invoke(invocation(hs))

    def test_diagnostic_notification_can_arrive_before_response(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            hs = harness.handshake()
            result = harness.invoke(invocation(hs, parameters={"emit_diagnostic": True}))
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(harness.diagnostics), 1)
            self.assertEqual(harness.diagnostics[0]["record_type"], "diagnostic")

    def test_cancel_request_roundtrip(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            harness.handshake()
            cancel = {
                "record_type": "cancel-request",
                "invocation_id": "invoke:transport:cancel",
                "requested_at": "2026-08-23T20:15:10Z",
                "reason": "test cancellation",
            }
            ack = harness.cancel(cancel)
            self.assertTrue(ack["acknowledged"])
            self.assertEqual(ack["invocation_id"], cancel["invocation_id"])

    def test_malformed_cancel_ack_fails_closed(self):
        with LocalProcessHarness(command("bad-cancel-ack"), self.manifest) as harness:
            harness.handshake()
            cancel = {
                "record_type": "cancel-request",
                "invocation_id": "invoke:transport:cancel",
                "requested_at": "2026-08-23T20:15:10Z",
                "reason": "test cancellation",
            }
            with self.assertRaisesRegex(HarnessError, "invalid-cancel-ack-record"):
                harness.cancel(cancel)

    def test_harness_rejects_invoke_before_handshake_locally(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            fake_hs = {"identity": {"runtime_instance_id": "runtime:synthetic:transport:1"}}
            with self.assertRaisesRegex(HarnessError, "invoke-before-handshake"):
                harness.invoke(invocation(fake_hs))

    def test_plugin_rejects_raw_invoke_before_handshake(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            fake_hs = {"identity": {"runtime_instance_id": "runtime:synthetic:transport:1"}}
            with self.assertRaisesRegex(RemoteProtocolError, "Handshake required"):
                harness.raw_request("raiatea.invoke", invocation(fake_hs))

    def test_transport_id_reuse_as_invocation_id_is_detected(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            hs = harness.handshake()
            req = invocation(hs)
            harness._next_rpc_id = lambda: req["invocation_id"]  # type: ignore[method-assign]
            with self.assertRaisesRegex(HarnessError, "transport-id-must-not-equal-invocation-id"):
                harness.invoke(req)

    def test_unknown_method_is_transport_error(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            harness.handshake()
            with self.assertRaisesRegex(RemoteProtocolError, "Method not found"):
                harness.raw_request("raiatea.unknown", {})

    def test_stdout_noise_is_protocol_violation(self):
        with LocalProcessHarness(command("noise-startup"), self.manifest) as harness:
            with self.assertRaisesRegex(HarnessError, "protocol-frame-invalid:malformed-json-frame"):
                harness.handshake()

    def test_bad_jsonrpc_response_version_fails_closed(self):
        with LocalProcessHarness(command("bad-version"), self.manifest) as harness:
            with self.assertRaisesRegex(HarnessError, "unsupported-jsonrpc-version"):
                harness.handshake()

    def test_duplicate_response_id_fails_on_next_exchange(self):
        with LocalProcessHarness(command("duplicate-response"), self.manifest) as harness:
            hs = harness.handshake()
            with self.assertRaisesRegex(HarnessError, "duplicate-jsonrpc-response-id"):
                harness.invoke(invocation(hs))

    def test_process_crash_during_startup_is_not_domain_result(self):
        with LocalProcessHarness(command("crash-startup"), self.manifest) as harness:
            with self.assertRaises(ProcessExited):
                harness.handshake()

    def test_process_crash_during_invocation_is_not_runtime_business_failure(self):
        with LocalProcessHarness(command("crash-invoke"), self.manifest) as harness:
            hs = harness.handshake()
            with self.assertRaises(ProcessExited):
                harness.invoke(invocation(hs))

    def test_stderr_structured_text_is_not_accepted_as_runtime_diagnostic(self):
        harness = LocalProcessHarness(command("stderr-diagnostic"), self.manifest)
        try:
            harness.start()
            harness.handshake()
            self.assertEqual(harness.diagnostics, [])
        finally:
            harness.close()
        self.assertIn("diagnostic", harness.stderr_text)

    def test_raw_inline_content_is_rejected_before_write(self):
        with LocalProcessHarness(command(), self.manifest) as harness:
            with self.assertRaisesRegex(T.TransportError, "inline-large-payload-field-forbidden"):
                harness.raw_request("raiatea.invoke", {"content": "x"})


if __name__ == "__main__":
    unittest.main()
