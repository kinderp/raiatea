from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prototype.p0_vs1.catalog_store import CatalogSnapshot, CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.extraction_service import LocalEpubExtractionService
from prototype.p0_vs1.reconciliation import Vs1ObservationScopeRegistry, Vs1bReconciliationEngine
from prototype.p0_vs1.search_contract import (
    SearchContractError,
    canonical_json_bytes,
    normalize_query_plan,
    search_index_fingerprint,
)
from prototype.p0_vs1.search_service import (
    SearchServiceError,
    SearchViewService,
    build_search_index,
    current_upstream_basis_fingerprint,
    validate_vs1e_state,
)
from prototype.p0_vs1.source_service import LocalSourceDiscoveryService


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"
_GEN_SPEC = importlib.util.spec_from_file_location("vs1e_fixture_generator", GENERATOR_PATH)
GENERATOR = importlib.util.module_from_spec(_GEN_SPEC)
assert _GEN_SPEC.loader is not None
_GEN_SPEC.loader.exec_module(GENERATOR)


def plan(
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


class Vs1eFixture(unittest.TestCase):
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
            self.extraction.extract(
                source_ref,
                rights_evidence_state="known-permitted",
            )
        self.search = SearchViewService(self.store, "scope:library")
        self.search.rebuild_index()

    def tearDown(self) -> None:
        self.broker.close()
        self.scopes.close()
        self.temp.cleanup()


class StructuredSearchTests(Vs1eFixture):
    def test_current_epub_content_is_searchable_with_match_evidence(self) -> None:
        intro = self.search.search(plan(("extracted_text", "contains", "Introduction")))
        self.assertEqual(intro["freshness"], "fresh")
        self.assertEqual(len(intro["source_ids"]), 1)
        self.assertTrue(intro["hits"][0]["matched_unit_refs"])

        details = self.search.search(plan(("extracted_text", "contains", "Details are in the second resource.")))
        self.assertEqual(details["freshness"], "fresh")
        self.assertEqual(len(details["source_ids"]), 1)
        self.assertNotEqual(intro["source_ids"], details["source_ids"])

        headings = self.search.search(plan(("semantic_type", "has", "heading")))
        self.assertEqual(headings["freshness"], "fresh")
        self.assertEqual(len(headings["source_ids"]), 2)
        self.assertTrue(all(hit["matched_unit_refs"] for hit in headings["hits"]))

        resource = self.search.search(plan(("resource", "has", "OEBPS/ch1.xhtml")))
        self.assertEqual(resource["freshness"], "fresh")
        self.assertEqual(len(resource["source_ids"]), 2)

        provider = self.search.search(plan(("provider_id", "eq", "python-stdlib")))
        route = self.search.search(plan(("route_profile", "eq", "direct-epub-stdlib")))
        self.assertEqual(provider["source_ids"], route["source_ids"])
        self.assertEqual(len(provider["source_ids"]), 2)

    def test_criteria_order_and_primary_sort_ties_are_deterministic(self) -> None:
        a = plan(
            ("provider_id", "eq", "python-stdlib"),
            ("semantic_type", "has", "heading"),
            sort_field="media_type",
            descending=True,
        )
        b = plan(
            ("semantic_type", "has", "heading"),
            ("provider_id", "eq", "python-stdlib"),
            sort_field="media_type",
            descending=True,
        )
        first = self.search.search(a)
        second = self.search.search(b)
        self.assertEqual(first["normalized_plan"], second["normalized_plan"])
        self.assertEqual(first["source_ids"], second["source_ids"])
        self.assertEqual(first["source_ids"], sorted(first["source_ids"]))

    def test_index_is_independent_of_nonsemantic_unit_and_entry_iteration_order(self) -> None:
        current = self.store.load()
        first = build_search_index(current, "scope:library")
        payload = deepcopy(current.payload)
        payload["vs1b"]["entries"] = list(reversed(payload["vs1b"]["entries"]))
        for extraction in payload["vs1d"]["extractions"]:
            for ref in extraction["record_refs"]:
                if ref["record_kind"] == "NormalizedRepresentationRecord":
                    record = extraction["records"][ref["ref_id"]]
                    record["units"] = list(reversed(record["units"]))
        reordered = CatalogSnapshot(revision=current.revision, payload=payload)
        second = build_search_index(reordered, "scope:library")
        self.assertEqual(first, second)
        self.assertEqual(search_index_fingerprint(first), search_index_fingerprint(second))

    def test_unknown_or_powerful_query_surfaces_fail_closed(self) -> None:
        cases = [
            plan(("title", "contains", "x")),
            plan(("extracted_text", "regex", ".*")),
            plan(("path", "eq", "/tmp")),
            plan(("natural_language", "eq", "find books")),
            plan(("embedding", "eq", "vector")),
            {"criteria": [], "sort_field": "relevance", "descending": False},
            {
                "criteria": [
                    {"field": "extracted_text", "operator": "contains", "value": True}
                ],
                "sort_field": "source_ref_id",
                "descending": False,
            },
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaises(SearchContractError):
                    normalize_query_plan(candidate)


class FreshnessTests(Vs1eFixture):
    def test_view_only_catalog_write_does_not_make_index_stale(self) -> None:
        before = self.search.search(plan(("semantic_type", "has", "heading")))
        basis = before["current_upstream_basis_fingerprint"]
        revision_before = self.store.load().revision
        self.search.save_view(
            "view:headings",
            plan(("semantic_type", "has", "heading")),
            ["source_ref_id", "media_type", "unit_count"],
        )
        self.assertGreater(self.store.load().revision, revision_before)
        after = self.search.search(plan(("semantic_type", "has", "heading")))
        self.assertEqual(after["freshness"], "fresh")
        self.assertEqual(after["current_upstream_basis_fingerprint"], basis)

    def test_upstream_change_makes_index_stale_and_returns_no_current_ids(self) -> None:
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["entries"][0]["current_location"] = "renamed.epub"
        self.store.save(payload, expected_revision=current.revision)
        result = self.search.search(plan(("semantic_type", "has", "heading")))
        self.assertEqual(result["freshness"], "stale")
        self.assertEqual(result["source_ids"], [])
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["blocked_reason"], "index-not-current")

    def test_nonfresh_upstream_never_claims_fresh_search(self) -> None:
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "test-gap",
        }
        self.store.save(payload, expected_revision=current.revision)
        result = self.search.search(plan(("semantic_type", "has", "heading")))
        self.assertEqual(result["freshness"], "stale")
        self.assertEqual(result["source_ids"], [])
        self.assertEqual(result["blocked_reason"], "upstream-not-current")
        with self.assertRaisesRegex(SearchServiceError, "not-fresh"):
            self.search.rebuild_index()


