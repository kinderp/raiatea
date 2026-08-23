# Provider-neutral Extraction Contract — Conceptual Model

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

Diagnostics, provenance, Source Coordinates and the applicable RightsDecision
span the flow. `ProcessingOutcome` describes technical/orchestration outcome;
it does not become a second policy authority.

This document defines a **conceptual model only**. It does not freeze JSON field
names, Python classes, REST resources, database tables, plugin transport or a
public compatibility version.

## 2. Ownership boundary

> Assertion status: `evidence-derived draft decision`

Raiatea Core owns:

- the meaning of `SourceReference`, `OriginalArtifact`, processing attempt,
  normalized representation, Source Coordinates, diagnostics and provenance;
- the distinction between Provider-native facts and Raiatea-derived facts;
- rights/policy decisions;
- normalized failure/degraded/partial semantics;
- orchestration-level run outcome;
- lineage between processing stages and produced artifacts.

A Provider/Adapter/ExtractorPlugin may provide:

- route/profile capabilities;
- Provider-native status and diagnostics;
- raw output references;
- content/structure/coordinate/asset evidence;
- Provider/model/runtime provenance.

It does **not** redefine Raiatea domain meaning or authorize its own processing.

The later Plugin API may define how a process advertises or transports these
concepts, but transport is not part of this document.

## 3. Core invariants

### I-01 — Provider is not RouteProfile

`ProviderRef` identifies the engine/provider family and its versioned identity.
`RouteProfileRef` identifies the materially configured processing route.

A route/profile may include, when relevant:

- mode/backend;
- OCR enabled/disabled;
- enrichment modes;
- model/revision/payload fingerprint;
- material parameters;
- execution class such as local/self-hosted/remote when policy permits it.

Capability claims attach to the route/profile, not merely the Provider brand.

### I-02 — Provider status is evidence, not Raiatea outcome truth

A Provider-native `success`/`failure` value is retained in Provider evidence.
Raiatea separately records its own structured `ProcessingOutcome`.

E-04 requires this because Provider success may coexist with missing visible
content or with malformed input that was not surfaced as degraded.

### I-03 — evidence state and evidence value are separate

The absence of a serialized value must not carry several incompatible meanings.
Raiatea must distinguish whether evidence is present/partial/unavailable/etc.
from whether the observed value itself is empty.

A trustworthy explicit empty collection is therefore **present evidence whose
value is empty**, not a special synonym for unavailable evidence.

### I-04 — Provider-native and Raiatea-derived facts never share an implicit basis

If Raiatea aligns a Provider block to a Source unit, derives a relation from
explicit Provider fields, or reconciles two stages, the normalized fact records
that basis. A derived fact must never be represented as if the Provider emitted
it directly.

### I-05 — evidence origin is separate from Provider evidence channel

A fact can be Provider-native whether it was found in a convenience normalized
view, a lossless/raw representation, metadata, stdout/stderr or another Provider
channel. The channel helps trace the fact but does not create a different
origin/epistemic category.

### I-06 — relations require identity evidence

Figure↔caption, link, table-cell, formula and other relations require explicit
Provider evidence or an explicit Raiatea alignment/derivation basis.

List position, visual proximity, typography or cardinality alone do not create a
Provider-native relation.

### I-07 — Source Coordinates are typed by Source semantics

PDF page geometry and EPUB package/logical anchors are different coordinate
families. A future contract may add time, code-line, spreadsheet-range or other
coordinate types without rewriting the base model.

### I-08 — Raw Extraction and Normalized Representation are distinct

Provider evidence remains inspectable after normalization. Normalization does
not destroy the provenance needed to explain how a Raiatea fact was produced.

### I-09 — partial structure is a normal successful state

A route may preserve content while lacking semantic roles, coordinates,
relations, table topology or formula structure. The base contract must allow
sparse evidence without treating it as an exception.

### I-10 — fallback is a ProcessingStage with lineage

