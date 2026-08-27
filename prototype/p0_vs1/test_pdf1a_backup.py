from __future__ import annotations

from pathlib import Path
import unittest

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
)
from prototype.p0_vs1.pdf1a_backup import MixedCatalogBackupService
from prototype.p0_vs1.search_service import SearchViewService
from prototype.p0_vs1.source_contract import PDF_MEDIA_TYPE
from prototype.p0_vs1.test_vs1f import Vs1fFixture


class Pdf1aBackupRestoreTests(Vs1fFixture):
    def setUp(self) -> None:
        super().setUp()
        self.pdf_path = self.root / "paper.pdf"
        self.pdf_path.write_bytes(b"%PDF-1.4\nPDF1a source-only fixture\n%%EOF\n")
        self.mixed_reconciliation = MixedDocumentReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )
        self.mixed_reconciliation.reconcile_inventory()
        self.mixed_discovery = MixedLocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:library",
        )
        self.mixed_discovery.discover(rights_evidence_state="known-permitted")

        # The new Source changes search-relevant upstream truth even though it has
        # no extraction yet. Rebuild the derived index and Smart members without
        # inventing PDF content.
        self.mixed_search = SearchViewService(self.store, "scope:library")
        self.mixed_search.rebuild_index()
        self.mixed_search.reevaluate_smart_collection("smart:headings")
        self.mixed_backup = MixedCatalogBackupService(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )

    def _pdf_ref(self, payload: dict) -> dict:
        return next(
            row
            for row in payload["vs1c"]["source_references"]
            if row["media_type"] == PDF_MEDIA_TYPE
        )

    def test_unextracted_pdf_source_survives_backup_restore_without_fake_content(self) -> None:
        before = self.store.load().payload
        pdf_ref = self._pdf_ref(before)
        self.assertTrue(pdf_ref["source_ref_id"].startswith("source-ref:"))
        self.assertFalse(pdf_ref["location_exposed"])
        self.assertFalse(
            any(
                row["source_ref_id"] == pdf_ref["source_ref_id"]
                for row in before["vs1d"]["extractions"]
            )
        )
        intro_before = self.mixed_search.search(self.intro_plan)
        self.assertEqual(intro_before["freshness"], "fresh")
        self.assertNotIn(pdf_ref["source_ref_id"], intro_before["source_ids"])

        raw = self.mixed_backup.export_bytes()
        target = CatalogStateStore(self.base / "pdf1a-restored.json")
        restored = self.mixed_backup.restore_into_empty_store(raw, target)
        self.assertEqual(restored["status"], "completed")
        self.assertEqual(restored["restored_source_count"], 3)

        after = target.load().payload
        restored_pdf = self._pdf_ref(after)
        self.assertEqual(restored_pdf, pdf_ref)
        active_pdf = [
            row
            for row in after["vs1b"]["entries"]
            if row["media_type"] == PDF_MEDIA_TYPE
            and row["superseded_by"] is None
            and row["availability"] == "known-present"
        ]
        self.assertEqual(len(active_pdf), 1)
        self.assertFalse(
            any(
                row["source_ref_id"] == pdf_ref["source_ref_id"]
                for row in after["vs1d"]["extractions"]
            )
        )
        restored_search = SearchViewService(target, "scope:library")
        intro_after = restored_search.search(self.intro_plan)
        self.assertEqual(intro_after["freshness"], "fresh")
        self.assertEqual(intro_after["source_ids"], intro_before["source_ids"])
        self.assertNotIn(pdf_ref["source_ref_id"], intro_after["source_ids"])

    def test_missing_pdf_blocks_mixed_restore_and_leaves_target_empty(self) -> None:
        raw = self.mixed_backup.export_bytes()
        self.pdf_path.unlink()
        target = CatalogStateStore(self.base / "pdf1a-missing-restored.json")
        with self.assertRaises(Exception):
            self.mixed_backup.restore_into_empty_store(raw, target)
        self.assertIsNone(target.load())


if __name__ == "__main__":
    unittest.main()
