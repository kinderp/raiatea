from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from . import proof_test_support as S

TRANSPORT_ROOT = S.REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "transport" / "0.1.0"
if str(TRANSPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(TRANSPORT_ROOT))
from process_harness import HarnessError, LocalProcessHarness  # noqa: E402

MANIFEST_VALIDATOR_PATH = S.REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "1.0.0" / "validate_manifest.py"
TRANSFORM_VALIDATOR_PATH = S.REPO_ROOT / "elaboration" / "p0" / "contracts" / "transformations" / "0.1.0" / "validate_transformation.py"

_MANIFEST_SPEC = importlib.util.spec_from_file_location("v1e_manifest_validator", MANIFEST_VALIDATOR_PATH)
MANIFEST_VALIDATOR = importlib.util.module_from_spec(_MANIFEST_SPEC)
assert _MANIFEST_SPEC.loader is not None
_MANIFEST_SPEC.loader.exec_module(MANIFEST_VALIDATOR)

_TRANSFORM_SPEC = importlib.util.spec_from_file_location("v1e_transform_validator", TRANSFORM_VALIDATOR_PATH)
T = importlib.util.module_from_spec(_TRANSFORM_SPEC)
assert _TRANSFORM_SPEC.loader is not None
_TRANSFORM_SPEC.loader.exec_module(T)


def _records(bundle: dict):
    values = bundle.get("records")
    if not isinstance(values, dict):
        raise AssertionError("proof bundle records missing")
    transformation = next(value for value in values.values() if value.get("record_kind") == "TransformationRecord")
    derived = next(value for value in values.values() if value.get("record_kind") == "DerivedArtifactRecord")
    return transformation, derived


def _assert_no_public_path_fields(value) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in {"path", "relative_path", "host_path", "filesystem_path"}:
                raise AssertionError(f"public transformation record leaked path field: {key}")
            _assert_no_public_path_fields(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_public_path_fields(child)


class TransformerProofTests(unittest.TestCase):
    def setUp(self):
        self.runtime = S.reset_runtime()
        self.manifest = S.load_manifest()
        MANIFEST_VALIDATOR.validate(self.manifest)

    def _run(self, invocation_id: str = "invoke:v1e:transform:1"):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"], invocation_id=invocation_id)
            result = harness.invoke(request)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(harness.diagnostics), 1)
        return request, result, S.read_output_bytes(), S.read_bundle()

    def test_transform_is_out_of_process_deterministic_and_preserves_input(self):
        before = self.runtime["input_path"].read_bytes()
        request, result, output, bundle = self._run()
        after = self.runtime["input_path"].read_bytes()
        self.assertEqual(before, after)
        self.assertEqual(output, b"alpha\nbeta\ngamma\n")
        self.assertNotEqual(before, output)
        transformation, derived = _records(bundle)
        T.validate_pair(transformation, derived)
        T.validate_bytes(transformation["input_artifact"], before, "input")
        T.validate_bytes(transformation["output_artifact"], output, "output")
        self.assertEqual(transformation["operation"]["profile_id"], "normalize-newlines-v1")
        self.assertEqual(transformation["rights_decision_ref"], request["runtime_context"]["rights_decision_ref"])
        self.assertEqual(result["provenance"]["input_refs"], [S.INPUT_HANDLE_ID])
        self.assertIn(S.DATA_HANDLE_ID, result["provenance"]["output_refs"])
        self.assertIn(transformation["transformation_id"], result["provenance"]["output_refs"])
        _assert_no_public_path_fields(bundle["records"])
        self.assertNotIn(str(self.runtime["input_path"].resolve()), json.dumps(bundle, sort_keys=True))

    def test_repeated_identical_input_produces_byte_identical_output(self):
        _, _, output1, bundle1 = self._run("invoke:v1e:transform:first")
        transformation1, derived1 = _records(bundle1)
        S.reset_runtime(self.runtime["input_bytes"])
        _, _, output2, bundle2 = self._run("invoke:v1e:transform:second")
        transformation2, derived2 = _records(bundle2)
        self.assertEqual(output1, output2)
        self.assertEqual(T.sha256_bytes(output1), T.sha256_bytes(output2))
        self.assertEqual(transformation1["input_artifact"], transformation2["input_artifact"])
        self.assertEqual(transformation1["output_artifact"], transformation2["output_artifact"])
        self.assertEqual(derived1["artifact"], derived2["artifact"])
        self.assertEqual(derived1["derivation"]["source_artifact"], derived2["derivation"]["source_artifact"])
        self.assertNotEqual(transformation1["transformation_id"], transformation2["transformation_id"])

    def test_wrong_media_type_is_structured_runtime_failure(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["inputs"][0]["handle"]["media_type"] = "application/octet-stream"
            result = harness.invoke(request)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"]["code"], "invalid-input-handle")

    def test_undeclared_profile_is_rejected_before_plugin_operation(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["capability"]["profile_id"] = "undeclared"
            with self.assertRaisesRegex(HarnessError, "invocation-profile-not-in-manifest"):
                harness.invoke(request)

    def test_input_handle_with_write_access_is_rejected_before_plugin(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["inputs"][0]["handle"]["access"] = "write-once-output"
            with self.assertRaisesRegex(HarnessError, "input-asset-handle-must-be-read"):
                harness.invoke(request)

    def test_output_target_with_read_access_is_rejected_before_plugin(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["output_targets"][0]["access"] = "read"
            with self.assertRaisesRegex(HarnessError, "output-target-must-be-write-once"):
                harness.invoke(request)

    def test_expired_input_handle_is_rejected_before_plugin(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["inputs"][0]["handle"]["expires_at"] = "2020-01-01T00:00:00Z"
            with self.assertRaisesRegex(HarnessError, "lease-expires-before-deadline"):
                harness.invoke(request)

    def test_non_core_issued_output_target_fails_closed(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["output_targets"][0]["handle_id"] = "handle:v1e:not-issued"
            result = harness.invoke(request)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"]["code"], "output-contract-violation")

    def test_same_input_output_artifact_identity_fails(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["parameters"]["output_artifact_id"] = request["parameters"]["input_artifact_id"]
            result = harness.invoke(request)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"]["code"], "output-contract-violation")

    def test_input_fingerprint_mismatch_fails(self):
        with LocalProcessHarness(S.transformer_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.request(hs["identity"]["runtime_instance_id"])
            request["inputs"][0]["handle"]["fingerprint"] = "sha256:" + "0" * 64
            result = harness.invoke(request)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"]["code"], "invalid-input-handle")


if __name__ == "__main__":
    unittest.main()
