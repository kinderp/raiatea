from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
sys.path.insert(0, str(ROUTES))
SPEC = importlib.util.spec_from_file_location(
    "p0_measure_b01_figure_evidence", ROUTES / "measure_b01_figure_evidence.py"
)
MEASURE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MEASURE)


GOLD = {
    "figures": [{"id": "figure-1"}],
    "reference_units": [
        {
            "id": "caption",
            "type": "caption",
            "text": "Figure 1. Deterministic Raiatea color grid.",
        }
    ],
    "figure_caption_relations": [
        {
            "figure_id": "figure-1",
            "caption_unit": "caption",
            "relation": "caption-of",
        }
    ],
}


class FigureMeasurementBindingTests(unittest.TestCase):
    def _provider_evidence(self, caption_text: str) -> dict:
        return {
            "figures": [{"provider_ref": "#/pictures/0"}],
            "figure_caption_relations": [
                {
                    "provider_figure_ref": "#/pictures/0",
                    "provider_caption_ref": "#/texts/2",
                    "caption_text": caption_text,
                    "provider_relation_source": "docling-picture.captions-explicit-ref",
                }
            ],
        }

    def test_exact_explicit_relation_binds_to_gold(self):
        evidence = self._provider_evidence(
            "Figure 1. Deterministic Raiatea color grid."
        )
        self.assertTrue(
            MEASURE._bind_single_explicit_relation_to_gold(evidence, GOLD)
        )
        relation = evidence["figure_caption_relations"][0]
        self.assertEqual(relation["gold_figure_id"], "figure-1")
        self.assertEqual(relation["gold_caption_unit"], "caption")
        self.assertEqual(
            relation["gold_matching_basis"],
            "single-explicit-figure-plus-exact-caption-text",
        )

    def test_whitespace_normalization_does_not_break_exact_caption_identity(self):
        evidence = self._provider_evidence(
            "  Figure 1.   Deterministic Raiatea color grid.  "
        )
        self.assertTrue(
            MEASURE._bind_single_explicit_relation_to_gold(evidence, GOLD)
        )

    def test_wrong_caption_text_remains_unbound(self):
        evidence = self._provider_evidence("Figure 9. Wrong caption.")
        self.assertFalse(
            MEASURE._bind_single_explicit_relation_to_gold(evidence, GOLD)
        )
        relation = evidence["figure_caption_relations"][0]
        self.assertNotIn("gold_figure_id", relation)
        self.assertNotIn("gold_caption_unit", relation)

    def test_relation_to_different_provider_figure_remains_unbound(self):
        evidence = self._provider_evidence(
            "Figure 1. Deterministic Raiatea color grid."
        )
        evidence["figure_caption_relations"][0]["provider_figure_ref"] = (
            "#/pictures/99"
        )
        self.assertFalse(
            MEASURE._bind_single_explicit_relation_to_gold(evidence, GOLD)
        )

    def test_multiple_provider_relations_remain_ambiguous(self):
        evidence = self._provider_evidence(
            "Figure 1. Deterministic Raiatea color grid."
        )
        evidence["figure_caption_relations"].append(
            dict(evidence["figure_caption_relations"][0])
        )
        self.assertFalse(
            MEASURE._bind_single_explicit_relation_to_gold(evidence, GOLD)
        )


if __name__ == "__main__":
    unittest.main()
