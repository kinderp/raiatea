from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.pdf1c_rights import (
    DOCLING_PLUGIN_ID,
    DoclingPdfRightsError,
    decide_local_docling_pdf_extraction,
    validate_docling_pdf_rights_decision,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry


class Pdf1cDoclingRightsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve() / "library"
        self.root.mkdir()
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:pdf1c", self.root)

    def tearDown(self) -> None:
        self.scopes.close()
        self.temp.cleanup()

    def test_known_permitted_creates_narrow_local_docling_decision(self) -> None:
        decision = decide_local_docling_pdf_extraction(
            self.scopes,
            "scope:pdf1c",
            plugin_id=DOCLING_PLUGIN_ID,
            rights_evidence_state="known-permitted",
        )
        self.assertIs(validate_docling_pdf_rights_decision(decision), decision)
        self.assertEqual(decision["policy_outcome"], "allow-local-byte-processing")
        self.assertFalse(decision["remote_processing"])
        self.assertFalse(decision["redistribution"])
        self.assertFalse(decision["source_filesystem_mutation"])
        self.assertFalse(decision["credentials_supplied"])
        self.assertFalse(decision["access_control_override"])
        self.assertFalse(decision["external_plugins"])
        self.assertFalse(decision["ocr"])

    def test_unknown_review_and_restricted_fail_closed(self) -> None:
        for state, message in (
            ("unknown", "rights-unknown"),
            ("requires-review", "review-required"),
            ("known-restricted", "known-restricted"),
        ):
            with self.subTest(state=state):
                with self.assertRaisesRegex(DoclingPdfRightsError, message):
                    decide_local_docling_pdf_extraction(
                        self.scopes,
                        "scope:pdf1c",
                        plugin_id=DOCLING_PLUGIN_ID,
                        rights_evidence_state=state,
                    )

    def test_poppler_plugin_cannot_reuse_docling_decision(self) -> None:
        with self.assertRaisesRegex(DoclingPdfRightsError, "plugin-invalid"):
            decide_local_docling_pdf_extraction(
                self.scopes,
                "scope:pdf1c",
                plugin_id="org.raiatea.pdf1.poppler-extractor",
                rights_evidence_state="known-permitted",
            )

    def test_tampered_policy_authority_is_rejected(self) -> None:
        decision = decide_local_docling_pdf_extraction(
            self.scopes,
            "scope:pdf1c",
            plugin_id=DOCLING_PLUGIN_ID,
            rights_evidence_state="known-permitted",
        )
        for key in (
            "remote_processing",
            "redistribution",
            "source_filesystem_mutation",
            "credentials_supplied",
            "access_control_override",
            "external_plugins",
            "ocr",
        ):
            with self.subTest(key=key):
                changed = dict(decision)
                changed[key] = True
                with self.assertRaises(DoclingPdfRightsError):
                    validate_docling_pdf_rights_decision(changed)


if __name__ == "__main__":
    unittest.main()
