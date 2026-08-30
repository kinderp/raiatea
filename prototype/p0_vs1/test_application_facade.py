from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.application_facade import (
    ApplicationFacadeError,
    RaiateaApplicationFacade,
)
from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
)
from prototype.p0_vs1.pdf1b_e05_contract import build_pdf_extraction_bundle
from prototype.p0_vs1.pdf1b_rights import (
    POPPLER_PLUGIN_ID,
    POPPLER_PROFILE,
    decide_local_poppler_pdf_extraction,
)
from prototype.p0_vs1.pdf1b_service import PDF1B_STATE_VERSION
from prototype.p0_vs1.poppler_e05_adapter import adapt_poppler_observation
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry
from prototype.p0_vs1.source_contract import PDF_MEDIA_TYPE
from prototype.p0_vs1 import test_vs1e as vs1e_tests


PDFTOHTML_SHA = "sha256:70bd5fbb655a14d0b02cb32cb53a601d3b0842a63553a24d1a6a612cf9f0624e"
PDFINFO_SHA = "sha256:3293dda06d80e1e38dab859aa47368c2876aedc41cbc2e24e8fb9a4e66392078"


def plan(
    *criteria: tuple[str, str, str],
    sort_field: str = "source_ref_id",
    descending: bool = False,
) -> dict:
    return {
        "criteria": [
            {"field": field, "operator": operator, "value": value}
            for field, operator, value in criteria
        ],
        "sort_field": sort_field,
        "descending": descending,
    }