OCR or another fallback is not an invisible retry. It has its own RouteProfile,
outcome, diagnostics, output, trigger reason and lineage.

### I-11 — policy restriction is a valid terminal result

A restricted/requires-authorization decision may legitimately terminate a
ProcessingRun without a Provider stage or NormalizedRepresentation. The contract
must not imply that every restriction should be retried through another route.

### I-12 — rights evidence is not the RightsDecision

Source/Provider/plugin rights evidence is input to policy. Raiatea Core owns the
`RightsDecision`. A run references the applicable decision/context rather than
letting an extractor authorize itself.

Any policy-disposition value repeated on a run is only a projection of that Core
decision for readability and is never independently authoritative.

### I-13 — stage outcomes do not mechanically determine run outcome

Each stage retains its own `ProcessingOutcome`. The overall run outcome is a
Raiatea orchestration-level assessment with an explicit derivation basis. It is
not implicitly the last stage, the worst stage or a Provider-native aggregate.

### I-14 — no universal quality score

Provider/route benchmark evidence can inform routing later, but the extraction
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

The diagram describes ownership/lineage, not a required serialization tree.

## 5. SourceReference and OriginalArtifact

> Assertion status: `provisional-decision constrained by glossary/E-04`

### `SourceReference`

Represents the Source in its workflow/evidentiary role. It is not required to be
Raiatea's universal Catalog identity and must not assume a filesystem path is
stable logical identity.

Conceptually it may carry:

- source class/family or detected media type;
- external/source-system reference where applicable;
- location/reference information under the relevant authority boundary;
- source fingerprint when available;
- provenance/rights-evidence references.

### `OriginalArtifact`

Represents a preserved or addressable original byte/object artifact when the
workflow has one.

Conceptually it may carry:

- artifact reference/handle;
- media type;
- byte size;
- cryptographic fingerprint;
- storage/reference semantics;
- provenance.

A SourceReference may exist without Raiatea storing a complete OriginalArtifact,
for example metadata/link-only workflows. Exact storage policy is outside E-05a.

## 6. ExtractionRequest

> Assertion status: `provisional-decision`

`ExtractionRequest` describes the requested/authorized processing intent, not the
Provider-specific command line.

Candidate concepts:

- SourceReference / OriginalArtifact input;
- requested capability/profile constraints;
- RightsDecision/policy context reference or requirement;
- optional requested evidence families;
- resource/policy constraints;
- correlation/idempotency context.

Provider-specific parameters belong to the selected RouteProfile/ProcessingStage
provenance unless Raiatea intentionally exposes a stable cross-provider option.

No plugin transport envelope is defined here.

## 7. ProviderRef and RouteProfileRef

### `ProviderRef`

Conceptually identifies:

- Provider/engine id;
- Provider version/immutable revision where available;
- Adapter/plugin identity separately, when applicable.

### `RouteProfileRef`

Conceptually identifies a reproducible processing configuration:

- profile id/version;
- ProviderRef;
- backend/mode;
- model/revision/payload fingerprints where relevant;
- material route parameters;
- local/self-hosted/remote execution context when relevant to policy;
- capability declarations or references.

The same Provider can expose multiple RouteProfiles. The same plugin can expose
multiple Provider/RouteProfile pairs.

## 8. EvidenceEnvelope<T>

> Assertion status: `provisional-decision; representation not frozen`

