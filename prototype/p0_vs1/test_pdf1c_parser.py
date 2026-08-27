from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from prototype.p0_vs1 import docling_reference
from prototype.p0_vs1.docling_product_parser import (
    failed_docling_observation,
    map_docling_document,
    run_docling_pdf,
)
from prototype.p0_vs1.docling_provider_runtime import DoclingProviderRuntimeError


SOURCE_REF = "source-ref:" + "1" * 64
SOURCE_BYTES = b"%PDF-1.4\nsynthetic"
SOURCE_FINGERPRINT = "sha256:" + __import__("hashlib").sha256(SOURCE_BYTES).hexdigest()


def provider() -> dict:
    return {
        "provider_id": "docling",
        "version": docling_reference.DOCLING_VERSION,
        "wheel_sha256": "sha256:" + docling_reference.DOCLING_WHEEL_SHA256,
        "environment_freeze_sha256": "sha256:" + docling_reference.ENVIRONMENT_FREEZE_SHA256,
        "model_payload_sha256": "sha256:" + docling_reference.MODEL_PAYLOAD_SHA256,
    }


def prov(
    page_no: int,
    left: float,
    top: float,
    right: float,
    bottom: float,
) -> list[dict]:
    return [
        {
            "page_no": page_no,
            "bbox": {
                "l": left,
                "t": top,
                "r": right,
                "b": bottom,
                "coord_origin": "TOPLEFT",
            },
        }
    ]


def base_document() -> dict:
    return {
        "pages": {
            "1": {
                "size": {"width": 612.0, "height": 792.0},
            }
        },
        "body": {
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/texts/1"},
                {"$ref": "#/texts/2"},
            ]
        },
        "texts": [
            {
                "label": "title",
                "text": "Document title",
                "level": 2,
                "prov": prov(1, 72.0, 720.0, 240.0, 690.0),
            },
            {
                "label": "paragraph",
                "text": "Body paragraph",
                "prov": prov(1, 72.0, 650.0, 300.0, 620.0),
            },
            {
                "label": "list_item",
                "orig": "1. First item",
                "text": "First item",
                "prov": prov(1, 72.0, 600.0, 220.0, 580.0),
            },
        ],
        "pictures": [],
    }


