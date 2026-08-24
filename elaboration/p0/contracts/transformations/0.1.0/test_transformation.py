from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("transformation_validator", ROOT / "validate_transformation.py")
V = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(V)


def refs():
    source = {
        "artifact_id": "artifact:source:1",
        "handle_id": "handle:source:1",
        "fingerprint": V.sha256_bytes(b"a\r\nb\r"),
        "media_type": "text/plain; charset=utf-8",
        "byte_length": 5,
    }
    output = {
        "artifact_id": "artifact:derived:1",
        "handle_id": "handle:derived:1",
        "fingerprint": V.sha256_bytes(b"a\nb\n"),
        "media_type": "text/plain; charset=utf-8",
        "byte_length": 4,
    }
    return source, output


def records():
    source, output = refs()
    transformation = {
        "schema_version": "0.1.0",
        "record_kind": "TransformationRecord",
        "transformation_id": "transform:1",
        "invocation_id": "invoke:1",
        "operation": {
            "plugin_id": "org.raiatea.newline-transformer-proof",
            "plugin_version": "0.1.0",
            "capability_id": "transform.run",
            "profile_id": "normalize-newlines-v1",
            "operation_id": "normalize-newlines",
            "operation_version": "1",
        },
        "input_artifact": source,
        "output_artifact": output,
        "parameters": {},
        "deterministic": True,
        "started_at": "2026-08-24T10:00:00Z",
        "ended_at": "2026-08-24T10:00:01Z",
        "rights_decision_ref": "rights:test:1",
    }
    derived = {
        "schema_version": "0.1.0",
        "record_kind": "DerivedArtifactRecord",
        "artifact": output,
        "derivation": {
            "relationship": "derived-from",
            "source_artifact": source,
            "transformation_id": "transform:1",
        },
    }
    return transformation, derived


class TransformationContractTests(unittest.TestCase):
    def test_valid_pair_and_bytes(self):
        transformation, derived = records()
        V.validate_pair(transformation, derived)
        V.validate_bytes(transformation["input_artifact"], b"a\r\nb\r", "input")
        V.validate_bytes(transformation["output_artifact"], b"a\nb\n", "output")

    def test_same_artifact_identity_fails(self):
        transformation, derived = records()
        transformation["output_artifact"]["artifact_id"] = transformation["input_artifact"]["artifact_id"]
        with self.assertRaisesRegex(V.TransformationContractError, "derived-artifact-identity-must-differ"):
            V.validate_transformation(transformation)

    def test_missing_derived_from_fails(self):
        transformation, derived = records()
        derived["derivation"]["relationship"] = "replaces"
        with self.assertRaisesRegex(V.TransformationContractError, "derived-from-relationship-required"):
            V.validate_derived_artifact(derived)

    def test_lineage_source_mismatch_fails(self):
        transformation, derived = records()
        derived["derivation"]["source_artifact"]["artifact_id"] = "artifact:other"
        with self.assertRaisesRegex(V.TransformationContractError, "lineage-source-artifact-mismatch"):
            V.validate_pair(transformation, derived)

    def test_output_fingerprint_mismatch_fails(self):
        transformation, _ = records()
        transformation["output_artifact"]["fingerprint"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(V.TransformationContractError, "output-fingerprint-mismatch"):
            V.validate_bytes(transformation["output_artifact"], b"a\nb\n", "output")

    def test_rights_authority_field_fails(self):
        transformation, _ = records()
        transformation["rights_grant"] = "allow"
        with self.assertRaisesRegex(V.TransformationContractError, "must-not-own-rights-authority"):
            V.validate_transformation(transformation)

    def test_host_path_in_artifact_ref_fails(self):
        transformation, _ = records()
        transformation["output_artifact"]["host_path"] = "/tmp/out.txt"
        with self.assertRaisesRegex(V.TransformationContractError, "forbidden-field:host_path"):
            V.validate_transformation(transformation)


if __name__ == "__main__":
    unittest.main()
