#!/usr/bin/env python3
"""First executable Raiatea Application Layer read facade.

This module intentionally sits above the accepted VS1/PDF product records.  It
composes catalog, search and extraction truth into small frontend-oriented read
models without making prototype storage records a public GUI contract.

The facade has no transport dependency: a future desktop IPC, HTTP or other UI
adapter can consume the same read models.  Extraction is hidden behind the
``ExtractionReader`` protocol so the current in-repository product state can be
replaced later by a Source Plane client without changing GUI semantics.
"""
from __future__ import annotations

from copy import deepcopy
import base64
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Protocol

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.extraction_service import validate_vs1d_state
from prototype.p0_vs1.pdf1b_product_service import validate_pdf1b_state
from prototype.p0_vs1.reconciliation import validate_state as validate_vs1b_state
from prototype.p0_vs1.search_service import (
    SearchServiceError,
    SearchViewService,
    current_upstream_basis_fingerprint,
)
from prototype.p0_vs1.source_contract import (
    EPUB_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    validate_source_reference,
)
from prototype.p0_vs1.source_service import validate_vs1c_state


CURSOR_PREFIX = "raiatea-cursor:"
MAX_PAGE_SIZE = 200


class ApplicationFacadeError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ApplicationFacadeError(message)


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ApplicationFacadeError("application-value-not-canonical-json") from exc


def _basis_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _encode_cursor(kind: str, basis: str, offset: int) -> str:
    payload = {"v": 1, "kind": kind, "basis": basis, "offset": offset}
    raw = base64.urlsafe_b64encode(_canonical_bytes(payload)).decode("ascii").rstrip("=")
    return CURSOR_PREFIX + raw


def _decode_cursor(cursor: str, *, kind: str, basis: str) -> int:
    _require(isinstance(cursor, str) and cursor.startswith(CURSOR_PREFIX), "application-cursor-invalid")
    token = cursor[len(CURSOR_PREFIX) :]
    _require(bool(token), "application-cursor-invalid")
    try:
        padded = token + "=" * (-len(token) % 4)
        value = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApplicationFacadeError("application-cursor-invalid") from exc
    _require(
        isinstance(value, dict)
        and set(value) == {"v", "kind", "basis", "offset"}
        and value["v"] == 1,
        "application-cursor-invalid",
    )
    _require(value["kind"] == kind, "application-cursor-kind-mismatch")
    _require(value["basis"] == basis, "application-cursor-stale")
    offset = value["offset"]
    _require(
        isinstance(offset, int) and not isinstance(offset, bool) and offset >= 0,
        "application-cursor-offset-invalid",
    )
    return offset


def _page(
    rows: list[Any],
    *,
    page_size: int,
    cursor: str | None,
    kind: str,
    basis: str,
) -> tuple[list[Any], str | None]:
    _require(
        isinstance(page_size, int)
        and not isinstance(page_size, bool)
        and 1 <= page_size <= MAX_PAGE_SIZE,
        "application-page-size-invalid",
    )
    offset = 0 if cursor is None else _decode_cursor(cursor, kind=kind, basis=basis)
    _require(offset <= len(rows), "application-cursor-offset-out-of-range")
    end = min(len(rows), offset + page_size)
    next_cursor = None if end >= len(rows) else _encode_cursor(kind, basis, end)
    return rows[offset:end], next_cursor


def _safe_relative_location(value: Any) -> str | None:
    if value is None:
        return None
    _require(isinstance(value, str) and value, "application-location-invalid")
    _require("\\" not in value, "application-location-not-normalized")
    path = PurePosixPath(value)
    _require(not path.is_absolute(), "application-absolute-location-forbidden")
    _require(".." not in path.parts and "." not in path.parts, "application-relative-location-invalid")
    _require(not value.startswith("~"), "application-relative-location-invalid")
    return value


def _item_ref(entry_id: str) -> str:
    digest = hashlib.sha256(entry_id.encode("utf-8")).hexdigest()
    return "app-item:" + digest


def _fallback_name(location: str | None, entry_id: str) -> str:
    if location:
        name = PurePosixPath(location).name
        if name:
            return name
    return entry_id


