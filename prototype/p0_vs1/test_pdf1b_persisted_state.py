from __future__ import annotations

from copy import deepcopy
import unittest

from prototype.p0_vs1.pdf1b_product_service import (
    PdfExtractionError,
    validate_pdf1b_state,
)
from prototype.p0_vs1.test_pdf1b_product import Pdf1bProductFixture


class Pdf1bPersistedProviderTests(Pdf1bProductFixture):
    def test_reload_rejects_tampered_current_provider_reference(self) -> None:
        source_ref = self.source_ref_for_location("single.pdf")
        result = self.service.extract(source_ref, rights_evidence_state="known-permitted")
        self.assertTrue(result["published_current"])
        state = deepcopy(self.store.load().payload["pdf1b"])
        state["current_extractions"][0]["provider_observation"]["provider"]["executables"]["pdftohtml"]["sha256"] = (
            "sha256:" + "0" * 64
        )
        with self.assertRaisesRegex(PdfExtractionError, "persisted-provider-reference-invalid"):
            validate_pdf1b_state(state, "scope:pdf1b")

    def test_reload_rejects_tampered_attempt_provider_reference(self) -> None:
        source_ref = self.source_ref_for_location("malformed.pdf")
        result = self.service.extract(source_ref, rights_evidence_state="known-permitted")
        self.assertFalse(result["published_current"])
        state = deepcopy(self.store.load().payload["pdf1b"])
        state["attempts"][0]["provider_observation"]["provider"]["version"] = "future-poppler"
        with self.assertRaisesRegex(PdfExtractionError, "persisted-provider-reference-invalid"):
            validate_pdf1b_state(state, "scope:pdf1b")


if __name__ == "__main__":
    unittest.main()
