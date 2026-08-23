# E-05b candidate extraction contract 0.1.0

Status: **Draft / internal / transport-neutral**.

This directory encodes the accepted E-05a conceptual boundary as a candidate machine-readable contract. It is not yet a public API, database schema, plugin transport, storage layout, Provider selection, or first-slice promotion.

## Record boundary

`processing-run.schema.json` keeps one root `ProcessingRunRecord` for orchestration and also defines reusable candidate record shapes under `$defs`:

1. `ProcessingRunRecord` — Provider/route identity, stages, technical outcome, produced references and provenance;
2. `ProviderEvidenceRecord` — Provider-native status, evidence channel/locator/fingerprint, diagnostics and optional non-semantic Provider grouping;
3. `NormalizedRepresentationRecord` — Raiatea-normalized content units, typed Source Coordinates and explicit or derived relations.

The separation is intentional. A run may reference produced evidence/representations without embedding their payloads. E-05b therefore does not prescribe whether a future implementation stores, streams or addresses these records separately.

## Required distinctions

- `ProviderRef` and `RouteProfileRef` are structurally separate;
- Provider-native status is evidence and remains inside an `EvidenceEnvelope`;
- evidence availability (`measured`, `partial`, `not-measured`, ...) is separate from observed value state (`present`, `explicit-empty`, `explicit-mismatch`, `unknown`);
- produced Provider evidence and normalized representations are explicit references outside `ProcessingOutcome`;
- `ProcessingOutcome` is execution plus scoped completeness/integrity assessments with explicit derivation basis;
- `RightsDecisionRef` is a reference to Core-owned policy authority, not a second policy decision inside extraction outcome;
- `SourceCoordinate` is a typed union. PDF geometric and EPUB logical/package coordinates are incompatible variants;
- OCR/fallback is an explicit `ProcessingStage` with route/profile identity, trigger basis, parent-stage lineage and reconciliation state;
- relations may be Provider-explicit or Raiatea-derived, but both require an explicit basis;
- Provider-native groupings may be retained as evidence but are explicitly non-semantic until another evidence-backed step interprets them.

## Evidence classification

| Concept / field | Classification | Evidence basis |
| --- | --- | --- |
| Provider + route/profile identity | required-by-evidence | Poppler controls and Docling native/RapidOCR profiles differ materially |
| evidence state + value state | required-by-evidence | E-04 distinguishes unavailable, partial, explicit-empty, mismatch and malformed evidence |
| Provider evidence channel/locator | required-by-evidence / optional locator | lossless/raw, normalized Provider views and diagnostics expose different facts |
| normalized content units | required-by-evidence | measured Providers segment the same source differently |
| semantic role | optional-when-provider-exposes | several routes preserve surface text without semantic roles |
| PDF `pdf-geometric` coordinate | optional-when-provider-exposes | B-01 Poppler/Docling geometry evidence |
| EPUB `epub-logical` coordinate | optional-when-provider-exposes | B-02 direct-package resource/fragment evidence |
| Provider-explicit relation | optional-when-provider-exposes | links, caption refs and other explicit Provider relations |
| Raiatea-derived relation | Raiatea-derived-with-explicit-basis | reading-order/alignment relations require inspectable derivation |
| ProcessingStage + OCR trigger/lineage | required-by-evidence | B01-PDF-007 native + OCR fallback |
| scoped completeness/integrity | required-by-evidence | Provider success can coexist with incomplete/unknown results |
| assessment basis | required-by-evidence | benchmark gold must not become implicit production runtime knowledge |
| RightsDecisionRef | required-by-evidence as reference only | Core remains the policy authority |
| universal quality score | intentionally absent | E-04 dimensions remain independent |

## Source Coordinates

The contract deliberately does **not** force every source class into page/bbox coordinates:

```text
PDF  -> kind=pdf-geometric, page_index, bbox_points_bottom_left
EPUB -> kind=epub-logical, resource, optional fragment, optional spine_index
```

EPUB content cannot acquire synthetic rendered page numbers merely to fit the PDF model.

## Conformance examples

- `examples/poppler-native-pdf.json` — completed native PDF run with scoped semantic uncertainty;
- `examples/docling-rapidocr-staged.json` — explicit native + OCR fallback stages and unresolved reconciliation;
- `examples/direct-epub-normalized.json` — EPUB logical/package coordinates with no page-number coercion;
- `examples/restricted-access-controlled.json` — restricted terminal run retaining provenance/Provider evidence without a NormalizedRepresentation.

These examples are contract tests, not production routing policy and not benchmark gold promoted into runtime knowledge.

## Mapper adaptation demonstrations

`adapt_benchmark.py` is **benchmark-only proof code**, not an Adapter SDK. It consumes two materially different mapper shapes already used in E-04:

- Poppler `pdftohtml-xml` (`pdf_routes.py`) -> E-05b PDF content units + ProviderEvidenceRecord;
- direct EPUB stdlib mapper (`epub_routes.py`) -> E-05b EPUB logical content units + ProviderEvidenceRecord.

Representative mapper-shaped inputs live under `adapter_inputs/`. The adaptation deliberately drops Provider-native implementation fields such as Poppler `native_bbox` and EPUB container/spine bookkeeping from normalized records. It also never reads benchmark gold, so source-level completeness remains `unknown` unless runtime evidence independently supports a stronger claim.

## Validation

`validate_contract.py` is dependency-light and enforces cross-field semantic invariants for run, Provider evidence and normalized representation records. `test_contract.py` and `test_adapt_benchmark.py` cover positive and negative cases.

Dedicated CI additionally validates the candidate JSON Schema with pinned `jsonschema==4.26.0` Draft 2020-12 support and validates both mapper-adaptation outputs against the same schema definitions. The custom validator remains necessary because several E-05 invariants are semantic rather than purely structural.

## Explicitly out of scope

- JSON-RPC/stdin/stdout/HTTP/gRPC or any transport;
- plugin manifests, lifecycle, permissions or sandboxing;
- Adapter/ExtractorPlugin implementation;
- Provider selection or first-slice promotion;
- universal quality score or universal Provider-shaped document tree;
- database/REST resource design;
- remote Provider authorization;
- rights-policy resolution;
- SourcePlugin/TransformerPlugin contracts.
