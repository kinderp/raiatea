from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p0_generate_figure_fixture", BENCH_DIR / "generate_fixtures.py"
)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


class B01FigureFixtureTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = json.loads(
            (BENCH_DIR / "manifests" / "fixtures.json").read_text(encoding="utf-8")
        )
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )

    def test_existing_b01_pdf_bytes_remain_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = GEN.generate_all(Path(tmp))
        hashes = {item["id"]: item["sha256"] for item in result["generated"]}
        self.assertEqual(
            hashes["B01-PDF-001"],
            "be1a5d9ef8a06c5534826ed29cfff34f1d030e0349f39da21b96bfc9a82f4311",
        )
        self.assertEqual(
            hashes["B01-PDF-002"],
            "fce2f6285698c63596d9fe4d42fcaff773b787e6521587c50fa23b5691f7edcc",
        )
        self.assertEqual(
            hashes["B01-PDF-003"],
            "91c16c6d06b213123256ae4b0ad15f8aa398c2dd5e9af34fc0f27e7cb494061b",
        )

    def test_figure_pdf_contains_explicit_image_xobject_caption_and_body_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = GEN.generate_all(root)
            data = (root / "B01-PDF-004.pdf").read_bytes()

        by_id = {item["id"]: item for item in result["generated"]}
        self.assertEqual(
            by_id["B01-PDF-004"]["sha256"],
            "8d4c9d3f70bc22cfe0ee7e9eabd76bc6f39d1baa98032112e44557379a34c3da",
        )
        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertIn(b"/Subtype /Image", data)
        self.assertIn(b"/Width 4 /Height 3", data)
        self.assertIn(b"/ColorSpace /DeviceRGB", data)
        self.assertIn(b"/BitsPerComponent 8", data)
        self.assertIn(b"/Im1 Do", data)
        self.assertIn(b"Body text before the benchmark figure.", data)
        self.assertIn(b"Figure 1. Deterministic Raiatea color grid.", data)
        self.assertIn(b"Body text after the benchmark figure.", data)
        self.assertIn(GEN._figure_pixel_payload(), data)
        self.assertIn(b"%%EOF", data)

    def test_authored_pixel_payload_has_stable_identity(self):
        payload = GEN._figure_pixel_payload()
        self.assertEqual(len(payload), 4 * 3 * 3)
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            "2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee",
        )

    def test_figure_manifest_is_fail_closed_and_separates_dimensions(self):
        fixture = next(
            item for item in self.fixtures["fixtures"] if item["id"] == "B01-PDF-004"
        )
        self.assertEqual(fixture["generator"], "pdf_figure_caption")
        self.assertIn("embedded-raster", fixture["traits"])
        self.assertIn("caption", fixture["traits"])
        self.assertEqual(fixture["dimensions"]["figures"], "target")
        self.assertEqual(fixture["dimensions"]["caption"], "target")
        self.assertEqual(fixture["dimensions"]["asset_identity"], "target")
        self.assertEqual(fixture["dimensions"]["figure_caption_association"], "target")
        self.assertEqual(fixture["rights"]["redistribution"], "not-established")
        self.assertFalse(fixture["rights"]["public_rights_safe"])
        self.assertEqual(fixture["rights"]["remote_provider"], "denied")

    def test_figure_gold_does_not_equate_proximity_with_association(self):
        gold = self.gold["fixtures"]["B01-PDF-004"]
        units = {unit["id"]: unit for unit in gold["reference_units"]}
        figure = gold["figures"][0]

        self.assertEqual(units["caption"]["type"], "caption")
        self.assertEqual(
            units["caption"]["text"], "Figure 1. Deterministic Raiatea color grid."
        )
        self.assertEqual(figure["kind"], "raster-image")
        self.assertEqual(figure["pixel_width"], 4)
        self.assertEqual(figure["pixel_height"], 3)
        self.assertEqual(
            figure["pixel_payload_sha256"],
            "2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee",
        )
        self.assertEqual(
            gold["figure_caption_relations"],
            [{"figure_id": "figure-1", "caption_unit": "caption", "relation": "caption-of"}],
        )
        self.assertIn("never from spatial proximity alone", gold["figure_intent_note"])
        self.assertNotIn("alt", gold)

    def test_figure_fixture_closes_only_its_planned_coverage_gap(self):
        gaps = self.fixtures["coverage_gaps"]
        self.assertFalse(any(item.startswith("B01-PDF-004 ") for item in gaps))
        self.assertTrue(any(item.startswith("B01-PDF-005 ") for item in gaps))
        self.assertTrue(any(item.startswith("B01-PDF-006 ") for item in gaps))
        self.assertTrue(any(item.startswith("B01-PDF-007 ") for item in gaps))


if __name__ == "__main__":
    unittest.main()
