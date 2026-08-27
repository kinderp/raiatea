from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
)
from prototype.p0_vs1.pdf1b_product_service import (
    LocalPopplerPdfExtractionService,
    PdfExtractionError,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry


class Pdf1bRightsOrderTests(unittest.TestCase):
    def test_denied_rights_fail_before_local_provider_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            root = base / "library"
            outputs = base / "outputs"
            root.mkdir()
            outputs.mkdir()
            (root / "paper.pdf").write_bytes(b"%PDF-1.4\nPDF1b rights-order fixture\n%%EOF\n")
            store = CatalogStateStore(base / "catalog.json")
            scopes = Vs1ObservationScopeRegistry()
            scopes.register_scope("scope:pdf-rights", root)
            broker = AssetBroker(scopes, outputs)
            try:
                reconciliation = MixedDocumentReconciliationEngine(
                    store,
                    scopes,
                    broker,
                    "scope:pdf-rights",
                )
                reconciliation.reconcile_inventory()
                discovery = MixedLocalSourceDiscoveryService(
                    store,
                    scopes,
                    "scope:pdf-rights",
                )
                discovered = discovery.discover(rights_evidence_state="known-permitted")
                source_ref = discovered["source_refs"][0]
                service = LocalPopplerPdfExtractionService(
                    store,
                    scopes,
                    broker,
                    "scope:pdf-rights",
                )

                with patch(
                    "prototype.p0_vs1.pdf1b_service.inspect_poppler_provider",
                    side_effect=AssertionError("Provider probe must not happen for denied rights"),
                ):
                    with self.assertRaisesRegex(PdfExtractionError, "rights-unknown"):
                        service.extract(source_ref, rights_evidence_state="unknown")
            finally:
                broker.close()
                scopes.close()


if __name__ == "__main__":
    unittest.main()
