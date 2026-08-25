from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.backup_contract import (
    BACKUP_VERSION,
    BackupContractError,
    build_backup,
    canonical_json_bytes,
    canonicalize_authority,
    decode_backup,
    sha256_ref,
)
from prototype.p0_vs1.backup_service import (
    BackupServiceError,
    CatalogBackupService,
    build_backup_authority,
)
from prototype.p0_vs1.catalog_store import CatalogSnapshot, CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.extraction_service import LocalEpubExtractionService
from prototype.p0_vs1.reconciliation import (
    Vs1ObservationScopeRegistry,
    Vs1bReconciliationEngine,
)
from prototype.p0_vs1.search_contract import canonical_json_bytes as search_json_bytes
from prototype.p0_vs1.search_service import SearchViewService
from prototype.p0_vs1.source_service import LocalSourceDiscoveryService


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"
_GEN_SPEC = importlib.util.spec_from_file_location("vs1f_fixture_generator", GENERATOR_PATH)
GENERATOR = importlib.util.module_from_spec(_GEN_SPEC)
assert _GEN_SPEC.loader is not None
_GEN_SPEC.loader.exec_module(GENERATOR)


def query(
    *criteria: tuple[str, str, str],
    sort_field: str = "source_ref_id",
    descending: bool = False,
) -> dict:
    return {
        "criteria": [
            {"field": field, "operator": operator, "value": value}
            for field, operator, value in criteria
        ],
        "sort_field": sort_field,
        "descending": descending,
    }


def _json_line(value: dict) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _raw(seq: int, path: Path) -> str:
    return _json_line(
        {
            "schema_version": 0,
            "seq": seq,
            "layer": "normalized_raw",
            "category": "filesystem",
            "type": "RAW_CREATE",
            "source": 1,
            "backend": "inotify",
            "path": str(path),
        }
    )


def _rename(seq: int, old_path: Path, new_path: Path) -> str:
    return _json_line(
        {
            "schema_version": 0,
            "seq": seq,
            "layer": "semantic",
            "category": "filesystem",
            "type": "FILE_RENAMED",
            "backend": "inotify",
            "old_path": str(old_path),
            "new_path": str(new_path),
        }
    )


def _active_identity_snapshot(payload: dict) -> list[dict]:
    rows = [
        {
            "entry_id": row["entry_id"],
            "logical_candidate_id": row["logical_candidate_id"],
            "stored_instance_id": row["stored_instance_id"],
            "current_location": row["current_location"],
            "location_history": deepcopy(row["location_history"]),
            "fingerprint": row["fingerprint"],
        }
        for row in payload["vs1b"]["entries"]
        if row["superseded_by"] is None and row["availability"] == "known-present"
    ]
    rows.sort(key=lambda row: row["entry_id"])
    return rows


def _e05_stable_snapshot(payload: dict) -> list[dict]:
    rows: list[dict] = []
    for extraction in payload["vs1d"]["extractions"]:
        records = extraction["records"]
        refs = extraction["record_refs"]
        run = next(
            records[ref["ref_id"]]
            for ref in refs
            if ref["record_kind"] == "ProcessingRunRecord"
        )
        evidence = next(
            records[ref["ref_id"]]
            for ref in refs
            if ref["record_kind"] == "ProviderEvidenceRecord"
        )
        representation = next(
            records[ref["ref_id"]]
            for ref in refs
            if ref["record_kind"] == "NormalizedRepresentationRecord"
        )
        rows.append(
            {
                "source_ref_id": extraction["source_ref_id"],
                "source_fingerprint": extraction["source_fingerprint"],
                "run_id": run["run_id"],
                "execution": run["outcome"]["execution"],
                "provider_id": evidence["provider"]["provider_id"],
                "provider_version": evidence["provider"]["version"],
                "route_profile": evidence["route_profile"]["route_profile_id"],
                "representation_id": representation["representation_id"],
                "units": deepcopy(representation["units"]),
                "relations": deepcopy(representation["relations"]),
                "plugin_id": extraction["plugin"]["plugin_id"],
                "rights_decision_id": extraction["rights_decision"]["decision_id"],
            }
        )
    rows.sort(key=lambda row: row["source_ref_id"])
    return rows


