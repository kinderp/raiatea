from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogSnapshot, CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.local_process_client import LocalPluginProcessClient
from prototype.p0_vs1.plugin_io import (
    BROKER_ENV,
    PluginIOError,
    Vs1PluginIO,
    plugin_read_handle,
    plugin_write_output,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry, Vs1bReconciliationEngine
from prototype.p0_vs1.rights import RightsDecisionError, decide_local_reference_discovery
from prototype.p0_vs1.source_contract import canonical_json_bytes
from prototype.p0_vs1.source_service import (
    DEFAULT_MANIFEST_PATH,
    LocalSourceDiscoveryService,
    SourceDiscoveryError,
    build_discovery_snapshot,
)


FORBIDDEN_PUBLIC_KEYS = {
    "path",
    "relative_path",
    "host_path",
    "filesystem_path",
    "location",
    "current_location",
    "location_history",
    "content",
    "bytes",
    "data",
    "rights_grant",
}


def _assert_no_forbidden_keys(testcase: unittest.TestCase, value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            testcase.assertNotIn(str(key).strip().lower().replace("-", "_"), FORBIDDEN_PUBLIC_KEYS)
            _assert_no_forbidden_keys(testcase, child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_forbidden_keys(testcase, child)


class Vs1cFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()
        self.payload = b"PK\x03\x04same-epub-content"
        (self.root / "one.epub").write_bytes(self.payload)
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "copy.epub").write_bytes(self.payload)
        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:library", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        self.reconciliation = Vs1bReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )
        self.reconciliation.reconcile_inventory()

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()


class DiscoverySnapshotTests(Vs1cFixture):
    def test_snapshot_is_path_free_and_keeps_equal_copies_distinct(self) -> None:
        snapshot = build_discovery_snapshot(self.store.load(), "scope:library")
        self.assertEqual(snapshot["freshness"], "fresh")
        self.assertEqual(len(snapshot["items"]), 2)
        self.assertEqual(len({row["catalog_entry_ref"] for row in snapshot["items"]}), 2)
        self.assertEqual(len({row["stored_instance_ref"] for row in snapshot["items"]}), 2)
        self.assertEqual(len({row["fingerprint"] for row in snapshot["items"]}), 1)
        serialized = json.dumps(snapshot, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("one.epub", serialized)
        self.assertNotIn("copy.epub", serialized)
        _assert_no_forbidden_keys(self, snapshot)

    def test_snapshot_is_independent_of_internal_entry_list_order(self) -> None:
        current = self.store.load()
        self.assertIsNotNone(current)
        first = build_discovery_snapshot(current, "scope:library")
        payload = deepcopy(current.payload)
        payload["vs1b"]["entries"] = list(reversed(payload["vs1b"]["entries"]))
        reordered = CatalogSnapshot(revision=current.revision, payload=payload)
        second = build_discovery_snapshot(reordered, "scope:library")
        self.assertEqual(first, second)

    def test_nonfresh_catalog_cannot_be_discovered(self) -> None:
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "test-gap",
        }
        altered = CatalogSnapshot(revision=current.revision, payload=payload)
        with self.assertRaisesRegex(SourceDiscoveryError, "catalog-not-fresh"):
            build_discovery_snapshot(altered, "scope:library")


class RightsDecisionTests(Vs1cFixture):
    def test_unknown_remains_unknown_in_reference_only_decision(self) -> None:
        decision = decide_local_reference_discovery(
            self.scopes,
            "scope:library",
            plugin_id="org.raiatea.vs1.local-source",
            rights_evidence_state="unknown",
        )
        self.assertEqual(decision["rights_evidence_state"], "unknown")
        self.assertEqual(
            decision["policy_outcome"],
            "allow-local-reference-only-with-unknown-rights-evidence",
        )
        self.assertFalse(decision["source_bytes_shared"])
        self.assertFalse(decision["redistribution"])
        self.assertEqual(decision["legal_conclusion"], "not-established-by-this-decision")

    def test_known_restricted_and_requires_review_fail_closed(self) -> None:
        for state in ("known-restricted", "requires-review"):
            with self.subTest(state=state):
                with self.assertRaises(RightsDecisionError):
                    decide_local_reference_discovery(
                        self.scopes,
                        "scope:library",
                        plugin_id="org.raiatea.vs1.local-source",
                        rights_evidence_state=state,
                    )


class PrivatePluginIOTests(unittest.TestCase):
    def test_broker_round_trip_is_handle_only_write_once_and_cleanup_bounded(self) -> None:
        io = Vs1PluginIO()
        root = io.root
        try:
            read_handle = io.add_input(b"snapshot", media_type="application/test-input")
            output_target = io.issue_output(
                media_type="application/test-output",
                max_byte_length=100,
            )
            self.assertTrue(set(read_handle).isdisjoint({"path", "root", "filename"}))
            self.assertTrue(set(output_target).isdisjoint({"path", "root", "filename"}))
            env = io.freeze()
            self.assertEqual(set(env), {BROKER_ENV})
            with patch.dict(os.environ, env, clear=False):
                self.assertEqual(plugin_read_handle(read_handle), b"snapshot")
                completed = plugin_write_output(output_target, b"bundle")
                with self.assertRaisesRegex(PluginIOError, "output-create-failed"):
                    plugin_write_output(output_target, b"again")
            io.verify_broker_unchanged()
            self.assertEqual(io.read_completed_output(output_target, completed), b"bundle")
        finally:
            io.close()
        self.assertFalse(root.exists())

    def test_input_and_output_tampering_are_detected(self) -> None:
        with Vs1PluginIO() as io:
            read_handle = io.add_input(b"snapshot", media_type="application/test-input")
            output_target = io.issue_output(
                media_type="application/test-output",
                max_byte_length=100,
            )
            env = io.freeze()
            broker = json.loads(io.broker_path.read_text(encoding="utf-8"))
            input_filename = broker["read_handles"][read_handle["handle_id"]]["filename"]
            (io.inputs / input_filename).write_bytes(b"tampered")
            with patch.dict(os.environ, env, clear=False):
                with self.assertRaisesRegex(PluginIOError, "fingerprint-mismatch"):
                    plugin_read_handle(read_handle)

        with Vs1PluginIO() as io:
            output_target = io.issue_output(
                media_type="application/test-output",
                max_byte_length=100,
            )
            env = io.freeze()
            with patch.dict(os.environ, env, clear=False):
                completed = plugin_write_output(output_target, b"bundle")
            broker = json.loads(io.broker_path.read_text(encoding="utf-8"))
            filename = broker["output_handles"][output_target["handle_id"]]["filename"]
            (io.outputs / filename).write_bytes(b"tampered")
            with self.assertRaisesRegex(PluginIOError, "fingerprint-mismatch"):
                io.read_completed_output(output_target, completed)

    def test_wrong_public_lease_is_rejected(self) -> None:
        with Vs1PluginIO() as io:
            read_handle = io.add_input(b"snapshot", media_type="application/test-input")
            env = io.freeze()
            wrong = dict(read_handle)
            wrong["lease_id"] = "lease:wrong"
            with patch.dict(os.environ, env, clear=False):
                with self.assertRaisesRegex(PluginIOError, "lease_id-mismatch"):
                    plugin_read_handle(wrong)


class LocalSourceProductTests(Vs1cFixture):
    def test_real_out_of_process_source_plugin_persists_path_free_refs(self) -> None:
        service = LocalSourceDiscoveryService(self.store, self.scopes, "scope:library")
        result = service.discover(rights_evidence_state="unknown")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_reference_count"], 2)
        persisted = self.store.load().payload["vs1c"]
        self.assertEqual(persisted["rights_decision"]["rights_evidence_state"], "unknown")
        self.assertEqual(len(persisted["source_references"]), 2)
        self.assertEqual(
            len({row["source_ref_id"] for row in persisted["source_references"]}),
            2,
        )
        self.assertEqual(
            len({row["fingerprint"] for row in persisted["source_references"]}),
            1,
        )
        serialized = json.dumps(persisted, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("one.epub", serialized)
        self.assertNotIn("copy.epub", serialized)
        _assert_no_forbidden_keys(self, persisted["source_references"])

    def test_source_reference_ids_are_stable_across_repeat_discovery(self) -> None:
        service = LocalSourceDiscoveryService(self.store, self.scopes, "scope:library")
        first = service.discover(rights_evidence_state="known-permitted")
        second = service.discover(rights_evidence_state="known-permitted")
        self.assertEqual(first["source_refs"], second["source_refs"])

    def test_restricted_rights_fail_before_catalog_mutation(self) -> None:
        service = LocalSourceDiscoveryService(self.store, self.scopes, "scope:library")
        before = self.store.load().revision
        with self.assertRaisesRegex(SourceDiscoveryError, "known-restricted"):
            service.discover(rights_evidence_state="known-restricted")
        self.assertEqual(self.store.load().revision, before)
        self.assertNotIn("vs1c", self.store.load().payload)

    def test_plugin_process_failure_does_not_mutate_catalog(self) -> None:
        manifest = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["entrypoint"]["command"] = [
            "python",
            "-m",
            "prototype.p0_vs1.plugins.local_source.missing_process",
        ]
        manifest_path = self.base / "bad-manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        service = LocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:library",
            manifest_path=manifest_path,
        )
        before = self.store.load().revision
        with self.assertRaisesRegex(SourceDiscoveryError, "source-plugin-execution-failed"):
            service.discover(rights_evidence_state="known-permitted")
        self.assertEqual(self.store.load().revision, before)
        self.assertNotIn("vs1c", self.store.load().payload)

    def test_tampered_plugin_bundle_is_rejected_without_persistence(self) -> None:
        service = LocalSourceDiscoveryService(self.store, self.scopes, "scope:library")
        real_read = Vs1PluginIO.read_completed_output

        def tamper(io: Vs1PluginIO, target: dict, completed: dict) -> bytes:
            raw = real_read(io, target, completed)
            bundle = json.loads(raw.decode("utf-8"))
            if bundle["record_refs"]:
                removed = bundle["record_refs"].pop()
                bundle["records"].pop(removed["ref_id"])
            return canonical_json_bytes(bundle)

        before = self.store.load().revision
        with patch.object(Vs1PluginIO, "read_completed_output", new=tamper):
            with self.assertRaises(SourceDiscoveryError):
                service.discover(rights_evidence_state="known-permitted")
        self.assertEqual(self.store.load().revision, before)
        self.assertNotIn("vs1c", self.store.load().payload)

    def test_catalog_change_during_plugin_run_rejects_stale_source_refs(self) -> None:
        service = LocalSourceDiscoveryService(self.store, self.scopes, "scope:library")
        real_invoke = LocalPluginProcessClient.invoke
        other_store = CatalogStateStore(self.store.path)

        def invoke_then_change(client: LocalPluginProcessClient, request: dict) -> dict:
            result = real_invoke(client, request)
            current = other_store.load()
            payload = deepcopy(current.payload)
            payload["concurrent_marker"] = {"changed": True}
            other_store.save(payload, expected_revision=current.revision)
            return result

        with patch.object(LocalPluginProcessClient, "invoke", new=invoke_then_change):
            with self.assertRaisesRegex(SourceDiscoveryError, "catalog-changed-during-plugin-run"):
                service.discover(rights_evidence_state="known-permitted")
        persisted = self.store.load().payload
        self.assertIn("concurrent_marker", persisted)
        self.assertNotIn("vs1c", persisted)

    def test_manifest_declares_no_network_source_filesystem_or_secrets(self) -> None:
        manifest = json.loads(DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["permissions"]["network"], [])
        self.assertEqual(manifest["permissions"]["filesystem"], [])
        self.assertEqual(manifest["permissions"]["secrets"], [])
        self.assertTrue(manifest["permissions"]["temporary_workspace"])
        self.assertEqual(manifest["families"], ["source"])
        self.assertEqual(manifest["capabilities"][0]["capability_id"], "source.discover")
        self.assertEqual(
            manifest["capabilities"][0]["profiles"][0]["profile_id"],
            "local-catalog-read-only",
        )


if __name__ == "__main__":
    unittest.main()
