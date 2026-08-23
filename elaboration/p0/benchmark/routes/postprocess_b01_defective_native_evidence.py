#!/usr/bin/env python3
"""Score exact-source B01-PDF-007 native/no-OCR Provider observations.

The source run remains raw evidence. This postprocessor adds benchmark-only,
gold-informed completeness/fallback dimensions without changing Provider output or
claiming a production routing heuristic.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
GOLD_PATH = BENCH_DIR / "manifests" / "b01-pdf-007-gold.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gold() -> dict[str, Any]:
    return _load(GOLD_PATH)


def _score(observation: dict[str, Any]) -> dict[str, Any]:
    from score_b01_defective_native import measure_b01_defective_native_dimensions

    return {
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "warnings": observation.get("warnings"),
        "raw_output_sha256": observation.get("raw_output_sha256"),
        "raw_output_bytes": observation.get("raw_output_bytes"),
        "dimensions": measure_b01_defective_native_dimensions(observation, _gold()),
    }


def postprocess_poppler(output: Path) -> list[dict[str, Any]]:
    observations = output / "observations"
    return [
        _score(_load(observations / "B01-PDF-007__pdftotext-bbox-layout.json")),
        _score(_load(observations / "B01-PDF-007__pdftohtml-xml.json")),
    ]


def postprocess_tika(output: Path) -> list[dict[str, Any]]:
    return [
        _score(
            _load(
                output
                / "observations"
                / "B01-PDF-007__tika-app-3.3.2-xhtml.json"
            )
        )
    ]


def postprocess_docling(output: Path) -> list[dict[str, Any]]:
    return [
        _score(_load(output / "observations" / "B01-PDF-007__docling.json"))
    ]


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
            "name": "raiatea-p0-b01-defective-native-scored-evidence",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only-separate-subprofile",
            "public_p0_schema": False,
            "no_universal_total_score": True,
        },
        "fixture_id": "B01-PDF-007",
        "provider_family": args.provider,
        "results": rows,
        "routing_policy": (
            "gold-informed benchmark fallback verdict only; production fallback must later "
            "derive from inspectable runtime evidence and preserve native/OCR provenance"
        ),
    }
    (output / "b01-defective-native-scored.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
