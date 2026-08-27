from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry
from prototype.p0_vs1.source_contract import EPUB_MEDIA_TYPE, PDF_MEDIA_TYPE


class Pdf1aTransitionFixture(unittest.TestCase):
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
        return MixedLocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:library",
        ).discover(rights_evidence_state="known-permitted")


class PdfDeleteAndMediaTransitionTests(Pdf1aTransitionFixture):
    def test_pdf_delete_keeps_stored_and_logical_history_as_missing_location_evidence(self) -> None:
        path = self.root / "paper.pdf"
        path.write_bytes(b"%PDF-1.4\nPDF1a delete fixture\n%%EOF\n")
        self.engine.reconcile_inventory()
        before = next(
            row
            for row in self.store.load().payload["vs1b"]["entries"]
            if row["availability"] == "known-present"
        )
        identity = (
            before["entry_id"],
            before["stored_instance_id"],
            before["logical_candidate_id"],
            before["fingerprint"],
        )

        path.unlink()
        self.engine.reconcile_inventory()
        after = next(
            row
            for row in self.store.load().payload["vs1b"]["entries"]
            if row["entry_id"] == before["entry_id"]
        )
        self.assertEqual(
            (
                after["entry_id"],
                after["stored_instance_id"],
                after["logical_candidate_id"],
                after["fingerprint"],
            ),
            identity,
        )
        self.assertEqual(after["current_location"], "paper.pdf")
        self.assertEqual(after["availability"], "confirmed-missing-at-location")
        self.assertEqual(
            after["reconciliation_status"],
            "missing-after-bounded-inventory",
        )

    def test_epub_to_pdf_media_transition_keeps_instance_only_after_inventory_but_rotates_source_ref(self) -> None:
        old_path = self.root / "document.epub"
        payload = b"same-physical-bytes-across-extension-transition"
        old_path.write_bytes(payload)
        self.engine.reconcile_inventory()
        first_discovery = self.discover()
        self.assertEqual(first_discovery["source_reference_count"], 1)
        before_payload = self.store.load().payload
        before_entry = next(
            row
            for row in before_payload["vs1b"]["entries"]
            if row["availability"] == "known-present"
        )
        before_ref = before_payload["vs1c"]["source_references"][0]
        self.assertEqual(before_entry["media_type"], EPUB_MEDIA_TYPE)
        self.assertEqual(before_ref["media_type"], EPUB_MEDIA_TYPE)

        new_path = self.root / "document.pdf"
        old_path.rename(new_path)

        # Model accepted location-transition evidence before the bounded inventory
        # verifies the new Location and media admission class. The transition may
        # preserve the physical Stored Instance candidate, but it is explicitly
        # non-fresh until inventory succeeds.
        snapshot = self.store.load()
        changed = deepcopy(snapshot.payload)
        entry = next(
            row
            for row in changed["vs1b"]["entries"]
            if row["entry_id"] == before_entry["entry_id"]
        )
        entry["location_history"].append("document.epub")
        entry["current_location"] = "document.pdf"
        entry["availability"] = "unavailable-or-unknown"
        entry["reconciliation_status"] = "transition-unverified"
        changed["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "test-media-transition",
        }
        self.store.save(changed, expected_revision=snapshot.revision)

        self.engine.reconcile_inventory()
        reconciled = self.store.load().payload
        after_entry = next(
            row
            for row in reconciled["vs1b"]["entries"]
            if row["availability"] == "known-present"
            and row["superseded_by"] is None
        )
        self.assertEqual(after_entry["entry_id"], before_entry["entry_id"])
        self.assertEqual(
            after_entry["stored_instance_id"],
            before_entry["stored_instance_id"],
        )
        self.assertEqual(after_entry["fingerprint"], before_entry["fingerprint"])
        self.assertEqual(after_entry["media_type"], PDF_MEDIA_TYPE)
        self.assertIn("document.epub", after_entry["location_history"])

        second_discovery = self.discover()
        self.assertEqual(second_discovery["source_reference_count"], 1)
        after_ref = self.store.load().payload["vs1c"]["source_references"][0]
        self.assertEqual(after_ref["media_type"], PDF_MEDIA_TYPE)
        self.assertNotEqual(after_ref["source_ref_id"], before_ref["source_ref_id"])
        self.assertEqual(
            after_ref["stored_instance_ref"],
            before_ref["stored_instance_ref"],
        )
        self.assertNotIn(
            before_ref["source_ref_id"],
            second_discovery["source_refs"],
        )
        self.assertNotIn("vs1d", self.store.load().payload)


if __name__ == "__main__":
    unittest.main()
