#!/usr/bin/env python3
"""VS1d Core orchestration for the official direct EPUB ExtractorPlugin."""
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
from prototype.p0_vs1.core_access import AssetBroker, CoreAccessError, ScopeRegistry
from prototype.p0_vs1.extraction_contract import (
    EXTRACTION_BUNDLE_MEDIA_TYPE,
    ExtractionContractError,
    canonical_extraction_bundle_bytes,
    validate_extraction_bundle,
)
from prototype.p0_vs1.extraction_rights import (
    OFFICIAL_EXTRACTOR_PLUGIN_ID,
    ExtractionRightsError,
    decide_local_epub_extraction,
    validate_extraction_rights_decision,
)
from prototype.p0_vs1.local_process_client import LocalPluginProcessClient, LocalPluginProcessError
from prototype.p0_vs1.plugin_io import PluginIOError, Vs1PluginIO
from prototype.p0_vs1.reconciliation import validate_state as validate_vs1b_state
from prototype.p0_vs1.source_contract import (
    EPUB_MEDIA_TYPE,
    SOURCE_REFERENCE_CONTRACT_ID,
    SOURCE_REFERENCE_CONTRACT_VERSION,
    sha256_ref,
    validate_source_reference,
)
from prototype.p0_vs1.source_service import validate_vs1c_state


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_MANIFEST_PATH = HERE / "plugins" / "direct_epub" / "manifest.json"
MANIFEST_VALIDATOR_PATH = (
    REPO_ROOT / "elaboration" / "p0" / "contracts" / "plugins" / "1.0.0" / "validate_manifest.py"
)
_MANIFEST_SPEC = importlib.util.spec_from_file_location("vs1d_manifest_validator", MANIFEST_VALIDATOR_PATH)
MANIFEST_VALIDATOR = importlib.util.module_from_spec(_MANIFEST_SPEC)
assert _MANIFEST_SPEC.loader is not None
_MANIFEST_SPEC.loader.exec_module(MANIFEST_VALIDATOR)


VS1D_STATE_VERSION = "raiatea.vs1d.extraction-state.0.1.0"
MAX_EXTRACTION_BUNDLE_BYTES = 16 * 1024 * 1024
OFFICIAL_EXTRACTOR_COMMAND = [
    "python",
    "-m",
    "prototype.p0_vs1.plugins.direct_epub.plugin",
]


class EpubExtractionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EpubExtractionError(message)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EpubExtractionError("extractor-plugin-manifest-unavailable") from exc
    try:
        MANIFEST_VALIDATOR.validate(value)
    except Exception as exc:
        raise EpubExtractionError(f"extractor-plugin-manifest-invalid:{exc}") from exc
    _validate_manifest_policy(value)
    return value


def _validate_manifest_policy(manifest: dict[str, Any]) -> None:
    plugin = manifest.get("plugin")
    _require(isinstance(plugin, dict), "extractor-manifest-plugin-required")
    _require(plugin.get("plugin_id") == OFFICIAL_EXTRACTOR_PLUGIN_ID, "extractor-plugin-id-invalid")
    _require(manifest.get("families") == ["extractor"], "extractor-family-invalid")
    _require(manifest.get("trust_tier") == "official", "extractor-trust-tier-invalid")
    permissions = manifest.get("permissions")
    _require(isinstance(permissions, dict), "extractor-permissions-required")
    _require(permissions.get("network") == [], "extractor-network-forbidden")
    _require(permissions.get("filesystem") == [], "extractor-filesystem-permission-forbidden")
    _require(permissions.get("secrets") == [], "extractor-secrets-forbidden")
    _require(permissions.get("temporary_workspace") is True, "extractor-temporary-workspace-required")
    capabilities = manifest.get("capabilities")
    _require(isinstance(capabilities, list) and len(capabilities) == 1, "extractor-capability-shape-invalid")
    capability = capabilities[0]
    _require(capability.get("capability_id") == "extract.run", "extractor-capability-invalid")
    profiles = capability.get("profiles")
    _require(isinstance(profiles, list) and len(profiles) == 1, "extractor-profile-shape-invalid")
    profile = profiles[0]
    _require(profile.get("profile_id") == "epub-direct-stdlib", "extractor-profile-invalid")
    _require(profile.get("family") == "extractor", "extractor-profile-family-invalid")
    _require(profile.get("input_classes") == [EPUB_MEDIA_TYPE], "extractor-input-class-invalid")
    entrypoint = manifest.get("entrypoint")
    _require(isinstance(entrypoint, dict), "extractor-entrypoint-required")
    _require(entrypoint.get("kind") == "process", "extractor-entrypoint-kind-invalid")
    _require(entrypoint.get("command") == OFFICIAL_EXTRACTOR_COMMAND, "extractor-official-command-invalid")


