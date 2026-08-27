from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1 import docling_reference as reference


GOOD_PLATFORM = {
    "system": "Linux",
    "machine": "x86_64",
    "python_version": "3.12.14",
    "os_id": "ubuntu",
    "os_version_id": "24.04",
}


def expected_model_manifest() -> dict:
    lock = json.loads(reference.DEFAULT_MODEL_LOCK.read_text(encoding="utf-8"))
    return {
        "file_count": lock["file_count"],
        "bytes": lock["bytes"],
        "files": deepcopy(lock["files"]),
        "payload_manifest_sha256": lock["payload_manifest_sha256"],
    }


class Pdf1cDoclingReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.wheel = self.base / "docling-2.118.0-py3-none-any.whl"
        self.wheel.write_bytes(b"placeholder-wheel")
        self.models = self.base / "models"
        self.models.mkdir()
        self.freeze = reference.load_constraints()
        self.model_manifest = expected_model_manifest()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def verify(self, **overrides):
        kwargs = {
            "wheel_path": self.wheel,
            "artifacts_path": self.models,
            "observed_freeze": self.freeze,
            "platform_facts": GOOD_PLATFORM,
        }
        kwargs.update(overrides)
        with (
            patch.object(reference, "_sha256_file", return_value=reference.DOCLING_WHEEL_SHA256),
            patch.object(reference, "model_payload_manifest", return_value=deepcopy(self.model_manifest)),
            patch.object(reference.importlib.metadata, "version", return_value=reference.DOCLING_VERSION),
        ):
            return reference.verify_reference_docling(**kwargs)

    def test_exact_reference_returns_path_free_provider_record(self) -> None:
        provider = self.verify()
        self.assertEqual(
            provider,
            {
                "provider_id": "docling",
                "version": "2.118.0",
                "wheel_sha256": "sha256:" + reference.DOCLING_WHEEL_SHA256,
                "environment_freeze_sha256": "sha256:" + reference.ENVIRONMENT_FREEZE_SHA256,
                "model_payload_sha256": "sha256:" + reference.MODEL_PAYLOAD_SHA256,
            },
        )
        serialized = json.dumps(provider, sort_keys=True)
        self.assertNotIn(str(self.base), serialized)
        self.assertNotIn("path", serialized.casefold())
        self.assertIs(reference.validate_reference_provider_record(provider), provider)

    def test_platform_reference_is_exact(self) -> None:
        cases = (
            ("system", "Windows", "platform-system"),
            ("machine", "aarch64", "platform-machine"),
            ("python_version", "3.12.13", "python-version"),
            ("os_id", "debian", "os-id"),
            ("os_version_id", "24.10", "os-version"),
        )
        for key, value, message in cases:
            with self.subTest(key=key):
                facts = dict(GOOD_PLATFORM)
                facts[key] = value
                with self.assertRaisesRegex(reference.DoclingReferenceError, message):
                    self.verify(platform_facts=facts)

    def test_wheel_fingerprint_drift_fails_closed(self) -> None:
        with (
            patch.object(reference, "_sha256_file", return_value="0" * 64),
            patch.object(reference, "model_payload_manifest", return_value=deepcopy(self.model_manifest)),
            patch.object(reference.importlib.metadata, "version", return_value=reference.DOCLING_VERSION),
        ):
            with self.assertRaisesRegex(reference.DoclingReferenceError, "wheel-fingerprint"):
                reference.verify_reference_docling(
                    wheel_path=self.wheel,
                    artifacts_path=self.models,
                    observed_freeze=self.freeze,
                    platform_facts=GOOD_PLATFORM,
                )

    def test_installed_environment_must_match_full_constraints(self) -> None:
        changed = list(self.freeze)
        changed[-1] = changed[-1].split("==", 1)[0] + "==0"
        with self.assertRaisesRegex(reference.DoclingReferenceError, "environment-mismatch"):
            self.verify(observed_freeze=changed)

    def test_real_installed_environment_uses_canonical_distribution_identity(self) -> None:
        versions = {}
        for spec in self.freeze:
            name, version = spec.split("==", 1)
            versions[reference._canonical_package_name(name)] = version

        def installed_version(name: str) -> str:
            return versions[reference._canonical_package_name(name)]

        with (
            patch.object(reference, "_sha256_file", return_value=reference.DOCLING_WHEEL_SHA256),
            patch.object(reference, "model_payload_manifest", return_value=deepcopy(self.model_manifest)),
            patch.object(reference.importlib.metadata, "version", side_effect=installed_version),
        ):
            provider = reference.verify_reference_docling(
                wheel_path=self.wheel,
                artifacts_path=self.models,
                observed_freeze=None,
                platform_facts=GOOD_PLATFORM,
            )
        self.assertEqual(provider["version"], reference.DOCLING_VERSION)

    def test_installed_docling_version_mismatch_fails(self) -> None:
        with (
            patch.object(reference, "_sha256_file", return_value=reference.DOCLING_WHEEL_SHA256),
            patch.object(reference, "model_payload_manifest", return_value=deepcopy(self.model_manifest)),
            patch.object(reference.importlib.metadata, "version", return_value="2.118.1"),
        ):
            with self.assertRaisesRegex(reference.DoclingReferenceError, "package-version"):
                reference.verify_reference_docling(
                    wheel_path=self.wheel,
                    artifacts_path=self.models,
                    observed_freeze=self.freeze,
                    platform_facts=GOOD_PLATFORM,
                )

    def test_constraint_lock_drift_fails_before_environment_acceptance(self) -> None:
        constraints = self.base / "constraints.txt"
        constraints.write_text("docling==2.118.0\n", encoding="utf-8")
        with self.assertRaisesRegex(reference.DoclingReferenceError, "constraints-drift"):
            self.verify(constraints_path=constraints, observed_freeze=["docling==2.118.0"])

    def test_model_payload_drift_fails_closed(self) -> None:
        cases = (
            ("file_count", reference.MODEL_FILE_COUNT - 1, "model-file-count"),
            ("bytes", reference.MODEL_BYTES - 1, "model-byte-count"),
            ("payload_manifest_sha256", "0" * 64, "model-manifest"),
        )
        for key, value, message in cases:
            with self.subTest(key=key):
                observed = deepcopy(self.model_manifest)
                observed[key] = value
                with (
                    patch.object(reference, "_sha256_file", return_value=reference.DOCLING_WHEEL_SHA256),
                    patch.object(reference, "model_payload_manifest", return_value=observed),
                    patch.object(reference.importlib.metadata, "version", return_value=reference.DOCLING_VERSION),
                ):
                    with self.assertRaisesRegex(reference.DoclingReferenceError, message):
                        reference.verify_reference_docling(
                            wheel_path=self.wheel,
                            artifacts_path=self.models,
                            observed_freeze=self.freeze,
                            platform_facts=GOOD_PLATFORM,
                        )

    def test_model_file_identity_drift_fails_even_when_totals_match(self) -> None:
        observed = deepcopy(self.model_manifest)
        observed["files"][0]["sha256"] = "0" * 64
        with (
            patch.object(reference, "_sha256_file", return_value=reference.DOCLING_WHEEL_SHA256),
            patch.object(reference, "model_payload_manifest", return_value=observed),
            patch.object(reference.importlib.metadata, "version", return_value=reference.DOCLING_VERSION),
        ):
            with self.assertRaisesRegex(reference.DoclingReferenceError, "model-files-mismatch"):
                reference.verify_reference_docling(
                    wheel_path=self.wheel,
                    artifacts_path=self.models,
                    observed_freeze=self.freeze,
                    platform_facts=GOOD_PLATFORM,
                )

    def test_persisted_provider_record_must_keep_exact_reference(self) -> None:
        provider = self.verify()
        for key in ("wheel_sha256", "environment_freeze_sha256", "model_payload_sha256"):
            with self.subTest(key=key):
                changed = deepcopy(provider)
                changed[key] = "sha256:" + "0" * 64
                with self.assertRaises(reference.DoclingReferenceError):
                    reference.validate_reference_provider_record(changed)


if __name__ == "__main__":
    unittest.main()
