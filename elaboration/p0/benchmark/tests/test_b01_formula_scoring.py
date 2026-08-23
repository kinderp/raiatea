from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_score_b01_formula", ROUTES / "score_b01_formula.py"
)
SCORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORE)


class B01FormulaScoringTests(unittest.TestCase):
    def setUp(self):
        gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )
        self.gold = gold["fixtures"]["B01-PDF-006"]

    def test_visible_surface_does_not_create_math_relations(self):
        observation = {
            "blocks": [
                {"text": "E = mc 2"},
                {"text": "x 2 + y 2 = z 2"},
                {"text": "( a + b ) c"},
            ]
        }
        dimensions = SCORE.measure_b01_formula_dimensions(observation, self.gold)
        self.assertEqual(dimensions["formula_surface_content"]["exact_once_count"], 3)
        self.assertEqual(dimensions["formula_display_order"]["satisfied_edges"], 2)
        relations = dimensions["explicit_math_relations"]
        self.assertEqual(relations["status"], "not-measured")
        self.assertEqual(relations["evidence_count"], 0)
        self.assertFalse(relations["visual_inference"])

    def test_repeated_exponent_glyphs_use_geometry_only_for_bbox_binding(self):
        observation = {
            "blocks": [
                {
                    "text": "2",
                    "page_index": 0,
                    "bbox_points_bottom_left": [166.0, 620.1, 171.0, 628.4],
                },
                {
                    "text": "2",
                    "page_index": 0,
                    "bbox_points_bottom_left": [118.0, 565.1, 123.0, 573.4],
                },
                {
                    "text": "2",
                    "page_index": 0,
                    "bbox_points_bottom_left": [160.0, 565.1, 165.0, 573.4],
                },
                {
                    "text": "2",
                    "page_index": 0,
                    "bbox_points_bottom_left": [202.0, 565.1, 207.0, 573.4],
                },
            ]
        }
        dimensions = SCORE.measure_b01_formula_dimensions(observation, self.gold)
        geometry = dimensions["token_geometry"]
        exponent_rows = [
            row
            for row in geometry["tokens"]
            if row["token_id"] in {"f1-exp2", "f2-x2", "f2-y2", "f2-z2"}
        ]
        self.assertTrue(all(row["evidence_available"] for row in exponent_rows))
        self.assertEqual(dimensions["explicit_math_relations"]["status"], "not-measured")

    def test_picture_grouping_is_diagnostic_not_formula_semantics(self):
        observation = {
            "blocks": [{"text": "E = mc 2"}],
            "provider_formula_groups": [
                {
                    "provider_ref": "#/pictures/0",
                    "provider_label": "picture",
                    "mathematical_semantics": False,
                }
            ],
        }
        dimensions = SCORE.measure_b01_formula_dimensions(observation, self.gold)
        diagnostic = dimensions["provider_group_diagnostic"]
        self.assertEqual(diagnostic["status"], "observed-nonsemantic")
        self.assertEqual(diagnostic["observed_count"], 1)
        self.assertEqual(dimensions["explicit_math_relations"]["status"], "not-measured")

    def test_missing_provider_text_is_not_scored_as_zero_fidelity(self):
        dimensions = SCORE.measure_b01_formula_dimensions({}, self.gold)
        self.assertEqual(dimensions["formula_surface_content"]["status"], "not-measured")
        self.assertEqual(dimensions["token_geometry"]["status"], "not-measured")
        self.assertEqual(dimensions["explicit_math_relations"]["status"], "not-measured")


if __name__ == "__main__":
    unittest.main()