class ViewTests(Vs1eFixture):
    def test_view_persists_and_projects_deterministically(self) -> None:
        self.search.save_view(
            "view:details",
            plan(("extracted_text", "contains", "Details are in the second resource.")),
            ["source_ref_id", "provider_id", "route_profile", "unit_count"],
        )
        result = self.search.evaluate_view("view:details")
        self.assertEqual(result["freshness"], "fresh")
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(
            list(result["rows"][0]),
            ["source_ref_id", "provider_id", "route_profile", "unit_count"],
        )
        persisted = self.store.load().payload["vs1e"]
        validate_vs1e_state(persisted, "scope:library")
        self.assertEqual([row["view_id"] for row in persisted["views"]], ["view:details"])

    def test_invalid_view_projection_and_stale_view_fail_closed(self) -> None:
        with self.assertRaises(SearchContractError):
            self.search.save_view(
                "view:bad",
                plan(),
                ["source_ref_id", "path"],
            )
        self.search.save_view("view:all", plan(), ["source_ref_id"])
        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["entries"][0]["current_location"] = "changed.epub"
        self.store.save(payload, expected_revision=current.revision)
        with self.assertRaisesRegex(SearchServiceError, "fresh-index"):
            self.search.evaluate_view("view:all")


class SmartCollectionTests(Vs1eFixture):
    def test_rule_is_separate_from_members_and_updates_after_real_catalog_growth(self) -> None:
        created = self.search.save_smart_collection(
            "smart:active",
            plan(("extracted_text", "contains", "Inert Active Content")),
        )
        self.assertEqual(created["members"], [])
        before = deepcopy(
            self.store.load().payload["vs1e"]["smart_collections"][0]["rule"]
        )
        before_bytes = canonical_json_bytes(before)

        GENERATOR.generate_epub_inert_active_content(self.root / "active.epub")
        self.reconciliation.reconcile_inventory()
        stale = self.search.search(plan(("semantic_type", "has", "heading")))
        self.assertEqual(stale["freshness"], "stale")
        with self.assertRaisesRegex(SearchServiceError, "fresh-index"):
            self.search.reevaluate_smart_collection("smart:active")

        discovered = self.discovery.discover(rights_evidence_state="known-permitted")
        extracted_ids = {
            row["source_ref_id"]
            for row in self.store.load().payload["vs1d"]["extractions"]
        }
        new_refs = [ref for ref in discovered["source_refs"] if ref not in extracted_ids]
        self.assertEqual(len(new_refs), 1)
        self.extraction.extract(new_refs[0], rights_evidence_state="known-permitted")
        self.search.rebuild_index()
        refreshed = self.search.reevaluate_smart_collection("smart:active")
        self.assertEqual(len(refreshed["members"]), 1)
        after = self.store.load().payload["vs1e"]["smart_collections"][0]
        self.assertEqual(canonical_json_bytes(after["rule"]), before_bytes)
        self.assertEqual(after["current_members"], refreshed["members"])
        self.assertEqual(
            after["evaluated_upstream_basis_fingerprint"],
            current_upstream_basis_fingerprint(self.store.load(), "scope:library"),
        )


class PersistenceAndRaceTests(Vs1eFixture):
    def test_vs1e_state_survives_reload_and_malformed_version_fails_closed(self) -> None:
        self.search.save_view("view:all", plan(), ["source_ref_id"])
        self.search.save_smart_collection("smart:all", plan())
        reloaded = CatalogStateStore(self.store.path).load()
        validate_vs1e_state(reloaded.payload["vs1e"], "scope:library")

        payload = deepcopy(reloaded.payload)
        payload["vs1e"]["state_version"] = "unsupported"
        self.store.save(payload, expected_revision=reloaded.revision)
        with self.assertRaisesRegex(SearchServiceError, "version-unsupported"):
            self.search.search(plan())

    def test_concurrent_catalog_write_rejects_stale_index_build(self) -> None:
        import prototype.p0_vs1.search_service as service_module

        real_build = service_module.build_search_index
        other_store = CatalogStateStore(self.store.path)

        def build_then_change(snapshot: CatalogSnapshot, scope_id: str) -> dict:
            index = real_build(snapshot, scope_id)
            current = other_store.load()
            payload = deepcopy(current.payload)
            payload["concurrent_marker"] = {"changed": True}
            other_store.save(payload, expected_revision=current.revision)
            return index

        with patch.object(service_module, "build_search_index", new=build_then_change):
            with self.assertRaisesRegex(SearchServiceError, "catalog-changed-during-build"):
                self.search.rebuild_index()
        self.assertIn("concurrent_marker", self.store.load().payload)


if __name__ == "__main__":
    unittest.main()
