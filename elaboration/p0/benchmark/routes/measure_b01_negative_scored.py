#!/usr/bin/env python3
"""Run the exact B01 negative raw route, then score its security/failure outcome."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from typing import Any

import measure_b01_negative_raw as raw
from score_b01_negative import score_raw_report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="provider", required=True)
    for name in ("poppler", "tika", "docling"):
        child = sub.add_parser(name)
        child.add_argument("--output", type=Path, required=True)
        child.add_argument("--qpdf", default="qpdf")
        child.add_argument("--evidence-source-commit")
        if name == "tika":
            child.add_argument("--tika-jar", type=Path, required=True)
            child.add_argument("--config", type=Path, required=True)
            child.add_argument("--java", default="java")
        if name == "docling":
            child.add_argument("--artifacts-path", type=Path, required=True)
            child.add_argument("--cache-root", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    output = args.output.resolve()
    kwargs: dict[str, Any] = {
        "provider": args.provider,
        "output": output,
        "qpdf_executable": args.qpdf,
        "evidence_source_commit": args.evidence_source_commit,
    }
    if args.provider == "tika":
        kwargs.update(
            tika_jar=args.tika_jar.resolve(),
            config=args.config.resolve(),
            java_executable=args.java,
        )
    elif args.provider == "docling":
        kwargs.update(
            artifacts_path=args.artifacts_path.resolve(),
            cache_root=args.cache_root.resolve(),
        )

    # The raw runner persists its own canonical JSON file and also prints it.
    # Suppress only that duplicate stdout so this scored CLI emits exactly one
    # valid JSON document; raw evidence remains unchanged on disk.
    with redirect_stdout(io.StringIO()):
        raw_report = raw.run(**kwargs)

    scored = score_raw_report(raw_report)
    scored_path = output / f"b01-negative-{args.provider}-scored.json"
    scored_path.write_text(
        json.dumps(scored, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(scored, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
