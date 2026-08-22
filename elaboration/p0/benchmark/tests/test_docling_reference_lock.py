from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES_DIR = BENCH_DIR / "routes"
SPEC = importlib.util.spec_from_file_location(
    "p0_verify_docling_reference", ROUTES_DIR / "verify_docling_reference.py"
)
VERIFY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VERIFY)


class DoclingReferenceLockTests(unittest.TestCase):
    def test_model_payload_excludes_ephemeral_cache_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model"
            cache = model / ".cache" / "huggingface" / "download"
            cache.mkdir(parents=True)
            (model / "weights.bin").write_bytes(b"stable")
            (cache / "weights.bin.metadata").write_text("variable", encoding="utf-8")
            first = VERIFY.model_payload_manifest(root)
            (cache / "weights.bin.metadata").write_text("different", encoding="utf-8")
            second = VERIFY.model_payload_manifest(root)
        self.assertEqual(first["file_count"], 1)
        self.assertEqual(first["files"][0]["path"], "model/weights.bin")
        self.assertEqual(
            first["payload_manifest_sha256"], second["payload_manifest_sha256"]
        )

    def test_reference_verifier_matches_exact_environment_and_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            constraints = root / "constraints.txt"
            constraints.write_text("alpha==1\nbeta==2\n", encoding="utf-8")
            artifacts = root / "artifacts"
            artifacts.mkdir()
            (artifacts / "weights.bin").write_bytes(b"weights")
            manifest = VERIFY.model_payload_manifest(artifacts)
            lock = root / "model-lock.json"
            lock.write_text(
                json.dumps(
                    {
                        "file_count": manifest["file_count"],
                        "bytes": manifest["bytes"],
                        "files": manifest["files"],
                        "payload_manifest_sha256": manifest[
                            "payload_manifest_sha256"
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                VERIFY, "installed_freeze", return_value=["alpha==1", "beta==2"]
            ):
                report = VERIFY.verify_reference(constraints, lock, artifacts)
        self.assertTrue(report["verified"])
        self.assertTrue(report["environment"]["match"])
        self.assertTrue(report["model_payload"]["match"])

    def test_reference_verifier_fails_closed_on_dependency_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            constraints = root / "constraints.txt"
            constraints.write_text("alpha==1\n", encoding="utf-8")
            artifacts = root / "artifacts"
            artifacts.mkdir()
            (artifacts / "weights.bin").write_bytes(b"weights")
            manifest = VERIFY.model_payload_manifest(artifacts)
            lock = root / "model-lock.json"
            lock.write_text(
                json.dumps(
                    {
                        "file_count": manifest["file_count"],
                        "bytes": manifest["bytes"],
                        "files": manifest["files"],
                        "payload_manifest_sha256": manifest[
                            "payload_manifest_sha256"
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                VERIFY, "installed_freeze", return_value=["alpha==2"]
            ):
                report = VERIFY.verify_reference(constraints, lock, artifacts)
        self.assertFalse(report["verified"])
        self.assertEqual(report["environment"]["missing"], ["alpha==1"])
        self.assertEqual(report["environment"]["unexpected"], ["alpha==2"])


if __name__ == "__main__":
    unittest.main()