def _assert_no_internal_authority(
    testcase: unittest.TestCase,
    value: object,
    *,
    forbidden_strings: list[str],
) -> None:
    forbidden_keys = {
        "records",
        "record_refs",
        "provider_observation",
        "current_location",
        "location_history",
        "host_path",
        "workspace_path",
        "root",
        "path",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            testcase.assertNotIn(key, forbidden_keys)
            _assert_no_internal_authority(
                testcase,
                child,
                forbidden_strings=forbidden_strings,
            )
    elif isinstance(value, list):
        for child in value:
            _assert_no_internal_authority(
                testcase,
                child,
                forbidden_strings=forbidden_strings,
            )
    elif isinstance(value, str):
        for forbidden in forbidden_strings:
            testcase.assertNotIn(forbidden, value)


class _FakeSourcePlaneReader:
    """Contract fake proving extraction runtime replacement stays behind one seam."""

    def current_summaries(self, snapshot, source_refs):
        result = {}
        for source in source_refs:
            source_ref_id = source["source_ref_id"]
            representation_id = "source-plane-representation:" + source_ref_id.removeprefix(
                "source-ref:"
            )
            result[source_ref_id] = {
                "state": "current",
                "state_family": "source-plane-fake",
                "source_ref_id": source_ref_id,
                "provider": {
                    "provider_id": "source-plane-fake",
                    "version": "1",
                    "route_profile": "fake-profile",
                },
                "run": {"run_id": "source-plane-run:" + source_ref_id[-12:]},
                "representation": {
                    "representation_id": representation_id,
                    "unit_count": 1,
                    "coordinate_families": [],
                    "evidence_state_by_family": {
                        "surface": ["present"],
                        "semantic_role": ["unavailable"],
                        "coordinate": ["unavailable"],
                    },
                },
                "rights": None,
                "provenance": {"runtime": "source-plane-fake"},
                "diagnostics": {
                    "state": "measured",
                    "count": 0,
                    "by_severity": {},
                    "items": [],
                },
                "warnings": {
                    "state": "measured",
                    "count": 0,
                    "highest_severity": None,
                },
            }
        return result

    def representation_page(
        self,
        snapshot,
        representation_id,
        *,
        page_size,
        cursor,
    ):
        return {
            "representation_id": representation_id,
            "basis": "sha256:" + "f" * 64,
            "cursor": cursor,
            "next_cursor": None,
            "units": [
                {
                    "unit_ref": "fake-unit-1",
                    "surface": {
                        "state": "present",
                        "value_state": "populated",
                        "value": "Source Plane compatible",
                    },
                    "semantic_role": {
                        "state": "unavailable",
                        "value_state": "unknown",
                    },
                    "coordinate": {
                        "state": "unavailable",
                        "value_state": "unknown",
                    },
                }
            ],
        }


class ApplicationFacadeEpubTests(vs1e_tests.Vs1eFixture):
    def setUp(self) -> None:
        super().setUp()
        self.facade = RaiateaApplicationFacade(self.store, "scope:library")

    def assert_public(self, value: object) -> None:
        _assert_no_internal_authority(
            self,
            value,
            forbidden_strings=[str(self.base), str(self.root), str(self.outputs)],
        )

    def test_library_is_paged_and_uses_relative_catalog_location_without_ontology_upgrade(self) -> None:
        first = self.facade.library_page(page_size=1)
        self.assertEqual(first["catalog_freshness"], "fresh")
        self.assertEqual(first["counts_basis"], "current")
        self.assertEqual(first["total_known_items"], 2)
        self.assertEqual(len(first["items"]), 1)
        self.assertIsNotNone(first["next_cursor"])
        item = first["items"][0]
        self.assertIn("logical_candidate_ref", item)
        self.assertNotIn("logical_identity_ref", item)
        self.assertFalse(
            Path(item["location"]["current_relative_location"]).is_absolute()
        )
        self.assertEqual(item["freshness"]["content"], "current")
        self.assertEqual(item["warnings"]["state"], "measured")
        self.assertEqual(item["warnings"]["count"], 0)

        second = self.facade.library_page(
            page_size=1,
            cursor=first["next_cursor"],
        )
        self.assertEqual(len(second["items"]), 1)
        self.assertNotEqual(
            item["catalog_entry_ref"],
            second["items"][0]["catalog_entry_ref"],
        )
        self.assertIsNone(second["next_cursor"])
        self.assert_public(first)
        self.assert_public(second)

    def test_source_detail_and_representation_page_expose_only_application_models(self) -> None:
        item = self.facade.library_page(page_size=1)["items"][0]
        detail = self.facade.source_detail(item["item_ref"])
        self.assertEqual(detail["media_type"], "application/epub+zip")
        self.assertIn("semantic", detail["available_panels"])
        self.assertIn("provider-evidence", detail["available_panels"])
        self.assertEqual(detail["warning_summary"]["state"], "measured")
        self.assertEqual(detail["warnings"], [])
        self.assertEqual(len(detail["representations"]), 1)

        representation_id = detail["representations"][0]["representation_id"]
        first = self.facade.representation_page(
            representation_id,
            page_size=1,
        )
        self.assertEqual(len(first["units"]), 1)
        self.assertIn("surface", first["units"][0])
        self.assertIn("semantic_role", first["units"][0])
        self.assertIn("coordinate", first["units"][0])
        if first["next_cursor"] is not None:
            second = self.facade.representation_page(
                representation_id,
                page_size=1,
                cursor=first["next_cursor"],
            )
            self.assertTrue(second["units"])
            self.assert_public(second)
        self.assert_public(detail)
        self.assert_public(first)

    def test_stale_catalog_withholds_current_source_and_search_hits(self) -> None:
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "application-facade-test-gap",
        }
        self.store.save(payload, expected_revision=current.revision)

        library = self.facade.library_page()
        self.assertEqual(library["catalog_freshness"], "reconcile-required")
        self.assertEqual(library["counts_basis"], "last-known")
        self.assertTrue(library["items"])
        for item in library["items"]:
            self.assertIsNone(item["source_ref_id"])
            self.assertEqual(item["freshness"]["content"], "not-established")
            self.assertEqual(item["extraction"]["state"], "not-established")

        search = self.facade.search_page(
            plan(("semantic_type", "has", "heading"))
        )
        self.assertEqual(search["freshness"], "stale")
        self.assertEqual(search["items"], [])
        self.assertEqual(search["blocked_reason"], "upstream-not-current")
        self.assert_public(library)
        self.assert_public(search)

    def test_library_cursor_is_bound_to_catalog_basis(self) -> None:
        first = self.facade.library_page(page_size=1)
        cursor = first["next_cursor"]
        self.assertIsNotNone(cursor)

        vs1e_tests.GENERATOR.generate_epub_inert_active_content(
            self.root / "new-source.epub"
        )
        self.reconciliation.reconcile_inventory()
        with self.assertRaisesRegex(ApplicationFacadeError, "cursor-stale"):
            self.facade.library_page(page_size=1, cursor=cursor)

    def test_search_page_preserves_query_semantics_and_adds_application_pagination(self) -> None:
        first = self.facade.search_page(plan(), page_size=1)
        self.assertEqual(first["freshness"], "fresh")
        self.assertEqual(first["total_known_matches"], 2)
        self.assertEqual(len(first["items"]), 1)
        self.assertIsNotNone(first["next_cursor"])
        self.assertTrue(first["items"][0]["matched_content_refs"] == [])

        second = self.facade.search_page(
            plan(),
            page_size=1,
            cursor=first["next_cursor"],
        )
        self.assertEqual(second["freshness"], "fresh")
        self.assertEqual(len(second["items"]), 1)
        self.assertIsNone(second["next_cursor"])
        self.assert_public(first)
        self.assert_public(second)

    def test_source_plane_reader_can_replace_in_repo_extraction_without_gui_shape_change(self) -> None:
        fake = RaiateaApplicationFacade(
            self.store,
            "scope:library",
            extraction_reader=_FakeSourcePlaneReader(),
        )
        item = fake.library_page(page_size=1)["items"][0]
        detail = fake.source_detail(item["item_ref"])
        self.assertEqual(
            detail["current_extractions"][0]["state_family"],
            "source-plane-fake",
        )
        representation_id = detail["representations"][0]["representation_id"]
        page = fake.representation_page(representation_id)
        self.assertEqual(
            page["units"][0]["surface"]["value"],
            "Source Plane compatible",
        )
        self.assert_public(detail)
        self.assert_public(page)


