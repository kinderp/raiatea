from __future__ import annotations

import unittest

from prototype.p0_vs1 import docling_reference
from prototype.p0_vs1.docling_product_parser import map_docling_document


SOURCE_REF = "source-ref:" + "1" * 64
FINGERPRINT = "sha256:" + "a" * 64


def provider() -> dict:
    return {
        "provider_id": "docling",
        "version": docling_reference.DOCLING_VERSION,
        "wheel_sha256": "sha256:" + docling_reference.DOCLING_WHEEL_SHA256,
        "environment_freeze_sha256": "sha256:" + docling_reference.ENVIRONMENT_FREEZE_SHA256,
        "model_payload_sha256": "sha256:" + docling_reference.MODEL_PAYLOAD_SHA256,
    }


def document() -> dict:
    return {
        "pages": {},
        "body": {"children": [{"$ref": "#/texts/0"}]},
        "texts": [
            {
                "label": "list_item",
                "orig": "1. First item",
                "text": "First item",
                "prov": [],
            }
        ],
        "pictures": [],
    }


class Pdf1cSurfacePolicyTests(unittest.TestCase):
    def test_list_item_prefers_explicit_lossless_orig_surface(self) -> None:
        bundle = map_docling_document(
            document(),
            source_ref_id=SOURCE_REF,
            source_fingerprint=FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        block = bundle["observation"]["blocks"][0]
        self.assertEqual(block["provider_label"], "list_item")
        self.assertEqual(block["text"], "1. First item")
        self.assertEqual(block["semantic_type"], "list_item")

    def test_non_list_item_keeps_docling_text_not_orig_override(self) -> None:
        doc = document()
        doc["texts"][0]["label"] = "text"
        doc["texts"][0]["orig"] = "Visible raw form"
        doc["texts"][0]["text"] = "Docling normalized text"
        bundle = map_docling_document(
            doc,
            source_ref_id=SOURCE_REF,
            source_fingerprint=FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        self.assertEqual(
            bundle["observation"]["blocks"][0]["text"],
            "Docling normalized text",
        )

    def test_explicit_docling_semantic_mismatch_is_not_corrected_from_gold_knowledge(self) -> None:
        doc = document()
        doc["texts"][0] = {
            "label": "section_header",
            "orig": "Raiatea benchmark link",
            "text": "Raiatea benchmark link",
            "prov": [],
        }
        bundle = map_docling_document(
            doc,
            source_ref_id=SOURCE_REF,
            source_fingerprint=FINGERPRINT,
            provider=provider(),
            provider_conversion_status="ConversionStatus.SUCCESS",
        )
        block = bundle["observation"]["blocks"][0]
        self.assertEqual(block["provider_label"], "section_header")
        self.assertEqual(block["semantic_type"], "heading")
        self.assertIsNone(block["semantic_level"])
        self.assertEqual(block["text"], "Raiatea benchmark link")


if __name__ == "__main__":
    unittest.main()
