from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BENCH_DIR = Path(__file__).resolve().parents[1]
ROUTES = BENCH_DIR / "routes"
LOCK = BENCH_DIR / "locks" / "docling-2.118.0-rapidocr-3.9.2-torch-en.json"
SPEC = importlib.util.spec_from_file_location(
    "p0_verify_rapidocr_reference", ROUTES / "verify_rapidocr_reference.py"
)
VERIFY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VERIFY)


class RapidOCRReferenceLockTests(unittest.TestCase):
    def _lock(self):
        return json.loads(LOCK.read_text(encoding="utf-8"))

    def _materialize_locked_payload(self, root: Path) -> None:
        # Synthetic bytes are used to exercise verifier semantics only; the
        # committed production lock itself remains the source of actual hashes.
        for index, item in enumerate(self._lock()["files"]):
            path = root / item["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((f"fixture-{index}" * 7).encode("ascii"))

    def test_missing_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            observed = VERIFY.payload_manifest(Path(tmp) / "missing")
            result = VERIFY.verify(self._lock(), observed)
            self.assertFalse(result["verified"])
            self.assertFalse(result["checks"]["exists"])

    def test_exact_synthetic_lock_can_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._materialize_locked_payload(root)
            observed = VERIFY.payload_manifest(root)
            synthetic_lock = {
                "profile_id": "synthetic",
                "file_count": observed["file_count"],
                "bytes": observed["bytes"],
                "files": observed["files"],
                "manifest_sha256": observed["manifest_sha256"],
            }
            result = VERIFY.verify(synthetic_lock, observed)
            self.assertTrue(result["verified"])
            self.assertTrue(all(result["checks"].values()))

    def test_single_byte_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._materialize_locked_payload(root)
            observed = VERIFY.payload_manifest(root)
            synthetic_lock = {
                "profile_id": "synthetic",
                "file_count": observed["file_count"],
                "bytes": observed["bytes"],
                "files": observed["files"],
                "manifest_sha256": observed["manifest_sha256"],
            }
            first = root / observed["files"][0]["path"]
            first.write_bytes(first.read_bytes() + b"x")
            drifted = VERIFY.payload_manifest(root)
            result = VERIFY.verify(synthetic_lock, drifted)
            self.assertFalse(result["verified"])
            self.assertFalse(result["checks"]["files"])
            self.assertFalse(result["checks"]["manifest_sha256"])

    def test_extra_file_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._materialize_locked_payload(root)
            observed = VERIFY.payload_manifest(root)
            synthetic_lock = {
                "profile_id": "synthetic",
                "file_count": observed["file_count"],
                "bytes": observed["bytes"],
                "files": observed["files"],
                "manifest_sha256": observed["manifest_sha256"],
            }
            (root / "unexpected.bin").write_bytes(b"unexpected")
            result = VERIFY.verify(synthetic_lock, VERIFY.payload_manifest(root))
            self.assertFalse(result["verified"])
            self.assertFalse(result["checks"]["file_count"])
            self.assertFalse(result["checks"]["files"])


if __name__ == "__main__":
    unittest.main()
