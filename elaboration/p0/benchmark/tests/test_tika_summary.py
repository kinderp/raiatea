from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_measure_tika_b01_summary", ROUTES_DIR / "measure_tika_b01.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _result(fixture_id: str, expected_units: int, expected_edges: int, heading_levels: int = 0):
    return {
        "fixture_id": fixture_id,
        "route_status": "success",
        "dimensions": {
            "content_text": {
                "status": "measured",
                "matched_units": expected_units,
                "exact_block_units": expected_units,
                "expected_units": expected_units,
            },
            "reading_order": {
                "status": "measured",
                "satisfied_edges": expected_edges,
                "expected_edges": expected_edges,
            },
            "source_coordinates": {"status": "not-measured"},
            "hierarchy": {
                "status": "measured",
                "type_exact_count": expected_units - 1,
                "expected_count": expected_units,
                "heading_levels": {
                    "status": "not-measured" if heading_levels else "not-applicable",
                    "exact_count": 0,
                    "expected_count": heading_levels,
                },
            },
            "links": {
                "status": "not-measured" if fixture_id == "B01-PDF-003" else "not-applicable",
                "target_exact_count": 0,
                "expected_count": 1 if fixture_id == "B01-PDF-003" else 0,
            },
        },
        "page_structure_observed": True,
        "bbox_structure_observed": False,
        "metadata_key_count": 20,
        "controlled_runtime_files": ["pdfbox-font-cache/.pdfbox.cache"],
        "side_effect_files": [],
        "raw_output_sha256": "a" * 64,
    }


class TikaSummaryTests(unittest.TestCase):
    def test_summary_retains_runtime_confinement_and_semantic_limits(self):
        report = {
            "environment": {
                "platform_system": "Linux",
                "platform_release": "test",
                "machine": "x86_64",
                "python_version": "3.12.14",
            },
            "route": {
                "tika_version": "3.3.2",
                "jar": {"sha256": "b" * 64, "verified": True},
                "java": {
                    "version_line": 'openjdk version "21.0.12"',
                    "executable_sha256": "c" * 64,
                },
                "ocr_policy": "explicit-no-ocr",
                "config_sha256": "d" * 64,
            },
            "results": [
                _result("B01-PDF-001", 3, 2),
                _result("B01-PDF-002", 5, 4),
                _result("B01-PDF-003", 8, 7, heading_levels=3),
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            MODULE._write_summary(report, path)
            text = path.read_text(encoding="utf-8")

        self.assertIn("pdfbox-font-cache/.pdfbox.cache", text)
        self.assertIn("Unexpected files observed under the controlled parent: `0`", text)
        self.assertIn("page structure observed: `True`", text)
        self.assertIn("bbox structure observed: `False`", text)
        self.assertIn("B01-PDF-003", text)
        self.assertIn("heading levels: `not-measured`", text)
        self.assertIn("links: `not-measured`", text)
        self.assertIn("visual/font cues are not promoted to semantic structure", text)
        self.assertIn('openjdk version "21.0.12"', text)
        self.assertIn("Java executable SHA-256", text)


if __name__ == "__main__":
    unittest.main()
