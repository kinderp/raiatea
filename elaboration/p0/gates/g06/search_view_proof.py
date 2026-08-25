#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Iterable


class SearchProofError(ValueError):
    pass


@dataclass(frozen=True)
class CatalogItem:
    """Proof-only item shape; not a production catalog schema."""

    item_id: str
    title: str
    media_type: str
    tags: tuple[str, ...]
    extracted_text: str
    year: int | None = None


@dataclass(frozen=True)
class CatalogSnapshot:
    catalog_revision: int
    index_revision: int
    items: tuple[CatalogItem, ...]


@dataclass(frozen=True)
class Criterion:
    field: str
    operator: str
    value: str | int


@dataclass(frozen=True)
class QueryPlan:
    criteria: tuple[Criterion, ...]
    sort_field: str = "title"
    descending: bool = False


@dataclass(frozen=True)
class SearchResult:
    freshness: str
    catalog_revision: int
    index_revision: int
    item_ids: tuple[str, ...]
    normalized_plan: tuple[tuple[str, str, str], ...]
    blocked_reason: str | None = None


@dataclass(frozen=True)
class ViewDefinition:
    view_id: str
    plan: QueryPlan
    projection: tuple[str, ...]


@dataclass(frozen=True)
class SmartCollection:
    collection_id: str
    rule: QueryPlan
    current_members: tuple[str, ...]
    evaluated_revision: int


_FILTER_OPERATORS = {
    "item_id": {"eq"},
    "title": {"eq", "contains"},
    "media_type": {"eq"},
    "tag": {"has"},
    "extracted_text": {"contains"},
    "year": {"eq"},
}
_SORT_FIELDS = {"item_id", "title", "media_type", "year"}
_PROJECTION_FIELDS = {"item_id", "title", "media_type", "tags", "year"}
_FORBIDDEN_VIEW_AUTHORITY_FIELDS = {
    "path",
    "target_path",
    "move_to",
    "delete",
    "write",
    "organize",
    "filesystem_action",
}


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise SearchProofError(f"{label}-required")


def _normalized_scalar(value: str | int) -> str:
    if isinstance(value, bool):
        raise SearchProofError("criterion-value-bool-forbidden")
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, str) or not value:
        raise SearchProofError("criterion-value-invalid")
    return value.casefold()


def normalize_plan(plan: QueryPlan) -> QueryPlan:
    if plan.sort_field not in _SORT_FIELDS:
        raise SearchProofError(f"unsupported-sort-field:{plan.sort_field}")

    normalized: list[Criterion] = []
    for criterion in plan.criteria:
        operators = _FILTER_OPERATORS.get(criterion.field)
        if operators is None:
            raise SearchProofError(f"unsupported-filter-field:{criterion.field}")
        if criterion.operator not in operators:
            raise SearchProofError(
                f"unsupported-filter-operator:{criterion.field}:{criterion.operator}"
            )
        value = _normalized_scalar(criterion.value)
        if criterion.field == "year":
            try:
                year = int(value)
            except ValueError as exc:
                raise SearchProofError("year-filter-must-be-integer") from exc
            normalized.append(Criterion("year", criterion.operator, year))
        else:
            normalized.append(Criterion(criterion.field, criterion.operator, value))

    normalized.sort(key=lambda item: (item.field, item.operator, str(item.value)))
    return QueryPlan(
        criteria=tuple(normalized),
        sort_field=plan.sort_field,
        descending=bool(plan.descending),
    )


def inspect_plan(plan: QueryPlan) -> tuple[tuple[str, str, str], ...]:
    normalized = normalize_plan(plan)
    return tuple(
        (criterion.field, criterion.operator, str(criterion.value))
        for criterion in normalized.criteria
    )


