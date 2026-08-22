#!/usr/bin/env python3
"""Run B01-PDF-004 through the already-pinned B-01 reference routes.

This evidence helper intentionally reuses the accepted Poppler, Tika and Docling
baseline implementations while constraining their fixture list to the authored
figure/caption fixture. It does not define E-05 and does not select a Provider.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FIGURE_FIXTURES = ["B01-PDF-004"]


def _limit_to_figure_fixture(module: Any) -> None:
    """Constrain an existing reference runner without changing its canonical defaults."""
    module.B01_NORMAL_FIXTURES = list(FIGURE_FIXTURES)


def run_poppler(output: Path, evidence_source_commit: str | None) -> dict[str, Any]:
    import measure_b01

    _limit_to_figure_fixture(measure_b01)
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

    _limit_to_figure_fixture(measure_tika_b01)
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

    _limit_to_figure_fixture(measure_docling_b01)
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
