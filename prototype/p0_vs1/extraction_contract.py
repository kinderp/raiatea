#!/usr/bin/env python3
"""VS1d internal wrapper around accepted E-05 extraction records.

E-05 records retain their accepted semantic contract. This module only defines
the bounded product bundle that carries those records across the official local
ExtractorPlugin boundary and enforces VS1d source/route/path invariants.

A VS1d product bundle is deliberately narrower than an arbitrary valid E-05 run:
it is the **publishable current extraction** for the promoted direct EPUB route.
A plugin process may complete while E-05 correctly reports a rejected/failed run;
such evidence is valid E-05 but is not publishable as the current extracted
representation in VS1d.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from prototype.p0_vs1.source_contract import canonical_json_bytes


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
E05_VALIDATOR_PATH = (
    REPO_ROOT
    / "elaboration"
    / "p0"
    / "contracts"
    / "extraction"
    / "0.1.0"
    / "validate_contract.py"
)
_E05_SPEC = importlib.util.spec_from_file_location("vs1d_e05_validator", E05_VALIDATOR_PATH)
E05 = importlib.util.module_from_spec(_E05_SPEC)
assert _E05_SPEC.loader is not None
_E05_SPEC.loader.exec_module(E05)


EXTRACTION_BUNDLE_VERSION = "raiatea.vs1d.e05-bundle.0.1.0"
EXTRACTION_BUNDLE_MEDIA_TYPE = "application/vnd.raiatea.vs1d-e05-bundle+json"
E05_CONTRACT_ID = "raiatea.extraction.processing-run"
E05_CONTRACT_VERSION = "0.1.0"
EXPECTED_PROVIDER_ID = "python-stdlib"
EXPECTED_ROUTE_PROFILE = "direct-epub-stdlib"
FORBIDDEN_PATH_KEYS = frozenset(
    {"path", "filepath", "file_path", "filename", "root", "relative_path", "location", "location_history"}
)


class ExtractionContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionContractError(message)


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label}-must-be-object")
    actual = set(value)
    missing = sorted(keys - actual)
    extra = sorted(actual - keys)
    _require(not missing, f"{label}-missing-field:{missing[0] if missing else ''}")
    _require(not extra, f"{label}-unknown-field:{extra[0] if extra else ''}")
    return value


def _walk_no_path_authority(value: Any, *, trail: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            _require(
                normalized not in FORBIDDEN_PATH_KEYS,
                f"extraction-bundle-path-field-forbidden:{trail}.{key}",
            )
            _walk_no_path_authority(child, trail=f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_no_path_authority(child, trail=f"{trail}[{index}]")


def _record_ref(ref_id: str, record_kind: str) -> dict[str, Any]:
    return {
        "ref_id": ref_id,
        "contract_id": E05_CONTRACT_ID,
        "contract_version": E05_CONTRACT_VERSION,
        "record_kind": record_kind,
    }


def build_extraction_bundle(
    *,
    source_ref_id: str,
    source_fingerprint: str,
    adapted: dict[str, Any],
) -> dict[str, Any]:
    _require(isinstance(source_ref_id, str) and source_ref_id.startswith("source-ref:"), "extraction-source-ref-id-invalid")
    _require(isinstance(source_fingerprint, str) and source_fingerprint.startswith("sha256:"), "extraction-source-fingerprint-invalid")
    run = adapted.get("run")
    evidence = adapted.get("provider_evidence")
    representation = adapted.get("normalized_representation")
    _require(isinstance(run, dict), "extraction-run-required")
    _require(isinstance(evidence, dict), "extraction-provider-evidence-required")

    refs = [
        _record_ref(str(run.get("run_id")), "ProcessingRunRecord"),
        _record_ref(str(evidence.get("evidence_id")), "ProviderEvidenceRecord"),
    ]
    records: dict[str, Any] = {
        refs[0]["ref_id"]: run,
        refs[1]["ref_id"]: evidence,
    }
    if isinstance(representation, dict):
        ref = _record_ref(str(representation.get("representation_id")), "NormalizedRepresentationRecord")
        refs.append(ref)
        records[ref["ref_id"]] = representation
    refs.sort(key=lambda row: row["ref_id"])
    bundle = {
        "bundle_version": EXTRACTION_BUNDLE_VERSION,
        "record_kind": "E05ExtractionBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": source_fingerprint,
        "record_refs": refs,
        "records": records,
    }
    validate_extraction_bundle(bundle)
    return bundle


def _validate_e05_record(kind: str, record: dict[str, Any]) -> None:
    try:
        if kind == "ProcessingRunRecord":
            E05.validate(record)
        elif kind == "ProviderEvidenceRecord":
            E05.validate_provider_evidence(record)
        elif kind == "NormalizedRepresentationRecord":
            E05.validate_representation(record)
        else:
            raise ExtractionContractError("extraction-record-kind-unsupported")
    except ExtractionContractError:
        raise
    except Exception as exc:
        raise ExtractionContractError(f"extraction-e05-semantic-invalid:{kind}:{exc}") from exc


def _validate_source_binding(record: dict[str, Any], source_ref_id: str, fingerprint: str, label: str) -> None:
    source = record.get("source_ref")
    _require(isinstance(source, dict), f"{label}-source-ref-required")
    _require(source.get("source_id") == source_ref_id, f"{label}-source-id-mismatch")
    _require(source.get("source_class") == "B-02", f"{label}-source-class-invalid")
    _require(source.get("fingerprint") == fingerprint, f"{label}-source-fingerprint-mismatch")


def _validate_route(evidence: dict[str, Any]) -> None:
    provider = evidence.get("provider")
    route = evidence.get("route_profile")
    _require(isinstance(provider, dict) and provider.get("provider_id") == EXPECTED_PROVIDER_ID, "extraction-provider-invalid")
    _require(isinstance(route, dict) and route.get("route_profile_id") == EXPECTED_ROUTE_PROFILE, "extraction-route-profile-invalid")
    _require(route.get("execution_context") == "local", "extraction-route-must-be-local")


def _validate_epub_coordinates(representation: dict[str, Any]) -> None:
    for index, unit in enumerate(representation.get("units", [])):
        _require(isinstance(unit, dict), f"extraction-unit-{index}-invalid")
        coordinate = unit.get("coordinate")
        _require(isinstance(coordinate, dict), f"extraction-unit-{index}-coordinate-required")
        if coordinate.get("value_state") != "populated":
            continue
        value = coordinate.get("value")
        _require(isinstance(value, dict), f"extraction-unit-{index}-coordinate-value-invalid")
        _require(value.get("kind") == "epub-logical", f"extraction-unit-{index}-coordinate-kind-invalid")
        _require("page_index" not in value, f"extraction-unit-{index}-invented-page-index-forbidden")
        _require("bbox_points_bottom_left" not in value, f"extraction-unit-{index}-invented-pdf-bbox-forbidden")
        _require(isinstance(value.get("resource"), str) and value.get("resource"), f"extraction-unit-{index}-resource-required")


def validate_extraction_bundle(value: Any) -> dict[str, Any]:
    bundle = _exact(
        value,
        {"bundle_version", "record_kind", "source_ref_id", "source_fingerprint", "record_refs", "records"},
        "extraction-bundle",
    )
    _require(bundle["bundle_version"] == EXTRACTION_BUNDLE_VERSION, "extraction-bundle-version-unsupported")
    _require(bundle["record_kind"] == "E05ExtractionBundle", "extraction-bundle-kind-invalid")
    source_ref_id = bundle["source_ref_id"]
    fingerprint = bundle["source_fingerprint"]
    _require(isinstance(source_ref_id, str) and source_ref_id.startswith("source-ref:"), "extraction-source-ref-id-invalid")
    _require(isinstance(fingerprint, str) and fingerprint.startswith("sha256:") and len(fingerprint) == 71, "extraction-source-fingerprint-invalid")

    refs = bundle["record_refs"]
    records = bundle["records"]
    _require(isinstance(refs, list) and 2 <= len(refs) <= 3, "extraction-record-ref-count-invalid")
    _require(isinstance(records, dict), "extraction-record-map-invalid")
    ids: list[str] = []
    kinds: dict[str, str] = {}
    for ref in refs:
        row = _exact(ref, {"ref_id", "contract_id", "contract_version", "record_kind"}, "extraction-record-ref")
        ref_id = row["ref_id"]
        _require(isinstance(ref_id, str) and ref_id, "extraction-record-ref-id-required")
        _require(ref_id not in ids, "extraction-record-ref-duplicate")
        _require(row["contract_id"] == E05_CONTRACT_ID, "extraction-record-ref-contract-invalid")
        _require(row["contract_version"] == E05_CONTRACT_VERSION, "extraction-record-ref-version-invalid")
        _require(row["record_kind"] in {"ProcessingRunRecord", "ProviderEvidenceRecord", "NormalizedRepresentationRecord"}, "extraction-record-ref-kind-invalid")
        ids.append(ref_id)
        kinds[ref_id] = row["record_kind"]
    _require(ids == sorted(ids), "extraction-record-refs-not-canonical-order")
    _require(set(records) == set(ids), "extraction-record-map-mismatch")
    _require(list(kinds.values()).count("ProcessingRunRecord") == 1, "extraction-processing-run-count-invalid")
    _require(list(kinds.values()).count("ProviderEvidenceRecord") == 1, "extraction-provider-evidence-count-invalid")
    _require(list(kinds.values()).count("NormalizedRepresentationRecord") <= 1, "extraction-normalized-count-invalid")

    run: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    representation: dict[str, Any] | None = None
    for ref_id in ids:
        record = records[ref_id]
        _require(isinstance(record, dict), "extraction-record-must-be-object")
        kind = kinds[ref_id]
        _validate_e05_record(kind, record)
        _validate_source_binding(record, source_ref_id, fingerprint, kind)
        if kind == "ProcessingRunRecord":
            _require(record.get("run_id") == ref_id, "extraction-run-ref-id-mismatch")
            run = record
        elif kind == "ProviderEvidenceRecord":
            _require(record.get("evidence_id") == ref_id, "extraction-evidence-ref-id-mismatch")
            evidence = record
        else:
            _require(record.get("representation_id") == ref_id, "extraction-representation-ref-id-mismatch")
            representation = record

    _require(run is not None and evidence is not None, "extraction-required-records-missing")
    # Runtime completion and E-05 execution outcome are intentionally separate.
    # Only a completed E-05 run with a normalized representation can become the
    # current publishable VS1d extraction. Rejected/failed E-05 evidence remains
    # valid evidence, but is not silently promoted into catalog content.
    outcome = run.get("outcome")
    _require(isinstance(outcome, dict), "extraction-run-outcome-required")
    _require(outcome.get("execution") == "completed", "extraction-run-not-publishable")
    _require(representation is not None, "extraction-normalized-representation-required")
    _validate_route(evidence)
    _validate_epub_coordinates(representation)
    _walk_no_path_authority(bundle)
    canonical_json_bytes(bundle)
    return bundle


def canonical_extraction_bundle_bytes(bundle: dict[str, Any]) -> bytes:
    validate_extraction_bundle(bundle)
    return canonical_json_bytes(bundle)
