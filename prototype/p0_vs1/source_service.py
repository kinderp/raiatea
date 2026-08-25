#!/usr/bin/env python3
"""VS1c Core orchestration for the official local SourcePlugin."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
from typing import Any

from prototype.p0_vs1.catalog_store import CatalogStateStore, CatalogStoreError
from prototype.p0_vs1.core_access import ScopeRegistry
from prototype.p0_vs1.local_process_client import LocalPluginProcessClient, LocalPluginProcessError
from prototype.p0_vs1.plugin_io import PluginIOError, Vs1PluginIO
from prototype.p0_vs1.reconciliation import validate_state as validate_vs1b_state
from prototype.p0_vs1.rights import RightsDecisionError, decide_local_reference_discovery, validate_rights_decision
from prototype.p0_vs1.source_contract import (
    DISCOVERY_SNAPSHOT_VERSION,
    EPUB_MEDIA_TYPE,
    SourceContractError,
    build_source_reference_bundle,
    canonical_json_bytes,
    discovery_snapshot_fingerprint,
    sha256_ref,
    validate_discovery_snapshot,
    validate_source_reference,
    validate_source_reference_bundle,
)


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_MANIFEST_PATH = HERE / "plugins" / "local_source" / "manifest.json"
MANIFEST_VALIDATOR_PATH = (
    REPO_ROOT
    / "elaboration"
    / "p0"
    / "contracts"
    / "plugins"
    / "1.0.0"
    / "validate_manifest.py"
)
_MANIFEST_SPEC = importlib.util.spec_from_file_location(
    "vs1c_manifest_validator", MANIFEST_VALIDATOR_PATH
)
MANIFEST_VALIDATOR = importlib.util.module_from_spec(_MANIFEST_SPEC)
assert _MANIFEST_SPEC.loader is not None
_MANIFEST_SPEC.loader.exec_module(MANIFEST_VALIDATOR)


VS1C_STATE_VERSION = "raiatea.vs1c.source-discovery.0.1.0"
SNAPSHOT_MEDIA_TYPE = "application/vnd.raiatea.vs1c-discovery-snapshot+json"
BUNDLE_MEDIA_TYPE = "application/vnd.raiatea.vs1c-source-reference-bundle+json"
MAX_BUNDLE_BYTES = 4 * 1024 * 1024


class SourceDiscoveryError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceDiscoveryError(message)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceDiscoveryError("source-plugin-manifest-unavailable") from exc
    try:
        MANIFEST_VALIDATOR.validate(value)
    except Exception as exc:
        raise SourceDiscoveryError(f"source-plugin-manifest-invalid:{exc}") from exc
    _validate_local_manifest_policy(value)
    return value


def _validate_local_manifest_policy(manifest: dict[str, Any]) -> None:
    _require(manifest.get("families") == ["source"], "local-source-manifest-family-invalid")
    plugin = manifest.get("plugin")
    _require(isinstance(plugin, dict), "local-source-manifest-plugin-invalid")
    _require(
        plugin.get("plugin_id") == "org.raiatea.vs1.local-source",
        "local-source-plugin-id-invalid",
    )
    _require(manifest.get("trust_tier") == "official", "local-source-trust-tier-invalid")
    permissions = manifest.get("permissions")
    _require(isinstance(permissions, dict), "local-source-permissions-invalid")
    _require(permissions.get("network") == [], "local-source-network-forbidden")
    _require(
        permissions.get("filesystem") == [],
        "local-source-filesystem-permission-forbidden",
    )
    _require(permissions.get("secrets") == [], "local-source-secrets-forbidden")
    _require(
        permissions.get("temporary_workspace") is True,
        "local-source-temporary-workspace-required",
    )
    capabilities = manifest.get("capabilities")
    _require(
        isinstance(capabilities, list) and len(capabilities) == 1,
        "local-source-capability-shape-invalid",
    )
    capability = capabilities[0]
    _require(
        capability.get("capability_id") == "source.discover",
        "local-source-capability-invalid",
    )
    profiles = capability.get("profiles")
    _require(
        isinstance(profiles, list) and len(profiles) == 1,
        "local-source-profile-shape-invalid",
    )
    profile = profiles[0]
    _require(
        profile.get("profile_id") == "local-catalog-read-only",
        "local-source-profile-invalid",
    )
    _require(profile.get("family") == "source", "local-source-profile-family-invalid")
    _require(
        profile.get("input_classes") == ["vs1c-discovery-snapshot"],
        "local-source-input-class-invalid",
    )
    _require(
        profile.get("output_classes") == ["vs1c-source-reference-bundle"],
        "local-source-output-class-invalid",
    )


def _active_discovery_items(vs1b: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in vs1b["entries"]:
        if entry["superseded_by"] is not None or entry["availability"] != "known-present":
            continue
        _require(
            entry["reconciliation_status"] == "verified-by-inventory",
            "source-discovery-entry-not-inventory-verified",
        )
        _require(
            entry["media_type"] == EPUB_MEDIA_TYPE,
            "source-discovery-entry-media-type-invalid",
        )
        items.append(
            {
                "catalog_entry_ref": entry["entry_id"],
                "stored_instance_ref": entry["stored_instance_id"],
                "logical_candidate_ref": entry["logical_candidate_id"],
                "media_type": entry["media_type"],
                "byte_length": entry["byte_length"],
                "fingerprint": entry["fingerprint"],
            }
        )
    items.sort(key=lambda row: row["catalog_entry_ref"])
    return items


def _discovery_basis_fingerprint(
    scope_id: str,
    vs1b: dict[str, Any],
    items: list[dict[str, Any]],
) -> str:
    """Fingerprint only canonical facts relevant to source discovery.

    VS1b stores ordered evidence/history where order can be meaningful, but a
    Source discovery snapshot must not change merely because the internal entry
    list is serialized in a different order. The catalog revision remains a
    separate stale-state fence.
    """

    basis = {
        "scope_ref": scope_id,
        "freshness": "fresh",
        "last_seq": vs1b["stream"]["last_seq"],
        "last_reconciled_seq": vs1b["stream"]["last_reconciled_seq"],
        "items": items,
    }
    return sha256_ref(basis)


def build_discovery_snapshot(catalog_snapshot: Any, scope_id: str) -> dict[str, Any]:
    _require(catalog_snapshot is not None, "source-discovery-catalog-required")
    revision = getattr(catalog_snapshot, "revision", None)
    payload = getattr(catalog_snapshot, "payload", None)
    _require(
        isinstance(revision, int) and revision >= 1,
        "source-discovery-catalog-revision-invalid",
    )
    _require(isinstance(payload, dict), "source-discovery-catalog-payload-invalid")
    vs1b = payload.get("vs1b")
    _require(isinstance(vs1b, dict), "source-discovery-vs1b-state-required")
    try:
        validate_vs1b_state(vs1b, scope_id)
    except Exception as exc:
        raise SourceDiscoveryError(f"source-discovery-vs1b-state-invalid:{exc}") from exc
    _require(
        vs1b["freshness"]["status"] == "fresh",
        "source-discovery-catalog-not-fresh",
    )
    items = _active_discovery_items(vs1b)
    snapshot = {
        "snapshot_version": DISCOVERY_SNAPSHOT_VERSION,
        "scope_ref": scope_id,
        "catalog_revision": revision,
        "vs1b_state_fingerprint": _discovery_basis_fingerprint(scope_id, vs1b, items),
        "freshness": "fresh",
        "items": items,
    }
    try:
        validate_discovery_snapshot(snapshot)
    except SourceContractError as exc:
        raise SourceDiscoveryError(f"source-discovery-snapshot-invalid:{exc}") from exc
    return snapshot


def _invocation_request(
    runtime_instance_id: str,
    scope_id: str,
    rights_decision_ref: str,
    snapshot_handle: dict[str, Any],
    output_target: dict[str, Any],
    snapshot_fingerprint: str,
) -> dict[str, Any]:
    deadline = datetime.now(timezone.utc) + timedelta(seconds=30)
    idempotency_basis = (
        f"{scope_id}:{rights_decision_ref}:{snapshot_fingerprint}".encode("utf-8")
    )
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:vs1c:source:" + secrets.token_urlsafe(14),
        "idempotency_key": (
            "idem:vs1c:source:" + hashlib.sha256(idempotency_basis).hexdigest()
        ),
        "runtime_instance_id": runtime_instance_id,
        "capability": {
            "capability_id": "source.discover",
            "profile_id": "local-catalog-read-only",
        },
        "inputs": [{"kind": "asset-handle", "handle": snapshot_handle}],
        "output_targets": [output_target],
        "runtime_context": {
            "workspace_scope_id": scope_id,
            "rights_decision_ref": rights_decision_ref,
            "secret_leases": [],
        },
        "deadline_at": deadline.isoformat().replace("+00:00", "Z"),
        "parameters": {},
    }


def _find_completed_asset(
    result: dict[str, Any], target_handle_id: str
) -> dict[str, Any]:
    assets = [
        row["handle"]
        for row in result.get("outputs", [])
        if isinstance(row, dict)
        and row.get("kind") == "asset-handle"
        and isinstance(row.get("handle"), dict)
    ]
    _require(
        len(assets) == 1,
        "source-plugin-completed-asset-count-invalid",
    )
    _require(
        assets[0].get("handle_id") == target_handle_id,
        "source-plugin-completed-asset-target-mismatch",
    )
    return assets[0]


def _result_record_refs(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row["record_ref"]
        for row in result.get("outputs", [])
        if isinstance(row, dict)
        and row.get("kind") == "record-ref"
        and isinstance(row.get("record_ref"), dict)
    ]


def _validate_plugin_result_against_snapshot(
    snapshot: dict[str, Any],
    bundle: dict[str, Any],
    result: dict[str, Any],
    rights_decision_ref: str,
) -> list[dict[str, Any]]:
    try:
        validate_source_reference_bundle(bundle)
    except SourceContractError as exc:
        raise SourceDiscoveryError(f"source-plugin-bundle-invalid:{exc}") from exc
    expected = build_source_reference_bundle(snapshot)
    _require(
        canonical_json_bytes(bundle) == canonical_json_bytes(expected),
        "source-plugin-bundle-does-not-match-snapshot",
    )
    expected_refs = expected["record_refs"]
    _require(
        _result_record_refs(result) == expected_refs,
        "source-plugin-result-record-refs-mismatch",
    )
    provenance = result.get("provenance")
    _require(isinstance(provenance, dict), "source-plugin-provenance-required")
    _require(
        provenance.get("rights_decision_ref") == rights_decision_ref,
        "source-plugin-rights-decision-ref-mismatch",
    )
    records = [bundle["records"][ref["ref_id"]] for ref in expected_refs]
    for record in records:
        validate_source_reference(record)
    return records


def _vs1c_state(
    *,
    scope_id: str,
    catalog_basis_revision: int,
    snapshot: dict[str, Any],
    rights_decision: dict[str, Any],
    manifest: dict[str, Any],
    result: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    state = {
        "state_version": VS1C_STATE_VERSION,
        "scope_ref": scope_id,
        "catalog_basis_revision": catalog_basis_revision,
        "vs1b_state_fingerprint": snapshot["vs1b_state_fingerprint"],
        "snapshot_fingerprint": discovery_snapshot_fingerprint(snapshot),
        "rights_decision": deepcopy(rights_decision),
        "plugin": {
            "plugin_id": manifest["plugin"]["plugin_id"],
            "plugin_version": manifest["plugin"]["version"],
            "manifest_fingerprint": sha256_ref(manifest),
        },
        "source_references": deepcopy(records),
        "provenance": deepcopy(result["provenance"]),
    }
    validate_vs1c_state(state, scope_id)
    return state


def validate_vs1c_state(value: Any, scope_id: str) -> dict[str, Any]:
    _require(isinstance(value, dict), "vs1c-state-must-be-object")
    expected = {
        "state_version",
        "scope_ref",
        "catalog_basis_revision",
        "vs1b_state_fingerprint",
        "snapshot_fingerprint",
        "rights_decision",
        "plugin",
        "source_references",
        "provenance",
    }
    _require(set(value) == expected, "vs1c-state-shape-invalid")
    _require(
        value["state_version"] == VS1C_STATE_VERSION,
        "vs1c-state-version-unsupported",
    )
    _require(value["scope_ref"] == scope_id, "vs1c-state-scope-mismatch")
    _require(
        isinstance(value["catalog_basis_revision"], int)
        and not isinstance(value["catalog_basis_revision"], bool)
        and value["catalog_basis_revision"] >= 1,
        "vs1c-state-catalog-basis-invalid",
    )
    for key in ("vs1b_state_fingerprint", "snapshot_fingerprint"):
        fingerprint = value[key]
        _require(
            isinstance(fingerprint, str)
            and fingerprint.startswith("sha256:")
            and len(fingerprint) == 71,
            f"vs1c-state-{key}-invalid",
        )
    validate_rights_decision(value["rights_decision"])
    plugin = value["plugin"]
    _require(
        isinstance(plugin, dict)
        and set(plugin)
        == {"plugin_id", "plugin_version", "manifest_fingerprint"},
        "vs1c-state-plugin-invalid",
    )
    _require(
        plugin["plugin_id"] == "org.raiatea.vs1.local-source",
        "vs1c-state-plugin-id-invalid",
    )
    _require(
        isinstance(plugin["plugin_version"], str) and plugin["plugin_version"],
        "vs1c-state-plugin-version-invalid",
    )
    _require(
        isinstance(plugin["manifest_fingerprint"], str)
        and plugin["manifest_fingerprint"].startswith("sha256:"),
        "vs1c-state-manifest-fingerprint-invalid",
    )
    records = value["source_references"]
    _require(isinstance(records, list), "vs1c-state-source-references-invalid")
    seen: set[str] = set()
    for record in records:
        validated = validate_source_reference(record)
        _require(
            validated["source_ref_id"] not in seen,
            "vs1c-state-source-ref-duplicate",
        )
        seen.add(validated["source_ref_id"])
    _require(
        [record["source_ref_id"] for record in records]
        == sorted(record["source_ref_id"] for record in records),
        "vs1c-state-source-refs-not-canonical-order",
    )
    provenance = value["provenance"]
    _require(isinstance(provenance, dict), "vs1c-state-provenance-invalid")
    _require(
        provenance.get("plugin_id") == plugin["plugin_id"],
        "vs1c-state-provenance-plugin-mismatch",
    )
    _require(
        provenance.get("rights_decision_ref")
        == value["rights_decision"]["decision_id"],
        "vs1c-state-provenance-rights-mismatch",
    )
    return value


class LocalSourceDiscoveryService:
    def __init__(
        self,
        store: CatalogStateStore,
        scopes: ScopeRegistry,
        scope_id: str,
        *,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
    ) -> None:
        self._store = store
        self._scopes = scopes
        self._scope_id = scope_id
        self._manifest_path = manifest_path
        self._scopes.require_capability(scope_id, "observe")

    def discover(self, *, rights_evidence_state: str) -> dict[str, Any]:
        catalog_snapshot = self._store.load()
        snapshot = build_discovery_snapshot(catalog_snapshot, self._scope_id)
        manifest = _load_manifest(self._manifest_path)
        try:
            rights_decision = decide_local_reference_discovery(
                self._scopes,
                self._scope_id,
                plugin_id=manifest["plugin"]["plugin_id"],
                rights_evidence_state=rights_evidence_state,
            )
        except RightsDecisionError as exc:
            raise SourceDiscoveryError(str(exc)) from exc

        snapshot_bytes = canonical_json_bytes(snapshot)
        with Vs1PluginIO() as plugin_io:
            input_handle = plugin_io.add_input(
                snapshot_bytes,
                media_type=SNAPSHOT_MEDIA_TYPE,
                ttl_seconds=120,
            )
            output_target = plugin_io.issue_output(
                media_type=BUNDLE_MEDIA_TYPE,
                max_byte_length=MAX_BUNDLE_BYTES,
                ttl_seconds=120,
            )
            environment = plugin_io.freeze()
            command = manifest["entrypoint"]["command"]
            try:
                with LocalPluginProcessClient(
                    command, manifest, extra_env=environment
                ) as client:
                    handshake = client.handshake()
                    request = _invocation_request(
                        handshake["identity"]["runtime_instance_id"],
                        self._scope_id,
                        rights_decision["decision_id"],
                        input_handle,
                        output_target,
                        discovery_snapshot_fingerprint(snapshot),
                    )
                    result = client.invoke(request)
                plugin_io.verify_broker_unchanged()
            except (LocalPluginProcessError, PluginIOError) as exc:
                raise SourceDiscoveryError(
                    f"source-plugin-execution-failed:{exc}"
                ) from exc

            _require(
                result.get("status") == "completed",
                "source-plugin-result-not-completed",
            )
            completed = _find_completed_asset(result, output_target["handle_id"])
            try:
                bundle_bytes = plugin_io.read_completed_output(
                    output_target, completed
                )
            except PluginIOError as exc:
                raise SourceDiscoveryError(
                    f"source-plugin-output-invalid:{exc}"
                ) from exc

        try:
            bundle = json.loads(bundle_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceDiscoveryError("source-plugin-bundle-json-invalid") from exc
        _require(
            canonical_json_bytes(bundle) == bundle_bytes,
            "source-plugin-bundle-not-canonical",
        )
        records = _validate_plugin_result_against_snapshot(
            snapshot,
            bundle,
            result,
            rights_decision["decision_id"],
        )

        original_payload = deepcopy(catalog_snapshot.payload)
        original_payload["vs1c"] = _vs1c_state(
            scope_id=self._scope_id,
            catalog_basis_revision=catalog_snapshot.revision,
            snapshot=snapshot,
            rights_decision=rights_decision,
            manifest=manifest,
            result=result,
            records=records,
        )
        try:
            saved = self._store.save(
                original_payload,
                expected_revision=catalog_snapshot.revision,
            )
        except CatalogStoreError as exc:
            raise SourceDiscoveryError(
                "source-discovery-catalog-changed-during-plugin-run"
            ) from exc
        return {
            "status": "completed",
            "catalog_revision": saved.revision,
            "catalog_basis_revision": catalog_snapshot.revision,
            "snapshot_fingerprint": discovery_snapshot_fingerprint(snapshot),
            "rights_decision_ref": rights_decision["decision_id"],
            "source_reference_count": len(records),
            "source_refs": [record["source_ref_id"] for record in records],
        }