class Vs1fFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()
        GENERATOR.generate_epub_spine(self.root / "spine.epub")
        GENERATOR.generate_epub_navigation(self.root / "navigation.epub")

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
        self.discovery = LocalSourceDiscoveryService(
            self.store,
            self.scopes,
            "scope:library",
        )
        discovered = self.discovery.discover(rights_evidence_state="known-permitted")
        self.extraction = LocalEpubExtractionService(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )
        for source_ref in discovered["source_refs"]:
            self.extraction.extract(source_ref, rights_evidence_state="known-permitted")

        self.search = SearchViewService(self.store, "scope:library")
        self.search.rebuild_index()
        self.intro_plan = query(("extracted_text", "contains", "Introduction"))
        self.heading_plan = query(("semantic_type", "has", "heading"))
        self.search.save_view(
            "view:introduction",
            self.intro_plan,
            ["source_ref_id", "provider_id", "unit_count"],
        )
        self.search.save_smart_collection("smart:headings", self.heading_plan)

        baseline = self.reconciliation.consume_jsonl(_raw(1, self.root / "baseline"))
        self.assertEqual(baseline["status"], "baseline-unproven-not-applied")
        self.reconciliation.reconcile_inventory()

        before_rename = self.store.load().payload
        spine_entry = next(
            row
            for row in before_rename["vs1b"]["entries"]
            if row["current_location"] == "spine.epub"
        )
        self.spine_ids = (
            spine_entry["entry_id"],
            spine_entry["logical_candidate_id"],
            spine_entry["stored_instance_id"],
        )
        old_path = self.root / "spine.epub"
        new_path = self.root / "renamed-spine.epub"
        old_path.rename(new_path)
        transitioned = self.reconciliation.consume_jsonl(_rename(2, old_path, new_path))
        self.assertEqual(transitioned["status"], "applied")

        stale = self.search.search(self.intro_plan)
        self.assertEqual(stale["freshness"], "stale")
        self.assertEqual(stale["source_ids"], [])
        self.reconciliation.reconcile_inventory()
        renamed = next(
            row
            for row in self.store.load().payload["vs1b"]["entries"]
            if row["entry_id"] == self.spine_ids[0]
        )
        self.assertEqual(
            (
                renamed["entry_id"],
                renamed["logical_candidate_id"],
                renamed["stored_instance_id"],
            ),
            self.spine_ids,
        )
        self.assertEqual(renamed["current_location"], "renamed-spine.epub")
        self.assertIn("spine.epub", renamed["location_history"])

        still_stale = self.search.search(self.intro_plan)
        self.assertEqual(still_stale["freshness"], "stale")
        self.search.rebuild_index()
        self.search.reevaluate_smart_collection("smart:headings")

        self.pre_query = self.search.search(self.intro_plan)
        self.pre_view = self.search.evaluate_view("view:introduction")
        self.pre_payload = deepcopy(self.store.load().payload)
        self.pre_smart = deepcopy(
            next(
                row
                for row in self.pre_payload["vs1e"]["smart_collections"]
                if row["collection_id"] == "smart:headings"
            )
        )
        self.pre_identities = _active_identity_snapshot(self.pre_payload)
        self.pre_source_refs = deepcopy(self.pre_payload["vs1c"]["source_references"])
        self.pre_e05 = _e05_stable_snapshot(self.pre_payload)

        self.backup = CatalogBackupService(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def new_target(self, name: str = "restored.json") -> CatalogStateStore:
        return CatalogStateStore(self.base / name)


class BackupAuthorityTests(Vs1fFixture):
    def test_repeated_export_is_byte_identical_and_excludes_derived_ephemeral_authority(self) -> None:
        first = self.backup.export_bytes()
        second = self.backup.export_bytes()
        self.assertEqual(first, second)
        decoded = decode_backup(first)
        authority = decoded["authority"]
        self.assertNotIn("index", authority)
        self.assertNotIn("smart_collections", authority)
        self.assertIn("views", authority)
        self.assertIn("smart_rules", authority)
        serialized = first.decode("utf-8")
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("plugin-input:", serialized)
        self.assertNotIn("plugin-output:", serialized)
        self.assertNotIn("lease:", serialized)
        self.assertNotIn('"handle_id"', serialized)
        self.assertNotIn('"source_bytes"', serialized)
        self.assertNotIn('"document_bytes"', serialized)
        self.assertIn("Introduction", serialized)

    def test_authority_hash_is_independent_of_unordered_collection_order(self) -> None:
        snapshot = self.store.load()
        authority = build_backup_authority(snapshot, "scope:library")
        reordered = deepcopy(authority)
        reordered["vs1b"]["entries"] = list(reversed(reordered["vs1b"]["entries"]))
        reordered["vs1c"]["source_references"] = list(
            reversed(reordered["vs1c"]["source_references"])
        )
        reordered["vs1d"]["extractions"] = list(
            reversed(reordered["vs1d"]["extractions"])
        )
        reordered["views"] = list(reversed(reordered["views"]))
        reordered["smart_rules"] = list(reversed(reordered["smart_rules"]))
        canonical_a = canonicalize_authority(authority, "scope:library")
        canonical_b = canonicalize_authority(reordered, "scope:library")
        self.assertEqual(canonical_a, canonical_b)
        self.assertEqual(sha256_ref(canonical_a), sha256_ref(canonical_b))

    def test_derived_index_and_member_cache_are_not_backup_authority(self) -> None:
        snapshot = self.store.load()
        baseline = build_backup_authority(snapshot, "scope:library")
        payload = deepcopy(snapshot.payload)
        payload["vs1e"]["index"] = {"corrupt-derived-cache": True}
        for collection in payload["vs1e"]["smart_collections"]:
            collection["current_members"] = ["source-ref:derived-cache-tamper"]
            collection["evaluated_upstream_basis_fingerprint"] = "sha256:" + "0" * 64
            collection["evaluated_catalog_revision"] = 999999
        tampered = CatalogSnapshot(revision=snapshot.revision, payload=payload)
        rebuilt_authority = build_backup_authority(tampered, "scope:library")
        self.assertEqual(baseline, rebuilt_authority)

    def test_stale_upstream_cannot_export_as_current(self) -> None:
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "test-stale",
        }
        self.store.save(payload, expected_revision=current.revision)
        with self.assertRaisesRegex(BackupServiceError, "not-fresh"):
            self.backup.export_bytes()


