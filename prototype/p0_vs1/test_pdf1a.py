from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.extraction_service import EpubExtractionError, LocalEpubExtractionService
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
    build_mixed_discovery_snapshot,
    media_type_for_name,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry
from prototype.p0_vs1.source_contract import EPUB_MEDIA_TYPE, PDF_MEDIA_TYPE


class Pdf1aFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()
        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:library", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        self.engine = MixedDocumentReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def discover(self) -> dict:
        service = MixedLocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:library",
        )
        return service.discover(rights_evidence_state="known-permitted")


class MediaAdmissionTests(unittest.TestCase):
    def test_supported_extensions_are_case_insensitive_and_bounded(self) -> None:
        self.assertEqual(media_type_for_name("a.epub"), EPUB_MEDIA_TYPE)
        self.assertEqual(media_type_for_name("a.EPUB"), EPUB_MEDIA_TYPE)
        self.assertEqual(media_type_for_name("a.pdf"), PDF_MEDIA_TYPE)
        self.assertEqual(media_type_for_name("a.PdF"), PDF_MEDIA_TYPE)
        self.assertIsNone(media_type_for_name("a.txt"))
        self.assertIsNone(media_type_for_name("pdf"))


class MixedInventoryTests(Pdf1aFixture):
    def test_mixed_scope_inventory_and_source_refs_are_path_free(self) -> None:
        (self.root / "book.epub").write_bytes(b"epub-fixture-bytes")
        (self.root / "paper.PDF").write_bytes(b"%PDF-1.4\nfixture\n")
        (self.root / "ignore.txt").write_text("ignored", encoding="utf-8")

        result = self.engine.reconcile_inventory()
        self.assertEqual(result["inventory_count"], 2)
        current = self.store.load().payload["vs1b"]
        active = [
            row for row in current["entries"]
            if row["superseded_by"] is None and row["availability"] == "known-present"
        ]
        self.assertEqual(
            {row["media_type"] for row in active},
            {EPUB_MEDIA_TYPE, PDF_MEDIA_TYPE},
        )
        self.assertEqual(
            [row["current_location"] for row in active],
            sorted(row["current_location"] for row in active),
        )

        discovered = self.discover()
        self.assertEqual(discovered["source_reference_count"], 2)
        refs = self.store.load().payload["vs1c"]["source_references"]
        self.assertEqual(
            {row["media_type"] for row in refs},
            {EPUB_MEDIA_TYPE, PDF_MEDIA_TYPE},
        )
        serialized = json.dumps(refs, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("book.epub", serialized)
        self.assertNotIn("paper.PDF", serialized)
        for row in refs:
            self.assertFalse(row["location_exposed"])

    def test_byte_identical_pdf_copies_remain_distinct_stored_instances(self) -> None:
        payload = b"%PDF-1.4\nsame-pdf\n"
        (self.root / "one.pdf").write_bytes(payload)
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "copy.pdf").write_bytes(payload)
        self.engine.reconcile_inventory()
        state = self.store.load().payload["vs1b"]
        pdfs = [
            row for row in state["entries"]
            if row["media_type"] == PDF_MEDIA_TYPE
            and row["superseded_by"] is None
            and row["availability"] == "known-present"
        ]
        self.assertEqual(len(pdfs), 2)
        self.assertEqual(len({row["fingerprint"] for row in pdfs}), 1)
        self.assertEqual(len({row["stored_instance_id"] for row in pdfs}), 2)
        self.assertEqual(len({row["logical_candidate_id"] for row in pdfs}), 2)

    def test_pdf_rename_preserves_candidate_identity_after_inventory(self) -> None:
        source = self.root / "old.pdf"
        source.write_bytes(b"%PDF-1.4\nrename\n")
        self.engine.reconcile_inventory()
        before = self.store.load().payload["vs1b"]
        current = next(
            row for row in before["entries"]
            if row["availability"] == "known-present"
        )
        ids = (
            current["entry_id"],
            current["stored_instance_id"],
            current["logical_candidate_id"],
        )

        target = self.root / "renamed.pdf"
        source.rename(target)
        # The bounded inventory path is sufficient for correctness even when a
        # live Alfred transition is unavailable. In that case identity cannot be
        # inferred from equal bytes alone, so inventory creates a new candidate.
        # Simulate the accepted Alfred transition evidence first to prove the
        # stronger identity-preserving path.
        current = deepcopy(self.store.load().payload)
        entry = next(row for row in current["vs1b"]["entries"] if row["entry_id"] == ids[0])
        entry["location_history"].append("old.pdf")
        entry["current_location"] = "renamed.pdf"
        entry["availability"] = "unavailable-or-unknown"
        entry["reconciliation_status"] = "transition-unverified"
        current["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "test-rename-transition",
        }
        snapshot = self.store.load()
        self.store.save(current, expected_revision=snapshot.revision)

        self.engine.reconcile_inventory()
        after = self.store.load().payload["vs1b"]
        active = next(
            row for row in after["entries"]
            if row["availability"] == "known-present" and row["superseded_by"] is None
        )
        self.assertEqual(
            (active["entry_id"], active["stored_instance_id"], active["logical_candidate_id"]),
            ids,
        )
        self.assertEqual(active["current_location"], "renamed.pdf")
        self.assertIn("old.pdf", active["location_history"])

    def test_same_location_changed_pdf_bytes_supersedes_candidate(self) -> None:
        path = self.root / "paper.pdf"
        path.write_bytes(b"%PDF-1.4\nversion-one\n")
        self.engine.reconcile_inventory()
        old = next(
            row for row in self.store.load().payload["vs1b"]["entries"]
            if row["availability"] == "known-present"
        )
        old_id = old["entry_id"]
        path.write_bytes(b"%PDF-1.4\nversion-two-longer\n")
        self.engine.reconcile_inventory()
        rows = self.store.load().payload["vs1b"]["entries"]
        old_after = next(row for row in rows if row["entry_id"] == old_id)
        active = next(
            row for row in rows
            if row["availability"] == "known-present" and row["superseded_by"] is None
        )
        self.assertEqual(old_after["superseded_by"], active["entry_id"])
        self.assertNotEqual(old_after["fingerprint"], active["fingerprint"])


