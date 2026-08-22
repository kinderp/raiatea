from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_measure_docling_b01_summary", ROUTES_DIR / "measure_docling_b01.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _result(fixture_id: str, matched: int, exact_blocks: int, edges: int, geometry: int, hierarchy_exact: int, hierarchy_segmentation: int):
    return {
        "fixture_id": fixture_id,
        "route_status": "success",
        "provider_conversion_status": "ConversionStatus.SUCCESS",
        "dimensions": {
            "content_text": {
                "status": "measured",
                "matched_units": matched,
                "exact_block_units": exact_blocks,
                "expected_units": matched,
            },
            "reading_order": {
                "status": "measured",
                "satisfied_edges": edges,
                "expected_edges": edges,
            },
            "source_coordinates": {
                "status": "measured" if geometry == matched else "partial",
                "geometry_evidence_count": geometry,
                "contained_count": geometry,
                "expected_count": matched,
            },
            "hierarchy": {
                "status": "measured",
                "type_exact_count": hierarchy_exact,
                "segmentation_exact_count": hierarchy_segmentation,
                "expected_count": matched,
            },
        },
        "page_structure_observed": True,
        "bbox_structure_observed": True,
        "body_order_source": "body.children",
        "raw_output_sha256": "a" * 64,
        "cache_delta_file_count": 0,
    }


class DoclingSummaryTests(unittest.TestCase):
    def test_summary_separates_content_segmentation_and_stable_model_payload(self):
        report = {
            "environment": {
                "platform_system": "Linux",
                "platform_release": "test",
                "machine": "x86_64",
                "python_version": "3.12.14",
            },
            "package_environment": {
                "docling_version": "2.118.0",
                "freeze_sha256": "b" * 64,
            },
            "reference_locks": {
                "expected_environment_freeze_sha256": "b" * 64,
            },
            "model_payload": {
                "file_count": 11,
                "bytes": 342987978,
                "payload_manifest_sha256": "c" * 64,
            },
            "model_artifacts": {
                "file_count": 39,
                "manifest_sha256": "d" * 64,
            },
            "results": [
                _result("B01-PDF-001", 3, 3, 2, 3, 3, 3),
                _result("B01-PDF-002", 5, 1, 4, 1, 5, 1),
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            MODULE._write_summary(report, path)
            text = path.read_text(encoding="utf-8")

        self.assertIn("reference text content preserved: `5/5`", text)
        self.assertIn("segmentation-exact Provider blocks: `1/5`", text)
        self.assertIn("unit-attributable geometry `1/5`", text)
        self.assertIn("segmentation-exact semantic units `1/5`", text)
        self.assertIn("stable model payload manifest SHA-256", text)
        self.assertIn("cache-inclusive download-tree", text)
        self.assertIn("Content preservation and Provider segmentation fidelity are separate dimensions", text)
        self.assertIn("No weighted/universal score is produced", text)


if __name__ == "__main__":
    unittest.main()
