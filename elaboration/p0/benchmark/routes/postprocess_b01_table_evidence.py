#!/usr/bin/env python3
"""Post-process B01-PDF-005 Provider runs into conservative table evidence.

The input directory must already contain an exact-source run produced by
``measure_b01_table_evidence.py``. Poppler/Tika contribute normalized text
observations unless an inspected explicit table mapper exists. Docling adds
lossless explicit table evidence plus text reached through explicit table/group
references. Descendant text remains unbound to cells and cannot repair topology.
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
    return _load(GOLD_PATH)["fixtures"]["B01-PDF-005"]


def _score(
    observation: dict[str, Any],
    explicit_table_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from score_b01_table import measure_b01_table_dimensions

    combined = dict(observation)
    combined["blocks"] = list(observation.get("blocks", []))
    if explicit_table_evidence is not None:
        if "tables" in explicit_table_evidence:
            combined["tables"] = explicit_table_evidence["tables"]

        # Docling's generic text mapper deliberately treats a TableItem as an
        # opaque non-text leaf. The lossless table evidence mapper may still
        # expose text descendants through explicit table/group refs. Add those
        # blocks only to content-preservation scoring. They carry no row/column
        # identity and therefore cannot repair explicit topology/cell binding.
        existing_refs = {
            block.get("docling_ref") or block.get("provider_ref")
            for block in combined["blocks"]
            if isinstance(block, dict)
        }
        for block in explicit_table_evidence.get("unbound_table_text_blocks", []):
            if not isinstance(block, dict):
                continue
            ref = block.get("docling_ref") or block.get("provider_ref")
            if ref is not None and ref in existing_refs:
                continue
            combined["blocks"].append(block)
            if ref is not None:
                existing_refs.add(ref)

    return {
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "warnings": observation.get("warnings", []),
        "provider_table_evidence": explicit_table_evidence,
        "dimensions": measure_b01_table_dimensions(combined, _gold()),
    }


def postprocess_poppler(output: Path) -> list[dict[str, Any]]:
    observations = output / "observations"
    return [
        _score(_load(observations / "B01-PDF-005__pdftotext-bbox-layout.json")),
        _score(_load(observations / "B01-PDF-005__pdftohtml-xml.json")),
    ]


def postprocess_tika(output: Path) -> list[dict[str, Any]]:
    observation = _load(
        output / "observations" / "B01-PDF-005__tika-app-3.3.2-xhtml.json"
    )
    return [_score(observation)]


def postprocess_docling(output: Path) -> list[dict[str, Any]]:
    from docling_table_evidence import map_docling_table_evidence

    observation = _load(output / "observations" / "B01-PDF-005__docling.json")
    raw = _load(output / "raw" / "B01-PDF-005__docling.json")
    explicit = map_docling_table_evidence(raw)
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
            "name": "raiatea-p0-b01-table-result",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
            "no_universal_total_score": True,
        },
        "fixture_id": "B01-PDF-005",
        "provider_family": args.provider,
        "results": rows,
        "structural_policy": (
            "Provider-native explicit structure only; no spatial reconstruction or list-position identity"
        ),
        "content_policy": (
            "explicit table/group descendant text may support content preservation but never supplies cell topology"
        ),
    }
    (output / "b01-table-evidence.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
