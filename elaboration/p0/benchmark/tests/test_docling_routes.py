from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


DOCLING = _load("p0_docling_routes", ROUTES_DIR / "docling_routes.py")
SCORE = _load("p0_score_b01_for_docling", ROUTES_DIR / "score_b01.py")


def _prov(page_no: int, bbox: dict):
    return [{"page_no": page_no, "bbox": bbox, "charspan": [0, 1]}]


def _doc() -> dict:
    return {
        "schema_name": "DoclingDocument",
        "version": "test",
        "pages": {
            "1": {"page_no": 1, "size": {"width": 612.0, "height": 792.0}},
            "2": {"page_no": 2, "size": {"width": 595.0, "height": 842.0}},
        },
        "texts": [
            {
                "label": "title",
                "text": "Title",
                "prov": _prov(
                    1,
                    {"l": 72, "t": 735, "r": 200, "b": 700, "coord_origin": "BOTTOMLEFT"},
                ),
            },
            {
                "label": "text",
                "text": "Left one.",
                "prov": _prov(
                    1,
                    {"l": 72, "t": 118, "r": 150, "b": 130, "coord_origin": "TOPLEFT"},
                ),
            },
            {
                "label": "text",
                "text": "Left two.",
                "prov": _prov(
                    1,
                    {"l": 72, "t": 158, "r": 150, "b": 170, "coord_origin": "TOPLEFT"},
                ),
            },
            {
                "label": "text",
                "text": "Second page.",
                "prov": _prov(
                    2,
                    {"l": 50, "t": 100, "r": 200, "b": 120, "coord_origin": "TOPLEFT"},
                ),
            },
        ],
        "groups": [
            {
                "label": "chapter",
                "children": [
                    {"$ref": "#/texts/1"},
                    {"$ref": "#/texts/2"},
                ],
            }
        ],
        "body": {
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/groups/0"},
                {"$ref": "#/texts/3"},
            ]
        },
    }


class DoclingMapperTests(unittest.TestCase):
    def test_body_and_group_refs_preserve_reading_order(self):
        observation = DOCLING.map_docling_document(_doc())
        self.assertEqual(observation["status"], "success")
        self.assertEqual(observation["body_order_source"], "body.children")
        self.assertEqual(
            [block["text"] for block in observation["blocks"]],
            ["Title", "Left one.", "Left two.", "Second page."],
        )
        self.assertFalse(
            any(warning["code"] == "docling-body-order-unavailable" for warning in observation["warnings"])
        )

    def test_label_mapping_is_conservative(self):
        document = _doc()
        document["texts"][1]["label"] = "section_header"
        document["texts"][2]["label"] = "list_item"
        document["texts"][3]["label"] = "mystery_future_label"
        observation = DOCLING.map_docling_document(document)
        blocks = {block["text"]: block for block in observation["blocks"]}
        self.assertEqual(blocks["Title"]["semantic_type"], "heading")
        self.assertEqual(blocks["Title"]["semantic_level"], 1)
        self.assertEqual(blocks["Left one."]["semantic_type"], "heading")
        self.assertIsNone(blocks["Left one."]["semantic_level"])
        self.assertEqual(blocks["Left two."]["semantic_type"], "list-item")
        self.assertIsNone(blocks["Second page."]["semantic_type"])
        warning = next(w for w in observation["warnings"] if w["code"] == "docling-unmapped-labels")
        self.assertEqual(warning["details"], ["mystery_future_label"])

    def test_bottomleft_bbox_maps_directly_and_page_number_is_zero_based(self):
        observation = DOCLING.map_docling_document(_doc())
        title = observation["blocks"][0]
        self.assertEqual(title["page_index"], 0)
        self.assertEqual(title["provider_bbox_origin"], "BOTTOMLEFT")
        self.assertEqual(title["bbox_points_bottom_left"], [72.0, 700.0, 200.0, 735.0])

    def test_topleft_bbox_uses_correct_page_height(self):
        observation = DOCLING.map_docling_document(_doc())
        left_one = observation["blocks"][1]
        second_page = observation["blocks"][3]
        self.assertEqual(left_one["bbox_points_bottom_left"], [72.0, 662.0, 150.0, 674.0])
        self.assertEqual(second_page["page_index"], 1)
        self.assertEqual(second_page["bbox_points_bottom_left"], [50.0, 722.0, 200.0, 742.0])

    def test_missing_page_size_for_topleft_bbox_is_visible_degradation(self):
        document = _doc()
        document["pages"].pop("2")
        observation = DOCLING.map_docling_document(document)
        second = next(block for block in observation["blocks"] if block["text"] == "Second page.")
        self.assertEqual(second["page_index"], 1)
        self.assertIsNone(second["bbox_points_bottom_left"])
        warnings = [w for w in observation["warnings"] if w["code"] == "docling-provenance-degraded"]
        self.assertTrue(any(w["details"]["reason"] == "missing-page-size-for-top-left-bbox" for w in warnings))

    def test_missing_provenance_is_not_fabricated(self):
        document = _doc()
        document["texts"][1].pop("prov")
        observation = DOCLING.map_docling_document(document)
        block = next(block for block in observation["blocks"] if block["text"] == "Left one.")
        self.assertIsNone(block["page_index"])
        self.assertIsNone(block["bbox_points_bottom_left"])
        self.assertEqual(block["provenance_count"], 0)

    def test_missing_body_uses_explicitly_warned_texts_fallback(self):
        document = _doc()
        document.pop("body")
        observation = DOCLING.map_docling_document(document)
        self.assertEqual(observation["body_order_source"], "texts-fallback")
        self.assertTrue(
            any(warning["code"] == "docling-body-order-unavailable" for warning in observation["warnings"])
        )

    def test_unresolved_and_cyclic_refs_are_visible(self):
        document = _doc()
        document["groups"][0]["children"].append({"$ref": "#/groups/0"})
        document["body"]["children"].append({"$ref": "#/texts/999"})
        observation = DOCLING.map_docling_document(document)
        codes = {warning["code"] for warning in observation["warnings"]}
        self.assertIn("docling-ref-cycle", codes)
        self.assertIn("docling-unresolved-ref", codes)