def _source_ref_record_ref(source_ref_id: str) -> dict[str, Any]:
    return {
        "ref_id": source_ref_id,
        "contract_id": SOURCE_REFERENCE_CONTRACT_ID,
        "contract_version": SOURCE_REFERENCE_CONTRACT_VERSION,
        "record_kind": "SourceReferenceRecord",
    }


def _resolve_source(catalog_snapshot: Any, scope_id: str, source_ref_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(catalog_snapshot is not None, "extraction-catalog-required")
    payload = getattr(catalog_snapshot, "payload", None)
    _require(isinstance(payload, dict), "extraction-catalog-payload-invalid")
    vs1b = payload.get("vs1b")
    vs1c = payload.get("vs1c")
    _require(isinstance(vs1b, dict), "extraction-vs1b-state-required")
    _require(isinstance(vs1c, dict), "extraction-vs1c-state-required")
    try:
        validate_vs1b_state(vs1b, scope_id)
        validate_vs1c_state(vs1c, scope_id)
    except Exception as exc:
        raise EpubExtractionError(f"extraction-upstream-state-invalid:{exc}") from exc
    _require(vs1b["freshness"]["status"] == "fresh", "extraction-catalog-not-fresh")

    matches = [row for row in vs1c["source_references"] if row.get("source_ref_id") == source_ref_id]
    _require(len(matches) == 1, "extraction-source-reference-not-current")
    source_ref = validate_source_reference(matches[0])
    stored_ref = source_ref["stored_instance_ref"]
    entries = [
        row
        for row in vs1b["entries"]
        if row.get("stored_instance_id") == stored_ref
        and row.get("superseded_by") is None
        and row.get("availability") == "known-present"
    ]
    _require(len(entries) == 1, "extraction-stored-instance-not-current")
    entry = entries[0]
    _require(entry.get("reconciliation_status") == "verified-by-inventory", "extraction-source-not-inventory-verified")
    for source_key, entry_key in (
        ("catalog_entry_ref", "entry_id"),
        ("logical_candidate_ref", "logical_candidate_id"),
        ("fingerprint", "fingerprint"),
        ("byte_length", "byte_length"),
        ("media_type", "media_type"),
    ):
        _require(source_ref[source_key] == entry[entry_key], f"extraction-source-current-{source_key}-mismatch")
    return source_ref, entry


def _invocation_request(
    *,
    runtime_instance_id: str,
    scope_id: str,
    rights_decision_ref: str,
    source_ref: dict[str, Any],
    input_handle: dict[str, Any],
    output_target: dict[str, Any],
) -> dict[str, Any]:
    deadline = datetime.now(timezone.utc) + timedelta(seconds=30)
    basis = f"{source_ref['source_ref_id']}:{source_ref['fingerprint']}:{rights_decision_ref}".encode("utf-8")
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:vs1d:epub:" + secrets.token_urlsafe(14),
        "idempotency_key": "idem:vs1d:epub:" + hashlib.sha256(basis).hexdigest(),
        "runtime_instance_id": runtime_instance_id,
        "capability": {"capability_id": "extract.run", "profile_id": "epub-direct-stdlib"},
        "inputs": [
            {"kind": "asset-handle", "handle": input_handle},
            {"kind": "record-ref", "record_ref": _source_ref_record_ref(source_ref["source_ref_id"])},
        ],
        "output_targets": [output_target],
        "runtime_context": {
            "workspace_scope_id": scope_id,
            "rights_decision_ref": rights_decision_ref,
            "secret_leases": [],
        },
        "deadline_at": deadline.isoformat().replace("+00:00", "Z"),
        "parameters": {},
    }


