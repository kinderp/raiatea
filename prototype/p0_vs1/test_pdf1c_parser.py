from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1 import docling_reference
from prototype.p0_vs1.docling_product_parser import (
    DoclingProductError,
    failed_docling_observation,
    map_docling_document,
    run_docling_pdf,
)


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


def document() -> dict:
    return {
        "pages": {
            "1": {
                "page_no": 1,
                "size": {"width": 612.0, "height": 792.0},
            }
        },
        "body": {
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/groups/0"},
            ]
        },
        "groups": [
            {
                "children": [
                    {"$ref": "#/texts/2"},
                    {"$ref": "#/texts/3"},
                ]
            }
        ],
        "texts": [
            {
                "label": "title",
                "text": "Raiatea PDF",
                "prov": prov(1, 72, 50, 220, 80),
            },
            {
                "label": "caption",
                "text": "Figure 1. Explicit caption.",
                "prov": prov(1, 72, 330, 260, 350),
            },
            {
                "label": "section_header",
                "level": 3,
                "text": "Nested section",
                "prov": prov(1, 72, 120, 220, 145),
            },
            {
                "label": "list_item",
                "text": "First item",
                "prov": [],
            },
            {
                "label": "mystery",
                "text": "Not in body",
                "prov": [],
            },
        ],
        "pictures": [
            {
                "self_ref": "#/pictures/0",
                "label": "picture",
                "prov": prov(1, 72, 170, 252, 290),
                "captions": [{"$ref": "#/texts/1"}],
            }
        ],
    }


class Pdf1cDoclingParserTests(unittest.TestCase):
    def map(
        self,
        doc: dict | None = None,
        status: str = "ConversionStatus.SUCCESS",
    ) -> dict:
        return map_docling_document(
            document() if doc is None else doc,
            source_ref_id=SOURCE_REF,
            source_fingerprint=SOURCE_FINGERPRINT,
            provider=provider(),
            provider_conversion_status=status,
        )

    def test_body_order_semantics_and_top_left_geometry_are_preserved(self) -> None:
        bundle = self.map()
        observation = bundle["observation"]
        self.assertEqual(observation["body_order_source"], "body.children")
        self.assertEqual(
            [
                (row["text"], row["semantic_type"], row["semantic_level"])
                for row in observation["blocks"]
            ],
            [
                ("Raiatea PDF", "heading", None),
                ("Nested section", "heading", 3),
                ("First item", "list_item", None),
            ],
        )
        self.assertEqual(
            observation["blocks"][0]["coordinate"],
            {
                "page_index": 0,
                "bbox_points_bottom_left": [72.0, 712.0, 220.0, 742.0],
            },
        )
        self.assertIsNone(observation["blocks"][2]["coordinate"])
        self.assertEqual(
            observation["blocks"][2]["provenance_source"],
            "docling-lossless-item",
        )

    def test_title_numeric_level_requires_explicit_provider_level(self) -> None:
        without_level = self.map()["observation"]["blocks"][0]
        self.assertEqual(without_level["provider_label"], "title")
        self.assertEqual(without_level["semantic_type"], "heading")
        self.assertIsNone(without_level["semantic_level"])

        doc = document()
        doc["texts"][0]["level"] = 1
        with_level = self.map(doc)["observation"]["blocks"][0]
        self.assertEqual(with_level["semantic_type"], "heading")
        self.assertEqual(with_level["semantic_level"], 1)

    def test_provider_text_surface_is_not_whitespace_normalized_in_observation(self) -> None:
        doc = document()
        doc["texts"][0]["text"] = "Raiatea   PDF\nTitle"
        row = self.map(doc)["observation"]["blocks"][0]
        self.assertEqual(row["text"], "Raiatea   PDF\nTitle")

    def test_picture_caption_relation_is_explicit_without_invented_body_order(self) -> None:
        observation = self.map()["observation"]
        self.assertEqual(observation["picture_collection_state"], "present")
        self.assertEqual(len(observation["pictures"]), 1)
        self.assertEqual(len(observation["caption_blocks"]), 1)
        self.assertEqual(
            observation["caption_blocks"][0]["provider_ref"],
            "#/texts/1",
        )
        self.assertEqual(
            observation["picture_caption_relations"][0]["relation_source"],
            "docling-picture.captions-explicit-ref",
        )
        self.assertNotIn(
            "#/texts/1",
            {row["provider_ref"] for row in observation["blocks"]},
        )

    def test_missing_picture_collection_is_unknown_not_explicit_zero(self) -> None:
        doc = document()
        doc.pop("pictures")
        observation = self.map(doc)["observation"]
        self.assertEqual(observation["picture_collection_state"], "unavailable")
        self.assertEqual(observation["pictures"], [])
        self.assertTrue(
            any(
                row["code"] == "docling-picture-collection-unavailable"
                for row in observation["warnings"]
            )
        )

    def test_malformed_picture_item_marks_collection_degraded(self) -> None:
        doc = document()
        doc["pictures"].append("invalid")
        observation = self.map(doc)["observation"]
        self.assertEqual(observation["picture_collection_state"], "degraded")
        self.assertEqual(len(observation["pictures"]), 1)

    def test_texts_fallback_is_explicit_when_body_order_missing(self) -> None:
        doc = document()
        doc.pop("body")
        observation = self.map(doc)["observation"]
        self.assertEqual(observation["body_order_source"], "texts-fallback")
        self.assertTrue(
            any(
                row["code"] == "docling-body-order-unavailable"
                for row in observation["warnings"]
            )
        )

    def test_unknown_label_remains_semantically_unknown(self) -> None:
        doc = document()
        doc["body"]["children"].append({"$ref": "#/texts/4"})
        observation = self.map(doc)["observation"]
        row = observation["blocks"][-1]
        self.assertEqual(row["provider_label"], "mystery")
        self.assertIsNone(row["semantic_type"])
        self.assertIsNone(row["semantic_level"])

    def test_partial_provider_status_is_degraded_not_promoted_to_success(self) -> None:
        observation = self.map(status="ConversionStatus.PARTIAL_SUCCESS")[
            "observation"
        ]
        self.assertEqual(observation["status"], "degraded")
        self.assertTrue(observation["blocks"])

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
            with self.assertRaisesRegex(
                DoclingProductError,
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
