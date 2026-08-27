#!/usr/bin/env python3
"""PDF1b bounded wrapper around accepted E-05 records for current Poppler PDF content."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from prototype.p0_vs1.source_contract import canonical_json_bytes


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
E05_VALIDATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "contracts" / "extraction" / "0.1.0" / "validate_contract.py"
_SPEC = importlib.util.spec_from_file_location("pdf1b_e05_validator", E05_VALIDATOR_PATH)
E05 = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(E05)

PDF1B_BUNDLE_VERSION = "raiatea.pdf1b.e05-bundle.0.1.0"
E05_CONTRACT_ID = "raiatea.extraction.processing-run"
E05_CONTRACT_VERSION = "0.1.0"


class PdfE05ContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PdfE05ContractError(message)


def _record_ref(ref_id: str, record_kind: str) -> dict[str, Any]:
    return {
        "ref_id": ref_id,
        "contract_id": E05_CONTRACT_ID,
        "contract_version": E05_CONTRACT_VERSION,
        "record_kind": record_kind,
    }


def validate_attempt_records(adapted: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(adapted, dict), "pdf-e05-adapted-must-be-object")
    run = adapted.get("run")
    evidence = adapted.get("provider_evidence")
    representation = adapted.get("normalized_representation")
    _require(isinstance(run, dict), "pdf-e05-run-required")
    _require(isinstance(evidence, dict), "pdf-e05-provider-evidence-required")
    try:
        E05.validate(run)
        E05.validate_provider_evidence(evidence)
        if representation is not None:
            _require(isinstance(representation, dict), "pdf-e05-representation-invalid")
            E05.validate_representation(representation)
    except PdfE05ContractError:
        raise
    except Exception as exc:
        raise PdfE05ContractError(f"pdf-e05-semantic-invalid:{exc}") from exc
    for label, record in (("run", run), ("evidence", evidence)):
        source = record.get("source_ref")
        _require(isinstance(source, dict), f"pdf-e05-{label}-source-required")
        _require(source.get("source_class") == "B-01", f"pdf-e05-{label}-source-class-invalid")
    provider = evidence.get("provider")
    route = evidence.get("route_profile")
    _require(isinstance(provider, dict) and provider.get("provider_id") == "poppler", "pdf-e05-provider-invalid")
    _require(isinstance(route, dict) and route.get("route_profile_id") == "pdf-poppler-pdftohtml-xml", "pdf-e05-route-invalid")
    _require(route.get("execution_context") == "local", "pdf-e05-route-not-local")
    if representation is not None:
        for index, unit in enumerate(representation.get("units", [])):
            coordinate = unit.get("coordinate") if isinstance(unit, dict) else None
            _require(isinstance(coordinate, dict), f"pdf-e05-unit-{index}-coordinate-required")
            if coordinate.get("value_state") != "populated":
                continue
            value = coordinate.get("value")
            _require(isinstance(value, dict), f"pdf-e05-unit-{index}-coordinate-value-invalid")
            _require(value.get("kind") == "pdf-geometric", f"pdf-e05-unit-{index}-coordinate-kind-invalid")
            _require(isinstance(value.get("page_index"), int), f"pdf-e05-unit-{index}-page-index-required")
            bbox = value.get("bbox_points_bottom_left")
            _require(isinstance(bbox, list) and len(bbox) == 4, f"pdf-e05-unit-{index}-bbox-required")
            _require("resource" not in value and "fragment" not in value, f"pdf-e05-unit-{index}-epub-coordinate-forbidden")
    return adapted


def build_pdf_extraction_bundle(
    *,
    source_ref_id: str,
    source_fingerprint: str,
    adapted: dict[str, Any],
) -> dict[str, Any]:
    validate_attempt_records(adapted)
    run = adapted["run"]
    evidence = adapted["provider_evidence"]
    representation = adapted.get("normalized_representation")
    _require(run.get("outcome", {}).get("execution") == "completed", "pdf-e05-run-not-publishable")
    _require(isinstance(representation, dict), "pdf-e05-normalized-representation-required")
    source = run.get("source_ref", {})
    _require(source.get("source_id") == source_ref_id, "pdf-e05-source-id-mismatch")
    _require(source.get("fingerprint") == source_fingerprint, "pdf-e05-source-fingerprint-mismatch")
    refs = [
        _record_ref(run["run_id"], "ProcessingRunRecord"),
        _record_ref(evidence["evidence_id"], "ProviderEvidenceRecord"),
        _record_ref(representation["representation_id"], "NormalizedRepresentationRecord"),
    ]
    refs.sort(key=lambda row: row["ref_id"])
    records = {
        run["run_id"]: run,
        evidence["evidence_id"]: evidence,
        representation["representation_id"]: representation,
    }
    bundle = {
        "bundle_version": PDF1B_BUNDLE_VERSION,
        "record_kind": "PdfE05ExtractionBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": source_fingerprint,
        "record_refs": refs,
        "records": records,
    }
    validate_pdf_extraction_bundle(bundle)
    return bundle


def validate_pdf_extraction_bundle(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "pdf-e05-bundle-must-be-object")
    expected = {"bundle_version", "record_kind", "source_ref_id", "source_fingerprint", "record_refs", "records"}
    _require(set(value) == expected, "pdf-e05-bundle-shape-invalid")
    _require(value["bundle_version"] == PDF1B_BUNDLE_VERSION, "pdf-e05-bundle-version-unsupported")
    _require(value["record_kind"] == "PdfE05ExtractionBundle", "pdf-e05-bundle-kind-invalid")
    _require(isinstance(value["source_ref_id"], str) and value["source_ref_id"].startswith("source-ref:"), "pdf-e05-source-ref-invalid")
    fingerprint = value["source_fingerprint"]
    _require(isinstance(fingerprint, str) and fingerprint.startswith("sha256:") and len(fingerprint) == 71, "pdf-e05-source-fingerprint-invalid")
    refs = value["record_refs"]
    records = value["records"]
    _require(isinstance(refs, list) and len(refs) == 3, "pdf-e05-record-ref-count-invalid")
    _require(isinstance(records, dict), "pdf-e05-records-invalid")
    ids = [row.get("ref_id") for row in refs if isinstance(row, dict)]
    _require(len(ids) == 3 and ids == sorted(ids) and len(set(ids)) == 3, "pdf-e05-record-ref-order-invalid")
    _require(set(records) == set(ids), "pdf-e05-record-map-mismatch")
    kinds = {row["record_kind"]: row["ref_id"] for row in refs}
    _require(set(kinds) == {"ProcessingRunRecord", "ProviderEvidenceRecord", "NormalizedRepresentationRecord"}, "pdf-e05-record-kinds-invalid")
    adapted = {
        "run": records[kinds["ProcessingRunRecord"]],
        "provider_evidence": records[kinds["ProviderEvidenceRecord"]],
        "normalized_representation": records[kinds["NormalizedRepresentationRecord"]],
    }
    validate_attempt_records(adapted)
    _require(adapted["run"].get("outcome", {}).get("execution") == "completed", "pdf-e05-run-not-current")
    for record in adapted.values():
        source = record.get("source_ref", {})
        _require(source.get("source_id") == value["source_ref_id"], "pdf-e05-record-source-id-mismatch")
        _require(source.get("fingerprint") == fingerprint, "pdf-e05-record-source-fingerprint-mismatch")
    canonical_json_bytes(value)
    return value
