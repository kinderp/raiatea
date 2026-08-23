# E-04 Evidence Synthesis for E-05

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
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
Raiatea-owned extraction semantics** without copying the benchmark JSON or any
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

> Which distinctions did real measured routes prove Raiatea must preserve, and
> which ideas are still speculative or deferred?

It does **not** select a Provider, promote the PDF/EPUB first slice, define a
machine-readable public schema, prescribe a database, or define the Raiatea
Plugin API transport.

## 2. Evidence classification used by E-05

Every candidate requirement is classified as one of:

### `required-by-evidence`

Multiple accepted observations, or one decisive failure/security observation,
show that collapsing the distinction would lose information or create an unsafe
interpretation.

### `optional-when-provider-exposes`

The concept is useful and observed in at least one route, but a conforming
extractor is not required to provide it for every Source or route.

### `raiatea-derived-with-explicit-basis`

Raiatea may align, reconcile or derive the fact, but the result must carry its
basis and must never be serialized as if the Provider itself emitted it.

### `provisional/deferred`

The current evidence does not justify freezing the concept in the base P0
contract. It may remain an extension point or return in a later source-class
increment.

This classification applies to **contract requirements**, not Provider ranking.
No weighted or universal score is introduced.

## 3. Accepted evidence inventory

### 3.1 B-01 PDF

The accepted B-01 evidence now covers the bounded E-03 set:

- clean born-digital text and page geometry;
- multi-column reading order;
- semantic structure, lists, code-like content and links;
- figures, raster identity, geometry and caption association;
- table content, explicit topology and degraded topology;
- formula surface, token geometry and explicit mathematical relations;
- mixed/defective native text with a separately pinned OCR-capable route;
- malformed and access-controlled negative fixtures outside quality averages.

Canonical compact evidence is retained under
[`benchmark/evidence/`](benchmark/evidence/) including:

- [`b01-pdf-003-semantic-structure/`](benchmark/evidence/b01-pdf-003-semantic-structure/);
- [`b01-pdf-004-figure-caption/`](benchmark/evidence/b01-pdf-004-figure-caption/);
- [`b01-pdf-005-table-structure/`](benchmark/evidence/b01-pdf-005-table-structure/);
- [`b01-pdf-006-formula-fidelity/`](benchmark/evidence/b01-pdf-006-formula-fidelity/);
- [`b01-pdf-007-defective-native-text/`](benchmark/evidence/b01-pdf-007-defective-native-text/);
- [`b01-pdf-negative-security/`](benchmark/evidence/b01-pdf-negative-security/);
- the pinned Poppler, Tika and Docling reference-route evidence directories.

### 3.2 B-02 EPUB

