from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p0_b01_pdf_007_fixture", BENCH_DIR / "b01_pdf_007_fixture.py"
)
FIXTURE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FIXTURE)


class B01DefectiveNativeFixtureTests(unittest.TestCase):
    def setUp(self):
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "b01-pdf-007-gold.json").read_text(
                encoding="utf-8"
            )
        )

    def test_fixture_bytes_are_deterministic_and_pinned(self):
        first = FIXTURE.build_fixture()
        second = FIXTURE.build_fixture()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 76090)
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            "4ed576898177b66cc7e187fbf791f32d4721a30c890ee429fad54949f53a59f0",
        )
        self.assertEqual(hashlib.sha256(first).hexdigest(), FIXTURE.EXPECTED_PDF_SHA256)

    def test_raster_payload_is_deterministic_project_authored_evidence(self):
        width, height, pixels = FIXTURE.raster_pixels()
        self.assertEqual((width, height), (834, 90))
        self.assertEqual(
            hashlib.sha256(pixels).hexdigest(),
            "9b86156aecfab15d577faee643ef1eaa04b9a565bf37f5db79b7f9090a9bdec3",
        )
        self.assertEqual(hashlib.sha256(pixels).hexdigest(), FIXTURE.EXPECTED_PIXEL_SHA256)
        self.assertEqual(set(pixels), {0, 255})

    def test_pdf_has_native_text_and_explicit_raster_xobject(self):
        pdf = FIXTURE.build_fixture()
        self.assertIn(b"Raiatea B01 PDF 007", pdf)
        self.assertIn(b"Native text before the raster-only region.", pdf)
        self.assertIn(b"Native text after the raster-only region.", pdf)
        self.assertIn(b"/Subtype /Image", pdf)
        self.assertIn(b"/Width 834 /Height 90", pdf)
        self.assertIn(b"/ColorSpace /DeviceGray /BitsPerComponent 8", pdf)

    def test_raster_words_are_not_present_in_native_pdf_text_layer(self):
        pdf = FIXTURE.build_fixture()
        self.assertNotIn(FIXTURE.RASTER_TEXT.encode("ascii"), pdf)
        evidence = FIXTURE.evidence()
        self.assertFalse(evidence["raster_words_present_in_pdf_text_layer"])

    def test_gold_separates_native_raster_and_visible_page_coverage(self):
        gold = self.gold
        self.assertEqual(gold["fixture"]["id"], "B01-PDF-007")
        self.assertIn("defective-native-text-layer", gold["fixture"]["source_traits"])
        by_id = {unit["id"]: unit for unit in gold["reference_units"]}
        self.assertEqual(by_id["raster-target"]["text"], "OCR TARGET 2026")
        self.assertFalse(by_id["raster-target"]["native_text_layer_authored"])
        self.assertEqual(
            by_id["raster-target"]["raster_pixel_sha256"],
            FIXTURE.EXPECTED_PIXEL_SHA256,
        )
        self.assertEqual(
            gold["native_text_layer_units"],
            ["title", "native-before", "native-after"],
        )
        self.assertEqual(gold["raster_visible_units"], ["raster-target"])
        self.assertTrue(gold["routing_intent"]["native_partial_is_not_complete_success"])
        self.assertFalse(
            gold["routing_intent"]["provider_success_status_alone_proves_completeness"]
        )

    def test_rights_remain_fail_closed(self):
        rights = self.gold["fixture"]["rights"]
        self.assertEqual(rights["redistribution"], "not-established")
        self.assertFalse(rights["public_rights_safe"])
        self.assertEqual(rights["remote_provider"], "denied")
        self.assertEqual(rights["decision_issue"], 131)


if __name__ == "__main__":
    unittest.main()