class DoclingScorerIntegrationTests(unittest.TestCase):
    def test_provider_neutral_scorer_accepts_docling_geometry_and_semantics(self):
        document = {
            "pages": {"1": {"page_no": 1, "size": {"width": 612, "height": 792}}},
            "texts": [
                {
                    "label": "title",
                    "text": "Raiatea B01 PDF 001",
                    "prov": _prov(1, {"l": 72, "t": 735, "r": 250, "b": 700, "coord_origin": "BOTTOMLEFT"}),
                },
                {
                    "label": "text",
                    "text": "Alpha paragraph preserves exact benchmark text.",
                    "prov": _prov(1, {"l": 72, "t": 680, "r": 400, "b": 650, "coord_origin": "BOTTOMLEFT"}),
                },
                {
                    "label": "text",
                    "text": "Beta paragraph follows alpha in reading order.",
                    "prov": _prov(1, {"l": 72, "t": 640, "r": 400, "b": 610, "coord_origin": "BOTTOMLEFT"}),
                },
            ],
            "body": {"children": [{"$ref": "#/texts/0"}, {"$ref": "#/texts/1"}, {"$ref": "#/texts/2"}]},
        }
        gold = {
            "reference_units": [
                {"id": "title", "type": "heading", "text": "Raiatea B01 PDF 001", "page_index": 0, "region": [72, 700, 360, 735]},
                {"id": "p1", "type": "paragraph", "text": "Alpha paragraph preserves exact benchmark text.", "page_index": 0, "region": [72, 650, 500, 680]},
                {"id": "p2", "type": "paragraph", "text": "Beta paragraph follows alpha in reading order.", "page_index": 0, "region": [72, 610, 500, 640]},
            ],
            "reading_order": [["title", "p1"], ["p1", "p2"]],
        }
        observation = DOCLING.map_docling_document(document)
        result = SCORE.measure_b01_fixture("B01-PDF-001", observation, gold)
        self.assertEqual(result["dimensions"]["content_text"]["matched_units"], 3)
        self.assertEqual(result["dimensions"]["reading_order"]["satisfied_edges"], 2)
        self.assertEqual(result["dimensions"]["source_coordinates"]["contained_count"], 3)
        self.assertEqual(result["dimensions"]["hierarchy"]["type_exact_count"], 3)


class DoclingArtifactTests(unittest.TestCase):
    def test_artifact_manifest_is_stable_and_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "z").mkdir()
            (root / "z" / "b.bin").write_bytes(b"b")
            (root / "a.bin").write_bytes(b"a")
            first = DOCLING.artifact_manifest(root)
            second = DOCLING.artifact_manifest(root)
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        self.assertEqual([item["path"] for item in first["files"]], ["a.bin", "z/b.bin"])
        self.assertEqual(first["file_count"], 2)

    def test_offline_environment_is_scoped_and_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = root / "artifacts"
            cache = root / "cache"
            artifacts.mkdir()
            old = os.environ.get("HF_HUB_OFFLINE")
            with DOCLING._offline_environment(artifacts, cache):
                self.assertEqual(os.environ["HF_HUB_OFFLINE"], "1")
                self.assertEqual(os.environ["TRANSFORMERS_OFFLINE"], "1")
                self.assertEqual(os.environ["DOCLING_DEVICE"], "cpu")
                self.assertEqual(Path(os.environ["DOCLING_ARTIFACTS_PATH"]), artifacts.resolve())
            self.assertEqual(os.environ.get("HF_HUB_OFFLINE"), old)


if __name__ == "__main__":
    unittest.main()
