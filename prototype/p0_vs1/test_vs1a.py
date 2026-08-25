from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.catalog_store import CatalogStateStore, CatalogStoreError, STORE_VERSION
from prototype.p0_vs1.core_access import AssetBroker, CoreAccessError, ScopeRegistry


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_VALIDATOR_PATH = (
    REPO_ROOT
    / "elaboration"
    / "p0"
    / "contracts"
    / "plugins"
    / "runtime"
    / "1.0.0"
    / "validate_runtime.py"
)
_RUNTIME_SPEC = importlib.util.spec_from_file_location("vs1a_runtime_validator", RUNTIME_VALIDATOR_PATH)
assert _RUNTIME_SPEC is not None and _RUNTIME_SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(_RUNTIME_SPEC)
_RUNTIME_SPEC.loader.exec_module(RUNTIME)


class MutableClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 25, 5, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def _try_symlink(testcase: unittest.TestCase, target: Path, link: Path, *, directory: bool) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        testcase.skipTest(f"real symlink/reparse creation unavailable on this runner: {exc}")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class CoreAssetBrokerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source_root = self.base / "library"
        self.output_root = self.base / "outputs"
        self.source_root.mkdir()
        self.output_root.mkdir()
        self.epub = self.source_root / "book.epub"
        self.payload = b"PK\x03\x04Raiatea VS1a EPUB fixture\n"
        self.epub.write_bytes(self.payload)
        self.clock = MutableClock()
        self.scopes = ScopeRegistry()
        self.scopes.register_scope("scope:library", self.source_root)
        self.broker = AssetBroker(self.scopes, self.output_root, clock=self.clock)

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def test_scope_public_record_does_not_disclose_root(self) -> None:
        record = self.scopes.public_scope("scope:library")
        self.assertEqual(record["scope_id"], "scope:library")
        self.assertEqual(record["capabilities"], ["observe", "read-for-processing"])
        self.assertTrue(set(record).isdisjoint({"root", "path", "host_path"}))

    def test_issue_and_read_opaque_asset_handle(self) -> None:
        handle = self.broker.issue_read_handle(
            "scope:library",
            "book.epub",
            media_type="application/epub+zip",
            ttl_seconds=60,
        )
        self.assertEqual(handle["access"], "read")
        self.assertEqual(handle["media_type"], "application/epub+zip")
        self.assertEqual(handle["byte_length"], len(self.payload))
        self.assertEqual(handle["fingerprint"], _sha256(self.payload))
        self.assertTrue(set(handle).isdisjoint({"path", "root", "relative_path", "host_path"}))
        self.assertEqual(self.broker.read_asset(handle), self.payload)

    def test_absolute_backslash_colon_and_traversal_paths_fail_closed(self) -> None:
        samples = (
            "/etc/passwd",
            "../outside.epub",
            "nested/../outside.epub",
            "nested\\outside.epub",
            "C:/outside.epub",
            "file.epub:stream",
            "./book.epub",
            "nested//book.epub",
        )
        for sample in samples:
            with self.subTest(sample=sample):
                with self.assertRaises(CoreAccessError):
                    self.broker.issue_read_handle(
                        "scope:library", sample, media_type="application/epub+zip"
                    )

    def test_unknown_scope_and_mutation_capability_fail_closed(self) -> None:
        with self.assertRaisesRegex(CoreAccessError, "unknown-scope-id"):
            self.broker.issue_read_handle(
                "scope:missing", "book.epub", media_type="application/epub+zip"
            )
        with self.assertRaisesRegex(CoreAccessError, "scope-mutation-capability-forbidden"):
            self.scopes.require_capability("scope:library", "write")

    def test_scope_registration_requires_absolute_nonreparse_directory(self) -> None:
        registry = ScopeRegistry()
        try:
            with self.assertRaisesRegex(CoreAccessError, "scope-root-must-be-absolute"):
                registry.register_scope("scope:relative", Path("relative"))
            file_root = self.base / "not-a-directory"
            file_root.write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(CoreAccessError, "scope-root-must-be-directory"):
                registry.register_scope("scope:file", file_root)
        finally:
            registry.close()

    def test_symlink_root_is_rejected(self) -> None:
        target = self.base / "real-root"
        target.mkdir()
        link = self.base / "linked-root"
        _try_symlink(self, target, link, directory=True)
        registry = ScopeRegistry()
        try:
            with self.assertRaisesRegex(CoreAccessError, "scope-root-symlink-or-reparse-forbidden"):
                registry.register_scope("scope:link", link)
        finally:
            registry.close()

    def test_intermediate_symlink_escape_is_rejected_before_bytes_return(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "secret.epub").write_bytes(b"outside-secret")
        link = self.source_root / "escape"
        _try_symlink(self, outside, link, directory=True)
        with self.assertRaises(CoreAccessError):
            self.broker.issue_read_handle(
                "scope:library", "escape/secret.epub", media_type="application/epub+zip"
            )

    def test_final_symlink_is_rejected_before_bytes_return(self) -> None:
        outside = self.base / "outside.epub"
        outside.write_bytes(b"outside-secret")
        link = self.source_root / "linked.epub"
        _try_symlink(self, outside, link, directory=False)
        with self.assertRaises(CoreAccessError):
            self.broker.issue_read_handle(
                "scope:library", "linked.epub", media_type="application/epub+zip"
            )

    def test_unknown_wrong_access_wrong_lease_and_extra_fields_fail(self) -> None:
        handle = self.broker.issue_read_handle(
            "scope:library", "book.epub", media_type="application/epub+zip"
        )
        unknown = dict(handle)
        unknown["handle_id"] = "asset:unknown"
        with self.assertRaisesRegex(CoreAccessError, "read-handle-unknown"):
            self.broker.read_asset(unknown)
        wrong_lease = dict(handle)
        wrong_lease["lease_id"] = "lease:wrong"
        with self.assertRaisesRegex(CoreAccessError, "read-handle-lease-mismatch"):
            self.broker.read_asset(wrong_lease)
        wrong_access = dict(handle)
        wrong_access["access"] = "write-once-output"
        with self.assertRaisesRegex(CoreAccessError, "read-handle-access-required"):
            self.broker.read_asset(wrong_access)
        extra = dict(handle)
        extra["rights_grant"] = True
        with self.assertRaisesRegex(CoreAccessError, "read-handle-unknown-field:rights_grant"):
            self.broker.read_asset(extra)

    def test_expired_read_handle_fails(self) -> None:
        handle = self.broker.issue_read_handle(
            "scope:library",
            "book.epub",
            media_type="application/epub+zip",
            ttl_seconds=5,
        )
        self.clock.advance(6)
        with self.assertRaisesRegex(CoreAccessError, "read-handle-expired"):
            self.broker.read_asset(handle)

    def test_changed_bytes_after_issue_fail_closed(self) -> None:
        handle = self.broker.issue_read_handle(
            "scope:library", "book.epub", media_type="application/epub+zip"
        )
        self.epub.write_bytes(b"PK\x03\x04changed-after-handle")
        with self.assertRaisesRegex(CoreAccessError, "asset-content-changed"):
            self.broker.read_asset(handle)

    def test_output_target_is_core_owned_write_once_and_path_free(self) -> None:
        target = self.broker.issue_output_target(
            media_type="application/json", max_byte_length=1024, ttl_seconds=60
        )
        self.assertEqual(target["access"], "write-once-output")
        self.assertTrue(set(target).isdisjoint({"path", "root", "relative_path", "filename"}))
        result = self.broker.write_output(target, b'{"ok":true}')
        self.assertEqual(result["byte_length"], 11)
        self.assertEqual(result["fingerprint"], _sha256(b'{"ok":true}'))
        self.assertEqual(
            self.broker.read_completed_output(str(result["handle_id"]), str(result["lease_id"])),
            b'{"ok":true}',
        )
        with self.assertRaisesRegex(CoreAccessError, "output-target-already-written"):
            self.broker.write_output(target, b"again")

    def test_output_target_rejects_unknown_authority_fields(self) -> None:
        target = self.broker.issue_output_target(
            media_type="application/json", max_byte_length=1024
        )
        extra = dict(target)
        extra["path"] = "/tmp/attacker-controlled"
        with self.assertRaisesRegex(CoreAccessError, "output-target-unknown-field:path"):
            self.broker.write_output(extra, b"{}")

    def test_completed_output_tampering_is_detected(self) -> None:
        target = self.broker.issue_output_target(
            media_type="application/json", max_byte_length=1024
        )
        result = self.broker.write_output(target, b'{"ok":true}')
        output_files = list(self.output_root.glob("*.bin"))
        self.assertEqual(len(output_files), 1)
        output_files[0].write_bytes(b"tampered")
        with self.assertRaisesRegex(CoreAccessError, "completed-output-content-changed"):
            self.broker.read_completed_output(
                str(result["handle_id"]), str(result["lease_id"])
            )

    def test_output_byte_budget_and_expiry_fail_closed(self) -> None:
        small = self.broker.issue_output_target(
            media_type="application/octet-stream", max_byte_length=3
        )
        with self.assertRaisesRegex(CoreAccessError, "output-exceeds-core-byte-budget"):
            self.broker.write_output(small, b"four")

        expiring = self.broker.issue_output_target(
            media_type="application/octet-stream", max_byte_length=10, ttl_seconds=2
        )
        self.clock.advance(3)
        with self.assertRaisesRegex(CoreAccessError, "output-target-expired"):
            self.broker.write_output(expiring, b"x")

    def test_asset_and_output_shapes_validate_inside_runtime_v1b_invocation(self) -> None:
        read_handle = self.broker.issue_read_handle(
            "scope:library",
            "book.epub",
            media_type="application/epub+zip",
            ttl_seconds=120,
        )
        output_target = self.broker.issue_output_target(
            media_type="application/vnd.raiatea.e05-proof-bundle+json",
            max_byte_length=1024,
            ttl_seconds=120,
        )
        manifest = {
            "plugin": {"plugin_id": "vs1a.contract-check", "version": "0.1.0"},
            "capabilities": [
                {
                    "capability_id": "extract.run",
                    "profiles": [{"profile_id": "epub-direct-stdlib"}],
                }
            ],
        }
        handshake = {
            "record_type": "handshake",
            "identity": {
                "plugin_id": "vs1a.contract-check",
                "plugin_version": "0.1.0",
                "manifest_fingerprint": RUNTIME.canonical_manifest_fingerprint(manifest),
                "runtime_contract_version": "1.0.0",
                "runtime_instance_id": "runtime:vs1a:test",
            },
            "advertised_profiles": [
                {"capability_id": "extract.run", "profile_id": "epub-direct-stdlib"}
            ],
            "observed_at": self.clock().isoformat().replace("+00:00", "Z"),
        }
        request = {
            "record_type": "invocation-request",
            "invocation_id": "invoke:vs1a:test",
            "idempotency_key": "idem:vs1a:test",
            "runtime_instance_id": "runtime:vs1a:test",
            "capability": {
                "capability_id": "extract.run",
                "profile_id": "epub-direct-stdlib",
            },
            "inputs": [{"kind": "asset-handle", "handle": read_handle}],
            "output_targets": [output_target],
            "runtime_context": {
                "workspace_scope_id": "scope:library",
                "rights_decision_ref": "rights:vs1a:local",
                "secret_leases": [],
            },
            "deadline_at": (self.clock() + timedelta(seconds=30))
            .isoformat()
            .replace("+00:00", "Z"),
            "parameters": {},
        }
        RUNTIME.validate_handshake(handshake, manifest)
        RUNTIME.validate_invocation(request, manifest, handshake)


class CatalogStateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.path = self.root / "catalog.json"
        self.store = CatalogStateStore(self.path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_save_load_and_revision_guard(self) -> None:
        first_payload = {"items": [], "freshness": "unknown"}
        first = self.store.save(first_payload, expected_revision=0)
        self.assertEqual(first.revision, 1)
        self.assertEqual(first.payload, first_payload)
        self.assertEqual(self.store.load(), first)

        second_payload = {"items": [{"id": "candidate:1"}], "freshness": "unknown"}
        second = self.store.save(second_payload, expected_revision=1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(self.store.load(), second)

        with self.assertRaisesRegex(CatalogStoreError, "catalog-stale-expected-revision"):
            self.store.save({"items": []}, expected_revision=1)

    def test_same_store_instance_serializes_competing_revision_writes(self) -> None:
        def write(value: str) -> tuple[str, object]:
            try:
                return ("ok", self.store.save({"writer": value}, expected_revision=0))
            except CatalogStoreError as exc:
                return ("error", str(exc))

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(write, ("a", "b")))
        statuses = sorted(status for status, _ in results)
        self.assertEqual(statuses, ["error", "ok"])
        self.assertIn(
            "catalog-stale-expected-revision",
            [value for status, value in results if status == "error"],
        )
        loaded = self.store.load()
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.revision, 1)

    def test_serialization_is_canonical_and_integrity_checked(self) -> None:
        snapshot = self.store.save({"z": 1, "a": {"b": 2}}, expected_revision=0)
        raw = self.path.read_bytes()
        self.assertNotIn(b" ", raw)
        envelope = json.loads(raw.decode("utf-8"))
        self.assertEqual(envelope["store_version"], STORE_VERSION)
        canonical_payload = json.dumps(
            snapshot.payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(
            envelope["payload_sha256"],
            "sha256:" + hashlib.sha256(canonical_payload).hexdigest(),
        )

    def test_corrupt_digest_fails_closed(self) -> None:
        self.store.save({"items": []}, expected_revision=0)
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        envelope["payload"]["items"] = [{"tampered": True}]
        self.path.write_text(
            json.dumps(envelope, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
            newline="",
        )
        with self.assertRaisesRegex(CatalogStoreError, "catalog-payload-integrity-mismatch"):
            self.store.load()

    def test_unsupported_version_fails_closed(self) -> None:
        self.store.save({"items": []}, expected_revision=0)
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        envelope["store_version"] = "raiatea.vs1.catalog-internal.99.0.0"
        self.path.write_text(
            json.dumps(envelope, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
            newline="",
        )
        with self.assertRaisesRegex(CatalogStoreError, "catalog-store-version-unsupported"):
            self.store.load()

    def test_noncanonical_envelope_fails_closed(self) -> None:
        self.store.save({"items": []}, expected_revision=0)
        envelope = json.loads(self.path.read_text(encoding="utf-8"))
        self.path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(CatalogStoreError, "catalog-envelope-not-canonical"):
            self.store.load()

    def test_catalog_target_symlink_or_reparse_is_rejected(self) -> None:
        target = self.root / "other.json"
        target.write_text("{}", encoding="utf-8")
        link = self.root / "linked-catalog.json"
        _try_symlink(self, target, link, directory=False)
        with self.assertRaisesRegex(
            CatalogStoreError, "catalog-target-symlink-or-reparse-forbidden"
        ):
            CatalogStateStore(link)

    def test_catalog_payload_must_be_json_object_and_json_safe(self) -> None:
        with self.assertRaisesRegex(CatalogStoreError, "catalog-payload-must-be-object"):
            self.store.save([], expected_revision=0)  # type: ignore[arg-type]
        with self.assertRaisesRegex(CatalogStoreError, "catalog-payload-not-json-safe"):
            self.store.save({"bad": {1, 2}}, expected_revision=0)


if __name__ == "__main__":
    unittest.main()
