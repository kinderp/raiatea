#!/usr/bin/env python3
"""Exploratory B01-PDF-007 Docling + RapidOCR profile.

This route is deliberately separate from the canonical Docling native/no-OCR
baseline. It reuses the exact Docling dependency/layout-model lock and the
RapidOCR bundle materialized by Docling's own model downloader for ``torch:en``.
Until that complete bundle is frozen in a Raiatea payload lock, output from this
helper is setup/exploratory evidence only and must not be described as a
canonical E-04 measurement.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Iterator

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE.parent

import sys
sys.path.insert(0, str(BENCH_DIR))
sys.path.insert(0, str(HERE))

import b01_pdf_007_fixture as fixture  # noqa: E402
from docling_routes import (  # noqa: E402
    DOCLING_VERSION,
    artifact_manifest,
    installed_environment,
    map_docling_document,
)
from score_b01_defective_native import (  # noqa: E402
    measure_b01_defective_native_dimensions,
)

RAPIDOCR_VERSION = "3.9.2"
PROFILE_ID = "docling-2.118.0-rapidocr-3.9.2-torch-en-default"


def _gold() -> dict[str, Any]:
    return json.loads(
        (BENCH_DIR / "manifests" / "b01-pdf-007-gold.json").read_text(
            encoding="utf-8"
        )
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


@contextmanager
def _controlled_environment(cache_root: Path) -> Iterator[None]:
    cache_root = cache_root.resolve()
    values = {
        "HF_HOME": str(cache_root / "huggingface"),
        "HUGGINGFACE_HUB_CACHE": str(cache_root / "huggingface" / "hub"),
        "TRANSFORMERS_CACHE": str(cache_root / "transformers"),
        "XDG_CACHE_HOME": str(cache_root / "xdg"),
        "TORCH_HOME": str(cache_root / "torch"),
        "MPLCONFIGDIR": str(cache_root / "matplotlib"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "DOCLING_DEVICE": "cpu",
        "DOCLING_NUM_THREADS": "4",
    }
    previous = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        yield
    finally:
        for key, old in previous.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


def run_exploratory(
    output: Path,
    artifacts_path: Path,
    cache_root: Path,
    evidence_source_commit: str | None,
) -> dict[str, Any]:
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)

    environment = installed_environment()
    if environment.get("docling_version") != DOCLING_VERSION:
        raise ValueError(f"Expected Docling {DOCLING_VERSION}")
    try:
        rapidocr_version = importlib.metadata.version("rapidocr")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ValueError("RapidOCR is not installed") from exc
    if rapidocr_version != RAPIDOCR_VERSION:
        raise ValueError(
            f"Expected RapidOCR {RAPIDOCR_VERSION}, observed {rapidocr_version}"
        )

    layout_payload = artifact_manifest(artifacts_path)
    if not layout_payload.get("exists") or not layout_payload.get("file_count"):
        raise ValueError("Pinned Docling model artifact root is missing")

    rapidocr_root = artifacts_path.resolve() / "RapidOcr"
    rapidocr_payload = artifact_manifest(rapidocr_root)
    _write_json(output / "rapidocr-bundle-manifest.json", rapidocr_payload)
    if not rapidocr_payload.get("exists") or not rapidocr_payload.get("file_count"):
        raise ValueError(
            "Docling RapidOCR bundle is missing; materialize it with "
            "docling-tools models download rapidocr --rapidocr-backend-lang torch:en"
        )

    source = output / "fixture" / "B01-PDF-007.pdf"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(fixture.build_fixture())

    cache_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="raiatea-docling-rapidocr-") as tmp:
        controlled = Path(tmp)
        input_dir = controlled / "input"
        input_dir.mkdir()
        local_input = input_dir / source.name
        local_input.write_bytes(source.read_bytes())

        with _controlled_environment(cache_root):
            from docling.datamodel.accelerator_options import (
                AcceleratorDevice,
                AcceleratorOptions,
            )
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import (
                OcrMode,
                PdfPipelineOptions,
                RapidOcrOptions,
            )
            from docling.document_converter import (
                DocumentConverter,
                PdfFormatOption,
            )

            pipeline_options = PdfPipelineOptions()
            pipeline_options.artifacts_path = artifacts_path.resolve()
            pipeline_options.enable_remote_services = False
            pipeline_options.allow_external_plugins = False
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = RapidOcrOptions(
                mode=OcrMode.DEFAULT,
                lang=["en"],
                backend="torch",
                use_cls=False,
                print_verbose=False,
            )
            pipeline_options.do_table_structure = False
            pipeline_options.do_code_enrichment = False
            pipeline_options.do_formula_enrichment = False
            pipeline_options.do_picture_classification = False
            pipeline_options.do_picture_description = False
            pipeline_options.do_chart_extraction = False
            pipeline_options.generate_page_images = False
            pipeline_options.generate_picture_images = False
            pipeline_options.generate_table_images = False
            pipeline_options.generate_parsed_pages = False
            pipeline_options.force_backend_text = False
            pipeline_options.accelerator_options = AcceleratorOptions(
                num_threads=4,
                device=AcceleratorDevice.CPU,
            )

            converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                    )
                },
            )
            result = converter.convert(local_input)
            raw_document = result.document.export_to_dict()
            provider_status = str(result.status)

    mapped = map_docling_document(raw_document)
    mapped["route"] = PROFILE_ID
    mapped["provider_conversion_status"] = provider_status
    mapped["route_options"] = {
        "do_ocr": True,
        "ocr_engine": "rapidocr",
        "rapidocr_version": RAPIDOCR_VERSION,
        "backend": "torch",
        "lang": ["en"],
        "mode": "default/pdf-aware-layout-regions",
        "use_cls": False,
        "artifact_resolution": "docling-managed-RapidOcr-bundle",
        "do_table_structure": False,
        "do_formula_enrichment": False,
        "remote_services": False,
        "external_plugins": False,
        "cpu_only": True,
    }
    raw_bytes = json.dumps(
        raw_document,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    mapped["raw_output_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    mapped["raw_output_bytes"] = len(raw_bytes)

    _write_json(output / "raw" / "B01-PDF-007__docling-rapidocr.json", raw_document)
    _write_json(
        output / "observations" / "B01-PDF-007__docling-rapidocr.json",
        mapped,
    )

    dimensions = measure_b01_defective_native_dimensions(mapped, _gold())
    report = {
        "contract": {
            "name": "raiatea-p0-b01-docling-rapidocr-exploratory",
            "version": "0.2.0",
            "scope": "setup-and-exploratory-evidence-only",
            "canonical_e04_measurement": False,
            "public_p0_schema": False,
        },
        "evidence_source_commit": evidence_source_commit,
        "profile_id": PROFILE_ID,
        "environment": environment,
        "rapidocr_version": rapidocr_version,
        "docling_model_root_manifest": layout_payload,
        "rapidocr_bundle": rapidocr_payload,
        "provider_conversion_status": provider_status,
        "dimensions": dimensions,
        "duration_seconds": round(time.perf_counter() - started, 9),
        "next_gate": (
            "freeze the complete Docling-managed RapidOcr bundle manifest before "
            "canonical offline measurement"
        ),
    }
    _write_json(output / "b01-docling-rapidocr-exploratory.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts-path", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--evidence-source-commit")
    args = parser.parse_args()
    report = run_exploratory(
        args.output.resolve(),
        args.artifacts_path.resolve(),
        args.cache_root.resolve(),
        args.evidence_source_commit,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
