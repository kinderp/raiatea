#!/usr/bin/env python3
"""Exploratory B01-PDF-007 Docling + RapidOCR profile.

This route is deliberately separate from the canonical Docling native/no-OCR
baseline. It reuses the exact Docling dependency/layout-model lock but enables
RapidOCR with explicitly supplied local Torch detector/recognizer/dictionary
payloads. Until the dictionary payload hash is frozen in a Raiatea lock, output
from this helper is setup/exploratory evidence only and must not be described as
a canonical E-04 measurement.
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
PROFILE_ID = "docling-2.118.0-rapidocr-3.9.2-torch-en-ppocrv4-default"
EXPECTED_DET_SHA256 = "62aba369c8245f131bb08348a7d9c3135234d5c139ec92b34c8ac7b9ba7c2846"
EXPECTED_REC_SHA256 = "f9723c94847de59df9b059faaed041fbb35f014ea973da40290b1e97004e1d4e"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def verify_ocr_payload(det: Path, rec: Path, keys: Path) -> dict[str, Any]:
    rows = {
        "detector": {
            "path": str(det.resolve()),
            "sha256": _sha256(det) if det.is_file() else None,
            "expected_sha256": EXPECTED_DET_SHA256,
        },
        "recognizer": {
            "path": str(rec.resolve()),
            "sha256": _sha256(rec) if rec.is_file() else None,
            "expected_sha256": EXPECTED_REC_SHA256,
        },
        "dictionary": {
            "path": str(keys.resolve()),
            "sha256": _sha256(keys) if keys.is_file() else None,
            "expected_sha256": None,
        },
    }
    rows["detector"]["verified"] = rows["detector"]["sha256"] == EXPECTED_DET_SHA256
    rows["recognizer"]["verified"] = rows["recognizer"]["sha256"] == EXPECTED_REC_SHA256
    rows["dictionary"]["verified"] = keys.is_file() and keys.stat().st_size > 0
    rows["canonical_lock_complete"] = False
    rows["exploratory_only_reason"] = (
        "dictionary SHA-256 has not yet been promoted into the Raiatea OCR payload lock"
    )
    return rows


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
    det_model: Path,
    rec_model: Path,
    rec_keys: Path,
    evidence_source_commit: str | None,
) -> dict[str, Any]:
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    payload = verify_ocr_payload(det_model, rec_model, rec_keys)
    if not payload["detector"]["verified"] or not payload["recognizer"]["verified"]:
        raise ValueError("RapidOCR detector/recognizer does not match pinned upstream SHA-256")
    if not payload["dictionary"]["verified"]:
        raise ValueError("RapidOCR English dictionary is missing or empty")

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
        raise ValueError("Pinned Docling layout model payload is missing")

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
                det_model_path=str(det_model.resolve()),
                rec_model_path=str(rec_model.resolve()),
                rec_keys_path=str(rec_keys.resolve()),
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
        "detector": "en_PP-OCRv3_det_mobile",
        "recognizer": "en_PP-OCRv4_rec_mobile",
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
    _write_json(output / "rapidocr-payload-evidence.json", payload)

    dimensions = measure_b01_defective_native_dimensions(mapped, _gold())
    report = {
        "contract": {
            "name": "raiatea-p0-b01-docling-rapidocr-exploratory",
            "version": "0.1.0",
            "scope": "setup-and-exploratory-evidence-only",
            "canonical_e04_measurement": False,
            "public_p0_schema": False,
        },
        "evidence_source_commit": evidence_source_commit,
        "profile_id": PROFILE_ID,
        "environment": environment,
        "rapidocr_version": rapidocr_version,
        "layout_model_payload": layout_payload,
        "ocr_payload": payload,
        "provider_conversion_status": provider_status,
        "dimensions": dimensions,
        "duration_seconds": round(time.perf_counter() - started, 9),
        "next_gate": (
            "freeze dictionary and complete OCR payload SHA-256 lock before canonical measurement"
        ),
    }
    _write_json(output / "b01-docling-rapidocr-exploratory.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts-path", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--det-model", type=Path, required=True)
    parser.add_argument("--rec-model", type=Path, required=True)
    parser.add_argument("--rec-keys", type=Path, required=True)
    parser.add_argument("--evidence-source-commit")
    args = parser.parse_args()
    report = run_exploratory(
        args.output.resolve(),
        args.artifacts_path.resolve(),
        args.cache_root.resolve(),
        args.det_model.resolve(),
        args.rec_model.resolve(),
        args.rec_keys.resolve(),
        args.evidence_source_commit,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
