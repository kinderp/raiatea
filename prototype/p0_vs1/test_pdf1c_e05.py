from __future__ import annotations

from copy import deepcopy
import unittest

from prototype.p0_vs1.docling_e05_adapter import adapt_docling_observation
from prototype.p0_vs1.pdf1c_e05_contract import (
    DoclingPdfE05ContractError,
    build_docling_pdf_extraction_bundle,
    validate_attempt_records,
    validate_docling_pdf_extraction_bundle,
)


SOURCE_REF = "source-ref:" + "1" * 64
FINGERPRINT = "sha256:" + "a" * 64
OBSERVATION_FINGERPRINT = "sha256:" + "b" * 64


def observation(status: str = "success") -> dict:
    blocks = [
        {
            "provider_ref": "#/texts/0",
            "body_order_index": 0,
            "text": "Raiatea PDF",
            "provider_label": "title",
            "semantic_type": "heading",
            "semantic_level": 1,
            "coordinate": {
                "page_index": 0,
                "bbox_points_bottom_left": [72.0, 700.0, 220.0, 730.0],
            },
            "provenance_count": 1,
            "provenance_source": "docling-text-provenance",
        },
        {
            "provider_ref": "#/texts/2",
            "body_order_index": 1,
            "text": "First item",
            "provider_label": "list_item",
            "semantic_type": "list_item",
            "semantic_level": None,
            "coordinate": None,
            "provenance_count": 0,
            "provenance_source": "docling-lossless-item",
        },
        {
            "provider_ref": "#/texts/3",
            "body_order_index": 2,
            "text": "Unknown semantics",
            "provider_label": "mystery",
            "semantic_type": None,
            "semantic_level": None,
            "coordinate": None,
            "provenance_count": 0,
            "provenance_source": "docling-lossless-item",
        },
    ] if status in {"success", "degraded"} else []
    return {
        "status": status,
        "provider_conversion_status": (
            "ConversionStatus.SUCCESS" if status == "success" else None
        ),
        "warnings": [],
        "body_order_source": "body.children" if blocks else "unavailable",
        "blocks": blocks,
        "picture_collection_state": "present" if blocks else "unavailable",
        "pictures": [],
        "caption_blocks": [],
        "picture_caption_relations": [],
        "raw_document_sha256": OBSERVATION_FINGERPRINT if blocks else None,
    }


class Pdf1cE05Tests(unittest.TestCase):
    def adapt(self, status: str = "success") -> dict:
        return adapt_docling_observation(
            observation(status),
            source_id=SOURCE_REF,
            fingerprint=FINGERPRINT,
            provider_version="2.118.0",
            provider_observation_fingerprint=OBSERVATION_FINGERPRINT,
            started_at="2026-08-27T12:00:00Z",
            ended_at="2026-08-27T12:00:01Z",
        )

    def test_success_maps_explicit_semantics_geometry_and_reading_order(self) -> None:
        adapted = self.adapt()
        validate_attempt_records(adapted)
        representation = adapted["normalized_representation"]
        units = representation["units"]
        self.assertEqual(
            units[0]["semantic_role"]["value"],
            {"type": "heading", "level": 1},
        )
        self.assertEqual(
            units[1]["semantic_role"]["value"],
            {"type": "list_item"},
        )
        self.assertEqual(units[2]["semantic_role"]["value_state"], "unknown")
        self.assertEqual(
            units[0]["coordinate"]["value"],
            {
                "kind": "pdf-geometric",
                "page_index": 0,
                "bbox_points_bottom_left": [72.0, 700.0, 220.0, 730.0],
            },
        )
        self.assertEqual(len(representation["relations"]), 2)
        self.assertIn(
            "body.children",
            representation["relations"][0]["basis"],
        )

    def test_core_semantic_mapping_is_not_mislabeled_provider_native(self) -> None:
        units = self.adapt()["normalized_representation"]["units"]
        self.assertEqual(units[0]["surface"]["origin"], "provider-native")
        self.assertEqual(units[0]["semantic_role"]["origin"], "raiatea-aligned")
        self.assertEqual(units[1]["semantic_role"]["origin"], "raiatea-aligned")
        self.assertEqual(units[0]["coordinate"]["origin"], "raiatea-aligned")
        self.assertEqual(units[2]["semantic_role"]["origin"], "unresolved")

    def test_provider_observation_is_referenced_without_coercing_picture_schema(self) -> None:
        adapted = self.adapt()
        evidence = adapted["provider_evidence"]
        self.assertEqual(evidence["provider"]["provider_id"], "docling")
        self.assertEqual(
            evidence["payload_fingerprint"],
            OBSERVATION_FINGERPRINT,
        )
        self.assertEqual(
            evidence["payload_locator"],
            f"catalog-provider-observation:{SOURCE_REF}:pdf-docling-native-no-ocr",
        )
        self.assertNotIn("pictures", adapted["normalized_representation"])

    def test_success_builds_publishable_three_record_bundle(self) -> None:
        bundle = build_docling_pdf_extraction_bundle(
            source_ref_id=SOURCE_REF,
            source_fingerprint=FINGERPRINT,
            adapted=self.adapt(),
        )
        self.assertIs(validate_docling_pdf_extraction_bundle(bundle), bundle)
        kinds = {row["record_kind"] for row in bundle["record_refs"]}
        self.assertEqual(
            kinds,
            {
                "ProcessingRunRecord",
                "ProviderEvidenceRecord",
                "NormalizedRepresentationRecord",
            },
        )

    def test_degraded_attempt_is_not_publishable_current_content(self) -> None:
        adapted = self.adapt("degraded")
        validate_attempt_records(adapted)
        self.assertEqual(adapted["run"]["outcome"]["execution"], "unknown")
        self.assertNotIn("normalized_representation", adapted)
        with self.assertRaisesRegex(
            DoclingPdfE05ContractError,
            "run-not-publishable",
        ):
            build_docling_pdf_extraction_bundle(
                source_ref_id=SOURCE_REF,
                source_fingerprint=FINGERPRINT,
                adapted=adapted,
            )

    def test_restricted_attempt_is_rejected_without_normalized_representation(self) -> None:
        adapted = self.adapt("restricted")
        validate_attempt_records(adapted)
        self.assertEqual(adapted["run"]["outcome"]["execution"], "rejected")
        self.assertNotIn("normalized_representation", adapted)

    def test_semantic_tamper_outside_accepted_mapping_fails_wrapper(self) -> None:
        adapted = self.adapt()
        changed = deepcopy(adapted)
        changed["normalized_representation"]["units"][0]["semantic_role"][
            "value"
        ]["type"] = "table"
        with self.assertRaisesRegex(
            DoclingPdfE05ContractError,
            "semantic-type-invalid",
        ):
            validate_attempt_records(changed)


if __name__ == "__main__":
    unittest.main()
