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


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _bind_single_explicit_relation_to_gold(
    provider_evidence: dict[str, Any],
    gold_fixture: dict[str, Any],
) -> bool:
    """Bind one explicit Provider relation only when identity is unambiguous.

    B01-PDF-004 intentionally has one authored figure and one authored caption.
    Cardinality alone is insufficient: the Provider must expose exactly one
    explicit picture relation, that relation must point to the sole Provider
    figure, and its caption text must exactly match the authored caption after
    whitespace normalization. This keeps the benchmark from crediting a wrong
    semantic relation merely because both sides happen to contain one item.
    """
    provider_figures = provider_evidence.get("figures")
    provider_relations = provider_evidence.get("figure_caption_relations")
    gold_figures = gold_fixture.get("figures")
    gold_relations = gold_fixture.get("figure_caption_relations")
    gold_units = gold_fixture.get("reference_units")

    if not all(
        isinstance(value, list)
        for value in (
            provider_figures,
            provider_relations,
            gold_figures,
            gold_relations,
            gold_units,
        )
    ):
        return False
    if not (
        len(provider_figures) == 1
        and len(provider_relations) == 1
        and len(gold_figures) == 1
        and len(gold_relations) == 1
    ):
        return False

    provider_figure = provider_figures[0]
    provider_relation = provider_relations[0]
    gold_figure = gold_figures[0]
    gold_relation = gold_relations[0]
    if not all(
        isinstance(value, dict)
        for value in (provider_figure, provider_relation, gold_figure, gold_relation)
    ):
        return False
    if gold_relation.get("figure_id") != gold_figure.get("id"):
        return False

    gold_caption_id = gold_relation.get("caption_unit")
    gold_caption = next(
        (
            unit
            for unit in gold_units
            if isinstance(unit, dict) and unit.get("id") == gold_caption_id
        ),
        None,
    )
    if not isinstance(gold_caption, dict):
        return False

    provider_ref = provider_figure.get("provider_ref")
    provider_relation_ref = provider_relation.get("provider_figure_ref")
    provider_caption_text = provider_relation.get("caption_text")
    expected_caption_text = gold_caption.get("text")
    relation_source = provider_relation.get("provider_relation_source")
    if not all(
        isinstance(value, str) and value
        for value in (
            provider_ref,
            provider_relation_ref,
            provider_caption_text,
            expected_caption_text,
            relation_source,
        )
    ):
        return False
    if provider_relation_ref != provider_ref:
        return False
    if _normalize_text(provider_caption_text) != _normalize_text(expected_caption_text):
        return False

    provider_relation["gold_figure_id"] = gold_figure.get("id")
    provider_relation["gold_caption_unit"] = gold_caption_id
    provider_relation["gold_matching_basis"] = (
        "single-explicit-figure-plus-exact-caption-text"
    )
    return True


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
    combined["blocks"] = list(observation.get("blocks", []))
    if provider_figure_evidence is not None:
        if "figures" in provider_figure_evidence:
            combined["figures"] = provider_figure_evidence["figures"]
        caption_blocks = provider_figure_evidence.get("caption_blocks")
        if isinstance(caption_blocks, list):
            combined["blocks"].extend(caption_blocks)
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
    from docling_figure_evidence import map_docling_figure_evidence

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
    raw_document = _load_observation(
        output / "raw" / "B01-PDF-004__docling.json"
    )
    explicit_picture = map_docling_figure_evidence(raw_document)

    if explicit_picture.get("status") == "success":
        if not _bind_single_explicit_relation_to_gold(explicit_picture, _gold()):
            explicit_picture.setdefault("warnings", []).append(
                {
                    "code": "docling-figure-gold-binding-ambiguous",
                    "details": (
                        "Expected one explicit Provider picture/caption relation with exact "
                        "authored caption text; relation remains unbound and cannot receive "
                        "figure-caption association credit."
                    ),
                }
            )

    _write_figure_results(
        output,
        "docling",
        [_scored_row(observation, explicit_picture)],
    )
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
