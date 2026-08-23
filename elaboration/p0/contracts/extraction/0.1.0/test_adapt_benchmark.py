from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

VALIDATE_SPEC = importlib.util.spec_from_file_location("e05b_validate", ROOT / "validate_contract.py")
VALIDATE = importlib.util.module_from_spec(VALIDATE_SPEC)
assert VALIDATE_SPEC.loader is not None
VALIDATE_SPEC.loader.exec_module(VALIDATE)

ADAPT_SPEC = importlib.util.spec_from_file_location("e05b_adapt", ROOT / "adapt_benchmark.py")
ADAPT = importlib.util.module_from_spec(ADAPT_SPEC)
assert ADAPT_SPEC.loader is not None
ADAPT_SPEC.loader.exec_module(ADAPT)


class E05bBenchmarkAdaptationTests(unittest.TestCase):
    def _input(self, name: str):
        return json.loads((ROOT / "adapter_inputs" / name).read_text(encoding="utf-8"))

    def _example(self, name: str):
        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_poppler_mapper_shape_adapts_without_native_field_leakage(self):
        observation = self._input("poppler-pdftohtml-observation.json")
        bundle = ADAPT.adapt_poppler_observation(
            observation,
            source_id="B01-PDF-001",
            fingerprint="sha256:poppler-adaptation-example",
        )
        VALIDATE.validate(bundle["run"])
        VALIDATE.validate_provider_evidence(bundle["provider_evidence"])
        VALIDATE.validate_representation(bundle["normalized_representation"])

        self.assertEqual(bundle["run"]["provider"]["provider_id"], "poppler")
        self.assertEqual(bundle["run"]["route_profile"]["route_profile_id"], "pdftohtml-xml")
        self.assertEqual(
            bundle["run"]["outcome"]["assessments"][0]["completeness"],
            "unknown",
        )
        coordinate = bundle["normalized_representation"]["units"][0]["coordinate"]["value"]
        self.assertEqual(coordinate["kind"], "pdf-geometric")
        serialized = json.dumps(bundle["normalized_representation"], sort_keys=True)
        self.assertNotIn("native_bbox", serialized)
        self.assertNotIn("mapped_coordinate_system", serialized)

    def test_direct_epub_mapper_shape_adapts_to_logical_coordinates(self):
        observation = self._input("direct-epub-observation.json")
        bundle = ADAPT.adapt_direct_epub_observation(
            observation,
            source_id="B02-EPUB-001",
            fingerprint="sha256:8a013c2e95ec99e07a29a09072872abe0c7e2fc0ba92378db9088817230be933",
            python_version="3.13.5",
        )
        VALIDATE.validate(bundle["run"])
        VALIDATE.validate_provider_evidence(bundle["provider_evidence"])
        VALIDATE.validate_representation(bundle["normalized_representation"])

        coordinates = [
            unit["coordinate"]["value"]
            for unit in bundle["normalized_representation"]["units"]
        ]
        self.assertTrue(all(item["kind"] == "epub-logical" for item in coordinates))
        self.assertTrue(all("page_index" not in item for item in coordinates))
        self.assertEqual(coordinates[0]["resource"], "OEBPS/ch1.xhtml")
        self.assertEqual(coordinates[2]["spine_index"], 1)
        self.assertEqual(
            bundle["run"]["outcome"]["assessments"][0]["completeness"],
            "unknown",
        )

    def test_explicit_epub_example_conforms(self):
        VALIDATE.validate_representation(self._example("direct-epub-normalized.json"))

    def test_epub_coordinate_rejects_pdf_page_fields(self):
        value = self._example("direct-epub-normalized.json")
        coordinate = value["units"][0]["coordinate"]["value"]
        coordinate["page_index"] = 0
        with self.assertRaisesRegex(VALIDATE.ContractError, "epub-must-not-use-pdf-fields"):
            VALIDATE.validate_representation(value)

    def test_restricted_attempt_retains_run_without_normalized_output(self):
        value = self._example("restricted-access-controlled.json")
        VALIDATE.validate(value)
        self.assertEqual(value["outcome"]["execution"], "restricted")
        self.assertTrue(value["produced"])
        self.assertTrue(all(item["kind"] == "provider-evidence" for item in value["produced"]))
        self.assertFalse(
            any(item["kind"] == "normalized-representation" for item in value["produced"])
        )

    def test_provider_grouping_cannot_be_marked_as_semantic(self):
        observation = self._input("poppler-pdftohtml-observation.json")
        bundle = ADAPT.adapt_poppler_observation(
            observation,
            source_id="B01-PDF-001",
            fingerprint="sha256:grouping-example",
        )
        evidence = bundle["provider_evidence"]
        evidence["groupings"] = [
            {
                "group_id": "g1",
                "provider_ref": "#/pictures/0",
                "label": "picture",
                "member_refs": ["block-0"],
                "semantic_interpretation": True,
                "basis": "negative conformance case",
            }
        ]
        with self.assertRaisesRegex(VALIDATE.ContractError, "must-remain-nonsemantic"):
            VALIDATE.validate_provider_evidence(evidence)


if __name__ == "__main__":
    unittest.main()
