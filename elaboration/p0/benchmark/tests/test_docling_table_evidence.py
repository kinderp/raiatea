from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
sys.path.insert(0, str(ROUTES))
SPEC = importlib.util.spec_from_file_location(
    "p0_docling_table_evidence", ROUTES / "docling_table_evidence.py"
)
DOCLING = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(DOCLING)


def _cell(row: int, column: int, text: str, header: bool = False) -> dict:
    return {
        "start_row_offset_idx": row,
        "end_row_offset_idx": row + 1,
        "start_col_offset_idx": column,
        "end_col_offset_idx": column + 1,
        "text": text,
        "column_header": header,
        "row_header": False,
        "row_section": False,
    }


class DoclingTableEvidenceTests(unittest.TestCase):
    def test_explicit_table_topology_and_roles_are_preserved(self):
        document = {
            "pages": {
                "1": {"page_no": 1, "size": {"width": 612.0, "height": 792.0}}
            },
            "tables": [
                {
                    "self_ref": "#/tables/0",
                    "label": "table",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {
                                "l": 72.0,
                                "t": 600.0,
                                "r": 540.0,
                                "b": 440.0,
                                "coord_origin": "BOTTOMLEFT",
                            },
                        }
                    ],
                    "data": {
                        "num_rows": 2,
                        "num_cols": 2,
                        "table_cells": [
                            _cell(0, 0, "Item", True),
                            _cell(0, 1, "Qty", True),
                            _cell(1, 0, "Alpha"),
                            _cell(1, 1, "2"),
                        ],
                    },
                }
            ],
        }
        evidence = DOCLING.map_docling_table_evidence(document)
        self.assertEqual(evidence["status"], "success")
        self.assertEqual(len(evidence["tables"]), 1)
        table = evidence["tables"][0]
        self.assertEqual(table["provider_ref"], "#/tables/0")
        self.assertEqual(table["page_index"], 0)
        self.assertEqual(table["bbox_points_bottom_left"], [72.0, 440.0, 540.0, 600.0])
        self.assertEqual(table["row_count"], 2)
        self.assertEqual(table["column_count"], 2)
        self.assertTrue(table["topology_complete"])
        self.assertEqual(
            [(cell["row"], cell["column"], cell["text"], cell["role"]) for cell in table["cells"]],
            [
                (0, 0, "Item", "header"),
                (0, 1, "Qty", "header"),
                (1, 0, "Alpha", "body"),
                (1, 1, "2", "body"),
            ],
        )

    def test_missing_table_collection_is_degraded_not_zero(self):
        evidence = DOCLING.map_docling_table_evidence({"pages": {}})
        self.assertEqual(evidence["status"], "degraded")
        self.assertIsNone(evidence["tables"])
        self.assertTrue(
            any(
                warning["code"] == "docling-table-collection-unavailable"
                for warning in evidence["warnings"]
            )
        )

    def test_explicit_empty_table_collection_is_known_zero(self):
        evidence = DOCLING.map_docling_table_evidence(
            {"pages": {}, "tables": []}
        )
        self.assertEqual(evidence["status"], "success")
        self.assertEqual(evidence["tables"], [])

    def test_malformed_table_item_makes_collection_identity_unknown(self):
        evidence = DOCLING.map_docling_table_evidence(
            {"pages": {}, "tables": [{"self_ref": "#/tables/0"}, 42]}
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertIsNone(evidence["tables"])
        self.assertTrue(
            any(
                warning["code"] == "docling-table-item-invalid"
                for warning in evidence["warnings"]
            )
        )

    def test_missing_table_data_preserves_presence_but_not_topology(self):
        evidence = DOCLING.map_docling_table_evidence(
            {"pages": {}, "tables": [{"self_ref": "#/tables/0", "label": "table"}]}
        )
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(len(evidence["tables"]), 1)
        table = evidence["tables"][0]
        self.assertIsNone(table["cells"])
        self.assertFalse(table["topology_complete"])

    def test_malformed_cell_keeps_table_but_marks_topology_incomplete(self):
        document = {
            "pages": {},
            "tables": [
                {
                    "self_ref": "#/tables/0",
                    "data": {
                        "num_rows": 1,
                        "num_cols": 2,
                        "table_cells": [_cell(0, 0, "Item", True), "bad-cell"],
                    },
                }
            ],
        }
        evidence = DOCLING.map_docling_table_evidence(document)
        self.assertEqual(evidence["status"], "degraded")
        self.assertEqual(len(evidence["tables"]), 1)
        self.assertEqual(len(evidence["tables"][0]["cells"]), 1)
        self.assertFalse(evidence["tables"][0]["topology_complete"])

    def test_spans_are_preserved_and_prevent_simple_grid_complete_claim(self):
        merged = _cell(0, 0, "Merged", True)
        merged["end_col_offset_idx"] = 2
        evidence = DOCLING.map_docling_table_evidence(
            {
                "pages": {},
                "tables": [
                    {
                        "self_ref": "#/tables/0",
                        "data": {
                            "num_rows": 1,
                            "num_cols": 2,
                            "table_cells": [merged],
                        },
                    }
                ],
            }
        )
        table = evidence["tables"][0]
        self.assertEqual(table["cells"][0]["column_span"], 2)
        self.assertFalse(table["topology_complete"])


if __name__ == "__main__":
    unittest.main()