def _completed_asset(result: dict[str, Any], target_id: str) -> dict[str, Any]:
    rows = [
        row["handle"]
        for row in result.get("outputs", [])
        if isinstance(row, dict) and row.get("kind") == "asset-handle" and isinstance(row.get("handle"), dict)
    ]
    _require(len(rows) == 1, "extractor-completed-asset-count-invalid")
    _require(rows[0].get("handle_id") == target_id, "extractor-completed-asset-target-mismatch")
    return rows[0]


def _result_record_refs(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row["record_ref"]
        for row in result.get("outputs", [])
        if isinstance(row, dict) and row.get("kind") == "record-ref" and isinstance(row.get("record_ref"), dict)
    ]


def _validate_result(
    *,
    source_ref: dict[str, Any],
    rights_decision_ref: str,
    bundle: dict[str, Any],
    result: dict[str, Any],
) -> None:
    try:
        validate_extraction_bundle(bundle)
    except ExtractionContractError as exc:
        raise EpubExtractionError(f"extractor-bundle-invalid:{exc}") from exc
    _require(bundle["source_ref_id"] == source_ref["source_ref_id"], "extractor-bundle-source-ref-mismatch")
    _require(bundle["source_fingerprint"] == source_ref["fingerprint"], "extractor-bundle-source-fingerprint-mismatch")
    _require(_result_record_refs(result) == bundle["record_refs"], "extractor-result-record-refs-mismatch")
    provenance = result.get("provenance")
    _require(isinstance(provenance, dict), "extractor-result-provenance-required")
    _require(provenance.get("rights_decision_ref") == rights_decision_ref, "extractor-result-rights-ref-mismatch")


def _extraction_entry(
    *,
    catalog_basis_revision: int,
    source_ref: dict[str, Any],
    rights_decision: dict[str, Any],
    manifest: dict[str, Any],
    bundle: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_ref_id": source_ref["source_ref_id"],
        "source_fingerprint": source_ref["fingerprint"],
        "catalog_basis_revision": catalog_basis_revision,
        "rights_decision": deepcopy(rights_decision),
        "plugin": {
            "plugin_id": manifest["plugin"]["plugin_id"],
            "plugin_version": manifest["plugin"]["version"],
            "manifest_fingerprint": sha256_ref(manifest),
            "route_profile": "epub-direct-stdlib",
        },
        "record_refs": deepcopy(bundle["record_refs"]),
        "records": deepcopy(bundle["records"]),
        "provenance": deepcopy(result["provenance"]),
    }


