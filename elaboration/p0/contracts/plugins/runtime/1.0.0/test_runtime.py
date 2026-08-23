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


def manifest(name: str) -> dict:
    return json.loads((PLUGIN_ROOT / "examples" / name).read_text(encoding="utf-8"))


def source_handshake(m: dict) -> dict:
    return {
        "record_type": "handshake",
        "identity": {
            "plugin_id": m["plugin"]["plugin_id"],
            "plugin_version": m["plugin"]["version"],
            "runtime_instance_id": "runtime:source:1",
            "manifest_fingerprint": V.canonical_manifest_fingerprint(m),
            "runtime_contract_version": "1.0.0",
        },
        "advertised_profiles": [
            {"capability_id": cap["capability_id"], "profile_id": p["profile_id"]}
            for cap in m["capabilities"] for p in cap["profiles"]
        ],
        "observed_at": "2026-08-23T19:45:00Z",
    }


def source_request(m: dict, hs: dict) -> dict:
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:1",
        "idempotency_key": "idem:1",
        "runtime_instance_id": hs["identity"]["runtime_instance_id"],
        "capability": {"capability_id": "source.discover", "profile_id": "local-read-only"},
        "inputs": [],
        "runtime_context": {
            "workspace_scope_id": "workspace:1",
            "rights_decision_ref": "rights:1",
            "secret_leases": [],
        },
        "deadline_at": "2026-08-23T19:46:00Z",
        "parameters": {"recursive": True, "max_depth": 4},
    }


def completed_source_result(m: dict, request: dict) -> dict:
    return {
        "record_type": "invocation-result",
        "invocation_id": request["invocation_id"],
        "runtime_instance_id": request["runtime_instance_id"],
        "status": "completed",
        "outputs": [
            {
                "kind": "record-ref",
                "record_ref": {
                    "ref_id": "source-ref:1",
                    "contract_id": "raiatea.source-reference",
                    "contract_version": "0.1.0",
                    "record_kind": "SourceReference",
                },
            }
        ],
        "diagnostic_refs": [],
        "provenance": {
            "plugin_id": m["plugin"]["plugin_id"],
            "plugin_version": m["plugin"]["version"],
            "runtime_instance_id": request["runtime_instance_id"],
            "invocation_id": request["invocation_id"],
            "capability": request["capability"],
            "started_at": "2026-08-23T19:45:01Z",
            "ended_at": "2026-08-23T19:45:02Z",
            "input_refs": [],
            "output_refs": ["source-ref:1"],
            "rights_decision_ref": "rights:1",
        },
    }