E-04 requires an explicit wrapper or equivalent semantics for optional/partial
evidence.

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
└── assessment/conflict?   # only when meaningful outside benchmark-only scoring
```

### 8.1 Evidence state

Candidate states:

```text
present
partial
unavailable
ambiguous
malformed
not-applicable
```

These names are provisional. Their semantic distinctions are evidence-required.

Important rules:

- `present` means attributable evidence exists and the envelope can safely
  describe its value;
- `partial` means some attributable evidence exists but the complete fact is not
  established;
- `unavailable` covers not-measured/not-exposed evidence and must not become
  zero/success;
- `ambiguous` preserves unresolved identity or multiple defensible mappings;
- `malformed` means the evidence channel itself cannot be safely interpreted;
- `not-applicable` is a semantic statement, not missing data.

### 8.2 Value state

When evidence is `present` or `partial`, the value may itself be:

```text
populated
empty
unknown
```

`empty` means a trustworthy producer explicitly exposed an empty value or
collection. This is how E-04's **explicit empty != unavailable** distinction is
preserved without making emptiness a kind of evidence availability.

The exact representation can later be simplified if a machine-readable schema
can infer `empty` unambiguously from `value`, but the semantic distinction must
survive.

### 8.3 Origin basis

Candidate origin/basis values:

```text
provider-native
raiatea-aligned
raiatea-derived
user-asserted
unresolved
```

A Provider-native fact may be found through different channels. Channel is
recorded separately, for example:

```text
provider-normalized-view
provider-lossless-raw
provider-metadata
provider-diagnostic-stream
other-provider-channel
```

This preserves the E-04 lesson that useful facts can exist only in lossless/raw
Provider output without pretending that `lossless` is a different epistemic
origin from another Provider-native fact.

### 8.4 Mismatch/conflict is not evidence state

E-04 benchmark records used exact/mismatch/partial-match assessments. Production
E-05 must not leak benchmark gold semantics into every payload.

A mismatch should instead be modeled when two available facts/claims conflict,
or in a validation/assessment object. It is not a synonym for unavailable or
partial evidence.

## 9. ProcessingRun and ProcessingStage

### 9.1 `ProcessingRun`

A run represents one Raiatea-governed processing attempt and may exist even when
no Provider stage is started or no normalized output is produced.

Candidate minimum:

- run id;
- request/input references;
- ordered/related ProcessingStages;
- start/end timestamps;
- overall ProcessingOutcome;
- `outcome_basis` or equivalent orchestration derivation reference;
- diagnostics;
- provenance;
- produced raw/normalized/derived references;
- authoritative RightsDecisionRef/policy context.

The run outcome summarizes the orchestration result for downstream consumers. It
must be derived explicitly from the applicable policy decision, stage outcomes,
produced outputs and Raiatea validation/normalization evidence. It is never
implicitly copied from the final Provider stage.

### 9.2 `ProcessingStage`

A stage represents one attributable operation/route execution or an explicitly
recorded stage that was not started because a prerequisite/policy gate prevented
execution.

Candidate minimum:

- stage id;
- stage kind/purpose;
- parent/prior stage relation;
- ProviderRef + RouteProfileRef where Provider-backed;
- stage trigger/reason, when Raiatea initiated a fallback;
- inputs;
- ProviderEvidence / RawExtractionRef outputs;
- Provider-native status, if a Provider was invoked;
- stage ProcessingOutcome;
- diagnostics;
- provenance/timing.

Stage-kind vocabulary remains extensible. Initial evidence supports concepts such
as native extraction, OCR/fallback, alignment and normalization, but E-05a does
not freeze an exhaustive enum.

## 10. ProcessingOutcome is multi-dimensional

> Assertion status: `evidence-derived draft decision`

A single boolean or monolithic enum cannot represent E-04 outcomes safely.

The conceptual model separates technical/orchestration axes from the authoritative
Core policy decision.

### 10.1 Execution

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

This is Raiatea's normalized execution assessment. Provider-native status remains
separately preserved.

`not-started` is provisional vocabulary for an attempt/stage intentionally not
invoked because a prerequisite or Core policy decision prevented execution. The
semantic distinction is useful even if the later schema chooses another name.

### 10.2 Output availability

Candidate states:

```text
present
empty
unavailable
unknown
```

This axis answers only whether output exists/was observable. It deliberately does
not encode validity. A present output may still have degraded or invalid
integrity.

### 10.3 Completeness

Candidate states:

```text
complete
partial
not-established
not-applicable
```

`not-established` is crucial. Provider success alone cannot imply completeness.

### 10.4 Integrity

Candidate states:

```text
established
degraded
invalid
not-established
not-applicable
```

This axis carries validity/usability assessment separately from output presence.
For example, output may be `present` while integrity is `invalid` because the
evidence/output cannot be safely interpreted.

### 10.5 Policy disposition is not an independent outcome axis

The authoritative policy decision remains `RightsDecisionRef` (or a more general
Core policy-decision reference if later requirements justify it).

For downstream readability a run may expose a non-authoritative projection such
as:

```text
allowed
restricted
requires-authorization
denied
not-evaluated
```

but that projection is **derived from and traceable to the Core decision**. An
ExtractorPlugin or Provider cannot set it independently.

### 10.6 Why the technical axes remain separate

The following combinations occurred or are required by E-04:

```text
execution=succeeded
output=present
completeness=not-established
integrity=not-established
rights_decision=allowed
```

```text
execution=failed
output=empty
completeness=not-applicable
integrity=not-applicable
rights_decision=requires-authorization
```

```text
execution=succeeded
output=present
completeness=partial
integrity=established
rights_decision=allowed
```

```text
execution=not-started
output=unavailable
completeness=not-applicable
integrity=not-applicable
rights_decision=denied
```

The final state vocabulary is a later E-05 decision; the orthogonality and
policy-ownership boundary are the evidence-derived invariants.

### 10.7 Run outcome versus stage outcomes

Each ProcessingStage retains its own outcome. The run-level outcome is a Core
orchestration summary with an explicit derivation basis.

For example, a native stage may `succeed` with partial completeness, an OCR stage
may `succeed` with partial recovery, and a normalization stage may still produce
a useful representation. The run outcome must not be generated by a hidden rule
such as “take the worst stage” or “copy the last stage”.

## 11. ProviderEvidence / RawExtractionRef

> Assertion status: `evidence-derived draft decision`

Raw Provider output must remain addressable/inspectable without making the
Provider schema Raiatea's public contract.

Conceptually ProviderEvidence may include or reference:

- raw output artifact/blob/document;
- Provider-native status;
- Provider diagnostics/stdout/stderr where policy permits retention;
- Provider-native object/reference ids needed for traceability;
- explicit Provider fields mapped into EvidenceEnvelopes;
- evidence channel/locator information;
- route/profile/runtime provenance;
- raw-output fingerprint.

Large raw artifacts should be referenced by an artifact handle/ref rather than
inlined by semantic contract requirement. Storage/streaming mechanics are outside
E-05a.

## 12. NormalizedRepresentation

A `NormalizedRepresentation` is Raiatea's Provider-neutral downstream view.

It may contain:

- ContentUnits;
- Source Coordinate evidence;
- semantic-role evidence;
- reading-order relations;
- link/reference relations;
- EmbeddedAssetRefs;
- table/formula/other structured evidence families;
- diagnostics;
- lineage back to ProviderEvidence and normalization stages.

It is **not** required to be one canonical tree. E-05a prefers a composable
unit/relation model because E-04 showed that segmentation and structure vary by
route and that many evidence families are partial.

## 13. ContentUnit

> Assertion status: `provisional-decision`

A ContentUnit is a unit inside one NormalizedRepresentation. It is not the same
thing as Raiatea's durable Catalog Logical Identity.

Candidate concepts:

- representation-local unit id;
- content/surface evidence;
- semantic-role evidence;
- Source Coordinate evidence list;
- Provider-native references;
- group/parent evidence when explicitly available;
- provenance/basis;
- diagnostics.

The base contract should not require every unit to have exactly one semantic
role, coordinate or parent.

## 14. Semantic-role evidence

E-04 supports roles such as heading, paragraph, list item, code/preformatted and
caption, but also shows that Provider roles may be absent or wrong.

Semantic role should therefore be evidence-bearing, not an unconditional type of
the ContentUnit.

Conceptually:

```text
semantic_role: EvidenceEnvelope<SemanticRole>
```

Heading level, list metadata and other role-specific properties are separate
optional evidence. Unknown role must not force a generic paragraph claim unless
that is explicitly a Raiatea normalization decision with basis.

## 15. SourceCoordinate family

> Assertion status: `evidence-derived family; field representation provisional`

### 15.1 PDF geometric coordinate

Conceptual variant:

```text
PdfPageRegionCoordinate
├── page identity/index
├── region geometry
├── units
├── origin/convention
├── EvidenceEnvelope basis/provenance
└── optional precision/diagnostic metadata
```

Region may later support bbox/polygon/extensible geometry. E-05a does not freeze
one JSON geometry encoding.

### 15.2 EPUB logical/package coordinate

Conceptual variant:

```text
EpubLogicalCoordinate
├── resource/package reference
├── fragment/anchor?
├── spine/navigation context?
├── EvidenceEnvelope basis/provenance
└── traceability/normalization metadata?
```

Exact authored resource/fragment evidence and Raiatea-normalized/traceable
coordinates must remain distinguishable. Rendered page numbers are not canonical
EPUB coordinates.

### 15.3 Extension rule

New Source Families may add coordinate variants without changing the semantics of
existing variants. Candidate future examples include media time ranges, code
line/ranges and spreadsheet cell ranges, but they remain deferred.

## 16. RelationEvidence

> Assertion status: `evidence-derived draft decision`

A relation connects identifiable endpoints and carries evidence state and basis.

Conceptually:

```text
RelationEvidence
├── relation kind
├── source endpoint
├── target endpoint(s)
├── EvidenceEnvelope / basis
├── Provider-native refs?
└── diagnostics / ambiguity
```

Evidence-backed relation families already measured include:

- reading-order precedence;
- hyperlink source↔target;
- figure↔caption;
- table↔cell/topology relations;
- mathematical superscript/fraction relations.

No relation is promoted to Provider-native evidence from proximity, typography or
list position alone.

## 17. EmbeddedAssetRef

Figures/assets demonstrated that presence, geometry, asset identity, pixel
identity and caption association are independent.

An EmbeddedAssetRef therefore should not imply all those properties exist.
Candidate evidence includes:

- asset reference/handle;
- media type;
- byte/pixel fingerprint where available;
- dimensions/geometry evidence;
- Source Coordinate evidence;
- relation evidence to caption/content units;
- provenance.

Storage semantics remain outside E-05a.

## 18. Structured evidence families: tables and formulas

E-05a does not freeze one giant structured-document schema.

### 18.1 Tables

Evidence supports independently optional concepts for:

- table presence;
- table geometry;
- row/column topology;
- cell identity/binding;
- cell text;
- cell role/header evidence;
- cell geometry;
- unbound descendant text with table lineage.

An explicit table object with degraded topology remains representable without
inventing missing cells.

### 18.2 Formulas

Evidence supports independently optional concepts for:

- visible formula surface/tokens;
- formula/token geometry;
- Provider grouping diagnostics;
- explicit mathematical relations.

A raised glyph or Provider picture group does not by itself become superscript
or formula semantics.

Detailed machine schemas for tables/formulas remain a later child after the base
contract and extension pattern are accepted.

## 19. Diagnostic

Diagnostics capture observable limitations without conflating them with outcome
axes.

Conceptually a Diagnostic may include:

- Raiatea diagnostic code/category;
- severity;
- message/details;
- Provider-native diagnostic reference/message where retained;
- affected stage/unit/relation/coordinate;
- evidence origin/basis;
- provenance.

Provider-specific exception strings are evidence, not the stable cross-provider
contract vocabulary.

## 20. OCR/fallback lineage

B01-PDF-007 requires explicit multi-stage lineage.

A run may conceptually look like:

```text
stage native-1
  route = docling-native-no-ocr
  outcome.execution = succeeded
  outcome.completeness = partial/not-established
  output = ProviderEvidence A

