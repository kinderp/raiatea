# E-04 Evidence Synthesis for E-05

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 1.0.0
>
> Last reviewed: 23 August 2026
>
> E-05a child issue: [#160](https://github.com/kinderp/raiatea/issues/160)
>
> E-05 parent: [#159](https://github.com/kinderp/raiatea/issues/159)
>
> E-04 evidence parent: [#129](https://github.com/kinderp/raiatea/issues/129)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Accepted B-01 evidence through: [PR #158](https://github.com/kinderp/raiatea/pull/158) / `c8a6d237`
>
> Rights gate: [#131](https://github.com/kinderp/raiatea/issues/131) remains independent and fail-closed

## 1. Purpose

E-04 measured Provider routes against Provider-neutral B-01 PDF and B-02 EPUB
fixtures. E-05 converts those observations into **requirements on Raiatea-owned
extraction semantics** without copying benchmark JSON or a Provider-native schema
into the product contract.

```text
E-04 fixtures + raw Provider evidence + benchmark normalization
                              │
                              ▼
                  evidence-derived requirements
                              │
                              ▼
          E-05 conceptual extraction contract
```

This document records which distinctions measured routes proved Raiatea must
preserve and which ideas remain optional, derived or deferred.

It does not select a Provider, promote the first slice, define a public schema,
prescribe persistence, or define Plugin API transport.

## 2. Requirement classification

### `required-by-evidence`

Accepted observations show that collapsing the distinction would lose measured
information, hide degradation or create an unsafe interpretation.

### `optional-when-provider-exposes`

The concept is observed and useful, but every route need not provide it.

### `raiatea-derived-with-explicit-basis`

Raiatea may align/reconcile/derive the fact, but the result records its basis and
must never look Provider-native when it is not.

### `provisional/deferred`

Current evidence does not justify freezing the concept in the base P0 contract.

These classes describe requirements, not Provider rankings. No universal score
is introduced.

## 3. Accepted evidence inventory

### 3.1 B-01 PDF

The bounded B-01 evidence covers:

- clean born-digital text and page geometry;
- multi-column reading order;
- semantic structure, lists, code-like content and links;
- figures, raster identity, geometry and caption association;
- tables, explicit/degraded topology and cell identity;
- formula surface, token geometry and explicit mathematical relations;
- mixed/defective native text plus a separately pinned OCR-capable route;
- malformed and access-controlled negatives outside quality averages.

Compact evidence is retained under [`benchmark/evidence/`](benchmark/evidence/)
and its pinned Poppler, Tika and Docling reference records.

### 3.2 B-02 EPUB

Accepted B-02 evidence from [PR #134](https://github.com/kinderp/raiatea/pull/134)
compares a package-aware direct stdlib route with local Pandoc.

Measured facts include:

- B02-EPUB-001 direct text `4/4`, full-exact logical/package coordinates `4/4`,
  reading order `3/3`;
- Pandoc text `4/4`, full-exact coordinates `0/4`, only `2/4` traceable;
- B02-EPUB-002 direct navigation `2/2`, authored link target `1/1`;
- Pandoc navigation `0/2`, semantic link `1/1`, authored target exact `0/1`;
- traversal-member negative: direct route rejects, measured Pandoc route accepts
  without expected reject/degrade signal;
- no observed side effect is only partial security evidence.

B-02 remains incomplete for images/captions/alt, footnotes/endnotes, semantic
table/code/MathML, broader composites and malformed/missing-resource cases.
Those gaps remain visible.

## 4. Evidence-to-requirement matrix

| Requirement | Classification | Evidence | E-05 consequence |
| --- | --- | --- | --- |
| Provider and route/profile identity are separate | `required-by-evidence` | Poppler controls differ; Docling native and Docling+RapidOCR differ | Preserve ProviderRef and RouteProfileRef independently with material mode/model/backend identity |
| Provider-native status is not Raiatea outcome truth | `required-by-evidence` | native B01-PDF-007 succeeds while visible content is missing; Tika succeeds on malformed NEG-001 | Preserve Provider status as evidence; normalize Raiatea execution and scoped result assessments separately |
| ProcessingOutcome and produced-output evidence are separate | `required-by-evidence` | negative routes may emit diagnostics/raw evidence while content collections are empty/unavailable; normalization may produce no representation | Run/stage carry explicit produced-output references/evidence; global outcome does not encode collection cardinality |
| Evidence state and evidence value are separate | `required-by-evidence` | E-04 distinguishes not-measured from trustworthy explicit-empty collections | Explicit empty = present evidence with empty value; unavailable evidence is distinct |
| Missing evidence is not zero or success | `required-by-evidence` | figure/table/formula/coordinate dimensions are often unavailable on otherwise successful routes | Preserve unavailable/partial/ambiguous/malformed/not-applicable states explicitly |
| Surface content and semantic interpretation are separate | `required-by-evidence` | PDF-003 text `8/8` while semantic roles/levels vary | Content, semantic role and semantic relations remain independent |
| Provider-native grouping is not automatically Raiatea semantics | `optional-when-provider-exposes` | Docling formula fixture has non-semantic picture grouping | Retain grouping evidence without coercing it into formula/figure semantics |
| Provider-native origin and Provider evidence channel are separate | `required-by-evidence` | useful explicit fields may exist only in lossless/raw Provider output | Origin remains Provider-native; raw/lossless/metadata/diagnostic channel is separate provenance |
| Relations need explicit evidence or explicit Raiatea derivation basis | `required-by-evidence` | figure↔caption, links, table topology, formula relations vary independently | Relation endpoints/type/origin are explicit; proximity/list position cannot masquerade as Provider-native relation evidence |
| Ambiguous identity cannot fall back to list position | `required-by-evidence` | figure/table review findings | Preserve ambiguous/unresolved identity and inspectable alignment basis |
| Text preservation does not imply table topology | `required-by-evidence` | PDF-005 text preserved while topology absent/degraded | Table presence, topology, binding, roles, content and geometry are separate optional evidence |
| Formula surface does not imply math semantics | `required-by-evidence` | PDF-006 surface/order preserved while superscript/fraction relations unavailable | Formula surface/token evidence and math relation evidence remain separate |
| Source Coordinates are source-class-specific | `required-by-evidence` | PDF page geometry vs EPUB package/resource/fragment | Extensible coordinate family with distinct PDF/EPUB variants |
| Coordinates can be partial per route/unit | `required-by-evidence` | Tika lacks PDF bbox; Pandoc EPUB has partial traceability | Coordinates carry evidence state/origin rather than being universally mandatory |
| Provider evidence and Raiatea normalization are separate | `required-by-evidence` | lossless fields and bounded alignments differ from convenience mappings | Preserve ProviderEvidence/Raw Extraction and NormalizedRepresentation separately |
| OCR/fallback is an explicit stage | `required-by-evidence` | native stage incomplete; locked RapidOCR gives partial reordered recovery | Native/OCR stages retain trigger, route/profile and lineage |
| Native/OCR reconciliation may be unresolved | `required-by-evidence` | measured output does not prove per-block native/OCR origin | No destructive merge without identity evidence |
| Exact and partial recovery are separate | `required-by-evidence` | RapidOCR token multiset right, authored order wrong | Partial/mismatch evidence stays useful without becoming exact recovery |
| Completeness and integrity are scoped, not universal | `required-by-evidence` | text may be preserved while figures/table/formula/coordinate dimensions are unavailable/degraded | ProcessingOutcome uses scoped assessments tied to declared request/capability/evidence-family scope and runtime basis |
| Restricted/requires-authorization is a valid terminal Core decision | `required-by-evidence` | access-controlled route evidence + accepted rights boundary | Core policy can terminate processing; refusal is not an extractor retry hint |
| Core policy authority and technical ProcessingOutcome are separate | `required-by-evidence` | E-01/E-03/#131 authority boundary; E-04 technical failures may merely reflect restriction | ProcessingOutcome stays technical/orchestration; authoritative disposition comes from RightsDecisionRef/Core policy |
| Security evidence may be partial/unavailable | `required-by-evidence` | B02 traversal case has no observed side effect but cannot prove all safety properties | Preserve measured scope; absence of observation is not proof |
| ProcessingRun may exist without Provider stage/NormalizedRepresentation | `required-by-evidence` plus accepted rights boundary | failed/restricted attempts retain provenance; Core can deny before invocation | Record not-started/equivalent reason and policy context without fabricating ProviderEvidence |
| Stage outcome and run outcome are distinct | `required-by-evidence` | native+OCR+normalization can have different outcomes | Run outcome is explicit Core orchestration assessment, never implicit last/worst-stage aggregation |
| Benchmark truth is not production runtime knowledge | `required-by-evidence` | E-04 gold identifies malformed/incomplete fixtures; production does not automatically possess that gold | Gold shapes contract/conformance tests; runtime completeness/integrity claims need explicit runtime basis |
| Rights evidence and RightsDecision are separate | `required-by-evidence` | E-01/E-03/#131 | Provider/plugin/source may report evidence; Core owns decision |
| No universal extraction quality score | `required-by-evidence` | E-04 keeps quality/security/resource dimensions separate | Contract carries facts/outcomes, not one Provider score |
| Route quality may reference benchmark evidence | `provisional/deferred` | versioned E-04 observations exist while selection gates remain open | Future routing may reference QualityProfile evidence; base payload does not embed benchmark score fields |
| One mandatory universal document tree | `provisional/deferred` | segmentation/structure differ by Provider | Prefer composable units/relations/evidence |

## 5. Cross-cutting conclusions

### 5.1 Route/profile is the unit of capability

Capability is a property of at least:

```text
Provider + version
Route/Profile + version
Mode/backend
Model/revision/payload when applicable
Material parameters
Relevant execution context
```

The later Plugin API may advertise these capabilities but must not collapse them
to plugin brand flags.

### 5.2 Outcome and evidence answer different questions

The contract needs separate answers to:

1. Was execution started and how did it terminate?
2. What output/evidence references were actually produced?
3. For each evidence collection/fact, is evidence present, partial, unavailable,
   ambiguous or malformed?
4. If evidence exists, is the observed value populated or explicitly empty?
5. For each declared result scope, is completeness complete/partial/not
   established and integrity established/degraded/invalid/not established?
6. What runtime basis supports each scoped result assessment?
7. What authoritative Core RightsDecision/policy context applies?

`ProcessingOutcome` addresses execution plus scoped result assessments. Output
cardinality and field-level evidence remain in produced-output references and
EvidenceEnvelopes. One `success` boolean cannot represent these questions.

### 5.3 Evidence state and evidence value are different

Conceptually:

```text
evidence_state = present | partial | unavailable | ambiguous | malformed | not-applicable
value_state    = populated | empty | unknown        # when evidence exists
```

Exact names remain provisional. Explicit empty is present evidence, not an
availability state. A mismatch belongs to validation/conflict between available
facts rather than evidence availability.

### 5.4 Provider-native origin and Provider channel are different

Candidate origin/basis:

```text
provider-native
raiatea-aligned
raiatea-derived
user-asserted
unresolved
```

Provider-native evidence may come from normalized view, lossless/raw output,
metadata or diagnostics. Channel is provenance, not a different origin.

### 5.5 Scoped result assessments prevent universal completeness/integrity

A ProcessingOutcome may contain multiple assessments, conceptually:

```text
scope = text-surface
completeness = complete
integrity = established
basis = <runtime validator/evidence>
```

while another scope in the same run remains:

```text
scope = table-topology
completeness = not-established
integrity = not-established
```

No global complete/established flag upgrades sparse EvidenceEnvelopes.

### 5.6 Stage outcome and run outcome are different

Each stage retains an outcome. The run outcome is a Core orchestration assessment
with explicit derivation basis from stage outcomes, produced outputs,
normalization/validation evidence and applicable policy.

No hidden “copy last stage” or “take worst stage” rule is allowed.

### 5.7 Benchmark truth and runtime truth are different

E-04 gold proves representation requirements. It does not create runtime facts.

- Tika NEG-001 proves Provider success cannot establish integrity; it does not
  imply production Raiatea always knows an arbitrary input is malformed.
- B01-PDF-007 proves the model must represent incomplete/partial processing; it
  does not imply Provider identity is a production fallback detector.

Production scoped assessments and claims such as degraded, invalid, exact
relation or fallback-required need explicit runtime basis.

### 5.8 Partial structure is normal

Successful extraction may yield text without roles, table text without cell
identity, formula surface without math relations, figures without associations,
links without exact target representation or coordinates only for some units.
Sparse evidence is expected.

## 6. Source Coordinate synthesis

### PDF

Evidence supports page identity/index, geometric region, units,
origin/convention, evidence state/origin/provenance and optional precision or
diagnostics. Bbox is not mandatory for every route.

### EPUB

Evidence supports package/resource reference, fragment/anchor, optional
spine/navigation context, evidence state/origin/provenance and exact vs
normalized/traceable basis. Rendered page numbers are not canonical EPUB
coordinates.

### Future classes

Media time ranges, code lines/ranges, spreadsheet ranges and other coordinate
families remain extension points until evidence exists.

## 7. OCR/fallback synthesis

```text
native extraction
      │
      ├── ProviderEvidence + stage outcome
      └── runtime routing/fallback basis
                 │
                 ▼
           OCR/fallback stage
                 │
                 ├── separate RouteProfile
                 ├── ProviderEvidence
                 ├── scoped partial/exact assessment when runtime evidence exists
                 └── stage lineage
                 │
                 ▼
             normalization
```

If native/OCR block identity cannot be proven, reconciliation remains unresolved.
E-04 gold proves the need for these states but does not itself define a
production fallback heuristic.

## 8. Negative/security synthesis

Accepted evidence establishes that:

- Provider-native success may occur on benchmark-known malformed input;
- restricted input can validly terminate without normalized output;
- generic failure and explicit restriction signal differ;
- Provider content collection `present+empty`, unavailable, and
  `present+unexpected-content` are distinct field-level evidence states/values;
- Core policy may stop execution before a Provider stage starts;
- provenance persists even for failure, restriction or not-started processing;
- policy refusal is not a transient technical error to route around;
- security evidence itself may remain partial/unavailable.

## 9. What E-04 does not justify

E-04 does **not** justify freezing:

- a production Provider winner or first-slice promotion;
- a universal weighted score;
- one all-content tree;
- one coordinate representation for every Source Family;
- final table/formula/figure machine schemas;
- automatic OCR fallback based on Provider identity;
- a public JSON Schema, REST API or database schema;
- plugin transport/sandbox/lifecycle/install semantics;
- remote Provider eligibility;
- B-03/B-04/B-05 production contracts;
- a redistribution-rights conclusion while #131 remains open.

## 10. Handoff to E-05

Evidence supports these accepted **conceptual** names for the E-05a model:

```text
SourceReference
OriginalArtifact
ExtractionRequest
ProviderRef
RouteProfileRef
ProcessingRun
ProcessingStage
ProviderEvidence / RawExtractionRef
EvidenceEnvelope<T>
NormalizedRepresentation
ContentUnit
SourceCoordinate
RelationEvidence
EmbeddedAssetRef
Diagnostic
ProcessingOutcome
ProvenanceRecord
RightsDecisionRef
```

`ProducedRef` in the companion model is only a conceptual union/reference over
actual produced object references, not an additional domain entity.

The names are accepted for conceptual work only, not as stable public API
resource names.

[`provider-neutral-extraction-contract.md`](provider-neutral-extraction-contract.md)
contains the accepted E-05a conceptual model. A machine-readable schema belongs
to a later E-05 child.

## 11. Accepted phase boundary

With E-05a accepted:

1. E-04 is treated as measured input to contract design rather than an invitation
   for another default B-01 fixture;
2. the next E-05 child may attempt a bounded machine-readable contract plus
   conformance tests;
3. #147 ExtractorPlugin consumes E-05 semantics and does not define a parallel
   result model;
4. #131, G-02/G-04/G-05 and first-slice promotion remain separate gates.