class RuntimeContractTests(unittest.TestCase):
    def setUp(self):
        self.source_manifest = manifest("local-read-only-source.json")
        self.handshake = source_handshake(self.source_manifest)
        self.request = source_request(self.source_manifest, self.handshake)

    def test_valid_source_flow(self):
        V.validate_handshake(self.handshake, self.source_manifest)
        V.validate_transition({
            "record_type": "lifecycle-transition",
            "runtime_instance_id": "runtime:source:1",
            "from": "starting",
            "to": "ready",
            "basis": "compatible handshake validated",
            "observed_at": "2026-08-23T19:45:00Z",
        })
        V.validate_invocation(self.request, self.source_manifest, self.handshake)
        V.validate_result(completed_source_result(self.source_manifest, self.request), self.request, self.source_manifest)

    def test_runtime_cannot_broaden_manifest_capabilities(self):
        value = copy.deepcopy(self.handshake)
        value["advertised_profiles"].append({"capability_id": "source.acquire", "profile_id": "undeclared"})
        with self.assertRaisesRegex(V.RuntimeContractError, "runtime-broadens-manifest-capabilities"):
            V.validate_handshake(value, self.source_manifest)

    def test_manifest_fingerprint_mismatch_is_incompatible(self):
        value = copy.deepcopy(self.handshake)
        value["identity"]["manifest_fingerprint"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(V.RuntimeContractError, "handshake-manifest-fingerprint-mismatch"):
            V.validate_handshake(value, self.source_manifest)

    def test_illegal_lifecycle_transition_fails(self):
        with self.assertRaisesRegex(V.RuntimeContractError, "illegal-lifecycle-transition"):
            V.validate_transition({"record_type": "lifecycle-transition", "from": "ready", "to": "starting"})

    def test_unknown_profile_invocation_fails(self):
        value = copy.deepcopy(self.request)
        value["capability"]["profile_id"] = "unknown"
        with self.assertRaisesRegex(V.RuntimeContractError, "invocation-profile-not-in-manifest"):
            V.validate_invocation(value, self.source_manifest, self.handshake)

    def test_control_plane_path_parameter_fails(self):
        value = copy.deepcopy(self.request)
        value["parameters"] = {"path": "/tmp/source.pdf"}
        with self.assertRaisesRegex(V.RuntimeContractError, "control-plane-parameter-key-forbidden"):
            V.validate_invocation(value, self.source_manifest, self.handshake)

    def test_control_plane_content_parameter_fails(self):
        value = copy.deepcopy(self.request)
        value["parameters"] = {"content": "x" * 100}
        with self.assertRaisesRegex(V.RuntimeContractError, "control-plane-parameter-key-forbidden"):
            V.validate_invocation(value, self.source_manifest, self.handshake)

    def test_secret_lease_must_not_contain_value(self):
        value = copy.deepcopy(self.request)
        value["runtime_context"]["secret_leases"] = [{"secret_name": "TOKEN", "lease_id": "lease:1", "value": "secret"}]
        with self.assertRaisesRegex(V.RuntimeContractError, "secret-lease-must-not-contain-value"):
            V.validate_invocation(value, self.source_manifest, self.handshake)

    def test_cancelled_result_requires_cancelled_error(self):
        result = completed_source_result(self.source_manifest, self.request)
        result["status"] = "cancelled"
        result["outputs"] = []
        result["provenance"]["output_refs"] = []
        result["error"] = {"code": "timeout", "message": "wrong", "retryable": False}
        with self.assertRaisesRegex(V.RuntimeContractError, "cancelled-status-requires-cancelled-error"):
            V.validate_result(result, self.request, self.source_manifest)

    def test_timeout_result_requires_timeout_error(self):
        result = completed_source_result(self.source_manifest, self.request)
        result["status"] = "timeout"
        result["outputs"] = []
        result["provenance"]["output_refs"] = []
        result["error"] = {"code": "plugin-internal-failure", "message": "wrong", "retryable": False}
        with self.assertRaisesRegex(V.RuntimeContractError, "timeout-status-requires-timeout-error"):
            V.validate_result(result, self.request, self.source_manifest)

    def test_diagnostic_secret_echo_fails_when_core_knows_value(self):
        diagnostic = {"message": "request failed token=supersecret"}
        with self.assertRaisesRegex(V.RuntimeContractError, "diagnostic-contains-secret-value"):
            V.validate_diagnostic_no_secret_values(diagnostic, {"supersecret"})

    def test_extractor_record_output_must_reference_e05(self):
        m = manifest("benchmark-backed-extractor.json")
        hs = source_handshake(m)
        hs["identity"]["runtime_instance_id"] = "runtime:extractor:1"
        req = {
            "record_type": "invocation-request",
            "invocation_id": "extract:1",
            "idempotency_key": "extract-idem:1",
            "runtime_instance_id": "runtime:extractor:1",
            "capability": {"capability_id": "extract.run", "profile_id": "pdf-native-no-ocr"},
            "inputs": [{"kind": "asset-handle", "handle": {"handle_id": "h:1", "lease_id": "l:1", "access": "read", "media_type": "application/pdf"}}],
            "runtime_context": {"workspace_scope_id": "workspace:1", "secret_leases": []},
            "deadline_at": "2026-08-23T19:46:00Z",
            "parameters": {},
        }
        V.validate_handshake(hs, m)
        V.validate_invocation(req, m, hs)
        result = {
            "record_type": "invocation-result",
            "invocation_id": "extract:1",
            "runtime_instance_id": "runtime:extractor:1",
            "status": "completed",
            "outputs": [{"kind": "record-ref", "record_ref": {"ref_id": "wrong:1", "contract_id": "provider.native", "contract_version": "1", "record_kind": "Document"}}],
            "diagnostic_refs": [],
            "provenance": {
                "plugin_id": m["plugin"]["plugin_id"],
                "plugin_version": m["plugin"]["version"],
                "runtime_instance_id": "runtime:extractor:1",
                "invocation_id": "extract:1",
                "capability": req["capability"],
                "started_at": "2026-08-23T19:45:01Z",
                "ended_at": "2026-08-23T19:45:02Z",
                "input_refs": ["h:1"],
                "output_refs": ["wrong:1"],
            },
        }
        with self.assertRaisesRegex(V.RuntimeContractError, "extractor-record-output-must-reference-e05"):
            V.validate_result(result, req, m)


if __name__ == "__main__":
    unittest.main()
