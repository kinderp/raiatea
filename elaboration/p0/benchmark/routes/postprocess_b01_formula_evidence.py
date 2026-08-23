#!/usr/bin/env python3
"""Post-process B01-PDF-006 Provider runs into conservative formula evidence.

Raw Provider output remains canonical evidence. This layer measures visible glyph
surface/order/geometry separately from explicit mathematical relations. Docling's
lossless picture groups are retained diagnostically and never promoted to math.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
GOLD_PATH = BENCH_DIR / "manifests" / "gold.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gold() -> dict[str, Any]:
    return _load(GOLD_PATH)["fixtures"]["B01-PDF-006"]


def _score(
    observation: dict[str, Any],
    explicit_diagnostic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from score_b01_formula import measure_b01_formula_dimensions

    combined = dict(observation)
    raw_blocks = observation.get("blocks")
    combined["blocks"] = list(raw_blocks) if isinstance(raw_blocks, list) else raw_blocks
    if explicit_diagnostic is not None:
        for key in (
            "formula_text_collection_state",
            "provider_group_collection_state",
            "math_relation_collection_state",
        ):
            if key in explicit_diagnostic:
                combined[key] = explicit_diagnostic[key]

        if isinstance(explicit_diagnostic.get("formula_text_blocks"), list):
            combined["formula_text_blocks"] = explicit_diagnostic["formula_text_blocks"]
        if isinstance(explicit_diagnostic.get("provider_formula_groups"), list):
            combined["provider_formula_groups"] = explicit_diagnostic["provider_formula_groups"]
        if "math_relations" in explicit_diagnostic:
            combined["math_relations"] = explicit_diagnostic["math_relations"]

    return {
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "warnings": observation.get("warnings", []),
        "provider_formula_diagnostic": explicit_diagnostic,
        "dimensions": measure_b01_formula_dimensions(combined, _gold()),
    }


def postprocess_poppler(output: Path) -> list[dict[str, Any]]:
    observations = output / "observations"
    return [
        _score(_load(observations / "B01-PDF-006__pdftotext-bbox-layout.json")),
        _score(_load(observations / "B01-PDF-006__pdftohtml-xml.json")),
    ]


def postprocess_tika(output: Path) -> list[dict[str, Any]]:
    observation = _load(
        output / "observations" / "B01-PDF-006__tika-app-3.3.2-xhtml.json"
    )
    return [_score(observation)]


def postprocess_docling(output: Path) -> list[dict[str, Any]]:
    from docling_formula_evidence import map_docling_formula_evidence

    observation = _load(output / "observations" / "B01-PDF-006__docling.json")
    raw = _load(output / "raw" / "B01-PDF-006__docling.json")
    explicit = map_docling_formula_evidence(raw)
    return [_score(observation, explicit)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=["poppler", "tika", "docling"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()

    if args.provider == "poppler":
        rows = postprocess_poppler(output)
    elif args.provider == "tika":
        rows = postprocess_tika(output)
    else:
        rows = postprocess_docling(output)

    payload = {
        "contract": {
            "name": "raiatea-p0-b01-formula-result",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
            "no_universal_total_score": True,
        },
        "fixture_id": "B01-PDF-006",
        "provider_family": args.provider,
        "results": rows,
        "semantic_policy": (
            "visible glyph preservation and geometry are independent from explicit "
            "mathematical relations; no typography/position/line inference"
        ),
    }
    (output / "b01-formula-evidence.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
