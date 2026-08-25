from __future__ import annotations

from dataclasses import fields
import unittest

from search_view_proof import (
    CatalogItem,
    CatalogSnapshot,
    Criterion,
    QueryPlan,
    SearchProofError,
    SmartCollection,
    ViewDefinition,
    create_view,
    evaluate_smart_collection,
    inspect_plan,
    normalize_plan,
    run_search,
)


def item(
    item_id: str,
    title: str,
    *,
    media_type: str = "application/epub+zip",
    tags: tuple[str, ...] = (),
    text: str = "",
    year: int | None = None,
) -> CatalogItem:
    return CatalogItem(
        item_id=item_id,
        title=title,
        media_type=media_type,
        tags=tags,
        extracted_text=text,
        year=year,
    )


def fresh_snapshot(items, revision: int = 1) -> CatalogSnapshot:
    return CatalogSnapshot(
        catalog_revision=revision,
        index_revision=revision,
        items=tuple(items),
    )


BASE_ITEMS = (
    item("item:003", "Signals", tags=("ai", "research"), text="Neural compression signals", year=2025),
    item("item:001", "Atlas", tags=("reference",), text="Filesystem observation handbook", year=2024),
    item("item:004", "Signals", tags=("ai",), text="Deterministic catalog search", year=2026),
    item("item:002", "Raiatea", media_type="application/pdf", tags=("ai", "docs"), text="Knowledge observatory architecture", year=2026),
)


