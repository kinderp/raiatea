from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e05b_validate", ROOT / "validate_contract.py")
VALIDATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATE)


class E05bConformanceTests(unittest.TestCase):
    def _load(self, name: str):
        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_poppler_example_conforms(self):
        VALIDATE.validate(self._load("poppler-native-pdf.json"))

    def test_docling_rapidocr_staged_example_conforms(self):
        VALIDATE.validate(self._load("docling-rapidocr-staged.json"))

    def test_restricted_before_provider_example_conforms(self):
        value = self._load("restricted-before-provider.json")
        VALIDATE.validate(value)
        self.assertEqual(value["stages"], [])
        self.assertEqual(value["produced"], [])
        self.assertEqual(value["outcome"]["execution"], "not-started")
        self.assertIn("rights_decision_ref", value)

    def test_boolean_success_is_rejected(self):
        value = self._load("poppler-native-pdf.json")
        value["outcome"]["success"] = True
        with self.assertRaisesRegex(VALIDATE.ContractError, "processing-outcome-must-not-be-boolean"):
            VALIDATE.validate(value)

    def test_global_unscoped_assessment_is_rejected(self):
        value = self._load("poppler-native-pdf.json")
        del value["outcome"]["assessments"][0]["scope"]
        with self.assertRaisesRegex(VALIDATE.ContractError, "scope-required"):
            VALIDATE.validate(value)

    def test_run_cannot_own_provider_route_identity(self):
        value = self._load("poppler-native-pdf.json")
        value["provider"] = {"provider_id": "poppler", "version": "24.02.0"}
        with self.assertRaisesRegex(VALIDATE.ContractError, "run-must-not-own-provider-route-identity"):
            VALIDATE.validate(value)

    def test_provider_and_route_identity_cannot_collapse_inside_provider_stage(self):
        value = self._load("poppler-native-pdf.json")
        executor = value["stages"][0]["executor"]
        executor["provider"]["route_profile_id"] = "pdftohtml-xml"
        with self.assertRaisesRegex(VALIDATE.ContractError, "provider-and-route-profile-must-remain-distinct"):
            VALIDATE.validate(value)

    def test_not_measured_evidence_cannot_claim_present_value(self):
        value = self._load("poppler-native-pdf.json")
        status = value["stages"][0]["provider_status"]
        status["evidence_state"] = "not-measured"
        with self.assertRaisesRegex(VALIDATE.ContractError, "not-measured-must-have-unknown-value"):
            VALIDATE.validate(value)

    def test_not_measured_evidence_origin_is_unresolved(self):
        evidence = {
            "evidence_state": "not-measured",
            "value_state": "unknown",
            "origin": "provider-native",
            "basis": "Provider did not expose the field",
        }
        with self.assertRaisesRegex(VALIDATE.ContractError, "not-measured-origin-must-be-unresolved"):
            VALIDATE._validate_evidence(evidence, "candidate")

    def test_explicit_empty_is_present_evidence_not_unavailable(self):
        evidence = {
            "evidence_state": "measured",
            "value_state": "explicit-empty",
            "origin": "provider-native",
            "basis": "Provider explicitly emitted an empty collection",
            "channel": "provider-lossless-raw",
            "value": [],
        }
        VALIDATE._validate_evidence(evidence, "candidate")
        self.assertEqual(evidence["value"], [])

    def test_mismatch_is_assessment_not_value_state(self):
        evidence = {
            "evidence_state": "measured",
            "value_state": "present",
            "origin": "provider-native",
            "basis": "Provider exposed the observed fact",
            "channel": "provider-lossless-raw",
            "value": "TARGET OCR 2026",
            "assessment": {
                "state": "mismatch",
                "basis": "comparison against an explicit authoritative expectation",
                "compared_to_ref": "expectation:ocr-target",
            },
        }
        VALIDATE._validate_evidence(evidence, "candidate")
        evidence["value_state"] = "explicit-mismatch"
        with self.assertRaisesRegex(VALIDATE.ContractError, "bad-value-state"):
            VALIDATE._validate_evidence(evidence, "candidate")

    def test_mismatch_assessment_requires_available_observed_value(self):
        evidence = {
            "evidence_state": "not-measured",
            "value_state": "unknown",
            "origin": "unresolved",
            "basis": "field unavailable",
            "assessment": {
                "state": "mismatch",
                "basis": "invalid synthetic comparison",
            },
        }
        with self.assertRaisesRegex(VALIDATE.ContractError, "assessment-requires-available-evidence"):
            VALIDATE._validate_evidence(evidence, "candidate")

    def test_provider_channel_does_not_replace_epistemic_origin(self):
        value = self._load("poppler-native-pdf.json")
        status = value["stages"][0]["provider_status"]
        del status["origin"]
        self.assertIn("channel", status)
        with self.assertRaisesRegex(VALIDATE.ContractError, "bad-evidence-origin"):
            VALIDATE.validate(value)

    def test_ocr_stage_requires_trigger_and_preceding_parent(self):
        value = self._load("docling-rapidocr-staged.json")
        del value["stages"][1]["trigger_basis"]
        with self.assertRaisesRegex(VALIDATE.ContractError, "ocr-fallback-trigger-basis-required"):
            VALIDATE.validate(value)

    def test_outcome_cannot_own_rights_policy(self):
        value = self._load("poppler-native-pdf.json")
        value["outcome"]["policy"] = "allowed"
        with self.assertRaisesRegex(VALIDATE.ContractError, "processing-outcome-must-not-own-policy"):
            VALIDATE.validate(value)

    def test_policy_restriction_is_not_technical_execution_state(self):
        value = self._load("restricted-before-provider.json")
        value["outcome"]["execution"] = "restricted"
        with self.assertRaisesRegex(VALIDATE.ContractError, "bad-execution-state"):
            VALIDATE.validate(value)

    def test_provider_stage_requires_provider_status(self):
        value = self._load("poppler-native-pdf.json")
        del value["stages"][0]["provider_status"]
        with self.assertRaisesRegex(VALIDATE.ContractError, "provider-status-required"):
            VALIDATE.validate(value)

    def test_core_stage_cannot_have_provider_status(self):
        value = self._load("poppler-native-pdf.json")
        value["stages"][1]["provider_status"] = {
            "evidence_state": "measured",
            "value_state": "present",
            "origin": "provider-native",
            "basis": "invalid test input",
            "value": "success",
        }
        with self.assertRaisesRegex(VALIDATE.ContractError, "core-stage-must-not-have-provider-status"):
            VALIDATE.validate(value)

    def test_provider_status_does_not_mechanically_determine_stage_outcome(self):
        value = self._load("poppler-native-pdf.json")
        self.assertEqual(value["stages"][0]["provider_status"]["value"], "success")
        value["stages"][0]["outcome"]["execution"] = "failed"
        value["stages"][0]["outcome"]["derivation_basis"] = (
            "Core validation rejected malformed Provider evidence despite Provider-native success"
        )
        VALIDATE.validate(value)
        self.assertEqual(value["stages"][0]["outcome"]["execution"], "failed")

    def test_native_provider_stage_cannot_produce_normalized_representation(self):
        value = self._load("poppler-native-pdf.json")
        value["stages"][0]["produced"].append(
            {"kind": "normalized-representation", "representation_id": "invalid-native-normalized"}
        )
        with self.assertRaisesRegex(VALIDATE.ContractError, "normalized-output-requires-normalization-or-alignment"):
            VALIDATE.validate(value)

    def test_normalized_output_requires_prior_input_lineage(self):
        value = self._load("poppler-native-pdf.json")
        value["stages"][1]["input_refs"] = []
        with self.assertRaisesRegex(VALIDATE.ContractError, "normalized-output-requires-input-lineage"):
            VALIDATE.validate(value)

    def test_stage_input_must_reference_prior_output(self):
        value = self._load("poppler-native-pdf.json")
        value["stages"][1]["input_refs"] = [
            {"kind": "provider-evidence", "evidence_id": "unknown", "channel": "xml"}
        ]
        with self.assertRaisesRegex(VALIDATE.ContractError, "input-must-reference-prior-produced-output"):
            VALIDATE.validate(value)

    def test_run_produced_ref_requires_stage_producer(self):
        value = self._load("poppler-native-pdf.json")
        value["produced"].append(
            {"kind": "provider-evidence", "evidence_id": "unproduced", "channel": "diagnostic"}
        )
        with self.assertRaisesRegex(VALIDATE.ContractError, "run-produced-ref-must-have-stage-producer"):
            VALIDATE.validate(value)

    def test_explicit_empty_coordinate_requires_null_value(self):
        value = self._load("direct-epub-normalized.json")
        coordinate = value["units"][0]["coordinate"]
        coordinate.update(
            {
                "evidence_state": "measured",
                "value_state": "explicit-empty",
                "origin": "provider-native",
                "basis": "Provider explicitly exposed no coordinate",
                "value": {},
            }
        )
        with self.assertRaisesRegex(VALIDATE.ContractError, "explicit-empty-must-use-null"):
            VALIDATE.validate_representation(value)


if __name__ == "__main__":
    unittest.main()