def _populated_value(envelope: Any) -> Any:
    if not isinstance(envelope, dict) or envelope.get("value_state") != "populated":
        return None
    return envelope.get("value")


def _public_envelope(envelope: Any) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        return {"state": "unavailable"}
    state = envelope.get("evidence_state")
    value_state = envelope.get("value_state")
    result: dict[str, Any] = {
        "state": state if isinstance(state, str) else "unavailable",
    }
    if isinstance(value_state, str):
        result["value_state"] = value_state
    if value_state == "populated" and "value" in envelope:
        result["value"] = deepcopy(envelope["value"])
    return result


def _record_by_kind(row: dict[str, Any], kind: str) -> dict[str, Any]:
    refs = row.get("record_refs")
    records = row.get("records")
    _require(isinstance(refs, list) and isinstance(records, dict), "application-extraction-records-invalid")
    matches = [
        records.get(ref.get("ref_id"))
        for ref in refs
        if isinstance(ref, dict) and ref.get("record_kind") == kind
    ]
    matches = [item for item in matches if isinstance(item, dict)]
    _require(len(matches) == 1, f"application-{kind}-count-invalid")
    return matches[0]


def _provider_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    provider = evidence.get("provider")
    route = evidence.get("route_profile")
    result: dict[str, Any] = {}
    if isinstance(provider, dict):
        for key in ("provider_id", "version", "provider_version"):
            value = provider.get(key)
            if isinstance(value, str) and value:
                result[key] = value
    if isinstance(route, dict):
        value = route.get("route_profile_id")
        if isinstance(value, str) and value:
            result["route_profile"] = value
    return result


