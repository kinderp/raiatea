from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
)
from prototype.p0_vs1.pdf1b_product_service import (
    LocalPopplerPdfExtractionService,
    validate_pdf1b_state,
)
from prototype.p0_vs1.poppler_product_parser import (
    PopplerProductError,
    _controlled_asset_path,
    inspect_poppler_provider,
    verify_reference_poppler,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry
from prototype.p0_vs1.source_contract import PDF_MEDIA_TYPE


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"
NEGATIVE_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "b01_pdf_negative_fixtures.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GENERATOR = _load("pdf1b_fixture_generator", GENERATOR_PATH)
NEGATIVE = _load("pdf1b_negative_generator", NEGATIVE_PATH)

EXPECTED_PIXEL_SHA = "sha256:2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee"
EXPECTED_LINK = "https://example.invalid/raiatea-benchmark"


def _walk_forbidden(testcase: unittest.TestCase, value: object, forbidden_values: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            testcase.assertNotIn(
                normalized,
                {
                    "path",
                    "filepath",
                    "file_path",
                    "filename",
                    "root",
                    "relative_path",
                    "host_path",
                    "workspace_path",
                    "location",
                    "current_location",
                    "location_history",
                },
            )
            _walk_forbidden(testcase, child, forbidden_values)
    elif isinstance(value, list):
        for child in value:
            _walk_forbidden(testcase, child, forbidden_values)
    elif isinstance(value, str):
        for forbidden in forbidden_values:
            testcase.assertNotIn(forbidden, value)


class Pdf1bProductFixture(unittest.TestCase):
    def setUp(self) -> None:
        provider = inspect_poppler_provider()
        verify_reference_poppler(provider)

        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()

        GENERATOR.generate_pdf_single_column(self.root / "single.pdf")
        GENERATOR.generate_pdf_semantic_structure(self.root / "link.pdf")
        GENERATOR.generate_pdf_figure_caption(self.root / "figure.pdf")
        (self.root / "malformed.pdf").write_bytes(NEGATIVE.build_malformed_pdf())
        protected, _ = NEGATIVE.generate_access_controlled_pdf("qpdf")
        (self.root / "protected.pdf").write_bytes(protected)

        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:pdf1b", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        self.reconciliation = MixedDocumentReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:pdf1b",
        )
        result = self.reconciliation.reconcile_inventory()
        self.assertEqual(result["inventory_count"], 5)
        discovery = MixedLocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:pdf1b",
        )
        discovered = discovery.discover(rights_evidence_state="known-permitted")
        self.assertEqual(discovered["source_reference_count"], 5)
        self.service = LocalPopplerPdfExtractionService(
            self.store,
            self.scopes,
            self.broker,
            "scope:pdf1b",
        )

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def source_ref_for_location(self, location: str) -> str:
        payload = self.store.load().payload
        entry = next(
            row
            for row in payload["vs1b"]["entries"]
            if row["current_location"] == location
            and row["availability"] == "known-present"
            and row["superseded_by"] is None
        )
        self.assertEqual(entry["media_type"], PDF_MEDIA_TYPE)
        reference = next(
            row
            for row in payload["vs1c"]["source_references"]
            if row["stored_instance_ref"] == entry["stored_instance_id"]
        )
        self.assertEqual(reference["media_type"], PDF_MEDIA_TYPE)
        return reference["source_ref_id"]

    def current_for(self, source_ref_id: str) -> dict:
        state = self.store.load().payload["pdf1b"]
        validate_pdf1b_state(state, "scope:pdf1b")
        return next(
            row for row in state["current_extractions"]
            if row["source_ref_id"] == source_ref_id
        )


