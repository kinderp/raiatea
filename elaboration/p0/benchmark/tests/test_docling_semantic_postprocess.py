from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_docling_semantic_postprocess",
    ROUTES_DIR / "postprocess_docling_b01_semantic.py",
)
POST = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(POST)


class DoclingSemanticPostprocessTests(unittest.TestCase):
    def test_list_orig_and_hyperlink_are_promoted_only_from_explicit_fields(self):
        observation = {
            "blocks": [
                {
                    "docling_ref": "#/texts/0",
                    "semantic_type": "list-item",
                    "text": "First list item.",
                },
                {
                    "docling_ref": "#/texts/1",
                    "semantic_type": "heading",
                    "text": "Raiatea benchmark link",
                },
            ],
            "warnings": [],
        }
        raw = {
            "texts": [
                {
                    "label": "list_item",
                    "text": "First list item.",
                    "orig": "1. First list item.",
                    "hyperlink": None,
                },
                {
                    "label": "section_header",
                    "text": "Raiatea benchmark link",
                    "orig": "Raiatea benchmark link",
                    "hyperlink": "https://example.invalid/raiatea-benchmark",
                },
            ]
        }

        result = POST.apply_explicit_docling_semantic_evidence(observation, raw)
        first = result["blocks"][0]
        self.assertEqual(first["text"], "1. First list item.")
        self.assertEqual(first["provider_normalized_text"], "First list item.")
        self.assertEqual(first["provider_surface_source"], "docling-lossless-orig")
        self.assertEqual(
            result["links"],
            [
                {
                    "kind": "uri",
                    "target": "https://example.invalid/raiatea-benchmark",
                    "from_text": "Raiatea benchmark link",
                    "docling_ref": "#/texts/1",
                    "source": "docling-lossless-hyperlink",
                }
            ],
        )

    def test_orig_is_not_used_to_rewrite_non_list_semantics(self):
        observation = {
            "blocks": [
                {
                    "docling_ref": "#/texts/0",
                    "semantic_type": "paragraph",
                    "text": "Normalized paragraph",
                }
            ],
            "warnings": [],
        }
        raw = {
            "texts": [
                {
                    "label": "text",
                    "text": "Normalized paragraph",
                    "orig": "Different authored paragraph",
                }
            ]
        }
        result = POST.apply_explicit_docling_semantic_evidence(observation, raw)
        self.assertEqual(result["blocks"][0]["text"], "Normalized paragraph")
        self.assertNotIn("provider_normalized_text", result["blocks"][0])

    def test_no_hyperlink_means_explicit_empty_link_collection(self):
        observation = {
            "blocks": [
                {
                    "docling_ref": "#/texts/0",
                    "semantic_type": "paragraph",
                    "text": "No link",
                }
            ],
            "warnings": [],
        }
        raw = {"texts": [{"label": "text", "text": "No link", "hyperlink": None}]}
        result = POST.apply_explicit_docling_semantic_evidence(observation, raw)
        self.assertEqual(result["links"], [])


if __name__ == "__main__":
    unittest.main()
