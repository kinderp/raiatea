from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location("p0_score_b01_structured", ROUTES_DIR / "score_b01.py")
SCORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORE)


def _gold():
    return {
        "reference_units": [
            {"id": "title", "type": "heading", "text": "Title", "page_index": 0, "region": [10, 700, 200, 740]},
            {"id": "p1", "type": "paragraph", "text": "First paragraph.", "page_index": 0, "region": [10, 650, 300, 690]},
            {"id": "p2", "type": "paragraph", "text": "Second paragraph.", "page_index": 0, "region": [10, 600, 300, 640]},
        ],
        "reading_order": [["title", "p1"], ["p1", "p2"]],
    }


class StructuredB01ScoringTests(unittest.TestCase):
    def test_missing_geometry_is_not_measured_not_zero(self):
        observation = {
            "route": "tika-test",
            "status": "success",
            "blocks": [
                {"text": "Title", "semantic_type": "heading", "page_index": None, "bbox_points_bottom_left": None},
                {"text": "First paragraph.", "semantic_type": "paragraph", "page_index": None, "bbox_points_bottom_left": None},
                {"text": "Second paragraph.", "semantic_type": "paragraph", "page_index": None, "bbox_points_bottom_left": None},
            ],
        }
        result = SCORE.measure_b01_fixture("fixture", observation, _gold())
        coordinates = result["dimensions"]["source_coordinates"]
        self.assertEqual(coordinates["status"], "not-measured")
        self.assertEqual(coordinates["geometry_evidence_count"], 0)
        self.assertNotIn("contained_count", coordinates)
        self.assertEqual(result["dimensions"]["content_text"]["matched_units"], 3)

    def test_explicit_semantic_types_measure_hierarchy(self):
        observation = {
            "route": "tika-test",
            "status": "success",
            "blocks": [
                {"text": "Title", "semantic_type": "heading", "semantic_level": 1},
                {"text": "First paragraph.", "semantic_type": "paragraph"},
                {"text": "Second paragraph.", "semantic_type": "paragraph"},
            ],
        }
        result = SCORE.measure_b01_fixture("fixture", observation, _gold())
        hierarchy = result["dimensions"]["hierarchy"]
        self.assertEqual(hierarchy["status"], "measured")
        self.assertEqual(hierarchy["semantic_evidence_count"], 3)
        self.assertEqual(hierarchy["type_exact_count"], 3)

    def test_semantic_mismatch_is_measured_not_hidden(self):
        observation = {
            "route": "tika-test",
            "status": "success",
            "blocks": [
                {"text": "Title", "semantic_type": "paragraph"},
                {"text": "First paragraph.", "semantic_type": "paragraph"},
                {"text": "Second paragraph.", "semantic_type": "paragraph"},
            ],
        }
        result = SCORE.measure_b01_fixture("fixture", observation, _gold())
        hierarchy = result["dimensions"]["hierarchy"]
        self.assertEqual(hierarchy["status"], "measured")
        self.assertEqual(hierarchy["type_exact_count"], 2)
        title = next(row for row in hierarchy["units"] if row["reference_unit"] == "title")
        self.assertFalse(title["type_exact"])
        self.assertEqual(title["observed_type"], "paragraph")

    def test_partial_semantic_evidence_stays_partial(self):
        observation = {
            "route": "mixed-test",
            "status": "success",
            "blocks": [
                {"text": "Title", "semantic_type": "heading"},
                {"text": "First paragraph.", "semantic_type": None},
                {"text": "Second paragraph.", "semantic_type": None},
            ],
        }
        result = SCORE.measure_b01_fixture("fixture", observation, _gold())
        hierarchy = result["dimensions"]["hierarchy"]
        self.assertEqual(hierarchy["status"], "partial")
        self.assertEqual(hierarchy["semantic_evidence_count"], 1)
        self.assertEqual(hierarchy["type_exact_count"], 1)

    def test_poppler_like_blocks_still_leave_hierarchy_unmeasured(self):
        observation = {
            "route": "poppler-control",
            "status": "success",
            "blocks": [
                {"text": "Title", "bbox_points_bottom_left": [10, 710, 100, 730], "page_index": 0},
                {"text": "First paragraph.", "bbox_points_bottom_left": [10, 660, 200, 680], "page_index": 0},
                {"text": "Second paragraph.", "bbox_points_bottom_left": [10, 610, 200, 630], "page_index": 0},
            ],
        }
        result = SCORE.measure_b01_fixture("fixture", observation, _gold())
        self.assertEqual(result["dimensions"]["hierarchy"]["status"], "not-measured")
        self.assertEqual(result["dimensions"]["source_coordinates"]["status"], "measured")
        self.assertEqual(result["dimensions"]["source_coordinates"]["contained_count"], 3)

    def test_partial_geometry_stays_partial(self):
        observation = {
            "route": "mixed-geometry",
            "status": "success",
            "blocks": [
                {"text": "Title", "page_index": 0, "bbox_points_bottom_left": [10, 710, 100, 730]},
                {"text": "First paragraph.", "page_index": None, "bbox_points_bottom_left": None},
                {"text": "Second paragraph.", "page_index": None, "bbox_points_bottom_left": None},
            ],
        }
        result = SCORE.measure_b01_fixture("fixture", observation, _gold())
        coordinates = result["dimensions"]["source_coordinates"]
        self.assertEqual(coordinates["status"], "partial")
        self.assertEqual(coordinates["geometry_evidence_count"], 1)
        self.assertEqual(coordinates["contained_count"], 1)


if __name__ == "__main__":
    unittest.main()
