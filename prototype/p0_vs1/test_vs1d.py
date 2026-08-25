from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.extraction_contract import validate_extraction_bundle
from prototype.p0_vs1.extraction_rights import (
    ExtractionRightsError,
    OFFICIAL_EXTRACTOR_PLUGIN_ID,
    decide_local_epub_extraction,
)
from prototype.p0_vs1.extraction_service import (
    DEFAULT_MANIFEST_PATH,
    EpubExtractionError,
    LocalEpubExtractionService,
    validate_vs1d_state,
)
from prototype.p0_vs1.local_process_client import LocalPluginProcessClient
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry, Vs1bReconciliationEngine
from prototype.p0_vs1.source_service import LocalSourceDiscoveryService


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"
_GEN_SPEC = importlib.util.spec_from_file_location("vs1d_fixture_generator", GENERATOR_PATH)
GENERATOR = importlib.util.module_from_spec(_GEN_SPEC)
assert _GEN_SPEC.loader is not None
_GEN_SPEC.loader.exec_module(GENERATOR)


FORBIDDEN_PATH_KEYS = {
    "path",
    "filepath",
    "file_path",
    "filename",
    "root",
    "relative_path",
    "location",
    "location_history",
}


def _assert_no_path_keys(testcase: unittest.TestCase, value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            testcase.assertNotIn(
                str(key).strip().lower().replace("-", "_"),
                FORBIDDEN_PATH_KEYS,
            )
            _assert_no_path_keys(testcase, child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_path_keys(testcase, child)


class Vs1dFixture(unittest.TestCase):
    unsafe = False

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()
        self.epub = self.root / "B02-EPUB-001.epub"
        if self.unsafe:
            GENERATOR.generate_epub_unsafe_path(self.epub)
        else:
            GENERATOR.generate_epub_spine(self.epub)
        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:library", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        self.reconciliation = Vs1bReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )
        self.reconciliation.reconcile_inventory()
        self.discovery = LocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:library",
        )
        discovered = self.discovery.discover(rights_evidence_state="known-permitted")
        self.source_ref_id = discovered["source_refs"][0]
        self.extraction = LocalEpubExtractionService(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()


class ExtractionRightsTests(Vs1dFixture):
    def test_only_known_permitted_can_cross_byte_processing_boundary(self) -> None:
        decision = decide_local_epub_extraction(
            self.scopes,
            "scope:library",
            plugin_id=OFFICIAL_EXTRACTOR_PLUGIN_ID,
            rights_evidence_state="known-permitted",
        )
        self.assertEqual(decision["rights_evidence_state"], "known-permitted")
        self.assertTrue(decision["source_bytes_shared"])
        self.assertEqual(
            decision["source_bytes_destination"],
            "same-host-core-private-workspace",
        )
        self.assertFalse(decision["remote_processing"])
        self.assertFalse(decision["redistribution"])
        self.assertFalse(decision["source_filesystem_mutation"])
        for state in ("unknown", "requires-review", "known-restricted"):
            with self.subTest(state=state):
                with self.assertRaises(ExtractionRightsError):
                    decide_local_epub_extraction(
                        self.scopes,
                        "scope:library",
                        plugin_id=OFFICIAL_EXTRACTOR_PLUGIN_ID,
                        rights_evidence_state=state,
                    )

    def test_rights_denial_does_not_mutate_catalog(self) -> None:
        before = self.store.load().revision
        with self.assertRaises(EpubExtractionError):
            self.extraction.extract(self.source_ref_id, rights_evidence_state="unknown")
        self.assertEqual(self.store.load().revision, before)
        self.assertNotIn("vs1d", self.store.load().payload)


class EpubExtractionProductTests(Vs1dFixture):
    def test_real_product_extractor_persists_text_structure_coordinates_and_provenance(self) -> None:
        result = self.extraction.extract(
            self.source_ref_id,
            rights_evidence_state="known-permitted",
        )
        self.assertEqual(result["status"], "completed")
        self.assertGreater(result["normalized_unit_count"], 0)

        persisted = self.store.load().payload["vs1d"]
        validate_vs1d_state(persisted, "scope:library")
        self.assertEqual(len(persisted["extractions"]), 1)
        row = persisted["extractions"][0]
        bundle = {
            "bundle_version": "raiatea.vs1d.e05-bundle.0.1.0",
            "record_kind": "E05ExtractionBundle",
            "source_ref_id": row["source_ref_id"],
            "source_fingerprint": row["source_fingerprint"],
            "record_refs": row["record_refs"],
            "records": row["records"],
        }
        validate_extraction_bundle(bundle)

        processing_runs = [
            row["records"][ref["ref_id"]]
            for ref in row["record_refs"]
            if ref["record_kind"] == "ProcessingRunRecord"
        ]
        self.assertEqual(len(processing_runs), 1)
        run = processing_runs[0]
        normalization_stages = [
            stage for stage in run["stages"]
            if stage["stage_kind"] == "normalization"
        ]
        self.assertEqual(len(normalization_stages), 1)
        self.assertEqual(
            normalization_stages[0]["executor"],
            {
                "kind": "raiatea-core",
                "operation_id": "normalize-provider-evidence",
            },
        )

        representations = [
            row["records"][ref["ref_id"]]
            for ref in row["record_refs"]
            if ref["record_kind"] == "NormalizedRepresentationRecord"
        ]
        self.assertEqual(len(representations), 1)
        representation = representations[0]
        surfaces = [
            unit["surface"]["value"]
            for unit in representation["units"]
            if unit["surface"].get("value_state") == "populated"
        ]
        self.assertIn("Introduction", surfaces)
        self.assertIn("The first chapter establishes the package order.", surfaces)
        self.assertIn("Next Chapter", surfaces)
        self.assertIn("The second chapter follows the first in the spine.", surfaces)
        self.assertTrue(representation["relations"])

        populated_coordinates = [
            unit["coordinate"]["value"]
            for unit in representation["units"]
            if unit["coordinate"].get("value_state") == "populated"
        ]
        self.assertTrue(populated_coordinates)
        self.assertTrue(
            all(coord["kind"] == "epub-logical" for coord in populated_coordinates)
        )
        self.assertTrue(
            any(coord["resource"].endswith("ch1.xhtml") for coord in populated_coordinates)
        )
        self.assertTrue(
            any(coord["resource"].endswith("ch2.xhtml") for coord in populated_coordinates)
        )
        self.assertTrue(all("page_index" not in coord for coord in populated_coordinates))
        self.assertTrue(
            all("bbox_points_bottom_left" not in coord for coord in populated_coordinates)
        )

        self.assertEqual(row["plugin"]["plugin_id"], OFFICIAL_EXTRACTOR_PLUGIN_ID)
        self.assertEqual(row["plugin"]["route_profile"], "epub-direct-stdlib")
        self.assertEqual(
            row["provenance"]["rights_decision_ref"],
            row["rights_decision"]["decision_id"],
        )
        serialized = json.dumps(row, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("B02-EPUB-001.epub", serialized)
        _assert_no_path_keys(self, row)

    def test_source_bytes_changed_after_discovery_fail_before_plugin_persistence(self) -> None:
        before = self.store.load().revision
        self.epub.write_bytes(self.epub.read_bytes() + b"changed")
        with self.assertRaisesRegex(EpubExtractionError, "changed-after-discovery"):
            self.extraction.extract(
                self.source_ref_id,
                rights_evidence_state="known-permitted",
            )
        self.assertEqual(self.store.load().revision, before)
        self.assertNotIn("vs1d", self.store.load().payload)

    def test_nonfresh_catalog_fails_before_extractor(self) -> None:
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "test-gap",
        }
        self.store.save(payload, expected_revision=current.revision)
        before = self.store.load().revision
        with self.assertRaisesRegex(EpubExtractionError, "catalog-not-fresh"):
            self.extraction.extract(
                self.source_ref_id,
                rights_evidence_state="known-permitted",
            )
        self.assertEqual(self.store.load().revision, before)

    def test_unknown_source_reference_fails_without_catalog_mutation(self) -> None:
        before = self.store.load().revision
        with self.assertRaisesRegex(EpubExtractionError, "source-reference-not-current"):
            self.extraction.extract(
                "source-ref:" + "0" * 64,
                rights_evidence_state="known-permitted",
            )
        self.assertEqual(self.store.load().revision, before)

    def test_catalog_change_during_extractor_run_rejects_stale_records(self) -> None:
        real_invoke = LocalPluginProcessClient.invoke
        other_store = CatalogStateStore(self.store.path)

        def invoke_then_change(client: LocalPluginProcessClient, request: dict) -> dict:
            result = real_invoke(client, request)
            current = other_store.load()
            payload = deepcopy(current.payload)
            payload["concurrent_marker"] = {"changed": True}
            other_store.save(payload, expected_revision=current.revision)
            return result

        with patch.object(LocalPluginProcessClient, "invoke", new=invoke_then_change):
            with self.assertRaisesRegex(
                EpubExtractionError,
                "catalog-changed-during-plugin-run",
            ):
                self.extraction.extract(
                    self.source_ref_id,
                    rights_evidence_state="known-permitted",
                )
        persisted = self.store.load().payload
        self.assertIn("concurrent_marker", persisted)
        self.assertNotIn("vs1d", persisted)

    def test_official_manifest_is_local_pathless_and_provider_observation_only(self) -> None:
        manifest = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["plugin"]["plugin_id"], OFFICIAL_EXTRACTOR_PLUGIN_ID)
        self.assertEqual(manifest["permissions"]["network"], [])
        self.assertEqual(manifest["permissions"]["filesystem"], [])
        self.assertEqual(manifest["permissions"]["secrets"], [])
        self.assertTrue(manifest["permissions"]["temporary_workspace"])
        self.assertEqual(manifest["capabilities"][0]["capability_id"], "extract.run")
        profile = manifest["capabilities"][0]["profiles"][0]
        self.assertEqual(profile["profile_id"], "epub-direct-stdlib")
        self.assertEqual(
            profile["output_classes"],
            ["vs1d-direct-epub-provider-observation"],
        )
        self.assertEqual(profile["contracts"], [])


class UnsafeEpubExtractionTests(Vs1dFixture):
    unsafe = True

    def test_unsafe_member_fails_without_fabricated_extraction_state(self) -> None:
        before = self.store.load().revision
        with self.assertRaisesRegex(EpubExtractionError, "run-not-publishable"):
            self.extraction.extract(
                self.source_ref_id,
                rights_evidence_state="known-permitted",
            )
        self.assertEqual(self.store.load().revision, before)
        self.assertNotIn("vs1d", self.store.load().payload)


if __name__ == "__main__":
    unittest.main()
