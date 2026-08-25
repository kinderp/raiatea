#!/usr/bin/env python3
"""VS1e deterministic structured-search contracts and pure evaluation.

This internal first-slice contract intentionally exposes no natural-language,
LLM, vector, regex, scripting or filesystem-action surface.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


SEARCH_INDEX_VERSION = "raiatea.vs1e.search-index.0.1.0"
VIEW_VERSION = "raiatea.vs1e.view.0.1.0"
SMART_COLLECTION_VERSION = "raiatea.vs1e.smart-collection.0.1.0"
MAX_QUERY_CRITERIA = 32
MAX_INDEX_SOURCES = 512
MAX_UNITS_PER_SOURCE = 8192

FILTER_OPERATORS = {
    "source_ref_id": frozenset({"eq"}),
    "media_type": frozenset({"eq"}),
    "extracted_text": frozenset({"contains"}),
    "semantic_type": frozenset({"has"}),
    "resource": frozenset({"has"}),
    "provider_id": frozenset({"eq"}),
    "route_profile": frozenset({"eq"}),
}
SORT_FIELDS = frozenset({"source_ref_id", "media_type", "unit_count"})
PROJECTION_FIELDS = frozenset(
    {
        "source_ref_id",
        "media_type",
        "fingerprint",
        "provider_id",
        "route_profile",
        "unit_count",
    }
)
FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {
        "path",
        "filepath",
        "file_path",
        "host_path",
        "filesystem_path",
        "location",
        "location_history",
        "root",
        "target_path",
        "move_to",
        "move",
        "write",
        "delete",
        "organize",
        "filesystem_action",
        "script",
        "regex",
        "natural_language",
        "prompt",
        "embedding",
        "vector",
    }
)


class SearchContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SearchContractError(message)


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SearchContractError("search-record-not-json-safe") from exc


def sha256_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == 71
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _opaque(value: Any, label: str) -> str:
    _require(isinstance(value, str) and value, f"{label}-required")
    _require("/" not in value and "\\" not in value, f"{label}-must-be-opaque")
    return value


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(keys - actual)
    extra = sorted(actual - keys)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _text(value: Any, label: str) -> str:
    _require(not isinstance(value, bool), f"{label}-bool-forbidden")
    _require(isinstance(value, str) and value, f"{label}-must-be-nonempty-text")
    return value


def normalize_query_plan(value: Any) -> dict[str, Any]:
    plan = _exact(value, {"criteria", "sort_field", "descending"}, "query-plan")
    criteria = plan["criteria"]
    _require(isinstance(criteria, list), "query-criteria-must-be-array")
    _require(len(criteria) <= MAX_QUERY_CRITERIA, "query-criteria-limit-exceeded")

    normalized: list[dict[str, str]] = []
    for index, raw in enumerate(criteria):
        row = _exact(raw, {"field", "operator", "value"}, f"criterion-{index}")
        field = _text(row["field"], f"criterion-{index}-field")
        operator = _text(row["operator"], f"criterion-{index}-operator")
        _require(
            field not in FORBIDDEN_AUTHORITY_FIELDS,
            f"query-authority-field-forbidden:{field}",
        )
        operators = FILTER_OPERATORS.get(field)
        _require(operators is not None, f"unsupported-filter-field:{field}")
        _require(
            operator in operators,
            f"unsupported-filter-operator:{field}:{operator}",
        )
        normalized.append(
            {
                "field": field,
                "operator": operator,
                "value": _text(row["value"], f"criterion-{index}-value").casefold(),
            }
        )
    normalized.sort(key=lambda row: (row["field"], row["operator"], row["value"]))

    sort_field = _text(plan["sort_field"], "query-sort-field")
    _require(sort_field in SORT_FIELDS, f"unsupported-sort-field:{sort_field}")
    _require(
        isinstance(plan["descending"], bool),
        "query-descending-must-be-boolean",
    )
    return {
        "criteria": normalized,
        "sort_field": sort_field,
        "descending": plan["descending"],
    }


def validate_search_unit(value: Any) -> dict[str, Any]:
    unit = _exact(
        value,
        {"unit_id", "surface", "semantic_type", "resource", "fragment", "spine_index"},
        "search-unit",
    )
    _opaque(unit["unit_id"], "search-unit-id")
    for key in ("surface", "semantic_type", "resource", "fragment"):
        _require(
            unit[key] is None or isinstance(unit[key], str),
            f"search-unit-{key}-invalid",
        )
    spine = unit["spine_index"]
    _require(
        spine is None
        or (
            isinstance(spine, int)
            and not isinstance(spine, bool)
            and spine >= 0
        ),
        "search-unit-spine-index-invalid",
    )
    return unit


def validate_index_source(value: Any) -> dict[str, Any]:
    source = _exact(
        value,
        {
            "source_ref_id",
            "logical_candidate_ref",
            "stored_instance_ref",
            "media_type",
            "fingerprint",
            "representation_id",
            "provider_id",
            "route_profile",
            "unit_count",
            "units",
        },
        "search-source",
    )
    for key in (
        "source_ref_id",
        "logical_candidate_ref",
        "stored_instance_ref",
        "representation_id",
        "provider_id",
        "route_profile",
    ):
        _opaque(source[key], f"search-source-{key}")
    _require(
        isinstance(source["media_type"], str) and source["media_type"],
        "search-source-media-type-required",
    )
    _require(
        _valid_sha256(source["fingerprint"]),
        "search-source-fingerprint-invalid",
    )
    _require(
        isinstance(source["unit_count"], int)
        and not isinstance(source["unit_count"], bool)
        and source["unit_count"] >= 0,
        "search-source-unit-count-invalid",
    )
    units = source["units"]
    _require(isinstance(units, list), "search-source-units-must-be-array")
    _require(
        len(units) <= MAX_UNITS_PER_SOURCE,
        "search-source-unit-limit-exceeded",
    )
    _require(
        source["unit_count"] == len(units),
        "search-source-unit-count-mismatch",
    )
    unit_ids: list[str] = []
    for raw in units:
        unit = validate_search_unit(raw)
        _require(unit["unit_id"] not in unit_ids, "search-unit-id-duplicate")
        unit_ids.append(unit["unit_id"])
    _require(unit_ids == sorted(unit_ids), "search-units-not-canonical-order")
    return source


def validate_search_index(value: Any) -> dict[str, Any]:
    index = _exact(
        value,
        {
            "index_version",
            "scope_ref",
            "built_from_catalog_revision",
            "upstream_basis_fingerprint",
            "sources",
        },
        "search-index",
    )
    _require(
        index["index_version"] == SEARCH_INDEX_VERSION,
        "search-index-version-unsupported",
    )
    _opaque(index["scope_ref"], "search-index-scope-ref")
    _require(
        isinstance(index["built_from_catalog_revision"], int)
        and not isinstance(index["built_from_catalog_revision"], bool)
        and index["built_from_catalog_revision"] >= 1,
        "search-index-catalog-revision-invalid",
    )
    _require(
        _valid_sha256(index["upstream_basis_fingerprint"]),
        "search-index-upstream-basis-invalid",
    )
    sources = index["sources"]
    _require(isinstance(sources, list), "search-index-sources-must-be-array")
    _require(
        len(sources) <= MAX_INDEX_SOURCES,
        "search-index-source-limit-exceeded",
    )
    source_ids: list[str] = []
    for raw in sources:
        source = validate_index_source(raw)
        _require(
            source["source_ref_id"] not in source_ids,
            "search-index-source-id-duplicate",
        )
        source_ids.append(source["source_ref_id"])
    _require(
        source_ids == sorted(source_ids),
        "search-index-sources-not-canonical-order",
    )
    return index


def search_index_fingerprint(index: dict[str, Any]) -> str:
    validate_search_index(index)
    return sha256_ref(index)


def _source_criterion_match(
    source: dict[str, Any],
    criterion: dict[str, str],
) -> tuple[bool, set[str]]:
    field = criterion["field"]
    value = criterion["value"]
    if field == "source_ref_id":
        return source["source_ref_id"].casefold() == value, set()
    if field == "media_type":
        return source["media_type"].casefold() == value, set()
    if field == "provider_id":
        return source["provider_id"].casefold() == value, set()
    if field == "route_profile":
        return source["route_profile"].casefold() == value, set()

    matched: set[str] = set()
    for unit in source["units"]:
        if field == "extracted_text":
            observed = unit["surface"]
            ok = isinstance(observed, str) and value in observed.casefold()
        elif field == "semantic_type":
            observed = unit["semantic_type"]
            ok = isinstance(observed, str) and observed.casefold() == value
        elif field == "resource":
            observed = unit["resource"]
            ok = isinstance(observed, str) and observed.casefold() == value
        else:
            raise SearchContractError(f"unsupported-filter-field:{field}")
        if ok:
            matched.add(unit["unit_id"])
    return bool(matched), matched


def _sort_value(source: dict[str, Any], field: str) -> Any:
    if field == "source_ref_id":
        return source["source_ref_id"].casefold()
    if field == "media_type":
        return source["media_type"].casefold()
    if field == "unit_count":
        return source["unit_count"]
    raise SearchContractError(f"unsupported-sort-field:{field}")


def stale_search_result(
    *,
    current_upstream_basis_fingerprint: str | None,
    index_upstream_basis_fingerprint: str | None,
    plan: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    normalized = normalize_query_plan(plan)
    return {
        "freshness": "stale",
        "current_upstream_basis_fingerprint": current_upstream_basis_fingerprint,
        "index_upstream_basis_fingerprint": index_upstream_basis_fingerprint,
        "normalized_plan": normalized,
        "source_ids": [],
        "hits": [],
        "blocked_reason": reason,
    }


def run_search(
    index: dict[str, Any],
    *,
    current_upstream_basis_fingerprint: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    validate_search_index(index)
    normalized = normalize_query_plan(plan)
    if index["upstream_basis_fingerprint"] != current_upstream_basis_fingerprint:
        return stale_search_result(
            current_upstream_basis_fingerprint=current_upstream_basis_fingerprint,
            index_upstream_basis_fingerprint=index["upstream_basis_fingerprint"],
            plan=normalized,
            reason="index-not-current",
        )

    matches: list[tuple[dict[str, Any], list[str]]] = []
    for source in index["sources"]:
        evidence: set[str] = set()
        for criterion in normalized["criteria"]:
            ok, refs = _source_criterion_match(source, criterion)
            if not ok:
                break
            evidence.update(refs)
        else:
            matches.append((source, sorted(evidence)))

    # Stable two-pass ordering gives an explicit ascending source-ref tie-breaker
    # even when the primary sort is descending.
    matches.sort(key=lambda item: item[0]["source_ref_id"].casefold())
    matches.sort(
        key=lambda item: _sort_value(item[0], normalized["sort_field"]),
        reverse=normalized["descending"],
    )
    hits = [
        {
            "source_ref_id": source["source_ref_id"],
            "matched_unit_refs": refs,
        }
        for source, refs in matches
    ]
    return {
        "freshness": "fresh",
        "current_upstream_basis_fingerprint": current_upstream_basis_fingerprint,
        "index_upstream_basis_fingerprint": index["upstream_basis_fingerprint"],
        "normalized_plan": normalized,
        "source_ids": [row["source_ref_id"] for row in hits],
        "hits": hits,
        "blocked_reason": None,
    }


def validate_view(value: Any) -> dict[str, Any]:
    view = _exact(
        value,
        {"view_version", "view_id", "plan", "projection"},
        "view",
    )
    _require(view["view_version"] == VIEW_VERSION, "view-version-unsupported")
    _opaque(view["view_id"], "view-id")
    view["plan"] = normalize_query_plan(view["plan"])
    projection = view["projection"]
    _require(
        isinstance(projection, list) and projection,
        "view-projection-required",
    )
    _require(
        len(projection) == len(set(projection)),
        "view-projection-duplicate",
    )
    for field in projection:
        _require(
            isinstance(field, str) and field,
            "view-projection-field-required",
        )
        _require(
            field not in FORBIDDEN_AUTHORITY_FIELDS,
            f"view-authority-field-forbidden:{field}",
        )
        _require(
            field in PROJECTION_FIELDS,
            f"unsupported-view-projection:{field}",
        )
    return view


def build_view(
    view_id: str,
    plan: dict[str, Any],
    projection: list[str],
) -> dict[str, Any]:
    value = {
        "view_version": VIEW_VERSION,
        "view_id": view_id,
        "plan": normalize_query_plan(plan),
        "projection": list(projection),
    }
    validate_view(value)
    return value


def validate_smart_collection(value: Any) -> dict[str, Any]:
    collection = _exact(
        value,
        {
            "collection_version",
            "collection_id",
            "rule",
            "current_members",
            "evaluated_upstream_basis_fingerprint",
            "evaluated_catalog_revision",
        },
        "smart-collection",
    )
    _require(
        collection["collection_version"] == SMART_COLLECTION_VERSION,
        "smart-collection-version-unsupported",
    )
    _opaque(collection["collection_id"], "smart-collection-id")
    collection["rule"] = normalize_query_plan(collection["rule"])
    members = collection["current_members"]
    _require(
        isinstance(members, list),
        "smart-collection-members-must-be-array",
    )
    _require(
        len(members) == len(set(members)),
        "smart-collection-members-duplicate",
    )
    for member in members:
        _opaque(member, "smart-collection-member")
    _require(
        members == sorted(members),
        "smart-collection-members-not-canonical-order",
    )
    _require(
        _valid_sha256(collection["evaluated_upstream_basis_fingerprint"]),
        "smart-collection-evaluated-basis-invalid",
    )
    _require(
        isinstance(collection["evaluated_catalog_revision"], int)
        and not isinstance(collection["evaluated_catalog_revision"], bool)
        and collection["evaluated_catalog_revision"] >= 1,
        "smart-collection-evaluated-revision-invalid",
    )
    return collection


def build_smart_collection(
    collection_id: str,
    rule: dict[str, Any],
    *,
    current_members: list[str],
    evaluated_upstream_basis_fingerprint: str,
    evaluated_catalog_revision: int,
) -> dict[str, Any]:
    value = {
        "collection_version": SMART_COLLECTION_VERSION,
        "collection_id": collection_id,
        "rule": normalize_query_plan(rule),
        "current_members": sorted(current_members),
        "evaluated_upstream_basis_fingerprint": evaluated_upstream_basis_fingerprint,
        "evaluated_catalog_revision": evaluated_catalog_revision,
    }
    validate_smart_collection(value)
    return value
