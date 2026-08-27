from __future__ import annotations

from copy import deepcopy
import unittest

from prototype.p0_vs1.docling_observation_contract import (
    DOCLING_OBSERVATION_VERSION,
    DOCLING_PROFILE,
    DoclingObservationError,
    encode_docling_observation_bundle,
    validate_docling_observation_bundle,
)


SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64


def valid_bundle() -> dict:
    return {
        "bundle_version": DOCLING_OBSERVATION_VERSION,
        "record_kind": "DoclingObservationBundle",
        "source_ref_id": "source-ref:" + "1" * 64,
        "source_fingerprint": SHA_A,
        "provider": {
            "provider_id": "docling",
            "version": "2.118.0",
            "wheel_sha256": SHA_B,
            "environment_freeze_sha256": SHA_C,
            "model_payload_sha256": SHA_D,
        },
        "route_profile": DOCLING_PROFILE,
        "observation": {
            "status": "success",
            "warnings": [],
            "blocks": [
                {
                    "provider_ref": "#/texts/0",
                    "text": "Introduction",
                    "provider_label": "title",
                    "semantic_type": "heading",
                    "semantic_level": 1,
                    "coordinate": {
                        "page_index": 0,
                        "bbox_points_bottom_left": [72.0, 700.0, 240.0, 730.0],
                    },
                    "provenance_source": "docling-text-provenance",
                },
                {
                    "provider_ref": "#/texts/1",
                    "text": "Figure 1. Example.",
                    "provider_label": "caption",
                    "semantic_type": "caption",
                    "semantic_level": None,
                    "coordinate": {
                        "page_index": 0,
                        "bbox_points_bottom_left": [72.0, 450.0, 260.0, 470.0],
                    },
                    "provenance_source": "docling-lossless-item",
                },
            ],
            "pictures": [
                {
                    "provider_ref": "#/pictures/0",
                    "provider_label": "picture",
                    "coordinate": {
                        "page_index": 0,
                        "bbox_points_bottom_left": [72.0, 500.0, 252.0, 620.0],
                    },
                    "provenance_source": "docling-picture-item",
                }
            ],
            "picture_caption_relations": [
                {
                    "relation_id": "relation:picture-caption:0",
                    "picture_ref": "#/pictures/0",
                    "caption_ref": "#/texts/1",
                    "relation_source": "docling-picture.captions-explicit-ref",
                }
            ],
            "raw_document_sha256": SHA_A,
        },
    }


class Pdf1cDoclingObservationContractTests(unittest.TestCase):
    def test_valid_semantic_picture_caption_bundle_is_canonical(self) -> None:
        bundle = valid_bundle()
        self.assertIs(validate_docling_observation_bundle(bundle), bundle)
        self.assertEqual(encode_docling_observation_bundle(bundle), encode_docling_observation_bundle(deepcopy(bundle)))

    def test_unknown_provider_label_cannot_gain_semantics(self) -> None:
        bundle = valid_bundle()
        bundle["observation"]["blocks"][0]["provider_label"] = "mystery_label"
        bundle["observation"]["blocks"][0]["semantic_type"] = "heading"
        with self.assertRaisesRegex(DoclingObservationError, "unmapped-label"):
            validate_docling_observation_bundle(bundle)

    def test_semantic_level_requires_heading(self) -> None:
        bundle = valid_bundle()
        bundle["observation"]["blocks"][0]["semantic_type"] = "paragraph"
        with self.assertRaisesRegex(DoclingObservationError, "semantic-level-requires-heading"):
            validate_docling_observation_bundle(bundle)

    def test_relation_must_reference_explicit_picture_and_caption(self) -> None:
        for key, value, message in (
            ("picture_ref", "#/pictures/missing", "picture-unknown"),
            ("caption_ref", "#/texts/missing", "caption-unknown"),
        ):
            with self.subTest(key=key):
                bundle = valid_bundle()
                bundle["observation"]["picture_caption_relations"][0][key] = value
                with self.assertRaisesRegex(DoclingObservationError, message):
                    validate_docling_observation_bundle(bundle)

    def test_host_path_authority_is_rejected_recursively(self) -> None:
        bundle = valid_bundle()
        bundle["observation"]["warnings"].append(
            {"code": "bad", "details": {"workspace_path": "/tmp/provider"}}
        )
        with self.assertRaisesRegex(DoclingObservationError, "host-path-field-forbidden"):
            validate_docling_observation_bundle(bundle)

    def test_non_success_cannot_carry_current_content(self) -> None:
        bundle = valid_bundle()
        bundle["observation"]["status"] = "failed"
        with self.assertRaisesRegex(DoclingObservationError, "non-success-blocks-forbidden"):
            validate_docling_observation_bundle(bundle)

    def test_missing_coordinate_stays_explicitly_unknown(self) -> None:
        bundle = valid_bundle()
        bundle["observation"]["blocks"][0]["coordinate"] = None
        validate_docling_observation_bundle(bundle)
        self.assertIsNone(bundle["observation"]["blocks"][0]["coordinate"])


if __name__ == "__main__":
    unittest.main()