Accepted B-02 evidence from [PR #134](https://github.com/kinderp/raiatea/pull/134)
compares a direct package-aware stdlib route with a local Pandoc route. Compact
evidence is retained in
[`b02-reference-linux-pandoc-3.1.11.1/`](benchmark/evidence/b02-reference-linux-pandoc-3.1.11.1/).

Measured facts include:

- direct EPUB text `4/4`, full-exact logical/package coordinates `4/4` and
  reading-order edges `3/3` on B02-EPUB-001;
- Pandoc text `4/4`, but full-exact coordinates `0/4` and only `2/4` traceable;
- direct navigation `2/2` and authored link target `1/1` on B02-EPUB-002;
- Pandoc navigation `0/2`, while preserving a semantic link but not the exact
  authored target representation;
- a traversal-member negative fixture rejected by the direct route but accepted
  by the measured Pandoc route without the expected reject/degrade signal;
- absence of observed side effects is only partial evidence, not proof of all
  internal or OS-level security properties.

B-02 coverage remains intentionally incomplete for images/captions/alt,
footnotes/endnotes, semantic table/code/MathML, broader composites and malformed
or missing-resource cases. E-05 must therefore avoid pretending that EPUB has a
complete production quality profile.

## 4. Evidence-to-requirement matrix

| Requirement | Classification | Evidence | E-05 consequence |
| --- | --- | --- | --- |
| Provider identity and route/profile identity are separate | `required-by-evidence` | Poppler controls differ on reading order/link behavior; Docling native and Docling+RapidOCR are materially different routes | Preserve Provider/engine and RouteProfile independently, including mode/backend/model/payload where material |
| Provider-native `success` is not Raiatea completeness/integrity truth | `required-by-evidence` | B01-PDF-007 native routes succeed while raster-visible content is missing; Tika succeeds on malformed NEG-001 without a corruption signal | Keep Provider-native status as evidence; model Raiatea execution/output/completeness/integrity assessment separately |
| Output availability is distinct from execution outcome | `required-by-evidence` | Negative routes can fail with empty output; access-controlled hardening distinguishes empty, unknown and anomalous content | Represent output present/empty/unavailable/unknown independently from execution status |
| Missing evidence is not zero or success | `required-by-evidence` | Figure/table/formula/coordinate dimensions repeatedly become `not-measured` on otherwise successful routes | Use explicit evidence availability/partiality; absence of a field must not silently mean empty or success |
| Surface content and semantic interpretation are separate | `required-by-evidence` | PDF-003 preserves text `8/8` across routes while semantic types and heading levels vary substantially | Content surface, semantic role and semantic relations are independently representable |
| Provider-native grouping is not automatically Raiatea semantics | `optional-when-provider-exposes` | Docling formula fixture exposes non-semantic `picture` groupings | Retain Provider grouping as evidence when useful without coercing it into formula/figure semantics |
| Explicit relations need explicit evidence or an explicit Raiatea derivation basis | `required-by-evidence` | figure↔caption, link source↔target, table cell topology and formula relations are independently available or unavailable | Relation evidence records endpoints, relation type and basis; geometry/list order alone cannot masquerade as Provider-native relation evidence |
| Ambiguous identity cannot fall back to list position | `required-by-evidence` | figure/table review findings showed cardinality/list-position matching could over-credit the wrong object | Preserve ambiguous/unresolved identity and require an inspectable alignment basis |
| Text preservation does not imply table topology preservation | `required-by-evidence` | PDF-005 has authored cell text `12/12` across measured routes while explicit topology is absent or degraded | Table existence, topology, cell binding, roles, content and geometry are separate optional evidence families |
| Formula surface does not imply mathematical semantics | `required-by-evidence` | PDF-006 surface/order can be preserved while explicit superscript/fraction relations are `0/5 not-measured` | Formula surface/token evidence and explicit math relation evidence remain separate |
| Source Coordinates are source-class-specific | `required-by-evidence` | PDF uses page/geometric evidence; EPUB direct route preserves package/resource/fragment semantics and must not be scored by rendered page | Define an extensible SourceCoordinate family, initially with distinct PDF and EPUB variants |
| Coordinates can be partial per route and per unit | `required-by-evidence` | Tika exposes no PDF bbox; Pandoc EPUB retains only partial traceability; Docling/Poppler expose differing geometry | Coordinate evidence uses explicit availability/basis rather than a mandatory universal coordinate |
| Provider-native evidence and Raiatea normalization are separate layers | `required-by-evidence` | useful lossless Docling fields differ from normalized convenience mappings; benchmark postprocessors add bounded alignment without changing Provider facts | Preserve inspectable ProviderEvidence/Raw Extraction and separately record Normalized Representation + basis |
| OCR/fallback is an explicit processing stage | `required-by-evidence` | B01-PDF-007 native stage is incomplete; locked RapidOCR route provides partial reordered recovery | Model native and OCR stages, trigger reason, route/profile and lineage; do not silently replace native output |
| Native/OCR reconciliation may legitimately be unresolved | `required-by-evidence` | measured Docling output does not prove per-block native vs OCR origin | `not-measured`/unresolved reconciliation is valid; no destructive merge without evidence |
| Exact recovery and partial surface recovery are separate | `required-by-evidence` | RapidOCR emits `TARGET OCR 2026` in the authored region: expected token multiset present, authored order wrong | A partial/mismatch result may be useful evidence without being promoted to exact recovery |
| Restricted/requires-authorization is a valid terminal outcome | `required-by-evidence` | B01 access-controlled routes correctly fail/restrict without an authorized credential route | Policy restriction is first-class; the contract must not imply that every failed extraction should be retried |
| Security evidence can itself be partial/not-measured | `required-by-evidence` | B02 Pandoc traversal case has no observed side effect but harness cannot prove all internal safety properties | Security/policy assessment records what was measured; absence of observation is not proof |
| A Processing Run exists even when no Normalized Representation is produced | `required-by-evidence` | malformed/restricted routes still have provider/version/invocation/outcome evidence | Provenance and outcome attach to attempted processing independently of successful normalized output |
| Rights evidence and RightsDecision are separate | `required-by-evidence` | E-01/E-03/#131 keep authority, Processing Rights and Redistribution Rights explicit and fail-closed | Provider/plugin/source may report rights evidence; Raiatea Core owns the policy decision and references it from the run |
| No universal extraction quality score | `required-by-evidence` | E-04 intentionally separates content, order, structure, coordinates, relations, security and resource observations | Contract carries facts/outcomes, not one Provider score; benchmark profiles may remain external evidence |
| Route quality/capability may reference benchmark evidence | `provisional/deferred` | E-04 produces versioned quality observations, but selection gates remain open | A future routing layer may reference a QualityProfile; do not embed benchmark score fields into the base extraction payload yet |
| One mandatory universal document tree | `provisional/deferred` | segmentation and semantic structure differ by Provider; E-04 scores relations/units without requiring one serialization tree | Prefer composable units/relations/evidence over freezing one Provider-shaped tree in E-05a |

## 5. Cross-cutting conclusions forced by the evidence

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

Real observations require several orthogonal questions:

1. Did the Provider process execute?
2. Is output present, empty, unavailable, malformed or unknown?
3. Is evidence for a particular fact present, partial or unavailable?
4. Is completeness established, partial or not established?
5. Is integrity established, degraded or not established?
6. Did policy allow processing, restrict it, or require authorization?

The contract may choose different names, but these questions cannot safely be
encoded by a single `success: bool` or an ever-growing monolithic status enum.

### 5.3 Evidence availability and value assessment are different

E-04 used states such as `not-measured`, explicit empty and mismatch. E-05 must
preserve the distinction while avoiding benchmark leakage.

For production semantics:

- **availability** answers whether a Provider/Raiatea fact is available and with
  what evidentiary quality;
- **value/conflict/assessment** answers whether available facts agree with some
  other asserted fact or normalization expectation.

An explicit mismatch is therefore not the same thing as missing evidence.
E-05a should model those as separate concepts rather than one overloaded enum.

### 5.4 Provider-native fact and Raiatea-derived fact need provenance of basis

A normalized fact may be useful even when the Provider did not emit it directly.
The evidence supports at least this conceptual basis vocabulary:

```text
provider-explicit
provider-lossless
raiatea-aligned
raiatea-derived
user-asserted
unresolved
```

Exact names are provisional. The invariant is not: Raiatea-derived alignment
must never be serialized as Provider-native truth.

### 5.5 Partial structure is normal, not exceptional

E-04 shows partial capability across ordinary successful extraction:

- text without semantic role;
- table descendant text without trustworthy cell identity;
- formula glyphs without mathematical relations;
- figures without caption relation or pixel identity;
- links without exact authored target representation;
- coordinates for some units but not others.

The base contract must therefore tolerate sparse/partial evidence by design.

## 6. Source Coordinate synthesis

### 6.1 PDF

Evidence supports a geometric coordinate family containing, where available:

- page identity/index;
- geometric region (bbox/polygon or extensible equivalent);
- units;
- origin/convention;
- Provider-native or Raiatea-derived basis;
- availability/precision metadata where relevant.

The contract must not require every Provider to emit bbox evidence.

### 6.2 EPUB

Evidence supports a logical/package coordinate family containing, where
available:

- package/resource path or reference;
- fragment/anchor;
- optional spine/navigation context;
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

The route decision is not “Provider X always needs OCR”. It is a Raiatea policy
or orchestration decision with an explicit basis. If native/OCR block identity
cannot be proven, reconciliation remains unresolved.

## 8. Negative/security synthesis

The final B-01 negative evidence adds a critical contract boundary:

- a Provider may report native `success` on intentionally malformed input;
- restricted input can validly terminate without normalized output;
- generic failure and explicit restriction signal are different evidence;
- output known-empty, output unknown and unexpected content under restriction
  are materially different states;
- invocation/policy evidence belongs in provenance even when extraction fails;
- the contract must never imply that a policy refusal is a transient technical
  error that should automatically be routed around.

B-02 negative evidence reinforces a second boundary: security expectations may
remain `partial` or `not-measured` even when no side effect is observed.

## 9. What E-04 does not justify

E-04 does **not** justify freezing:

- a production Provider winner;
- a first-slice promotion decision;
- a universal weighted quality score;
- one all-content document tree;
- one coordinate representation for every Source Family;
- a final table/formula/figure object schema;
- automatic OCR fallback based only on Provider identity;
- a public JSON Schema, REST API or database schema;
- plugin transport, sandbox, lifecycle or installation semantics;
- remote Provider eligibility;
- B-03/B-04/B-05 production contracts;
- a redistribution-rights conclusion while #131 remains open.

## 10. Handoff to E-05 conceptual modeling

The evidence supports exploring a small set of concepts:

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

These are **conceptual names**, not accepted API resource names.

The companion
[`provider-neutral-extraction-contract.md`](provider-neutral-extraction-contract.md)
turns this matrix into a candidate domain model. A machine-readable schema is a
later E-05 child only after the conceptual distinctions survive review.

## 11. Phase boundary

After acceptance of E-05a:

1. E-04 evidence is treated as the measured input to contract design rather than
   extended by another default B-01 fixture;
2. E-05 continues with state/coordinate/provenance refinement and only then a
   candidate machine-readable contract;
3. #147 `ExtractorPlugin` consumes E-05 semantics later and does not define a
   parallel extraction result model;
4. #131, G-02/G-04/G-05 and first-slice promotion remain separate gates.
