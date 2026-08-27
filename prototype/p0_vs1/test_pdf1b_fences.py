from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.local_process_client import LocalPluginProcessClient
from prototype.p0_vs1.pdf1b_service import PdfExtractionError
from prototype.p0_vs1.test_pdf1b_product import Pdf1bProductFixture


class Pdf1bPublicationFenceTests(Pdf1bProductFixture):
    def test_source_change_after_provider_output_rejects_publication(self) -> None:
        source_ref = self.source_ref_for_location("single.pdf")
        source_path = self.root / "single.pdf"
        original = source_path.read_bytes()
        real_invoke = LocalPluginProcessClient.invoke

        def invoke_then_change(client: LocalPluginProcessClient, request: dict) -> dict:
            result = real_invoke(client, request)
            source_path.write_bytes(original + b"\nchanged-after-provider-output")
            return result

        with patch.object(LocalPluginProcessClient, "invoke", new=invoke_then_change):
            with self.assertRaisesRegex(PdfExtractionError, "source-changed-during-plugin-run"):
                self.service.extract(source_ref, rights_evidence_state="known-permitted")

        payload = self.store.load().payload
        self.assertNotIn("pdf1b", payload)

    def test_catalog_change_during_provider_run_rejects_stale_pdf_state(self) -> None:
        source_ref = self.source_ref_for_location("single.pdf")
        real_invoke = LocalPluginProcessClient.invoke
        other_store = CatalogStateStore(self.store.path)

        def invoke_then_change(client: LocalPluginProcessClient, request: dict) -> dict:
            result = real_invoke(client, request)
            current = other_store.load()
            payload = deepcopy(current.payload)
            payload["concurrent_pdf1b_marker"] = {"changed": True}
            other_store.save(payload, expected_revision=current.revision)
            return result

        with patch.object(LocalPluginProcessClient, "invoke", new=invoke_then_change):
            with self.assertRaisesRegex(PdfExtractionError, "catalog-changed-during-plugin-run"):
                self.service.extract(source_ref, rights_evidence_state="known-permitted")

        payload = self.store.load().payload
        self.assertIn("concurrent_pdf1b_marker", payload)
        self.assertNotIn("pdf1b", payload)


if __name__ == "__main__":
    unittest.main()
