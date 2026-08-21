from __future__ import annotations

import importlib.util
import json
from pathlib import Path
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


GEN = _load("p0_generate_fixtures_b02", BENCH_DIR / "generate_fixtures.py")
ROUTES = _load("p0_epub_routes", ROUTES_DIR / "epub_routes.py")
SCORE = _load("p0_score_b02", ROUTES_DIR / "score_b02.py")


class DirectEpubRouteTests(unittest.TestCase):
    def setUp(self):
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )

    def test_direct_route_preserves_spine_and_authored_fragments(self):
        with tempfile.TemporaryDirectory() as tmp:
            GEN.generate_all(Path(tmp))
            observation = ROUTES.parse_direct_epub(Path(tmp) / "B02-EPUB-001.epub")
            self.assertEqual(observation["status"], "success")
            self.assertEqual(observation["spine"], ["ch1", "ch2"])
            blocks = {block["text"]: block for block in observation["blocks"]}
            self.assertEqual(blocks["Introduction"]["resource"], "OEBPS/ch1.xhtml")
            self.assertEqual(blocks["Introduction"]["fragment"], "intro")
            self.assertEqual(
                blocks["The first chapter establishes the package order."]["fragment"],
                "intro-text",
            )

    def test_direct_route_preserves_navigation_and_cross_resource_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            GEN.generate_all(Path(tmp))
            observation = ROUTES.parse_direct_epub(Path(tmp) / "B02-EPUB-002.epub")
            self.assertEqual(observation["status"], "success")
            nav_by_label = {item["label"]: item for item in observation["navigation"]}
            self.assertEqual(nav_by_label["Details"]["resource"], "OEBPS/ch2.xhtml")
            self.assertEqual(nav_by_label["Details"]["fragment"], "details")
            self.assertEqual(observation["links"][0]["from_fragment"], "to-details")
            self.assertEqual(observation["links"][0]["target_resource"], "OEBPS/ch2.xhtml")
            self.assertEqual(observation["links"][0]["target_fragment"], "details")

    def test_direct_route_reports_active_content_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            GEN.generate_all(Path(tmp))
            observation = ROUTES.parse_direct_epub(Path(tmp) / "B02-EPUB-NEG-001.epub")
            self.assertEqual(observation["status"], "degraded")
            codes = {warning["code"] for warning in observation["warnings"]}
            self.assertIn("active-content-present", codes)
            self.assertTrue(observation["active_content"])

    def test_direct_route_rejects_unsafe_package_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            GEN.generate_all(Path(tmp))
            observation = ROUTES.parse_direct_epub(Path(tmp) / "B02-EPUB-NEG-002.epub")
            self.assertEqual(observation["status"], "rejected")
            codes = {warning["code"] for warning in observation["warnings"]}
            self.assertIn("unsafe-package-member", codes)

    def test_path_validator_rejects_cross_platform_hazards(self):
        cases = {
            "../outside.txt": "parent-traversal",
            "/absolute.txt": "absolute-path",
            r"nested\file.txt": "backslash-path",
            "C:/windows.txt": "absolute-path",
        }
        for value, expected in cases.items():
            self.assertEqual(ROUTES._unsafe_member_reason(value), expected)


class PandocMapperTests(unittest.TestCase):
    def test_mapper_tracks_resource_markers_and_heading_fragments(self):
        document = {
            "pandoc-api-version": [1, 23, 1],
            "blocks": [
                {"t": "Para", "c": [{"t": "Span", "c": [["ch1.xhtml", [], []], []]}]},
                {"t": "Header", "c": [1, ["ch1.xhtml#intro", [], []], [{"t": "Str", "c": "Introduction"}]]},
                {"t": "Para", "c": [{"t": "Str", "c": "Alpha"}, {"t": "Space"}, {"t": "Str", "c": "paragraph."}]},
                {"t": "Para", "c": [{"t": "Span", "c": [["ch2.xhtml", [], []], []]}]},
                {"t": "Header", "c": [1, ["ch2.xhtml#details", [], []], [{"t": "Str", "c": "Details"}]]},
            ],
        }
        observation = ROUTES.map_pandoc_json(document)
        self.assertEqual(observation["spine"], ["ch1", "ch2"])
        headings = [block for block in observation["blocks"] if block["type"] == "heading"]
        self.assertEqual(headings[0]["resource"], "ch1.xhtml")
        self.assertEqual(headings[0]["fragment"], "intro")
        paragraph = next(block for block in observation["blocks"] if block["type"] == "paragraph")
        self.assertEqual(paragraph["resource"], "ch1.xhtml")
        self.assertIsNone(paragraph["fragment"])
        codes = {warning["code"] for warning in observation["warnings"]}
        self.assertIn("navigation-not-exposed-in-pandoc-ast", codes)

    def test_mapper_preserves_raw_link_target_and_missing_from_fragment(self):
        document = {
            "pandoc-api-version": [1, 23, 1],
            "blocks": [
                {"t": "Para", "c": [{"t": "Span", "c": [["ch1.xhtml", [], []], []]}]},
                {"t": "Para", "c": [{"t": "Link", "c": [["", [], []], [{"t": "Str", "c": "Go"}], ["#ch2.xhtml#details", ""]]}]},
            ],
        }
        observation = ROUTES.map_pandoc_json(document)
        self.assertEqual(observation["links"][0]["raw_target"], "#ch2.xhtml#details")
        self.assertEqual(observation["links"][0]["from_resource"], "ch1.xhtml")
        self.assertIsNone(observation["links"][0]["from_fragment"])

    def test_pandoc_runner_uses_sandbox_and_controlled_input(self):
        captured = {}

        class Completed:
            returncode = 0
            stdout = '{"pandoc-api-version":[1,23,1],"meta":{},"blocks":[]}'
            stderr = ""

        def fake_run(command, **kwargs):
            captured["command"] = command
            captured["cwd"] = Path(kwargs["cwd"])
            return Completed()

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.epub"
            source.write_bytes(b"fixture")
            with mock.patch.object(ROUTES.subprocess, "run", side_effect=fake_run):
                observation = ROUTES.run_pandoc_epub(source, "pandoc")

        self.assertEqual(observation["status"], "success")
        self.assertTrue(observation["sandbox_enabled"])
        self.assertIn("--sandbox", captured["command"])
        input_argument = Path(captured["command"][-1])
        self.assertNotEqual(input_argument, source)
        self.assertEqual(input_argument.name, "source.epub")
        self.assertEqual(captured["cwd"].name, "work")

    def test_missing_pandoc_version_is_reported_not_raised(self):
        info = ROUTES.pandoc_version("raiatea-pandoc-does-not-exist")
        self.assertIsNone(info["version"])
        self.assertIsNone(info["returncode"])
        self.assertIsNotNone(info["error"])


