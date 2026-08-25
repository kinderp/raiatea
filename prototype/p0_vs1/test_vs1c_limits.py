from __future__ import annotations

import json
import unittest

from prototype.p0_vs1.local_process_client import MAX_FRAME_BYTES
from prototype.p0_vs1.source_contract import (
    DISCOVERY_SNAPSHOT_VERSION,
    EPUB_MEDIA_TYPE,
    MAX_DISCOVERY_ITEMS,
    SourceContractError,
    build_source_reference_bundle,
    validate_discovery_snapshot,
)


class Vs1cDiscoveryLimitTests(unittest.TestCase):
    def _snapshot(self, count: int) -> dict:
        fingerprint = "sha256:" + "a" * 64
        items = [
            {
                "catalog_entry_ref": f"entry:{index:04d}",
                "stored_instance_ref": f"stored-instance:{index:04d}",
                "logical_candidate_ref": f"logical-candidate:{index:04d}",
                "media_type": EPUB_MEDIA_TYPE,
                "byte_length": 1024 + index,
                "fingerprint": fingerprint,
            }
            for index in range(count)
        ]
        return {
            "snapshot_version": DISCOVERY_SNAPSHOT_VERSION,
            "scope_ref": "scope:test",
            "catalog_revision": 1,
            "vs1b_state_fingerprint": "sha256:" + "b" * 64,
            "freshness": "fresh",
            "items": items,
        }

    def test_maximum_discovery_result_stays_inside_transport_frame(self) -> None:
        snapshot = self._snapshot(MAX_DISCOVERY_ITEMS)
        validate_discovery_snapshot(snapshot)
        bundle = build_source_reference_bundle(snapshot)
        completed_handle = {
            "handle_id": "plugin-output:test",
            "lease_id": "lease:test",
            "access": "write-once-output",
            "media_type": "application/vnd.raiatea.vs1c-source-reference-bundle+json",
            "byte_length": 999999,
            "fingerprint": "sha256:" + "c" * 64,
            "expires_at": "2026-08-25T20:00:00Z",
        }
        outputs = [{"kind": "asset-handle", "handle": completed_handle}]
        outputs.extend(
            {"kind": "record-ref", "record_ref": ref}
            for ref in bundle["record_refs"]
        )
        runtime_result = {
            "record_type": "invocation-result",
            "invocation_id": "invoke:vs1c:max-frame",
            "runtime_instance_id": "runtime:vs1c:max-frame",
            "status": "completed",
            "outputs": outputs,
            "diagnostic_refs": ["diag:max-frame"],
            "provenance": {
                "plugin_id": "org.raiatea.vs1.local-source",
                "plugin_version": "0.1.0",
                "runtime_instance_id": "runtime:vs1c:max-frame",
                "invocation_id": "invoke:vs1c:max-frame",
                "capability": {
                    "capability_id": "source.discover",
                    "profile_id": "local-catalog-read-only",
                },
                "started_at": "2026-08-25T19:00:00Z",
                "ended_at": "2026-08-25T19:00:01Z",
                "input_refs": ["plugin-input:max-frame"],
                "output_refs": [completed_handle["handle_id"]]
                + [ref["ref_id"] for ref in bundle["record_refs"]],
                "rights_decision_ref": "rights-decision:" + "d" * 64,
            },
        }
        jsonrpc_response = {
            "jsonrpc": "2.0",
            "id": "vs1c-rpc:max-frame",
            "result": runtime_result,
        }
        encoded = (
            json.dumps(
                jsonrpc_response,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            + b"\n"
        )
        self.assertLessEqual(len(encoded), MAX_FRAME_BYTES)
        # Keep explicit headroom for small future non-reference metadata without
        # silently moving the first-slice boundary to the transport ceiling.
        self.assertLess(len(encoded), int(MAX_FRAME_BYTES * 0.85))

    def test_discovery_above_single_frame_bound_fails_before_plugin(self) -> None:
        snapshot = self._snapshot(MAX_DISCOVERY_ITEMS + 1)
        with self.assertRaisesRegex(SourceContractError, "item-limit-exceeded"):
            validate_discovery_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
