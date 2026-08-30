from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from prototype.p0_vs1.application_bridge_contract import (
    METHOD_GATEWAY_STATUS,
    METHOD_LIBRARY_PAGE,
    METHOD_REPRESENTATION_PAGE,
    METHOD_SEARCH_PAGE,
    METHOD_SOURCE_DETAIL,
    decode_frame,
    encode_frame,
    request_message,
)
from prototype.p0_vs1.application_bridge_sidecar import (
    ApplicationBridgeService,
    JSONRPC_INVALID_PARAMS,
    JSONRPC_METHOD_NOT_FOUND,
    handle_request,
)
from prototype.p0_vs1.application_facade import RaiateaApplicationFacade
from prototype.p0_vs1 import test_vs1e as vs1e_tests


class ApplicationBridgeServiceTests(vs1e_tests.Vs1eFixture):
    def setUp(self) -> None:
        super().setUp()
        self.facade = RaiateaApplicationFacade(self.store, "scope:library")
        self.service = ApplicationBridgeService(self.facade)

    def _request(self, method: str, params: dict | None = None) -> dict:
        return handle_request(
            self.service,
            request_message("rpc:test", method, params or {}),
        )

    def test_live_service_delegates_current_application_models(self) -> None:
        status = self._request(METHOD_GATEWAY_STATUS)["result"]["payload"]
        self.assertEqual(status["mode"], "live")

        library = self._request(
            METHOD_LIBRARY_PAGE,
            {"page_size": 10, "cursor": None},
        )["result"]["payload"]
        self.assertEqual(library["catalog_freshness"], "fresh")
        self.assertGreaterEqual(len(library["items"]), 1)

        first = library["items"][0]
        detail = self._request(
            METHOD_SOURCE_DETAIL,
            {"item_ref": first["item_ref"]},
        )["result"]["payload"]
        self.assertEqual(detail["item_ref"], first["item_ref"])
        self.assertTrue(detail["representations"])

        search = self._request(
            METHOD_SEARCH_PAGE,
            {
                "plan": {
                    "criteria": [
                        {
                            "field": "extracted_text",
                            "operator": "contains",
                            "value": "Introduction",
                        }
                    ],
                    "sort_field": "source_ref_id",
                    "descending": False,
                },
                "page_size": 10,
                "cursor": None,
            },
        )["result"]["payload"]
        self.assertEqual(search["freshness"], "fresh")
        self.assertEqual(len(search["items"]), 1)

        representation_id = detail["representations"][0]["representation_id"]
        representation = self._request(
            METHOD_REPRESENTATION_PAGE,
            {
                "representation_id": representation_id,
                "page_size": 10,
                "cursor": None,
            },
        )["result"]["payload"]
        self.assertEqual(representation["representation_id"], representation_id)
        self.assertTrue(representation["units"])

    def test_bridge_does_not_accept_host_authority_or_unknown_methods(self) -> None:
        unknown = self._request("system.shell", {})
        self.assertEqual(unknown["error"]["code"], JSONRPC_METHOD_NOT_FOUND)

        forbidden = self._request(
            METHOD_LIBRARY_PAGE,
            {"page_size": 10, "cursor": None, "path": "/tmp/escape"},
        )
        # The wire contract itself rejects this key before dispatch in real I/O;
        # direct service dispatch still fails closed as an unknown parameter.
        self.assertEqual(forbidden["error"]["code"], JSONRPC_INVALID_PARAMS)

    def test_stale_search_remains_blocked_through_bridge(self) -> None:
        current = self.store.load()
        assert current is not None
        payload = json.loads(json.dumps(current.payload))
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "bridge-stale-test",
        }
        self.store.save(payload, expected_revision=current.revision)

        search = self._request(
            METHOD_SEARCH_PAGE,
            {
                "plan": {
                    "criteria": [],
                    "sort_field": "source_ref_id",
                    "descending": False,
                }
            },
        )["result"]["payload"]
        self.assertEqual(search["freshness"], "stale")
        self.assertEqual(search["items"], [])
        self.assertIsNotNone(search["blocked_reason"])


class ApplicationBridgeSubprocessTests(vs1e_tests.Vs1eFixture):
    def setUp(self) -> None:
        super().setUp()
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "prototype.p0_vs1.application_bridge_sidecar",
                "--catalog-store",
                str(self.store.path),
                "--scope-id",
                "scope:library",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        assert self.process.stderr is not None

    def tearDown(self) -> None:
        if getattr(self, "process", None) is not None:
            assert self.process.stdin is not None
            self.process.stdin.close()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        super().tearDown()

    def _rpc(self, request_id: str, method: str, params: dict) -> dict:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        frame = encode_frame(request_message(request_id, method, params))
        self.process.stdin.write(frame)
        self.process.stdin.flush()
        raw = self.process.stdout.readline()
        self.assertTrue(raw, "sidecar closed stdout before response")
        return decode_frame(raw)

    def test_real_subprocess_exposes_full_read_chain_without_host_paths(self) -> None:
        status = self._rpc("rpc:status", METHOD_GATEWAY_STATUS, {})
        self.assertEqual(status["result"]["payload"]["mode"], "live")

        library_response = self._rpc(
            "rpc:library",
            METHOD_LIBRARY_PAGE,
            {"page_size": 10, "cursor": None},
        )
        library = library_response["result"]["payload"]
        first = library["items"][0]

        detail = self._rpc(
            "rpc:detail",
            METHOD_SOURCE_DETAIL,
            {"item_ref": first["item_ref"]},
        )["result"]["payload"]

        search = self._rpc(
            "rpc:search",
            METHOD_SEARCH_PAGE,
            {
                "plan": {
                    "criteria": [
                        {
                            "field": "semantic_type",
                            "operator": "has",
                            "value": "heading",
                        }
                    ],
                    "sort_field": "source_ref_id",
                    "descending": False,
                },
                "page_size": 10,
                "cursor": None,
            },
        )["result"]["payload"]
        self.assertEqual(search["freshness"], "fresh")

        representation_id = detail["representations"][0]["representation_id"]
        representation = self._rpc(
            "rpc:representation",
            METHOD_REPRESENTATION_PAGE,
            {
                "representation_id": representation_id,
                "page_size": 5,
                "cursor": None,
            },
        )["result"]["payload"]
        self.assertTrue(representation["units"])

        public_wire = json.dumps(
            [status, library_response, detail, search, representation],
            sort_keys=True,
        )
        self.assertNotIn(str(self.base), public_wire)
        self.assertNotIn(str(self.root), public_wire)
        self.assertNotIn(str(self.store.path), public_wire)

    def test_real_subprocess_rejects_malformed_and_host_authority_requests(self) -> None:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(b"not-json\n")
        self.process.stdin.flush()
        malformed = decode_frame(self.process.stdout.readline())
        self.assertEqual(malformed["error"]["code"], -32700)

        # Bypass request_message deliberately to prove the sidecar wire validator
        # rejects renderer-supplied host authority before method dispatch.
        raw_request = (
            b'{"id":"rpc:host","jsonrpc":"2.0","method":"library.page",'
            b'"params":{"path":"/tmp/private"}}\n'
        )
        self.process.stdin.write(raw_request)
        self.process.stdin.flush()
        rejected = decode_frame(self.process.stdout.readline())
        self.assertEqual(rejected["error"]["code"], -32700)

        unknown = self._rpc("rpc:unknown", "system.shell", {})
        self.assertEqual(unknown["error"]["code"], JSONRPC_METHOD_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