class B02ScoringTests(unittest.TestCase):
    def setUp(self):
        self.gold = json.loads(
            (BENCH_DIR / "manifests" / "gold.json").read_text(encoding="utf-8")
        )

    def test_direct_observation_scores_all_b02_001_reference_coordinates_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            GEN.generate_all(Path(tmp))
            observation = ROUTES.parse_direct_epub(Path(tmp) / "B02-EPUB-001.epub")
            result = SCORE.measure_normal_fixture(
                "B02-EPUB-001", observation, self.gold["fixtures"]["B02-EPUB-001"]
            )
            coords = result["dimensions"]["source_coordinates"]
            self.assertEqual(coords["full_exact_count"], coords["expected_count"])
            self.assertEqual(result["dimensions"]["content_text"]["exact_fraction"], 1.0)
            self.assertEqual(
                result["dimensions"]["reading_order"]["satisfied_edges"],
                result["dimensions"]["reading_order"]["expected_edges"],
            )

    def test_pandoc_like_observation_exposes_paragraph_anchor_degradation(self):
        observation = {
            "route": "pandoc-epub",
            "status": "success",
            "warnings": [],
            "spine": ["ch1", "ch2"],
            "blocks": [
                {"type": "heading", "text": "Introduction", "resource": "ch1.xhtml", "fragment": "intro"},
                {"type": "paragraph", "text": "The first chapter establishes the package order.", "resource": "ch1.xhtml", "fragment": None},
                {"type": "heading", "text": "Next Chapter", "resource": "ch2.xhtml", "fragment": "next"},
                {"type": "paragraph", "text": "The second chapter follows the first in the spine.", "resource": "ch2.xhtml", "fragment": None},
            ],
            "navigation": [],
            "links": [],
        }
        result = SCORE.measure_normal_fixture(
            "B02-EPUB-001", observation, self.gold["fixtures"]["B02-EPUB-001"]
        )
        coords = result["dimensions"]["source_coordinates"]
        self.assertEqual(coords["full_exact_count"], 0)
        self.assertEqual(coords["traceable_count"], 2)
        self.assertEqual(result["dimensions"]["content_text"]["exact_fraction"], 1.0)

    def test_negative_fixture_scoring_keeps_partial_and_not_measured_states(self):
        direct_active = {
            "route": "direct-epub-stdlib",
            "status": "degraded",
            "warnings": [{"code": "active-content-present"}],
            "side_effect_files": [],
        }
        direct_result = SCORE.measure_negative_fixture(
            "B02-EPUB-NEG-001", direct_active, self.gold["fixtures"]["B02-EPUB-NEG-001"]
        )
        self.assertTrue(direct_result["expected_state_assessment"]["satisfied"])
        script = next(
            item for item in direct_result["security_expectations"]
            if item["expectation"] == "script-not-executed"
        )
        self.assertEqual(script["status"], "measured")
        self.assertTrue(script["satisfied"])

        pandoc_unsafe = {
            "route": "pandoc-epub",
            "status": "success",
            "warnings": [],
            "side_effect_files": [],
            "sandbox_enabled": True,
            "network_instrumentation": "not-measured",
        }
        pandoc_result = SCORE.measure_negative_fixture(
            "B02-EPUB-NEG-002", pandoc_unsafe, self.gold["fixtures"]["B02-EPUB-NEG-002"]
        )
        self.assertFalse(pandoc_result["expected_state_assessment"]["satisfied"])
        checks = {item["expectation"]: item for item in pandoc_result["security_expectations"]}
        self.assertEqual(checks["no-path-escape"]["status"], "partial")
        self.assertTrue(checks["no-path-escape"]["satisfied"])
        self.assertEqual(checks["no-extractall"]["status"], "not-measured")
        self.assertIsNone(checks["no-extractall"]["satisfied"])


if __name__ == "__main__":
    unittest.main()
