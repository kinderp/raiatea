from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
sys.path.insert(0, str(ROUTES))
SPEC = importlib.util.spec_from_file_location(
    "p0_docling_figure_evidence", ROUTES / "docling_figure_evidence.py"
)
DOCLING = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DOCLING)


class DoclingFigureEvidenceTests(unittest.TestCase):
    def test_explicit_picture_caption_ref_is_preserved_without_pixel_claim(self):
        document = {
            "pages": {
                "1": {"page_no": 1, "size": {"width": 612.0, "height": 792.0}}
            },
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "label": "caption",
                    "text": "Figure 1. Deterministic Raiatea color grid.",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {
                                "l": 72.0,
                                "t": 478.616,
                                "r": 292.728,
                                "b": 467.516,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        }
                    ],
                }
            ],
            "pictures": [
                {
                    "self_ref": "#/pictures/0",
                    "label": "picture",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {
                                "l": 70.9052,
                                "t": 621.0238,
                                "r": 252.6001,
                                "b": 500.0570,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        }
                    ],
                    "captions": [{"$ref": "#/texts/0"}],
                }
            ],
        }
        evidence = DOCLING.map_docling_figure_evidence(document)
        self.assertEqual(evidence["status"], "success")
        self.assertEqual(len(evidence["figures"]), 1)
        self.assertEqual(evidence["figures"][0]["provider_ref"], "#/pictures/0")
        self.assertEqual(evidence["figures"][0]["page_index"], 0)
        self.assertEqual(
            evidence["figures"][0]["bbox_points_bottom_left"],
            [70.9052, 500.057, 252.6001, 621.0238],
        )
        self.assertEqual(len(evidence["caption_blocks"]), 1)
        self.assertEqual(evidence["caption_blocks"][0]["semantic_type"], "caption")
        self.assertEqual(len(evidence["figure_caption_relations"]), 1)
        relation = evidence["figure_caption_relations"][0]
        self.assertEqual(relation["provider_figure_ref"], "#/pictures/0")
        self.assertEqual(relation["provider_caption_ref"], "#/texts/0")
        self.assertEqual(
            relation["provider_relation_source"],
            "docling-picture.captions-explicit-ref",
        )
        self.assertFalse(evidence["asset_identity_available"])
        self.assertIsNone(evidence["figures"][0]["decoded_pixel_sha256"])

    def test_missing_picture_collection_is_degraded_not_zero_figures(self):
        evidence = DOCLING.map_docling_figure_evidence(
            {"pages": {}, "texts": []}
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertIsNone(evidence["figures"])
        self.assertTrue(
            any(
                warning["code"] == "docling-picture-collection-unavailable"
                for warning in evidence["warnings"]
            )
        )

    def test_invalid_picture_collection_is_degraded_not_zero_figures(self):
        evidence = DOCLING.map_docling_figure_evidence(
            {"pages": {}, "texts": [], "pictures": {"unexpected": "shape"}}
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertIsNone(evidence["figures"])

    def test_explicit_empty_picture_collection_is_known_zero(self):
        evidence = DOCLING.map_docling_figure_evidence(
            {"pages": {}, "texts": [], "pictures": []}
        )
        self.assertEqual(evidence["status"], "success")
        self.assertEqual(evidence["figures"], [])

    def test_unresolved_caption_ref_stays_visible(self):
        document = {
            "pages": {},
            "texts": [],
            "pictures": [
                {
                    "self_ref": "#/pictures/0",
                    "label": "picture",
                    "captions": [{"$ref": "#/texts/99"}],
                }
            ],
        }
        evidence = DOCLING.map_docling_figure_evidence(document)
        self.assertEqual(evidence["caption_blocks"], [])
        self.assertEqual(evidence["figure_caption_relations"], [])
        self.assertTrue(
            any(
                warning["code"] == "docling-picture-caption-ref-unresolved"
                for warning in evidence["warnings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
