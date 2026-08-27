from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.docling_observation_contract import (
    DOCLING_OBSERVATION_MEDIA_TYPE,
    DOCLING_OBSERVATION_VERSION,
    DOCLING_PROFILE,
    canonical_json_bytes,
)
from prototype.p0_vs1 import docling_reference
from prototype.p0_vs1.pdf1a import (
    MixedDocumentReconciliationEngine,
    MixedLocalSourceDiscoveryService,
)
from prototype.p0_vs1.pdf1c_service import (
    DoclingPdfExtractionError,
    LocalDoclingPdfExtractionService,
    validate_pdf1c_state,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry
from prototype.p0_vs1.source_contract import PDF_MEDIA_TYPE


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GENERATOR = _load("pdf1c_service_fixture_generator", GENERATOR_PATH)


def provider() -> dict:
    return {
        "provider_id": "docling",
        "version": docling_reference.DOCLING_VERSION,
        "wheel_sha256": "sha256:" + docling_reference.DOCLING_WHEEL_SHA256,
        "environment_freeze_sha256": "sha256:" + docling_reference.ENVIRONMENT_FREEZE_SHA256,
        "model_payload_sha256": "sha256:" + docling_reference.MODEL_PAYLOAD_SHA256,
    }


def provider_bundle(source_ref_id: str, fingerprint: str, *, status: str = "success") -> dict:
    blocks = [
        {
            "provider_ref": "#/texts/0",
            "body_order_index": 0,
            "text": "Raiatea PDF 001",
            "provider_label": "title",
            "semantic_type": "heading",
            "semantic_level": 1,
            "coordinate": {
                "page_index": 0,
                "bbox_points_bottom_left": [72.0, 700.0, 220.0, 730.0],
            },
            "provenance_count": 1,
            "provenance_source": "docling-text-provenance",
        },
        {
            "provider_ref": "#/texts/1",
            "body_order_index": 1,
            "text": "Body paragraph.",
            "provider_label": "text",
            "semantic_type": "paragraph",
            "semantic_level": None,
            "coordinate": None,
            "provenance_count": 0,
            "provenance_source": "docling-lossless-item",
        },
    ] if status in {"success", "degraded"} else []
    return {
        "bundle_version": DOCLING_OBSERVATION_VERSION,
        "record_kind": "DoclingObservationBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": fingerprint,
        "provider": provider(),
        "route_profile": DOCLING_PROFILE,
        "observation": {
            "status": status,
            "provider_conversion_status": (
                "ConversionStatus.SUCCESS" if status == "success"
                else "ConversionStatus.PARTIAL_SUCCESS" if status == "degraded"
                else None
            ),
            "warnings": [],
            "body_order_source": "body.children" if blocks else "unavailable",
            "blocks": blocks,
            "picture_collection_state": "present" if blocks else "unavailable",
            "pictures": [],
            "caption_blocks": [],
            "picture_caption_relations": [],
            "raw_document_sha256": (
                "sha256:" + hashlib.sha256(b"lossless-docling-json").hexdigest()
                if blocks else None
            ),
        },
    }


class FakePluginIO:
    next_output_bytes: bytes = b""
    on_read_completed = None

    def __init__(self) -> None:
        self.input_handle = None
        self.output_target = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def add_input(self, source_bytes: bytes, *, media_type: str, ttl_seconds: int):
        fingerprint = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
        self.input_handle = {
            "handle_id": "asset:pdf1c-test",
            "lease_id": "lease:pdf1c-test",
            "access": "read",
            "media_type": media_type,
            "byte_length": len(source_bytes),
            "fingerprint": fingerprint,
            "expires_at": "2099-01-01T00:00:00Z",
        }
        return deepcopy(self.input_handle)

    def issue_output(self, *, media_type: str, max_byte_length: int, ttl_seconds: int):
        self.output_target = {
            "handle_id": "output:pdf1c-test",
            "lease_id": "lease:pdf1c-output",
            "access": "write-once-output",
            "media_type": media_type,
            "max_byte_length": max_byte_length,
            "expires_at": "2099-01-01T00:00:00Z",
        }
        return deepcopy(self.output_target)

    def freeze(self):
        return {"RAIATEA_VS1_PLUGIN_IO_BROKER": "/core/private/broker.json"}

    def verify_broker_unchanged(self):
        return None

    def read_completed_output(self, output_target, completed):
        if self.on_read_completed is not None:
            self.on_read_completed()
        return bytes(self.next_output_bytes)


class FakeClient:
    result_callback = None
    last_request = None

    def __init__(self, command, manifest, *, extra_env=None, max_invocation_timeout_seconds=60):
        self.command = command
        self.manifest = manifest
        self.extra_env = extra_env
        self.max_timeout = max_invocation_timeout_seconds

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def handshake(self):
        return {"identity": {"runtime_instance_id": "runtime:pdf1c:test"}}

    def invoke(self, request):
        type(self).last_request = deepcopy(request)
        if self.result_callback is not None:
            self.result_callback(request)
        output_target = request["output_targets"][0]
        completed = {
            "handle_id": output_target["handle_id"],
            "lease_id": output_target["lease_id"],
            "access": "read",
            "media_type": DOCLING_OBSERVATION_MEDIA_TYPE,
            "byte_length": len(FakePluginIO.next_output_bytes),
            "fingerprint": "sha256:" + hashlib.sha256(FakePluginIO.next_output_bytes).hexdigest(),
            "expires_at": output_target["expires_at"],
        }
        return {
            "record_type": "invocation-result",
            "invocation_id": request["invocation_id"],
            "runtime_instance_id": "runtime:pdf1c:test",
            "status": "completed",
            "outputs": [{"kind": "asset-handle", "handle": completed}],
            "diagnostic_refs": [],
            "provenance": {
                "plugin_id": "org.raiatea.pdf1.docling-extractor",
                "plugin_version": "0.1.0",
                "runtime_instance_id": "runtime:pdf1c:test",
                "invocation_id": request["invocation_id"],
                "capability": request["capability"],
                "started_at": "2026-08-27T12:00:00Z",
                "ended_at": "2026-08-27T12:00:01Z",
                "input_refs": [],
                "output_refs": [output_target["handle_id"]],
                "rights_decision_ref": request["runtime_context"]["rights_decision_ref"],
            },
        }


class Pdf1cServiceFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.cache_parent = self.base / "cache-parent"
        self.models = self.base / "models"
        self.wheel = self.base / "docling.whl"
        for directory in (self.root, self.outputs, self.cache_parent, self.models):
            directory.mkdir()
        self.wheel.write_bytes(b"test-wheel")
        GENERATOR.generate_pdf_single_column(self.root / "single.pdf")

        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:pdf1c", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        reconciliation = MixedDocumentReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:pdf1c",
        )
        self.assertEqual(reconciliation.reconcile_inventory()["inventory_count"], 1)
        discovery = MixedLocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:pdf1c",
        )
        discovery.discover(rights_evidence_state="known-permitted")
        self.source_ref = self.source_ref_for_location("single.pdf")
        self.service = LocalDoclingPdfExtractionService(
            self.store,
            self.scopes,
            self.broker,
            "scope:pdf1c",
            wheel_path=self.wheel,
            artifacts_path=self.models,
            cache_parent=self.cache_parent,
        )
        FakePluginIO.next_output_bytes = b""
        FakePluginIO.on_read_completed = None
        FakeClient.result_callback = None
        FakeClient.last_request = None

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def source_ref_for_location(self, location: str) -> str:
        payload = self.store.load().payload
        entry = next(
            row for row in payload["vs1b"]["entries"]
            if row["current_location"] == location
            and row["availability"] == "known-present"
            and row["superseded_by"] is None
        )
        self.assertEqual(entry["media_type"], PDF_MEDIA_TYPE)
        ref = next(
            row for row in payload["vs1c"]["source_references"]
            if row["stored_instance_ref"] == entry["stored_instance_id"]
        )
        return ref["source_ref_id"]

    def configure_bundle(self, status: str = "success") -> dict:
        payload = self.store.load().payload
        source = next(
            row for row in payload["vs1c"]["source_references"]
            if row["source_ref_id"] == self.source_ref
        )
        bundle = provider_bundle(self.source_ref, source["fingerprint"], status=status)
        FakePluginIO.next_output_bytes = canonical_json_bytes(bundle)
        return bundle

    def extract(self, *, status: str = "success"):
        self.configure_bundle(status)
        with (
            patch("prototype.p0_vs1.pdf1c_service.verify_reference_docling", return_value=provider()),
            patch("prototype.p0_vs1.pdf1c_service.Vs1PluginIO", FakePluginIO),
            patch("prototype.p0_vs1.pdf1c_service.LocalPluginProcessClient", FakeClient),
            patch("prototype.p0_vs1.pdf1c_service.build_docling_extra_env", return_value={
                "RAIATEA_VS1_PLUGIN_IO_BROKER": "/core/broker",
                "RAIATEA_PDF1C_DOCLING_WHEEL": str(self.wheel),
                "RAIATEA_PDF1C_DOCLING_ARTIFACTS": str(self.models),
                "RAIATEA_PDF1C_DOCLING_CACHE_ROOT": str(self.cache_parent),
            }),
        ):
            return self.service.extract(
                self.source_ref,
                rights_evidence_state="known-permitted",
            )


