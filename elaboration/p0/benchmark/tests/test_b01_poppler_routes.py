from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ROUTES = _load("p0_pdf_routes", ROUTES_DIR / "pdf_routes.py")
SCORE = _load("p0_score_b01", ROUTES_DIR / "score_b01.py")


BBOX_XHTML = b'''<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><body><doc>
<page width="612.000000" height="792.000000"><flow>
<block xMin="72" yMin="59.076" xMax="247.086" yMax="75.726"><line><word>Raiatea</word><word>B01</word><word>PDF</word><word>002</word></line></block>
<block xMin="72" yMin="118.384" xMax="118.704" yMax="129.484"><line><word>Left</word><word>one.</word></line></block>
<block xMin="330" yMin="118.384" xMax="384.696" yMax="129.484"><line><word>Right</word><word>one.</word></line></block>
<block xMin="72" yMin="158.384" xMax="117.360" yMax="169.484"><line><word>Left</word><word>two.</word></line></block>
<block xMin="330" yMin="158.384" xMax="383.352" yMax="169.484"><line><word>Right</word><word>two.</word></line></block>
</flow></page></doc></body></html>'''

PDF2XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<pdf2xml producer="poppler" version="25.06.0">
<page number="1" position="absolute" top="0" left="0" height="1188" width="918">
<text top="89" left="108" width="263" height="25">Raiatea B01 PDF 002</text>
<text top="178" left="108" width="70" height="17">Left one.</text>
<text top="238" left="108" width="68" height="17">Left two.</text>
<text top="178" left="495" width="82" height="17">Right one.</text>
<text top="238" left="495" width="80" height="17">Right two.</text>
</page></pdf2xml>'''


def _gold_b01_002():
    return {
        "reference_units": [
            {"id": "title", "type": "heading", "text": "Raiatea B01 PDF 002", "page_index": 0, "region": [72, 700, 360, 735]},
            {"id": "l1", "type": "paragraph", "text": "Left one.", "page_index": 0, "region": [72, 650, 250, 680]},
            {"id": "l2", "type": "paragraph", "text": "Left two.", "page_index": 0, "region": [72, 610, 250, 640]},
            {"id": "r1", "type": "paragraph", "text": "Right one.", "page_index": 0, "region": [330, 650, 520, 680]},
            {"id": "r2", "type": "paragraph", "text": "Right two.", "page_index": 0, "region": [330, 610, 520, 640]}
        ],
        "reading_order": [["title", "l1"], ["l1", "l2"], ["l2", "r1"], ["r1", "r2"]],
    }


def _controlled_output(filename: str, payload: bytes):
    temp = tempfile.TemporaryDirectory()
    work = Path(temp.name) / "work"
    work.mkdir()
    (work / filename).write_bytes(payload)
    metadata = {
        "returncode": 0,
        "stdout": "",
        "stderr": "",
        "duration_seconds": 0.001,
        "command_options": ["synthetic", str(work / filename)],
        "generated_files": [filename],
        "side_effect_files": [],
        "controlled_parent": True,
        "os_level_sandbox": False,
        "network_instrumentation": "not-measured",
        "_temporary_directory": temp,
    }
    return work, metadata


class PopplerMappingTests(unittest.TestCase):
    def test_top_left_point_conversion(self):
        bbox = ROUTES._convert_top_left_bbox(72, 118.384, 118.704, 129.484, 792)
        self.assertAlmostEqual(bbox[0], 72)
        self.assertAlmostEqual(bbox[1], 662.516)
        self.assertAlmostEqual(bbox[2], 118.704)
        self.assertAlmostEqual(bbox[3], 673.616)

    def test_pdftotext_bbox_mapping_preserves_observed_flow_order(self):
        work, metadata = _controlled_output("bbox.html", BBOX_XHTML)
        with mock.patch.object(ROUTES, "_controlled_run", return_value=(work, metadata)):
            observation = ROUTES.run_pdftotext_bbox_layout(Path("fixture.pdf"))
        self.assertEqual(observation["status"], "success")
        self.assertEqual(
            [block["text"] for block in observation["blocks"]],
            ["Raiatea B01 PDF 002", "Left one.", "Right one.", "Left two.", "Right two."],
        )
        left_one = observation["blocks"][1]
        self.assertAlmostEqual(left_one["bbox_points_bottom_left"][1], 662.516)
        self.assertEqual(observation["native_coordinate_system"], "top-left-points")

    def test_pdftohtml_mapping_uses_physical_page_size_for_scale(self):
        work, metadata = _controlled_output("out.xml", PDF2XML)
        # Simulate the copied input path carried in the command metadata.
        metadata["command_options"] = ["-xml", "-hidden", "-nodrm", "-q", str(work.parent / "input" / "fixture.pdf"), str(work / "out")]
        with mock.patch.object(ROUTES, "_controlled_run", return_value=(work, metadata)), mock.patch.object(
            ROUTES, "_pdfinfo_page_sizes", return_value={0: (612.0, 792.0)}
        ):
            observation = ROUTES.run_pdftohtml_xml(Path("fixture.pdf"))
        self.assertEqual(observation["status"], "success")
        page = observation["pages"][0]
        self.assertAlmostEqual(page["scale_to_points_x"], 2 / 3)
        self.assertAlmostEqual(page["scale_to_points_y"], 2 / 3)
        self.assertEqual(
            [block["text"] for block in observation["blocks"]],
            ["Raiatea B01 PDF 002", "Left one.", "Left two.", "Right one.", "Right two."],
        )
        self.assertAlmostEqual(observation["blocks"][1]["bbox_points_bottom_left"][0], 72.0)
        self.assertAlmostEqual(observation["blocks"][1]["bbox_points_bottom_left"][1], 662.0)

    def test_pdfinfo_parses_generic_page_size(self):
        completed = subprocess.CompletedProcess(
            ["pdfinfo"],
            0,
            stdout="Pages:          2\nPage size:       612 x 792 pts (letter)\n",
            stderr="",
        )
        with mock.patch.object(ROUTES.subprocess, "run", return_value=completed):
            sizes = ROUTES._pdfinfo_page_sizes(Path("fixture.pdf"))
        self.assertEqual(sizes, {0: (612.0, 792.0), 1: (612.0, 792.0)})

    def test_pdfinfo_parses_per_page_sizes(self):
        completed = subprocess.CompletedProcess(
            ["pdfinfo"],
            0,
            stdout=(
                "Pages:          2\n"
                "Page    1 size:  612 x 792 pts (letter)\n"
                "Page    2 size:  595 x 842 pts (A4)\n"
            ),
            stderr="",
        )
        with mock.patch.object(ROUTES.subprocess, "run", return_value=completed):
            sizes = ROUTES._pdfinfo_page_sizes(Path("fixture.pdf"))
        self.assertEqual(sizes, {0: (612.0, 792.0), 1: (595.0, 842.0)})

    def test_missing_executable_is_reported(self):
        info = ROUTES.executable_version("raiatea-poppler-does-not-exist")
        self.assertIsNone(info["version"])
        self.assertIsNone(info["returncode"])
        self.assertIsNotNone(info["error"])


class B01ScoringTests(unittest.TestCase):
    def _observation(self, route: str, order: list[str]):
        regions = {
            "Raiatea B01 PDF 002": [72.0, 716.0, 247.0, 733.0],
            "Left one.": [72.0, 662.0, 119.0, 674.0],
            "Left two.": [72.0, 622.0, 118.0, 634.0],
            "Right one.": [330.0, 662.0, 385.0, 674.0],
            "Right two.": [330.0, 622.0, 384.0, 634.0],
        }
        return {
            "route": route,
            "status": "success",
            "warnings": [],
            "blocks": [
                {"type": "text-block", "text": text, "page_index": 0, "bbox_points_bottom_left": regions[text]}
                for text in order
            ],
        }

    def test_bbox_flow_exposes_reading_order_degradation(self):
        observation = self._observation(
            "pdftotext-bbox-layout",
            ["Raiatea B01 PDF 002", "Left one.", "Right one.", "Left two.", "Right two."],
        )
        result = SCORE.measure_b01_fixture("B01-PDF-002", observation, _gold_b01_002())
        self.assertEqual(result["dimensions"]["content_text"]["matched_units"], 5)
        self.assertEqual(result["dimensions"]["source_coordinates"]["contained_count"], 5)
        self.assertEqual(result["dimensions"]["reading_order"]["satisfied_edges"], 3)
        self.assertEqual(result["dimensions"]["reading_order"]["expected_edges"], 4)
        self.assertEqual(result["dimensions"]["hierarchy"]["status"], "not-measured")

    def test_pdf2xml_order_matches_current_gold(self):
        observation = self._observation(
            "pdftohtml-xml",
            ["Raiatea B01 PDF 002", "Left one.", "Left two.", "Right one.", "Right two."],
        )
        result = SCORE.measure_b01_fixture("B01-PDF-002", observation, _gold_b01_002())
        self.assertEqual(result["dimensions"]["reading_order"]["satisfied_edges"], 4)
        self.assertEqual(result["dimensions"]["source_coordinates"]["contained_count"], 5)

    def test_duplicate_reference_text_is_not_silently_aligned(self):
        gold = {
            "reference_units": [
                {"id": "a", "text": "Same", "page_index": 0, "region": [0, 0, 100, 100]},
                {"id": "b", "text": "Same", "page_index": 0, "region": [100, 0, 200, 100]},
            ],
            "reading_order": [["a", "b"]],
        }
        observation = {
            "route": "control",
            "status": "success",
            "blocks": [
                {"text": "Same", "page_index": 0, "bbox_points_bottom_left": [1, 1, 10, 10]},
                {"text": "Same", "page_index": 0, "bbox_points_bottom_left": [101, 1, 110, 10]},
            ],
        }
        result = SCORE.measure_b01_fixture("duplicate", observation, gold)
        self.assertEqual(result["dimensions"]["content_text"]["matched_units"], 0)
        self.assertFalse(result["dimensions"]["reading_order"]["edges"][0]["satisfied"])
        self.assertTrue(result["dimensions"]["reading_order"]["edges"][0]["ambiguous_duplicate_text"])


if __name__ == "__main__":
    unittest.main()
