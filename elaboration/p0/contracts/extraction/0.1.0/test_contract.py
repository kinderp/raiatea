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

    def test_provider_and_route_identity_cannot_collapse(self):
        value = self._load("poppler-native-pdf.json")
        value["provider"]["route_profile_id"] = "pdftohtml-xml"
        with self.assertRaisesRegex(VALIDATE.ContractError, "provider-and-route-profile-must-remain-distinct"):
            VALIDATE.validate(value)

    def test_not_measured_evidence_cannot_claim_present_value(self):
        value = self._load("poppler-native-pdf.json")
        status = value["stages"][0]["provider_status"]
        status["evidence_state"] = "not-measured"
        with self.assertRaisesRegex(VALIDATE.ContractError, "not-measured-must-have-unknown-value"):
            VALIDATE.validate(value)

    def test_explicit_empty_is_not_unavailable(self):
        value = self._load("poppler-native-pdf.json")
        status = value["stages"][0]["provider_status"]
        status.update({"evidence_state": "measured", "value_state": "explicit-empty", "value": []})
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


if __name__ == "__main__":
    unittest.main()