def validate_vs1d_state(value: Any, scope_id: str) -> dict[str, Any]:
    _require(isinstance(value, dict), "vs1d-state-must-be-object")
    _require(set(value) == {"state_version", "scope_ref", "extractions"}, "vs1d-state-shape-invalid")
    _require(value["state_version"] == VS1D_STATE_VERSION, "vs1d-state-version-unsupported")
    _require(value["scope_ref"] == scope_id, "vs1d-state-scope-mismatch")
    rows = value["extractions"]
    _require(isinstance(rows, list), "vs1d-extractions-must-be-array")
    ids: list[str] = []
    for row in rows:
        _require(isinstance(row, dict), "vs1d-extraction-entry-invalid")
        expected = {
            "source_ref_id",
            "source_fingerprint",
            "catalog_basis_revision",
            "rights_decision",
            "plugin",
            "record_refs",
            "records",
            "provenance",
        }
        _require(set(row) == expected, "vs1d-extraction-entry-shape-invalid")
        source_ref_id = row["source_ref_id"]
        _require(isinstance(source_ref_id, str) and source_ref_id.startswith("source-ref:"), "vs1d-source-ref-invalid")
        _require(source_ref_id not in ids, "vs1d-source-ref-duplicate")
        ids.append(source_ref_id)
        validate_extraction_rights_decision(row["rights_decision"])
        plugin = row["plugin"]
        _require(isinstance(plugin, dict) and set(plugin) == {"plugin_id", "plugin_version", "manifest_fingerprint", "route_profile"}, "vs1d-plugin-state-invalid")
        _require(plugin["plugin_id"] == OFFICIAL_EXTRACTOR_PLUGIN_ID, "vs1d-plugin-id-invalid")
        _require(plugin["route_profile"] == "epub-direct-stdlib", "vs1d-route-profile-invalid")
        bundle = {
            "bundle_version": "raiatea.vs1d.e05-bundle.0.1.0",
            "record_kind": "E05ExtractionBundle",
            "source_ref_id": source_ref_id,
            "source_fingerprint": row["source_fingerprint"],
            "record_refs": row["record_refs"],
            "records": row["records"],
        }
        validate_extraction_bundle(bundle)
        provenance = row["provenance"]
        _require(isinstance(provenance, dict), "vs1d-provenance-invalid")
        _require(provenance.get("plugin_id") == plugin["plugin_id"], "vs1d-provenance-plugin-mismatch")
        _require(
            provenance.get("rights_decision_ref") == row["rights_decision"]["decision_id"],
            "vs1d-provenance-rights-mismatch",
        )
    _require(ids == sorted(ids), "vs1d-extractions-not-canonical-order")
    return value


