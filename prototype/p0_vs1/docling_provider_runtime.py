#!/usr/bin/env python3
"""PDF1c real Docling provider runtime with fail-closed result classification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from prototype.p0_vs1.docling_observation_contract import (
    DOCLING_OBSERVATION_VERSION,
    DOCLING_PROFILE,
    validate_docling_observation_bundle,
)
from prototype.p0_vs1.docling_product_parser import (
    _offline_environment,
    _provider_status,
    failed_docling_observation,
    map_docling_document,
)
from prototype.p0_vs1.docling_reference import validate_reference_provider_record


class DoclingProviderRuntimeError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingProviderRuntimeError(message)


def _source_sha(source_bytes: bytes) -> str:
    return "sha256:" + hashlib.sha256(source_bytes).hexdigest()


def _restriction_signal(result: Any) -> bool:
    fragments: list[str] = [str(getattr(result, "status", ""))]
    errors = getattr(result, "errors", None)
    if isinstance(errors, (list, tuple)):
        for error in errors:
            fragments.append(type(error).__name__)
            for attribute in ("error_message", "message", "details"):
                value = getattr(error, attribute, None)
                if isinstance(value, str):
                    fragments.append(value)
    combined = " ".join(fragments).casefold()
    return "password" in combined or "encrypted" in combined


def _enum_value(value: Any) -> str | None:
    candidate = getattr(value, "value", value)
    if isinstance(candidate, str) and candidate:
        return candidate
    return None


def _provider_error_evidence(result: Any) -> list[dict[str, Any]]:
    """Keep only bounded structural Docling error metadata, never free-form text."""
    errors = getattr(result, "errors", None)
    if not isinstance(errors, (list, tuple)):
        return []
    evidence: list[dict[str, Any]] = []
    for error in errors[:16]:
        row: dict[str, Any] = {"error_type": type(error).__name__}
        component = _enum_value(getattr(error, "component_type", None))
        category = _enum_value(getattr(error, "category", None))
        page_no = getattr(error, "page_no", None)
        module_name = getattr(error, "module_name", None)
        if component is not None:
            row["component_type"] = component
        if category is not None:
            row["category"] = category
        if isinstance(page_no, int) and not isinstance(page_no, bool) and page_no >= 1:
            row["page_no"] = page_no
        if (
            isinstance(module_name, str)
            and 0 < len(module_name) <= 128
            and all(ch.isalnum() or ch in "._" for ch in module_name)
        ):
            row["module_name"] = module_name
        evidence.append(row)
    return evidence


def _failed_result_observation(
    *,
    source_ref_id: str,
    source_fingerprint: str,
    provider: dict[str, Any],
    result: Any,
) -> dict[str, Any]:
    provider_status = str(getattr(result, "status", ""))
    bundle = failed_docling_observation(
        source_ref_id=source_ref_id,
        source_fingerprint=source_fingerprint,
        provider=provider,
        restricted=_restriction_signal(result),
        error_type="DoclingConversionFailure",
    )
    observation = bundle["observation"]
    observation["provider_conversion_status"] = provider_status or None
    details = observation["warnings"][0]["details"]
    if isinstance(details, dict):
        details["provider_errors"] = _provider_error_evidence(result)
    validate_docling_observation_bundle(bundle)
    return bundle


def _unknown_observation(
    *,
    source_ref_id: str,
    source_fingerprint: str,
    provider: dict[str, Any],
    provider_conversion_status: str,
) -> dict[str, Any]:
    validate_reference_provider_record(provider)
    bundle = {
        "bundle_version": DOCLING_OBSERVATION_VERSION,
        "record_kind": "DoclingObservationBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": source_fingerprint,
        "provider": dict(provider),
        "route_profile": DOCLING_PROFILE,
        "observation": {
            "status": "unknown",
            "provider_conversion_status": provider_conversion_status,
            "warnings": [
                {
                    "code": "docling-conversion-status-unknown",
                    "details": {"status_type": "provider-status-not-promoted"},
                }
            ],
            "body_order_source": "unavailable",
            "blocks": [],
            "picture_collection_state": "unavailable",
            "pictures": [],
            "caption_blocks": [],
            "picture_caption_relations": [],
            "raw_document_sha256": None,
        },
    }
    validate_docling_observation_bundle(bundle)
    return bundle


def run_docling_pdf_product(
    source_bytes: bytes,
    *,
    source_ref_id: str,
    source_fingerprint: str,
    provider: dict[str, Any],
    artifacts_path: Path,
    cache_root: Path,
) -> dict[str, Any]:
    """Run the exact native/no-OCR Docling profile and classify before export."""
    validate_reference_provider_record(provider)
    _require(isinstance(source_bytes, bytes) and source_bytes, "docling-source-bytes-required")
    _require(_source_sha(source_bytes) == source_fingerprint, "docling-source-fingerprint-mismatch")
    artifacts = artifacts_path.resolve()
    _require(artifacts.is_dir(), "docling-artifacts-root-unavailable")
    cache_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="raiatea-pdf1c-docling-") as temporary:
        local_input = Path(temporary).resolve() / "source.pdf"
        local_input.write_bytes(source_bytes)
        try:
            with _offline_environment(artifacts, cache_root):
                from docling.datamodel.accelerator_options import (  # type: ignore[import-not-found]
                    AcceleratorDevice,
                    AcceleratorOptions,
                )
                from docling.datamodel.base_models import InputFormat  # type: ignore[import-not-found]
                from docling.datamodel.pipeline_options import PdfPipelineOptions  # type: ignore[import-not-found]
                from docling.document_converter import (  # type: ignore[import-not-found]
                    DocumentConverter,
                    PdfFormatOption,
                )

                options = PdfPipelineOptions()
                options.artifacts_path = artifacts
                options.enable_remote_services = False
                options.allow_external_plugins = False
                options.do_ocr = False
                options.do_table_structure = False
                options.do_code_enrichment = False
                options.do_formula_enrichment = False
                options.do_picture_classification = False
                options.do_picture_description = False
                options.do_chart_extraction = False
                options.generate_page_images = False
                options.generate_picture_images = False
                options.generate_table_images = False
                options.generate_parsed_pages = False
                options.force_backend_text = False
                options.accelerator_options = AcceleratorOptions(
                    num_threads=4,
                    device=AcceleratorDevice.CPU,
                )
                converter = DocumentConverter(
                    allowed_formats=[InputFormat.PDF],
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=options)
                    },
                )
                # Normal Provider failures are structured ConversionResult evidence,
                # not exceptional control flow. Unexpected exceptions still fail closed.
                result = converter.convert(local_input, raises_on_error=False)
        except Exception as exc:
            message = str(exc).casefold()
            restricted = "password" in message or "encrypted" in message
            return failed_docling_observation(
                source_ref_id=source_ref_id,
                source_fingerprint=source_fingerprint,
                provider=provider,
                restricted=restricted,
                error_type=type(exc).__name__,
            )

        provider_status = str(result.status)
        normalized_status = _provider_status(provider_status)
        if normalized_status == "failed":
            return _failed_result_observation(
                source_ref_id=source_ref_id,
                source_fingerprint=source_fingerprint,
                provider=provider,
                result=result,
            )
        if normalized_status == "unknown":
            return _unknown_observation(
                source_ref_id=source_ref_id,
                source_fingerprint=source_fingerprint,
                provider=provider,
                provider_conversion_status=provider_status,
            )

        try:
            exported = result.document.export_to_dict()
        except Exception as exc:
            return failed_docling_observation(
                source_ref_id=source_ref_id,
                source_fingerprint=source_fingerprint,
                provider=provider,
                restricted=False,
                error_type=type(exc).__name__,
            )

    return map_docling_document(
        exported,
        source_ref_id=source_ref_id,
        source_fingerprint=source_fingerprint,
        provider=provider,
        provider_conversion_status=provider_status,
    )


__all__ = ["DoclingProviderRuntimeError", "run_docling_pdf_product"]
