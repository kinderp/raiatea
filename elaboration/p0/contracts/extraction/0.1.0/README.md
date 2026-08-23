# E-05b candidate extraction contract 0.1.0

Status: **Draft / internal / transport-neutral**.

This directory encodes the accepted E-05a conceptual boundary as a candidate machine-readable contract. It is not yet a public API, database schema, plugin transport, storage layout, Provider selection, or first-slice promotion.

## Record boundary

`processing-run.schema.json` keeps one root `ProcessingRunRecord` for Core orchestration and also defines reusable candidate record shapes under `$defs`:

1. `ProcessingRunRecord` — source/run identity, ordered stages, Core technical outcome, produced references, rights-decision reference and provenance;
2. `ProviderEvidenceRecord` — Provider + route/profile identity, Provider-native status, evidence channel/locator/fingerprint, diagnostics and optional non-semantic Provider grouping;
3. `NormalizedRepresentationRecord` — Raiatea-normalized content units, typed Source Coordinates and explicit or derived relations.

Provider identity is deliberately **not** mandatory on the run. A run may terminate before any Provider is selected or invoked. Provider/route identity is attached to Provider-backed stage executors and ProviderEvidence records.

The record separation does not prescribe whether a future implementation stores, streams or addresses these records separately.

## Processing stages and ownership

Each stage has an explicit `executor`:

```text
provider
  └── ProviderRef + RouteProfileRef + Provider-native status

raiatea-core
  └── operation_id; no Provider-native status
```

Provider-backed stages and Core stages both carry a separate `ProcessingOutcome`. Provider-native status is therefore never mechanically promoted to either stage outcome or run outcome.

Core-owned `normalization` / `alignment` stages consume explicit previously produced references. A `NormalizedRepresentationRef` is valid only when produced by a Core normalization/alignment stage with non-empty input lineage. Provider-native extraction cannot directly claim a Raiatea normalized representation.

The run-level `ProcessingOutcome` remains a Core orchestration assessment with its own derivation basis. A run with no stages and no produced outputs is valid, for example when an authoritative Core rights gate terminates processing before Provider selection.

## EvidenceEnvelope semantics

Evidence availability, observed value, epistemic origin and Provider channel are separate axes.

Candidate machine states:

```text
EvidenceState:
  measured | partial | not-measured | malformed-evidence | ambiguous | not-applicable

ValueState:
  present | explicit-empty | unknown

EvidenceOrigin:
  provider-native | raiatea-aligned | raiatea-derived | user-asserted | unresolved
```

`channel` describes where Provider evidence was observed (`lossless/raw`, normalized Provider view, diagnostic stream, etc.); it never substitutes for `origin`.

A trustworthy empty collection is `evidence_state=measured`, `value_state=explicit-empty`, with its actual empty value. For a singular SourceCoordinate the explicit empty value is `null`.

**Mismatch is not a ValueState.** When two available facts are compared, mismatch/consistency belongs to an optional `EvidenceAssessment` carrying its own basis and optional compared-to reference. An unavailable or malformed fact cannot be declared a proven mismatch.

## Policy and technical outcome are separate

`ProcessingOutcome.execution` is technical/orchestration state (`not-started`, `completed`, `failed`, `rejected`, `unsupported`, `cancelled`, `timeout`, `unknown`). It does not contain a `restricted` policy state.

Authoritative permission/restriction remains Core-owned through `RightsDecisionRef`. Therefore:

- a run stopped by policy before Provider invocation is technically `not-started` plus a RightsDecisionRef;
- a Provider attempt that fails on an access-controlled artifact remains technically `failed`, while the RightsDecisionRef/diagnostics preserve the authorization boundary;
- no extractor or ProcessingOutcome becomes a second rights-policy authority.

## Required distinctions

- `ProviderRef` and `RouteProfileRef` are structurally separate;
- Provider/route identity is stage/evidence scoped, not unconditional run identity;
- Provider-native status, stage outcome and run outcome are three distinct concepts;
- evidence availability, observed value, epistemic origin, channel and comparison assessment are distinct concepts;
- produced Provider evidence and normalized representations are explicit references outside `ProcessingOutcome`;
- stage `input_refs` must refer to outputs of earlier stages, making normalization derivation inspectable;
- `RightsDecisionRef` is a reference to Core-owned policy authority, not a policy field inside extraction outcome;
- `SourceCoordinate` is a typed union. PDF geometric and EPUB logical/package coordinates are incompatible variants;
- OCR/fallback is an explicit Provider-backed stage with trigger basis, parent-stage lineage and reconciliation state;
- relations may be Provider-explicit or Raiatea-derived, but both require an explicit basis;
- Provider-native groupings may be retained as evidence but remain explicitly non-semantic until another evidence-backed step interprets them.