def _match(item: CatalogItem, criterion: Criterion) -> bool:
    value = criterion.value
    if criterion.field == "item_id":
        return item.item_id.casefold() == str(value)
    if criterion.field == "title":
        observed = item.title.casefold()
        return observed == str(value) if criterion.operator == "eq" else str(value) in observed
    if criterion.field == "media_type":
        return item.media_type.casefold() == str(value)
    if criterion.field == "tag":
        tags = {tag.casefold() for tag in item.tags}
        return str(value) in tags
    if criterion.field == "extracted_text":
        return str(value) in item.extracted_text.casefold()
    if criterion.field == "year":
        return item.year == value
    raise SearchProofError(f"unsupported-filter-field:{criterion.field}")


def _sort_value(item: CatalogItem, field: str) -> Any:
    if field == "item_id":
        return item.item_id.casefold()
    if field == "title":
        return item.title.casefold()
    if field == "media_type":
        return item.media_type.casefold()
    if field == "year":
        # None remains deterministic and sorts before known years.
        return (-1 if item.year is None else item.year)
    raise SearchProofError(f"unsupported-sort-field:{field}")


def run_search(snapshot: CatalogSnapshot, plan: QueryPlan) -> SearchResult:
    normalized = normalize_plan(plan)
    inspected = inspect_plan(normalized)
    if snapshot.index_revision != snapshot.catalog_revision:
        return SearchResult(
            freshness="stale",
            catalog_revision=snapshot.catalog_revision,
            index_revision=snapshot.index_revision,
            item_ids=(),
            normalized_plan=inspected,
            blocked_reason="index-not-current",
        )

    matched = [
        item
        for item in snapshot.items
        if all(_match(item, criterion) for criterion in normalized.criteria)
    ]

    # Explicit stable tie-breaker: item_id is always ascending, even when the
    # primary sort direction is descending. Python's stable sort makes the
    # second pass preserve that tie-break ordering for equal primary values.
    matched.sort(key=lambda item: item.item_id.casefold())
    matched.sort(
        key=lambda item: _sort_value(item, normalized.sort_field),
        reverse=normalized.descending,
    )
    return SearchResult(
        freshness="fresh",
        catalog_revision=snapshot.catalog_revision,
        index_revision=snapshot.index_revision,
        item_ids=tuple(item.item_id for item in matched),
        normalized_plan=inspected,
    )


def create_view(view_id: str, plan: QueryPlan, projection: Iterable[str]) -> ViewDefinition:
    _require_text(view_id, "view-id")
    normalized = normalize_plan(plan)
    projected = tuple(projection)
    if not projected:
        raise SearchProofError("view-projection-required")
    for field_name in projected:
        if field_name in _FORBIDDEN_VIEW_AUTHORITY_FIELDS:
            raise SearchProofError(f"view-mutation-authority-forbidden:{field_name}")
        if field_name not in _PROJECTION_FIELDS:
            raise SearchProofError(f"unsupported-view-projection:{field_name}")

    # Defense in depth for future proof edits: the View proof record itself may
    # not grow filesystem-mutation authority fields without failing tests/code.
    record_fields = {field.name for field in fields(ViewDefinition)}
    leaked = sorted(record_fields & _FORBIDDEN_VIEW_AUTHORITY_FIELDS)
    if leaked:
        raise SearchProofError(f"view-record-authority-field-forbidden:{leaked[0]}")
    return ViewDefinition(view_id=view_id, plan=normalized, projection=projected)


def evaluate_smart_collection(
    collection_id: str,
    rule: QueryPlan,
    snapshot: CatalogSnapshot,
) -> SmartCollection:
    _require_text(collection_id, "collection-id")
    normalized = normalize_plan(rule)
    result = run_search(snapshot, normalized)
    if result.freshness != "fresh":
        raise SearchProofError("smart-collection-requires-fresh-index")
    return SmartCollection(
        collection_id=collection_id,
        rule=normalized,
        current_members=result.item_ids,
        evaluated_revision=snapshot.catalog_revision,
    )
