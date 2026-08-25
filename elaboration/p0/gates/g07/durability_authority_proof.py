#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Iterable


PROOF_SCHEMA_VERSION = "g07-proof-catalog-0.1.0"
_ALLOWED_SCOPE_CAPABILITIES = frozenset({"observe", "read-for-processing"})
_MUTATION_CAPABILITIES = frozenset({"write", "move", "delete", "organize"})


class G07ProofError(ValueError):
    pass


@dataclass(frozen=True)
class LogicalItem:
    logical_id: str
    title: str


@dataclass(frozen=True)
class LocationRecord:
    location_id: str
    logical_id: str
    path: str
    availability: str


@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    logical_id: str
    observer: str
    source_ref: str


@dataclass(frozen=True)
class ViewRecord:
    view_id: str
    normalized_plan: tuple[tuple[str, str, str], ...]
    projection: tuple[str, ...]


@dataclass(frozen=True)
class SmartCollectionRuleRecord:
    collection_id: str
    normalized_plan: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class BoundedCatalogState:
    """Proof-only catalog state; not a production persistence schema."""

    catalog_revision: int
    logical_items: tuple[LogicalItem, ...]
    locations: tuple[LocationRecord, ...]
    provenance: tuple[ProvenanceRecord, ...]
    views: tuple[ViewRecord, ...]
    smart_collection_rules: tuple[SmartCollectionRuleRecord, ...]


@dataclass(frozen=True)
class ScopeGrant:
    """Core-created proof authority. External requests cannot construct its root."""

    scope_id: str
    root: str
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class CoreAuthorityConfig:
    scopes: tuple[ScopeGrant, ...]


@dataclass(frozen=True)
class ExternalRequest:
    """External/UI/API-shaped request deliberately has no root or secret field."""

    scope_id: str
    path: str
    capability: str


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    scope_id: str
    capability: str
    normalized_path: str | None
    reason: str


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise G07ProofError(f"{label}-required")
    return value