stage ocr-1
  triggered_by = fallback decision derived from native evidence
  route = docling-rapidocr-locked
  input = OriginalArtifact or authorized derivative
  output = ProviderEvidence B
  recovery = partial evidence

stage normalize-1
  inputs = A + B
  reconciliation = unresolved where block origin cannot be proven
  output = NormalizedRepresentation C

run outcome
  derived_from = native-1 + ocr-1 + normalize-1 + applicable Core policy decision
```

The normalizer must be allowed to preserve both A and B without destructively
choosing one when identity is ambiguous.

Fallback trigger policy itself is orchestration/routing policy and remains a
later E-05/E-07 concern. E-05a only requires it to be traceable.

## 21. Restricted/security outcomes

The contract must support a run that terminates without normalized content.

For an access-controlled Source without an authorized credential route:

```text
ProcessingRun
├── RightsDecisionRef = requires-authorization/restricted
├── Provider-native failure/restriction evidence, if a Provider was invoked
├── execution = not-started/failed/rejected/unsupported as actually normalized
├── output = empty/unavailable/unknown as actually observed
├── diagnostics
├── provenance
└── NormalizedRepresentation = absent
```

If Core policy denies Provider execution before invocation, ProviderEvidence is
absent for the legitimate reason `not-started`; this is different from missing
Provider evidence after an attempted run.

A generic Provider failure and an explicit restriction signal are not the same
evidence. Likewise, absence of observed side effects is not proof of unmeasured
security properties.

## 22. RightsEvidence vs RightsDecisionRef

> Assertion status: `accepted boundary inherited from E-01/E-03; representation provisional`

The semantic contract separates:

### Rights evidence

May originate from Source metadata, user assertion, plugin/source connector or
licensed system evidence. It can be incomplete or unknown.

### RightsDecisionRef

References the authoritative Raiatea Core policy decision applicable to the
processing action. The decision may be allowed, denied, restricted or require
review/authorization.

Any policy-disposition value shown alongside ProcessingOutcome is only a
traceable projection of this decision and never an independent decision source.

An extractor does not authorize itself by reporting a permissive license string.
Unknown rights-sensitive state remains fail-closed according to Core policy.

Redistribution Rights remain separately governed by #131 and are not implied by
Processing Rights.

## 23. Provenance minimum

Every attempted ProcessingRun should be able to trace, where applicable:

- SourceReference / OriginalArtifact reference and fingerprint;
- request/correlation id;
- authoritative RightsDecisionRef/policy context;
- Provider id/version/revision, if invoked;
- RouteProfile id/version, if invoked;
- backend/mode;
- model/revision/payload fingerprint;
- material parameters;
- execution environment relevant to reproducibility;
- stage kind and parent/prior stage relation;
- stage start/end timestamps or explicit `not-started` reason;
- Provider-native status, if available;
- stage ProcessingOutcome;
- overall run ProcessingOutcome and its derivation basis;
- diagnostics;
- raw/provider evidence references and fingerprints;
- normalized/derived output references;
- normalization/alignment origin basis and Provider evidence channel where relevant.

Provenance is required even for failed/restricted runs because the attempted
processing or policy-gated request itself is evidence.

## 24. Evidence basis and normalization lineage

A normalized field/fact should be traceable to at least one of:

```text
ProviderEvidence
another normalized fact
Raiatea alignment/derivation operation
user assertion
policy decision
```

Normalization lineage should answer:

> Why does Raiatea believe this normalized fact, and which Provider/source
> evidence can be inspected to challenge or reproduce it?

This is stronger than merely storing `provider="docling"` on a document.

## 25. Scenario validation

The conceptual model must represent the accepted evidence below without special
Provider-specific fields.

### Scenario A — Provider success, completeness not established

B01-PDF-007 native route:

- Provider-native status: success;
- execution: succeeded;
- output: present;
- native text: present;
- visible raster target: absent;
- completeness: partial/not-established with explicit basis;
- applicable RightsDecision: allowed;
- later OCR stage may be triggered.

### Scenario B — Provider success on malformed input

B01 NEG-001 / Tika:

- Provider-native status: success;
- execution: succeeded;
- output: empty;
- Provider corruption signal: unavailable;
- integrity/completeness: not established;
- Raiatea diagnostic: malformed negative not surfaced;
- Provider-native success is preserved but not treated as contract-level truth.

### Scenario C — restricted Source

B01 NEG-002:

- authoritative RightsDecision: requires-authorization/restricted;
- Provider-native failure/restriction evidence if an eligible Provider was invoked;
- no unauthorized credential route supplied;
- output: empty/unavailable as observed;
- normalized output absent;
- ProcessingRun + provenance still present.

### Scenario D — text complete, structure partial

B01-PDF-005:

- visible table cell strings preserved;
- explicit table may be absent or degraded;
- topology/cell binding may be unavailable;
- no inferred row/column identity.

### Scenario E — surface math present, semantics unavailable

B01-PDF-006:

- formula glyph surface preserved;
- geometry partially available;
- explicit superscript/fraction relations unavailable;
- non-semantic Provider grouping may be retained with `origin_basis=provider-native`
  and its Provider evidence channel.

### Scenario F — EPUB text present, logical traceability partial

B02 Pandoc:

- text complete for the minimal fixture;
- reading order preserved;
- exact package/resource/fragment coordinate evidence partial/unavailable;
- semantic link present but authored target representation normalized;
- coordinate evidence remains partial rather than fabricated exact.

### Scenario G — security expectation not proven by success

B02 traversal-member Pandoc case:

- Provider-native status: success;
- expected reject/degrade signal absent;
- no controlled-root side effect observed;
- broader path-safety properties remain partial/not-measured;
- contract can retain success plus unresolved security evidence simultaneously.

### Scenario H — trustworthy explicit empty versus unavailable evidence

A Provider explicitly exposes an empty relation collection:

```text
evidence_state = present
value_state = empty
value = []
origin_basis = provider-native
```

A route that exposes no relation collection instead records:

```text
evidence_state = unavailable
value = absent
```

These states cannot collapse into one nullable field without losing E-04
semantics.

## 26. Compatibility boundary with Raiatea Plugin API #147

E-05 owns **domain semantics**. #147 will later define plugin mechanics.

A future `ExtractorPlugin` should be able to expose conceptually:

```text
extract.probe
    -> one or more RouteProfile/capability descriptions

