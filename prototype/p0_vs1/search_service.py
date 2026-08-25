#!/usr/bin/env python3
"""VS1e Core-owned search index, View and Smart Collection service."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from prototype.p0_vs1.catalog_store import CatalogStateStore, CatalogStoreError
from prototype.p0_vs1.extraction_service import validate_vs1d_state
from prototype.p0_vs1.reconciliation import validate_state as validate_vs1b_state
from prototype.p0_vs1.search_contract import (
    SEARCH_INDEX_VERSION,
    SMART_COLLECTION_VERSION,
    VIEW_VERSION,
    SearchContractError,
    build_smart_collection,
    build_view,
    canonical_json_bytes,
    normalize_query_plan,
    run_search,
    sha256_ref,
    stale_search_result,
    validate_index_source,
    validate_search_index,
    validate_smart_collection,
    validate_view,
)
from prototype.p0_vs1.source_contract import validate_source_reference
from prototype.p0_vs1.source_service import validate_vs1c_state


VS1E_STATE_VERSION = "raiatea.vs1e.search-state.0.1.0"


class SearchServiceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SearchServiceError(message)


def _populated_value(envelope: Any) -> Any:
    if not isinstance(envelope, dict) or envelope.get("value_state") != "populated":
        return None
    return envelope.get("value")


def _record_by_kind(extraction: dict[str, Any], kind: str) -> dict[str, Any]:
    matches = [
        extraction["records"][ref["ref_id"]]
        for ref in extraction["record_refs"]
        if ref.get("record_kind") == kind
    ]
    _require(len(matches) == 1, f"search-upstream-{kind}-count-invalid")
    _require(isinstance(matches[0], dict), f"search-upstream-{kind}-invalid")
    return matches[0]


def _canonical_index_unit(raw: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(raw, dict), "search-upstream-unit-invalid")
    unit_id = raw.get("unit_id")
    _require(isinstance(unit_id, str) and unit_id, "search-upstream-unit-id-required")

    surface_value = _populated_value(raw.get("surface"))
    surface = surface_value if isinstance(surface_value, str) else None

    semantic_value = _populated_value(raw.get("semantic_role"))
    semantic_type = (
        semantic_value.get("type")
        if isinstance(semantic_value, dict) and isinstance(semantic_value.get("type"), str)
        else None
    )

    coordinate_value = _populated_value(raw.get("coordinate"))
    resource: str | None = None
    fragment: str | None = None
    spine_index: int | None = None
    if isinstance(coordinate_value, dict):
        _require(
            coordinate_value.get("kind") == "epub-logical",
            "search-upstream-coordinate-kind-invalid",
        )
        observed_resource = coordinate_value.get("resource")
        _require(
            isinstance(observed_resource, str) and observed_resource,
            "search-upstream-resource-required",
        )
        resource = observed_resource
        observed_fragment = coordinate_value.get("fragment")
        _require(
            observed_fragment is None or isinstance(observed_fragment, str),
            "search-upstream-fragment-invalid",
        )
        fragment = observed_fragment
        observed_spine = coordinate_value.get("spine_index")
        _require(
            observed_spine is None
            or (
                isinstance(observed_spine, int)
                and not isinstance(observed_spine, bool)
                and observed_spine >= 0
            ),
            "search-upstream-spine-index-invalid",
        )
        spine_index = observed_spine

    return {
        "unit_id": unit_id,
        "surface": surface,
        "semantic_type": semantic_type,
        "resource": resource,
        "fragment": fragment,
        "spine_index": spine_index,
    }


def _current_upstream_projection(
    catalog_snapshot: Any,
    scope_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    _require(catalog_snapshot is not None, "search-catalog-required")
    revision = getattr(catalog_snapshot, "revision", None)
    payload = getattr(catalog_snapshot, "payload", None)
    _require(
        isinstance(revision, int) and not isinstance(revision, bool) and revision >= 1,
        "search-catalog-revision-invalid",
    )
    _require(isinstance(payload, dict), "search-catalog-payload-invalid")
    vs1b = payload.get("vs1b")
    vs1c = payload.get("vs1c")
    vs1d = payload.get("vs1d")
    _require(isinstance(vs1b, dict), "search-vs1b-state-required")
    _require(isinstance(vs1c, dict), "search-vs1c-state-required")
    _require(isinstance(vs1d, dict), "search-vs1d-state-required")
    try:
        validate_vs1b_state(vs1b, scope_id)
        validate_vs1c_state(vs1c, scope_id)
        validate_vs1d_state(vs1d, scope_id)
    except Exception as exc:
        raise SearchServiceError(f"search-upstream-state-invalid:{exc}") from exc
    _require(vs1b["freshness"]["status"] == "fresh", "search-upstream-not-fresh")

    current_entries: dict[str, dict[str, Any]] = {}
    entry_basis: list[dict[str, Any]] = []
    for entry in vs1b["entries"]:
        if entry.get("superseded_by") is not None:
            continue
        if entry.get("availability") != "known-present":
            continue
        _require(
            entry.get("reconciliation_status") == "verified-by-inventory",
            "search-upstream-entry-not-verified",
        )
        stored = entry["stored_instance_id"]
        _require(stored not in current_entries, "search-upstream-stored-instance-duplicate")
        current_entries[stored] = entry
        entry_basis.append(
            {
                "entry_id": entry["entry_id"],
                "logical_candidate_id": entry["logical_candidate_id"],
                "stored_instance_id": stored,
                "current_location": entry["current_location"],
                "fingerprint": entry["fingerprint"],
                "byte_length": entry["byte_length"],
                "media_type": entry["media_type"],
                "availability": entry["availability"],
                "reconciliation_status": entry["reconciliation_status"],
            }
        )
    entry_basis.sort(key=lambda row: row["entry_id"])

    source_refs: dict[str, dict[str, Any]] = {}
    source_basis: list[dict[str, Any]] = []
    for raw in vs1c["source_references"]:
        source = validate_source_reference(raw)
        source_ref_id = source["source_ref_id"]
        _require(source_ref_id not in source_refs, "search-upstream-source-ref-duplicate")
        entry = current_entries.get(source["stored_instance_ref"])
        _require(entry is not None, "search-upstream-source-not-current")
        _require(
            source["catalog_entry_ref"] == entry["entry_id"]
            and source["logical_candidate_ref"] == entry["logical_candidate_id"]
            and source["fingerprint"] == entry["fingerprint"]
            and source["byte_length"] == entry["byte_length"]
            and source["media_type"] == entry["media_type"],
            "search-upstream-source-entry-mismatch",
        )
        source_refs[source_ref_id] = source
        source_basis.append(deepcopy(source))
    source_basis.sort(key=lambda row: row["source_ref_id"])

    index_sources: list[dict[str, Any]] = []
    extraction_basis: list[dict[str, Any]] = []
    seen_extractions: set[str] = set()
    for extraction in vs1d["extractions"]:
        source_ref_id = extraction["source_ref_id"]
        _require(source_ref_id not in seen_extractions, "search-upstream-extraction-duplicate")
        seen_extractions.add(source_ref_id)
        source = source_refs.get(source_ref_id)
        _require(source is not None, "search-upstream-extraction-source-not-current")
        _require(
            extraction["source_fingerprint"] == source["fingerprint"],
            "search-upstream-extraction-fingerprint-mismatch",
        )

        representation = _record_by_kind(extraction, "NormalizedRepresentationRecord")
        evidence = _record_by_kind(extraction, "ProviderEvidenceRecord")
        run = _record_by_kind(extraction, "ProcessingRunRecord")
        _require(
            representation.get("source_ref", {}).get("source_id") == source_ref_id
            and representation.get("source_ref", {}).get("fingerprint") == source["fingerprint"],
            "search-upstream-representation-source-mismatch",
        )
        _require(
            run.get("outcome", {}).get("execution") == "completed",
            "search-upstream-run-not-completed",
        )
        provider = evidence.get("provider")
        route = evidence.get("route_profile")
        _require(
            isinstance(provider, dict)
            and isinstance(provider.get("provider_id"), str)
            and provider["provider_id"],
            "search-upstream-provider-required",
        )
        _require(
            isinstance(route, dict)
            and isinstance(route.get("route_profile_id"), str)
            and route["route_profile_id"],
            "search-upstream-route-required",
        )
        units_raw = representation.get("units")
        _require(isinstance(units_raw, list), "search-upstream-units-required")
        units = [_canonical_index_unit(row) for row in units_raw]
        units.sort(key=lambda row: row["unit_id"])
        representation_id = representation.get("representation_id")
        _require(
            isinstance(representation_id, str) and representation_id,
            "search-upstream-representation-id-required",
        )
        indexed = {
            "source_ref_id": source_ref_id,
            "logical_candidate_ref": source["logical_candidate_ref"],
            "stored_instance_ref": source["stored_instance_ref"],
            "media_type": source["media_type"],
            "fingerprint": source["fingerprint"],
            "representation_id": representation_id,
            "provider_id": provider["provider_id"],
            "route_profile": route["route_profile_id"],
            "unit_count": len(units),
            "units": units,
        }
        validate_index_source(indexed)
        index_sources.append(indexed)
        extraction_basis.append(
            {
                "source_ref_id": source_ref_id,
                "source_fingerprint": extraction["source_fingerprint"],
                "rights_decision_id": extraction["rights_decision"]["decision_id"],
                "plugin_id": extraction["plugin"]["plugin_id"],
                "plugin_version": extraction["plugin"]["plugin_version"],
                "manifest_fingerprint": extraction["plugin"]["manifest_fingerprint"],
                "provider_id": provider["provider_id"],
                "route_profile": route["route_profile_id"],
                "representation_id": representation_id,
                "units": units,
            }
        )
    index_sources.sort(key=lambda row: row["source_ref_id"])
    extraction_basis.sort(key=lambda row: row["source_ref_id"])

    basis = {
        "scope_ref": scope_id,
        "vs1b_freshness": "fresh",
        "current_entries": entry_basis,
        "source_references": source_basis,
        "current_extractions": extraction_basis,
    }
    canonical_json_bytes(basis)
    return basis, index_sources


def current_upstream_basis_fingerprint(catalog_snapshot: Any, scope_id: str) -> str:
    basis, _ = _current_upstream_projection(catalog_snapshot, scope_id)
    return sha256_ref(basis)


def build_search_index(catalog_snapshot: Any, scope_id: str) -> dict[str, Any]:
    basis, sources = _current_upstream_projection(catalog_snapshot, scope_id)
    index = {
        "index_version": SEARCH_INDEX_VERSION,
        "scope_ref": scope_id,
        "built_from_catalog_revision": catalog_snapshot.revision,
        "upstream_basis_fingerprint": sha256_ref(basis),
        "sources": sources,
    }
    validate_search_index(index)
    return index


def validate_vs1e_state(value: Any, scope_id: str) -> dict[str, Any]:
    _require(isinstance(value, dict), "vs1e-state-must-be-object")
    _require(
        set(value) == {"state_version", "scope_ref", "index", "views", "smart_collections"},
        "vs1e-state-shape-invalid",
    )
    _require(value["state_version"] == VS1E_STATE_VERSION, "vs1e-state-version-unsupported")
    _require(value["scope_ref"] == scope_id, "vs1e-state-scope-mismatch")
    index = validate_search_index(value["index"])
    _require(index["scope_ref"] == scope_id, "vs1e-index-scope-mismatch")

    views = value["views"]
    _require(isinstance(views, list), "vs1e-views-must-be-array")
    view_ids: list[str] = []
    for raw in views:
        view = validate_view(raw)
        _require(view["view_id"] not in view_ids, "vs1e-view-id-duplicate")
        view_ids.append(view["view_id"])
    _require(view_ids == sorted(view_ids), "vs1e-views-not-canonical-order")

    collections = value["smart_collections"]
    _require(isinstance(collections, list), "vs1e-smart-collections-must-be-array")
    collection_ids: list[str] = []
    for raw in collections:
        collection = validate_smart_collection(raw)
        _require(
            collection["collection_id"] not in collection_ids,
            "vs1e-smart-collection-id-duplicate",
        )
        collection_ids.append(collection["collection_id"])
    _require(
        collection_ids == sorted(collection_ids),
        "vs1e-smart-collections-not-canonical-order",
    )
    return value


def _empty_or_prior_lists(payload: dict[str, Any], scope_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prior = payload.get("vs1e")
    if prior is None:
        return [], []
    validate_vs1e_state(prior, scope_id)
    return deepcopy(prior["views"]), deepcopy(prior["smart_collections"])


class SearchViewService:
    def __init__(self, store: CatalogStateStore, scope_id: str) -> None:
        self._store = store
        self._scope_id = scope_id

    def rebuild_index(self) -> dict[str, Any]:
        snapshot = self._store.load()
        _require(snapshot is not None, "search-catalog-required")
        index = build_search_index(snapshot, self._scope_id)
        payload = deepcopy(snapshot.payload)
        views, collections = _empty_or_prior_lists(payload, self._scope_id)
        payload["vs1e"] = {
            "state_version": VS1E_STATE_VERSION,
            "scope_ref": self._scope_id,
            "index": index,
            "views": views,
            "smart_collections": collections,
        }
        validate_vs1e_state(payload["vs1e"], self._scope_id)
        try:
            saved = self._store.save(payload, expected_revision=snapshot.revision)
        except CatalogStoreError as exc:
            raise SearchServiceError("search-index-catalog-changed-during-build") from exc
        return {
            "status": "completed",
            "catalog_revision": saved.revision,
            "built_from_catalog_revision": snapshot.revision,
            "upstream_basis_fingerprint": index["upstream_basis_fingerprint"],
            "source_count": len(index["sources"]),
        }

    def _load_vs1e(self) -> tuple[Any, dict[str, Any]]:
        snapshot = self._store.load()
        _require(snapshot is not None, "search-catalog-required")
        state = snapshot.payload.get("vs1e")
        _require(isinstance(state, dict), "search-index-not-built")
        validate_vs1e_state(state, self._scope_id)
        return snapshot, state

    def search(self, plan: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_query_plan(plan)
        try:
            snapshot, state = self._load_vs1e()
        except SearchServiceError:
            raise
        index = state["index"]
        try:
            current_basis = current_upstream_basis_fingerprint(snapshot, self._scope_id)
        except SearchServiceError:
            return stale_search_result(
                current_upstream_basis_fingerprint=None,
                index_upstream_basis_fingerprint=index["upstream_basis_fingerprint"],
                plan=normalized,
                reason="upstream-not-current",
            )
        return run_search(
            index,
            current_upstream_basis_fingerprint=current_basis,
            plan=normalized,
        )

    def save_view(
        self,
        view_id: str,
        plan: dict[str, Any],
        projection: list[str],
    ) -> dict[str, Any]:
        view = build_view(view_id, plan, projection)
        snapshot, state = self._load_vs1e()
        views = [deepcopy(row) for row in state["views"] if row["view_id"] != view_id]
        views.append(view)
        views.sort(key=lambda row: row["view_id"])
        payload = deepcopy(snapshot.payload)
        payload["vs1e"]["views"] = views
        validate_vs1e_state(payload["vs1e"], self._scope_id)
        try:
            saved = self._store.save(payload, expected_revision=snapshot.revision)
        except CatalogStoreError as exc:
            raise SearchServiceError("view-catalog-changed-during-save") from exc
        return {"status": "completed", "catalog_revision": saved.revision, "view_id": view_id}

    def evaluate_view(self, view_id: str) -> dict[str, Any]:
        snapshot, state = self._load_vs1e()
        matches = [row for row in state["views"] if row["view_id"] == view_id]
        _require(len(matches) == 1, "view-not-found")
        view = matches[0]
        result = self.search(view["plan"])
        _require(result["freshness"] == "fresh", "view-requires-fresh-index")
        by_id = {row["source_ref_id"]: row for row in state["index"]["sources"]}
        rows: list[dict[str, Any]] = []
        for source_id in result["source_ids"]:
            source = by_id[source_id]
            rows.append({field: source[field] for field in view["projection"]})
        return {
            "view_id": view_id,
            "freshness": "fresh",
            "upstream_basis_fingerprint": result["current_upstream_basis_fingerprint"],
            "source_ids": result["source_ids"],
            "projection": deepcopy(view["projection"]),
            "rows": rows,
        }

    def save_smart_collection(
        self,
        collection_id: str,
        rule: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = normalize_query_plan(rule)
        snapshot, state = self._load_vs1e()
        result = self.search(normalized)
        _require(
            result["freshness"] == "fresh",
            "smart-collection-requires-fresh-index",
        )
        collection = build_smart_collection(
            collection_id,
            normalized,
            current_members=result["source_ids"],
            evaluated_upstream_basis_fingerprint=result["current_upstream_basis_fingerprint"],
            evaluated_catalog_revision=snapshot.revision,
        )
        collections = [
            deepcopy(row)
            for row in state["smart_collections"]
            if row["collection_id"] != collection_id
        ]
        collections.append(collection)
        collections.sort(key=lambda row: row["collection_id"])
        payload = deepcopy(snapshot.payload)
        payload["vs1e"]["smart_collections"] = collections
        validate_vs1e_state(payload["vs1e"], self._scope_id)
        try:
            saved = self._store.save(payload, expected_revision=snapshot.revision)
        except CatalogStoreError as exc:
            raise SearchServiceError("smart-collection-catalog-changed-during-save") from exc
        return {
            "status": "completed",
            "catalog_revision": saved.revision,
            "collection_id": collection_id,
            "members": deepcopy(collection["current_members"]),
            "evaluated_upstream_basis_fingerprint": collection[
                "evaluated_upstream_basis_fingerprint"
            ],
        }

    def reevaluate_smart_collection(self, collection_id: str) -> dict[str, Any]:
        snapshot, state = self._load_vs1e()
        matches = [
            row for row in state["smart_collections"]
            if row["collection_id"] == collection_id
        ]
        _require(len(matches) == 1, "smart-collection-not-found")
        prior = matches[0]
        rule_bytes = canonical_json_bytes(prior["rule"])
        result = self.search(prior["rule"])
        _require(
            result["freshness"] == "fresh",
            "smart-collection-requires-fresh-index",
        )
        updated = build_smart_collection(
            collection_id,
            prior["rule"],
            current_members=result["source_ids"],
            evaluated_upstream_basis_fingerprint=result["current_upstream_basis_fingerprint"],
            evaluated_catalog_revision=snapshot.revision,
        )
        _require(
            canonical_json_bytes(updated["rule"]) == rule_bytes,
            "smart-collection-rule-mutated-during-evaluation",
        )
        collections = [
            deepcopy(row)
            for row in state["smart_collections"]
            if row["collection_id"] != collection_id
        ]
        collections.append(updated)
        collections.sort(key=lambda row: row["collection_id"])
        payload = deepcopy(snapshot.payload)
        payload["vs1e"]["smart_collections"] = collections
        validate_vs1e_state(payload["vs1e"], self._scope_id)
        try:
            saved = self._store.save(payload, expected_revision=snapshot.revision)
        except CatalogStoreError as exc:
            raise SearchServiceError(
                "smart-collection-catalog-changed-during-reevaluation"
            ) from exc
        return {
            "status": "completed",
            "catalog_revision": saved.revision,
            "collection_id": collection_id,
            "members": deepcopy(updated["current_members"]),
            "evaluated_upstream_basis_fingerprint": updated[
                "evaluated_upstream_basis_fingerprint"
            ],
        }
