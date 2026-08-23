# Provider-neutral Extraction Contract — Conceptual Model

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.3.0
>
> Last reviewed: 23 August 2026
>
> E-05a child issue: [#160](https://github.com/kinderp/raiatea/issues/160)
>
> E-05 parent: [#159](https://github.com/kinderp/raiatea/issues/159)
>
> Evidence synthesis: [`e04-evidence-synthesis.md`](e04-evidence-synthesis.md)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Plugin API consumer: [#147](https://github.com/kinderp/raiatea/issues/147)
>
> Rights gate: [#131](https://github.com/kinderp/raiatea/issues/131) remains independent and fail-closed

## 1. Purpose

E-05 needs a **Raiatea-owned semantic contract** between heterogeneous extraction
routes and downstream Raiatea capabilities.

The contract must let different Providers expose different levels of evidence
without forcing them into one Provider-shaped document schema and without
silently upgrading missing, partial or inferred evidence into truth.

The conceptual boundary is:

```text
Source / Original Artifact
          │
          ▼
   ExtractionRequest
          │
          ▼
   Core policy / rights gate
          │
          ▼
     ProcessingRun
          │
          ├── ProcessingStage: native extraction
          │        │
          │        └── ProviderEvidence / Raw Extraction
          │
          ├── optional ProcessingStage: OCR/fallback
          │        │
          │        └── ProviderEvidence / Raw Extraction
          │
          └── Raiatea normalization/alignment
                   │
                   ▼
          NormalizedRepresentation
```

Diagnostics, provenance, Source Coordinates and the authoritative policy/rights
decision span the flow. `ProcessingOutcome` describes technical/orchestration
outcome; it is not a second policy authority.

This document defines a **conceptual model only**. It does not freeze JSON field
names, Python classes, REST resources, database tables, plugin transport or a
public compatibility version.

## 2. Ownership boundary

> Assertion status: `evidence-derived draft decision`

Raiatea Core owns:

- the meaning of SourceReference, processing attempt, NormalizedRepresentation,
  Source Coordinates, diagnostics and provenance;
- the distinction between Provider-native facts and Raiatea-derived facts;
- normalized failure/degraded/partial semantics;
- orchestration-level run outcome;
- policy/rights decisions and their authority;
- lineage between stages and produced artifacts.

A Provider/Adapter/ExtractorPlugin may provide:

- route/profile capability evidence;
- Provider-native status and diagnostics;
- raw output references;
- content/structure/coordinate/asset evidence;
- Provider/model/runtime provenance.

It does **not** redefine Raiatea domain meaning or authorize its own processing.
The later Plugin API may define transport, lifecycle and envelopes, but transport
is not part of E-05a.

## 3. Evidence-derived invariants

### I-01 — Provider is not RouteProfile

`ProviderRef` identifies the engine/provider family and versioned identity.
`RouteProfileRef` identifies the materially configured route: mode/backend,
OCR/enrichment state, model/revision/payload where relevant, material parameters
and execution class.

Capabilities attach to RouteProfile, not merely Provider brand.

### I-02 — Provider status is evidence, not Raiatea outcome truth

Provider-native success/failure is retained as evidence. Raiatea records a
separate structured `ProcessingOutcome`.

### I-03 — evidence state and evidence value are separate

A trustworthy explicitly empty collection is **present evidence whose value is
empty**. It is not a form of unavailable evidence.

### I-04 — Provider-native facts and Raiatea-derived facts never share an implicit basis

Alignment, reconciliation or derivation by Raiatea records its basis. A derived
fact must never be represented as if the Provider emitted it.

### I-05 — evidence origin and Provider evidence channel are separate

A fact remains Provider-native whether it was found in a convenience view,
lossless/raw document, metadata or diagnostic stream. Channel aids traceability;
it does not define a new epistemic origin.

### I-06 — relations require identity evidence

Figure↔caption, link, table-cell, formula and similar relations require explicit
Provider evidence or an explicit Raiatea alignment/derivation basis. List
position, proximity, typography or cardinality alone do not create a
Provider-native relation.

### I-07 — Source Coordinates are typed by Source semantics

PDF page geometry and EPUB package/logical anchors are different coordinate
families. Future families may extend the model without rewriting existing ones.

### I-08 — Raw Extraction and Normalized Representation are distinct

Provider evidence remains inspectable after normalization. Normalization does
not destroy the provenance needed to explain a Raiatea fact.

### I-09 — partial structure is normal

Content may be preserved while semantic roles, coordinates, relations, table
topology or mathematical structure are unavailable. Sparse evidence is a normal
state, not an exception.

### I-10 — fallback is an explicit stage with lineage

OCR/fallback has its own RouteProfile, outcome, diagnostics, output, trigger
reason and lineage. It is not an invisible retry or replacement.

### I-11 — policy restriction is a valid terminal result

A Core decision such as restricted/requires-authorization may legitimately
terminate a run before Provider invocation or before normalized output exists.
The contract must not imply automatic routing around a refusal.

### I-12 — rights evidence is not the RightsDecision

Source/Provider/plugin rights evidence is input to policy. Raiatea Core owns the
authoritative decision. Any disposition repeated on a run is only a traceable
projection/reference, never an independent extractor-produced decision.

### I-13 — stage outcomes do not mechanically determine run outcome

Each stage retains its outcome. The overall run outcome is a Raiatea
orchestration-level assessment with explicit derivation basis; it is not
implicitly the last stage or the worst stage.

### I-14 — benchmark truth is not automatic production knowledge

E-04 gold can prove that a fixture is malformed, incomplete or mismatched because
the benchmark owns authored truth. A production run may assert such a condition
only when it has an explicit runtime basis: Provider evidence, Core validation,
an authoritative expectation, user assertion or another inspectable source.

E-04 conclusions therefore justify the **shape of the contract and conformance
tests**, not hidden production detectors. Without runtime evidence,
completeness/integrity remains `not-established` rather than importing benchmark
gold truth.

### I-15 — no universal quality score

Provider/route benchmark evidence may inform later routing, but the extraction
contract does not carry one authoritative weighted score.

## 4. Conceptual object graph

```text
SourceReference ───────────────┐
                               │
OriginalArtifact ──────────────┤
                               ▼
                       ExtractionRequest
                               │
                               ▼
                       RightsDecisionRef
                               │
                               ▼
                         ProcessingRun
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
      ProcessingStage     Diagnostics       ProvenanceRecord
             │
             ├── ProviderRef
             ├── RouteProfileRef
             ├── Provider-native status
             ├── ProviderEvidence / RawExtractionRef
             ├── stage ProcessingOutcome
             └── stage inputs/outputs
                               │
                               ▼
                   Raiatea normalization
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          ContentUnit   RelationEvidence  EmbeddedAssetRef
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                    NormalizedRepresentation
```

The graph describes ownership and lineage, not a required serialization tree.

## 5. SourceReference, OriginalArtifact and ExtractionRequest

> Assertion status: `provisional-decision constrained by glossary/E-04`

### SourceReference

Represents the Source in its workflow/evidentiary role. It is not Raiatea's
universal Catalog identity and must not assume a filesystem path is stable
logical identity.

Candidate information may include source class/media type, external/source-system
reference, location/reference information under the authority boundary,
fingerprint when available and provenance/rights-evidence references.

### OriginalArtifact

Represents a preserved or addressable original byte/object artifact when one
exists. Candidate information includes artifact handle/reference, media type,
size, cryptographic fingerprint and provenance.

A SourceReference may exist without Raiatea storing a complete OriginalArtifact,
for example metadata/link-only workflows. Storage policy is outside E-05a.

### ExtractionRequest

Describes requested processing intent, not a Provider command line. Candidate
information includes input reference, requested capability/profile constraints,
applicable policy/rights context, optional requested evidence families,
resource constraints and correlation/idempotency context.

Provider-specific parameters belong to the selected RouteProfile/ProcessingStage
provenance unless Raiatea later defines a stable cross-provider option.

## 6. ProviderRef and RouteProfileRef

### ProviderRef

Conceptually identifies Provider/engine id and version/immutable revision where
available. Adapter/plugin identity remains separately traceable.

### RouteProfileRef

Conceptually identifies a reproducible route configuration:

- profile id/version;
- ProviderRef;
- backend/mode;
- model/revision/payload fingerprints where relevant;
- material parameters;
- execution class/context where relevant;
- capability declarations or references.

One Provider may expose many RouteProfiles. One plugin may expose many
Provider/RouteProfile combinations.

## 7. EvidenceEnvelope<T>

> Assertion status: `provisional-decision; representation not frozen`

E-04 requires explicit semantics for optional/partial evidence.

Conceptually:

```text
EvidenceEnvelope<T>
├── evidence_state
├── value_state?
├── value? : T
├── origin_basis
├── provider_evidence_ref?
├── provider_channel?
├── provenance_ref?
├── diagnostics[]
└── assessment/conflict?
```

### 7.1 Evidence state

Candidate states:

```text
present
partial
unavailable
ambiguous
malformed
not-applicable
```

- `present`: attributable evidence exists and can safely describe its value;
- `partial`: some attributable evidence exists but the fact is incomplete;
- `unavailable`: not measured/not exposed; never becomes zero/success;
- `ambiguous`: identity/mapping has multiple defensible interpretations;
- `malformed`: the evidence channel itself cannot be safely interpreted;
- `not-applicable`: the concept does not apply.

### 7.2 Value state

When evidence is present or partial, the value may be:

```text
populated
empty
unknown
```

`empty` means a trustworthy producer explicitly exposed an empty value or
collection. This preserves **explicit empty != unavailable** without making
emptiness a form of availability.

The later machine schema may infer value-state from `value` if it can do so
unambiguously; the semantic distinction must survive.

### 7.3 Origin basis

Candidate origin/basis values:

```text
provider-native
raiatea-aligned
raiatea-derived
user-asserted
unresolved
```

For Provider-native facts, channel/locator is separate, for example:

```text
provider-normalized-view
provider-lossless-raw
provider-metadata
provider-diagnostic-stream
other-provider-channel
```

### 7.4 Conflict/mismatch is not evidence state

Mismatch belongs to validation/conflict/assessment between available facts. It
is not a synonym for missing or partial evidence and benchmark gold semantics do
not automatically become production payload fields.

## 8. ProcessingRun and ProcessingStage

### ProcessingRun

A run is one Raiatea-governed processing attempt and may exist even when no
Provider stage starts or no normalized output is produced.

Candidate minimum:

- run id and input/request references;
- ordered/related stages;
- start/end timestamps;
- overall ProcessingOutcome;
- explicit run-outcome derivation basis;
- diagnostics and provenance;
- produced raw/normalized/derived references;
- authoritative RightsDecisionRef/policy context.

Run outcome summarizes orchestration for downstream consumers. It is derived
from applicable policy, stage outcomes, produced outputs and Raiatea
validation/normalization evidence; it is never implicitly copied from the final
Provider stage.

### ProcessingStage

A stage is one attributable operation/route execution or an explicitly recorded
stage that was not started because a prerequisite/policy gate prevented it.

Candidate minimum:

- stage id and kind/purpose;
- parent/prior stage relation;
- ProviderRef + RouteProfileRef where Provider-backed;
- trigger/reason for fallback or orchestration transition;
- inputs and raw outputs;
- Provider-native status if invoked;
- stage ProcessingOutcome;
- diagnostics and provenance/timing.

Stage vocabulary remains extensible; E-05a does not freeze an exhaustive enum.

## 9. ProcessingOutcome is multi-dimensional

> Assertion status: `evidence-derived draft decision`

A single boolean or monolithic enum cannot represent E-04 outcomes safely.
Technical/orchestration state is separate from authoritative Core policy.

### 9.1 Execution

Candidate states:

```text
not-started
succeeded
failed
rejected
unsupported
cancelled
timeout
unknown
```

Provider-native status remains separately preserved. `not-started` is provisional
vocabulary for a stage/run intentionally not invoked because a prerequisite or
Core decision prevented execution.

### 9.2 Output availability

Candidate states:

```text
present
empty
unavailable
unknown
```

This axis answers only whether output exists/was observable. It does not encode
validity: output can be `present` while integrity is degraded or invalid.

### 9.3 Completeness

Candidate states:

```text
complete
partial
not-established
not-applicable
```

Completeness claims require an explicit production basis. Provider success alone
cannot establish completeness.

### 9.4 Integrity

Candidate states:

```text
established
degraded
invalid
not-established
not-applicable
```

Integrity is independent from output presence. A present output may be invalid or
degraded; without validation evidence it may remain not-established.

### 9.5 Core policy disposition

Authoritative policy remains in `RightsDecisionRef` or a later more general Core
policy-decision reference if evidence justifies one.

For readability a run may project a disposition such as:

```text
allowed
restricted
requires-authorization
denied
not-evaluated
```

but the projection must be derived from and traceable to the Core decision. A
Provider or ExtractorPlugin cannot set it independently.

### 9.6 Run outcome versus stage outcomes

Each stage retains its own outcome. The run-level outcome is a Core orchestration
summary with explicit derivation basis.

A native stage can succeed with partial/not-established completeness, an OCR
stage can succeed with partial recovery, and normalization can still produce a
useful representation. Hidden rules such as “take worst stage” or “copy last
stage” are forbidden.

## 10. ProviderEvidence / RawExtractionRef and NormalizedRepresentation

> Assertion status: `evidence-derived draft decision`

### ProviderEvidence / RawExtractionRef

Raw Provider output remains addressable/inspectable without making the Provider
schema Raiatea's public contract.

Candidate evidence includes or references:

- raw output artifact/blob/document;
- Provider-native status;
- Provider diagnostics/stdout/stderr where retention permits;
- Provider-native object/reference ids;
- explicit Provider fields mapped to EvidenceEnvelopes;
- Provider evidence channel/locator;
- route/profile/runtime provenance;
- raw-output fingerprint.

Large raw artifacts should be referenced by handle/ref; storage/streaming is
outside E-05a.

### NormalizedRepresentation

Raiatea's Provider-neutral downstream view may contain ContentUnits, coordinates,
semantic-role evidence, relations, assets, sparse structured evidence,
diagnostics and lineage back to raw Provider evidence.

It is **not** required to be one canonical tree. E-04 favors a composable
unit/relation model because segmentation and structure vary by route and many
evidence families are partial.

## 11. ContentUnit and semantic evidence

A ContentUnit is representation-local and is not the durable Catalog Logical
Identity.

Candidate information includes:

- representation-local unit id;
- content/surface evidence;
- semantic-role evidence;
- Source Coordinate evidence;
- Provider-native references;
- explicit group/parent evidence where available;
- provenance/basis;
- diagnostics.

Semantic role is evidence-bearing, not an unconditional ContentUnit type:

```text
semantic_role: EvidenceEnvelope<SemanticRole>
```

Heading level, list metadata and role-specific properties remain separate
optional evidence. Unknown role must not silently become paragraph unless that is
a Raiatea normalization decision with basis.

## 12. SourceCoordinate family

> Assertion status: `evidence-derived family; representation provisional`

### PDF geometric coordinate

Conceptually:

```text
PdfPageRegionCoordinate
├── page identity/index
├── region geometry
├── units
├── origin/convention
├── evidence state/origin/provenance
└── optional precision/diagnostics
```

Region geometry may later support bbox/polygon or equivalent. No JSON geometry
encoding is frozen here.

### EPUB logical/package coordinate

Conceptually:

```text
EpubLogicalCoordinate
├── resource/package reference
├── fragment/anchor?
├── spine/navigation context?
├── evidence state/origin/provenance
└── traceability/normalization metadata?
```

Exact authored and Raiatea-normalized/traceable coordinates remain distinct.
Rendered page numbers are not canonical EPUB Source Coordinates.

### Extension rule

Future coordinate variants may be added for media time, code line/range,
spreadsheet cell/range and other Source Families, but those variants remain
deferred until evidence exists.

## 13. Relations, assets and sparse structured evidence

### RelationEvidence

Conceptually:

```text
RelationEvidence
├── relation kind
├── source endpoint
├── target endpoint(s)
├── EvidenceEnvelope/basis
├── Provider-native refs?
└── diagnostics/ambiguity
```

Measured relation families include reading-order precedence, links,
figure↔caption, table topology/cells and mathematical relations.

### EmbeddedAssetRef

Figure evidence shows that asset presence, geometry, byte/pixel identity and
caption relation are independent. EmbeddedAssetRef therefore makes those
properties optional evidence rather than implied attributes.

### Tables

Table evidence remains sparse/composable: table presence, geometry, topology,
cell binding, cell text, roles and cell geometry are independent. Unbound table
descendant text can retain lineage without invented row/column identity.

### Formulas

Formula evidence keeps surface/tokens, geometry, Provider grouping and explicit
mathematical relations separate. A raised glyph or Provider picture group is not
by itself superscript/formula semantics.

Detailed table/formula machine schemas are deferred until the base contract and
extension pattern are accepted.

## 14. Diagnostic

Diagnostics capture observable limitations without conflating them with outcome
axes.

Candidate information includes Raiatea diagnostic category/code, severity,
message/details, Provider diagnostic reference where retained, affected
stage/unit/relation/coordinate, evidence basis and provenance.

Provider-specific exception strings are evidence, not the stable cross-provider
contract vocabulary.

## 15. OCR/fallback lineage

B01-PDF-007 requires explicit multi-stage lineage:

```text
stage native-1
  route = docling-native-no-ocr
  provider_status = success
  output = ProviderEvidence A
  completeness = not-established unless runtime evidence establishes more

stage ocr-1
  triggered_by = explicit Raiatea routing decision/basis
  route = docling-rapidocr-locked
  output = ProviderEvidence B
  recovery evidence = partial

stage normalize-1
  inputs = A + B
  reconciliation = unresolved where block origin cannot be proven
  output = NormalizedRepresentation C

run outcome
  derived_from = stage outcomes + produced outputs + runtime validation + Core policy
```

The normalizer may preserve A and B without destructively choosing one when
identity is ambiguous.

E-04 gold proves that the native route missed authored raster text and RapidOCR
reordered the target; **production routing does not automatically know those
gold facts**. A production fallback trigger needs its own explicit runtime basis.
Fallback policy itself remains later orchestration/routing work.

## 16. Restricted/security outcomes and policy authority

The contract supports a run that terminates without normalized content.

For an access-controlled Source:

```text
ProcessingRun
├── authoritative RightsDecisionRef / policy decision
├── Provider-native failure/restriction evidence, if a Provider was invoked
├── execution = not-started/failed/rejected/unsupported as actually normalized
├── output = empty/unavailable/unknown as actually observed
├── diagnostics
├── provenance
└── NormalizedRepresentation = absent
```

If Core policy prevents Provider execution, ProviderEvidence is absent for the
legitimate reason `not-started`; this differs from unavailable Provider evidence
after an attempted run.

A generic Provider failure and explicit restriction signal are different
evidence. Absence of observed side effects is not proof of unmeasured security
properties.

## 17. RightsEvidence vs RightsDecisionRef

> Assertion status: `accepted boundary inherited from E-01/E-03; representation provisional`

Rights evidence may originate from Source metadata, user assertion, a connector
or licensed system and may be incomplete/unknown.

`RightsDecisionRef` references the authoritative Core policy decision applicable
to the processing action. An extractor does not authorize itself by reporting a
permissive license string. Unknown rights-sensitive state remains fail-closed
according to Core policy.

Redistribution Rights remain separately governed by #131 and are not implied by
Processing Rights.

## 18. Provenance minimum

Every attempted ProcessingRun should be able to trace, where applicable:

- SourceReference / OriginalArtifact and fingerprint;
- request/correlation id;
- authoritative RightsDecisionRef/policy context;
- Provider id/version/revision if invoked;
- RouteProfile id/version if invoked;
- backend/mode and model/revision/payload fingerprint;
- material parameters;
- relevant execution environment;
- stage kind and parent/prior relation;
- stage timestamps or explicit not-started reason;
- Provider-native status if available;
- each stage ProcessingOutcome;
- overall run ProcessingOutcome + derivation basis;
- diagnostics;
- raw/provider evidence references/fingerprints;
- normalized/derived output references;
- normalization/alignment origin basis and Provider evidence channel.

Provenance is required even for failed/restricted or policy-gated runs because
the attempted processing/request evaluation is itself evidence.

## 19. Benchmark truth vs production assessment

> Assertion status: `evidence-derived boundary`

E-04 benchmark gold provides authoritative truth **inside the benchmark only**.
It is used to prove that the production contract needs certain representational
states; it is not a hidden runtime information source.

Examples:

- NEG-001 tells the benchmark that Tika returned Provider-native success on a
  malformed fixture. In production, absent an independent validator, Raiatea can
  conclude only that integrity/completeness is `not-established`; it cannot
  manufacture the fact `malformed` from benchmark history.
- B01-PDF-007 tells the benchmark that native extraction missed raster-visible
  authored text. In production, a fallback decision requires its own detector,
  policy or evidence basis; Provider brand does not imply incompleteness.
- benchmark exact/mismatch scores validate contract behavior but are not
  automatically serialized into every production ContentUnit or relation.

A production assessment such as `complete`, `degraded`, `invalid`, exact relation
or fallback-required must therefore identify an explicit runtime basis.

## 20. Scenario validation

The conceptual model must represent accepted E-04 evidence without
Provider-specific contract fields.

### A — Provider success, completeness not established

A native extraction stage can record Provider-native success and output present
while completeness remains not-established. If a runtime validator later finds
partial coverage, it may set `partial` with that validator as basis.

### B — benchmark-known malformed input not surfaced by Provider

For Tika NEG-001, benchmark evidence records Provider-native success and no
relevant corruption diagnostic. This proves Provider success cannot establish
integrity. A production run without independent validation remains
`integrity=not-established`; benchmark gold does not become a production
malformed detector.

### C — restricted Source

A Core decision may be requires-authorization/restricted, normalized output may
be absent, and ProcessingRun/provenance still exists. Provider evidence is
present only if an authorized/eligible Provider stage was actually invoked.

### D — text complete, structure partial

Table text may be present while table topology/cell binding is unavailable. No
row/column identity is invented.

### E — surface math present, semantics unavailable

Formula glyphs may be present while explicit mathematical relations are
unavailable. Non-semantic grouping remains Provider-native evidence with its
channel locator.

### F — EPUB text present, logical traceability partial

Text/order may be preserved while package/resource/fragment coordinate evidence
is partial/unavailable. Raiatea does not fabricate exact anchors.

### G — security expectation not proven by success

A Provider may report success while a security expectation remains partial or
unmeasured. No observed side effect is not proof of all internal safety
properties.

### H — trustworthy explicit empty versus unavailable

Provider explicitly exposes an empty relation collection:

```text
evidence_state = present
value_state = empty
value = []
origin_basis = provider-native
```

Route exposes no relation collection:

```text
evidence_state = unavailable
value = absent
```

The later schema must not collapse those states into one nullable field.

### I — stage/run outcome aggregation

A native stage may succeed with not-established completeness, OCR may succeed
with partial recovery, and normalization may produce useful output. The run
outcome records a Core orchestration assessment and derivation basis; it is not
implicitly the last or worst stage.

## 21. Compatibility boundary with Plugin API #147

E-05 owns **domain semantics**. #147 later defines plugin mechanics.

Conceptually a future ExtractorPlugin should support:

```text
extract.probe
    -> RouteProfile/capability evidence

extract.run
    -> ProviderEvidence + stage evidence compatible with E-05 semantics
```

The Plugin API may later define manifest, capability advertisement, lifecycle,
permissions, isolation, transport/envelope, version negotiation and artifact
handles. It must not define a second extraction-domain model or independent
policy decision channel.

E-05 does not require JSON-RPC, gRPC or another transport.

## 22. Deferred after E-05a

E-05a intentionally does not decide:

- exact JSON field names or JSON Schema;
- stable public version numbers;
- database persistence/API resources;
- Adapter SDK interfaces;
- plugin manifest/transport/lifecycle;
- artifact storage/streaming protocol;
- deterministic routing policy and route-selection thresholds;
- automatic OCR trigger policy;
- complete table/formula schemas;
- B-03/B-04/B-05 coordinate variants;
- remote Provider eligibility;
- first-slice promotion;
- redistribution rights under #131.

## 23. Next E-05 child after conceptual acceptance

Only after E-05a survives review should E-05 create a bounded child for a
**candidate machine-readable contract** and conformance tests.

That child should:

1. encode only evidence-required or deliberately accepted optional concepts;
2. include negative tests for evidence-state/value-state collapse,
   Provider/Raiatea origin confusion, coordinate coercion, hidden run/stage
   aggregation, benchmark-gold leakage and restricted-output states;
3. remain independent of plugin transport;
4. demonstrate at least two existing benchmark mappers can adapt without leaking
   native Provider schemas;
5. still avoid selecting a production Provider or first slice.
