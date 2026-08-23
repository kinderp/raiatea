from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("plugin_manifest_validator", ROOT / "validate_manifest.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def load_example(name: str) -> dict:
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class PluginManifestTests(unittest.TestCase):
    def test_examples_pass_semantic_validation(self):
        for name in (
            "local-read-only-source.json",
            "benchmark-backed-extractor.json",
            "minimal-transformer.json",
        ):
            VALIDATOR.validate(load_example(name))

    def test_incompatible_plugin_api_major_fails(self):
        value = load_example("local-read-only-source.json")
        value["raiatea_plugin_api"] = {"min_inclusive": "2.0.0", "max_exclusive": "3.0.0"}
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "plugin-api-incompatible"):
            VALIDATOR.validate(value)

    def test_duplicate_capability_id_fails(self):
        value = load_example("local-read-only-source.json")
        value["capabilities"].append(copy.deepcopy(value["capabilities"][0]))
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "duplicate-capability-id"):
            VALIDATOR.validate(value)

    def test_duplicate_profile_fails(self):
        value = load_example("benchmark-backed-extractor.json")
        value["capabilities"][0]["profiles"].append(copy.deepcopy(value["capabilities"][0]["profiles"][0]))
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "duplicate-capability-profile"):
            VALIDATOR.validate(value)

    def test_extractor_profile_requires_e05_contract(self):
        value = load_example("benchmark-backed-extractor.json")
        value["capabilities"][0]["profiles"][0]["contracts"] = []
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "extractor-profile-missing-e05-contract"):
            VALIDATOR.validate(value)

    def test_non_extractor_must_not_claim_extraction_contract(self):
        value = load_example("minimal-transformer.json")
        value["capabilities"][0]["profiles"][0]["contracts"] = [
            {
                "contract_id": "raiatea.extraction.processing-run",
                "version_range": {"min_inclusive": "0.1.0", "max_exclusive": "0.2.0"},
            }
        ]
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "non-extractor-must-not-own-extraction-contract"):
            VALIDATOR.validate(value)

    def test_network_wildcard_fails(self):
        value = load_example("local-read-only-source.json")
        value["permissions"]["network"] = [{"host": "*", "scopes": ["https"]}]
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "network-wildcard-forbidden"):
            VALIDATOR.validate(value)

    def test_embedded_secret_value_fails(self):
        value = load_example("local-read-only-source.json")
        value["permissions"]["secrets"] = ["TOKEN=secret"]
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "secret-value-must-not-be-embedded"):
            VALIDATOR.validate(value)

    def test_trust_tier_cannot_be_rights_authority(self):
        value = load_example("local-read-only-source.json")
        value["rights_decision"] = "allow"
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "manifest-must-not-own-rights-decision"):
            VALIDATOR.validate(value)

    def test_profile_quality_truth_is_forbidden(self):
        value = load_example("benchmark-backed-extractor.json")
        value["capabilities"][0]["profiles"][0]["quality_score"] = 1.0
        with self.assertRaisesRegex(VALIDATOR.ManifestError, "capability-profile-must-not-claim-quality-truth"):
            VALIDATOR.validate(value)

    def test_read_only_source_example_has_no_write_permission(self):
        value = load_example("local-read-only-source.json")
        self.assertEqual(value["permissions"]["network"], [])
        self.assertTrue(value["permissions"]["filesystem"])
        self.assertTrue(all(row["mode"] == "read" for row in value["permissions"]["filesystem"]))


if __name__ == "__main__":
    unittest.main()
