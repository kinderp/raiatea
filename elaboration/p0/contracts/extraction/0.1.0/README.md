# E-05b candidate extraction contract 0.1.0

Status: **Draft / internal / transport-neutral**.

This directory encodes the accepted E-05a conceptual boundary as a candidate machine-readable contract. It is not yet a public API, database schema, plugin transport, or Provider selection.

## Root record

`processing-run.schema.json` defines one root `ProcessingRunRecord`. The candidate deliberately avoids a universal Provider-shaped document tree.

Required distinctions:

- `ProviderRef` and `RouteProfileRef` are structurally separate;
- Provider-native status is evidence and remains inside an `EvidenceEnvelope`;
- evidence availability (`measured`, `partial`, `not-measured`, ...) is separate from observed value state (`present`, `explicit-empty`, `explicit-mismatch`, `unknown`);
- produced Provider evidence and normalized representations are explicit references outside `ProcessingOutcome`;
- `ProcessingOutcome` is execution plus scoped completeness/integrity assessments with explicit derivation basis;
- `RightsDecisionRef` is a reference to Core-owned policy authority, not a second policy decision inside extraction outcome;
- `SourceCoordinate` is a typed union. PDF geometric and EPUB logical/package coordinates are distinct variants;
- OCR/fallback is an explicit `ProcessingStage` with route/profile identity, trigger basis, parent-stage lineage and reconciliation state;
- relations may be Provider-explicit or Raiatea-derived, but both require an explicit basis.

## Evidence classification

The fields in this first slice are limited to accepted E-05a distinctions:

- **required-by-evidence**: provider + route profile identity, structured execution outcome, scoped assessments, explicit evidence state/value state, produced references, stage lineage, provenance basis;
- **optional-when-provider-exposes**: model revision, payload fingerprint, diagnostics, Provider evidence channel;
- **Raiatea-derived-with-explicit-basis**: scoped completeness/integrity assessments, run derivation basis, fallback trigger basis;
- **provisional/deferred**: stable public resource names, storage identifiers, database keys, transport envelopes and Plugin API methods.

## Examples

- `examples/poppler-native-pdf.json` demonstrates a native PDF route where text completeness can be known while semantic completeness remains unknown.
- `examples/docling-rapidocr-staged.json` demonstrates explicit native + OCR stages, separate route profiles and unresolved native/OCR reconciliation.

These are conformance examples, not production routing policy and not benchmark gold promoted into runtime knowledge.

## Validation

`validate_contract.py` is dependency-light and enforces cross-field semantic invariants. `test_contract.py` includes negative tests against boolean success, unscoped assessment, Provider/route identity collapse, unavailable evidence claiming a present value, OCR fallback without lineage, and duplicate policy authority.

A dedicated CI job also validates the JSON Schema and examples with a pinned standards-compliant JSON Schema implementation. The custom validator remains useful because several E-05 invariants are semantic rather than purely structural.

## Explicitly out of scope

- JSON-RPC/stdin/stdout/HTTP/gRPC;
- plugin manifests, lifecycle, permissions or sandboxing;
- Adapter/ExtractorPlugin implementation;
- Provider selection or first-slice promotion;
- universal quality score;
- database/REST resource design;
- remote Provider authorization;
- rights-policy resolution.
