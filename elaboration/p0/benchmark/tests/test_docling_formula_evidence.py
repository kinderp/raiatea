from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
sys.path.insert(0, str(ROUTES))
SPEC = importlib.util.spec_from_file_location(
    "p0_docling_formula_evidence", ROUTES / "docling_formula_evidence.py"
)
DOCLING = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DOCLING)


class DoclingFormulaEvidenceTests(unittest.TestCase):
    def test_picture_children_are_preserved_without_formula_semantics(self):
        document = {
            "pages": {"1": {"page_no": 1, "size": {"width": 612.0, "height": 792.0}}},
            "texts": [
                {
                    "label": "text",
                    "text": "E = mc",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {
                                "l": 108.0,
                                "t": 621.488,
                                "r": 164.0,
                                "b": 606.688,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        }
                    ],
                },
                {
                    "label": "text",
                    "text": "2",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {
                                "l": 166.0,
                                "t": 628.462,
                                "r": 171.004,
                                "b": 620.137,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        }
                    ],
                },
            ],
            "pictures": [
                {
                    "label": "picture",
                    "children": [{"$ref": "#/texts/0"}, {"$ref": "#/texts/1"}],
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {
                                "l": 108.1,
                                "t": 630.3,
                                "r": 170.5,
                                "b": 608.3,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        }
                    ],
                }
            ],
            "groups": [],
        }
        evidence = DOCLING.map_docling_formula_evidence(document)
        self.assertEqual(evidence["status"], "success")
        self.assertEqual(evidence["formula_text_collection_state"], "measured")
        self.assertEqual(evidence["provider_group_collection_state"], "measured")
        self.assertEqual(evidence["math_relation_collection_state"], "not-measured")
        self.assertEqual(len(evidence["formula_text_blocks"]), 2)
        self.assertEqual(len(evidence["provider_formula_groups"]), 1)
        group = evidence["provider_formula_groups"][0]
        self.assertEqual(group["provider_label"], "picture")
        self.assertFalse(group["mathematical_semantics"])
        self.assertEqual([item["text"] for item in group["children"]], ["E = mc", "2"])
        self.assertFalse(evidence["formula_enrichment_enabled"])
        self.assertIsNone(evidence["math_relations"])

    def test_missing_picture_collection_is_not_measured_not_empty_success(self):
        evidence = DOCLING.map_docling_formula_evidence(
            {"texts": [], "pages": {}}
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(evidence["provider_formula_groups"], [])
        self.assertEqual(evidence["provider_group_collection_state"], "not-measured")
        self.assertTrue(
            any(
                warning["code"] == "docling-formula-groups-unavailable"
                for warning in evidence["warnings"]
            )
        )

    def test_valid_empty_picture_collection_is_measured_empty(self):
        evidence = DOCLING.map_docling_formula_evidence(
            {"texts": [], "pictures": [], "pages": {}}
        )
        self.assertEqual(evidence["status"], "success")
        self.assertEqual(evidence["formula_text_collection_state"], "measured")
        self.assertEqual(evidence["provider_group_collection_state"], "measured")
        self.assertEqual(evidence["provider_formula_groups"], [])

    def test_missing_text_collection_is_not_measured_not_zero(self):
        evidence = DOCLING.map_docling_formula_evidence(
            {"pictures": [], "pages": {}}
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(evidence["formula_text_blocks"], [])
        self.assertEqual(evidence["formula_text_collection_state"], "not-measured")
        self.assertTrue(
            any(
                warning["code"] == "docling-formula-texts-unavailable"
                for warning in evidence["warnings"]
            )
        )

    def test_malformed_text_item_makes_collection_partial(self):
        evidence = DOCLING.map_docling_formula_evidence(
            {
                "texts": [{"text": "E = mc"}, "bad-item"],
                "pictures": [],
                "pages": {},
            }
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(evidence["formula_text_collection_state"], "partial")
        self.assertEqual(len(evidence["formula_text_blocks"]), 1)
        self.assertTrue(
            any(
                warning["code"] == "docling-formula-text-invalid-item"
                for warning in evidence["warnings"]
            )
        )

    def test_unresolved_picture_child_marks_group_collection_partial(self):
        evidence = DOCLING.map_docling_formula_evidence(
            {
                "texts": [],
                "pages": {},
                "pictures": [
                    {"label": "picture", "children": [{"$ref": "#/texts/99"}]}
                ],
            }
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(evidence["provider_group_collection_state"], "partial")
        self.assertTrue(
            any(
                warning["code"] == "docling-formula-group-unresolved-child"
                for warning in evidence["warnings"]
            )
        )
        self.assertFalse(
            evidence["provider_formula_groups"][0]["mathematical_semantics"]
        )

    def test_invalid_picture_collection_shape_is_not_measured(self):
        evidence = DOCLING.map_docling_formula_evidence(
            {"texts": [], "pictures": {"not": "a-list"}, "pages": {}}
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(evidence["provider_group_collection_state"], "not-measured")
        self.assertTrue(
            any(
                warning["code"] == "docling-formula-groups-invalid"
                for warning in evidence["warnings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
