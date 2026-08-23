# E-04 Evidence Synthesis for E-05

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.2.0
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
fixtures. E-05 now needs to convert those observations into **requirements on
Raiatea-owned extraction semantics** without copying benchmark JSON or any
Provider-native schema into the product contract.

This document is the bridge:

```text
E-04 fixtures + raw Provider evidence + benchmark normalization
                              │
                              ▼
                  evidence-derived requirements
                              │
                              ▼
          E-05 conceptual extraction contract
```

It answers:

> Which distinctions did measured routes prove Raiatea must preserve, and which
> ideas remain optional, derived or deferred?

It does **not** select a Provider, promote the PDF/EPUB first slice, define a
machine-readable public schema, prescribe a database, or define Plugin API
transport.

## 2. Requirement classification

Every E-05 requirement derived here is classified as one of:

### `required-by-evidence`

Accepted observations show that collapsing the distinction would lose measured
information, hide degradation or create an unsafe interpretation.

### `optional-when-provider-exposes`

The concept is observed and useful, but a conforming route is not required to
provide it for every Source.

### `raiatea-derived-with-explicit-basis`

Raiatea may align, reconcile or derive the fact, but the result must carry its
basis and must never be represented as if the Provider emitted it directly.

### `provisional/deferred`

Current evidence does not justify freezing the concept in the base P0 contract.

These classes describe **contract requirements**, not Provider rankings. E-05
introduces no weighted or universal quality score.

## 3. Accepted evidence inventory

### 3.1 B-01 PDF

The bounded B-01 evidence now covers:

- clean born-digital text and page geometry;
- multi-column reading order;
- semantic structure, lists, code-like content and links;
- figures, raster identity, geometry and caption association;
- tables, explicit/degraded topology and cell identity;
- formula surface, token geometry and explicit mathematical relations;
- mixed/defective native text with a separately pinned OCR-capable route;
- malformed and access-controlled negative fixtures outside quality averages.

Compact evidence is retained under [`benchmark/evidence/`](benchmark/evidence/),
including the semantic, figure, table, formula, defective-native/OCR and negative
security slices plus the pinned Poppler/Tika/Docling reference-route records.

### 3.2 B-02 EPUB