class BackupIntegrityTests(Vs1fFixture):
    def test_corruption_noncanonical_version_unknown_field_and_transient_refs_fail_closed(self) -> None:
        raw = self.backup.export_bytes()
        backup = decode_backup(raw)

        corrupt = deepcopy(backup)
        corrupt["authority"]["vs1b"]["freshness"]["reason"] = "tampered"
        with self.assertRaisesRegex(BackupContractError, "integrity-mismatch"):
            decode_backup(canonical_json_bytes(corrupt))

        pretty = json.dumps(backup, indent=2, ensure_ascii=False).encode("utf-8")
        with self.assertRaisesRegex(BackupContractError, "not-canonical"):
            decode_backup(pretty)

        unsupported = deepcopy(backup)
        unsupported["backup_version"] = BACKUP_VERSION + ".future"
        with self.assertRaisesRegex(BackupContractError, "version-unsupported"):
            decode_backup(canonical_json_bytes(unsupported))

        extra = deepcopy(backup)
        extra["root"] = str(self.root)
        with self.assertRaises(BackupContractError):
            decode_backup(canonical_json_bytes(extra))

        authority = deepcopy(backup["authority"])
        authority["views"][0]["plan"]["criteria"][0]["value"] = "plugin-input:dead"
        with self.assertRaisesRegex(BackupContractError, "transient-reference"):
            build_backup(
                scope_ref="scope:library",
                source_catalog_revision=backup["source_catalog_revision"],
                authority=authority,
            )


