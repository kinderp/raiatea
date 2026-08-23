#!/usr/bin/env python3
"""Run B01-PDF-007 through unchanged pinned native/no-OCR B-01 routes.

Evidence-first only: this helper preserves raw/normalized Provider observations
without deciding whether OCR fallback is needed. Completeness/fallback scoring is
a later step after raw evidence inspection.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(HERE))

import b01_pdf_007_fixture as fixture  # noqa: E402
from docling_routes import run_docling_pdf_json  # noqa: E402
from pdf_routes import (  # noqa: E402
    executable_version,
    run_pdftohtml_xml,
    run_pdftotext_bbox_layout,
)
from tika_routes import run_tika_pdf_xhtml, verify_tika_jar  # noqa: E402


CONTRACT = {
    "name": "raiatea-p0-b01-defective-native-raw-evidence",
    "version": "0.1.0",
    "scope": "benchmark-evidence-only-separate-subprofile",
    "public_p0_schema": False,
    "no_fallback_decision_yet": True,
}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _materialize_fixture(output: Path) -> Path:
    fixture_dir = output / "fixture"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    source = fixture_dir / "B01-PDF-007.pdf"
    source.write_bytes(fixture.build_fixture())
    observed = fixture.evidence()
    if observed["pdf_sha256"] != fixture.EXPECTED_PDF_SHA256:
        raise ValueError("B01-PDF-007 deterministic PDF identity drift")
    if observed["raster_pixel_sha256"] != fixture.EXPECTED_PIXEL_SHA256:
        raise ValueError("B01-PDF-007 deterministic raster identity drift")
    _write_json(output / "fixture-evidence.json", observed)
    return source


def _summary_record(observation: dict[str, Any]) -> dict[str, Any]:
    return {
        "route": observation.get("route"),
        "status": observation.get("status"),
        "warning_count": len(observation.get("warnings", []))
        if isinstance(observation.get("warnings"), list)
        else None,
        "warnings": observation.get("warnings"),
        "block_count": len(observation.get("blocks", []))
        if isinstance(observation.get("blocks"), list)
        else None,
        "raw_output_sha256": observation.get("raw_output_sha256"),
        "raw_output_bytes": observation.get("raw_output_bytes"),
    }


def run_poppler(output: Path, evidence_source_commit: str | None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    source = _materialize_fixture(output)
    observations = output / "observations"
    observations.mkdir(exist_ok=True)

    bbox = run_pdftotext_bbox_layout(source)
    html = run_pdftohtml_xml(source)
    _write_json(observations / "B01-PDF-007__pdftotext-bbox-layout.json", bbox)
    _write_json(observations / "B01-PDF-007__pdftohtml-xml.json", html)

    report = {
        "contract": CONTRACT,
        "evidence_source_commit": evidence_source_commit,
        "provider_family": "poppler-controls",
        "fixture": fixture.evidence(),
        "route_versions": {
            "pdftotext": executable_version("pdftotext"),
            "pdftohtml": executable_version("pdftohtml"),
            "pdfinfo": executable_version("pdfinfo"),
        },
        "results": [_summary_record(bbox), _summary_record(html)],
        "decision_boundary": {
            "fallback_needed_decided": False,
            "ocr_route_executed": False,
            "provider_selected": False,
        },
    }
    _write_json(output / "b01-defective-native-raw.json", report)
    return report


def run_tika(
    output: Path,
    tika_jar: Path,
    config: Path,
    evidence_source_commit: str | None,
    java_executable: str = "java",
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    source = _materialize_fixture(output)
    jar_evidence = verify_tika_jar(tika_jar)
    if not jar_evidence.get("verified"):
        raise ValueError("Tika artifact must match the pinned SHA-512")
    observation = run_tika_pdf_xhtml(
        source,
        tika_jar,
        config,
        java_executable=java_executable,
    )
    _write_json(
        output / "observations" / "B01-PDF-007__tika-app-3.3.2-xhtml.json",
        observation,
    )
    report = {
        "contract": CONTRACT,
        "evidence_source_commit": evidence_source_commit,
        "provider_family": "apache-tika",
        "fixture": fixture.evidence(),
        "tika_artifact": jar_evidence,
        "results": [_summary_record(observation)],
        "decision_boundary": {
            "fallback_needed_decided": False,
            "ocr_route_executed": False,
            "provider_selected": False,
        },
    }
    _write_json(output / "b01-defective-native-raw.json", report)
    return report


def run_docling(
    output: Path,
    artifacts_path: Path,
    cache_root: Path,
    evidence_source_commit: str | None,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    source = _materialize_fixture(output)
    observation = run_docling_pdf_json(source, artifacts_path, cache_root)
    raw_document = observation.pop("raw_document", None)
    if raw_document is not None:
        _write_json(output / "raw" / "B01-PDF-007__docling.json", raw_document)
    _write_json(
        output / "observations" / "B01-PDF-007__docling.json",
        observation,
    )
    report = {
        "contract": CONTRACT,
        "evidence_source_commit": evidence_source_commit,
        "provider_family": "docling",
        "fixture": fixture.evidence(),
        "route_options": observation.get("route_options"),
        "results": [_summary_record(observation)],
        "decision_boundary": {
            "fallback_needed_decided": False,
            "ocr_route_executed": False,
            "provider_selected": False,
        },
    }
    _write_json(output / "b01-defective-native-raw.json", report)
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
    output = args.output.resolve()
    if args.provider == "poppler":
        report = run_poppler(output, args.evidence_source_commit)
    elif args.provider == "tika":
        report = run_tika(
            output,
            args.tika_jar.resolve(),
            args.config.resolve(),
            args.evidence_source_commit,
            java_executable=args.java,
        )
    else:
        report = run_docling(
            output,
            args.artifacts_path.resolve(),
            args.cache_root.resolve(),
            args.evidence_source_commit,
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
