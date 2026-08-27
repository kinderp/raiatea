#!/usr/bin/env python3
"""Rights-first public product facade for PDF1b Poppler extraction.

The underlying PDF1b orchestrator still revalidates every invariant. This facade
ensures a denied/review-required request is resolved from current Source + Core
rights policy before any local Provider preparation/probe is attempted.
"""
from __future__ import annotations

from prototype.p0_vs1.pdf1b_rights import (
    PdfRightsError,
    decide_local_poppler_pdf_extraction,
)
from prototype.p0_vs1.pdf1b_service import (
    LocalPopplerPdfExtractionService as _ValidatedPopplerOrchestrator,
    PdfExtractionError,
    _load_manifest,
    _resolve_source,
    validate_pdf1b_state,
)


class LocalPopplerPdfExtractionService(_ValidatedPopplerOrchestrator):
    def extract(self, source_ref_id: str, *, rights_evidence_state: str) -> dict:
        snapshot = self._store.load()
        if snapshot is None:
            raise PdfExtractionError("pdf-extraction-catalog-required")
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