class RestoreTests(Vs1fFixture):
    def test_full_restore_reconciles_real_files_and_reproduces_user_visible_knowledge(self) -> None:
        raw = self.backup.export_bytes()
        target = self.new_target()
        restored = self.backup.restore_into_empty_store(raw, target)
        self.assertEqual(restored["status"], "completed")
        self.assertEqual(restored["catalog_revision"], 1)
        self.assertTrue(restored["reconciled_before_publish"])

        restored_payload = target.load().payload
        self.assertEqual(_active_identity_snapshot(restored_payload), self.pre_identities)
        self.assertEqual(restored_payload["vs1c"]["source_references"], self.pre_source_refs)
        self.assertEqual(_e05_stable_snapshot(restored_payload), self.pre_e05)

        restored_search = SearchViewService(target, "scope:library")
        post_query = restored_search.search(self.intro_plan)
        post_view = restored_search.evaluate_view("view:introduction")
        post_smart = next(
            row
            for row in target.load().payload["vs1e"]["smart_collections"]
            if row["collection_id"] == "smart:headings"
        )
        self.assertEqual(post_query["source_ids"], self.pre_query["source_ids"])
        self.assertEqual(post_query["hits"], self.pre_query["hits"])
        self.assertEqual(post_view["source_ids"], self.pre_view["source_ids"])
        self.assertEqual(post_view["rows"], self.pre_view["rows"])
        self.assertEqual(
            search_json_bytes(post_smart["rule"]),
            search_json_bytes(self.pre_smart["rule"]),
        )
        self.assertEqual(post_smart["current_members"], self.pre_smart["current_members"])
        self.assertEqual(post_smart["evaluated_catalog_revision"], 1)
        self.assertEqual(
            target.load().payload["vs1e"]["index"]["built_from_catalog_revision"],
            1,
        )

    def test_restore_scope_mismatch_and_nonempty_target_fail_without_overwrite(self) -> None:
        raw = self.backup.export_bytes()
        self.scopes.register_scope("scope:other", self.root)
        wrong_service = CatalogBackupService(
            self.store,
            self.scopes,
            self.broker,
            "scope:other",
        )
        with self.assertRaisesRegex(BackupServiceError, "scope-mismatch"):
            wrong_service.restore_into_empty_store(
                raw,
                self.new_target("wrong-scope.json"),
            )

        target = self.new_target("occupied.json")
        target.save({"already": "occupied"}, expected_revision=0)
        before = target.load()
        with self.assertRaisesRegex(BackupServiceError, "must-be-empty"):
            self.backup.restore_into_empty_store(raw, target)
        self.assertEqual(target.load(), before)

    def test_changed_missing_or_extra_physical_source_leaves_target_empty(self) -> None:
        raw = self.backup.export_bytes()

        renamed = self.root / "renamed-spine.epub"
        original_bytes = renamed.read_bytes()
        renamed.write_bytes(original_bytes + b"changed")
        changed_target = self.new_target("changed.json")
        with self.assertRaises(BackupServiceError):
            self.backup.restore_into_empty_store(raw, changed_target)
        self.assertIsNone(changed_target.load())
        renamed.write_bytes(original_bytes)

        navigation = self.root / "navigation.epub"
        navigation_bytes = navigation.read_bytes()
        navigation.unlink()
        missing_target = self.new_target("missing.json")
        with self.assertRaises(BackupServiceError):
            self.backup.restore_into_empty_store(raw, missing_target)
        self.assertIsNone(missing_target.load())
        navigation.write_bytes(navigation_bytes)

        GENERATOR.generate_epub_inert_active_content(self.root / "unexpected.epub")
        extra_target = self.new_target("extra.json")
        with self.assertRaisesRegex(BackupServiceError, "source-set-mismatch"):
            self.backup.restore_into_empty_store(raw, extra_target)
        self.assertIsNone(extra_target.load())


if __name__ == "__main__":
    unittest.main()