class MixedSourceDownstreamFenceTests(Pdf1aFixture):
    def test_pdf_source_reference_cannot_enter_epub_extractor(self) -> None:
        (self.root / "paper.pdf").write_bytes(b"%PDF-1.4\nnot-an-epub\n")
        self.engine.reconcile_inventory()
        self.discover()
        pdf_ref = next(
            row for row in self.store.load().payload["vs1c"]["source_references"]
            if row["media_type"] == PDF_MEDIA_TYPE
        )
        extractor = LocalEpubExtractionService(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )
        with self.assertRaises(EpubExtractionError):
            extractor.extract(
                pdf_ref["source_ref_id"],
                rights_evidence_state="known-permitted",
            )
        self.assertNotIn("vs1d", self.store.load().payload)

    def test_mixed_snapshot_contains_pdf_without_claiming_extraction(self) -> None:
        (self.root / "paper.pdf").write_bytes(b"%PDF-1.4\nsource-only\n")
        self.engine.reconcile_inventory()
        snapshot = build_mixed_discovery_snapshot(
            self.store.load(),
            "scope:library",
        )
        self.assertEqual(len(snapshot["items"]), 1)
        self.assertEqual(snapshot["items"][0]["media_type"], PDF_MEDIA_TYPE)
        self.discover()
        payload = self.store.load().payload
        self.assertIn("vs1c", payload)
        self.assertNotIn("vs1d", payload)
        self.assertNotIn("vs1e", payload)


if __name__ == "__main__":
    unittest.main()
