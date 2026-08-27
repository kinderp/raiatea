from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from prototype.p0_vs1 import docling_environment as env


class Pdf1cDoclingEnvironmentTests(unittest.TestCase):
    def test_reference_record_is_exact_and_disables_enrichment(self) -> None:
        record = env.reference_environment_record()
        self.assertIs(env.validate_reference_environment_record(record), record)
        for key in (
            "remote_services_enabled",
            "external_plugins_enabled",
            "ocr_enabled",
            "table_structure_enabled",
            "code_enrichment_enabled",
            "formula_enrichment_enabled",
            "picture_classification_enabled",
            "picture_description_enabled",
            "chart_extraction_enabled",
        ):
            self.assertIs(record[key], False)

    def test_environment_drift_fails_closed(self) -> None:
        mutations = {
            "docling_version": "2.119.0",
            "wheel_sha256": "0" * 64,
            "environment_freeze_sha256": "1" * 64,
            "model_payload_sha256": "2" * 64,
            "platform": "windows",
            "python_version": "3.12.13",
            "architecture": "aarch64",
            "ocr_enabled": True,
            "table_structure_enabled": True,
            "formula_enrichment_enabled": True,
            "remote_services_enabled": True,
            "external_plugins_enabled": True,
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                record = env.reference_environment_record()
                record[key] = value
                with self.assertRaises(env.DoclingEnvironmentError):
                    env.validate_reference_environment_record(record)

    def test_repository_model_lock_matches_promoted_reference(self) -> None:
        lock = env.load_model_lock()
        self.assertEqual(lock["docling_version"], "2.118.0")
        self.assertEqual(lock["file_count"], 11)
        self.assertEqual(lock["bytes"], 342_987_978)
        self.assertEqual(
            lock["payload_manifest_sha256"],
            "c9afe973808a41c359c1f270f063097972985c096468089b206031395f8a885e",
        )

    def test_model_payload_hash_and_size_are_verified_byte_for_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "models"
            root.mkdir()
            relative = "layout/model.bin"
            target = root / relative
            target.parent.mkdir(parents=True)
            payload = b"exact-model-payload"
            target.write_bytes(payload)
            sha = hashlib.sha256(payload).hexdigest()
            lock = {
                "contract": {"name": "test", "version": "0", "scope": "test"},
                "docling_version": "2.118.0",
                "download_component": "layout",
                "file_count": 1,
                "bytes": len(payload),
                "files": [{"path": relative, "bytes": len(payload), "sha256": sha}],
                "payload_manifest_sha256": "a" * 64,
            }
            lock_path = base / "lock.json"
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            patches = (
                mock.patch.object(env, "MODEL_LOCK_PATH", lock_path),
                mock.patch.object(env, "DOCLING_MODEL_FILE_COUNT", 1),
                mock.patch.object(env, "DOCLING_MODEL_BYTES", len(payload)),
                mock.patch.object(env, "DOCLING_MODEL_PAYLOAD_SHA256", "a" * 64),
            )
            with patches[0], patches[1], patches[2], patches[3]:
                result = env.verify_model_payload(root)
                self.assertEqual(result["bytes"], len(payload))
                target.write_bytes(payload + b"x")
                with self.assertRaises(env.DoclingEnvironmentError):
                    env.verify_model_payload(root)

    def test_model_lock_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "models"
            root.mkdir()
            lock = {
                "contract": {"name": "test", "version": "0", "scope": "test"},
                "docling_version": "2.118.0",
                "download_component": "layout",
                "file_count": 1,
                "bytes": 1,
                "files": [{"path": "../escape", "bytes": 1, "sha256": "0" * 64}],
                "payload_manifest_sha256": "b" * 64,
            }
            lock_path = base / "lock.json"
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            with (
                mock.patch.object(env, "MODEL_LOCK_PATH", lock_path),
                mock.patch.object(env, "DOCLING_MODEL_FILE_COUNT", 1),
                mock.patch.object(env, "DOCLING_MODEL_BYTES", 1),
                mock.patch.object(env, "DOCLING_MODEL_PAYLOAD_SHA256", "b" * 64),
            ):
                with self.assertRaisesRegex(env.DoclingEnvironmentError, "traversal"):
                    env.verify_model_payload(root)


if __name__ == "__main__":
    unittest.main()