def _require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise G07ProofError(f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise G07ProofError(f"{label}-missing-field:{missing[0]}")
    if extra:
        raise G07ProofError(f"{label}-unknown-field:{extra[0]}")
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_plan(plan: tuple[tuple[str, str, str], ...], label: str) -> None:
    if not isinstance(plan, tuple):
        raise G07ProofError(f"{label}-must-be-tuple")
    for criterion in plan:
        if (
            not isinstance(criterion, tuple)
            or len(criterion) != 3
            or not all(isinstance(part, str) and part for part in criterion)
        ):
            raise G07ProofError(f"{label}-criterion-invalid")


def _state_to_payload(state: BoundedCatalogState) -> dict[str, Any]:
    if not isinstance(state.catalog_revision, int) or isinstance(state.catalog_revision, bool) or state.catalog_revision < 0:
        raise G07ProofError("catalog-revision-invalid")

    logical_items = []
    seen_logical_ids: set[str] = set()
    for item in sorted(state.logical_items, key=lambda row: row.logical_id):
        _require_text(item.logical_id, "logical-id")
        _require_text(item.title, "title")
        if item.logical_id in seen_logical_ids:
            raise G07ProofError("logical-id-duplicate")
        seen_logical_ids.add(item.logical_id)
        logical_items.append({"logical_id": item.logical_id, "title": item.title})

    locations = []
    seen_location_ids: set[str] = set()
    for location in sorted(state.locations, key=lambda row: row.location_id):
        _require_text(location.location_id, "location-id")
        _require_text(location.logical_id, "location-logical-id")
        _require_text(location.path, "location-path")
        if location.logical_id not in seen_logical_ids:
            raise G07ProofError("location-logical-id-unknown")
        if location.availability not in {
            "known-present",
            "unavailable-or-unknown",
            "confirmed-missing-at-location",
        }:
            raise G07ProofError("location-availability-invalid")
        if location.location_id in seen_location_ids:
            raise G07ProofError("location-id-duplicate")
        seen_location_ids.add(location.location_id)
        locations.append(
            {
                "availability": location.availability,
                "location_id": location.location_id,
                "logical_id": location.logical_id,
                "path": location.path,
            }
        )

    provenance = []
    seen_provenance_ids: set[str] = set()
    for record in sorted(state.provenance, key=lambda row: row.provenance_id):
        _require_text(record.provenance_id, "provenance-id")
        _require_text(record.logical_id, "provenance-logical-id")
        _require_text(record.observer, "observer")
        _require_text(record.source_ref, "source-ref")
        if record.logical_id not in seen_logical_ids:
            raise G07ProofError("provenance-logical-id-unknown")
        if record.provenance_id in seen_provenance_ids:
            raise G07ProofError("provenance-id-duplicate")
        seen_provenance_ids.add(record.provenance_id)
        provenance.append(
            {
                "logical_id": record.logical_id,
                "observer": record.observer,
                "provenance_id": record.provenance_id,
                "source_ref": record.source_ref,
            }
        )

    views = []
    seen_view_ids: set[str] = set()
    for view in sorted(state.views, key=lambda row: row.view_id):
        _require_text(view.view_id, "view-id")
        _validate_plan(view.normalized_plan, "view-plan")
        if not isinstance(view.projection, tuple) or not view.projection:
            raise G07ProofError("view-projection-invalid")
        if not all(isinstance(name, str) and name for name in view.projection):
            raise G07ProofError("view-projection-invalid")
        if view.view_id in seen_view_ids:
            raise G07ProofError("view-id-duplicate")
        seen_view_ids.add(view.view_id)
        views.append(
            {
                "normalized_plan": [list(item) for item in view.normalized_plan],
                "projection": list(view.projection),
                "view_id": view.view_id,
            }
        )

    rules = []
    seen_collection_ids: set[str] = set()
    for rule in sorted(state.smart_collection_rules, key=lambda row: row.collection_id):
        _require_text(rule.collection_id, "collection-id")
        _validate_plan(rule.normalized_plan, "smart-rule-plan")
        if rule.collection_id in seen_collection_ids:
            raise G07ProofError("collection-id-duplicate")
        seen_collection_ids.add(rule.collection_id)
        rules.append(
            {
                "collection_id": rule.collection_id,
                "normalized_plan": [list(item) for item in rule.normalized_plan],
            }
        )

    return {
        "catalog_revision": state.catalog_revision,
        "logical_items": logical_items,
        "locations": locations,
        "provenance": provenance,
        "smart_collection_rules": rules,
        "views": views,
    }


def export_catalog(state: BoundedCatalogState) -> bytes:
    payload = _state_to_payload(state)
    payload_bytes = _canonical_json_bytes(payload)
    envelope = {
        "payload": payload,
        "payload_sha256": _sha256(payload_bytes),
        "schema_version": PROOF_SCHEMA_VERSION,
    }
    return _canonical_json_bytes(envelope)


def _parse_plan(value: Any, label: str) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(value, list):
        raise G07ProofError(f"{label}-must-be-array")
    result = []
    for criterion in value:
        if (
            not isinstance(criterion, list)
            or len(criterion) != 3
            or not all(isinstance(part, str) and part for part in criterion)
        ):
            raise G07ProofError(f"{label}-criterion-invalid")
        result.append((criterion[0], criterion[1], criterion[2]))
    return tuple(result)


def restore_catalog(export_bytes: bytes) -> BoundedCatalogState:
    try:
        decoded = json.loads(export_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise G07ProofError("backup-invalid-json") from exc

    envelope = _require_exact_keys(
        decoded,
        {"payload", "payload_sha256", "schema_version"},
        "backup-envelope",
    )
    if envelope["schema_version"] != PROOF_SCHEMA_VERSION:
        raise G07ProofError("backup-schema-version-unsupported")
    expected_digest = _require_text(envelope["payload_sha256"], "payload-sha256")
    payload = _require_exact_keys(
        envelope["payload"],
        {
            "catalog_revision",
            "logical_items",
            "locations",
            "provenance",
            "smart_collection_rules",
            "views",
        },
        "catalog-payload",
    )
    actual_digest = _sha256(_canonical_json_bytes(payload))
    if actual_digest != expected_digest:
        raise G07ProofError("backup-integrity-mismatch")

    revision = payload["catalog_revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise G07ProofError("catalog-revision-invalid")

    def require_array(name: str) -> list[Any]:
        value = payload[name]
        if not isinstance(value, list):
            raise G07ProofError(f"{name}-must-be-array")
        return value

    logical_items = []
    for raw in require_array("logical_items"):
        row = _require_exact_keys(raw, {"logical_id", "title"}, "logical-item")
        logical_items.append(
            LogicalItem(
                logical_id=_require_text(row["logical_id"], "logical-id"),
                title=_require_text(row["title"], "title"),
            )
        )

    locations = []
    for raw in require_array("locations"):
        row = _require_exact_keys(
            raw,
            {"availability", "location_id", "logical_id", "path"},
            "location",
        )
        locations.append(
            LocationRecord(
                location_id=_require_text(row["location_id"], "location-id"),
                logical_id=_require_text(row["logical_id"], "location-logical-id"),
                path=_require_text(row["path"], "location-path"),
                availability=_require_text(row["availability"], "location-availability"),
            )
        )

    provenance = []
    for raw in require_array("provenance"):
        row = _require_exact_keys(
            raw,
            {"logical_id", "observer", "provenance_id", "source_ref"},
            "provenance",
        )
        provenance.append(
            ProvenanceRecord(
                provenance_id=_require_text(row["provenance_id"], "provenance-id"),
                logical_id=_require_text(row["logical_id"], "provenance-logical-id"),
                observer=_require_text(row["observer"], "observer"),
                source_ref=_require_text(row["source_ref"], "source-ref"),
            )
        )

    views = []
    for raw in require_array("views"):
        row = _require_exact_keys(raw, {"normalized_plan", "projection", "view_id"}, "view")
        projection = row["projection"]
        if not isinstance(projection, list) or not projection or not all(
            isinstance(name, str) and name for name in projection
        ):
            raise G07ProofError("view-projection-invalid")
        views.append(
            ViewRecord(
                view_id=_require_text(row["view_id"], "view-id"),
                normalized_plan=_parse_plan(row["normalized_plan"], "view-plan"),
                projection=tuple(projection),
            )
        )

    rules = []
    for raw in require_array("smart_collection_rules"):
        row = _require_exact_keys(raw, {"collection_id", "normalized_plan"}, "smart-rule")
        rules.append(
            SmartCollectionRuleRecord(
                collection_id=_require_text(row["collection_id"], "collection-id"),
                normalized_plan=_parse_plan(row["normalized_plan"], "smart-rule-plan"),
            )
        )

    state = BoundedCatalogState(
        catalog_revision=revision,
        logical_items=tuple(logical_items),
        locations=tuple(locations),
        provenance=tuple(provenance),
        views=tuple(views),
        smart_collection_rules=tuple(rules),
    )
    # Re-run all referential/duplicate/value validation and canonicalize the
    # ordering before the caller may accept restored state.
    canonical_payload = _state_to_payload(state)
    if canonical_payload != payload:
        raise G07ProofError("backup-payload-not-canonical")
    return state


def _canonical_absolute_path(value: str, label: str) -> PurePosixPath:
    text = _require_text(value, label)
    path = PurePosixPath(text)
    if not path.is_absolute():
        raise G07ProofError(f"{label}-must-be-absolute")
    if ".." in path.parts:
        raise G07ProofError(f"{label}-traversal-forbidden")
    return path


def create_core_scope(scope_id: str, root: str, capabilities: Iterable[str]) -> ScopeGrant:
    _require_text(scope_id, "scope-id")
    normalized_root = _canonical_absolute_path(root, "scope-root")
    normalized_capabilities = tuple(sorted(set(capabilities)))
    if not normalized_capabilities:
        raise G07ProofError("scope-capability-required")
    unsupported = sorted(set(normalized_capabilities) - _ALLOWED_SCOPE_CAPABILITIES)
    if unsupported:
        raise G07ProofError(f"scope-capability-forbidden:{unsupported[0]}")
    return ScopeGrant(
        scope_id=scope_id,
        root=str(normalized_root),
        capabilities=normalized_capabilities,
    )


def build_core_authority(scopes: Iterable[ScopeGrant]) -> CoreAuthorityConfig:
    values = tuple(sorted(scopes, key=lambda scope: scope.scope_id))
    seen: set[str] = set()
    for scope in values:
        if scope.scope_id in seen:
            raise G07ProofError("scope-id-duplicate")
        seen.add(scope.scope_id)
        # Revalidate even preconstructed dataclass instances; callers may not
        # bypass Core capability/root rules by instantiating ScopeGrant directly.
        validated = create_core_scope(scope.scope_id, scope.root, scope.capabilities)
        if validated != scope:
            raise G07ProofError("scope-not-canonical")
    return CoreAuthorityConfig(scopes=values)


def authorize_request(
    authority: CoreAuthorityConfig,
    request: ExternalRequest,
) -> AuthorizationDecision:
    _require_text(request.scope_id, "request-scope-id")
    _require_text(request.capability, "request-capability")
    if request.capability in _MUTATION_CAPABILITIES:
        return AuthorizationDecision(
            allowed=False,
            scope_id=request.scope_id,
            capability=request.capability,
            normalized_path=None,
            reason="mutation-capability-not-granted-by-proof",
        )

    grant = next((scope for scope in authority.scopes if scope.scope_id == request.scope_id), None)
    if grant is None:
        return AuthorizationDecision(
            allowed=False,
            scope_id=request.scope_id,
            capability=request.capability,
            normalized_path=None,
            reason="unknown-scope-id",
        )

    if request.capability not in grant.capabilities:
        return AuthorizationDecision(
            allowed=False,
            scope_id=request.scope_id,
            capability=request.capability,
            normalized_path=None,
            reason="capability-not-granted",
        )

    try:
        requested_path = _canonical_absolute_path(request.path, "request-path")
    except G07ProofError as exc:
        return AuthorizationDecision(
            allowed=False,
            scope_id=request.scope_id,
            capability=request.capability,
            normalized_path=None,
            reason=str(exc),
        )

    root = _canonical_absolute_path(grant.root, "scope-root")
    root_parts = root.parts
    path_parts = requested_path.parts
    if len(path_parts) < len(root_parts) or path_parts[: len(root_parts)] != root_parts:
        return AuthorizationDecision(
            allowed=False,
            scope_id=request.scope_id,
            capability=request.capability,
            normalized_path=str(requested_path),
            reason="path-outside-scope",
        )

    return AuthorizationDecision(
        allowed=True,
        scope_id=request.scope_id,
        capability=request.capability,
        normalized_path=str(requested_path),
        reason="authorized-by-existing-core-scope",
    )


def assert_authority_shapes_minimal() -> None:
    forbidden = {
        "secret",
        "secrets",
        "token",
        "password",
        "document_bytes",
        "content_bytes",
        "requested_root",
        "root_override",
    }
    for record_type in (ScopeGrant, ExternalRequest, AuthorizationDecision):
        names = {field.name for field in fields(record_type)}
        overlap = sorted(names & forbidden)
        if overlap:
            raise G07ProofError(f"authority-record-forbidden-field:{overlap[0]}")
