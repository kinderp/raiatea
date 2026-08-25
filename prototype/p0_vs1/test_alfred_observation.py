from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.alfred_observation import (
    ALFRED_EVIDENCE_REVISION,
    AlfredObservationAdapter,
    AlfredObservationError,
)
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry


class AlfredObservationAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = (Path(self.temp.name) / "library").resolve()
        self.root.mkdir()
        self.scopes = Vs1ObservationScopeRegistry()
        self.scopes.register_scope("scope:library", self.root)
        self.adapter = AlfredObservationAdapter(self.scopes)

    def tearDown(self) -> None:
        self.scopes.close()
        self.temp.cleanup()

    def line(self, value: dict) -> str:
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)

    def semantic(self, event_type: str, *, seq: int = 10, **paths: str) -> dict:
        return {
            "schema_version": 0,
            "seq": seq,
            "ts_ns": 123456789,
            "layer": "semantic",
            "category": "filesystem",
            "type": event_type,
            "backend": "inotify",
            **paths,
        }

    def test_single_path_semantic_mappings_match_alfred_v0(self) -> None:
        expected = {
            "FILE_CREATED": "location-appeared",
            "DIR_CREATED": "location-appeared",
            "FILE_READY": "content-ready",
            "FILE_MODIFIED": "location-content-changed",
            "FILE_DELETED": "location-disappeared-observed",
            "DIR_DELETED": "location-disappeared-observed",
        }
        for event_type, kind in expected.items():
            with self.subTest(event_type=event_type):
                path = self.root / ("dir" if event_type.startswith("DIR_") else "book.epub")
                record = self.semantic(event_type, path=str(path))
                adapted = self.adapter.adapt_jsonl("scope:library", self.line(record))
                self.assertTrue(adapted["authoritative_catalog_evidence"])
                self.assertEqual(adapted["observation"]["kind"], kind)
                self.assertEqual(
                    adapted["observation"]["location"],
                    "dir" if event_type.startswith("DIR_") else "book.epub",
                )
                self.assertEqual(adapted["source_seq"], 10)
                self.assertEqual(adapted["observer"]["alfred_revision"], ALFRED_EVIDENCE_REVISION)

    def test_transition_semantic_uses_old_and_new_without_path_alias(self) -> None:
        for event_type in (
            "FILE_RENAMED",
            "FILE_MOVED",
            "FILE_RELOCATED",
            "DIR_RENAMED",
            "DIR_MOVED",
            "DIR_RELOCATED",
        ):
            with self.subTest(event_type=event_type):
                old = self.root / "old.epub"
                new = self.root / "nested" / "new.epub"
                record = self.semantic(
                    event_type,
                    old_path=str(old),
                    new_path=str(new),
                    identity={"device_id": 8, "inode_id": 123},
                )
                adapted = self.adapter.adapt("scope:library", record)
                obs = adapted["observation"]
                self.assertEqual(obs["kind"], "location-transition")
                self.assertEqual(obs["old_location"], "old.epub")
                self.assertEqual(obs["new_location"], "nested/new.epub")
                self.assertEqual(obs["filesystem_identity"], {"device_id": 8, "inode_id": 123})

    def test_global_overflow_is_pathless_and_uncertain(self) -> None:
        adapted = self.adapter.adapt(
            "scope:library",
            self.semantic("OVERFLOW", seq=20),
        )
        obs = adapted["observation"]
        self.assertEqual(obs["kind"], "observation-incomplete")
        self.assertEqual(obs["confidence"], "uncertain")
        self.assertEqual(obs["freshness_effect"], "reconcile-required")
        self.assertTrue(set(obs).isdisjoint({"location", "old_location", "new_location"}))

    def test_diagnostic_stale_and_recovery_end_never_claim_catalog_freshness(self) -> None:
        stale = {
            "schema_version": 0,
            "seq": 30,
            "layer": "diagnostic",
            "category": "watch",
            "type": "WATCH_STALE",
            "backend": "inotify",
            "path": str(self.root),
            "watch": {"watch_id": 7, "state": "stale", "reason": "IN_MOVE_SELF"},
        }
        recovery_end = {
            "schema_version": 0,
            "seq": 31,
            "layer": "diagnostic",
            "category": "recovery",
            "type": "WATCH_RESYNC_END",
            "backend": "inotify",
            "path": str(self.root),
            "recovery": {"directories_seen": 2, "directories_watched": 2},
        }
        stale_adapted = self.adapter.adapt("scope:library", stale)
        end_adapted = self.adapter.adapt("scope:library", recovery_end)
        self.assertFalse(stale_adapted["authoritative_catalog_evidence"])
        self.assertEqual(stale_adapted["observation"]["kind"], "observer-health")
        self.assertEqual(stale_adapted["observation"]["freshness_effect"], "reconcile-required")
        self.assertEqual(
            end_adapted["observation"]["freshness_effect"],
            "observer-recovered-reconcile-still-required",
        )

    def test_actual_jsonl_stale_event_dropped_shape_is_accepted(self) -> None:
        # Mirrors Alfred test_record_jsonl.c: schema/layer/category/type/backend/path/watch.
        record = {
            "schema_version": 0,
            "layer": "diagnostic",
            "category": "watch",
            "type": "WATCH_STALE_EVENT_DROPPED",
            "backend": "inotify",
            "path": str(self.root / "watched"),
            "watch": {"watch_id": 7, "event_mask": "IN_CREATE", "event_name": "a.txt"},
        }
        adapted = self.adapter.adapt("scope:library", record)
        self.assertEqual(adapted["observation"]["diagnostic_type"], "WATCH_STALE_EVENT_DROPPED")
        self.assertEqual(adapted["observation"]["location"], "watched")

    def test_normalized_raw_record_advances_stream_evidence_but_is_not_catalog_truth(self) -> None:
        record = {
            "schema_version": 0,
            "seq": 44,
            "layer": "normalized_raw",
            "category": "filesystem",
            "type": "RAW_MOVED_FROM",
            "source": 1,
            "raw_mask": 64,
            "cookie": 123,
            "path": str(self.root / "old.epub"),
        }
        adapted = self.adapter.adapt("scope:library", record)
        self.assertEqual(adapted["source_seq"], 44)
        self.assertFalse(adapted["authoritative_catalog_evidence"])
        self.assertIsNone(adapted["observation"])

    def test_session_context_is_non_authoritative(self) -> None:
        record = {
            "schema_version": 0,
            "seq": 45,
            "layer": "diagnostic",
            "category": "lifecycle",
            "type": "SESSION_CONTEXT",
            "workspace": {"root": str(self.root), "id": "ws-raiatea"},
            "ledger": {"session_id": "session:1"},
        }
        adapted = self.adapter.adapt("scope:library", record)
        self.assertFalse(adapted["authoritative_catalog_evidence"])
        self.assertIsNone(adapted["observation"])

    def test_record_id_is_deterministic_independent_of_json_key_order(self) -> None:
        record = self.semantic("FILE_READY", path=str(self.root / "book.epub"), seq=50)
        reordered = {key: record[key] for key in reversed(tuple(record))}
        left = self.adapter.adapt("scope:library", record)
        right = self.adapter.adapt("scope:library", reordered)
        self.assertEqual(left["source_record_id"], right["source_record_id"])
        self.assertEqual(left["observation"]["observation_id"], right["observation"]["observation_id"])

    def test_unknown_schema_field_tuple_and_invented_event_id_fail_closed(self) -> None:
        bad_records = []
        wrong_schema = self.semantic("FILE_READY", path=str(self.root / "book.epub"))
        wrong_schema["schema_version"] = 1
        bad_records.append((wrong_schema, "alfred-schema-version-unsupported"))

        extra = self.semantic("FILE_READY", path=str(self.root / "book.epub"))
        extra["future_field"] = True
        bad_records.append((extra, "alfred-record-unknown-field:future_field"))

        invented = self.semantic("FILE_READY", path=str(self.root / "book.epub"))
        invented["event_id"] = "not-in-current-jsonl-v0"
        bad_records.append((invented, "alfred-record-unknown-field:event_id"))

        bad_tuple = {
            "schema_version": 0,
            "layer": "semantic",
            "category": "watch",
            "type": "WATCH_STALE",
        }
        bad_records.append((bad_tuple, "alfred-record-tuple-unsupported"))

        for record, message in bad_records:
            with self.subTest(message=message):
                with self.assertRaisesRegex(AlfredObservationError, message):
                    self.adapter.adapt("scope:library", record)

    def test_semantic_path_applicability_is_fail_closed(self) -> None:
        single_with_alias = self.semantic(
            "FILE_READY",
            path=str(self.root / "book.epub"),
            old_path=str(self.root / "old.epub"),
        )
        transition_with_path = self.semantic(
            "FILE_RENAMED",
            path=str(self.root / "alias.epub"),
            old_path=str(self.root / "old.epub"),
            new_path=str(self.root / "new.epub"),
        )
        overflow_with_path = self.semantic("OVERFLOW", path=str(self.root))
        for record in (single_with_alias, transition_with_path, overflow_with_path):
            with self.assertRaises(AlfredObservationError):
                self.adapter.adapt("scope:library", record)

    def test_out_of_scope_absolute_alfred_path_is_rejected(self) -> None:
        outside = (self.root.parent / "outside.epub").resolve()
        with self.assertRaisesRegex(AlfredObservationError, "alfred-path-outside-bound-scope"):
            self.adapter.adapt(
                "scope:library",
                self.semantic("FILE_READY", path=str(outside)),
            )

    def test_jsonl_parser_rejects_multiple_frames_and_invalid_json(self) -> None:
        with self.assertRaisesRegex(AlfredObservationError, "alfred-jsonl-must-be-one-frame"):
            self.adapter.parse_jsonl("{}\n{}")
        with self.assertRaisesRegex(AlfredObservationError, "alfred-jsonl-invalid"):
            self.adapter.parse_jsonl("{")


if __name__ == "__main__":
    unittest.main()