class LocalEpubExtractionService:
    def __init__(
        self,
        store: CatalogStateStore,
        scopes: ScopeRegistry,
        source_broker: AssetBroker,
        scope_id: str,
        *,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
    ) -> None:
        self._store = store
        self._scopes = scopes
        self._source_broker = source_broker
        self._scope_id = scope_id
        self._manifest_path = manifest_path
        self._scopes.require_capability(scope_id, "read-for-processing")

    def extract(self, source_ref_id: str, *, rights_evidence_state: str) -> dict[str, Any]:
        catalog_snapshot = self._store.load()
        _require(catalog_snapshot is not None, "extraction-catalog-required")
        source_ref, entry = _resolve_source(catalog_snapshot, self._scope_id, source_ref_id)
        manifest = _load_manifest(self._manifest_path)
        try:
            rights_decision = decide_local_epub_extraction(
                self._scopes,
                self._scope_id,
                plugin_id=manifest["plugin"]["plugin_id"],
                rights_evidence_state=rights_evidence_state,
            )
        except ExtractionRightsError as exc:
            raise EpubExtractionError(str(exc)) from exc

        location = entry["current_location"]
        try:
            source_handle = self._source_broker.issue_read_handle(
                self._scope_id,
                location,
                media_type=EPUB_MEDIA_TYPE,
                ttl_seconds=120,
            )
            _require(source_handle["fingerprint"] == source_ref["fingerprint"], "extraction-source-changed-after-discovery")
            _require(source_handle["byte_length"] == source_ref["byte_length"], "extraction-source-length-changed-after-discovery")
            source_bytes = self._source_broker.read_asset(source_handle)
        except CoreAccessError as exc:
            raise EpubExtractionError(f"extraction-source-safe-read-failed:{exc}") from exc

        with Vs1PluginIO() as plugin_io:
            input_handle = plugin_io.add_input(source_bytes, media_type=EPUB_MEDIA_TYPE, ttl_seconds=120)
            _require(input_handle["fingerprint"] == source_ref["fingerprint"], "extraction-private-copy-fingerprint-mismatch")
            output_target = plugin_io.issue_output(
                media_type=EXTRACTION_BUNDLE_MEDIA_TYPE,
                max_byte_length=MAX_EXTRACTION_BUNDLE_BYTES,
                ttl_seconds=120,
            )
            environment = plugin_io.freeze()
            try:
                with LocalPluginProcessClient(
                    manifest["entrypoint"]["command"],
                    manifest,
                    extra_env=environment,
                ) as client:
                    handshake = client.handshake()
                    request = _invocation_request(
                        runtime_instance_id=handshake["identity"]["runtime_instance_id"],
                        scope_id=self._scope_id,
                        rights_decision_ref=rights_decision["decision_id"],
                        source_ref=source_ref,
                        input_handle=input_handle,
                        output_target=output_target,
                    )
                    result = client.invoke(request)
                plugin_io.verify_broker_unchanged()
            except (LocalPluginProcessError, PluginIOError) as exc:
                raise EpubExtractionError(f"extractor-plugin-execution-failed:{exc}") from exc

            _require(result.get("status") == "completed", "extractor-result-not-completed")
            completed = _completed_asset(result, output_target["handle_id"])
            try:
                bundle_bytes = plugin_io.read_completed_output(output_target, completed)
            except PluginIOError as exc:
                raise EpubExtractionError(f"extractor-output-invalid:{exc}") from exc

        try:
            bundle = json.loads(bundle_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EpubExtractionError("extractor-bundle-json-invalid") from exc
        _require(canonical_extraction_bundle_bytes(bundle) == bundle_bytes, "extractor-bundle-not-canonical")
        _validate_result(
            source_ref=source_ref,
            rights_decision_ref=rights_decision["decision_id"],
            bundle=bundle,
            result=result,
        )

        # The extractor worked from the exact private copy created above. Before
        # publishing that representation, re-open the original source through the
        # already-issued VS1a handle. If the source was replaced, moved, removed or
        # changed while the plugin ran, VS1a's handle fingerprint/length boundary
        # fails and the older representation is not promoted as current content.
        try:
            final_source_bytes = self._source_broker.read_asset(source_handle)
        except CoreAccessError as exc:
            raise EpubExtractionError(
                f"extraction-source-changed-during-plugin-run:{exc}"
            ) from exc
        _require(
            len(final_source_bytes) == source_ref["byte_length"]
            and hashlib.sha256(final_source_bytes).hexdigest()
            == source_ref["fingerprint"].removeprefix("sha256:"),
            "extraction-source-changed-during-plugin-run",
        )

        payload = deepcopy(catalog_snapshot.payload)
        existing: list[dict[str, Any]] = []
        prior = payload.get("vs1d")
        if prior is not None:
            validate_vs1d_state(prior, self._scope_id)
            existing = [deepcopy(row) for row in prior["extractions"] if row["source_ref_id"] != source_ref_id]
        existing.append(
            _extraction_entry(
                catalog_basis_revision=catalog_snapshot.revision,
                source_ref=source_ref,
                rights_decision=rights_decision,
                manifest=manifest,
                bundle=bundle,
                result=result,
            )
        )
        existing.sort(key=lambda row: row["source_ref_id"])
        payload["vs1d"] = {
            "state_version": VS1D_STATE_VERSION,
            "scope_ref": self._scope_id,
            "extractions": existing,
        }
        validate_vs1d_state(payload["vs1d"], self._scope_id)
        try:
            saved = self._store.save(payload, expected_revision=catalog_snapshot.revision)
        except CatalogStoreError as exc:
            raise EpubExtractionError("extraction-catalog-changed-during-plugin-run") from exc

        representation = next(
            (
                bundle["records"][ref["ref_id"]]
                for ref in bundle["record_refs"]
                if ref["record_kind"] == "NormalizedRepresentationRecord"
            ),
            None,
        )
        return {
            "status": "completed",
            "catalog_revision": saved.revision,
            "catalog_basis_revision": catalog_snapshot.revision,
            "source_ref_id": source_ref_id,
            "rights_decision_ref": rights_decision["decision_id"],
            "record_refs": deepcopy(bundle["record_refs"]),
            "normalized_unit_count": len(representation.get("units", [])) if isinstance(representation, dict) else 0,
        }
