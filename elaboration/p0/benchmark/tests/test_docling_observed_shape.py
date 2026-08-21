from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


DOCLING = _load("p0_docling_observed_mapper", ROUTES_DIR / "docling_routes.py")
SCORE = _load("p0_docling_observed_score", ROUTES_DIR / "score_b01.py")


def _bbox(left, top, right, bottom):
    return {
        "page_no": 1,
        "bbox": {
            "l": left,
            "t": top,
            "r": right,
            "b": bottom,
            "coord_origin": "BOTTOMLEFT",
        },
        "charspan": [0, 1],
    }


def _observed_two_column_shape():
    return {
        "pages": {"1": {"size": {"width": 612.0, "height": 792.0}, "page_no": 1}},
        "body": {
            "self_ref": "#/body",
            "children": [{"$ref": "#/texts/0"}, {"$ref": "#/texts/1"}],
            "label": "unspecified",
        },
        "texts": [
            {
                "self_ref": "#/texts/0",
                "parent": {"$ref": "#/body"},
                "children": [],
                "label": "section_header",
                "level": 1,
                "text": "Raiatea B01 PDF 002",
                "prov": [_bbox(72.0, 732.924, 247.086, 716.274)],
            },
            {
                "self_ref": "#/texts/1",
                "parent": {"$ref": "#/body"},
                "children": [],
                "label": "text",
                "text": "Left one. Left two. Right one. Right two.",
                "prov": [_bbox(72.0, 673.616, 384.696, 622.516)],
            },
        ],
        "groups": [],
    }


def _gold_two_column():
    return {
        "reference_units": [
            {"id": "title", "type": "heading", "text": "Raiatea B01 PDF 002", "page_index": 0, "region": [72, 700, 360, 735]},
            {"id": "l1", "type": "paragraph", "text": "Left one.", "page_index": 0, "region": [72, 650, 250, 680]},
            {"id": "l2", "type": "paragraph", "text": "Left two.", "page_index": 0, "region": [72, 610, 250, 640]},
            {"id": "r1", "type": "paragraph", "text": "Right one.", "page_index": 0, "region": [330, 650, 520, 680]},
            {"id": "r2", "type": "paragraph", "text": "Right two.", "page_index": 0, "region": [330, 610, 520, 640]},
        ],
        "reading_order": [["title", "l1"], ["l1", "l2"], ["l2", "r1"], ["r1", "r2"]],
    }


class ObservedDoclingShapeTests(unittest.TestCase):
    def test_empty_children_on_text_items_are_leaves_not_groups(self):
        observation = DOCLING.map_docling_document(_observed_two_column_shape())
        self.assertEqual(
            [block["text"] for block in observation["blocks"]],
            ["Raiatea B01 PDF 002", "Left one. Left two. Right one. Right two."],
        )
        self.assertEqual(observation["body_order_source"], "body.children")

    def test_section_header_uses_explicit_docling_level(self):
        observation = DOCLING.map_docling_document(_observed_two_column_shape())
        title = observation["blocks"][0]
        self.assertEqual(title["semantic_type"], "heading")
        self.assertEqual(title["semantic_level"], 1)
        self.assertEqual(title["bbox_points_bottom_left"], [72.0, 716.274, 247.086, 732.924])

    def test_aggregate_text_block_preserves_content_and_reading_order_without_fake_unit_geometry(self):
        observation = DOCLING.map_docling_document(_observed_two_column_shape())
        result = SCORE.measure_b01_fixture(
            "B01-PDF-002", observation, _gold_two_column()
        )

        content = result["dimensions"]["content_text"]
        self.assertEqual(content["matched_units"], 5)
        self.assertEqual(content["exact_block_units"], 1)
        states = {row["reference_unit"]: row["match_state"] for row in content["units"]}
        self.assertEqual(states["title"], "exact-block")
        for unit_id in ["l1", "l2", "r1", "r2"]:
            self.assertEqual(states[unit_id], "substring-in-provider-block")

        order = result["dimensions"]["reading_order"]
        self.assertEqual(order["satisfied_edges"], 4)
        self.assertEqual(order["expected_edges"], 4)
        self.assertEqual(order["observed_reference_unit_order"], ["title", "l1", "l2", "r1", "r2"])

        coords = result["dimensions"]["source_coordinates"]
        self.assertEqual(coords["status"], "partial")
        self.assertEqual(coords["geometry_evidence_count"], 1)
        self.assertEqual(coords["provider_geometry_observed_count"], 5)
        self.assertEqual(coords["contained_count"], 1)
        for row in coords["units"]:
            if row["reference_unit"] == "title":
                self.assertTrue(row["unit_geometry_attributable"])
            else:
                self.assertFalse(row["unit_geometry_attributable"])
                self.assertIsNone(row["bbox_inside_gold_region"])

        hierarchy = result["dimensions"]["hierarchy"]
        self.assertEqual(hierarchy["status"], "measured")
        self.assertEqual(hierarchy["type_exact_count"], 5)
        self.assertEqual(hierarchy["segmentation_exact_count"], 1)


if __name__ == "__main__":
    unittest.main()
