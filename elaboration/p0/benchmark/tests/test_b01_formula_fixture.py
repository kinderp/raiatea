from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p0_generate_formula_fixture", BENCH_DIR / "generate_fixtures.py"
)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


CANONICAL_B01_HASHES = {
    "B01-PDF-001": "be1a5d9ef8a06c5534826ed29cfff34f1d030e0349f39da21b96bfc9a82f4311",
    "B01-PDF-002": "fce2f6285698c63596d9fe4d42fcaff773b787e6521587c50fa23b5691f7edcc",
    "B01-PDF-003": "91c16c6d06b213123256ae4b0ad15f8aa398c2dd5e9af34fc0f27e7cb494061b",
    "B01-PDF-004": "8d4c9d3f70bc22cfe0ee7e9eabd76bc6f39d1baa98032112e44557379a34c3da",
    "B01-PDF-005": "f841920e1e9b2566124c2d174bc6627ecaf5ebc96482898f163a4f3e1aa04456",
    "B01-PDF-006": "f3b711f45bcff702fedb2abdf8efa013b8b074eaa9e0adf555618e9342a488ba",
}


class B01FormulaFixtureTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = json.loads(
            (BENCH_DIR / "manifests" / "fixtures.json").read_text(encoding="utf-8")
        )
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )

    def test_formula_fixture_is_deterministic_and_preserves_prior_b01_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            first_result = GEN.generate_all(first)
            second_result = GEN.generate_all(second)

            first_hashes = {item["id"]: item["sha256"] for item in first_result["generated"]}
            second_hashes = {item["id"]: item["sha256"] for item in second_result["generated"]}
            for fixture_id, expected_sha in CANONICAL_B01_HASHES.items():
                self.assertEqual(first_hashes[fixture_id], expected_sha)
                self.assertEqual(second_hashes[fixture_id], expected_sha)

            data = (first / "B01-PDF-006.pdf").read_bytes()
            self.assertEqual(len(data), 1621)
            self.assertEqual(hashlib.sha256(data).hexdigest(), CANONICAL_B01_HASHES["B01-PDF-006"])

    def test_formula_pdf_contains_separate_positioned_glyphs_and_fraction_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            GEN.generate_all(root)
            data = (root / "B01-PDF-006.pdf").read_bytes()

        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertIn(b"Raiatea B01 PDF 006", data)
        self.assertIn(b"Body text before the benchmark formulas.", data)
        self.assertIn(b"Body text after the benchmark formulas.", data)
        self.assertIn(b"BT /F1 16 Tf 1 0 0 1 156 610 Tm (c) Tj ET", data)
        self.assertIn(b"BT /F1 9 Tf 1 0 0 1 166 622 Tm (2) Tj ET", data)
        self.assertIn(b"BT /F1 9 Tf 1 0 0 1 118 567 Tm (2) Tj ET", data)
        self.assertIn(b"108 486 m 164 486 l S", data)
        self.assertIn(b"BT /F1 14 Tf 1 0 0 1 132 462 Tm (c) Tj ET", data)
        self.assertNotIn(b"/StructTreeRoot", data)
        self.assertNotIn(b"/MathML", data)
        self.assertIn(b"%%EOF", data)

    def test_manifest_targets_content_structure_and_geometry_separately(self):
        fixture = next(
            item for item in self.fixtures["fixtures"] if item["id"] == "B01-PDF-006"
        )
        self.assertEqual(fixture["generator"], "pdf_formula_fidelity")
        self.assertEqual(fixture["profile"], "normal-quality")
        self.assertIn("mathematical-formula", fixture["traits"])
        self.assertIn("positioned-superscript", fixture["traits"])
        self.assertIn("fraction-bar", fixture["traits"])
        self.assertEqual(fixture["dimensions"]["formula_tokens"], "target")
        self.assertEqual(fixture["dimensions"]["formula_presence"], "target")
        self.assertEqual(fixture["dimensions"]["formula_structure"], "target")
        self.assertEqual(fixture["dimensions"]["formula_geometry"], "target")
        self.assertEqual(fixture["dimensions"]["token_geometry"], "target")
        self.assertEqual(fixture["rights"]["redistribution"], "not-established")
        self.assertFalse(fixture["rights"]["public_rights_safe"])
        self.assertEqual(fixture["rights"]["remote_provider"], "denied")
        self.assertEqual(fixture["rights"]["decision_issue"], 131)

    def test_gold_declares_superscript_and_fraction_relations_without_visual_inference(self):
        gold = self.gold["fixtures"]["B01-PDF-006"]
        self.assertEqual(
            gold["coordinate_semantics"],
            {"kind": "pdf-page-geometry", "units": "points", "origin": "bottom-left"},
        )
        self.assertEqual(
            gold["formula_display_order"],
            ["formula-energy", "formula-pythagorean", "formula-fraction"],
        )
        formulas = {formula["id"]: formula for formula in gold["formulas"]}
        self.assertEqual(len(formulas), 3)

        energy = formulas["formula-energy"]
        self.assertEqual(
            energy["relations"],
            [{"kind": "superscript", "base_token": "f1-c", "script_token": "f1-exp2"}],
        )

        pythagorean = formulas["formula-pythagorean"]
        self.assertEqual(
            [relation["kind"] for relation in pythagorean["relations"]],
            ["superscript", "superscript", "superscript"],
        )

        fraction = formulas["formula-fraction"]
        relation = fraction["relations"][0]
        self.assertEqual(relation["kind"], "fraction")
        self.assertEqual(
            relation["numerator_tokens"],
            ["f3-lparen", "f3-a", "f3-plus", "f3-b", "f3-rparen"],
        )
        self.assertEqual(relation["denominator_tokens"], ["f3-c"])
        self.assertEqual(relation["bar_region"], [108, 484, 164, 488])
        self.assertIn("never credited from font size", gold["formula_intent_note"])
        self.assertIn("not semantic math tags", gold["formula_intent_note"])

    def test_formula_internal_order_is_separate_from_surrounding_reading_order(self):
        gold = self.gold["fixtures"]["B01-PDF-006"]
        self.assertEqual(
            gold["reading_order"],
            [["title", "body-before"], ["body-before", "body-after"]],
        )
        self.assertIn("separate from authored formula token order", gold["reading_order_note"])
        for formula in gold["formulas"]:
            token_ids = [token["id"] for token in formula["tokens"]]
            self.assertEqual(formula["token_order"], token_ids)

    def test_formula_gap_is_closed_without_hiding_later_b01_gaps(self):
        gaps = self.fixtures["coverage_gaps"]
        self.assertFalse(any(item.startswith("B01-PDF-006 ") for item in gaps))
        self.assertTrue(any(item.startswith("B01-PDF-007 ") for item in gaps))
        self.assertTrue(any("malformed/access-controlled" in item for item in gaps))


if __name__ == "__main__":
    unittest.main()