class DeterministicSearchViewProofTests(unittest.TestCase):
    def test_query_plan_is_normalized_and_inspectable(self):
        left = QueryPlan(
            criteria=(
                Criterion("tag", "has", "AI"),
                Criterion("media_type", "eq", "APPLICATION/EPUB+ZIP"),
            ),
            sort_field="title",
        )
        right = QueryPlan(
            criteria=(
                Criterion("media_type", "eq", "application/epub+zip"),
                Criterion("tag", "has", "ai"),
            ),
            sort_field="title",
        )
        self.assertEqual(inspect_plan(left), inspect_plan(right))
        self.assertEqual(normalize_plan(left), normalize_plan(right))

    def test_structured_metadata_and_extracted_text_filters(self):
        snapshot = fresh_snapshot(BASE_ITEMS)
        plan = QueryPlan(
            criteria=(
                Criterion("tag", "has", "ai"),
                Criterion("extracted_text", "contains", "catalog"),
                Criterion("year", "eq", 2026),
            ),
            sort_field="title",
        )
        result = run_search(snapshot, plan)
        self.assertEqual(result.freshness, "fresh")
        self.assertEqual(result.item_ids, ("item:004",))
        self.assertEqual(result.blocked_reason, None)

    def test_unknown_filter_field_fails_closed(self):
        with self.assertRaisesRegex(SearchProofError, "unsupported-filter-field:embedding"):
            normalize_plan(QueryPlan(criteria=(Criterion("embedding", "nearest", "x"),)))

    def test_unknown_operator_fails_closed(self):
        with self.assertRaisesRegex(SearchProofError, "unsupported-filter-operator:title:semantic"):
            normalize_plan(QueryPlan(criteria=(Criterion("title", "semantic", "atlas"),)))

    def test_unknown_sort_field_fails_closed(self):
        with self.assertRaisesRegex(SearchProofError, "unsupported-sort-field:score"):
            normalize_plan(QueryPlan(criteria=(), sort_field="score"))

    def test_stable_order_has_explicit_item_id_tie_breaker(self):
        plan = QueryPlan(criteria=(Criterion("tag", "has", "ai"),), sort_field="title")
        first = run_search(fresh_snapshot(BASE_ITEMS), plan)
        second = run_search(fresh_snapshot(tuple(reversed(BASE_ITEMS))), plan)
        self.assertEqual(first.item_ids, second.item_ids)
        self.assertEqual(first.item_ids, ("item:002", "item:003", "item:004"))
        # The two equal-title Signals rows use ascending item_id as a stable tie-breaker.
        self.assertLess(first.item_ids.index("item:003"), first.item_ids.index("item:004"))

    def test_descending_primary_sort_keeps_item_id_tie_breaker_explicit(self):
        plan = QueryPlan(criteria=(Criterion("tag", "has", "ai"),), sort_field="title", descending=True)
        result = run_search(fresh_snapshot(tuple(reversed(BASE_ITEMS))), plan)
        self.assertEqual(result.item_ids[:2], ("item:003", "item:004"))

    def test_stale_index_cannot_masquerade_as_fresh_results(self):
        snapshot = CatalogSnapshot(catalog_revision=7, index_revision=6, items=BASE_ITEMS)
        result = run_search(snapshot, QueryPlan(criteria=()))
        self.assertEqual(result.freshness, "stale")
        self.assertEqual(result.item_ids, ())
        self.assertEqual(result.blocked_reason, "index-not-current")
        self.assertEqual(result.catalog_revision, 7)
        self.assertEqual(result.index_revision, 6)

    def test_view_is_query_projection_without_mutation_authority(self):
        view = create_view(
            "view:ai",
            QueryPlan(criteria=(Criterion("tag", "has", "ai"),), sort_field="title"),
            ("item_id", "title", "tags"),
        )
        self.assertIsInstance(view, ViewDefinition)
        self.assertEqual(view.projection, ("item_id", "title", "tags"))
        record_fields = {field.name for field in fields(ViewDefinition)}
        self.assertTrue({"view_id", "plan", "projection"} <= record_fields)
        self.assertTrue(record_fields.isdisjoint({"path", "target_path", "move_to", "delete", "write", "organize"}))

    def test_view_rejects_filesystem_or_unknown_projection(self):
        plan = QueryPlan(criteria=())
        with self.assertRaisesRegex(SearchProofError, "view-mutation-authority-forbidden:target_path"):
            create_view("view:bad", plan, ("item_id", "target_path"))
        with self.assertRaisesRegex(SearchProofError, "unsupported-view-projection:extracted_text"):
            create_view("view:bad", plan, ("item_id", "extracted_text"))

    def test_smart_collection_stores_rule_separately_from_members(self):
        rule = QueryPlan(criteria=(Criterion("tag", "has", "ai"),), sort_field="item_id")
        collection = evaluate_smart_collection("smart:ai", rule, fresh_snapshot(BASE_ITEMS, revision=10))
        self.assertIsInstance(collection, SmartCollection)
        self.assertEqual(collection.current_members, ("item:002", "item:003", "item:004"))
        self.assertEqual(collection.evaluated_revision, 10)
        self.assertNotIn("current_members", {field.name for field in fields(QueryPlan)})
        self.assertEqual(collection.rule, normalize_plan(rule))

    def test_smart_collection_recomputation_is_deterministic_after_catalog_change(self):
        rule = QueryPlan(criteria=(Criterion("tag", "has", "ai"),), sort_field="item_id")
        before = evaluate_smart_collection("smart:ai", rule, fresh_snapshot(BASE_ITEMS, revision=1))
        changed = tuple(
            item(
                row.item_id,
                row.title,
                media_type=row.media_type,
                tags=(() if row.item_id == "item:003" else row.tags),
                text=row.extracted_text,
                year=row.year,
            )
            for row in BASE_ITEMS
        )
        after = evaluate_smart_collection("smart:ai", rule, fresh_snapshot(tuple(reversed(changed)), revision=2))
        self.assertEqual(before.rule, after.rule)
        self.assertEqual(before.current_members, ("item:002", "item:003", "item:004"))
        self.assertEqual(after.current_members, ("item:002", "item:004"))
        self.assertEqual(after.evaluated_revision, 2)

    def test_smart_collection_refuses_stale_index(self):
        snapshot = CatalogSnapshot(catalog_revision=2, index_revision=1, items=BASE_ITEMS)
        with self.assertRaisesRegex(SearchProofError, "smart-collection-requires-fresh-index"):
            evaluate_smart_collection("smart:ai", QueryPlan(criteria=()), snapshot)


if __name__ == "__main__":
    unittest.main()
