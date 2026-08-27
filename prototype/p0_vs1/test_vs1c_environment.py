from __future__ import annotations

import os
from pathlib import Path
import queue
import sys
import unittest
from unittest.mock import patch

from prototype.p0_vs1 import local_process_client as process_client
from prototype.p0_vs1.local_process_client import (
    MAX_STDOUT_BUFFERED_FRAMES,
    LocalPluginProcessClient,
    LocalPluginProcessError,
    build_child_environment,
    normalize_product_command,
)


LOCAL_SOURCE_MANIFEST = {
    "plugin": {"plugin_id": "org.raiatea.vs1.local-source"},
    "permissions": {"resource_hints": {"timeout_seconds": 30}},
}


class Vs1cChildEnvironmentTests(unittest.TestCase):
    def test_ambient_credentials_and_pythonpath_do_not_cross_plugin_boundary(self) -> None:
        ambient = {
            "AWS_SECRET_ACCESS_KEY": "do-not-inherit",
            "GITHUB_TOKEN": "do-not-inherit",
            "OPENAI_API_KEY": "do-not-inherit",
            "HTTP_PROXY": "http://user:password@example.invalid",
            "PATH": "/tmp/ambient-untrusted-tools",
            "PYTHONPATH": "/tmp/ambient-untrusted-pythonpath",
            "RAIATEA_VS1_PLUGIN_IO_BROKER": "/tmp/ambient-wrong-broker",
        }
        with patch.dict(os.environ, ambient, clear=False):
            child = build_child_environment(
                {"RAIATEA_VS1_PLUGIN_IO_BROKER": "/tmp/core-issued-broker"},
                manifest=LOCAL_SOURCE_MANIFEST,
            )
        for forbidden in (
            "AWS_SECRET_ACCESS_KEY",
            "GITHUB_TOKEN",
            "OPENAI_API_KEY",
            "HTTP_PROXY",
            "PATH",
        ):
            self.assertNotIn(forbidden, child)
        self.assertEqual(
            child["RAIATEA_VS1_PLUGIN_IO_BROKER"],
            "/tmp/core-issued-broker",
        )
        self.assertNotEqual(child["PYTHONPATH"], ambient["PYTHONPATH"])
        self.assertTrue(Path(child["PYTHONPATH"]).is_absolute())
        self.assertEqual(child["PYTHONNOUSERSITE"], "1")
        self.assertEqual(child["PYTHONDONTWRITEBYTECODE"], "1")

    def test_only_core_declared_vs1c_extra_environment_key_is_allowed(self) -> None:
        with self.assertRaisesRegex(
            LocalPluginProcessError,
            "extra-environment-key-forbidden",
        ):
            build_child_environment(
                {"OTHER_SECRET": "not-allowed"},
                manifest=LOCAL_SOURCE_MANIFEST,
            )

    def test_local_source_cannot_receive_docling_provider_authority(self) -> None:
        for key in (
            "RAIATEA_PDF1C_DOCLING_WHEEL",
            "RAIATEA_PDF1C_DOCLING_ARTIFACTS",
            "RAIATEA_PDF1C_DOCLING_CACHE_ROOT",
        ):
            with self.subTest(key=key):
                with self.assertRaisesRegex(
                    LocalPluginProcessError,
                    "extra-environment-key-forbidden",
                ):
                    build_child_environment(
                        {
                            "RAIATEA_VS1_PLUGIN_IO_BROKER": "/tmp/core-issued-broker",
                            key: "/tmp/docling-authority",
                        },
                        manifest=LOCAL_SOURCE_MANIFEST,
                    )

    def test_local_source_never_resolves_or_receives_docling_compiler_path(self) -> None:
        with patch.object(
            process_client,
            "resolve_docling_compiler_toolchain_path",
            return_value="/should/not/be/used",
        ) as resolver:
            child = build_child_environment(
                {"RAIATEA_VS1_PLUGIN_IO_BROKER": "/tmp/core-issued-broker"},
                manifest=LOCAL_SOURCE_MANIFEST,
            )
        resolver.assert_not_called()
        self.assertNotIn("PATH", child)

    def test_manifest_python_token_uses_current_interpreter(self) -> None:
        command = normalize_product_command(
            ["python", "-m", "prototype.p0_vs1.plugins.local_source.plugin"]
        )
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(
            command[1:],
            ["-m", "prototype.p0_vs1.plugins.local_source.plugin"],
        )

    def test_official_local_source_identity_cannot_select_another_command(self) -> None:
        with self.assertRaisesRegex(
            LocalPluginProcessError,
            "official-local-source-command-forbidden",
        ):
            LocalPluginProcessClient(
                [sys.executable, "-c", "print('not the official plugin')"],
                LOCAL_SOURCE_MANIFEST,
            )

    def test_unresponsive_plugin_handshake_times_out_and_can_be_closed(self) -> None:
        client = LocalPluginProcessClient(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            {"permissions": {"resource_hints": {"timeout_seconds": 30}}},
        )
        try:
            with patch(
                "prototype.p0_vs1.local_process_client.HANDSHAKE_TIMEOUT_SECONDS",
                0.2,
            ):
                with self.assertRaisesRegex(
                    LocalPluginProcessError,
                    "response-timeout",
                ):
                    client.handshake()
        finally:
            client.close()
        self.assertIsNone(client.process)

    def test_stdout_frame_queue_is_bounded(self) -> None:
        client = LocalPluginProcessClient(
            [sys.executable, "-c", "pass"],
            {"permissions": {"resource_hints": {"timeout_seconds": 30}}},
        )
        self.assertEqual(client._stdout_queue.maxsize, MAX_STDOUT_BUFFERED_FRAMES)
        for _ in range(MAX_STDOUT_BUFFERED_FRAMES):
            client._stdout_queue.put_nowait(b"{}\n")
        with self.assertRaises(queue.Full):
            client._stdout_queue.put_nowait(b"overflow\n")


if __name__ == "__main__":
    unittest.main()
