from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from . import proof_broker as BROKER
from . import proof_test_support as S

TRANSPORT_ROOT = S.REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "transport" / "0.1.0"
if str(TRANSPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(TRANSPORT_ROOT))
from process_harness import HarnessError, LocalProcessHarness, ProcessExited  # noqa: E402

MANIFEST_VALIDATOR_PATH = S.REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "1.0.0" / "validate_manifest.py"
E05_VALIDATOR_PATH = S.REPO_ROOT / "elaboration" / "p0" / "contracts" / "extraction" / "0.1.0" / "validate_contract.py"

_MANIFEST_SPEC = importlib.util.spec_from_file_location("v1d_manifest_validator", MANIFEST_VALIDATOR_PATH)
MANIFEST_VALIDATOR = importlib.util.module_from_spec(_MANIFEST_SPEC)
assert _MANIFEST_SPEC.loader is not None
_MANIFEST_SPEC.loader.exec_module(MANIFEST_VALIDATOR)

_E05_SPEC = importlib.util.spec_from_file_location("v1d_e05_validator", E05_VALIDATOR_PATH)
E05 = importlib.util.module_from_spec(_E05_SPEC)
assert _E05_SPEC.loader is not None
_E05_SPEC.loader.exec_module(E05)


def _find_record(bundle: dict, record_kind: str) -> dict:
    for ref in bundle["record_refs"]:
        if ref["record_kind"] == record_kind:
            return bundle["records"][ref["ref_id"]]
    raise AssertionError(f"record kind not found: {record_kind}")


def _all_coordinate_values(representation: dict):
    for unit in representation.get("units", []):
        coordinate = unit.get("coordinate")
        if isinstance(coordinate, dict) and coordinate.get("value_state") == "populated":
            value = coordinate.get("value")
            if isinstance(value, dict):
                yield value