Accepted B-02 evidence from [PR #134](https://github.com/kinderp/raiatea/pull/134)
compares a package-aware direct stdlib route with local Pandoc. Compact evidence
is retained under
[`b02-reference-linux-pandoc-3.1.11.1/`](benchmark/evidence/b02-reference-linux-pandoc-3.1.11.1/).

Measured facts include:

- B02-EPUB-001 direct text `4/4`, full-exact logical/package coordinates `4/4`,
  reading-order edges `3/3`;
- Pandoc text `4/4`, but full-exact coordinates `0/4` and only `2/4` traceable;
- B02-EPUB-002 direct navigation `2/2` and authored link target `1/1`;
- Pandoc navigation `0/2`, semantic link `1/1`, authored target exact `0/1`;
- a traversal-member negative fixture rejected by the direct route but accepted
  by the measured Pandoc route without the expected reject/degrade signal;
- no observed side effect is only partial evidence, not proof of all internal or
  OS-level security properties.

B-02 coverage remains intentionally incomplete for images/captions/alt,
footnotes/endnotes, semantic table/code/MathML, broader composites and malformed
or missing-resource cases. E-05 must preserve those gaps rather than treat them
as measured success.

## 4. Evidence-to-requirement matrix

| Requirement | Classification | Evidence | E-05 consequence |
| --- | --- | --- | --- |
| Provider identity and route/profile identity are separate | `required-by-evidence` | Poppler controls differ on reading-order/link behavior; Docling native and Docling+RapidOCR are materially different routes | Preserve Provider/engine and RouteProfile independently, including material mode/backend/model/payload identity |
| Provider-native `success` is not Raiatea completeness/integrity truth | `required-by-evidence` | B01-PDF-007 native routes succeed while raster-visible content is missing; Tika succeeds on malformed NEG-001 without a corruption signal | Keep Provider-native status as evidence; normalize execution/output/completeness/integrity separately |
| Output availability is distinct from execution outcome and output integrity | `required-by-evidence` | Negative routes fail with empty output; a future present output may still be unusable | Output answers present/empty/unavailable/unknown; integrity/validity is a separate assessment |
| Evidence state is distinct from evidence value | `required-by-evidence` | E-04 distinguishes not-measured from trustworthy explicit empty collections | A trustworthy empty collection is present evidence with an empty value; unavailable evidence is different |
| Missing evidence is not zero or success | `required-by-evidence` | Figure/table/formula/coordinate dimensions are often unavailable on otherwise successful routes | Evidence state must explicitly preserve unavailable/partial/ambiguous/malformed/not-applicable cases |
| Surface content and semantic interpretation are separate | `required-by-evidence` | PDF-003 text `8/8` across routes while semantic types and heading levels differ | Content surface, semantic role and semantic relations remain independent |
| Provider-native grouping is not automatically Raiatea semantics | `optional-when-provider-exposes` | Docling formula fixture exposes non-semantic `picture` groupings | Retain grouping evidence when useful without coercing it into formula/figure semantics |
| Provider-native origin is distinct from the Provider evidence channel | `required-by-evidence` | useful explicit fields can appear only in lossless/raw Docling output rather than convenience mappings | Record origin as Provider-native; separately retain raw/lossless/metadata/diagnostic channel locator |
| Explicit relations need explicit evidence or explicit Raiatea derivation basis | `required-by-evidence` | figure↔caption, link, table topology and formula relations vary independently | Relation evidence records endpoints, relation type and origin/basis; geometry/list position alone cannot become Provider-native relation truth |
| Ambiguous identity cannot fall back to list position | `required-by-evidence` | figure/table reviews showed cardinality/list-position matching could over-credit objects | Preserve ambiguous/unresolved identity and an inspectable alignment basis |
| Text preservation does not imply table topology preservation | `required-by-evidence` | PDF-005 authored cell strings are preserved while explicit topology is absent/degraded | Table presence, topology, cell binding, roles, text and geometry are independently optional |
| Formula surface does not imply mathematical semantics | `required-by-evidence` | PDF-006 surface/order can be preserved while explicit superscript/fraction relations are unavailable | Formula surface/token evidence and math relation evidence remain separate |
| Source Coordinates are source-class-specific | `required-by-evidence` | PDF page geometry vs EPUB package/resource/fragment semantics | Define an extensible SourceCoordinate family with distinct PDF and EPUB variants |
| Coordinates can be partial per route and unit | `required-by-evidence` | Tika lacks PDF bbox; Pandoc EPUB retains only partial traceability | Coordinate evidence has explicit evidence state/origin rather than a mandatory universal coordinate |
| Provider evidence and Raiatea normalization are separate layers | `required-by-evidence` | lossless Provider fields and bounded benchmark alignments differ from convenience mappings | Preserve inspectable ProviderEvidence/Raw Extraction and separately record NormalizedRepresentation + derivation basis |
| OCR/fallback is an explicit processing stage | `required-by-evidence` | B01-PDF-007 native stage incomplete; locked RapidOCR route provides partial reordered recovery | Model native/OCR stages, trigger reason, route/profile and lineage; do not silently replace native output |
| Native/OCR reconciliation may legitimately be unresolved | `required-by-evidence` | measured Docling output does not prove per-block native vs OCR origin | unresolved reconciliation is valid; no destructive merge without identity evidence |
| Exact recovery and partial surface recovery are separate | `required-by-evidence` | RapidOCR emits `TARGET OCR 2026` in authored region while authored order is `OCR TARGET 2026` | Partial/mismatch evidence may be useful without becoming exact recovery |
| Restricted/requires-authorization is a valid terminal Core policy disposition | `required-by-evidence` | access-controlled routes are measured without an authorized credential route | RightsDecision/policy can terminate processing; this is not an extractor-owned retry hint |
| Core policy authority and technical ProcessingOutcome are separate | `required-by-evidence` | E-01/E-03/#131 establish Core-owned rights decisions; E-04 shows technical failure may merely be a Provider symptom of restriction | ProcessingOutcome remains technical/orchestration state; any policy disposition is authoritative only through RightsDecisionRef |
| Security evidence can itself be partial/unavailable | `required-by-evidence` | B02 Pandoc traversal case has no observed side effect but harness cannot prove all internal safety properties | Security assessment records what is measured; absence of observation is not proof |
| A ProcessingRun exists even when no Provider stage/NormalizedRepresentation is produced | `required-by-evidence` plus accepted rights boundary | malformed/restricted attempts retain provenance; Core policy can also stop work before Provider execution | Run can record `not-started`/equivalent technical state and authoritative RightsDecisionRef |
| Stage outcome and run outcome are distinct | `required-by-evidence` | native + OCR + normalization may each have different partial/success states | Run outcome is an explicit Core orchestration assessment, never hidden last-stage/worst-stage aggregation |
| Rights evidence and RightsDecision are separate | `required-by-evidence` | E-01/E-03/#131 keep authority, Processing Rights and Redistribution Rights distinct | Provider/plugin/source may report rights evidence; Raiatea Core owns the decision |
| No universal extraction quality score | `required-by-evidence` | E-04 intentionally separates content/order/structure/coordinates/relations/security/resource observations | Contract carries facts/outcomes, not one Provider score |
| Route quality/capability may reference benchmark evidence | `provisional/deferred` | E-04 produces versioned quality observations while selection gates remain open | Future routing may reference QualityProfile evidence; do not embed benchmark scores into base extraction payload |
| One mandatory universal document tree | `provisional/deferred` | segmentation and structure differ by Provider | Prefer composable units/relations/evidence over a Provider-shaped tree |

## 5. Cross-cutting conclusions

### 5.1 Route/profile is the unit of capability

The evidence does not support statements such as “Docling supports OCR” or
“Poppler preserves reading order” without naming the measured route/profile.
Capability is a property of at least:

```text
Provider + version
Route/Profile + version
Mode/backend
Model/revision/payload, when applicable
Material parameters
Execution context relevant to the claim
```

E-05 therefore needs `ProviderRef` and `RouteProfileRef` as distinct concepts.
The later Plugin API may advertise route capabilities, but must not collapse
them to a plugin brand flag.

### 5.2 One status field is structurally insufficient

Real observations require separate questions:

1. Was execution started and how did it terminate?
2. Is output present, empty, unavailable or unknown?
3. Is present output valid/usable, degraded or not established?
4. Is evidence for a particular fact present, partial, unavailable or ambiguous?
5. If evidence is present, is its value populated or explicitly empty?
6. Is completeness established, partial or not established?
7. What authoritative Core RightsDecision/policy context applies?

These questions cannot safely be encoded by one `success: bool` or one
mega-enum.

### 5.3 Evidence state and evidence value are different

E-04 used `not-measured`, explicit empty and mismatch states. E-05 must preserve
the distinctions while avoiding benchmark leakage.

Conceptually:

```text
evidence_state = present | partial | unavailable | ambiguous | malformed | not-applicable
value_state    = populated | empty | unknown        # when evidence exists
```

Exact names remain provisional. The invariant is that **explicit empty is present
evidence**, not an availability state, and unavailable evidence is not an empty
value.

A mismatch is also not evidence availability. It belongs to a conflict,
validation or assessment between facts that are already available.

### 5.4 Provider-native origin and Provider evidence channel are different

The evidence supports a conceptual origin/basis vocabulary such as:

```text
provider-native
raiatea-aligned
raiatea-derived
user-asserted
unresolved
```

A Provider-native fact may be found in different channels:

```text
provider-normalized-view
provider-lossless-raw
provider-metadata
provider-diagnostic-stream
```

The channel supports provenance; it does not change a Provider-native fact into
a different epistemic category.

### 5.5 Stage outcome and run outcome are different

Each Provider-backed or Raiatea stage retains its own outcome. The overall run
outcome is a Core orchestration assessment with an explicit derivation basis
from stage outcomes, produced outputs, normalization/validation evidence and the
applicable RightsDecision.

The contract must never hide a rule such as “copy the last stage” or “take the
worst stage”.

### 5.6 Partial structure is normal, not exceptional

E-04 shows ordinary successful extraction with:

- text without semantic role;
- table descendant text without trustworthy cell identity;
- formula glyphs without mathematical relations;
- figures without caption relation or pixel identity;
- links without exact authored target representation;
- coordinates for some units but not others.

Sparse/partial evidence must therefore be normal in the base contract.

## 6. Source Coordinate synthesis

### 6.1 PDF

Evidence supports a geometric coordinate family containing, where available:

- page identity/index;
- geometric region (bbox/polygon or extensible equivalent);
- units;
- origin/convention;
- evidence state/origin/provenance;
- optional precision/diagnostic metadata.

The contract must not require every Provider to emit bbox evidence.

### 6.2 EPUB

Evidence supports a logical/package coordinate family containing, where
available:

- package/resource path or reference;
- fragment/anchor;
- optional spine/navigation context;
- evidence state/origin/provenance;
- exact vs normalized/traceable basis when Raiatea alignment occurs.

Rendered page numbers are not canonical EPUB Source Coordinates.

### 6.3 Future classes

Time ranges for audio/video, code line/range references, spreadsheet cell ranges
and other coordinate families remain extension points. E-05a should leave room
for them without designing them speculatively.

## 7. OCR/fallback synthesis

B01-PDF-007 establishes an explicit stage model:

```text
native extraction
      │
      ├── output + diagnostics
      ├── completeness evidence
      │
      └── routing/fallback reason
                 │
                 ▼
           OCR/fallback stage
                 │
                 ├── separate RouteProfile
                 ├── output + coordinates
                 ├── exact/partial evidence
                 └── stage lineage
```

The route decision is not “Provider X always needs OCR”. It is a Raiatea
orchestration decision with an explicit basis. If native/OCR block identity
cannot be proven, reconciliation remains unresolved.

## 8. Negative/security synthesis

The final B-01 negative evidence adds critical boundaries:

- Provider-native `success` may occur on intentionally malformed input;
- restricted input can validly terminate without normalized output;
- generic failure and explicit restriction signal are different evidence;
- output known-empty, output unknown and unexpected content under restriction
  are materially different observations;
- a Core policy decision may also prevent Provider execution entirely;
- invocation/policy evidence belongs in provenance even when extraction fails or
  never starts;
- policy refusal is not a transient technical error to route around.

B-02 negative evidence reinforces that security expectations may remain partial
or unavailable even when no side effect is observed.

## 9. What E-04 does not justify

E-04 does **not** justify freezing:

- a production Provider winner;
- a first-slice promotion decision;
- a universal weighted quality score;
- one all-content document tree;
- one coordinate representation for every Source Family;
- a final table/formula/figure machine schema;
- automatic OCR fallback based only on Provider identity;
- a public JSON Schema, REST API or database schema;
- plugin transport, sandbox, lifecycle or installation semantics;
- remote Provider eligibility;
- B-03/B-04/B-05 production contracts;
- a redistribution-rights conclusion while #131 remains open.

## 10. Handoff to E-05 conceptual modeling

The evidence supports exploring:

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

These are conceptual names, not accepted API resource names.

The companion
[`provider-neutral-extraction-contract.md`](provider-neutral-extraction-contract.md)
turns this synthesis into the candidate domain model. A machine-readable schema
is a later E-05 child only after these distinctions survive review.

## 11. Phase boundary

After acceptance of E-05a:

1. E-04 evidence is treated as measured input to contract design rather than
   extended by another default B-01 feature fixture;
2. E-05 continues with a bounded candidate machine-readable contract and
   conformance tests only after conceptual acceptance;
3. #147 `ExtractorPlugin` consumes E-05 semantics later and does not define a
   parallel extraction result model;
4. #131, G-02/G-04/G-05 and first-slice promotion remain separate gates.
