from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
PLUGIN_ROOT = ROOT.parents[1] / "1.0.0"
SPEC = importlib.util.spec_from_file_location("runtime_validator", ROOT / "validate_runtime.py")
V = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(V)


def manifest() -> dict:
    return json.loads((PLUGIN_ROOT / "examples" / "local-read-only-source.json").read_text(encoding="utf-8"))


def handshake(m: dict) -> dict:
    return {
        "record_type": "handshake",
        "identity": {
            "plugin_id": m["plugin"]["plugin_id"],
            "plugin_version": m["plugin"]["version"],
            "runtime_instance_id": "runtime:source:bounds",
            "manifest_fingerprint": V.canonical_manifest_fingerprint(m),
            "runtime_contract_version": "1.0.0",
        },
        "advertised_profiles": [
            {"capability_id": cap["capability_id"], "profile_id": profile["profile_id"]}
            for cap in m["capabilities"]
            for profile in cap["profiles"]
        ],
        "observed_at": "2026-08-23T19:45:00Z",
    }


def request(m: dict, hs: dict) -> dict:
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:bounds:1",
        "idempotency_key": "idem:bounds:1",
        "runtime_instance_id": hs["identity"]["runtime_instance_id"],
        "capability": {"capability_id": "source.discover", "profile_id": "local-read-only"},
        "inputs": [],
        "output_targets": [],
        "runtime_context": {"workspace_scope_id": "workspace:1", "secret_leases": []},
        "deadline_at": "2026-08-23T19:46:00Z",
        "parameters": {},
    }


def asset_result(m: dict, req: dict, handle: dict) -> dict:
    return {
        "record_type": "invocation-result",
        "invocation_id": req["invocation_id"],
        "runtime_instance_id": req["runtime_instance_id"],
        "status": "completed",
        "outputs": [{"kind": "asset-handle", "handle": handle}],
        "diagnostic_refs": [],
        "provenance": {
            "plugin_id": m["plugin"]["plugin_id"],
            "plugin_version": m["plugin"]["version"],
            "runtime_instance_id": req["runtime_instance_id"],
            "invocation_id": req["invocation_id"],
            "capability": req["capability"],
            "started_at": "2026-08-23T19:45:01Z",
            "ended_at": "2026-08-23T19:45:02Z",
            "input_refs": [
                item["handle"]["handle_id"] if item["kind"] == "asset-handle" else item["record_ref"]["ref_id"]
                for item in req["inputs"]
            ],
            "output_refs": [handle["handle_id"]],
        },
    }


class RuntimeHandleBoundsTests(unittest.TestCase):
    def setUp(self):
        self.manifest = manifest()
        self.handshake = handshake(self.manifest)
        self.request = request(self.manifest, self.handshake)

    def test_input_lease_must_cover_invocation_deadline(self):
        value = copy.deepcopy(self.request)
        value["inputs"] = [{
            "kind": "asset-handle",
            "handle": {
                "handle_id": "in:1",
                "lease_id": "lease:in:1",
                "access": "read",
                "expires_at": "2026-08-23T19:45:59Z",
            },
        }]
        with self.assertRaisesRegex(V.RuntimeContractError, "input-handle-lease-expires-before-deadline"):
            V.validate_invocation(value, self.manifest, self.handshake)

    def test_output_target_lease_must_cover_invocation_deadline(self):
        value = copy.deepcopy(self.request)
        value["output_targets"] = [{
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "expires_at": "2026-08-23T19:45:59Z",
        }]
        with self.assertRaisesRegex(V.RuntimeContractError, "output-target-lease-expires-before-deadline"):
            V.validate_invocation(value, self.manifest, self.handshake)

    def test_same_handle_cannot_be_read_input_and_output_target(self):
        value = copy.deepcopy(self.request)
        value["inputs"] = [{
            "kind": "asset-handle",
            "handle": {"handle_id": "shared:1", "lease_id": "lease:read", "access": "read"},
        }]
        value["output_targets"] = [{
            "handle_id": "shared:1",
            "lease_id": "lease:write",
            "access": "write-once-output",
        }]
        with self.assertRaisesRegex(V.RuntimeContractError, "handle-cannot-be-input-and-output-target"):
            V.validate_invocation(value, self.manifest, self.handshake)

    def test_output_must_not_exceed_core_byte_limit(self):
        req = copy.deepcopy(self.request)
        req["output_targets"] = [{
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "byte_length": 10,
        }]
        V.validate_invocation(req, self.manifest, self.handshake)
        result = asset_result(self.manifest, req, {
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "byte_length": 11,
            "fingerprint": "sha256:" + "a" * 64,
        })
        with self.assertRaisesRegex(V.RuntimeContractError, "output-handle-exceeds-authorized-byte-limit"):
            V.validate_result(result, req, self.manifest)

    def test_completed_output_asset_requires_actual_length_and_fingerprint(self):
        req = copy.deepcopy(self.request)
        req["output_targets"] = [{
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "byte_length": 10,
        }]
        result = asset_result(self.manifest, req, {
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "byte_length": 5,
        })
        with self.assertRaisesRegex(V.RuntimeContractError, "output-handle-fingerprint-required"):
            V.validate_result(result, req, self.manifest)

    def test_plugin_cannot_extend_output_lease_metadata(self):
        req = copy.deepcopy(self.request)
        req["output_targets"] = [{
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "expires_at": "2026-08-23T19:47:00Z",
        }]
        result = asset_result(self.manifest, req, {
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "expires_at": "2026-08-23T20:00:00Z",
            "byte_length": 5,
            "fingerprint": "sha256:" + "b" * 64,
        })
        with self.assertRaisesRegex(V.RuntimeContractError, "output-handle-expiry-mismatch"):
            V.validate_result(result, req, self.manifest)

    def test_valid_bounded_output_handle_passes(self):
        req = copy.deepcopy(self.request)
        req["output_targets"] = [{
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "media_type": "application/json",
            "byte_length": 10,
            "expires_at": "2026-08-23T19:47:00Z",
        }]
        V.validate_invocation(req, self.manifest, self.handshake)
        result = asset_result(self.manifest, req, {
            "handle_id": "out:1",
            "lease_id": "lease:out:1",
            "access": "write-once-output",
            "media_type": "application/json",
            "byte_length": 5,
            "fingerprint": "sha256:" + "c" * 64,
            "expires_at": "2026-08-23T19:47:00Z",
        })
        V.validate_result(result, req, self.manifest)


if __name__ == "__main__":
    unittest.main()
