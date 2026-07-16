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
import render_visual  # noqa: E402
import validate_module as validator  # noqa: E402


class ModuleValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example_path = ROOT / "examples" / "self-attention.json"
        cls.procedure_path = ROOT / "examples" / "self-attention-procedure.json"
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))
        cls.procedure = json.loads(cls.procedure_path.read_text(encoding="utf-8"))
        cls.template = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "src" / "module.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "src" / "module.js").read_text(encoding="utf-8")

    def clone_example(self) -> dict:
        return json.loads(json.dumps(self.example))

    def clone_procedure(self) -> dict:
        return json.loads(json.dumps(self.procedure))

    def messages(self, issues) -> str:
        return "\n".join(str(issue) for issue in issues)

    def test_example_module_is_valid(self) -> None:
        issues = validator.validate_module(self.clone_example())
        self.assertEqual([], issues, self.messages(issues))

    def test_procedure_module_is_valid(self) -> None:
        issues = validator.validate_module(self.clone_procedure())
        self.assertEqual([], issues, self.messages(issues))

    def test_example_uses_semantic_primitives(self) -> None:
        data = self.clone_example()
        self.assertEqual("primitives", data["visual"]["type"])
        kinds = {item["kind"] for item in data["visual"]["items"]}
        self.assertEqual({"box", "edge"}, kinds)

    def test_procedure_uses_advanced_primitives(self) -> None:
        kinds = {item["kind"] for item in self.clone_procedure()["visual"]["items"]}
        self.assertTrue({"token-row", "matrix", "weighted-sum", "vector"}.issubset(kinds))

    def test_primitive_renderer_generates_accessible_svg(self) -> None:
        visual = self.clone_example()["visual"]
        markup = render_visual.render_visual(visual)
        self.assertIn('<svg viewBox="0 0 900 420"', markup)
        self.assertIn('<title id="visual-title">', markup)
        self.assertIn('id="attention" data-node', markup)
        self.assertIn('id="f2" data-flow', markup)

    def test_advanced_renderer_outputs_matrix_and_weighted_sum(self) -> None:
        markup = render_visual.render_visual(self.clone_procedure()["visual"])
        self.assertIn('id="tokens" data-node', markup)
        self.assertIn('id="scores" data-node', markup)
        self.assertIn('primitive-matrix-focus', markup)
        self.assertIn('id="context-sum" data-node', markup)
        self.assertIn('primitive-weighted-result', markup)

    def test_quiz_correct_index_must_exist(self) -> None:
        data = self.clone_example()
        data["steps"][0]["quiz"]["correctIndex"] = 99
        issues = validator.validate_module(data)
        self.assertIn("correctIndex", self.messages(issues))

    def test_duplicate_concept_ids_are_rejected(self) -> None:
        data = self.clone_example()
        data["concepts"].append(dict(data["concepts"][0]))
        issues = validator.validate_module(data)
        self.assertIn("duplicate concept id", self.messages(issues))

    def test_duplicate_primitive_ids_are_rejected(self) -> None:
        data = self.clone_example()
        duplicate = dict(data["visual"]["items"][0])
        data["visual"]["items"].append(duplicate)
        issues = validator.validate_module(data)
        self.assertIn("duplicate primitive id", self.messages(issues))

    def test_unknown_primitive_kind_is_rejected(self) -> None:
        data = self.clone_example()
        data["visual"]["items"][0]["kind"] = "circle"
        issues = validator.validate_module(data)
        self.assertIn("must be one of", self.messages(issues))

    def test_matrix_rows_must_have_equal_length(self) -> None:
        data = self.clone_procedure()
        matrix = next(item for item in data["visual"]["items"] if item["kind"] == "matrix")
        matrix["values"].append([1, 2])
        issues = validator.validate_module(data)
        self.assertIn("same length", self.messages(issues))

    def test_matrix_labels_must_match_dimensions(self) -> None:
        data = self.clone_procedure()
        matrix = next(item for item in data["visual"]["items"] if item["kind"] == "matrix")
        matrix["columnLabels"] = ["only-one"]
        issues = validator.validate_module(data)
        self.assertIn("must contain 6 labels", self.messages(issues))

    def test_token_row_active_index_must_exist(self) -> None:
        data = self.clone_procedure()
        token_row = next(item for item in data["visual"]["items"] if item["kind"] == "token-row")
        token_row["activeIndex"] = 99
        issues = validator.validate_module(data)
        self.assertIn("existing token", self.messages(issues))

    def test_weighted_sum_requires_terms(self) -> None:
        data = self.clone_procedure()
        weighted = next(item for item in data["visual"]["items"] if item["kind"] == "weighted-sum")
        weighted["terms"] = []
        issues = validator.validate_module(data)
        self.assertIn("at least one term", self.messages(issues))

    def test_unknown_visual_node_is_rejected(self) -> None:
        data = self.clone_example()
        data["steps"][0].setdefault("activeNodes", []).append("missing-node")
        issues = validator.validate_module(data)
        self.assertIn("does not exist", self.messages(issues))

    def test_animated_flow_must_reference_edge(self) -> None:
        data = self.clone_example()
        data["steps"][0]["animatedFlows"] = ["input"]
        issues = validator.validate_module(data)
        self.assertIn("edge primitives", self.messages(issues))

    def test_unknown_prerequisite_concept_reference_is_rejected(self) -> None:
        data = self.clone_example()
        data["prerequisites"][0]["conceptRef"] = "not-a-concept"
        issues = validator.validate_module(data)
        self.assertIn("unknown concept reference", self.messages(issues))

    def test_broken_internal_output_link_is_rejected(self) -> None:
        output = '<!doctype html><html><script>window.RAIATEA_MODULE={}</script><a href="#missing">x</a></html>'
        issues = validator.validate_rendered_html(output)
        self.assertIn("broken internal reference", self.messages(issues))

    def test_unresolved_template_placeholder_is_rejected(self) -> None:
        output = '<!doctype html><html><script>window.RAIATEA_MODULE={}</script>{{ missing }}</html>'
        issues = validator.validate_rendered_html(output)
        self.assertIn("unresolved placeholder", self.messages(issues))

    def test_external_resources_are_rejected(self) -> None:
        output = '<!doctype html><html><script>window.RAIATEA_MODULE={}</script><img src="https://example.com/x.png"></html>'
        issues = validator.validate_rendered_html(output)
        self.assertIn("external resource", self.messages(issues))

    def test_rendered_example_passes_output_validation(self) -> None:
        data = self.clone_example()
        output = builder.render_module(data, self.template, self.css, self.js)
        issues = validator.validate_rendered_html(output)
        self.assertEqual([], issues, self.messages(issues))
        self.assertIn('class="primitive-node primitive-attention"', output)
        self.assertNotIn("<svg viewBox=\\\"", json.dumps(data["visual"], ensure_ascii=False))

    def test_rendered_procedure_passes_output_validation(self) -> None:
        data = self.clone_procedure()
        output = builder.render_module(data, self.template, self.css, self.js)
        issues = validator.validate_rendered_html(output)
        self.assertEqual([], issues, self.messages(issues))
        self.assertIn('primitive-weighted-sum', output)
        self.assertIn('primitive-matrix', output)

    def test_load_and_validate_reports_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "broken.json"
            path.write_text('{"id":', encoding="utf-8")
            with self.assertRaises(validator.ModuleValidationError):
                validator.load_and_validate(path)


if __name__ == "__main__":
    unittest.main()
