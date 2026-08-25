from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker, CoreAccessError
from prototype.p0_vs1.reconciliation import (
    EPUB_MEDIA_TYPE,
    ReconciliationError,
    Vs1ObservationScopeRegistry,
    Vs1bReconciliationEngine,
    scan_epub_inventory,
)


def _try_symlink(testcase: unittest.TestCase, target: Path, link: Path, *, directory: bool) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        testcase.skipTest(f"real symlink/reparse creation unavailable on this runner: {exc}")


class Vs1bReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()
        self.store = CatalogStateStore(self.base / "catalog.json")
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:library", self.root)
        self.broker = AssetBroker(self.scopes, self.outputs)
        self.engine = Vs1bReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()

    def write_epub(self, relative: str, payload: bytes) -> Path:
        path = self.root / Path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def line(self, value: dict) -> str:
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)

    def raw(self, seq: int, event_type: str = "RAW_CREATE", path: Path | None = None) -> str:
        value = {
            "schema_version": 0,
            "seq": seq,
            "layer": "normalized_raw",
            "category": "filesystem",
            "type": event_type,
            "source": 1,
            "backend": "inotify",
        }
        if path is not None:
            value["path"] = str(path)
        return self.line(value)

    def semantic(self, seq: int | None, event_type: str, **paths: str) -> str:
        value = {
            "schema_version": 0,
            "layer": "semantic",
            "category": "filesystem",
            "type": event_type,
            "backend": "inotify",
            **paths,
        }
        if seq is not None:
            value["seq"] = seq
        return self.line(value)

    def diagnostic(self, seq: int, event_type: str, *, category: str, path: Path | None = None) -> str:
        value = {
            "schema_version": 0,
            "seq": seq,
            "layer": "diagnostic",
            "category": category,
            "type": event_type,
            "backend": "inotify",
        }
        if path is not None:
            value["path"] = str(path)
        return self.line(value)

    def establish_stream_baseline(self, seq: int = 1) -> None:
        result = self.engine.consume_jsonl(self.raw(seq, path=self.root / "baseline"))
        self.assertEqual(result["status"], "baseline-unproven-not-applied")
        self.assertEqual(result["freshness"]["status"], "reconcile-required")
        reconciled = self.engine.reconcile_inventory()
        self.assertEqual(reconciled["freshness"]["status"], "fresh")
        self.assertEqual(reconciled["last_reconciled_seq"], seq)

    def test_initial_inventory_is_deterministic_and_fresh(self) -> None:
        self.write_epub("z.epub", b"same-z")
        self.write_epub("nested/A.EPUB", b"nested-a")
        (self.root / "ignore.txt").write_text("ignore", encoding="utf-8")
        inventory = scan_epub_inventory(self.scopes, self.broker, "scope:library")
        self.assertEqual([item["location"] for item in inventory], ["nested/A.EPUB", "z.epub"])
        self.assertTrue(all(item["media_type"] == EPUB_MEDIA_TYPE for item in inventory))
        result = self.engine.reconcile_inventory()
        self.assertEqual(result["inventory_count"], 2)
        state = self.engine.current_state()
        self.assertEqual(state["freshness"], {"status": "fresh", "reason": "bounded-inventory-complete"})
        self.assertEqual([entry["current_location"] for entry in state["entries"]], ["nested/A.EPUB", "z.epub"])

    def test_symlink_or_reparse_file_and_directory_are_not_followed(self) -> None:
        self.write_epub("real.epub", b"real")
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "secret.epub").write_bytes(b"secret")
        dir_link = self.root / "linked-dir"
        _try_symlink(self, outside, dir_link, directory=True)
        file_link = self.root / "linked.epub"
        _try_symlink(self, outside / "secret.epub", file_link, directory=False)
        inventory = scan_epub_inventory(self.scopes, self.broker, "scope:library")
        self.assertEqual([item["location"] for item in inventory], ["real.epub"])

    def test_byte_identical_copies_remain_distinct_candidates(self) -> None:
        payload = b"PK\x03\x04same-epub-bytes"
        self.write_epub("a.epub", payload)
        self.write_epub("copies/b.epub", payload)
        self.engine.reconcile_inventory()
        entries = [entry for entry in self.engine.current_state()["entries"] if entry["availability"] == "known-present"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["fingerprint"], entries[1]["fingerprint"])
        self.assertNotEqual(entries[0]["stored_instance_id"], entries[1]["stored_instance_id"])
        self.assertNotEqual(entries[0]["logical_candidate_id"], entries[1]["logical_candidate_id"])

    def test_first_sequence_is_unproven_then_checkpoint_persists(self) -> None:
        self.write_epub("book.epub", b"book")
        self.engine.reconcile_inventory()
        result = self.engine.consume_jsonl(self.raw(7, path=self.root / "raw.tmp"))
        self.assertEqual(result["status"], "baseline-unproven-not-applied")
        self.assertEqual(self.engine.current_state()["stream"]["last_seq"], 7)
        reloaded = Vs1bReconciliationEngine(
            self.store,
            self.scopes,
            self.broker,
            "scope:library",
        )
        self.assertEqual(reloaded.current_state()["stream"]["last_seq"], 7)
        self.assertEqual(reloaded.current_state()["freshness"]["status"], "reconcile-required")

    def test_exact_replay_is_idempotent_without_revision_change(self) -> None:
        self.establish_stream_baseline()
        line = self.raw(2, path=self.root / "raw.tmp")
        first = self.engine.consume_jsonl(line)
        self.assertEqual(first["status"], "applied")
        before = self.store.load()
        assert before is not None
        second = self.engine.consume_jsonl(line)
        after = self.store.load()
        self.assertEqual(second["status"], "duplicate")
        self.assertEqual(second["revision"], before.revision)
        self.assertEqual(after, before)

    def test_sequence_gap_requires_reconcile_and_does_not_apply_transition(self) -> None:
        original = self.write_epub("old.epub", b"stable")
        self.engine.reconcile_inventory()
        self.establish_stream_baseline(1)
        before = self.engine.current_state()["entries"][0]
        original.rename(self.root / "new.epub")
        result = self.engine.consume_jsonl(
            self.semantic(
                3,
                "FILE_RENAMED",
                old_path=str(self.root / "old.epub"),
                new_path=str(self.root / "new.epub"),
            )
        )
        self.assertIn(result["status"], {"gap-not-applied", "continuity-untrusted-not-applied"})
        state = self.engine.current_state()
        self.assertEqual(state["freshness"]["status"], "reconcile-required")
        active = [entry for entry in state["entries"] if entry["superseded_by"] is None]
        self.assertEqual(active[0]["current_location"], before["current_location"])
        self.engine.reconcile_inventory()
        # With no trusted transition evidence applied, inventory conservatively keeps
        # the missing old instance and creates a new candidate at the new path.
        final = self.engine.current_state()
        present = [entry for entry in final["entries"] if entry["availability"] == "known-present"]
        missing = [entry for entry in final["entries"] if entry["availability"] == "confirmed-missing-at-location"]
        self.assertEqual([entry["current_location"] for entry in present], ["new.epub"])
        self.assertIn("old.epub", [entry["current_location"] for entry in missing])
        self.assertNotEqual(present[0]["logical_candidate_id"], before["logical_candidate_id"])

    def test_contiguous_rename_preserves_ids_and_location_history_after_reconcile(self) -> None:
        old = self.write_epub("old.epub", b"stable")
        self.engine.reconcile_inventory()
        original = next(entry for entry in self.engine.current_state()["entries"] if entry["current_location"] == "old.epub")
        self.establish_stream_baseline(1)
        old.rename(self.root / "new.epub")
        result = self.engine.consume_jsonl(
            self.semantic(
                2,
                "FILE_RENAMED",
                old_path=str(self.root / "old.epub"),
                new_path=str(self.root / "new.epub"),
            )
        )
        self.assertEqual(result["status"], "applied")
        transitioned = next(entry for entry in self.engine.current_state()["entries"] if entry["entry_id"] == original["entry_id"])
        self.assertEqual(transitioned["current_location"], "new.epub")
        self.assertEqual(transitioned["location_history"], ["old.epub"])
        self.assertEqual(transitioned["logical_candidate_id"], original["logical_candidate_id"])
        self.assertEqual(transitioned["stored_instance_id"], original["stored_instance_id"])
        self.assertEqual(transitioned["availability"], "unavailable-or-unknown")
        self.engine.reconcile_inventory()
        verified = next(entry for entry in self.engine.current_state()["entries"] if entry["entry_id"] == original["entry_id"])
        self.assertEqual(verified["availability"], "known-present")
        self.assertEqual(verified["reconciliation_status"], "verified-by-inventory")
        self.assertEqual(self.engine.current_state()["freshness"]["status"], "fresh")

    def test_same_location_changed_bytes_creates_new_candidate_and_supersedes_old(self) -> None:
        path = self.write_epub("book.epub", b"v1")
        self.engine.reconcile_inventory()
        original = next(entry for entry in self.engine.current_state()["entries"] if entry["current_location"] == "book.epub")
        path.write_bytes(b"v2-changed")
        self.engine.reconcile_inventory()
        state = self.engine.current_state()
        old = next(entry for entry in state["entries"] if entry["entry_id"] == original["entry_id"])
        new = next(entry for entry in state["entries"] if entry["entry_id"] == old["superseded_by"])
        self.assertEqual(old["availability"], "confirmed-missing-at-location")
        self.assertEqual(old["reconciliation_status"], "content-replaced-at-location-unresolved")
        self.assertEqual(new["current_location"], "book.epub")
        self.assertEqual(new["availability"], "known-present")
        self.assertNotEqual(old["logical_candidate_id"], new["logical_candidate_id"])
        self.assertNotEqual(old["stored_instance_id"], new["stored_instance_id"])

    def test_delete_is_location_level_and_history_survives_inventory(self) -> None:
        path = self.write_epub("book.epub", b"delete-me")
        self.engine.reconcile_inventory()
        original = self.engine.current_state()["entries"][0]
        self.establish_stream_baseline(1)
        path.unlink()
        result = self.engine.consume_jsonl(
            self.semantic(2, "FILE_DELETED", path=str(self.root / "book.epub"))
        )
        self.assertEqual(result["status"], "applied")
        deleted = next(entry for entry in self.engine.current_state()["entries"] if entry["entry_id"] == original["entry_id"])
        self.assertEqual(deleted["availability"], "confirmed-missing-at-location")
        self.assertEqual(deleted["logical_candidate_id"], original["logical_candidate_id"])
        self.engine.reconcile_inventory()
        retained = next(entry for entry in self.engine.current_state()["entries"] if entry["entry_id"] == original["entry_id"])
        self.assertEqual(retained["availability"], "confirmed-missing-at-location")
        self.assertEqual(retained["logical_candidate_id"], original["logical_candidate_id"])

    def test_stale_and_recovery_end_cannot_restore_freshness_without_inventory(self) -> None:
        self.write_epub("book.epub", b"book")
        self.engine.reconcile_inventory()
        self.establish_stream_baseline(1)
        stale = self.engine.consume_jsonl(
            self.diagnostic(2, "WATCH_STALE", category="watch", path=self.root)
        )
        self.assertEqual(stale["freshness"]["status"], "reconcile-required")
        state = self.engine.current_state()
        self.assertEqual(state["entries"][0]["availability"], "unavailable-or-unknown")
        recovery = self.engine.consume_jsonl(
            self.diagnostic(3, "WATCH_RESYNC_END", category="recovery", path=self.root)
        )
        self.assertEqual(recovery["freshness"]["status"], "reconcile-required")
        self.assertNotEqual(self.engine.current_state()["freshness"]["status"], "fresh")
        self.engine.reconcile_inventory()
        self.assertEqual(self.engine.current_state()["freshness"]["status"], "fresh")
        self.assertEqual(self.engine.current_state()["entries"][0]["availability"], "known-present")

    def test_no_sequence_never_applies_semantic_transition(self) -> None:
        old = self.write_epub("old.epub", b"book")
        self.engine.reconcile_inventory()
        before = self.engine.current_state()["entries"][0]
        old.rename(self.root / "new.epub")
        result = self.engine.consume_jsonl(
            self.semantic(
                None,
                "FILE_RENAMED",
                old_path=str(self.root / "old.epub"),
                new_path=str(self.root / "new.epub"),
            )
        )
        self.assertEqual(result["status"], "continuity-unproven-not-applied")
        state = self.engine.current_state()
        self.assertEqual(state["entries"][0]["current_location"], before["current_location"])
        self.assertEqual(state["freshness"]["status"], "reconcile-required")

    def test_old_unseen_sequence_is_not_destructively_reapplied(self) -> None:
        self.write_epub("book.epub", b"book")
        self.engine.reconcile_inventory()
        self.establish_stream_baseline(5)
        self.engine.consume_jsonl(self.raw(6, path=self.root / "raw6"))
        before = self.engine.current_state()
        result = self.engine.consume_jsonl(
            self.semantic(4, "FILE_DELETED", path=str(self.root / "book.epub"))
        )
        self.assertEqual(result["status"], "old-or-out-of-order-not-applied")
        after = self.engine.current_state()
        entry_before = before["entries"][0]
        entry_after = after["entries"][0]
        self.assertEqual(entry_after["availability"], entry_before["availability"])
        self.assertEqual(after["freshness"]["status"], "reconcile-required")
        self.assertEqual(after["stream"]["last_seq"], 6)

    def test_malformed_or_out_of_scope_record_does_not_advance_checkpoint(self) -> None:
        self.write_epub("book.epub", b"book")
        self.engine.reconcile_inventory()
        self.establish_stream_baseline(1)
        before = self.engine.current_state()
        with self.assertRaises(Exception):
            self.engine.consume_jsonl("{")
        self.assertEqual(self.engine.current_state(), before)
        outside = self.base / "outside.epub"
        with self.assertRaises(Exception):
            self.engine.consume_jsonl(
                self.semantic(2, "FILE_READY", path=str(outside))
            )
        self.assertEqual(self.engine.current_state(), before)

    def test_inventory_failure_does_not_claim_fresh_or_commit_partial_state(self) -> None:
        self.write_epub("book.epub", b"book")
        initial = self.engine.current_state()
        with patch.object(
            self.broker,
            "issue_read_handle",
            side_effect=CoreAccessError("forced-safe-read-failure"),
        ):
            with self.assertRaisesRegex(ReconciliationError, "inventory-safe-read-failed"):
                self.engine.reconcile_inventory()
        self.assertEqual(self.engine.current_state(), initial)
        self.assertIsNone(self.store.load())


if __name__ == "__main__":
    unittest.main()
