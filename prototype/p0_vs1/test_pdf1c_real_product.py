from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
)
from prototype.p0_vs1.pdf1c_service import (
    LocalDoclingPdfExtractionService,
    validate_pdf1c_state,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"
NEGATIVE_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "b01_pdf_negative_fixtures.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GENERATOR = _load("pdf1c_real_generator", GENERATOR_PATH)
NEGATIVE = _load("pdf1c_real_negative", NEGATIVE_PATH)


class Pdf1cRealProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            "PDF1C_DOCLING_WHEEL",
            "PDF1C_DOCLING_ARTIFACTS",
            "PDF1C_DOCLING_CACHE_PARENT",
        )
        missing = [key for key in required if not os.environ.get(key)]
        if missing:
            raise RuntimeError(f"pdf1c-real-provider-environment-missing:{missing[0]}")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()

        GENERATOR.generate_pdf_single_column(self.root / "001-single.pdf")
        GENERATOR.generate_pdf_two_column(self.root / "002-two-column.pdf")
        GENERATOR.generate_pdf_semantic_structure(self.root / "003-semantic.pdf")
        GENERATOR.generate_pdf_figure_caption(self.root / "004-figure.pdf")
        (self.root / "900-malformed.pdf").write_bytes(NEGATIVE.build_malformed_pdf())
        protected, _generator_evidence = NEGATIVE.generate_access_controlled_pdf(
            os.environ.get("PDF1C_QPDF", "qpdf")
        )
        (self.root / "901-protected.pdf").write_bytes(protected)

        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:pdf1c-real", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        self.reconciliation = MixedDocumentReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:pdf1c-real",
        )
        result = self.reconciliation.reconcile_inventory()
        self.assertEqual(result["inventory_count"], 6)
        discovery = MixedLocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:pdf1c-real",
        )
        discovered = discovery.discover(rights_evidence_state="known-permitted")
        self.assertEqual(len(discovered["source_refs"]), 6)

        self.service = LocalDoclingPdfExtractionService(
            self.store,
            self.scopes,
            self.broker,
            "scope:pdf1c-real",
            wheel_path=Path(os.environ["PDF1C_DOCLING_WHEEL"]).resolve(),
            artifacts_path=Path(os.environ["PDF1C_DOCLING_ARTIFACTS"]).resolve(),
            cache_parent=Path(os.environ["PDF1C_DOCLING_CACHE_PARENT"]).resolve(),
        )

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def source_ref(self, location: str) -> str:
        payload = self.store.load().payload
        entry = next(
            row
            for row in payload["vs1b"]["entries"]
            if row["current_location"] == location
            and row["availability"] == "known-present"
            and row["superseded_by"] is None
        )
        return next(
            row["source_ref_id"]
            for row in payload["vs1c"]["source_references"]
            if row["stored_instance_ref"] == entry["stored_instance_id"]
        )

    def extract(self, location: str) -> dict:
        return self.service.extract(
            self.source_ref(location),
            rights_evidence_state="known-permitted",
        )

    def current(self, location: str) -> dict:
        source_ref_id = self.source_ref(location)
        state = self.store.load().payload["pdf1c"]
        return next(
            row
            for row in state["current_extractions"]
            if row["source_ref_id"] == source_ref_id
        )

    def representation(self, location: str) -> dict:
        current = self.current(location)
        return next(
            current["records"][ref["ref_id"]]
            for ref in current["record_refs"]
            if ref["record_kind"] == "NormalizedRepresentationRecord"
        )

    def publication_diagnostic(self, location: str, result: dict) -> dict:
        source_ref_id = self.source_ref(location)
        state = self.store.load().payload.get("pdf1c", {})
        attempts = state.get("attempts", []) if isinstance(state, dict) else []
        matching = [
            row for row in attempts
            if isinstance(row, dict) and row.get("source_ref_id") == source_ref_id
        ]
        diagnostic = {"service_result": result}
        if matching:
            observation = matching[-1].get("provider_observation", {}).get("observation", {})
            diagnostic.update(
                {
                    "observation_status": observation.get("status"),
                    "provider_conversion_status": observation.get("provider_conversion_status"),
                    "warning_codes": [
                        row.get("code")
                        for row in observation.get("warnings", [])
                        if isinstance(row, dict)
                    ],
                    "run_execution": matching[-1].get("run", {}).get("outcome", {}).get("execution"),
                }
            )
        return diagnostic

    def test_real_docling_product_path_preserves_semantics_and_known_limits(self) -> None:
        for location in (
            "001-single.pdf",
            "002-two-column.pdf",
            "003-semantic.pdf",
            "004-figure.pdf",
        ):
            with self.subTest(location=location):
                result = self.extract(location)
                self.assertTrue(
                    result["published_current"],
                    self.publication_diagnostic(location, result),
                )
                self.assertEqual(result["processing_execution"], "completed")

        state = self.store.load().payload["pdf1c"]
        validate_pdf1c_state(state, "scope:pdf1c-real")
        self.assertEqual(len(state["current_extractions"]), 4)

        simple = self.representation("001-single.pdf")
        simple_surfaces = [unit["surface"]["value"] for unit in simple["units"]]
        self.assertIn("Raiatea B01 PDF 001", simple_surfaces)
        title = next(unit for unit in simple["units"] if unit["surface"]["value"] == "Raiatea B01 PDF 001")
        self.assertEqual(title["semantic_role"]["value"]["type"], "heading")
        self.assertEqual(title["coordinate"]["value"]["kind"], "pdf-geometric")

        two_column_observation = self.current("002-two-column.pdf")["provider_observation"]["observation"]
        aggregated = [row["text"] for row in two_column_observation["blocks"]]
        self.assertTrue(
            any(
                all(token in text for token in ("Left one.", "Left two.", "Right one.", "Right two."))
                for text in aggregated
            ),
            "PDF1c must preserve measured Docling coarse two-column segmentation rather than split with Poppler/gold",
        )

        semantic_observation = self.current("003-semantic.pdf")["provider_observation"]["observation"]
        semantic_by_text = {row["text"]: row for row in semantic_observation["blocks"]}
        self.assertEqual(semantic_by_text["Raiatea B01 PDF 003"]["semantic_type"], "heading")
        self.assertEqual(semantic_by_text["Semantic Structure"]["semantic_type"], "heading")
        self.assertNotEqual(
            semantic_by_text['print("raiatea-structure")']["semantic_type"],
            "code",
            "Known Docling native-profile semantic mismatch must remain visible rather than corrected from fixture typography",
        )
        self.assertEqual(
            semantic_by_text["Raiatea benchmark link"]["semantic_type"],
            "heading",
            "Known Docling link-label misclassification must remain visible in Provider evidence",
        )

        figure_observation = self.current("004-figure.pdf")["provider_observation"]["observation"]
        self.assertEqual(figure_observation["picture_collection_state"], "present")
        self.assertEqual(len(figure_observation["pictures"]), 1)
        self.assertEqual(len(figure_observation["picture_caption_relations"]), 1)
        relation = figure_observation["picture_caption_relations"][0]
        self.assertEqual(relation["relation_source"], "docling-picture.captions-explicit-ref")
        caption = next(
            row
            for row in figure_observation["caption_blocks"]
            if row["provider_ref"] == relation["caption_ref"]
        )
        self.assertEqual(caption["text"], "Figure 1. Deterministic Raiatea color grid.")

    def test_real_docling_negative_inputs_become_attempts_not_current_content(self) -> None:
        malformed = self.extract("900-malformed.pdf")
        protected = self.extract("901-protected.pdf")
        self.assertFalse(malformed["published_current"])
        self.assertFalse(protected["published_current"])
        self.assertNotEqual(malformed["processing_execution"], "completed")
        self.assertNotEqual(protected["processing_execution"], "completed")

        state = self.store.load().payload["pdf1c"]
        validate_pdf1c_state(state, "scope:pdf1c-real")
        negative_refs = {
            self.source_ref("900-malformed.pdf"),
            self.source_ref("901-protected.pdf"),
        }
        current_refs = {row["source_ref_id"] for row in state["current_extractions"]}
        self.assertTrue(negative_refs.isdisjoint(current_refs))
        attempt_refs = {row["source_ref_id"] for row in state["attempts"]}
        self.assertTrue(negative_refs.issubset(attempt_refs))
        protected_attempt = next(
            row for row in state["attempts"]
            if row["source_ref_id"] == self.source_ref("901-protected.pdf")
        )
        self.assertIn(
            protected_attempt["provider_observation"]["observation"]["status"],
            {"restricted", "failed", "unknown"},
        )
        serialized = json.dumps(state, sort_keys=True)
        self.assertNotIn("raiatea-fixture-user", serialized)
        self.assertNotIn("raiatea-fixture-owner", serialized)


if __name__ == "__main__":
    unittest.main()
