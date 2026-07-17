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
import validate_module_v2 as validator  # noqa: E402


class ModuleValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example_path = ROOT / "examples" / "self-attention.json"
        cls.qkv_path = ROOT / "examples" / "query-key-value.json"
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))
        cls.qkv_source = json.loads(cls.qkv_path.read_text(encoding="utf-8"))
        cls.qkv = validator.load_and_validate(cls.qkv_path)
        cls.template = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "src" / "module.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "src" / "module.js").read_text(encoding="utf-8")

    def clone_example(self) -> dict:
        return json.loads(json.dumps(self.example))

    def clone_qkv(self) -> dict:
        return json.loads(json.dumps(self.qkv))

    def messages(self, issues) -> str:
        return "\n".join(str(issue) for issue in issues)

    def test_example_module_is_valid(self) -> None:
        issues = validator.validate_module(self.clone_example())
        self.assertEqual([], issues, self.messages(issues))

    def test_query_key_value_source_uses_layout_reference(self) -> None:
        self.assertEqual(
            {"type": "layout", "source": "query-key-value.layout.json"},
            self.qkv_source["visual"],
        )

    def test_query_key_value_module_is_valid_after_layout_resolution(self) -> None:
        data = self.clone_qkv()
        issues = validator.validate_module(data)
        self.assertEqual([], issues, self.messages(issues))
        self.assertEqual("primitives", data["visual"]["type"])
        self.assertEqual("query-key-value.layout.json", data["build"]["layoutSource"])
        self.assertEqual(
            {"query", "key", "value"},
            {
                item["id"]
                for item in data["visual"]["items"]
                if item["id"] in {"query", "key", "value"}
            },
        )

    def test_query_key_value_module_renders_without_template_changes(self) -> None:
        output = builder.render_module(self.clone_qkv(), self.template, self.css, self.js)
        issues = validator.validate_rendered_html(output)
        self.assertEqual([], issues, self.messages(issues))
        self.assertIn("Query, Key e Value", output)
        self.assertIn('id="attention-result" data-node', output)
        self.assertIn("selezione + contenuto", output)
        self.assertIn('"layoutSource": "query-key-value.layout.json"', output)
        self.assertIn("stepwise-decomposition", output)

    def test_example_uses_semantic_primitives(self) -> None:
        data = self.clone_example()
        self.assertEqual("primitives", data["visual"]["type"])
        self.assertEqual({"box", "edge"}, {item["kind"] for item in data["visual"]["items"]})

    def test_example_contains_adaptive_micro_activity(self) -> None:
        remediation = self.example["steps"][0]["quiz"]["remediation"]
        self.assertEqual("self-attention", remediation["conceptRef"])
        self.assertEqual("choice", remediation["activity"]["type"])
        self.assertEqual(2, len(remediation["activity"]["answers"]))

    def test_example_contains_step_provenance(self) -> None:
        provenance = self.example["steps"][0]["provenance"]
        self.assertEqual("adaptation", provenance["kind"])
        self.assertIn("interactive-reconstruction", provenance["transformations"])
        self.assertEqual([55], provenance["sourcePages"])

    def test_primitive_renderer_generates_accessible_svg(self) -> None:
        markup = render_visual.render_visual(self.clone_example()["visual"])
        self.assertIn('<svg viewBox="0 0 900 420"', markup)
        self.assertIn('<title id="visual-title">', markup)
        self.assertIn('id="attention" data-node', markup)
        self.assertIn('id="f2" data-flow', markup)

    def test_quiz_correct_index_must_exist(self) -> None:
        data = self.clone_example()
        data["steps"][0]["quiz"]["correctIndex"] = 99
        self.assertIn("correctIndex", self.messages(validator.validate_module(data)))

    def test_remediation_requires_title(self) -> None:
        data = self.clone_example()
        del data["steps"][0]["quiz"]["remediation"]["title"]
        self.assertIn("remediation.title", self.messages(validator.validate_module(data)))

    def test_remediation_concept_reference_must_exist(self) -> None:
        data = self.clone_example()
        data["steps"][0]["quiz"]["remediation"]["conceptRef"] = "missing-concept"
        self.assertIn("unknown concept reference", self.messages(validator.validate_module(data)))

    def test_micro_activity_requires_two_answers(self) -> None:
        data = self.clone_example()
        data["steps"][0]["quiz"]["remediation"]["activity"]["answers"] = ["solo"]
        self.assertIn("at least two answers", self.messages(validator.validate_module(data)))

    def test_micro_activity_correct_index_must_exist(self) -> None:
        data = self.clone_example()
        data["steps"][0]["quiz"]["remediation"]["activity"]["correctIndex"] = 9
        self.assertIn("must refer to an answer", self.messages(validator.validate_module(data)))

    def test_micro_activity_type_is_choice(self) -> None:
        data = self.clone_example()
        data["steps"][0]["quiz"]["remediation"]["activity"]["type"] = "free-text"
        self.assertIn("must be choice", self.messages(validator.validate_module(data)))

    def test_provenance_kind_is_controlled(self) -> None:
        data = self.clone_example()
        data["steps"][0]["provenance"]["kind"] = "unknown"
        self.assertIn("provenance.kind", self.messages(validator.validate_module(data)))

    def test_provenance_pages_are_positive(self) -> None:
        data = self.clone_example()
        data["steps"][0]["provenance"]["sourcePages"] = [0]
        self.assertIn("positive integer", self.messages(validator.validate_module(data)))

    def test_provenance_transformations_are_controlled(self) -> None:
        data = self.clone_example()
        data["steps"][0]["provenance"]["transformations"] = ["invented-transform"]
        self.assertIn("transformations[0]", self.messages(validator.validate_module(data)))

    def test_duplicate_concept_ids_are_rejected(self) -> None:
        data = self.clone_example()
        data["concepts"].append(dict(data["concepts"][0]))
        self.assertIn("duplicate concept id", self.messages(validator.validate_module(data)))

    def test_duplicate_primitive_ids_are_rejected(self) -> None:
        data = self.clone_example()
        data["visual"]["items"].append(dict(data["visual"]["items"][0]))
        self.assertIn("duplicate primitive id", self.messages(validator.validate_module(data)))

    def test_unknown_primitive_kind_is_rejected(self) -> None:
        data = self.clone_example()
        data["visual"]["items"][0]["kind"] = "circle"
        self.assertIn("must be one of", self.messages(validator.validate_module(data)))

    def test_unknown_visual_node_is_rejected(self) -> None:
        data = self.clone_example()
        data["steps"][0].setdefault("activeNodes", []).append("missing-node")
        self.assertIn("does not exist", self.messages(validator.validate_module(data)))

    def test_animated_flow_must_reference_edge(self) -> None:
        data = self.clone_example()
        data["steps"][0]["animatedFlows"] = ["input"]
        self.assertIn("edge primitives", self.messages(validator.validate_module(data)))

    def test_unknown_prerequisite_concept_reference_is_rejected(self) -> None:
        data = self.clone_example()
        data["prerequisites"][0]["conceptRef"] = "not-a-concept"
        self.assertIn("unknown concept reference", self.messages(validator.validate_module(data)))

    def test_broken_internal_output_link_is_rejected(self) -> None:
        output = '<!doctype html><html><script>window.RAIATEA_MODULE={}</script><a href="#missing">x</a></html>'
        self.assertIn("broken internal reference", self.messages(validator.validate_rendered_html(output)))

    def test_dynamic_javascript_internal_link_is_not_treated_as_static(self) -> None:
        output = '<!doctype html><html><script>window.RAIATEA_MODULE={};const x = `<a href="#concept-${escapeHtml(ref)}">x</a>`;</script></html>'
        self.assertNotIn("broken internal reference", self.messages(validator.validate_rendered_html(output)))

    def test_unresolved_template_placeholder_is_rejected(self) -> None:
        output = '<!doctype html><html><script>window.RAIATEA_MODULE={}</script>{{ missing }}</html>'
        self.assertIn("unresolved placeholder", self.messages(validator.validate_rendered_html(output)))

    def test_external_resources_are_rejected(self) -> None:
        output = '<!doctype html><html><script>window.RAIATEA_MODULE={}</script><img src="https://example.com/x.png"></html>'
        self.assertIn("external resource", self.messages(validator.validate_rendered_html(output)))

    def test_rendered_example_passes_output_validation(self) -> None:
        output = builder.render_module(self.clone_example(), self.template, self.css, self.js)
        issues = validator.validate_rendered_html(output)
        self.assertEqual([], issues, self.messages(issues))
        self.assertIn('class="primitive-node primitive-attention"', output)
        self.assertIn("data-remediation-activity", output)
        self.assertIn('id="evidenceGrid"', output)
        self.assertIn("raiatea-progress:", output)
        self.assertIn("activityCompleted", output)
        self.assertIn('id="stepProvenance"', output)
        self.assertIn("renderStepProvenance", output)
        self.assertIn("interactive-reconstruction", output)

    def test_load_and_validate_reports_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "broken.json"
            path.write_text('{"id":', encoding="utf-8")
            with self.assertRaises(validator.ModuleValidationError):
                validator.load_and_validate(path)


if __name__ == "__main__":
    unittest.main()
