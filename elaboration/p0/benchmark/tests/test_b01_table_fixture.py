from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p0_generate_fixtures", BENCH_DIR / "generate_fixtures.py"
)
GENERATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GENERATE)


CANONICAL_B01_HASHES = {
    "B01-PDF-001": "be1a5d9ef8a06c5534826ed29cfff34f1d030e0349f39da21b96bfc9a82f4311",
    "B01-PDF-002": "fce2f6285698c63596d9fe4d42fcaff773b787e6521587c50fa23b5691f7edcc",
    "B01-PDF-003": "91c16c6d06b213123256ae4b0ad15f8aa398c2dd5e9af34fc0f27e7cb494061b",
    "B01-PDF-004": "8d4c9d3f70bc22cfe0ee7e9eabd76bc6f39d1baa98032112e44557379a34c3da",
    "B01-PDF-005": "0a00e239f3e06473442852ee2c49b1fd032e8d840e98c2a7968c0fb33b236eb1",
}


class B01TableFixtureTests(unittest.TestCase):
    def setUp(self):
        self.fixtures_manifest = json.loads(
            (BENCH_DIR / "manifests" / "fixtures.json").read_text(encoding="utf-8")
        )
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )

    def test_generated_table_fixture_is_deterministic_and_preserves_prior_b01_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            GENERATE.generate_all(first)
            GENERATE.generate_all(second)

            for fixture_id, expected_sha in CANONICAL_B01_HASHES.items():
                filename = f"{fixture_id}.pdf"
                first_bytes = (first / filename).read_bytes()
                second_bytes = (second / filename).read_bytes()
                self.assertEqual(first_bytes, second_bytes, fixture_id)
                self.assertEqual(hashlib.sha256(first_bytes).hexdigest(), expected_sha)

            table_bytes = (first / "B01-PDF-005.pdf").read_bytes()
            self.assertEqual(len(table_bytes), 1274)
            for text in (
                b"Raiatea B01 PDF 005",
                b"Body text before the benchmark table.",
                b"Item",
                b"Qty",
                b"Price",
                b"Alpha",
                b"Beta",
                b"Total",
                b"14.00",
                b"Body text after the benchmark table.",
            ):
                self.assertIn(text, table_bytes)
            self.assertIn(b"72 440 m 72 600 l S", table_bytes)
            self.assertIn(b"72 600 m 540 600 l S", table_bytes)
            self.assertIn(b"540 440 m 540 600 l S", table_bytes)
            self.assertIn(b"72 440 m 540 440 l S", table_bytes)

    def test_manifest_declares_table_dimensions_and_fail_closed_rights(self):
        fixture = next(
            item
            for item in self.fixtures_manifest["fixtures"]
            if item["id"] == "B01-PDF-005"
        )
        self.assertEqual(fixture["generator"], "pdf_table_structure")
        self.assertEqual(fixture["profile"], "normal-quality")
        self.assertEqual(fixture["expected_outcome"], "success")
        self.assertEqual(fixture["dimensions"]["tables"], "target")
        self.assertEqual(fixture["dimensions"]["table_cells"], "target")
        self.assertEqual(fixture["dimensions"]["table_topology"], "target")
        self.assertEqual(fixture["dimensions"]["table_geometry"], "target")
        self.assertEqual(fixture["dimensions"]["header_roles"], "target")
        self.assertFalse(fixture["rights"]["public_rights_safe"])
        self.assertEqual(fixture["rights"]["redistribution"], "not-established")
        self.assertEqual(fixture["rights"]["remote_provider"], "denied")
        self.assertEqual(fixture["rights"]["decision_issue"], 131)

    def test_gold_declares_one_complete_four_by_three_table(self):
        fixture = self.gold["fixtures"]["B01-PDF-005"]
        self.assertEqual(
            fixture["coordinate_semantics"],
            "PDF page points, bottom-left origin",
        )
        self.assertEqual(len(fixture["tables"]), 1)
        table = fixture["tables"][0]
        self.assertEqual(table["id"], "table-1")
        self.assertEqual(table["page_index"], 0)
        self.assertEqual(table["region"], [72, 440, 540, 600])
        self.assertEqual(table["row_count"], 4)
        self.assertEqual(table["column_count"], 3)
        self.assertEqual(len(table["cells"]), 12)

        coordinates = {(cell["row"], cell["column"]) for cell in table["cells"]}
        self.assertEqual(
            coordinates,
            {(row, column) for row in range(4) for column in range(3)},
        )
        self.assertEqual(len({cell["id"] for cell in table["cells"]}), 12)
        self.assertEqual(
            [cell["text"] for cell in table["cells"]],
            [
                "Item", "Qty", "Price",
                "Alpha", "2", "3.50",
                "Beta", "1", "7.00",
                "Total", "3", "14.00",
            ],
        )
        self.assertTrue(
            all(cell["role"] == "header" for cell in table["cells"][:3])
        )
        self.assertTrue(
            all(cell["role"] == "body" for cell in table["cells"][3:])
        )
        for cell in table["cells"]:
            left, bottom, right, top = cell["region"]
            self.assertLess(left, right)
            self.assertLess(bottom, top)
            self.assertGreaterEqual(left, table["region"][0])
            self.assertGreaterEqual(bottom, table["region"][1])
            self.assertLessEqual(right, table["region"][2])
            self.assertLessEqual(top, table["region"][3])
            self.assertNotIn("row_span", cell)
            self.assertNotIn("column_span", cell)

    def test_table_internal_topology_is_separate_from_surrounding_reading_order(self):
        fixture = self.gold["fixtures"]["B01-PDF-005"]
        self.assertEqual(
            fixture["reading_order"], ["title", "body-before", "body-after"]
        )
        self.assertIn("table topology", fixture["reading_order_note"])
        self.assertIn("Provider-native table structure", fixture["table_intent_note"])

    def test_table_coverage_gap_is_closed_without_hiding_later_b01_gaps(self):
        gaps = self.fixtures_manifest["coverage_gaps"]
        self.assertFalse(any("B01-PDF-005" in gap for gap in gaps))
        self.assertTrue(any("B01-PDF-006" in gap for gap in gaps))
        self.assertTrue(any("B01-PDF-007" in gap for gap in gaps))


if __name__ == "__main__":
    unittest.main()