class Pdf1cServiceTests(Pdf1cServiceFixture):
    def test_denied_rights_stop_before_provider_verification_and_source_read(self) -> None:
        with (
            patch("prototype.p0_vs1.pdf1c_service.verify_reference_docling") as verify_provider,
            patch.object(self.broker, "issue_read_handle", wraps=self.broker.issue_read_handle) as issue_handle,
        ):
            with self.assertRaisesRegex(DoclingPdfExtractionError, "rights-unknown"):
                self.service.extract(
                    self.source_ref,
                    rights_evidence_state="unknown",
                )
        verify_provider.assert_not_called()
        issue_handle.assert_not_called()

    def test_success_publishes_independent_docling_current_e05_state(self) -> None:
        result = self.extract(status="success")
        self.assertTrue(result["published_current"])
        self.assertEqual(result["processing_execution"], "completed")
        payload = self.store.load().payload
        state = payload["pdf1c"]
        validate_pdf1c_state(state, "scope:pdf1c")
        current = next(row for row in state["current_extractions"] if row["source_ref_id"] == self.source_ref)
        representation = next(
            current["records"][ref["ref_id"]]
            for ref in current["record_refs"]
            if ref["record_kind"] == "NormalizedRepresentationRecord"
        )
        self.assertEqual(representation["units"][0]["semantic_role"]["value"], {"type": "heading", "level": 1})
        self.assertEqual(current["provider_observation"]["provider"], provider())

    def test_degraded_is_attempt_evidence_not_current_content(self) -> None:
        result = self.extract(status="degraded")
        self.assertFalse(result["published_current"])
        self.assertEqual(result["processing_execution"], "unknown")
        state = self.store.load().payload["pdf1c"]
        self.assertEqual(state["current_extractions"], [])
        self.assertEqual(len(state["attempts"]), 1)
        self.assertEqual(state["attempts"][0]["provider_observation"]["observation"]["status"], "degraded")

    def test_physical_source_change_after_provider_output_rejects_publication(self) -> None:
        self.configure_bundle("success")

        def mutate_source():
            path = self.root / "single.pdf"
            path.write_bytes(path.read_bytes() + b"changed-during-docling")

        FakePluginIO.on_read_completed = mutate_source
        before = self.store.load()
        with (
            patch("prototype.p0_vs1.pdf1c_service.verify_reference_docling", return_value=provider()),
            patch("prototype.p0_vs1.pdf1c_service.Vs1PluginIO", FakePluginIO),
            patch("prototype.p0_vs1.pdf1c_service.LocalPluginProcessClient", FakeClient),
            patch("prototype.p0_vs1.pdf1c_service.build_docling_extra_env", return_value={
                "RAIATEA_VS1_PLUGIN_IO_BROKER": "/core/broker",
                "RAIATEA_PDF1C_DOCLING_WHEEL": str(self.wheel),
                "RAIATEA_PDF1C_DOCLING_ARTIFACTS": str(self.models),
                "RAIATEA_PDF1C_DOCLING_CACHE_ROOT": str(self.cache_parent),
            }),
        ):
            with self.assertRaisesRegex(DoclingPdfExtractionError, "source-changed-during-plugin-run"):
                self.service.extract(self.source_ref, rights_evidence_state="known-permitted")
        self.assertEqual(self.store.load(), before)

    def test_catalog_change_during_provider_run_rejects_stale_publication(self) -> None:
        self.configure_bundle("success")
        before = self.store.load()

        def mutate_catalog(_request):
            current = self.store.load()
            payload = deepcopy(current.payload)
            payload["concurrent_marker"] = "changed"
            self.store.save(payload, expected_revision=current.revision)

        FakeClient.result_callback = mutate_catalog
        with (
            patch("prototype.p0_vs1.pdf1c_service.verify_reference_docling", return_value=provider()),
            patch("prototype.p0_vs1.pdf1c_service.Vs1PluginIO", FakePluginIO),
            patch("prototype.p0_vs1.pdf1c_service.LocalPluginProcessClient", FakeClient),
            patch("prototype.p0_vs1.pdf1c_service.build_docling_extra_env", return_value={
                "RAIATEA_VS1_PLUGIN_IO_BROKER": "/core/broker",
                "RAIATEA_PDF1C_DOCLING_WHEEL": str(self.wheel),
                "RAIATEA_PDF1C_DOCLING_ARTIFACTS": str(self.models),
                "RAIATEA_PDF1C_DOCLING_CACHE_ROOT": str(self.cache_parent),
            }),
        ):
            with self.assertRaisesRegex(DoclingPdfExtractionError, "catalog-changed-during-plugin-run"):
                self.service.extract(self.source_ref, rights_evidence_state="known-permitted")
        after = self.store.load()
        self.assertGreater(after.revision, before.revision)
        self.assertNotIn("pdf1c", after.payload)
        self.assertEqual(after.payload["concurrent_marker"], "changed")

    def test_existing_poppler_state_is_not_modified_by_docling_publication(self) -> None:
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["pdf1b"] = {"opaque": "existing-poppler-state"}
        self.store.save(payload, expected_revision=current.revision)
        before_pdf1b = deepcopy(self.store.load().payload["pdf1b"])
        result = self.extract(status="success")
        self.assertTrue(result["published_current"])
        self.assertEqual(self.store.load().payload["pdf1b"], before_pdf1b)

    def test_persisted_provider_reference_tamper_is_rejected_before_new_run(self) -> None:
        self.extract(status="success")
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["pdf1c"]["current_extractions"][0]["provider_observation"]["provider"]["model_payload_sha256"] = "sha256:" + "0" * 64
        self.store.save(payload, expected_revision=current.revision)
        with self.assertRaises(DoclingPdfExtractionError):
            self.service.extract(self.source_ref, rights_evidence_state="known-permitted")

    def test_plugin_record_ref_claim_is_rejected(self) -> None:
        self.configure_bundle("success")

        class RecordRefClient(FakeClient):
            def invoke(self, request):
                result = super().invoke(request)
                result["outputs"].append(
                    {
                        "kind": "record-ref",
                        "record_ref": {
                            "ref_id": "run:forbidden",
                            "contract_id": "raiatea.extraction.processing-run",
                            "contract_version": "0.1.0",
                            "record_kind": "ProcessingRunRecord",
                        },
                    }
                )
                return result

        before = self.store.load()
        with (
            patch("prototype.p0_vs1.pdf1c_service.verify_reference_docling", return_value=provider()),
            patch("prototype.p0_vs1.pdf1c_service.Vs1PluginIO", FakePluginIO),
            patch("prototype.p0_vs1.pdf1c_service.LocalPluginProcessClient", RecordRefClient),
            patch("prototype.p0_vs1.pdf1c_service.build_docling_extra_env", return_value={
                "RAIATEA_VS1_PLUGIN_IO_BROKER": "/core/broker",
                "RAIATEA_PDF1C_DOCLING_WHEEL": str(self.wheel),
                "RAIATEA_PDF1C_DOCLING_ARTIFACTS": str(self.models),
                "RAIATEA_PDF1C_DOCLING_CACHE_ROOT": str(self.cache_parent),
            }),
        ):
            with self.assertRaisesRegex(DoclingPdfExtractionError, "must-not-claim-core-e05-record-refs"):
                self.service.extract(self.source_ref, rights_evidence_state="known-permitted")
        self.assertEqual(self.store.load(), before)


if __name__ == "__main__":
    unittest.main()
