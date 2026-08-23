from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_score_b01_table", ROUTES / "score_b01_table.py"
)
SCORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORE)


class B01TableScoringTests(unittest.TestCase):
    def setUp(self):
        gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )
        self.gold = gold["fixtures"]["B01-PDF-005"]
        self.blocks = [
            {"text": "Raiatea B01 PDF 005", "page_index": 0},
            {"text": "Body text before the benchmark table.", "page_index": 0},
            {"text": "Item Qty Price", "page_index": 0},
            {"text": "Alpha 2 3.50", "page_index": 0},
            {"text": "Beta 1 7.00", "page_index": 0},
            {"text": "Total 3 14.00", "page_index": 0},
            {"text": "Body text after the benchmark table.", "page_index": 0},
        ]

    def _explicit_table(self) -> dict:
        cells = []
        for gold_cell in self.gold["tables"][0]["cells"]:
            cells.append(
                {
                    "provider_ref": f"provider-{gold_cell['id']}",
                    "row": gold_cell["row"],
                    "column": gold_cell["column"],
                    "row_span": 1,
                    "column_span": 1,
                    "text": gold_cell["text"],
                    "role": gold_cell["role"],
                    "bbox_points_bottom_left": list(gold_cell["region"]),
                }
            )
        return {
            "provider_ref": "#/tables/0",
            "page_index": 0,
            "bbox_points_bottom_left": [72.0, 440.0, 540.0, 600.0],
            "row_count": 4,
            "column_count": 3,
            "cells": cells,
            "topology_complete": True,
        }

    def test_page_text_can_measure_cell_content_without_claiming_table_structure(self):
        dimensions = SCORE.measure_b01_table_dimensions(
            {"blocks": self.blocks}, self.gold
        )
        content = dimensions["cell_text_content"]
        self.assertEqual(content["status"], "measured")
        self.assertEqual(content["expected_count"], 12)
        self.assertEqual(content["exact_once_count"], 12)
        self.assertEqual(content["binding"], "page-text-presence-only")
        self.assertEqual(dimensions["table_presence"]["status"], "not-measured")
        self.assertEqual(dimensions["table_topology"]["status"], "not-measured")
        self.assertEqual(dimensions["explicit_cell_text"]["status"], "not-measured")
        self.assertEqual(dimensions["header_roles"]["status"], "not-measured")

    def test_one_explicit_table_can_measure_topology_text_roles_and_geometry(self):
        dimensions = SCORE.measure_b01_table_dimensions(
            {"blocks": self.blocks, "tables": [self._explicit_table()]}, self.gold
        )
        self.assertTrue(dimensions["table_presence"]["count_exact"])
        self.assertTrue(dimensions["table_topology"]["topology_exact"])
        self.assertEqual(dimensions["explicit_cell_text"]["exact_count"], 12)
        self.assertEqual(dimensions["header_roles"]["status"], "measured")
        self.assertEqual(dimensions["header_roles"]["exact_count"], 12)
        self.assertEqual(dimensions["table_geometry"]["status"], "measured")
        self.assertTrue(dimensions["table_geometry"]["bbox_exact"])
        self.assertEqual(dimensions["table_geometry"]["max_absolute_edge_error_points"], 0.0)
        self.assertEqual(dimensions["cell_geometry"]["status"], "measured")
        self.assertEqual(dimensions["cell_geometry"]["bbox_exact_count"], 12)

    def test_extra_table_keeps_count_measured_but_identity_dependent_dimensions_unmeasured(self):
        dimensions = SCORE.measure_b01_table_dimensions(
            {
                "blocks": self.blocks,
                "tables": [self._explicit_table(), {"provider_ref": "#/tables/extra"}],
            },
            self.gold,
        )
        self.assertEqual(dimensions["table_presence"]["status"], "measured")
        self.assertEqual(dimensions["table_presence"]["observed_count"], 2)
        self.assertFalse(dimensions["table_presence"]["count_exact"])
        self.assertEqual(dimensions["table_topology"]["status"], "not-measured")
        self.assertEqual(dimensions["explicit_cell_text"]["status"], "not-measured")
        self.assertEqual(dimensions["table_geometry"]["status"], "not-measured")
        self.assertIn("list-position", dimensions["table_topology"]["reason"])

    def test_incomplete_explicit_table_does_not_trigger_spatial_reconstruction(self):
        table = self._explicit_table()
        table["topology_complete"] = False
        table["cells"] = table["cells"][:-1]
        dimensions = SCORE.measure_b01_table_dimensions(
            {"blocks": self.blocks, "tables": [table]}, self.gold
        )
        self.assertEqual(dimensions["table_presence"]["status"], "measured")
        self.assertEqual(dimensions["table_topology"]["status"], "not-measured")
        self.assertEqual(dimensions["explicit_cell_text"]["status"], "not-measured")
        self.assertIn("spatial reconstruction", dimensions["table_topology"]["reason"])

    def test_wrong_explicit_topology_is_measured_as_mismatch_without_repair(self):
        table = self._explicit_table()
        table["row_count"] = 3
        table["topology_complete"] = True
        dimensions = SCORE.measure_b01_table_dimensions(
            {"blocks": self.blocks, "tables": [table]}, self.gold
        )
        topology = dimensions["table_topology"]
        self.assertEqual(topology["status"], "measured")
        self.assertFalse(topology["topology_exact"])
        self.assertEqual(topology["observed_rows"], 3)
        self.assertEqual(dimensions["explicit_cell_text"]["status"], "not-measured")

    def test_duplicate_provider_cell_coordinate_prevents_cell_binding(self):
        table = self._explicit_table()
        table["cells"][1]["row"] = 0
        table["cells"][1]["column"] = 0
        dimensions = SCORE.measure_b01_table_dimensions(
            {"blocks": self.blocks, "tables": [table]}, self.gold
        )
        topology = dimensions["table_topology"]
        self.assertTrue(topology["duplicate_or_invalid_coordinates"])
        self.assertFalse(topology["topology_exact"])
        self.assertEqual(dimensions["explicit_cell_text"]["status"], "not-measured")

    def test_missing_explicit_roles_are_not_inferred_from_first_row(self):
        table = self._explicit_table()
        for cell in table["cells"]:
            cell["role"] = None
        dimensions = SCORE.measure_b01_table_dimensions(
            {"blocks": self.blocks, "tables": [table]}, self.gold
        )
        roles = dimensions["header_roles"]
        self.assertEqual(roles["status"], "not-measured")
        self.assertEqual(roles["evidence_count"], 0)
        self.assertEqual(roles["exact_count"], 0)

    def test_cell_geometry_reports_raw_error_without_tolerance(self):
        table = self._explicit_table()
        table["cells"][0]["bbox_points_bottom_left"] = [71.5, 560.0, 300.5, 600.25]
        dimensions = SCORE.measure_b01_table_dimensions(
            {"blocks": self.blocks, "tables": [table]}, self.gold
        )
        geometry = dimensions["cell_geometry"]
        self.assertEqual(geometry["status"], "measured")
        self.assertEqual(geometry["bbox_exact_count"], 11)
        self.assertEqual(geometry["max_observed_edge_error_points"], 0.5)
        self.assertIn("no post-hoc geometry tolerance", geometry["policy"])


if __name__ == "__main__":
    unittest.main()
