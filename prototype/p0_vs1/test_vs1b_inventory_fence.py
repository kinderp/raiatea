from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.reconciliation import (
    ReconciliationError,
    Vs1ObservationScopeRegistry,
    Vs1bReconciliationEngine,
    scan_epub_inventory,
)


class Vs1bInventoryFenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "library"
        self.outputs = self.base / "outputs"
        self.root.mkdir()
        self.outputs.mkdir()
        self.book = self.root / "book.epub"
        self.book.write_bytes(b"PK\x03\x04book")
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

    def _line(self, value: dict) -> str:
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)

    def _raw(self, seq: int) -> str:
        return self._line(
            {
                "schema_version": 0,
                "seq": seq,
                "layer": "normalized_raw",
                "category": "filesystem",
                "type": "RAW_CREATE",
                "source": 1,
                "backend": "inotify",
                "path": str(self.root / "baseline"),
            }
        )

    def _modified(self, seq: int) -> str:
        return self._line(
            {
                "schema_version": 0,
                "seq": seq,
                "layer": "semantic",
                "category": "filesystem",
                "type": "FILE_MODIFIED",
                "backend": "inotify",
                "path": str(self.book),
            }
        )

    def test_concurrent_alfred_record_prevents_stale_inventory_from_becoming_fresh(self) -> None:
        baseline = self.engine.consume_jsonl(self._raw(1))
        self.assertEqual(baseline["status"], "baseline-unproven-not-applied")
        self.engine.reconcile_inventory()
        self.assertEqual(self.engine.current_state()["freshness"]["status"], "fresh")

        real_scan = scan_epub_inventory
        observed: dict[str, object] = {}

        def scan_with_concurrent_event(*args: object, **kwargs: object) -> list[dict]:
            observed.update(self.engine.consume_jsonl(self._modified(2)))
            return real_scan(*args, **kwargs)

        with patch(
            "prototype.p0_vs1.reconciliation.scan_epub_inventory",
            side_effect=scan_with_concurrent_event,
        ):
            with self.assertRaisesRegex(
                ReconciliationError,
                "inventory-state-changed-during-scan",
            ):
                self.engine.reconcile_inventory()

        self.assertEqual(observed["status"], "applied")
        state = self.engine.current_state()
        self.assertEqual(state["stream"]["last_seq"], 2)
        self.assertEqual(state["stream"]["last_reconciled_seq"], 1)
        self.assertEqual(state["freshness"]["status"], "reconcile-required")
        self.assertNotEqual(state["freshness"]["reason"], "bounded-inventory-complete")


if __name__ == "__main__":
    unittest.main()