def _rights_summary(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    result: dict[str, Any] = {}
    for key in (
        "decision_id",
        "disposition",
        "processing_disposition",
        "rights_evidence_state",
        "execution_class",
    ):
        observed = value.get(key)
        if isinstance(observed, (str, bool, int)) and not isinstance(observed, float):
            result[key] = observed
    return result or None


def _run_summary(run: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ("processing_run_id", "run_id"):
        value = run.get(key)
        if isinstance(value, str) and value:
            result["run_id"] = value
            break
    outcome = run.get("outcome")
    if isinstance(outcome, dict):
        result["outcome"] = {
            key: deepcopy(value)
            for key, value in outcome.items()
            if key in {"execution", "result", "status"}
        }
    diagnostics = run.get("diagnostics")
    if isinstance(diagnostics, list):
        result["diagnostic_count"] = len(diagnostics)
    return result


def _representation_summary(representation: dict[str, Any]) -> dict[str, Any]:
    representation_id = representation.get("representation_id")
    _require(
        isinstance(representation_id, str) and representation_id,
        "application-representation-id-required",
    )
    units = representation.get("units")
    _require(isinstance(units, list), "application-representation-units-required")
    coordinate_families: set[str] = set()
    evidence_state_by_family: dict[str, set[str]] = {
        "surface": set(),
        "semantic_role": set(),
        "coordinate": set(),
    }
    for unit in units:
        if not isinstance(unit, dict):
            continue
        for family in evidence_state_by_family:
            envelope = unit.get(family)
            if isinstance(envelope, dict) and isinstance(envelope.get("evidence_state"), str):
                evidence_state_by_family[family].add(envelope["evidence_state"])
        coordinate = _populated_value(unit.get("coordinate"))
        if isinstance(coordinate, dict) and isinstance(coordinate.get("kind"), str):
            coordinate_families.add(coordinate["kind"])
    return {
        "representation_id": representation_id,
        "unit_count": len(units),
        "coordinate_families": sorted(coordinate_families),
        "evidence_state_by_family": {
            family: sorted(states)
            for family, states in evidence_state_by_family.items()
        },
    }


def _public_unit(unit: Any) -> dict[str, Any]:
    _require(isinstance(unit, dict), "application-content-unit-invalid")
    unit_id = unit.get("unit_id")
    _require(isinstance(unit_id, str) and unit_id, "application-content-unit-id-required")
    return {
        "unit_ref": unit_id,
        "surface": _public_envelope(unit.get("surface")),
        "semantic_role": _public_envelope(unit.get("semantic_role")),
        "coordinate": _public_envelope(unit.get("coordinate")),
    }


def _extraction_summary(row: dict[str, Any], *, state_family: str) -> dict[str, Any]:
    representation = _record_by_kind(row, "NormalizedRepresentationRecord")
    evidence = _record_by_kind(row, "ProviderEvidenceRecord")
    run = _record_by_kind(row, "ProcessingRunRecord")
    provider = _provider_summary(evidence)
    plugin = row.get("plugin") if isinstance(row.get("plugin"), dict) else {}
    provenance_summary: dict[str, Any] = {}
    for key in ("plugin_id", "plugin_version", "route_profile"):
        value = plugin.get(key)
        if isinstance(value, str) and value:
            provenance_summary[key] = value
    provenance_summary.update(provider)
    representation_summary = _representation_summary(representation)
    return {
        "state": "current",
        "state_family": state_family,
        "source_ref_id": row["source_ref_id"],
        "provider": provider,
        "run": _run_summary(run),
        "representation": representation_summary,
        "rights": _rights_summary(row.get("rights_decision")),
        "provenance": provenance_summary,
        "warning_count": 0,
    }


class ExtractionReader(Protocol):
    """Application-facing extraction seam; a Source Plane client can implement it."""

    def current_summaries(
        self,
        snapshot: Any,
        source_refs: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        ...

    def representation_page(
        self,
        snapshot: Any,
        representation_id: str,
        *,
        page_size: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        ...


class InRepoExtractionReader:
    """Temporary adapter over current VS1d EPUB and PDF1b persisted product state."""

    @staticmethod
    def _current_rows(snapshot: Any) -> list[tuple[str, dict[str, Any]]]:
        payload = getattr(snapshot, "payload", None)
        _require(isinstance(payload, dict), "application-catalog-payload-invalid")
        scope_id = None
        vs1b = payload.get("vs1b")
        if isinstance(vs1b, dict):
            scope_id = vs1b.get("scope_ref")
        _require(isinstance(scope_id, str) and scope_id, "application-scope-ref-required")

        rows: list[tuple[str, dict[str, Any]]] = []
        vs1d = payload.get("vs1d")
        if vs1d is not None:
            validate_vs1d_state(vs1d, scope_id)
            rows.extend(("vs1d-epub", row) for row in vs1d["extractions"])
        pdf1b = payload.get("pdf1b")
        if pdf1b is not None:
            validate_pdf1b_state(pdf1b, scope_id)
            rows.extend(("pdf1b-poppler", row) for row in pdf1b["current_extractions"])
        return rows

    def current_summaries(
        self,
        snapshot: Any,
        source_refs: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        requested = {row["source_ref_id"] for row in source_refs}
        result: dict[str, dict[str, Any]] = {}
        for state_family, row in self._current_rows(snapshot):
            source_ref_id = row.get("source_ref_id")
            if source_ref_id not in requested:
                continue
            _require(source_ref_id not in result, "application-current-extraction-duplicate")
            result[source_ref_id] = _extraction_summary(row, state_family=state_family)
        return result

    def representation_page(
        self,
        snapshot: Any,
        representation_id: str,
        *,
        page_size: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        _require(
            isinstance(representation_id, str) and representation_id,
            "application-representation-id-required",
        )
        matches: list[dict[str, Any]] = []
        for _, row in self._current_rows(snapshot):
            representation = _record_by_kind(row, "NormalizedRepresentationRecord")
            if representation.get("representation_id") == representation_id:
                matches.append(representation)
        _require(len(matches) == 1, "application-representation-not-found")
        representation = matches[0]
        units = representation.get("units")
        _require(isinstance(units, list), "application-representation-units-required")
        unit_ids = [
            unit.get("unit_id") if isinstance(unit, dict) else None
            for unit in units
        ]
        basis = _basis_ref({"representation_id": representation_id, "unit_ids": unit_ids})
        selected, next_cursor = _page(
            units,
            page_size=page_size,
            cursor=cursor,
            kind="representation",
            basis=basis,
        )
        return {
            "representation_id": representation_id,
            "basis": basis,
            "cursor": cursor,
            "next_cursor": next_cursor,
            "units": [_public_unit(unit) for unit in selected],
        }


class RaiateaApplicationFacade:
    """Read-only application facade for the first executable GUI vertical slice."""

    def __init__(
        self,
        store: CatalogStateStore,
        scope_id: str,
        *,
        extraction_reader: ExtractionReader | None = None,
        search_service: SearchViewService | None = None,
    ) -> None:
        self._store = store
        self._scope_id = scope_id
        self._extractions = extraction_reader or InRepoExtractionReader()
        self._search = search_service or SearchViewService(store, scope_id)

    def _load(self) -> Any:
        snapshot = self._store.load()
        _require(snapshot is not None, "application-catalog-required")
        _require(isinstance(snapshot.payload, dict), "application-catalog-payload-invalid")
        vs1b = snapshot.payload.get("vs1b")
        _require(isinstance(vs1b, dict), "application-vs1b-state-required")
        try:
            validate_vs1b_state(vs1b, self._scope_id)
        except Exception as exc:
            raise ApplicationFacadeError(f"application-vs1b-state-invalid:{exc}") from exc
        return snapshot

    def _catalog_projection(
        self,
        snapshot: Any,
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        payload = snapshot.payload
        vs1b = payload["vs1b"]
        entries = [
            row
            for row in vs1b["entries"]
            if isinstance(row, dict) and row.get("superseded_by") is None
        ]
        entries.sort(key=lambda row: row["entry_id"])
        entries_by_stored = {row["stored_instance_id"]: row for row in entries}

        current_source_refs: dict[str, dict[str, Any]] = {}
        vs1c = payload.get("vs1c")
        if vs1c is not None:
            try:
                validate_vs1c_state(vs1c, self._scope_id)
            except Exception as exc:
                raise ApplicationFacadeError(f"application-vs1c-state-invalid:{exc}") from exc
            for raw in vs1c["source_references"]:
                source = validate_source_reference(raw)
                entry = entries_by_stored.get(source["stored_instance_ref"])
                if entry is None or entry.get("availability") != "known-present":
                    continue
                if any(
                    source[source_key] != entry[entry_key]
                    for source_key, entry_key in (
                        ("catalog_entry_ref", "entry_id"),
                        ("logical_candidate_ref", "logical_candidate_id"),
                        ("fingerprint", "fingerprint"),
                        ("byte_length", "byte_length"),
                        ("media_type", "media_type"),
                    )
                ):
                    continue
                current_source_refs[source["stored_instance_ref"]] = source

        refs = list(current_source_refs.values())
        extraction_summaries = self._extractions.current_summaries(snapshot, refs)
        return entries, current_source_refs, extraction_summaries

    def _library_item(
        self,
        entry: dict[str, Any],
        source_ref: dict[str, Any] | None,
        extraction: dict[str, Any] | None,
        *,
        catalog_freshness: str,
    ) -> dict[str, Any]:
        location = _safe_relative_location(entry.get("current_location"))
        media_type = entry.get("media_type")
        _require(isinstance(media_type, str) and media_type, "application-media-type-invalid")
        capabilities = ["view-history"]
        if entry.get("availability") == "known-present":
            capabilities.append("view-original")
        if source_ref is not None and catalog_freshness == "fresh":
            capabilities.append("request-extraction")
        if extraction is not None:
            capabilities.extend(["view-semantic", "view-provider-evidence", "view-processing", "view-provenance"])

        extraction_model: dict[str, Any] = {"state": "not-extracted"}
        if extraction is not None:
            extraction_model = {
                "state": "current",
                "current_representation_id": extraction["representation"]["representation_id"],
                "provider_profile_summary": deepcopy(extraction["provider"]),
            }

        return {
            "item_ref": _item_ref(entry["entry_id"]),
            "catalog_entry_ref": entry["entry_id"],
            "source_ref_id": None if source_ref is None else source_ref["source_ref_id"],
            "logical_candidate_ref": entry["logical_candidate_id"],
            "stored_instance_ref": entry["stored_instance_id"],
            "display": {
                "title": None,
                "fallback_name": _fallback_name(location, entry["entry_id"]),
                "media_type": media_type,
                "kind": "document-source",
            },
            "location": {
                "scope_ref": self._scope_id,
                "current_relative_location": location,
                "availability": entry["availability"],
                "history_count": len(entry.get("location_history", [])),
            },
            "content": {
                "byte_length": entry.get("byte_length"),
                "fingerprint_summary": entry.get("fingerprint"),
            },
            "extraction": extraction_model,
            "freshness": {
                "catalog": catalog_freshness,
                "content": "current" if source_ref is not None else "not-established",
            },
            "warnings": {"count": 0, "highest_severity": None},
            "capabilities": capabilities,
        }

    @staticmethod
    def _catalog_basis(entries: list[dict[str, Any]], freshness: dict[str, Any]) -> str:
        basis = {
            "freshness": freshness,
            "entries": [
                {
                    "entry_id": row["entry_id"],
                    "logical_candidate_id": row["logical_candidate_id"],
                    "stored_instance_id": row["stored_instance_id"],
                    "current_location": row.get("current_location"),
                    "availability": row.get("availability"),
                    "fingerprint": row.get("fingerprint"),
                    "byte_length": row.get("byte_length"),
                    "media_type": row.get("media_type"),
                    "superseded_by": row.get("superseded_by"),
                }
                for row in entries
            ],
        }
        return _basis_ref(basis)

    def library_page(
        self,
        *,
        page_size: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        snapshot = self._load()
        entries, sources, extractions = self._catalog_projection(snapshot)
        freshness = snapshot.payload["vs1b"]["freshness"]
        freshness_status = freshness["status"]
        models = [
            self._library_item(
                entry,
                sources.get(entry["stored_instance_id"]),
                extractions.get(
                    sources[entry["stored_instance_id"]]["source_ref_id"]
                )
                if entry["stored_instance_id"] in sources
                else None,
                catalog_freshness=freshness_status,
            )
            for entry in entries
        ]
        basis = self._catalog_basis(entries, freshness)
        selected, next_cursor = _page(
            models,
            page_size=page_size,
            cursor=cursor,
            kind="library",
            basis=basis,
        )
        return {
            "catalog_freshness": freshness_status,
            "counts_basis": "current" if freshness_status == "fresh" else "last-known",
            "basis": basis,
            "total_known_items": len(models),
            "cursor": cursor,
            "next_cursor": next_cursor,
            "items": deepcopy(selected),
        }

    def source_detail(self, item_ref: str) -> dict[str, Any]:
        _require(isinstance(item_ref, str) and item_ref.startswith("app-item:"), "application-item-ref-invalid")
        snapshot = self._load()
        entries, sources, extractions = self._catalog_projection(snapshot)
        matches = [entry for entry in entries if _item_ref(entry["entry_id"]) == item_ref]
        _require(len(matches) == 1, "application-item-not-found")
        entry = matches[0]
        source = sources.get(entry["stored_instance_id"])
        extraction = None if source is None else extractions.get(source["source_ref_id"])
        freshness = snapshot.payload["vs1b"]["freshness"]["status"]
        item = self._library_item(
            entry,
            source,
            extraction,
            catalog_freshness=freshness,
        )

        panels = ["history"]
        if entry["availability"] == "known-present":
            panels.insert(0, "original")
        if extraction is not None:
            panels.extend(["semantic", "provider-evidence", "processing", "provenance"])

        actions: list[str] = []
        if source is not None and freshness == "fresh":
            actions.append("reprocess" if extraction is not None else "request-extraction")

        return {
            "item_ref": item_ref,
            "catalog_entry_ref": entry["entry_id"],
            "logical_candidate_ref": entry["logical_candidate_id"],
            "stored_instance_ref": entry["stored_instance_id"],
            "source_ref_id": None if source is None else source["source_ref_id"],
            "display": deepcopy(item["display"]),
            "locations": [deepcopy(item["location"])],
            "availability": entry["availability"],
            "media_type": entry["media_type"],
            "content_identity": deepcopy(item["content"]),
            "catalog_freshness": freshness,
            "current_extractions": [] if extraction is None else [deepcopy(extraction)],
            "representations": [] if extraction is None else [deepcopy(extraction["representation"])],
            "evidence_summaries": [] if extraction is None else [{"provider": deepcopy(extraction["provider"])}],
            "processing_runs": [] if extraction is None else [deepcopy(extraction["run"])],
            "provenance_summary": None if extraction is None else deepcopy(extraction["provenance"]),
            "rights_summary": None if extraction is None else deepcopy(extraction["rights"]),
            "warnings": [] if extraction is None else ([{"count": extraction["warning_count"]}] if extraction["warning_count"] else []),
            "available_panels": panels,
            "available_actions": actions,
        }

    def representation_page(
        self,
        representation_id: str,
        *,
        page_size: int = 100,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        snapshot = self._load()
        return self._extractions.representation_page(
            snapshot,
            representation_id,
            page_size=page_size,
            cursor=cursor,
        )

    def _library_items_by_source(
        self,
        snapshot: Any,
    ) -> dict[str, dict[str, Any]]:
        entries, sources, extractions = self._catalog_projection(snapshot)
        freshness = snapshot.payload["vs1b"]["freshness"]["status"]
        result: dict[str, dict[str, Any]] = {}
        for entry in entries:
            source = sources.get(entry["stored_instance_id"])
            if source is None:
                continue
            result[source["source_ref_id"]] = self._library_item(
                entry,
                source,
                extractions.get(source["source_ref_id"]),
                catalog_freshness=freshness,
            )
        return result

    def search_page(
        self,
        plan: dict[str, Any],
        *,
        page_size: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        result = self._search.search(plan)
        normalized_plan = deepcopy(result.get("normalized_plan", plan))
        if result.get("freshness") != "fresh":
            return {
                "freshness": "stale",
                "blocked_reason": result.get("blocked_reason", "index-not-current"),
                "interpreted_plan": normalized_plan,
                "total_known_matches": None,
                "cursor": None,
                "next_cursor": None,
                "items": [],
            }

        snapshot = self._load()
        try:
            current_basis = current_upstream_basis_fingerprint(snapshot, self._scope_id)
        except SearchServiceError:
            return {
                "freshness": "stale",
                "blocked_reason": "upstream-not-current",
                "interpreted_plan": normalized_plan,
                "total_known_matches": None,
                "cursor": None,
                "next_cursor": None,
                "items": [],
            }
        result_basis = result.get("current_upstream_basis_fingerprint")
        if result_basis != current_basis:
            return {
                "freshness": "stale",
                "blocked_reason": "application-composition-basis-changed",
                "interpreted_plan": normalized_plan,
                "total_known_matches": None,
                "cursor": None,
                "next_cursor": None,
                "items": [],
            }

        by_source = self._library_items_by_source(snapshot)
        source_ids = result.get("source_ids")
        _require(isinstance(source_ids, list), "application-search-source-ids-invalid")
        if any(source_id not in by_source for source_id in source_ids):
            return {
                "freshness": "stale",
                "blocked_reason": "application-search-catalog-mismatch",
                "interpreted_plan": normalized_plan,
                "total_known_matches": None,
                "cursor": None,
                "next_cursor": None,
                "items": [],
            }

        hits = result.get("hits") if isinstance(result.get("hits"), list) else []
        hit_by_source = {
            hit.get("source_ref_id"): hit
            for hit in hits
            if isinstance(hit, dict) and isinstance(hit.get("source_ref_id"), str)
        }
        rows = [
            {
                "item": deepcopy(by_source[source_id]),
                "matched_content_refs": deepcopy(
                    hit_by_source.get(source_id, {}).get("matched_unit_refs", [])
                ),
                "match_snippets": [],
            }
            for source_id in source_ids
        ]
        basis = _basis_ref(
            {
                "upstream": current_basis,
                "plan": normalized_plan,
                "source_ids": source_ids,
            }
        )
        selected, next_cursor = _page(
            rows,
            page_size=page_size,
            cursor=cursor,
            kind="search",
            basis=basis,
        )
        return {
            "freshness": "fresh",
            "blocked_reason": None,
            "interpreted_plan": normalized_plan,
            "total_known_matches": len(rows),
            "cursor": cursor,
            "next_cursor": next_cursor,
            "items": selected,
        }


__all__ = [
    "ApplicationFacadeError",
    "ExtractionReader",
    "InRepoExtractionReader",
    "RaiateaApplicationFacade",
]