def _assert_no_public_path_fields(value) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in {"path", "relative_path", "host_path", "filesystem_path"}:
                raise AssertionError(f"public proof record leaked path field: {key}")
            _assert_no_public_path_fields(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_public_path_fields(child)


def _validate_b02_epub_representation(representation: dict) -> None:
    """Proof-level cross-record guard exposed by the first real B-02 plugin.

    E-05 0.1.0 validates each SourceCoordinate variant internally but does not yet
    bind source_ref.source_class to a coordinate family. The v1d proof therefore
    adds this bounded B-02 conformance assertion rather than silently changing the
    accepted E-05 contract inside a transport-validation PR.
    """
    E05.validate_representation(representation)
    source_ref = representation.get("source_ref")
    if not isinstance(source_ref, dict) or source_ref.get("source_class") != "B-02":
        raise E05.ContractError("v1d-b02-source-class-required")
    for value in _all_coordinate_values(representation):
        if value.get("kind") != "epub-logical":
            raise E05.ContractError("v1d-b02-requires-epub-logical-coordinate")
        if "page_index" in value or "bbox_points_bottom_left" in value:
            raise E05.ContractError("v1d-b02-must-not-carry-pdf-coordinate-fields")


class SourceProofTests(unittest.TestCase):
    def setUp(self):
        self.runtime = S.reset_runtime()
        self.manifest = S.load_manifest(S.SOURCE_MANIFEST_PATH)
        MANIFEST_VALIDATOR.validate(self.manifest)

    def test_source_proof_runs_out_of_process_without_path_leak(self):
        with LocalProcessHarness(S.source_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.source_request(hs["identity"]["runtime_instance_id"])
            result = harness.invoke(request)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(harness.diagnostics), 1)

        bundle = S.load_output_bundle("handle:v1d:source:bundle", "lease:v1d:source:bundle")
        self.assertTrue(bundle["proof_only"])
        self.assertFalse(bundle["location_exposed"])
        self.assertEqual(len(bundle["records"]), 2)
        serialized = json.dumps(bundle, sort_keys=True)
        self.assertNotIn(str(self.runtime["source_root"].resolve()), serialized)
        self.assertNotIn("relative_path", serialized)
        _assert_no_public_path_fields(bundle["records"])
        for row in bundle["records"]:
            self.assertFalse(row.get("location_exposed", True))
            self.assertTrue(row["fingerprint"].startswith("sha256:"))
        self.assertEqual(self.manifest["permissions"]["network"], [])
        self.assertTrue(all(row["mode"] == "read" for row in self.manifest["permissions"]["filesystem"]))

    def test_source_write_or_acquire_capability_is_rejected_before_plugin_operation(self):
        with LocalProcessHarness(S.source_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.source_request(hs["identity"]["runtime_instance_id"])
            request["capability"] = {"capability_id": "source.acquire", "profile_id": "local-read-only"}
            with self.assertRaisesRegex(HarnessError, "invocation-profile-not-in-manifest"):
                harness.invoke(request)

    def test_source_scope_escape_fails_as_runtime_error_not_transport_error(self):
        broker = json.loads(BROKER.BROKER_PATH.read_text(encoding="utf-8"))
        broker["workspace_scopes"]["workspace:v1d:source"] = "../outside"
        BROKER.BROKER_PATH.write_text(json.dumps(broker), encoding="utf-8")
        with LocalProcessHarness(S.source_command(), self.manifest) as harness:
            hs = harness.handshake()
            result = harness.invoke(S.source_request(hs["identity"]["runtime_instance_id"]))
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"]["code"], "unauthorized-runtime-request")
            self.assertIn("scope-escape", result["error"]["message"])

    def test_source_process_crash_maps_to_post_handshake_failed_lifecycle(self):
        harness = LocalProcessHarness(S.source_command(), self.manifest)
        try:
            harness.start()
            hs = harness.handshake()
            request = S.source_request(hs["identity"]["runtime_instance_id"])
            request["parameters"] = {"proof_fault": "crash"}
            with self.assertRaises(ProcessExited):
                harness.invoke(request)
        finally:
            harness.close()
        self.assertIn(("ready", "failed"), [(row["from"], row["to"]) for row in harness.lifecycle_events])


class EpubExtractorProofTests(unittest.TestCase):
    def setUp(self):
        self.runtime = S.reset_runtime()
        self.manifest = S.load_manifest(S.EXTRACTOR_MANIFEST_PATH)
        MANIFEST_VALIDATOR.validate(self.manifest)

    def _successful_bundle(self) -> dict:
        with LocalProcessHarness(S.extractor_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.extractor_request(hs["identity"]["runtime_instance_id"], self.runtime["epub_path"])
            result = harness.invoke(request)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(harness.diagnostics), 1)
            self.assertTrue(all(
                output["record_ref"]["contract_id"] == "raiatea.extraction.processing-run"
                for output in result["outputs"]
                if output["kind"] == "record-ref"
            ))
        return S.load_output_bundle("handle:v1d:epub:bundle", "lease:v1d:epub:bundle")

    def test_epub_extractor_emits_valid_e05_records_and_logical_coordinates(self):
        bundle = self._successful_bundle()
        self.assertFalse(bundle["provider_native_schema_exposed"])
        kinds = set()
        for ref in bundle["record_refs"]:
            record = bundle["records"][ref["ref_id"]]
            kinds.add(E05.validate_any(record))
        self.assertEqual(kinds, {"processing-run", "provider-evidence", "normalized-representation"})

        normalized = _find_record(bundle, "NormalizedRepresentationRecord")
        _validate_b02_epub_representation(normalized)
        coordinates = list(_all_coordinate_values(normalized))
        self.assertTrue(coordinates)
        self.assertTrue(all(value["kind"] == "epub-logical" for value in coordinates))
        self.assertTrue(all("page_index" not in value for value in coordinates))
        self.assertTrue(all("bbox_points_bottom_left" not in value for value in coordinates))

        provider = _find_record(bundle, "ProviderEvidenceRecord")
        self.assertEqual(provider["provider"]["provider_id"], "python-stdlib")
        self.assertEqual(provider["route_profile"]["route_profile_id"], "direct-epub-stdlib")
        extractor_profiles = {
            profile["profile_id"]
            for capability in self.manifest["capabilities"]
            if capability["capability_id"] == "extract.run"
            for profile in capability["profiles"]
        }
        self.assertIn("epub-direct-stdlib", extractor_profiles)

    def test_wrong_media_type_is_structured_runtime_failure(self):
        with LocalProcessHarness(S.extractor_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.extractor_request(hs["identity"]["runtime_instance_id"], self.runtime["epub_path"])
            request["inputs"][0]["handle"]["media_type"] = "application/pdf"
            result = harness.invoke(request)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["error"]["code"], "invalid-input-handle")

    def test_undeclared_extractor_profile_is_rejected_before_plugin_operation(self):
        with LocalProcessHarness(S.extractor_command(), self.manifest) as harness:
            hs = harness.handshake()
            request = S.extractor_request(hs["identity"]["runtime_instance_id"], self.runtime["epub_path"])
            request["capability"]["profile_id"] = "undeclared"
            with self.assertRaisesRegex(HarnessError, "invocation-profile-not-in-manifest"):
                harness.invoke(request)

    def test_expired_or_write_input_handle_is_rejected_by_v1b_before_plugin(self):
        with LocalProcessHarness(S.extractor_command(), self.manifest) as harness:
            hs = harness.handshake()
            expired = S.extractor_request(hs["identity"]["runtime_instance_id"], self.runtime["epub_path"])
            expired["inputs"][0]["handle"]["expires_at"] = "2020-01-01T00:00:00Z"
            with self.assertRaisesRegex(HarnessError, "lease-expires-before-deadline"):
                harness.invoke(expired)

            wrong_access = S.extractor_request(hs["identity"]["runtime_instance_id"], self.runtime["epub_path"])
            wrong_access["inputs"][0]["handle"]["access"] = "write-once-output"
            with self.assertRaisesRegex(HarnessError, "input-asset-handle-must-be-read"):
                harness.invoke(wrong_access)

    def test_epub_source_coordinate_must_not_accept_pdf_variant(self):
        bundle = self._successful_bundle()
        normalized = copy.deepcopy(_find_record(bundle, "NormalizedRepresentationRecord"))
        target = next(unit for unit in normalized["units"] if unit.get("coordinate", {}).get("value_state") == "populated")
        target["coordinate"]["value"] = {
            "kind": "pdf-geometric",
            "page_index": 0,
            "bbox_points_bottom_left": [0.0, 0.0, 10.0, 10.0],
        }
        with self.assertRaises(E05.ContractError):
            _validate_b02_epub_representation(normalized)


if __name__ == "__main__":
    unittest.main()
