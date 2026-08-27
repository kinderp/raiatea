from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1 import docling_reference
from prototype.p0_vs1 import local_process_client as process_client
from prototype.p0_vs1.docling_observation_contract import (
    DOCLING_OBSERVATION_MEDIA_TYPE,
    DOCLING_OBSERVATION_VERSION,
    DOCLING_PROFILE,
)
from prototype.p0_vs1.docling_process_environment import (
    ARTIFACTS_ENV,
    BROKER_ENV,
    CACHE_ENV,
    WHEEL_ENV,
    build_docling_extra_env,
)
from prototype.p0_vs1.local_process_client import (
    LocalPluginProcessClient,
    LocalPluginProcessError,
    build_child_environment,
    normalize_product_command,
)
from prototype.p0_vs1.plugins.docling_pdf import plugin


SOURCE_REF = "source-ref:" + "1" * 64
FINGERPRINT = "sha256:" + "a" * 64
DOCLING_MANIFEST_IDENTITY = {"plugin": {"plugin_id": "org.raiatea.pdf1.docling-extractor"}}


def provider() -> dict:
    return {
        "provider_id": "docling",
        "version": docling_reference.DOCLING_VERSION,
        "wheel_sha256": "sha256:" + docling_reference.DOCLING_WHEEL_SHA256,
        "environment_freeze_sha256": "sha256:" + docling_reference.ENVIRONMENT_FREEZE_SHA256,
        "model_payload_sha256": "sha256:" + docling_reference.MODEL_PAYLOAD_SHA256,
    }


def observation_bundle() -> dict:
    return {
        "bundle_version": DOCLING_OBSERVATION_VERSION,
        "record_kind": "DoclingObservationBundle",
        "source_ref_id": SOURCE_REF,
        "source_fingerprint": FINGERPRINT,
        "provider": provider(),
        "route_profile": DOCLING_PROFILE,
        "observation": {
            "status": "success",
            "provider_conversion_status": "ConversionStatus.SUCCESS",
            "warnings": [],
            "body_order_source": "body.children",
            "blocks": [],
            "picture_collection_state": "present",
            "pictures": [],
            "caption_blocks": [],
            "picture_caption_relations": [],
            "raw_document_sha256": "sha256:" + "b" * 64,
        },
    }


def request() -> dict:
    return {
        "invocation_id": "invoke:pdf1c:test",
        "capability": {"capability_id": "extract.run", "profile_id": DOCLING_PROFILE},
        "inputs": [
            {
                "kind": "asset-handle",
                "handle": {
                    "handle_id": "asset:test",
                    "lease_id": "lease:test",
                    "access": "read",
                    "media_type": "application/pdf",
                    "byte_length": 10,
                    "fingerprint": FINGERPRINT,
                    "expires_at": "2099-01-01T00:00:00Z",
                },
            },
            {
                "kind": "record-ref",
                "record_ref": {
                    "ref_id": SOURCE_REF,
                    "contract_id": "raiatea.vs1.source-reference",
                    "contract_version": "0.1.0",
                    "record_kind": "SourceReferenceRecord",
                },
            },
        ],
        "output_targets": [
            {
                "handle_id": "output:test",
                "lease_id": "lease:output",
                "access": "write-once-output",
                "media_type": DOCLING_OBSERVATION_MEDIA_TYPE,
                "max_byte_length": 1024 * 1024,
                "expires_at": "2099-01-01T00:00:00Z",
            }
        ],
        "runtime_context": {
            "workspace_scope_id": "scope:test",
            "rights_decision_ref": "rights-decision:" + "c" * 64,
            "secret_leases": [],
        },
    }


