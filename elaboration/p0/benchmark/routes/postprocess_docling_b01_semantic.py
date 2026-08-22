#!/usr/bin/env python3
"""Post-process B01-PDF-003 Docling evidence from explicit lossless JSON fields.

This helper is intentionally scoped to benchmark evidence for E-04f. It leaves
the canonical E-04e Docling mapper/runner unchanged. Only explicit Provider
fields are promoted:

- list-item ``orig`` becomes the authored surface text while the normalized
  ``text`` is retained as metadata;
- ``hyperlink`` becomes an explicit link observation.

The Provider-neutral scorer is then rerun on B01-PDF-003. No visual/layout
inference is introduced.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
MANIFEST_DIR = BENCH_DIR / "manifests"
sys.path.insert(0, str(HERE))

from score_b01 import measure_b01_fixture  # noqa: E402

FIXTURE_ID = "B01-PDF-003"
ROUTE = "docling-2.118.0-standard-pdf-native-no-ocr"


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def apply_explicit_docling_semantic_evidence(
    observation: dict[str, Any], raw_document: dict[str, Any]
) -> dict[str, Any]:
    blocks_by_ref = {
        block.get("docling_ref"): block
        for block in observation.get("blocks", [])
        if isinstance(block, dict) and block.get("docling_ref")
    }
    links: list[dict[str, Any]] = []
    texts = raw_document.get("texts", [])
    if not isinstance(texts, list):
        texts = []

    for index, item in enumerate(texts):
        if not isinstance(item, dict):
            continue
        ref = f"#/texts/{index}"
        block = blocks_by_ref.get(ref)
        provider_text = item.get("text")
        provider_orig = item.get("orig")
        label = str(item.get("label") or "").lower()

        if (
            block is not None
            and label == "list_item"
            and isinstance(provider_orig, str)
            and provider_orig.strip()
        ):
            authored_surface = _normalize_text(provider_orig)
            normalized_surface = _normalize_text(str(block.get("text", "")))
            if authored_surface and authored_surface != normalized_surface:
                block["provider_normalized_text"] = normalized_surface
                block["provider_surface_source"] = "docling-lossless-orig"
                block["text"] = authored_surface

        hyperlink = item.get("hyperlink")
        if isinstance(hyperlink, str) and hyperlink.strip():
            target = hyperlink.strip()
            from_text = None
            if isinstance(provider_orig, str) and provider_orig.strip():
                from_text = _normalize_text(provider_orig)
            elif isinstance(provider_text, str) and provider_text.strip():
                from_text = _normalize_text(provider_text)
            links.append(
                {
                    "kind": "uri"
                    if target.startswith(("http://", "https://"))
                    else "other",
                    "target": target,
                    "from_text": from_text,
                    "docling_ref": ref,
                    "source": "docling-lossless-hyperlink",
                }
            )

    observation["links"] = links
    observation.setdefault("warnings", []).append(
        {
            "code": "docling-semantic-postprocess",
            "details": (
                "B01-PDF-003 benchmark-only postprocess uses explicit lossless "
                "orig/hyperlink fields; no visual or typography inference."
            ),
        }
    )
    return observation


def postprocess(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    raw_path = output_dir / "raw" / f"{FIXTURE_ID}__docling.json"
    observation_path = output_dir / "observations" / f"{FIXTURE_ID}__docling.json"
    results_path = output_dir / "docling-b01-results.json"
    if not raw_path.is_file() or not observation_path.is_file() or not results_path.is_file():
        raise FileNotFoundError("Docling baseline output is incomplete for semantic postprocessing")

    raw_document = json.loads(raw_path.read_text(encoding="utf-8"))
    observation = json.loads(observation_path.read_text(encoding="utf-8"))
    report = json.loads(results_path.read_text(encoding="utf-8"))
    gold = json.loads((MANIFEST_DIR / "gold.json").read_text(encoding="utf-8"))

    apply_explicit_docling_semantic_evidence(observation, raw_document)
    rescored = measure_b01_fixture(
        FIXTURE_ID,
        observation,
        gold["fixtures"][FIXTURE_ID],
    )

    previous = next(
        (item for item in report.get("results", []) if item.get("fixture_id") == FIXTURE_ID),
        {},
    )
    for key in (
        "fixture_sha256",
        "provider_conversion_status",
        "page_structure_observed",
        "bbox_structure_observed",
        "body_order_source",
        "model_payload_manifest_sha256",
        "cache_delta_file_count",
        "cache_delta_files",
        "route_options",
    ):
        if key in previous:
            rescored[key] = previous[key]

    supplement = {
        "contract": {
            "name": "raiatea-p0-b01-docling-semantic-supplement",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
        },
        "evidence_source_commit": report.get("evidence_source_commit"),
        "fixture_id": FIXTURE_ID,
        "route": ROUTE,
        "explicit_evidence_policy": {
            "list_surface": "docling lossless orig for explicit list_item only",
            "links": "docling lossless hyperlink only",
            "visual_inference": False,
        },
        "observation": observation,
        "result": rescored,
        "decision_boundary": report.get("decision_boundary", {}),
        "rights_state": report.get("rights_state", {}),
    }

    semantic_observation_path = (
        output_dir / "observations" / f"{FIXTURE_ID}__docling-semantic.json"
    )
    semantic_observation_path.write_text(
        json.dumps(observation, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    supplement_path = output_dir / "docling-b01-semantic-supplement.json"
    supplement_path.write_text(
        json.dumps(supplement, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return supplement


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    supplement = postprocess(args.output)
    print(json.dumps(supplement, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