## Evidence classification

| Concept / field | Classification | Evidence basis |
| --- | --- | --- |
| Provider + route/profile identity | required-by-evidence where Provider-backed | Poppler controls and Docling native/RapidOCR profiles differ materially |
| provider/core stage executor distinction | required by accepted E-05a ownership boundary | Raiatea Core owns normalization/alignment; Providers own route execution evidence |
| stage outcome distinct from Provider status | required-by-evidence | Provider native `success` may coexist with Raiatea-invalid/degraded assessment |
| run outcome distinct from stage outcome | required-by-evidence | overall orchestration is not last-stage/worst-stage aggregation |
| evidence state + value state | required-by-evidence | E-04 distinguishes unavailable, partial and explicit-empty evidence |
| evidence origin separate from channel | required by E-05a I-04/I-05 | Provider-native facts may be read through different channels; Raiatea may align/derive others |
| mismatch as assessment | required by E-05a §7.4 | comparison/conflict is not evidence availability or value cardinality |
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

- `examples/poppler-native-pdf.json` — Provider extraction followed by explicit Core normalization;
- `examples/docling-rapidocr-staged.json` — native Provider stage, OCR fallback Provider stage, then Core normalization with unresolved reconciliation;
- `examples/direct-epub-normalized.json` — EPUB logical/package coordinates with no page-number coercion;
- `examples/restricted-access-controlled.json` — Provider invocation technically fails on access-controlled input; RightsDecisionRef preserves the authorization boundary and no normalization occurs;
- `examples/restricted-before-provider.json` — technical execution is `not-started` because the Core rights gate terminates the run before any Provider stage starts.

These examples are contract tests, not production routing policy and not benchmark gold promoted into runtime knowledge.

## Mapper adaptation demonstrations

`adapt_benchmark.py` is **benchmark-only proof code**, not an Adapter SDK. It consumes two materially different mapper shapes already used in E-04:

- Poppler `pdftohtml-xml` (`pdf_routes.py`) -> ProviderEvidenceRecord -> Core normalization -> PDF geometric NormalizedRepresentationRecord;
- direct EPUB stdlib mapper (`epub_routes.py`) -> ProviderEvidenceRecord -> Core normalization -> EPUB logical NormalizedRepresentationRecord.

Representative mapper-shaped inputs live under `adapter_inputs/`. The adaptation deliberately drops Provider-native implementation fields such as Poppler `native_bbox` and EPUB container/spine bookkeeping from normalized records. It never reads benchmark gold, so source-level completeness remains `unknown` unless runtime evidence independently supports a stronger claim.

For Poppler, the text surface remains `origin=provider-native`, while conversion from Poppler's native top-left scaled coordinates into canonical bottom-left PDF points is explicitly `origin=raiatea-aligned`. This demonstrates why origin and Provider channel cannot be the same field.

## Validation

`validate_contract.py` is dependency-light and enforces cross-field semantic invariants for run, Provider evidence and normalized representation records. It also checks stage ordering, single producer identity, prior-output input references, Core normalization lineage, Provider/Core executor boundaries, evidence origin semantics and mismatch-assessment validity.

`test_contract.py` and `test_adapt_benchmark.py` cover positive and negative cases. Dedicated CI additionally validates the JSON Schema with pinned `jsonschema==4.26.0` Draft 2020-12 support and validates both mapper-adaptation outputs against the same schema definitions.

## Explicitly out of scope

- JSON-RPC/stdin/stdout/HTTP/gRPC or any transport;
- plugin manifests, lifecycle, permissions or sandboxing;
- production Adapter/ExtractorPlugin implementation;
- Provider selection or first-slice promotion;
- universal quality score or universal Provider-shaped document tree;
- database/REST resource design;
- remote Provider authorization;
- rights-policy resolution;
- SourcePlugin/TransformerPlugin contracts.