extract.run
    -> ProviderEvidence + stage/run evidence compatible with E-05 semantics
```

The Plugin API may later define:

- manifest format;
- capability advertisement;
- lifecycle;
- permissions;
- process isolation;
- transport/envelope;
- version negotiation;
- artifact handles.

It must not define a second incompatible extraction-domain model or an
independent policy decision channel.

Likewise E-05 does not require JSON-RPC, gRPC or another transport.

## 27. What remains deferred after E-05a

E-05a intentionally does not decide:

- exact JSON field names or JSON Schema;
- stable public contract version numbers;
- database persistence model;
- API resources;
- Adapter SDK interfaces;
- plugin manifest/transport/lifecycle;
- artifact storage/streaming protocol;
- deterministic routing policy;
- benchmark-derived route selection thresholds;
- automatic OCR trigger policy;
- complete table/formula schemas;
- B-03/B-04/B-05 Source Coordinate variants;
- remote Provider eligibility;
- first-slice promotion;
- redistribution rights under #131.

## 28. Next E-05 child after conceptual acceptance

Only after this conceptual model survives review should E-05 create a bounded
child for a **candidate machine-readable contract** and conformance tests.

That child should:

1. encode only concepts classified `required-by-evidence` or deliberately
   accepted `optional-when-provider-exposes`;
2. include negative tests for evidence-state/value-state collapse,
   Provider/Raiatea origin confusion, invalid Source Coordinate coercion,
   run/stage outcome aggregation and restricted-output states;
3. remain independent of plugin transport;
4. demonstrate at least two existing benchmark mappers can adapt to it without
   leaking their native schemas;
5. still avoid selecting a production Provider or first slice.
