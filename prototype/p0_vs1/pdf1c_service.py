#!/usr/bin/env python3
"""PDF1c rights-first Core orchestration for local Docling PDF extraction."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import tempfile
from typing import Any

from prototype.p0_vs1.catalog_store import CatalogStateStore, CatalogStoreError
from prototype.p0_vs1.core_access import AssetBroker, CoreAccessError, ScopeRegistry
from prototype.p0_vs1.docling_e05_adapter import adapt_docling_observation
from prototype.p0_vs1.docling_observation_contract import (
    DOCLING_OBSERVATION_MEDIA_TYPE,
    DOCLING_PROFILE,
    DoclingObservationError,
    canonical_json_bytes as docling_json_bytes,
    validate_docling_observation_bundle,
)
from prototype.p0_vs1.docling_process_environment import (
    DoclingProcessEnvironmentError,
    build_docling_extra_env,
)
from prototype.p0_vs1.docling_reference import (
    DoclingReferenceError,
    validate_reference_provider_record,
    verify_reference_docling,
)
from prototype.p0_vs1.local_process_client import (
    LocalPluginProcessClient,
    LocalPluginProcessError,
)
from prototype.p0_vs1.pdf1c_e05_contract import (
    DoclingPdfE05ContractError,
    build_docling_pdf_extraction_bundle,
    validate_attempt_records,
    validate_docling_pdf_extraction_bundle,
)
from prototype.p0_vs1.pdf1c_rights import (
    DOCLING_PLUGIN_ID,
    DoclingPdfRightsError,
    decide_local_docling_pdf_extraction,
    validate_docling_pdf_rights_decision,
)
from prototype.p0_vs1.plugin_io import PluginIOError, Vs1PluginIO
from prototype.p0_vs1.reconciliation import validate_state as validate_vs1b_state
from prototype.p0_vs1.source_contract import (
    PDF_MEDIA_TYPE,
    SOURCE_REFERENCE_CONTRACT_ID,
    SOURCE_REFERENCE_CONTRACT_VERSION,
    sha256_ref,
    validate_source_reference,
)
from prototype.p0_vs1.source_service import validate_vs1c_state


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_MANIFEST_PATH = HERE / "plugins" / "docling_pdf" / "manifest.json"
MANIFEST_VALIDATOR_PATH = (
    REPO_ROOT
    / "elaboration"
    / "p0"
    / "contracts"
    / "plugins"
    / "1.0.0"
    / "validate_manifest.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "pdf1c_manifest_validator",
    MANIFEST_VALIDATOR_PATH,
)
MANIFEST_VALIDATOR = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(MANIFEST_VALIDATOR)

PDF1C_STATE_VERSION = "raiatea.pdf1c.extraction-state.0.1.0"
MAX_PROVIDER_OBSERVATION_BYTES = 16 * 1024 * 1024
MAX_ATTEMPTS = 64
OFFICIAL_COMMAND = [
    "python",
    "-m",
    "prototype.p0_vs1.plugins.docling_pdf.plugin",
]
PROVIDER_TIMEOUT_SECONDS = 300
LEASE_SECONDS = 420


class DoclingPdfExtractionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingPdfExtractionError(message)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DoclingPdfExtractionError("docling-plugin-manifest-unavailable") from exc
    try:
        MANIFEST_VALIDATOR.validate(value)
    except Exception as exc:
        raise DoclingPdfExtractionError(
            f"docling-plugin-manifest-invalid:{exc}"
        ) from exc
    _validate_manifest_policy(value)
    return value


def _validate_manifest_policy(manifest: dict[str, Any]) -> None:
    plugin = manifest.get("plugin")
    _require(isinstance(plugin, dict), "docling-manifest-plugin-required")
    _require(plugin.get("plugin_id") == DOCLING_PLUGIN_ID, "docling-plugin-id-invalid")
    _require(manifest.get("families") == ["extractor"], "docling-plugin-family-invalid")
    _require(manifest.get("trust_tier") == "official", "docling-plugin-trust-invalid")
    permissions = manifest.get("permissions")
    _require(isinstance(permissions, dict), "docling-plugin-permissions-required")
    _require(permissions.get("network") == [], "docling-plugin-network-forbidden")
    _require(permissions.get("filesystem") == [], "docling-plugin-filesystem-permission-forbidden")
    _require(permissions.get("secrets") == [], "docling-plugin-secrets-forbidden")
    _require(permissions.get("temporary_workspace") is True, "docling-plugin-workspace-required")
    hints = permissions.get("resource_hints")
    _require(isinstance(hints, dict), "docling-plugin-resource-hints-required")
    _require(hints.get("cpu_cores") == 4, "docling-plugin-cpu-profile-invalid")
    _require(hints.get("timeout_seconds") == PROVIDER_TIMEOUT_SECONDS, "docling-plugin-timeout-profile-invalid")
    capabilities = manifest.get("capabilities")
    _require(isinstance(capabilities, list) and len(capabilities) == 1, "docling-plugin-capability-shape-invalid")
    capability = capabilities[0]
    _require(capability.get("capability_id") == "extract.run", "docling-plugin-capability-invalid")
    profiles = capability.get("profiles")
    _require(isinstance(profiles, list) and len(profiles) == 1, "docling-plugin-profile-shape-invalid")
    profile = profiles[0]
    _require(profile.get("profile_id") == DOCLING_PROFILE, "docling-plugin-profile-invalid")
    _require(profile.get("family") == "extractor", "docling-plugin-profile-family-invalid")
    _require(profile.get("input_classes") == [PDF_MEDIA_TYPE], "docling-plugin-input-class-invalid")
    _require(
        profile.get("output_classes") == ["pdf1c-docling-provider-observation"],
        "docling-plugin-output-class-invalid",
    )
    contracts = profile.get("contracts")
    _require(isinstance(contracts, list) and len(contracts) == 1, "docling-plugin-e05-compatibility-required")
    _require(
        contracts[0].get("contract_id") == "raiatea.extraction.processing-run",
        "docling-plugin-e05-contract-invalid",
    )
    _require("record_kinds" not in contracts[0], "docling-plugin-must-not-claim-core-e05-record-kinds")
    entrypoint = manifest.get("entrypoint")
    _require(
        isinstance(entrypoint, dict) and entrypoint.get("kind") == "process",
        "docling-plugin-entrypoint-invalid",
    )
    _require(entrypoint.get("command") == OFFICIAL_COMMAND, "docling-plugin-command-invalid")


def _resolve_source(
    snapshot: Any,
    scope_id: str,
    source_ref_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(snapshot is not None, "docling-extraction-catalog-required")
    payload = getattr(snapshot, "payload", None)
    _require(isinstance(payload, dict), "docling-extraction-catalog-payload-invalid")
    vs1b = payload.get("vs1b")
    vs1c = payload.get("vs1c")
    _require(isinstance(vs1b, dict), "docling-extraction-vs1b-required")
    _require(isinstance(vs1c, dict), "docling-extraction-vs1c-required")
    try:
        validate_vs1b_state(vs1b, scope_id)
        validate_vs1c_state(vs1c, scope_id)
    except Exception as exc:
        raise DoclingPdfExtractionError(
            f"docling-extraction-upstream-invalid:{exc}"
        ) from exc
    _require(vs1b["freshness"]["status"] == "fresh", "docling-extraction-catalog-not-fresh")
    matches = [
        row
        for row in vs1c["source_references"]
        if row.get("source_ref_id") == source_ref_id
    ]
    _require(len(matches) == 1, "docling-source-reference-not-current")
    source_ref = validate_source_reference(matches[0])
    _require(source_ref["media_type"] == PDF_MEDIA_TYPE, "docling-source-reference-media-type-invalid")
    entries = [
        row
        for row in vs1b["entries"]
        if row.get("stored_instance_id") == source_ref["stored_instance_ref"]
        and row.get("superseded_by") is None
        and row.get("availability") == "known-present"
    ]
    _require(len(entries) == 1, "docling-stored-instance-not-current")
    entry = entries[0]
    _require(
        entry.get("reconciliation_status") == "verified-by-inventory",
        "docling-source-not-inventory-verified",
    )
    for source_key, entry_key in (
        ("catalog_entry_ref", "entry_id"),
        ("logical_candidate_ref", "logical_candidate_id"),
        ("fingerprint", "fingerprint"),
        ("byte_length", "byte_length"),
        ("media_type", "media_type"),
    ):
        _require(
            source_ref[source_key] == entry[entry_key],
            f"docling-source-current-{source_key}-mismatch",
        )
    return source_ref, entry


def _source_ref_record_ref(source_ref_id: str) -> dict[str, Any]:
    return {
        "ref_id": source_ref_id,
        "contract_id": SOURCE_REFERENCE_CONTRACT_ID,
        "contract_version": SOURCE_REFERENCE_CONTRACT_VERSION,
        "record_kind": "SourceReferenceRecord",
    }


def _request(
    *,
    runtime_instance_id: str,
    scope_id: str,
    rights_decision_ref: str,
    source_ref: dict[str, Any],
    input_handle: dict[str, Any],
    output_target: dict[str, Any],
) -> dict[str, Any]:
    deadline = datetime.now(timezone.utc) + timedelta(seconds=PROVIDER_TIMEOUT_SECONDS)
    basis = (
        f"{source_ref['source_ref_id']}:{source_ref['fingerprint']}:{rights_decision_ref}"
    ).encode("utf-8")
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:pdf1c:docling:" + secrets.token_urlsafe(14),
        "idempotency_key": "idem:pdf1c:docling:" + hashlib.sha256(basis).hexdigest(),
        "runtime_instance_id": runtime_instance_id,
        "capability": {"capability_id": "extract.run", "profile_id": DOCLING_PROFILE},
        "inputs": [
            {"kind": "asset-handle", "handle": input_handle},
            {
                "kind": "record-ref",
                "record_ref": _source_ref_record_ref(source_ref["source_ref_id"]),
            },
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
        if isinstance(row, dict)
        and row.get("kind") == "asset-handle"
        and isinstance(row.get("handle"), dict)
    ]
    _require(len(rows) == 1, "docling-plugin-completed-asset-count-invalid")
    _require(
        rows[0].get("handle_id") == target_id,
        "docling-plugin-completed-asset-target-mismatch",
    )
    return rows[0]


def _validate_provider_result(
    provider_bundle: dict[str, Any],
    source_ref: dict[str, Any],
    result: dict[str, Any],
    rights_ref: str,
) -> None:
    try:
        validate_docling_observation_bundle(provider_bundle)
        validate_reference_provider_record(provider_bundle["provider"])
    except (DoclingObservationError, DoclingReferenceError) as exc:
        raise DoclingPdfExtractionError(
            f"docling-provider-observation-invalid:{exc}"
        ) from exc
    _require(
        provider_bundle["source_ref_id"] == source_ref["source_ref_id"],
        "docling-provider-source-ref-mismatch",
    )
    _require(
        provider_bundle["source_fingerprint"] == source_ref["fingerprint"],
        "docling-provider-source-fingerprint-mismatch",
    )
    record_refs = [
        row
        for row in result.get("outputs", [])
        if isinstance(row, dict) and row.get("kind") == "record-ref"
    ]
    _require(not record_refs, "docling-plugin-must-not-claim-core-e05-record-refs")
    provenance = result.get("provenance")
    _require(isinstance(provenance, dict), "docling-plugin-provenance-required")
    _require(
        provenance.get("rights_decision_ref") == rights_ref,
        "docling-plugin-rights-ref-mismatch",
    )


def _adapt(
    provider_bundle: dict[str, Any],
    source_ref: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    provenance = result.get("provenance")
    _require(isinstance(provenance, dict), "docling-plugin-provenance-required")
    started_at = provenance.get("started_at")
    _require(
        isinstance(started_at, str) and started_at,
        "docling-plugin-started-at-required",
    )
    ended_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    observation_fingerprint = "sha256:" + hashlib.sha256(
        docling_json_bytes(provider_bundle)
    ).hexdigest()
    adapted = adapt_docling_observation(
        provider_bundle["observation"],
        source_id=source_ref["source_ref_id"],
        fingerprint=source_ref["fingerprint"],
        provider_version=provider_bundle["provider"]["version"],
        provider_observation_fingerprint=observation_fingerprint,
        started_at=started_at,
        ended_at=ended_at,
    )
    try:
        validate_attempt_records(adapted)
    except DoclingPdfE05ContractError as exc:
        raise DoclingPdfExtractionError(f"docling-core-e05-invalid:{exc}") from exc
    return adapted


def _plugin_state(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "plugin_id": manifest["plugin"]["plugin_id"],
        "plugin_version": manifest["plugin"]["version"],
        "manifest_fingerprint": sha256_ref(manifest),
        "route_profile": DOCLING_PROFILE,
    }


def _attempt_id(source_ref_id: str, invocation_id: str) -> str:
    basis = f"{source_ref_id}:{invocation_id}".encode("utf-8")
    return "pdf-docling-attempt:" + hashlib.sha256(basis).hexdigest()


def _current_entry(
    *,
    catalog_basis_revision: int,
    source_ref: dict[str, Any],
    rights_decision: dict[str, Any],
    manifest: dict[str, Any],
    provider_bundle: dict[str, Any],
    e05_bundle: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_ref_id": source_ref["source_ref_id"],
        "source_fingerprint": source_ref["fingerprint"],
        "catalog_basis_revision": catalog_basis_revision,
        "rights_decision": deepcopy(rights_decision),
        "plugin": _plugin_state(manifest),
        "provider_observation": deepcopy(provider_bundle),
        "record_refs": deepcopy(e05_bundle["record_refs"]),
        "records": deepcopy(e05_bundle["records"]),
        "provenance": deepcopy(provenance),
    }


def _attempt_entry(
    *,
    catalog_basis_revision: int,
    source_ref: dict[str, Any],
    rights_decision: dict[str, Any],
    manifest: dict[str, Any],
    provider_bundle: dict[str, Any],
    adapted: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    invocation_id = provenance.get("invocation_id")
    _require(
        isinstance(invocation_id, str) and invocation_id,
        "docling-attempt-invocation-id-required",
    )
    return {
        "attempt_id": _attempt_id(source_ref["source_ref_id"], invocation_id),
        "source_ref_id": source_ref["source_ref_id"],
        "source_fingerprint": source_ref["fingerprint"],
        "catalog_basis_revision": catalog_basis_revision,
        "rights_decision": deepcopy(rights_decision),
        "plugin": _plugin_state(manifest),
        "provider_observation": deepcopy(provider_bundle),
        "run": deepcopy(adapted["run"]),
        "provider_evidence": deepcopy(adapted["provider_evidence"]),
        "provenance": deepcopy(provenance),
    }


def validate_pdf1c_state(value: Any, scope_id: str) -> dict[str, Any]:
    _require(isinstance(value, dict), "pdf1c-state-must-be-object")
    _require(
        set(value)
        == {"state_version", "scope_ref", "current_extractions", "attempts"},
        "pdf1c-state-shape-invalid",
    )
    _require(value["state_version"] == PDF1C_STATE_VERSION, "pdf1c-state-version-unsupported")
    _require(value["scope_ref"] == scope_id, "pdf1c-state-scope-mismatch")
    current = value["current_extractions"]
    attempts = value["attempts"]
    _require(isinstance(current, list), "pdf1c-current-extractions-invalid")
    _require(
        isinstance(attempts, list) and len(attempts) <= MAX_ATTEMPTS,
        "pdf1c-attempts-invalid",
    )
    current_ids: list[str] = []
    for row in current:
        _require(isinstance(row, dict), "pdf1c-current-entry-invalid")
        expected = {
            "source_ref_id",
            "source_fingerprint",
            "catalog_basis_revision",
            "rights_decision",
            "plugin",
            "provider_observation",
            "record_refs",
            "records",
            "provenance",
        }
        _require(set(row) == expected, "pdf1c-current-entry-shape-invalid")
        source_ref_id = row["source_ref_id"]
        _require(
            isinstance(source_ref_id, str) and source_ref_id.startswith("source-ref:"),
            "pdf1c-current-source-ref-invalid",
        )
        _require(source_ref_id not in current_ids, "pdf1c-current-source-ref-duplicate")
        current_ids.append(source_ref_id)
        validate_docling_pdf_rights_decision(row["rights_decision"])
        plugin = row["plugin"]
        _require(
            isinstance(plugin, dict)
            and plugin.get("plugin_id") == DOCLING_PLUGIN_ID
            and plugin.get("route_profile") == DOCLING_PROFILE,
            "pdf1c-current-plugin-invalid",
        )
        validate_docling_observation_bundle(row["provider_observation"])
        validate_reference_provider_record(row["provider_observation"]["provider"])
        bundle = {
            "bundle_version": "raiatea.pdf1c.e05-bundle.0.1.0",
            "record_kind": "DoclingPdfE05ExtractionBundle",
            "source_ref_id": source_ref_id,
            "source_fingerprint": row["source_fingerprint"],
            "record_refs": row["record_refs"],
            "records": row["records"],
        }
        validate_docling_pdf_extraction_bundle(bundle)
        provenance = row["provenance"]
        _require(isinstance(provenance, dict), "pdf1c-current-provenance-invalid")
        _require(
            provenance.get("plugin_id") == DOCLING_PLUGIN_ID,
            "pdf1c-current-provenance-plugin-invalid",
        )
        _require(
            provenance.get("rights_decision_ref")
            == row["rights_decision"]["decision_id"],
            "pdf1c-current-provenance-rights-invalid",
        )
    _require(current_ids == sorted(current_ids), "pdf1c-current-not-canonical")

    attempt_order: list[tuple[str, str]] = []
    seen_attempts: set[str] = set()
    for row in attempts:
        _require(isinstance(row, dict), "pdf1c-attempt-entry-invalid")
        expected = {
            "attempt_id",
            "source_ref_id",
            "source_fingerprint",
            "catalog_basis_revision",
            "rights_decision",
            "plugin",
            "provider_observation",
            "run",
            "provider_evidence",
            "provenance",
        }
        _require(set(row) == expected, "pdf1c-attempt-entry-shape-invalid")
        attempt_id = row["attempt_id"]
        _require(
            isinstance(attempt_id, str)
            and attempt_id.startswith("pdf-docling-attempt:"),
            "pdf1c-attempt-id-invalid",
        )
        _require(attempt_id not in seen_attempts, "pdf1c-attempt-id-duplicate")
        seen_attempts.add(attempt_id)
        validate_docling_pdf_rights_decision(row["rights_decision"])
        validate_docling_observation_bundle(row["provider_observation"])
        validate_reference_provider_record(row["provider_observation"]["provider"])
        adapted = {
            "run": row["run"],
            "provider_evidence": row["provider_evidence"],
        }
        validate_attempt_records(adapted)
        _require(
            row["run"].get("outcome", {}).get("execution") != "completed",
            "pdf1c-attempt-must-not-be-current-success",
        )
        provenance = row["provenance"]
        _require(isinstance(provenance, dict), "pdf1c-attempt-provenance-invalid")
        ended = provenance.get("ended_at")
        _require(
            isinstance(ended, str) and ended,
            "pdf1c-attempt-ended-at-required",
        )
        attempt_order.append((ended, attempt_id))
    _require(
        attempt_order == sorted(attempt_order),
        "pdf1c-attempts-not-canonical",
    )
    return value


class LocalDoclingPdfExtractionService:
    def __init__(
        self,
        store: CatalogStateStore,
        scopes: ScopeRegistry,
        source_broker: AssetBroker,
        scope_id: str,
        *,
        wheel_path: Path,
        artifacts_path: Path,
        cache_parent: Path,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
    ) -> None:
        self._store = store
        self._scopes = scopes
        self._source_broker = source_broker
        self._scope_id = scope_id
        self._wheel_path = wheel_path.resolve()
        self._artifacts_path = artifacts_path.resolve()
        self._cache_parent = cache_parent.resolve()
        self._manifest_path = manifest_path
        self._scopes.require_capability(scope_id, "read-for-processing")
        _require(self._cache_parent.is_dir(), "docling-cache-parent-unavailable")

    def extract(
        self,
        source_ref_id: str,
        *,
        rights_evidence_state: str,
    ) -> dict[str, Any]:
        catalog_snapshot = self._store.load()
        _require(
            catalog_snapshot is not None,
            "docling-extraction-catalog-required",
        )
        existing_state = catalog_snapshot.payload.get("pdf1c")
        if existing_state is not None:
            validate_pdf1c_state(existing_state, self._scope_id)

        # Source truth and rights are established before Provider preparation or
        # source-byte access.
        source_ref, entry = _resolve_source(
            catalog_snapshot,
            self._scope_id,
            source_ref_id,
        )
        manifest = _load_manifest(self._manifest_path)
        try:
            rights_decision = decide_local_docling_pdf_extraction(
                self._scopes,
                self._scope_id,
                plugin_id=manifest["plugin"]["plugin_id"],
                rights_evidence_state=rights_evidence_state,
            )
        except DoclingPdfRightsError as exc:
            raise DoclingPdfExtractionError(str(exc)) from exc

        try:
            provider = verify_reference_docling(
                wheel_path=self._wheel_path,
                artifacts_path=self._artifacts_path,
            )
        except DoclingReferenceError as exc:
            raise DoclingPdfExtractionError(
                f"docling-reference-provider-unavailable:{exc}"
            ) from exc
        validate_reference_provider_record(provider)

        location = entry["current_location"]
        try:
            source_handle = self._source_broker.issue_read_handle(
                self._scope_id,
                location,
                media_type=PDF_MEDIA_TYPE,
                ttl_seconds=LEASE_SECONDS,
            )
            _require(
                source_handle["fingerprint"] == source_ref["fingerprint"],
                "docling-source-changed-after-discovery",
            )
            _require(
                source_handle["byte_length"] == source_ref["byte_length"],
                "docling-source-length-changed-after-discovery",
            )
            source_bytes = self._source_broker.read_asset(source_handle)
        except CoreAccessError as exc:
            raise DoclingPdfExtractionError(
                f"docling-source-safe-read-failed:{exc}"
            ) from exc

        with tempfile.TemporaryDirectory(
            prefix="raiatea-pdf1c-cache-",
            dir=self._cache_parent,
        ) as cache_temporary:
            cache_root = Path(cache_temporary).resolve()
            with Vs1PluginIO() as plugin_io:
                input_handle = plugin_io.add_input(
                    source_bytes,
                    media_type=PDF_MEDIA_TYPE,
                    ttl_seconds=LEASE_SECONDS,
                )
                _require(
                    input_handle["fingerprint"] == source_ref["fingerprint"],
                    "docling-private-copy-fingerprint-mismatch",
                )
                output_target = plugin_io.issue_output(
                    media_type=DOCLING_OBSERVATION_MEDIA_TYPE,
                    max_byte_length=MAX_PROVIDER_OBSERVATION_BYTES,
                    ttl_seconds=LEASE_SECONDS,
                )
                try:
                    environment = build_docling_extra_env(
                        plugin_io.freeze(),
                        wheel_path=self._wheel_path,
                        artifacts_path=self._artifacts_path,
                        cache_root=cache_root,
                    )
                    with LocalPluginProcessClient(
                        manifest["entrypoint"]["command"],
                        manifest,
                        extra_env=environment,
                        max_invocation_timeout_seconds=PROVIDER_TIMEOUT_SECONDS,
                    ) as client:
                        handshake = client.handshake()
                        request = _request(
                            runtime_instance_id=handshake["identity"]["runtime_instance_id"],
                            scope_id=self._scope_id,
                            rights_decision_ref=rights_decision["decision_id"],
                            source_ref=source_ref,
                            input_handle=input_handle,
                            output_target=output_target,
                        )
                        result = client.invoke(request)
                    plugin_io.verify_broker_unchanged()
                except (
                    DoclingProcessEnvironmentError,
                    LocalPluginProcessError,
                    PluginIOError,
                ) as exc:
                    raise DoclingPdfExtractionError(
                        f"docling-plugin-execution-failed:{exc}"
                    ) from exc
                _require(
                    result.get("status") == "completed",
                    "docling-plugin-result-not-completed",
                )
                completed = _completed_asset(
                    result,
                    output_target["handle_id"],
                )
                try:
                    provider_bytes = plugin_io.read_completed_output(
                        output_target,
                        completed,
                    )
                except PluginIOError as exc:
                    raise DoclingPdfExtractionError(
                        f"docling-plugin-output-invalid:{exc}"
                    ) from exc

        try:
            provider_bundle = json.loads(provider_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DoclingPdfExtractionError(
                "docling-provider-observation-json-invalid"
            ) from exc
        _require(
            docling_json_bytes(provider_bundle) == provider_bytes,
            "docling-provider-observation-not-canonical",
        )
        _validate_provider_result(
            provider_bundle,
            source_ref,
            result,
            rights_decision["decision_id"],
        )
        adapted = _adapt(provider_bundle, source_ref, result)

        try:
            final_source_bytes = self._source_broker.read_asset(source_handle)
        except CoreAccessError as exc:
            raise DoclingPdfExtractionError(
                f"docling-source-changed-during-plugin-run:{exc}"
            ) from exc
        _require(
            len(final_source_bytes) == source_ref["byte_length"]
            and hashlib.sha256(final_source_bytes).hexdigest()
            == source_ref["fingerprint"].removeprefix("sha256:"),
            "docling-source-changed-during-plugin-run",
        )

        payload = deepcopy(catalog_snapshot.payload)
        state = payload.get("pdf1c")
        if state is None:
            state = {
                "state_version": PDF1C_STATE_VERSION,
                "scope_ref": self._scope_id,
                "current_extractions": [],
                "attempts": [],
            }
        else:
            validate_pdf1c_state(state, self._scope_id)
            state = deepcopy(state)

        execution = adapted["run"].get("outcome", {}).get("execution")
        if execution == "completed":
            try:
                e05_bundle = build_docling_pdf_extraction_bundle(
                    source_ref_id=source_ref["source_ref_id"],
                    source_fingerprint=source_ref["fingerprint"],
                    adapted=adapted,
                )
            except DoclingPdfE05ContractError as exc:
                raise DoclingPdfExtractionError(
                    f"docling-current-e05-invalid:{exc}"
                ) from exc
            current = [
                deepcopy(row)
                for row in state["current_extractions"]
                if row["source_ref_id"] != source_ref_id
            ]
            current.append(
                _current_entry(
                    catalog_basis_revision=catalog_snapshot.revision,
                    source_ref=source_ref,
                    rights_decision=rights_decision,
                    manifest=manifest,
                    provider_bundle=provider_bundle,
                    e05_bundle=e05_bundle,
                    provenance=result["provenance"],
                )
            )
            current.sort(key=lambda row: row["source_ref_id"])
            state["current_extractions"] = current
            published = True
        else:
            attempts = list(state["attempts"])
            attempts.append(
                _attempt_entry(
                    catalog_basis_revision=catalog_snapshot.revision,
                    source_ref=source_ref,
                    rights_decision=rights_decision,
                    manifest=manifest,
                    provider_bundle=provider_bundle,
                    adapted=adapted,
                    provenance=result["provenance"],
                )
            )
            attempts.sort(
                key=lambda row: (
                    row["provenance"]["ended_at"],
                    row["attempt_id"],
                )
            )
            state["attempts"] = attempts[-MAX_ATTEMPTS:]
            published = False

        validate_pdf1c_state(state, self._scope_id)
        payload["pdf1c"] = state
        try:
            saved = self._store.save(
                payload,
                expected_revision=catalog_snapshot.revision,
            )
        except CatalogStoreError as exc:
            raise DoclingPdfExtractionError(
                "docling-catalog-changed-during-plugin-run"
            ) from exc

        observation = provider_bundle["observation"]
        return {
            "status": "completed" if published else "observed-not-published",
            "processing_execution": execution,
            "catalog_revision": saved.revision,
            "catalog_basis_revision": catalog_snapshot.revision,
            "source_ref_id": source_ref_id,
            "rights_decision_ref": rights_decision["decision_id"],
            "published_current": published,
            "text_block_count": len(observation["blocks"]),
            "picture_count": len(observation["pictures"]),
            "caption_relation_count": len(observation["picture_caption_relations"]),
        }


__all__ = [
    "DoclingPdfExtractionError",
    "LocalDoclingPdfExtractionService",
    "validate_pdf1c_state",
]