class Pdf1cDoclingParserTests(unittest.TestCase):
    def test_body_order_semantics_and_top_left_geometry_are_preserved(self) -> None:
        bundle = map_docling_document(
            base_document(),
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        observation = bundle["observation"]
        self.assertEqual(observation["body_order_source"], "docling-body.children")
        self.assertEqual([row["body_order_index"] for row in observation["blocks"]], [0, 1, 2])
        self.assertEqual(observation["blocks"][0]["semantic_type"], "heading")
        self.assertEqual(observation["blocks"][0]["semantic_level"], 2)
        self.assertEqual(
            observation["blocks"][0]["coordinate"]["bbox_points_bottom_left"],
            [72.0, 72.0, 240.0, 102.0],
        )
        self.assertEqual(observation["blocks"][2]["text"], "1. First item")

    def test_unknown_label_remains_semantically_unknown(self) -> None:
        document = base_document()
        document["texts"][1]["label"] = "mystery"
        bundle = map_docling_document(
            document,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        block = bundle["observation"]["blocks"][1]
        self.assertEqual(block["provider_label"], "mystery")
        self.assertIsNone(block["semantic_type"])
        self.assertIsNone(block["semantic_level"])

    def test_title_numeric_level_requires_explicit_provider_level(self) -> None:
        document = base_document()
        document["texts"][0].pop("level")
        bundle = map_docling_document(
            document,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        block = bundle["observation"]["blocks"][0]
        self.assertEqual(block["semantic_type"], "heading")
        self.assertIsNone(block["semantic_level"])

    def test_provider_text_surface_is_not_whitespace_normalized_in_observation(self) -> None:
        document = base_document()
        document["texts"][1]["text"] = "Body   paragraph\nwith spacing"
        bundle = map_docling_document(
            document,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        self.assertEqual(
            bundle["observation"]["blocks"][1]["text"],
            "Body   paragraph\nwith spacing",
        )

    def test_texts_fallback_is_explicit_when_body_order_missing(self) -> None:
        document = base_document()
        document.pop("body")
        bundle = map_docling_document(
            document,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        observation = bundle["observation"]
        self.assertEqual(observation["body_order_source"], "docling-texts-fallback")
        self.assertTrue(any(row["code"] == "docling-body-order-unavailable" for row in observation["warnings"]))

    def test_missing_picture_collection_is_unknown_not_explicit_zero(self) -> None:
        document = base_document()
        document.pop("pictures")
        bundle = map_docling_document(
            document,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        observation = bundle["observation"]
        self.assertEqual(observation["picture_collection_state"], "unavailable")
        self.assertEqual(observation["pictures"], [])

    def test_malformed_picture_item_marks_collection_degraded(self) -> None:
        document = base_document()
        document["pictures"] = ["bad"]
        bundle = map_docling_document(
            document,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        self.assertEqual(bundle["observation"]["picture_collection_state"], "degraded")

    def test_picture_caption_relation_is_explicit_without_invented_body_order(self) -> None:
        document = base_document()
        document["texts"].append(
            {
                "label": "caption",
                "text": "Figure caption",
                "prov": prov(1, 72.0, 490.0, 250.0, 470.0),
            }
        )
        document["pictures"] = [
            {
                "label": "picture",
                "prov": prov(1, 72.0, 620.0, 252.0, 500.0),
                "captions": [{"$ref": "#/texts/3"}],
            }
        ]
        bundle = map_docling_document(
            document,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        observation = bundle["observation"]
        self.assertEqual(observation["picture_collection_state"], "present")
        self.assertEqual(len(observation["pictures"]), 1)
        self.assertEqual(len(observation["caption_blocks"]), 1)
        self.assertEqual(len(observation["picture_caption_relations"]), 1)
        self.assertNotIn("body_order_index", observation["caption_blocks"][0])

    def test_partial_provider_status_is_degraded_not_promoted_to_success(self) -> None:
        bundle = map_docling_document(
            base_document(),
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.PARTIAL_SUCCESS",
        )
        self.assertEqual(bundle["observation"]["status"], "degraded")

    def test_failed_and_restricted_attempts_are_path_free_and_have_no_current_content(self) -> None:
        for restricted in (False, True):
            with self.subTest(restricted=restricted):
                bundle = failed_docling_observation(
                    source_ref_id=SOURCE_REF,
                    source_fingerprint=SOURCE_FINGERPRINT,
                    provider=provider(),
                    restricted=restricted,
                    error_type="PdfiumError",
                )
                observation = bundle["observation"]
                self.assertEqual(
                    observation["status"],
                    "restricted" if restricted else "failed",
                )
                self.assertEqual(observation["blocks"], [])
                self.assertIsNone(observation["raw_document_sha256"])
                serialized = json.dumps(bundle, sort_keys=True)
                self.assertNotIn("/tmp/", serialized)
                self.assertNotIn("workspace_path", serialized)

    def test_run_rejects_source_fingerprint_before_importing_docling(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            artifacts = root / "models"
            artifacts.mkdir()
            cache = root / "cache"
            with mock.patch.dict("sys.modules", {"docling": None}):
                with self.assertRaisesRegex(
                    DoclingProviderRuntimeError,
                    "source-fingerprint-mismatch",
                ):
                    run_docling_pdf(
                        SOURCE_BYTES,
                        source_ref_id=SOURCE_REF,
                        source_fingerprint="sha256:" + "0" * 64,
                        provider=provider(),
                        artifacts_path=artifacts,
                        cache_root=cache,
                    )


if __name__ == "__main__":
    unittest.main()
