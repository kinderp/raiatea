from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p0_generate_semantic_fixture", BENCH_DIR / "generate_fixtures.py"
)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


class B01SemanticFixtureTests(unittest.TestCase):
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

    def test_semantic_pdf_contains_authored_text_fonts_and_uri_annotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            GEN.generate_all(root)
            data = (root / "B01-PDF-003.pdf").read_bytes()

        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertIn(b"Raiatea B01 PDF 003", data)
        self.assertIn(b"Semantic Structure", data)
        self.assertIn(b"First list item", data)
        self.assertIn(b"raiatea-structure", data)
        self.assertIn(b"/BaseFont /Courier", data)
        self.assertIn(b"/Subtype /Link", data)
        self.assertIn(b"/S /URI", data)
        self.assertIn(b"https://example.invalid/raiatea-benchmark", data)
        self.assertNotIn(b"http://", data)
        self.assertIn(b"%%EOF", data)

    def test_semantic_fixture_manifest_is_fail_closed_and_targets_structure(self):
        fixture = next(
            item for item in self.fixtures["fixtures"] if item["id"] == "B01-PDF-003"
        )
        self.assertEqual(fixture["generator"], "pdf_semantic_structure")
        self.assertEqual(fixture["expected_outcome"], "success")
        self.assertIn("semantic-structure", fixture["traits"])
        self.assertIn("deep-hierarchy", fixture["traits"])
        self.assertIn("list", fixture["traits"])
        self.assertIn("code", fixture["traits"])
        self.assertIn("link-annotation", fixture["traits"])
        self.assertEqual(fixture["dimensions"]["hierarchy"], "target")
        self.assertEqual(fixture["dimensions"]["links"], "target")
        self.assertEqual(fixture["rights"]["redistribution"], "not-established")
        self.assertFalse(fixture["rights"]["public_rights_safe"])
        self.assertEqual(fixture["rights"]["remote_provider"], "denied")

    def test_semantic_gold_is_authored_before_provider_measurement(self):
        gold = self.gold["fixtures"]["B01-PDF-003"]
        units = {unit["id"]: unit for unit in gold["reference_units"]}

        self.assertEqual(units["title"]["type"], "heading")
        self.assertEqual(units["title"]["level"], 1)
        self.assertEqual(units["section"]["type"], "heading")
        self.assertEqual(units["section"]["level"], 2)
        self.assertEqual(units["nested"]["type"], "heading")
        self.assertEqual(units["nested"]["level"], 3)
        self.assertEqual(units["li1"]["type"], "list-item")
        self.assertEqual(units["li2"]["type"], "list-item")
        self.assertEqual(units["code"]["type"], "code")
        self.assertEqual(units["link-label"]["type"], "paragraph")
        self.assertEqual(len(gold["reading_order"]), len(gold["reference_units"]) - 1)
        self.assertEqual(
            gold["links"],
            [
                {
                    "id": "uri-link",
                    "from_unit": "link-label",
                    "kind": "uri",
                    "target": "https://example.invalid/raiatea-benchmark",
                }
            ],
        )
        self.assertIn("typography alone", gold["semantic_intent_note"])

    def test_semantic_fixture_closes_only_its_planned_coverage_gap(self):
        gaps = self.fixtures["coverage_gaps"]
        self.assertFalse(any("B01-PDF-003" in item for item in gaps))
        self.assertTrue(any("B01-PDF-004" in item for item in gaps))
        self.assertTrue(any("B01-PDF-005" in item for item in gaps))
        self.assertTrue(any("B01-PDF-007" in item for item in gaps))


if __name__ == "__main__":
    unittest.main()