class Pdf1cProcessEnvironmentTests(unittest.TestCase):
    def test_core_builder_returns_only_broker_and_docling_installation_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            wheel = base / "docling.whl"
            wheel.write_bytes(b"wheel")
            models = base / "models"
            models.mkdir()
            cache = base / "cache"
            env = build_docling_extra_env(
                {BROKER_ENV: str(base / "broker.json")},
                wheel_path=wheel,
                artifacts_path=models,
                cache_root=cache,
            )
        self.assertEqual(set(env), {BROKER_ENV, WHEEL_ENV, ARTIFACTS_ENV, CACHE_ENV})
        self.assertTrue(Path(env[WHEEL_ENV]).is_absolute())
        self.assertTrue(Path(env[ARTIFACTS_ENV]).is_absolute())
        self.assertTrue(Path(env[CACHE_ENV]).is_absolute())

    def test_child_environment_does_not_inherit_credentials_or_ambient_docling_refs(self) -> None:
        supplied = {
            BROKER_ENV: "/core/broker",
            WHEEL_ENV: "/core/docling.whl",
            ARTIFACTS_ENV: "/core/models",
            CACHE_ENV: "/core/cache",
        }
        ambient = {
            "OPENAI_API_KEY": "secret",
            "HTTP_PROXY": "http://secret.invalid",
            "PATH": "/ambient/untrusted/tools",
            WHEEL_ENV: "/ambient/wrong.whl",
            ARTIFACTS_ENV: "/ambient/wrong-models",
        }
        with (
            patch.dict(os.environ, ambient, clear=False),
            patch.object(
                process_client,
                "resolve_docling_compiler_toolchain_path",
                return_value="/core/reference-tools",
            ),
        ):
            child = build_child_environment(
                supplied,
                manifest=DOCLING_MANIFEST_IDENTITY,
            )
        self.assertNotIn("OPENAI_API_KEY", child)
        self.assertNotIn("HTTP_PROXY", child)
        self.assertEqual(child["PATH"], "/core/reference-tools")
        self.assertNotEqual(child["PATH"], ambient["PATH"])
        for key, value in supplied.items():
            self.assertEqual(child[key], value)

    def test_linux_toolchain_resolver_uses_os_default_path_and_explicit_cc1plus(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            system_bin = base / "system-bin"
            gcc_libexec = base / "gcc-libexec"
            system_bin.mkdir()
            gcc_libexec.mkdir()
            tools = {}
            for name in ("g++", "gcc", "as", "ld"):
                tool = system_bin / name
                tool.write_text("tool", encoding="utf-8")
                tools[name] = tool
            cc1plus = gcc_libexec / "cc1plus"
            cc1plus.write_text("tool", encoding="utf-8")

            which_calls: list[tuple[str, str | None]] = []

            def fake_which(name: str, path: str | None = None) -> str | None:
                which_calls.append((name, path))
                value = tools.get(name)
                return str(value) if value is not None else None

            completed = subprocess.CompletedProcess(
                [str(tools["g++"]), "-print-prog-name=cc1plus"],
                0,
                stdout=str(cc1plus) + "\n",
                stderr="",
            )
            with (
                patch.object(process_client.sys, "platform", "linux"),
                patch.object(process_client.shutil, "which", side_effect=fake_which),
                patch.object(process_client.subprocess, "run", return_value=completed) as run,
            ):
                value = process_client.resolve_docling_compiler_toolchain_path()

        self.assertEqual(
            value,
            os.pathsep.join((str(system_bin), str(gcc_libexec))),
        )
        self.assertEqual(
            which_calls,
            [("g++", os.defpath), ("gcc", os.defpath), ("as", os.defpath), ("ld", os.defpath)],
        )
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][0], str(tools["g++"].resolve()))

    def test_non_linux_docling_environment_adds_no_compiler_path(self) -> None:
        with patch.object(process_client.sys, "platform", "win32"):
            child = build_child_environment(
                {BROKER_ENV: "C:\\core\\broker"},
                manifest=DOCLING_MANIFEST_IDENTITY,
            )
        self.assertNotIn("PATH", child)

    def test_arbitrary_extra_environment_remains_forbidden(self) -> None:
        with self.assertRaisesRegex(LocalPluginProcessError, "extra-environment-key-forbidden"):
            build_child_environment(
                {"RAIATEA_PDF1C_ARBITRARY": "/tmp/no"},
                manifest=DOCLING_MANIFEST_IDENTITY,
            )

    def test_official_docling_identity_locks_command(self) -> None:
        manifest = DOCLING_MANIFEST_IDENTITY
        command = normalize_product_command(
            ["python", "-m", "prototype.p0_vs1.plugins.docling_pdf.plugin"],
            manifest,
        )
        self.assertEqual(command[1:], ["-m", "prototype.p0_vs1.plugins.docling_pdf.plugin"])
        with self.assertRaisesRegex(LocalPluginProcessError, "official-docling-command-forbidden"):
            normalize_product_command(["python", "-m", "prototype.p0_vs1.plugins.poppler_pdf.plugin"], manifest)

    def test_docling_timeout_extension_is_opt_in_and_absolutely_bounded(self) -> None:
        manifest = {"permissions": {"resource_hints": {"timeout_seconds": 300}}}
        client = LocalPluginProcessClient(
            ["python", "-c", "pass"],
            manifest,
            max_invocation_timeout_seconds=300,
        )
        self.assertEqual(client.max_invocation_timeout_seconds, 300.0)
        deadline = datetime.now(timezone.utc) + timedelta(minutes=10)
        timeout = client._invocation_timeout({"deadline_at": deadline.isoformat().replace("+00:00", "Z")})
        self.assertLessEqual(timeout, 300.0)
        with self.assertRaisesRegex(LocalPluginProcessError, "max-invocation-timeout-invalid"):
            LocalPluginProcessClient(
                ["python", "-c", "pass"],
                manifest,
                max_invocation_timeout_seconds=301,
            )

    def test_plugin_verifies_provider_before_reading_pdf_bytes(self) -> None:
        req = request()
        fake_paths = (Path("/provider/docling.whl"), Path("/provider/models"), Path("/provider/cache"))
        with (
            patch.object(plugin, "read_docling_provider_paths_from_env", return_value=fake_paths),
            patch.object(plugin, "verify_reference_docling", side_effect=ValueError("drift")),
            patch.object(plugin, "plugin_read_handle") as read_handle,
        ):
            result, diagnostics = plugin._invoke(
                plugin._manifest(),
                "runtime:pdf1c:test",
                req,
            )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(diagnostics, [])
        read_handle.assert_not_called()

    def test_plugin_emits_only_provider_observation_asset(self) -> None:
        req = request()
        fake_paths = (Path("/provider/docling.whl"), Path("/provider/models"), Path("/provider/cache"))
        completed = {
            "handle_id": "output:test",
            "lease_id": "lease:output",
            "access": "read",
            "media_type": DOCLING_OBSERVATION_MEDIA_TYPE,
            "byte_length": 100,
            "fingerprint": "sha256:" + "d" * 64,
            "expires_at": "2099-01-01T00:00:00Z",
        }
        with (
            patch.object(plugin, "read_docling_provider_paths_from_env", return_value=fake_paths),
            patch.object(plugin, "verify_reference_docling", return_value=provider()),
            patch.object(plugin, "plugin_read_handle", return_value=b"pdf-bytes"),
            patch.object(plugin, "run_docling_pdf", return_value=observation_bundle()),
            patch.object(plugin, "plugin_write_output", return_value=completed) as write_output,
        ):
            result, diagnostics = plugin._invoke(
                plugin._manifest(),
                "runtime:pdf1c:test",
                req,
            )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["outputs"], [{"kind": "asset-handle", "handle": completed}])
        self.assertEqual(len(diagnostics), 1)
        payload = write_output.call_args.args[1]
        decoded = json.loads(payload.decode("utf-8"))
        self.assertEqual(decoded["record_kind"], "DoclingObservationBundle")
        self.assertNotIn("ProcessingRunRecord", payload.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