class Pdf1bHappyPathTests(Pdf1bProductFixture):
    def test_single_column_pdf_becomes_current_text_with_pdf_coordinates(self) -> None:
        source_ref = self.source_ref_for_location("single.pdf")
        result = self.service.extract(source_ref, rights_evidence_state="known-permitted")
        self.assertTrue(result["published_current"])
        self.assertGreater(result["text_block_count"], 0)
        current = self.current_for(source_ref)

        representation = next(
            current["records"][ref["ref_id"]]
            for ref in current["record_refs"]
            if ref["record_kind"] == "NormalizedRepresentationRecord"
        )
        surfaces = [
            unit["surface"]["value"]
            for unit in representation["units"]
            if unit["surface"]["value_state"] == "populated"
        ]
        self.assertTrue(any("Raiatea" in text for text in surfaces))
        for unit in representation["units"]:
            self.assertEqual(unit["semantic_role"]["value_state"], "unknown")
            if unit["coordinate"]["value_state"] == "populated":
                coordinate = unit["coordinate"]["value"]
                self.assertEqual(coordinate["kind"], "pdf-geometric")
                self.assertIsInstance(coordinate["page_index"], int)
                self.assertEqual(len(coordinate["bbox_points_bottom_left"]), 4)

        _walk_forbidden(
            self,
            current["provider_observation"],
            [str(self.root), str(self.base), "single.pdf"],
        )

    def test_explicit_pdf_link_is_retained_as_provider_evidence(self) -> None:
        source_ref = self.source_ref_for_location("link.pdf")
        result = self.service.extract(source_ref, rights_evidence_state="known-permitted")
        self.assertTrue(result["published_current"])
        current = self.current_for(source_ref)
        links = current["provider_observation"]["observation"]["links"]
        self.assertTrue(any(link["target"] == EXPECTED_LINK for link in links))
        matched = next(link for link in links if link["target"] == EXPECTED_LINK)
        self.assertEqual(matched["provider_source"], "pdftohtml-explicit-anchor")
        self.assertIn("Raiatea benchmark link", matched["from_text"])

    def test_explicit_pdf_image_retains_geometry_and_fingerprints_without_asset_bytes(self) -> None:
        source_ref = self.source_ref_for_location("figure.pdf")
        result = self.service.extract(source_ref, rights_evidence_state="known-permitted")
        self.assertTrue(result["published_current"])
        current = self.current_for(source_ref)
        figures = current["provider_observation"]["observation"]["figures"]
        self.assertEqual(len(figures), 1)
        figure = figures[0]
        self.assertEqual(figure["provider_source"], "pdftohtml-explicit-image-element")
        self.assertEqual(figure["page_index"], 0)
        self.assertEqual(figure["decoded_pixel_sha256"], EXPECTED_PIXEL_SHA)
        self.assertEqual((figure["pixel_width"], figure["pixel_height"]), (4, 3))
        self.assertGreater(figure["asset_bytes"], 0)
        self.assertNotIn("asset", figure)
        self.assertNotIn("bytes_payload", figure)
        self.assertEqual(len(figure["bbox_points_bottom_left"]), 4)


class Pdf1bNegativeProductTests(Pdf1bProductFixture):
    def test_malformed_pdf_is_attempt_evidence_not_current_content(self) -> None:
        source_ref = self.source_ref_for_location("malformed.pdf")
        result = self.service.extract(source_ref, rights_evidence_state="known-permitted")
        self.assertFalse(result["published_current"])
        self.assertIn(result["processing_execution"], {"failed", "rejected", "unknown"})
        state = self.store.load().payload["pdf1b"]
        self.assertFalse(any(row["source_ref_id"] == source_ref for row in state["current_extractions"]))
        attempt = next(row for row in state["attempts"] if row["source_ref_id"] == source_ref)
        self.assertNotEqual(attempt["run"]["outcome"]["execution"], "completed")
        self.assertEqual(attempt["provider_observation"]["observation"]["blocks"], [])

    def test_password_protected_pdf_fails_closed_without_inferred_restriction_or_current_content(self) -> None:
        source_ref = self.source_ref_for_location("protected.pdf")
        result = self.service.extract(source_ref, rights_evidence_state="known-permitted")
        self.assertFalse(result["published_current"])
        # This exact pdftohtml route is measured to fail without necessarily
        # exposing an explicit password/encryption signal. Core must preserve
        # that limited evidence instead of upgrading a generic Provider failure
        # to a restriction claim merely because the test fixture is known here.
        self.assertEqual(result["processing_execution"], "failed")
        state = self.store.load().payload["pdf1b"]
        attempt = next(row for row in state["attempts"] if row["source_ref_id"] == source_ref)
        self.assertEqual(attempt["provider_observation"]["observation"]["status"], "failed")
        self.assertFalse(attempt["rights_decision"]["credentials_supplied"])
        self.assertFalse(attempt["rights_decision"]["access_control_override"])
        self.assertFalse(any(row["source_ref_id"] == source_ref for row in state["current_extractions"]))

    def test_unsafe_generated_image_reference_fails_workspace_containment(self) -> None:
        work = self.base / "provider-work"
        work.mkdir()
        outside = self.base / "outside.png"
        outside.write_bytes(b"not-an-image")
        with self.assertRaises(PopplerProductError):
            _controlled_asset_path(work, str(outside))
        with self.assertRaises(PopplerProductError):
            _controlled_asset_path(work, "../outside.png")


if __name__ == "__main__":
    unittest.main()
