from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import layout_visual  # noqa: E402
import render_visual  # noqa: E402
import validate_module_v2 as validator  # noqa: E402


class DeclarativeLayoutTests(unittest.TestCase):
    def test_pipeline_compiles_to_boxes_and_edges(self) -> None:
        visual = layout_visual.compile_layout({
            "type": "pipeline",
            "nodes": [
                {"id": "a", "title": "A"},
                {"id": "b", "title": "B"},
                {"id": "c", "title": "C"},
            ],
        })
        self.assertEqual("primitives", visual["type"])
        self.assertEqual(3, len([item for item in visual["items"] if item["kind"] == "box"]))
        self.assertEqual(2, len([item for item in visual["items"] if item["kind"] == "edge"]))

    def test_branch_merge_compiles_qkv_without_manual_coordinates(self) -> None:
        path = ROOT / "examples" / "query-key-value.layout.json"
        layout = json.loads(path.read_text(encoding="utf-8"))
        visual = layout_visual.compile_layout(layout)
        ids = {item["id"] for item in visual["items"]}
        self.assertTrue({"embedding", "query", "key", "value", "attention-result"}.issubset(ids))
        markup = render_visual.render_visual(visual)
        self.assertIn('id="query" data-node', markup)
        self.assertIn('id="value-to-attention-result" data-flow', markup)

    def test_compiled_visual_is_accepted_by_module_validator(self) -> None:
        module_path = ROOT / "examples" / "query-key-value.json"
        data = json.loads(module_path.read_text(encoding="utf-8"))
        layout = json.loads((ROOT / "examples" / "query-key-value.layout.json").read_text(encoding="utf-8"))
        data["visual"] = layout_visual.compile_layout(layout)
        issues = validator.validate_module(data)
        self.assertEqual([], issues, "\n".join(str(issue) for issue in issues))

    def test_invalid_layout_is_rejected(self) -> None:
        with self.assertRaises(layout_visual.LayoutError):
            layout_visual.compile_layout({"type": "parallel", "branches": []})


if __name__ == "__main__":
    unittest.main()
