#!/usr/bin/env python3
"""Run B01-PDF-004 through the already-pinned B-01 reference routes.

This evidence helper intentionally reuses the accepted Poppler, Tika and Docling
baseline implementations while constraining their fixture list to the authored
figure/caption fixture. Figure dimensions remain benchmark-only and independent;
no Provider or public E-05 contract is selected here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
GOLD_PATH = BENCH_DIR / "manifests" / "gold.json"
FIGURE_FIXTURES = ["B01-PDF-004"]


def _limit_to_figure_fixture(module: Any) -> None:
    """Constrain an existing reference runner without changing its canonical defaults."""
    module.B01_NORMAL_FIXTURES = list(FIGURE_FIXTURES)


def _gold() -> dict[str, Any]:
    return json.loads(GOLD_PATH.read_text(encoding="utf-8"))["fixtures"]["B01-PDF-004"]


def _load_observation(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_figure_results(output: Path, provider: str, rows: list[dict[str, Any]]) -> None:
    payload = {
        "contract": {
            "name": "raiatea-p0-b01-figure-result",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
            "no_universal_total_score": True,
        },
        "fixture_id": "B01-PDF-004",
        "provider_family": provider,
        "results": rows,
        "association_policy": "explicit Provider-originated relation evidence only; never spatial proximity",
    }
    (output / "b01-figure-evidence.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _scored_row(
    observation: dict[str, Any],
    provider_figure_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from score_b01_figure import measure_b01_figure_dimensions

    combined = dict(observation)
    if provider_figure_evidence is not None:
        if "figures" in provider_figure_evidence:
            combined["figures"] = provider_figure_evidence["figures"]
        if provider_figure_evidence.get("figure_caption_relations") is not None:
            combined["figure_caption_relations"] = provider_figure_evidence[
                "figure_caption_relations"
            ]
    return {
        "route": observation.get("route"),
        "route_status": observation.get("status"),
        "warnings": observation.get("warnings", []),
        "provider_figure_evidence": provider_figure_evidence,
        "dimensions": measure_b01_figure_dimensions(combined, _gold()),
    }


def run_poppler(output: Path, evidence_source_commit: str | None) -> dict[str, Any]:
    import measure_b01
    from poppler_figure_evidence import run_pdftohtml_figure_evidence

    _limit_to_figure_fixture(measure_b01)
    report = measure_b01.run_baseline(
        output,
        evidence_source_commit=evidence_source_commit,
    )
    observations = output / "observations"
    pdftotext = _load_observation(
        observations / "B01-PDF-004__pdftotext-bbox-layout.json"
    )
    pdftohtml = _load_observation(
        observations / "B01-PDF-004__pdftohtml-xml.json"
    )
    explicit_images = run_pdftohtml_figure_evidence(
        output / "fixtures" / "B01-PDF-004.pdf"
    )
    _write_figure_results(
        output,
        "poppler",
        [
            _scored_row(pdftotext),
            _scored_row(pdftohtml, explicit_images),
        ],
    )
    return report


def run_tika(
    output: Path,
    tika_jar: Path,
    config: Path,
    evidence_source_commit: str | None,
    java_executable: str,
) -> dict[str, Any]:
    import measure_tika_b01

    _limit_to_figure_fixture(measure_tika_b01)
    report = measure_tika_b01.run_baseline(
        output,
        jar_path=tika_jar,
        config_path=config,
        java_executable=java_executable,
        evidence_source_commit=evidence_source_commit,
    )
    observation = _load_observation(
        output / "observations" / "B01-PDF-004__tika-app-3.3.2-xhtml.json"
    )
    _write_figure_results(output, "tika", [_scored_row(observation)])
    return report


def run_docling(
    output: Path,
    artifacts_path: Path,
    cache_root: Path,
    evidence_source_commit: str | None,
) -> dict[str, Any]:
    import measure_docling_b01

    _limit_to_figure_fixture(measure_docling_b01)
    report = measure_docling_b01.run_baseline(
        output,
        artifacts_path=artifacts_path,
        cache_root=cache_root,
        evidence_source_commit=evidence_source_commit,
    )
    observation = _load_observation(
        output / "observations" / "B01-PDF-004__docling.json"
    )
    # Picture-specific Docling evidence is added only after inspecting the pinned
    # lossless JSON shape. Until then, missing figure evidence remains explicit.
    _write_figure_results(output, "docling", [_scored_row(observation)])
    return report


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
