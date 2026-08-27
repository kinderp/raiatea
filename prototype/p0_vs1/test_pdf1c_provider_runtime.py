from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from prototype.p0_vs1 import docling_reference
from prototype.p0_vs1.docling_provider_runtime import run_docling_pdf_product


SOURCE_BYTES = b"%PDF-1.4\nprovider-runtime-test"
FINGERPRINT = "sha256:" + hashlib.sha256(SOURCE_BYTES).hexdigest()
SOURCE_REF = "source-ref:" + "1" * 64


def provider() -> dict:
    return {
        "provider_id": "docling",
        "version": docling_reference.DOCLING_VERSION,
        "wheel_sha256": "sha256:" + docling_reference.DOCLING_WHEEL_SHA256,
        "environment_freeze_sha256": "sha256:" + docling_reference.ENVIRONMENT_FREEZE_SHA256,
        "model_payload_sha256": "sha256:" + docling_reference.MODEL_PAYLOAD_SHA256,
    }


class NeverExportDocument:
    def export_to_dict(self):
        raise AssertionError("export_to_dict must not be called for non-completed status")


class ErrorRecord:
    def __init__(self, message: str) -> None:
        self.error_message = message


class FakeResult:
    def __init__(self, status: str, error_message: str) -> None:
        self.status = status
        self.errors = [ErrorRecord(error_message)]
        self.document = NeverExportDocument()


def fake_docling_modules(result: FakeResult) -> dict[str, types.ModuleType]:
    docling = types.ModuleType("docling")
    docling.__path__ = []  # type: ignore[attr-defined]
    datamodel = types.ModuleType("docling.datamodel")
    datamodel.__path__ = []  # type: ignore[attr-defined]

    accelerator = types.ModuleType("docling.datamodel.accelerator_options")
    class AcceleratorDevice:
        CPU = "cpu"
    class AcceleratorOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
    accelerator.AcceleratorDevice = AcceleratorDevice
    accelerator.AcceleratorOptions = AcceleratorOptions

    base_models = types.ModuleType("docling.datamodel.base_models")
    class InputFormat:
        PDF = "pdf"
    base_models.InputFormat = InputFormat

    pipeline_options = types.ModuleType("docling.datamodel.pipeline_options")
    class PdfPipelineOptions:
        pass
    pipeline_options.PdfPipelineOptions = PdfPipelineOptions

    converter_module = types.ModuleType("docling.document_converter")
    class PdfFormatOption:
        def __init__(self, *, pipeline_options):
            self.pipeline_options = pipeline_options
    class DocumentConverter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def convert(self, _path):
            return result
    converter_module.PdfFormatOption = PdfFormatOption
    converter_module.DocumentConverter = DocumentConverter

    return {
        "docling": docling,
        "docling.datamodel": datamodel,
        "docling.datamodel.accelerator_options": accelerator,
        "docling.datamodel.base_models": base_models,
        "docling.datamodel.pipeline_options": pipeline_options,
        "docling.document_converter": converter_module,
    }


class Pdf1cProviderRuntimeTests(unittest.TestCase):
    def run_status(self, status: str, message: str) -> dict:
        result = FakeResult(status, message)
        modules = fake_docling_modules(result)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            artifacts = base / "models"
            cache = base / "cache"
            artifacts.mkdir()
            with patch.dict(sys.modules, modules, clear=False):
                return run_docling_pdf_product(
                    SOURCE_BYTES,
                    source_ref_id=SOURCE_REF,
                    source_fingerprint=FINGERPRINT,
                    provider=provider(),
                    artifacts_path=artifacts,
                    cache_root=cache,
                )

    def test_failed_result_is_attempt_evidence_without_exporting_document(self) -> None:
        bundle = self.run_status("ConversionStatus.FAILURE", "Data format error")
        self.assertEqual(bundle["observation"]["status"], "failed")
        self.assertEqual(bundle["observation"]["blocks"], [])
        self.assertIsNone(bundle["observation"]["raw_document_sha256"])

    def test_password_failure_is_restricted_attempt_without_export(self) -> None:
        bundle = self.run_status("ConversionStatus.FAILURE", "Incorrect password")
        self.assertEqual(bundle["observation"]["status"], "restricted")
        self.assertEqual(bundle["observation"]["blocks"], [])
        self.assertEqual(
            bundle["observation"]["warnings"][0]["code"],
            "docling-access-restriction-signaled",
        )

    def test_unknown_provider_status_is_unknown_attempt_without_export(self) -> None:
        bundle = self.run_status("ConversionStatus.NEW_FUTURE_STATE", "No known mapping")
        self.assertEqual(bundle["observation"]["status"], "unknown")
        self.assertEqual(bundle["observation"]["body_order_source"], "unavailable")
        self.assertEqual(bundle["observation"]["blocks"], [])


if __name__ == "__main__":
    unittest.main()
