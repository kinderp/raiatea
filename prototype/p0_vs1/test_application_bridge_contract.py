from __future__ import annotations

import json
from pathlib import Path
import unittest

from prototype.p0_vs1.application_bridge_contract import (
    ApplicationBridgeContractError,
    BRIDGE_VERSION,
    METHOD_GATEWAY_STATUS,
    METHOD_LIBRARY_PAGE,
    decode_frame,
    encode_frame,
    error_message,
    request_message,
    result_message,
    validate_result_envelope,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_LIBRARY_FIXTURE = (
    REPO_ROOT
    / "frontend"
    / "src"
    / "gateway"
    / "fixtures"
    / "bridge-library-page.json"
)


class ApplicationBridgeContractTests(unittest.TestCase):
    def test_result_allows_application_content_metadata(self) -> None:
        response = result_message(
            "rpc:1",
            METHOD_GATEWAY_STATUS,
            {
                "content": {"byte_length": 42},
                "current_relative_location": "Books/example.epub",
            },
        )
        round_trip = decode_frame(encode_frame(response))
        self.assertEqual(round_trip, response)
        self.assertEqual(round_trip["result"]["bridge_version"], BRIDGE_VERSION)

    def test_shared_library_fixture_is_valid_python_bridge_evidence(self) -> None:
        fixture = json.loads(SHARED_LIBRARY_FIXTURE.read_text(encoding="utf-8"))
        validated = validate_result_envelope(fixture)
        self.assertEqual(validated["bridge_version"], BRIDGE_VERSION)
        self.assertEqual(validated["method"], METHOD_LIBRARY_PAGE)
        self.assertEqual(
            validated["payload"]["items"][0]["location"]["current_relative_location"],
            "Books/fixture.epub",
        )

    def test_host_authority_fields_are_rejected_recursively(self) -> None:
        for forbidden in (
            "path",
            "file_path",
            "host_path",
            "absolute_path",
            "root",
            "catalog_store_path",
            "cwd",
        ):
            with self.subTest(forbidden=forbidden):
                with self.assertRaisesRegex(
                    ApplicationBridgeContractError,
                    "bridge-host-authority-field-forbidden",
                ):
                    validate_result_envelope(
                        {
                            "bridge_version": BRIDGE_VERSION,
                            "method": METHOD_GATEWAY_STATUS,
                            "payload": {"nested": {forbidden: "/tmp/private"}},
                        }
                    )

    def test_request_shape_is_closed_and_notifications_are_not_supported(self) -> None:
        with self.assertRaisesRegex(
            ApplicationBridgeContractError,
            "bridge-request-shape-invalid",
        ):
            decode_frame('{"jsonrpc":"2.0","method":"gateway.status","params":{}}\n')

        with self.assertRaisesRegex(
            ApplicationBridgeContractError,
            "bridge-request-shape-invalid",
        ):
            decode_frame(
                '{"jsonrpc":"2.0","id":"1","method":"gateway.status","params":{},"extra":true}\n'
            )

    def test_request_and_protocol_error_round_trip(self) -> None:
        request = request_message("rpc:2", METHOD_GATEWAY_STATUS, {})
        self.assertEqual(decode_frame(encode_frame(request)), request)
        error = error_message("rpc:2", -32602, "bridge-page-size-invalid")
        self.assertEqual(decode_frame(encode_frame(error)), error)

    def test_frame_size_is_bounded_before_decode(self) -> None:
        huge = "x" * (1024 * 1024)
        with self.assertRaisesRegex(
            ApplicationBridgeContractError,
            "bridge-frame-too-large",
        ):
            decode_frame((huge + "\n").encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