class ApplicationFacadePdfContractTests(unittest.TestCase):
    """PDF proof uses accepted contracts only; no Poppler executable is required."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()
        (self.root / "sample.pdf").write_bytes(b"%PDF-1.4\n% bounded contract fixture\n")

        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:app-pdf", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        self.reconciliation = MixedDocumentReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:app-pdf",
        )
        self.reconciliation.reconcile_inventory()
        discovery = MixedLocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:app-pdf",
        )
        discovery.discover(rights_evidence_state="known-permitted")
        self._install_synthetic_current_pdf_extraction()
        self.facade = RaiateaApplicationFacade(self.store, "scope:app-pdf")

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def _install_synthetic_current_pdf_extraction(self) -> None:
        snapshot = self.store.load()
        source = snapshot.payload["vs1c"]["source_references"][0]
        self.assertEqual(source["media_type"], PDF_MEDIA_TYPE)
        observation = {
            "status": "success",
            "warnings": [],
            "pages": [
                {
                    "page_index": 0,
                    "width_points": 612.0,
                    "height_points": 792.0,
                }
            ],
            "blocks": [
                {
                    "block_id": "block-00000000",
                    "text": "Raiatea PDF content",
                    "page_index": 0,
                    "bbox_points_bottom_left": [72.0, 700.0, 250.0, 720.0],
                }
            ],
            "links": [],
            "figures": [],
            "raw_xml_sha256": "sha256:" + "3" * 64,
        }
        provider_observation = {
            "bundle_version": "raiatea.pdf1b.poppler-observation.0.1.0",
            "record_kind": "PopplerObservationBundle",
            "source_ref_id": source["source_ref_id"],
            "source_fingerprint": source["fingerprint"],
            "provider": {
                "provider_id": "poppler",
                "version": "24.02.0",
                "executables": {
                    "pdftohtml": {
                        "version": "24.02.0",
                        "sha256": PDFTOHTML_SHA,
                    },
                    "pdfinfo": {
                        "version": "24.02.0",
                        "sha256": PDFINFO_SHA,
                    },
                },
            },
            "route_profile": POPPLER_PROFILE,
            "observation": observation,
        }
        adapted = adapt_poppler_observation(
            observation,
            source_id=source["source_ref_id"],
            fingerprint=source["fingerprint"],
            provider_version="24.02.0",
            provider_observation_fingerprint="sha256:" + "c" * 64,
            started_at="2026-08-30T04:00:00Z",
            ended_at="2026-08-30T04:00:01Z",
        )
        bundle = build_pdf_extraction_bundle(
            source_ref_id=source["source_ref_id"],
            source_fingerprint=source["fingerprint"],
            adapted=adapted,
        )
        rights = decide_local_poppler_pdf_extraction(
            self.scopes,
            "scope:app-pdf",
            plugin_id=POPPLER_PLUGIN_ID,
            rights_evidence_state="known-permitted",
        )
        current_row = {
            "source_ref_id": source["source_ref_id"],
            "source_fingerprint": source["fingerprint"],
            "catalog_basis_revision": snapshot.revision,
            "rights_decision": rights,
            "plugin": {
                "plugin_id": POPPLER_PLUGIN_ID,
                "plugin_version": "0.1.0",
                "manifest_fingerprint": "sha256:" + "d" * 64,
                "route_profile": POPPLER_PROFILE,
            },
            "provider_observation": provider_observation,
            "record_refs": deepcopy(bundle["record_refs"]),
            "records": deepcopy(bundle["records"]),
            "provenance": {
                "plugin_id": POPPLER_PLUGIN_ID,
                "rights_decision_ref": rights["decision_id"],
            },
        }
        payload = deepcopy(snapshot.payload)
        payload["pdf1b"] = {
            "state_version": PDF1B_STATE_VERSION,
            "scope_ref": "scope:app-pdf",
            "current_extractions": [current_row],
            "attempts": [],
        }
        self.store.save(payload, expected_revision=snapshot.revision)

    def test_pdf_uses_same_source_detail_and_representation_contract(self) -> None:
        library = self.facade.library_page()
        self.assertEqual(library["total_known_items"], 1)
        item = library["items"][0]
        self.assertEqual(item["display"]["media_type"], PDF_MEDIA_TYPE)
        self.assertEqual(item["extraction"]["state"], "current")
        self.assertEqual(item["warnings"]["state"], "measured")

        detail = self.facade.source_detail(item["item_ref"])
        self.assertEqual(detail["media_type"], PDF_MEDIA_TYPE)
        self.assertIn("semantic", detail["available_panels"])
        self.assertEqual(
            detail["current_extractions"][0]["state_family"],
            "pdf1b-poppler",
        )
        representation = detail["representations"][0]
        self.assertIn("pdf-geometric", representation["coordinate_families"])
        page = self.facade.representation_page(
            representation["representation_id"],
            page_size=1,
        )
        self.assertEqual(
            page["units"][0]["coordinate"]["value"]["kind"],
            "pdf-geometric",
        )
        self.assertEqual(
            page["units"][0]["semantic_role"]["value_state"],
            "unknown",
        )
        _assert_no_internal_authority(
            self,
            {"library": library, "detail": detail, "page": page},
            forbidden_strings=[str(self.base), str(self.root), str(self.outputs)],
        )


if __name__ == "__main__":
    unittest.main()
