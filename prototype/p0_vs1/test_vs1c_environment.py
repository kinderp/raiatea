from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from prototype.p0_vs1.local_process_client import (
    LocalPluginProcessClient,
    LocalPluginProcessError,
    build_child_environment,
    normalize_product_command,
)


class Vs1cChildEnvironmentTests(unittest.TestCase):
    def test_ambient_credentials_and_pythonpath_do_not_cross_plugin_boundary(self) -> None:
        ambient = {
            "AWS_SECRET_ACCESS_KEY": "do-not-inherit",
            "GITHUB_TOKEN": "do-not-inherit",
            "OPENAI_API_KEY": "do-not-inherit",
            "HTTP_PROXY": "http://user:password@example.invalid",
            "PYTHONPATH": "/tmp/ambient-untrusted-pythonpath",
            "RAIATEA_VS1_PLUGIN_IO_BROKER": "/tmp/ambient-wrong-broker",
        }
        with patch.dict(os.environ, ambient, clear=False):
            child = build_child_environment(
                {"RAIATEA_VS1_PLUGIN_IO_BROKER": "/tmp/core-issued-broker"}
            )
        for forbidden in (
            "AWS_SECRET_ACCESS_KEY",
            "GITHUB_TOKEN",
            "OPENAI_API_KEY",
            "HTTP_PROXY",
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
            build_child_environment({"OTHER_SECRET": "not-allowed"})

    def test_manifest_python_token_uses_current_interpreter(self) -> None:
        command = normalize_product_command(
            ["python", "-m", "prototype.p0_vs1.plugins.local_source.plugin"]
        )
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(
            command[1:],
            ["-m", "prototype.p0_vs1.plugins.local_source.plugin"],
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


if __name__ == "__main__":
    unittest.main()
