#!/usr/bin/env python3
"""Rights-first public product facade for PDF1b Poppler extraction.

The underlying PDF1b orchestrator still revalidates every invocation invariant.
This facade adds two product-level guarantees:

1. denied/review-required requests are resolved from current Source + Core rights
   policy before any local Provider preparation/probe;
2. persisted PDF1b state is accepted only when every retained ProviderObservation
   still identifies the exact Poppler reference build promoted for PDF1b.
"""
from __future__ import annotations

from typing import Any

from prototype.p0_vs1.pdf1b_rights import (
    PdfRightsError,
    decide_local_poppler_pdf_extraction,
)
from prototype.p0_vs1.pdf1b_service import (
    LocalPopplerPdfExtractionService as _ValidatedPopplerOrchestrator,
    PdfExtractionError,
    _load_manifest,
    _resolve_source,
    validate_pdf1b_state as _validate_pdf1b_state,
)
from prototype.p0_vs1.poppler_product_parser import (
    PopplerProductError,
    verify_reference_poppler,
)


def validate_pdf1b_state(value: Any, scope_id: str) -> dict[str, Any]:
    state = _validate_pdf1b_state(value, scope_id)
    for collection in ("current_extractions", "attempts"):
        for row in state[collection]:
            try:
                verify_reference_poppler(row["provider_observation"]["provider"])
            except PopplerProductError as exc:
                raise PdfExtractionError(
                    f"pdf1b-persisted-provider-reference-invalid:{exc}"
                ) from exc
    return state


class LocalPopplerPdfExtractionService(_ValidatedPopplerOrchestrator):
    def extract(self, source_ref_id: str, *, rights_evidence_state: str) -> dict:
        snapshot = self._store.load()
        if snapshot is None:
            raise PdfExtractionError("pdf-extraction-catalog-required")
        existing = snapshot.payload.get("pdf1b")
        if existing is not None:
            validate_pdf1b_state(existing, self._scope_id)
        # Establish that the requested Source is current before evaluating a
        # processing decision. This does not open/read source bytes.
        _resolve_source(snapshot, self._scope_id, source_ref_id)
        manifest = _load_manifest(self._manifest_path)
        try:
            decide_local_poppler_pdf_extraction(
                self._scopes,
                self._scope_id,
                plugin_id=manifest["plugin"]["plugin_id"],
                rights_evidence_state=rights_evidence_state,
            )
        except PdfRightsError as exc:
            raise PdfExtractionError(str(exc)) from exc
        # Allowed requests enter the fully validated orchestrator, which repeats
        # the deterministic RightsDecision and all Provider/source/catalog fences.
        return super().extract(
            source_ref_id,
            rights_evidence_state=rights_evidence_state,
        )


__all__ = [
    "LocalPopplerPdfExtractionService",
    "PdfExtractionError",
    "validate_pdf1b_state",
]
