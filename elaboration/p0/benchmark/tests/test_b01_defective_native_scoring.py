from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_score_b01_defective_native", ROUTES / "score_b01_defective_native.py"
)
SCORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORE)


class B01DefectiveNativeScoringTests(unittest.TestCase):
    def setUp(self):
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "b01-pdf-007-gold.json").read_text(
                encoding="utf-8"
            )
        )
        self.native_blocks = [
            {
                "text": "Raiatea B01 PDF 007",
                "page_index": 0,
                "bbox_points_bottom_left": [72.0, 725.86, 266.54, 744.36],
            },
            {
                "text": "Native text before the raster-only region.",
                "page_index": 0,
                "bbox_points_bottom_left": [72.0, 662.516, 286.092, 673.616],
            },
            {
                "text": "Native text after the raster-only region.",
                "page_index": 0,
                "bbox_points_bottom_left": [72.0, 477.516, 276.084, 488.616],
            },
        ]

    def test_nominal_success_with_missing_raster_target_requires_benchmark_fallback(self):
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"route": "synthetic-native", "status": "success", "warnings": [], "blocks": self.native_blocks},
            self.gold,
        )
        self.assertEqual(dimensions["native_text_content"]["exact_once_count"], 3)
        self.assertEqual(dimensions["raster_visible_text_content"]["recovered_count"], 0)
        self.assertEqual(dimensions["visible_page_coverage"]["coverage_fraction"], "3/4")
        self.assertEqual(dimensions["raster_region_alignment"]["candidate_count"], 0)
        verdict = dimensions["benchmark_fallback_verdict"]
        self.assertEqual(verdict["status"], "measured")
        self.assertTrue(verdict["required"])
        self.assertTrue(verdict["nominal_provider_success_with_material_visible_gap"])
        self.assertFalse(verdict["raster_region_partial_surface_evidence"])
        self.assertFalse(verdict["production_routing_heuristic"])

    def test_recovered_raster_target_closes_visible_page_gap(self):
        blocks = self.native_blocks + [
            {
                "text": "OCR TARGET 2026",
                "page_index": 0,
                "bbox_points_bottom_left": [80.0, 545.0, 300.0, 580.0],
            }
        ]
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"route": "synthetic-ocr", "status": "success", "warnings": [], "blocks": blocks},
            self.gold,
        )
        self.assertEqual(dimensions["raster_visible_text_content"]["exact_once_count"], 1)
        self.assertEqual(dimensions["visible_page_coverage"]["coverage_fraction"], "4/4")
        self.assertFalse(dimensions["benchmark_fallback_verdict"]["required"])
        self.assertEqual(dimensions["raster_visible_text_coordinates"]["evidence_count"], 1)
        alignment = dimensions["raster_region_alignment"]
        self.assertEqual(alignment["candidate_count"], 1)
        self.assertEqual(alignment["exact_candidate_count"], 1)
        self.assertEqual(alignment["token_multiset_exact_candidate_count"], 1)

    def test_wrong_word_order_is_partial_ocr_surface_not_exact_recovery(self):
        blocks = self.native_blocks + [
            {
                "text": "TARGET OCR 2026",
                "page_index": 0,
                "bbox_points_bottom_left": [70.0, 540.333, 491.667, 591.333],
            }
        ]
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"route": "synthetic-ocr", "status": "success", "warnings": [], "blocks": blocks},
            self.gold,
        )
        self.assertEqual(dimensions["raster_visible_text_content"]["recovered_count"], 0)
        self.assertEqual(dimensions["visible_page_coverage"]["coverage_fraction"], "3/4")
        alignment = dimensions["raster_region_alignment"]
        self.assertEqual(alignment["candidate_count"], 1)
        self.assertEqual(alignment["exact_candidate_count"], 0)
        self.assertEqual(alignment["token_multiset_exact_candidate_count"], 1)
        candidate = alignment["units"][0]["candidates"][0]
        self.assertFalse(candidate["token_order_exact"])
        self.assertTrue(candidate["token_multiset_exact"])
        self.assertTrue(candidate["partial_surface_evidence"])
        verdict = dimensions["benchmark_fallback_verdict"]
        self.assertTrue(verdict["required"])
        self.assertTrue(verdict["raster_region_partial_surface_evidence"])
        self.assertTrue(verdict["raster_region_token_set_exact_order_mismatch"])
        self.assertIn("partial OCR surface", verdict["reason"])

    def test_raster_image_bbox_is_not_substituted_for_missing_ocr_text_coordinate(self):
        observation = {
            "status": "success",
            "warnings": [],
            "blocks": self.native_blocks,
            "figures": [
                {
                    "page_index": 0,
                    "bbox_points_bottom_left": [72.0, 540.0, 489.0, 585.0],
                }
            ],
        }
        dimensions = SCORE.measure_b01_defective_native_dimensions(observation, self.gold)
        self.assertEqual(dimensions["raster_visible_text_coordinates"]["status"], "not-measured")
        self.assertEqual(dimensions["raster_visible_text_coordinates"]["evidence_count"], 0)
        self.assertTrue(dimensions["benchmark_fallback_verdict"]["required"])

    def test_provider_success_and_warnings_do_not_prove_completeness(self):
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {
                "route": "synthetic",
                "status": "success",
                "warnings": [{"code": "bbox-not-exposed"}],
                "blocks": self.native_blocks,
            },
            self.gold,
        )
        outcome = dimensions["provider_outcome"]
        self.assertEqual(outcome["route_status"], "success")
        self.assertEqual(outcome["warning_count"], 1)
        self.assertFalse(outcome["explicit_completeness_state_available"])
        self.assertTrue(
            dimensions["benchmark_fallback_verdict"][
                "nominal_provider_success_with_material_visible_gap"
            ]
        )

    def test_missing_text_collection_is_not_zero_and_does_not_force_fallback(self):
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"route": "synthetic", "status": "failed", "warnings": []}, self.gold
        )
        self.assertEqual(dimensions["native_text_content"]["status"], "not-measured")
        self.assertEqual(dimensions["raster_visible_text_content"]["status"], "not-measured")
        self.assertEqual(dimensions["raster_region_alignment"]["status"], "not-measured")
        self.assertEqual(dimensions["visible_page_coverage"]["status"], "not-measured")
        verdict = dimensions["benchmark_fallback_verdict"]
        self.assertEqual(verdict["status"], "not-measured")
        self.assertIsNone(verdict["required"])

    def test_malformed_text_item_propagates_partial_state(self):
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {
                "status": "success",
                "warnings": [],
                "blocks": self.native_blocks + ["malformed-block"],
            },
            self.gold,
        )
        self.assertEqual(dimensions["native_text_content"]["status"], "partial")
        self.assertEqual(dimensions["raster_visible_text_content"]["status"], "partial")
        self.assertEqual(dimensions["raster_region_alignment"]["status"], "partial")
        self.assertEqual(dimensions["visible_page_coverage"]["status"], "partial")
        self.assertEqual(dimensions["benchmark_fallback_verdict"]["status"], "partial")
        self.assertTrue(dimensions["benchmark_fallback_verdict"]["required"])

    def test_tika_like_blocks_preserve_content_but_not_coordinates(self):
        blocks = [
            {"text": block["text"], "page_index": 0, "bbox_points_bottom_left": None}
            for block in self.native_blocks
        ]
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"status": "success", "warnings": [], "blocks": blocks}, self.gold
        )
        self.assertEqual(dimensions["native_text_content"]["exact_once_count"], 3)
        self.assertEqual(dimensions["native_text_coordinates"]["status"], "not-measured")
        self.assertEqual(dimensions["native_text_coordinates"]["evidence_count"], 0)

    def test_duplicate_raster_text_is_visible_but_ambiguous(self):
        blocks = self.native_blocks + [
            {"text": "OCR TARGET 2026", "page_index": 0},
            {"text": "OCR TARGET 2026", "page_index": 0},
        ]
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"status": "success", "warnings": [], "blocks": blocks}, self.gold
        )
        raster = dimensions["raster_visible_text_content"]
        self.assertEqual(raster["recovered_count"], 1)
        self.assertEqual(raster["exact_once_count"], 0)
        self.assertEqual(raster["ambiguous_count"], 1)
        self.assertFalse(dimensions["benchmark_fallback_verdict"]["required"])
        self.assertEqual(dimensions["raster_visible_text_coordinates"]["status"], "not-measured")

    def test_unattributed_docling_blocks_keep_native_ocr_overlap_unknown(self):
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"status": "success", "warnings": [], "blocks": self.native_blocks},
            self.gold,
        )
        reconciliation = dimensions["native_ocr_reconciliation"]
        self.assertEqual(reconciliation["status"], "not-measured")
        self.assertEqual(reconciliation["unattributed_block_count"], 3)
        self.assertFalse(reconciliation["destructive_merge_allowed"])

    def test_explicit_stage_attribution_can_measure_overlap_without_merging(self):
        blocks = [
            {"text": "same", "extraction_stage": "native"},
            {"text": "same", "extraction_stage": "ocr"},
            {"text": "ocr-only", "extraction_stage": "ocr"},
        ]
        dimensions = SCORE.measure_b01_defective_native_dimensions(
            {"status": "success", "warnings": [], "blocks": blocks}, self.gold
        )
        reconciliation = dimensions["native_ocr_reconciliation"]
        self.assertEqual(reconciliation["status"], "measured")
        self.assertEqual(reconciliation["exact_text_overlap_count"], 1)
        self.assertEqual(reconciliation["exact_text_overlap"], ["same"])
        self.assertFalse(reconciliation["destructive_merge_allowed"])


if __name__ == "__main__":
    unittest.main()
