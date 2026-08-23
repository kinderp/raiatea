#!/usr/bin/env python3
"""Run B01-PDF-005 through the already-pinned B-01 reference routes.

This helper is deliberately evidence-first. It constrains the accepted Poppler,
Tika and Docling B-01 runners to the authored table fixture and preserves their
raw/normalized observations for inspection. It does not score table structure
and does not define the future E-05 public extraction contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TABLE_FIXTURES = ["B01-PDF-005"]


def _limit_to_table_fixture(module: Any) -> None:
    """Constrain an existing reference runner without changing its defaults."""
    module.B01_NORMAL_FIXTURES = list(TABLE_FIXTURES)


def run_poppler(output: Path, evidence_source_commit: str | None) -> dict[str, Any]:
    import measure_b01

    _limit_to_table_fixture(measure_b01)
    return measure_b01.run_baseline(
        output,
        evidence_source_commit=evidence_source_commit,
    )


def run_tika(
    output: Path,
    tika_jar: Path,
    config: Path,
    evidence_source_commit: str | None,
    java_executable: str,
) -> dict[str, Any]:
    import measure_tika_b01

    _limit_to_table_fixture(measure_tika_b01)
    return measure_tika_b01.run_baseline(
        output,
        jar_path=tika_jar,
        config_path=config,
        java_executable=java_executable,
        evidence_source_commit=evidence_source_commit,
    )


def run_docling(
    output: Path,
    artifacts_path: Path,
    cache_root: Path,
    evidence_source_commit: str | None,
) -> dict[str, Any]:
    import measure_docling_b01

    _limit_to_table_fixture(measure_docling_b01)
    return measure_docling_b01.run_baseline(
        output,
        artifacts_path=artifacts_path,
        cache_root=cache_root,
        evidence_source_commit=evidence_source_commit,
    )


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
    if args.provider == "poppler":
        report = run_poppler(args.output.resolve(), args.evidence_source_commit)
    elif args.provider == "tika":
        report = run_tika(
            args.output.resolve(),
            args.tika_jar.resolve(),
            args.config.resolve(),
            args.evidence_source_commit,
            args.java,
        )
    else:
        report = run_docling(
            args.output.resolve(),
            args.artifacts_path.resolve(),
            args.cache_root.resolve(),
            args.evidence_source_commit,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
