from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_score_b01_figure", ROUTES / "score_b01_figure.py"
)
SCORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORE)


class B01FigureScoringTests(unittest.TestCase):
    def setUp(self):
        gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )
        self.gold = gold["fixtures"]["B01-PDF-004"]
        self.blocks = [
            {"text": "Raiatea B01 PDF 004", "page_index": 0},
            {"text": "Body text before the benchmark figure.", "page_index": 0},
            {"text": "Figure 1. Deterministic Raiatea color grid.", "page_index": 0},
            {"text": "Body text after the benchmark figure.", "page_index": 0},
        ]

    def test_missing_figure_collection_is_not_zero_or_failure(self):
        dimensions = SCORE.measure_b01_figure_dimensions(
            {"blocks": self.blocks}, self.gold
        )
        self.assertEqual(dimensions["caption_text"]["status"], "measured")
        self.assertEqual(dimensions["caption_text"]["exact_count"], 1)
        self.assertEqual(dimensions["figure_presence"]["status"], "not-measured")
        self.assertEqual(dimensions["figure_geometry"]["status"], "not-measured")
        self.assertEqual(dimensions["asset_identity"]["status"], "not-measured")
        self.assertEqual(
            dimensions["figure_caption_association"]["status"], "not-measured"
        )

    def test_explicit_figure_can_measure_exact_geometry_and_pixel_identity(self):
        observation = {
            "blocks": self.blocks,
            "figures": [
                {
                    "provider_ref": "image-1",
                    "page_index": 0,
                    "bbox_points_bottom_left": [72.0, 500.0, 252.0, 620.0],
                    "decoded_pixel_sha256": "2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee",
                    "asset_sha256": "provider-encoded-sha",
                    "asset_bytes": 113,
                }
            ],
        }
        dimensions = SCORE.measure_b01_figure_dimensions(observation, self.gold)
        geometry = dimensions["figure_geometry"]
        self.assertTrue(dimensions["figure_presence"]["count_exact"])
        self.assertEqual(geometry["status"], "measured")
        self.assertEqual(geometry["page_exact_count"], 1)
        self.assertEqual(geometry["bbox_exact_count"], 1)
        self.assertEqual(geometry["max_observed_edge_error_points"], 0.0)
        self.assertEqual(geometry["figures"][0]["absolute_edge_error_points"], [0.0, 0.0, 0.0, 0.0])
        self.assertEqual(geometry["figures"][0]["matching_basis"], "single-figure-cardinality")
        self.assertEqual(dimensions["asset_identity"]["status"], "measured")
        self.assertEqual(dimensions["asset_identity"]["exact_count"], 1)

    def test_ambiguous_figure_count_does_not_use_first_item_as_gold_identity(self):
        observation = {
            "blocks": self.blocks,
            "figures": [
                {
                    "provider_ref": "image-1",
                    "page_index": 0,
                    "bbox_points_bottom_left": [72.0, 500.0, 252.0, 620.0],
                    "decoded_pixel_sha256": "2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee",
                },
                {
                    "provider_ref": "image-extra",
                    "page_index": 0,
                    "bbox_points_bottom_left": [300.0, 300.0, 320.0, 320.0],
                    "decoded_pixel_sha256": "extra",
                },
            ],
        }
        dimensions = SCORE.measure_b01_figure_dimensions(observation, self.gold)
        self.assertEqual(dimensions["figure_presence"]["status"], "measured")
        self.assertEqual(dimensions["figure_presence"]["observed_count"], 2)
        self.assertFalse(dimensions["figure_presence"]["count_exact"])
        self.assertEqual(dimensions["figure_geometry"]["status"], "not-measured")
        self.assertEqual(dimensions["figure_geometry"]["evidence_count"], 0)
        self.assertEqual(dimensions["asset_identity"]["status"], "not-measured")
        self.assertEqual(dimensions["asset_identity"]["evidence_count"], 0)
        self.assertIn("ambiguous", dimensions["figure_geometry"]["reason"])

    def test_geometry_reports_raw_error_without_post_hoc_tolerance(self):
        observation = {
            "blocks": self.blocks,
            "figures": [
                {
                    "provider_ref": "picture-0",
                    "page_index": 0,
                    "bbox_points_bottom_left": [
                        70.90522003173828,
                        500.0570068359375,
                        252.6000518798828,
                        621.0237884521484,
                    ],
                }
            ],
        }
        geometry = SCORE.measure_b01_figure_dimensions(
            observation, self.gold
        )["figure_geometry"]
        row = geometry["figures"][0]
        self.assertEqual(geometry["status"], "measured")
        self.assertEqual(geometry["page_exact_count"], 1)
        self.assertEqual(geometry["bbox_exact_count"], 0)
        self.assertAlmostEqual(geometry["max_observed_edge_error_points"], 1.0947799682617188)
        self.assertAlmostEqual(row["absolute_edge_error_points"][0], 1.0947799682617188)
        self.assertAlmostEqual(row["absolute_edge_error_points"][1], 0.0570068359375)
        self.assertAlmostEqual(row["absolute_edge_error_points"][2], 0.6000518798828125)
        self.assertAlmostEqual(row["absolute_edge_error_points"][3], 1.0237884521484375)
        self.assertIn("post-hoc tolerance", geometry["policy"])
        self.assertIn("no list-position matching", geometry["policy"])

    def test_nearby_caption_never_creates_association(self):
        observation = {
            "blocks": self.blocks,
            "figures": [
                {
                    "provider_ref": "image-1",
                    "page_index": 0,
                    "bbox_points_bottom_left": [72.0, 500.0, 252.0, 620.0],
                }
            ],
        }
        dimensions = SCORE.measure_b01_figure_dimensions(observation, self.gold)
        association = dimensions["figure_caption_association"]
        self.assertEqual(association["status"], "not-measured")
        self.assertFalse(association["proximity_inference"])
        self.assertIn("Spatial proximity", association["reason"])

    def test_explicit_provider_relation_is_creditable(self):
        observation = {
            "blocks": self.blocks,
            "figures": [{"provider_ref": "picture-0", "page_index": 0}],
            "figure_caption_relations": [
                {
                    "gold_figure_id": "figure-1",
                    "gold_caption_unit": "caption",
                    "provider_relation_source": "provider-explicit-caption-ref",
                }
            ],
        }
        association = SCORE.measure_b01_figure_dimensions(
            observation, self.gold
        )["figure_caption_association"]
        self.assertEqual(association["status"], "measured")
        self.assertEqual(association["evidence_count"], 1)
        self.assertEqual(association["exact_count"], 1)
        self.assertFalse(association["proximity_inference"])

    def test_encoded_asset_hash_alone_does_not_claim_pixel_identity(self):
        observation = {
            "blocks": self.blocks,
            "figures": [
                {
                    "provider_ref": "image-1",
                    "page_index": 0,
                    "asset_sha256": "encoded-only",
                    "asset_bytes": 42,
                }
            ],
        }
        identity = SCORE.measure_b01_figure_dimensions(
            observation, self.gold
        )["asset_identity"]
        self.assertEqual(identity["status"], "not-measured")
        self.assertEqual(identity["evidence_count"], 0)


if __name__ == "__main__":
    unittest.main()
