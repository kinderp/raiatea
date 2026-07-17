from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import build_module as builder  # noqa: E402
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

    def test_canonical_loader_resolves_layout_reference(self) -> None:
        module_path = ROOT / "examples" / "query-key-value.json"
        data = validator.load_and_validate(module_path)
        self.assertEqual("primitives", data["visual"]["type"])
        self.assertEqual("query-key-value.layout.json", data["build"]["layoutSource"])
        ids = {item["id"] for item in data["visual"]["items"]}
        self.assertIn("attention-result", ids)

    def test_canonical_builder_renders_layout_backed_module(self) -> None:
        module_path = ROOT / "examples" / "query-key-value.json"
        data = validator.load_and_validate(module_path)
        template = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
        css = (ROOT / "src" / "module.css").read_text(encoding="utf-8")
        js = (ROOT / "src" / "module.js").read_text(encoding="utf-8")
        output = builder.render_module(data, template, css, js)
        issues = validator.validate_rendered_html(output)
        self.assertEqual([], issues, "\n".join(str(issue) for issue in issues))
        self.assertIn('id="embedding" data-node', output)
        self.assertIn('id="attention-result" data-node', output)
        self.assertIn('"layoutSource": "query-key-value.layout.json"', output)

    def test_module_schema_documents_layout_reference(self) -> None:
        schema = json.loads((ROOT / "schema" / "module.schema.json").read_text(encoding="utf-8"))
        variants = schema["properties"]["visual"]["oneOf"]
        layout_variants = [
            variant
            for variant in variants
            if variant.get("properties", {}).get("type", {}).get("const") == "layout"
        ]
        self.assertEqual(1, len(layout_variants))
        layout_variant = layout_variants[0]
        self.assertEqual(["type", "source"], layout_variant["required"])
        pattern = layout_variant["properties"]["source"]["pattern"]
        self.assertRegex("nested/example.layout.json", pattern)
        self.assertNotRegex("../outside.layout.json", pattern)

    def test_missing_layout_reference_fails_clearly(self) -> None:
        source = json.loads((ROOT / "examples" / "query-key-value.json").read_text(encoding="utf-8"))
        source["visual"]["source"] = "missing.layout.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            module_path = Path(temporary_directory) / "module.json"
            module_path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(validator.ModuleValidationError) as context:
                validator.load_and_validate(module_path)
        self.assertIn("layout file does not exist", str(context.exception))

    def test_layout_reference_requires_layout_json_suffix(self) -> None:
        source = json.loads((ROOT / "examples" / "query-key-value.json").read_text(encoding="utf-8"))
        source["visual"]["source"] = "visual.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            module_path = Path(temporary_directory) / "module.json"
            module_path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(validator.ModuleValidationError) as context:
                validator.load_and_validate(module_path)
        self.assertIn("relative *.layout.json path", str(context.exception))

    def test_layout_reference_cannot_escape_module_directory(self) -> None:
        source = json.loads((ROOT / "examples" / "query-key-value.json").read_text(encoding="utf-8"))
        source["visual"]["source"] = "../outside.layout.json"
        with tempfile.TemporaryDirectory() as temporary_directory:
            module_path = Path(temporary_directory) / "inside" / "module.json"
            module_path.parent.mkdir()
            module_path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(validator.ModuleValidationError) as context:
                validator.load_and_validate(module_path)
        self.assertIn("relative *.layout.json path", str(context.exception))

    def test_invalid_layout_values_fail_as_validation_error(self) -> None:
        source = json.loads((ROOT / "examples" / "query-key-value.json").read_text(encoding="utf-8"))
        source["visual"]["source"] = "broken.layout.json"
        invalid_layout = {
            "type": "pipeline",
            "x": "left",
            "nodes": [
                {"id": "a", "title": "A"},
                {"id": "b", "title": "B"},
            ],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            module_path = directory / "module.json"
            module_path.write_text(json.dumps(source), encoding="utf-8")
            (directory / "broken.layout.json").write_text(
                json.dumps(invalid_layout),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ModuleValidationError) as context:
                validator.load_and_validate(module_path)
        self.assertIn("invalid declarative layout", str(context.exception))

    def test_invalid_layout_is_rejected(self) -> None:
        with self.assertRaises(layout_visual.LayoutError):
            layout_visual.compile_layout({"type": "parallel", "branches": []})


if __name__ == "__main__":
    unittest.main()
