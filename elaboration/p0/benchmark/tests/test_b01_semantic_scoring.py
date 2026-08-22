from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_score_b01_semantic", ROUTES_DIR / "score_b01.py"
)
SCORE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCORE)


def _gold():
    return {
        "reference_units": [
            {"id": "title", "type": "heading", "level": 1, "text": "Title", "page_index": 0, "region": [10, 700, 200, 740]},
            {"id": "section", "type": "heading", "level": 2, "text": "Section", "page_index": 0, "region": [10, 650, 200, 690]},
            {"id": "li", "type": "list-item", "text": "1. Item", "page_index": 0, "region": [20, 600, 200, 630]},
            {"id": "code", "type": "code", "text": "print(1)", "page_index": 0, "region": [20, 550, 200, 580]},
            {"id": "link-label", "type": "paragraph", "text": "Example link", "page_index": 0, "region": [10, 500, 200, 530]},
        ],
        "reading_order": [["title", "section"], ["section", "li"], ["li", "code"], ["code", "link-label"]],
        "links": [
            {
                "id": "uri-link",
                "from_unit": "link-label",
                "kind": "uri",
                "target": "https://example.invalid/test",
            }
        ],
    }


def _block(text: str, semantic_type: str, level=None):
    return {
        "text": text,
        "semantic_type": semantic_type,
        "semantic_level": level,
        "page_index": 0,
        "bbox_points_bottom_left": [10, 10, 20, 20],
    }


class B01SemanticScoringTests(unittest.TestCase):
    def test_heading_levels_are_measured_only_from_explicit_evidence(self):
        observation = {
            "route": "structured-test",
            "status": "success",
            "blocks": [
                _block("Title", "heading", 1),
                _block("Section", "heading", 2),
                _block("1. Item", "list-item"),
                _block("print(1)", "code"),
                _block("Example link", "paragraph"),
            ],
            "links": [],
        }
        result = SCORE.measure_b01_fixture("semantic", observation, _gold())
        hierarchy = result["dimensions"]["hierarchy"]
        self.assertEqual(hierarchy["type_exact_count"], 5)
        levels = hierarchy["heading_levels"]
        self.assertEqual(levels["status"], "measured")
        self.assertEqual(levels["expected_count"], 2)
        self.assertEqual(levels["evidence_count"], 2)
        self.assertEqual(levels["exact_count"], 2)

    def test_missing_heading_levels_do_not_turn_type_fidelity_into_failure(self):
        observation = {
            "route": "structured-no-level-test",
            "status": "success",
            "blocks": [
                _block("Title", "heading"),
                _block("Section", "heading"),
                _block("1. Item", "list-item"),
                _block("print(1)", "code"),
                _block("Example link", "paragraph"),
            ],
        }
        result = SCORE.measure_b01_fixture("semantic", observation, _gold())
        hierarchy = result["dimensions"]["hierarchy"]
        self.assertEqual(hierarchy["type_exact_count"], 5)
        levels = hierarchy["heading_levels"]
        self.assertEqual(levels["status"], "not-measured")
        self.assertEqual(levels["evidence_count"], 0)
        self.assertEqual(levels["exact_count"], 0)

    def test_partial_heading_level_evidence_stays_partial(self):
        observation = {
            "route": "structured-partial-level-test",
            "status": "success",
            "blocks": [
                _block("Title", "heading", 1),
                _block("Section", "heading"),
                _block("1. Item", "list-item"),
                _block("print(1)", "code"),
                _block("Example link", "paragraph"),
            ],
        }
        result = SCORE.measure_b01_fixture("semantic", observation, _gold())
        levels = result["dimensions"]["hierarchy"]["heading_levels"]
        self.assertEqual(levels["status"], "partial")
        self.assertEqual(levels["evidence_count"], 1)
        self.assertEqual(levels["exact_count"], 1)

    def test_link_dimension_is_not_measured_when_route_exposes_no_link_collection(self):
        observation = {
            "route": "no-link-observation",
            "status": "success",
            "blocks": [_block("Example link", "paragraph")],
        }
        result = SCORE.measure_b01_fixture("semantic", observation, _gold())
        links = result["dimensions"]["links"]
        self.assertEqual(links["status"], "not-measured")
        self.assertEqual(links["expected_count"], 1)

    def test_link_target_without_source_association_is_partial_not_guessed(self):
        observation = {
            "route": "target-only-link-observation",
            "status": "success",
            "blocks": [_block("Example link", "paragraph")],
            "links": [
                {"kind": "uri", "target": "https://example.invalid/test"}
            ],
        }
        result = SCORE.measure_b01_fixture("semantic", observation, _gold())
        links = result["dimensions"]["links"]
        self.assertEqual(links["status"], "partial")
        self.assertEqual(links["target_exact_count"], 1)
        self.assertEqual(links["association_evidence_count"], 0)
        self.assertEqual(links["association_exact_count"], 0)

    def test_link_target_and_source_text_can_be_measured_without_layout_guess(self):
        observation = {
            "route": "associated-link-observation",
            "status": "success",
            "blocks": [_block("Example link", "paragraph")],
            "links": [
                {
                    "kind": "uri",
                    "target": "https://example.invalid/test",
                    "from_text": "Example link",
                }
            ],
        }
        result = SCORE.measure_b01_fixture("semantic", observation, _gold())
        links = result["dimensions"]["links"]
        self.assertEqual(links["status"], "measured")
        self.assertEqual(links["target_exact_count"], 1)
        self.assertEqual(links["association_evidence_count"], 1)
        self.assertEqual(links["association_exact_count"], 1)


if __name__ == "__main__":
    unittest.main()
