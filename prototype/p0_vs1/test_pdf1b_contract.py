from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.pdf1b_e05_contract import (
    build_pdf_extraction_bundle,
    validate_attempt_records,
    validate_pdf_extraction_bundle,
)
from prototype.p0_vs1.pdf1b_rights import (
    POPPLER_PLUGIN_ID,
    PdfRightsError,
    decide_local_poppler_pdf_extraction,
)
from prototype.p0_vs1.poppler_e05_adapter import adapt_poppler_observation
from prototype.p0_vs1.poppler_observation_contract import (
    PopplerObservationError,
    validate_poppler_observation_bundle,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry


PDFTOHTML_SHA = "sha256:70bd5fbb655a14d0b02cb32cb53a601d3b0842a63553a24d1a6a612cf9f0624e"
PDFINFO_SHA = "sha256:3293dda06d80e1e38dab859aa47368c2876aedc41cbc2e24e8fb9a4e66392078"


def provider_bundle(status: str = "success") -> dict:
    observation = {
        "status": status,
        "warnings": [],
        "pages": [],
        "blocks": [],
        "links": [],
        "figures": [],
        "raw_xml_sha256": None,
    }
    if status == "success":
        observation.update(
            {
                "pages": [{"page_index": 0, "width_points": 612.0, "height_points": 792.0}],
                "blocks": [
                    {
                        "block_id": "block-00000000",
                        "text": "Raiatea PDF content",
                        "page_index": 0,
                        "bbox_points_bottom_left": [72.0, 700.0, 250.0, 720.0],
                    }
                ],
                "links": [
                    {
                        "link_id": "link-00000000",
                        "kind": "uri",
                        "target": "https://example.invalid/raiatea",
                        "from_text": "Raiatea PDF content",
                        "page_index": 0,
                        "provider_source": "pdftohtml-explicit-anchor",
                    }
                ],
                "figures": [
                    {
                        "provider_ref": "figure-00000000",
                        "provider_source": "pdftohtml-explicit-image-element",
                        "page_index": 0,
                        "bbox_points_bottom_left": [72.0, 500.0, 252.0, 620.0],
                        "asset_sha256": "sha256:" + "1" * 64,
                        "asset_bytes": 113,
                        "pixel_width": 4,
                        "pixel_height": 3,
                        "decoded_pixel_sha256": "sha256:" + "2" * 64,
                        "decode_warning": None,
                    }
                ],
                "raw_xml_sha256": "sha256:" + "3" * 64,
            }
        )
    else:
        observation["warnings"] = [
            {
                "code": "pdf-access-restriction-signaled" if status == "restricted" else "pdftohtml-failed",
                "details": "bounded provider outcome",
            }
        ]
    return {
        "bundle_version": "raiatea.pdf1b.poppler-observation.0.1.0",
        "record_kind": "PopplerObservationBundle",
        "source_ref_id": "source-ref:" + "a" * 64,
        "source_fingerprint": "sha256:" + "b" * 64,
        "provider": {
            "provider_id": "poppler",
            "version": "24.02.0",
            "executables": {
                "pdftohtml": {"version": "24.02.0", "sha256": PDFTOHTML_SHA},
                "pdfinfo": {"version": "24.02.0", "sha256": PDFINFO_SHA},
            },
        },
        "route_profile": "pdf-poppler-pdftohtml-xml",
        "observation": observation,
    }


class Pdf1bObservationTests(unittest.TestCase):
    def test_success_observation_is_closed_path_free_and_keeps_link_figure_evidence(self) -> None:
        value = provider_bundle()
        validate_poppler_observation_bundle(value)
        self.assertEqual(value["observation"]["links"][0]["target"], "https://example.invalid/raiatea")
        self.assertEqual(value["observation"]["figures"][0]["decoded_pixel_sha256"], "sha256:" + "2" * 64)

    def test_host_path_authority_is_rejected(self) -> None:
        value = provider_bundle()
        value["provider"]["host_path"] = "/tmp/pdftohtml"
        with self.assertRaises(PopplerObservationError):
            validate_poppler_observation_bundle(value)

    def test_failed_or_restricted_observation_cannot_carry_current_content(self) -> None:
        value = provider_bundle("restricted")
        value["observation"]["blocks"] = [
            {
                "block_id": "block-00000000",
                "text": "must not survive restriction",
                "page_index": 0,
                "bbox_points_bottom_left": [1.0, 1.0, 2.0, 2.0],
            }
        ]
        with self.assertRaisesRegex(PopplerObservationError, "blocks-forbidden"):
            validate_poppler_observation_bundle(value)


class Pdf1bRightsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:pdf", self.root)

    def tearDown(self) -> None:
        self.scopes.close()
        self.temp.cleanup()

    def test_only_known_permitted_crosses_pdf_byte_boundary(self) -> None:
        allowed = decide_local_poppler_pdf_extraction(
            self.scopes,
            "scope:pdf",
            plugin_id=POPPLER_PLUGIN_ID,
            rights_evidence_state="known-permitted",
        )
        self.assertFalse(allowed["remote_processing"])
        self.assertFalse(allowed["credentials_supplied"])
        self.assertFalse(allowed["access_control_override"])
        for state in ("unknown", "requires-review", "known-restricted"):
            with self.subTest(state=state):
                with self.assertRaises(PdfRightsError):
                    decide_local_poppler_pdf_extraction(
                        self.scopes,
                        "scope:pdf",
                        plugin_id=POPPLER_PLUGIN_ID,
                        rights_evidence_state=state,
                    )


class Pdf1bCoreE05Tests(unittest.TestCase):
    def adapt(self, status: str = "success") -> dict:
        bundle = provider_bundle(status)
        return adapt_poppler_observation(
            bundle["observation"],
            source_id=bundle["source_ref_id"],
            fingerprint=bundle["source_fingerprint"],
            provider_version="24.02.0",
            provider_observation_fingerprint="sha256:" + "c" * 64,
            started_at="2026-08-27T10:00:00Z",
            ended_at="2026-08-27T10:00:01Z",
        )

    def test_success_becomes_pdf_geometric_representation_without_invented_semantics(self) -> None:
        adapted = self.adapt()
        validate_attempt_records(adapted)
        representation = adapted["normalized_representation"]
        unit = representation["units"][0]
        self.assertEqual(unit["surface"]["value"], "Raiatea PDF content")
        self.assertEqual(unit["semantic_role"]["value_state"], "unknown")
        self.assertEqual(unit["coordinate"]["value"]["kind"], "pdf-geometric")
        self.assertEqual(unit["coordinate"]["value"]["page_index"], 0)
        self.assertNotIn("page_index", unit["semantic_role"])
        bundle = build_pdf_extraction_bundle(
            source_ref_id=provider_bundle()["source_ref_id"],
            source_fingerprint=provider_bundle()["source_fingerprint"],
            adapted=adapted,
        )
        validate_pdf_extraction_bundle(bundle)

    def test_restricted_attempt_is_valid_e05_evidence_but_has_no_current_representation(self) -> None:
        adapted = self.adapt("restricted")
        validate_attempt_records(adapted)
        self.assertEqual(adapted["run"]["outcome"]["execution"], "rejected")
        self.assertNotIn("normalized_representation", adapted)
        with self.assertRaisesRegex(Exception, "not-publishable"):
            build_pdf_extraction_bundle(
                source_ref_id=provider_bundle("restricted")["source_ref_id"],
                source_fingerprint=provider_bundle("restricted")["source_fingerprint"],
                adapted=adapted,
            )

    def test_link_and_figure_evidence_are_not_coerced_into_text_units(self) -> None:
        adapted = self.adapt()
        representation = adapted["normalized_representation"]
        self.assertEqual(len(representation["units"]), 1)
        serialized = str(representation)
        self.assertNotIn("https://example.invalid/raiatea", serialized)
        self.assertNotIn("decoded_pixel_sha256", serialized)
        original = provider_bundle()["observation"]
        self.assertEqual(len(original["links"]), 1)
        self.assertEqual(len(original["figures"]), 1)


if __name__ == "__main__":
    unittest.main()
