from __future__ import annotations

from copy import deepcopy
import unittest

from prototype.p0_vs1.application_facade import (
    ApplicationFacadeError,
    RaiateaApplicationFacade,
)
from prototype.p0_vs1 import test_vs1e as vs1e_tests


def _plan() -> dict:
    return {
        "criteria": [],
        "sort_field": "source_ref_id",
        "descending": False,
    }


class _MutableExtractionReader:
    """Small fake whose visible result can change without catalog mutation."""

    def __init__(self) -> None:
        self.generation = 1

    def current_summaries(self, snapshot, source_refs):
        result = {}
        for source in source_refs:
            source_ref_id = source["source_ref_id"]
            suffix = source_ref_id.removeprefix("source-ref:")[-12:]
            representation_id = f"mutable-representation:{self.generation}:{suffix}"
            result[source_ref_id] = {
                "state": "current",
                "state_family": "mutable-fake",
                "source_ref_id": source_ref_id,
                "provider": {
                    "provider_id": "mutable-fake",
                    "version": str(self.generation),
                    "route_profile": "mutable-profile",
                },
                "run": {"run_id": f"mutable-run:{self.generation}:{suffix}"},
                "representation": {
                    "representation_id": representation_id,
                    "unit_count": 1,
                    "coordinate_families": [],
                    "evidence_state_by_family": {
                        "surface": ["present"],
                        "semantic_role": ["unavailable"],
                        "coordinate": ["unavailable"],
                    },
                },
                "rights": None,
                "provenance": {"generation": self.generation},
                "diagnostics": {
                    "state": "measured",
                    "count": 0,
                    "by_severity": {},
                    "items": [],
                },
                "warnings": {
                    "state": "measured",
                    "count": 0,
                    "highest_severity": None,
                },
            }
        return result

    def representation_page(
        self,
        snapshot,
        representation_id,
        *,
        page_size,
        cursor,
    ):
        return {
            "representation_id": representation_id,
            "basis": "sha256:" + "e" * 64,
            "cursor": cursor,
            "next_cursor": None,
            "units": [],
        }


class ApplicationFacadeResultBasisTests(vs1e_tests.Vs1eFixture):
    def setUp(self) -> None:
        super().setUp()
        self.reader = _MutableExtractionReader()
        self.facade = RaiateaApplicationFacade(
            self.store,
            "scope:library",
            extraction_reader=self.reader,
        )

    def test_library_cursor_invalidates_when_visible_extraction_changes(self) -> None:
        first = self.facade.library_page(page_size=1)
        self.assertIsNotNone(first["next_cursor"])

        self.reader.generation += 1

        with self.assertRaisesRegex(ApplicationFacadeError, "cursor-stale"):
            self.facade.library_page(
                page_size=1,
                cursor=first["next_cursor"],
            )

    def test_search_cursor_invalidates_when_composed_library_rows_change(self) -> None:
        first = self.facade.search_page(_plan(), page_size=1)
        self.assertEqual(first["freshness"], "fresh")
        self.assertIsNotNone(first["next_cursor"])

        self.reader.generation += 1

        with self.assertRaisesRegex(ApplicationFacadeError, "cursor-stale"):
            self.facade.search_page(
                _plan(),
                page_size=1,
                cursor=first["next_cursor"],
            )

    def test_old_representation_id_is_not_read_after_extraction_projection_changes(self) -> None:
        item = self.facade.library_page(page_size=1)["items"][0]
        detail = self.facade.source_detail(item["item_ref"])
        representation_id = detail["representations"][0]["representation_id"]

        self.reader.generation += 1

        with self.assertRaisesRegex(
            ApplicationFacadeError,
            "representation-not-current",
        ):
            self.facade.representation_page(representation_id)

    def test_representation_page_is_blocked_when_catalog_becomes_stale(self) -> None:
        normal = RaiateaApplicationFacade(self.store, "scope:library")
        item = normal.library_page(page_size=1)["items"][0]
        detail = normal.source_detail(item["item_ref"])
        representation_id = detail["representations"][0]["representation_id"]

        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "representation-direct-read-fence-test",
        }
        self.store.save(payload, expected_revision=current.revision)

        with self.assertRaisesRegex(
            ApplicationFacadeError,
            "representation-not-current",
        ):
            normal.representation_page(representation_id)


if __name__ == "__main__":
    unittest.main()
