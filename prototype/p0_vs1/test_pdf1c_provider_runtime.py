from __future__ import annotations

import hashlib
import json
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
    def __init__(
        self,
        message: str,
        *,
        component_type: str = "model",
        category: str = "inference_failure",
        page_no: int | None = 1,
        module_name: str = "docling.pipeline.standard_pdf_pipeline",
    ) -> None:
        self.error_message = message
        self.component_type = component_type
        self.category = category
        self.page_no = page_no
        self.module_name = module_name


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

        def convert(self, _path, *, raises_on_error: bool = True):
            if raises_on_error:
                raise AssertionError(
                    "PDF1c must receive structured ConversionResult failures"
                )
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

    def test_failed_result_is_structured_attempt_without_exporting_document(self) -> None:
        secret_message = "/private/source.pdf failed: hidden provider detail"
        bundle = self.run_status("ConversionStatus.FAILURE", secret_message)
        observation = bundle["observation"]
        self.assertEqual(observation["status"], "failed")
        self.assertEqual(observation["provider_conversion_status"], "ConversionStatus.FAILURE")
        self.assertEqual(observation["blocks"], [])
        self.assertIsNone(observation["raw_document_sha256"])
        warning = observation["warnings"][0]
        self.assertEqual(warning["code"], "docling-conversion-failed")
        provider_errors = warning["details"]["provider_errors"]
        self.assertEqual(
            provider_errors,
            [
                {
                    "error_type": "ErrorRecord",
                    "component_type": "model",
                    "category": "inference_failure",
                    "page_no": 1,
                    "module_name": "docling.pipeline.standard_pdf_pipeline",
                }
            ],
        )
        serialized = json.dumps(bundle, sort_keys=True)
        self.assertNotIn(secret_message, serialized)
        self.assertNotIn("/private/source.pdf", serialized)

    def test_password_failure_is_restricted_attempt_without_export(self) -> None:
        bundle = self.run_status("ConversionStatus.FAILURE", "Incorrect password")
        observation = bundle["observation"]
        self.assertEqual(observation["status"], "restricted")
        self.assertEqual(observation["provider_conversion_status"], "ConversionStatus.FAILURE")
        self.assertEqual(observation["blocks"], [])
        self.assertEqual(
            observation["warnings"][0]["code"],
            "docling-access-restriction-signaled",
        )
        self.assertNotIn("Incorrect password", json.dumps(bundle, sort_keys=True))

    def test_unknown_provider_status_is_unknown_attempt_without_export(self) -> None:
        bundle = self.run_status("ConversionStatus.NEW_FUTURE_STATE", "No known mapping")
        self.assertEqual(bundle["observation"]["status"], "unknown")
        self.assertEqual(
            bundle["observation"]["provider_conversion_status"],
            "ConversionStatus.NEW_FUTURE_STATE",
        )
        self.assertEqual(bundle["observation"]["body_order_source"], "unavailable")
        self.assertEqual(bundle["observation"]["blocks"], [])


if __name__ == "__main__":
    unittest.main()
