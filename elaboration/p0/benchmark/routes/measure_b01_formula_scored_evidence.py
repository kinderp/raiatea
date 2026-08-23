#!/usr/bin/env python3
"""Run and conservatively score B01-PDF-006 on one pinned Provider route.

Raw Provider evidence is preserved by the existing evidence-first runner. This
wrapper adds benchmark-only formula dimensions without changing Provider modes or
the authored gold.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import measure_b01_formula_evidence as raw
import postprocess_b01_formula_evidence as postprocess


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="provider", required=True)

    poppler = subparsers.add_parser("poppler")
    poppler.add_argument("--output", type=Path, required=True)
    poppler.add_argument("--evidence-source-commit")

    tika = subparsers.add_parser("tika")
    tika.add_argument("--output", type=Path, required=True)
    tika.add_argument("--tika-jar", type=Path, required=True)
    tika.add_argument("--config", type=Path, required=True)
    tika.add_argument("--java", default="java")
    tika.add_argument("--evidence-source-commit")

    docling = subparsers.add_parser("docling")
    docling.add_argument("--output", type=Path, required=True)
    docling.add_argument("--artifacts-path", type=Path, required=True)
    docling.add_argument("--cache-root", type=Path, required=True)
    docling.add_argument("--evidence-source-commit")
    return parser


def main() -> int:
    args = _parser().parse_args()
    output = args.output.resolve()

    if args.provider == "poppler":
        raw.run_poppler(output, args.evidence_source_commit)
        rows = postprocess.postprocess_poppler(output)
    elif args.provider == "tika":
        raw.run_tika(
            output,
            args.tika_jar.resolve(),
            args.config.resolve(),
            args.evidence_source_commit,
            args.java,
        )
        rows = postprocess.postprocess_tika(output)
    else:
        raw.run_docling(
            output,
            args.artifacts_path.resolve(),
            args.cache_root.resolve(),
            args.evidence_source_commit,
        )
        rows = postprocess.postprocess_docling(output)

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
