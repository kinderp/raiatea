# P0 Elaboration

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 4.0.0-draft.2
>
> Last reviewed: 23 August 2026
>
> Accepted evidence baseline through: [PR #158](https://github.com/kinderp/raiatea/pull/158) / `c8a6d237`
>
> Current E-05 child: [#160](https://github.com/kinderp/raiatea/issues/160)
>
> Phase: **Elaboration — P0 risk reduction and architecture**
>
> Parent roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Phase gate: [`genesis/inception/08-inception-review.md`](../../genesis/inception/08-inception-review.md)

This directory contains evidence-oriented P0 Elaboration artifacts. Its purpose
is to reduce risk before a first product slice is promoted to `planned` work.

The current PDF/EPUB first slice remains a **working hypothesis**. Nothing in
this directory makes it implemented or planned by itself.

## E-01 — accepted source/rights/threat boundary

Accepted through #123 / PR #124 / `c1be73d`:

- [`source-taxonomy.md`](source-taxonomy.md) — Source Families, non-exclusive
  traits/profiles, candidate Benchmark Classes, Source Coordinate and
  quality-profile expectations;
- [`rights-data-boundary.md`](rights-data-boundary.md) — Processing Authority,
  Processing Rights, Redistribution Rights, sensitivity, retention and
  local/remote Provider data flows;
- [`threat-boundary.md`](threat-boundary.md) — trust zones, untrusted-content
  boundary, filesystem/path/provider threats and evidence required by G-02/G-03/
  G-04/G-05/G-07.

Acceptance records the boundary; it does not claim that a risk gate is satisfied
or that the first slice has been promoted.

## E-02 — accepted technology survey / build-buy-reuse

> Assertion status: `mixed`

Accepted through #125 / PR #126 / `18a4b5d`:

- [`technology-survey.md`](technology-survey.md) — current primary-source survey
  for extraction/OCR/conversion Provider candidates;
- [`provider-evidence-snapshot.md`](provider-evidence-snapshot.md) — immutable
  release/tag/commit index for version-sensitive Provider/runtime/license claims;
- [`provider-maintenance-snapshot.md`](provider-maintenance-snapshot.md) —
  observable release-cadence and compatibility-surface signals plus Raiatea
  re-benchmark implications, without subjective maturity scoring;
- [`provider-matrix.md`](provider-matrix.md) — Provider × Source Family,
  structure/coordinates, OCR, deployment, licensing and B-01/B-02 comparison;
- [`build-buy-reuse.md`](build-buy-reuse.md) — capability-level decisions across
  reuse, compose, build-thin-layer, benchmark-first and defer.

E-02 does not select a production Provider. Provider-published benchmark numbers
remain documented claims until Raiatea measures them with its own fixtures.
Mutable `main`/`master` links in narrative text are convenience references only;
the evidence snapshot is authoritative for the version observed by E-02.
Maintenance signals such as release frequency or major transitions are
architecture inputs, not quality scores or proof of stability.

### Remote-route eligibility rule

The survey may record that a hosted/API/external service exists, but **existence
is not route eligibility**. E-02 admits only local/self-hosted routes to the
current benchmark candidate set. An externally hosted Provider route remains
blocked until a separate, current evidence record covers the Provider data-policy
attributes required by E-01 — retention, training/improvement use, logging,
region/data residency, subprocessors and deletion controls as applicable — and
the rights/sensitivity policy explicitly makes that route eligible.

A self-hosted HTTP/service process inside the user's controlled environment is
not treated as an external remote Provider merely because it uses a network
protocol locally.

## E-03 — accepted rights-safe benchmark fixtures / gold data

> Assertion status: `mixed`

Accepted through #127 / PR #128:

- [`benchmark-fixture-plan.md`](benchmark-fixture-plan.md) — Provider-neutral B-01
  PDF and B-02 EPUB fixture families, negative/security cases and reproducibility
  requirements;
- [`benchmark-rights-manifest.md`](benchmark-rights-manifest.md) — provenance,
  Processing Rights, Redistribution Rights, retention, CI/public exposure and
  remote-route eligibility boundary;
- [`gold-data-contract.md`](gold-data-contract.md) — per-dimension gold semantics
  for content, hierarchy, reading order, Source Coordinates, links/assets,
  tables/formulas/code and expected failure/degradation states.

E-03 defines the material and reference semantics that E-04 measures. It does
not select a Provider or make the PDF/EPUB first slice `planned`.

### E-03 fixture principles

- public baseline should prefer project-created/generated fixtures;
- private/licensed Sources may inform private exploratory comparisons but cannot
  become public benchmark dependencies;
- PDF and EPUB use different Source Coordinate semantics; concrete EPUB anchor
  representation remains provisional;
- failure/security fixtures are not mixed into normal quality averages;
- gold data is Provider-neutral and may express exact, tolerance-based,
  relational, ordered, human-reviewed or intentionally ambiguous expectations;
- no fixture or gold format becomes the future P0 public extraction schema.

## E-04 — measured benchmark evidence

> Assertion status: `mixed`

E-04 has **measured evidence accepted through its child PRs**, including final
bounded B-01 evidence through PR #158. Parent issue #129 intentionally remains
open while E-05a synthesizes the evidence package and the project determines
formal E-04 closure. Do not read this section as a premature parent-phase
acceptance claim.

The benchmark harness and compact evidence under
[`benchmark/evidence/`](benchmark/evidence/) cover the bounded B-01 PDF set and
a minimal B-02 EPUB comparison.

### B-01 PDF evidence now includes

- born-digital native text and page geometry;
- multi-column reading order;
- semantic structure, lists, code-like content and links;
- figures/assets, geometry, pixel identity and caption relation evidence;
- tables, explicit/degraded topology and cell-binding distinctions;
- formula surface/geometry versus explicit mathematical relations;
- mixed/defective native text with a separately pinned OCR-capable route;
- malformed and access-controlled negative/security fixtures outside normal
  quality averages.

Final bounded B-01 child: #157 / PR #158 / `c8a6d237`.

### B-02 EPUB evidence includes

PR #134 compares a direct package-aware stdlib route and local Pandoc route for
minimal text/spine/order, navigation/link and negative/security fixtures.

Key measured boundary: EPUB Source Coordinates are package/resource/logical
anchors, not rendered page numbers. Text preservation and exact logical/package
traceability can diverge substantially by route.

B-02 coverage remains intentionally incomplete for images/captions/alt,
footnotes/endnotes, semantic table/code/MathML, larger composites and malformed
or missing-resource cases. Those gaps are recorded rather than silently treated
as measured success.

### E-04 conclusions that feed E-05

- Provider identity and RouteProfile identity are distinct;
- Provider-native `success` is not completeness/integrity truth;
- content preservation, semantic interpretation, relations and coordinates are
  independently partial;
- evidence state and observed value/cardinality are distinct;
- produced-output evidence is distinct from ProcessingOutcome;
- Raw Extraction / Provider Evidence must remain distinguishable from Raiatea
  Normalized Representation;
- Source Coordinates are source-class-specific and may be partial;
- OCR/fallback is an explicit lineage stage, not a silent replacement;
- restricted/requires-authorization is a valid Core policy disposition;
- benchmark gold shapes the contract but is not automatic production runtime
  knowledge;
- no universal quality score is justified.

The detailed synthesis is being drafted in
[`e04-evidence-synthesis.md`](e04-evidence-synthesis.md).

## E-05 — current Provider-neutral extraction contract exploration

> Assertion status: `provisional-decision`

E-05 parent issue: #159. Current bounded child: #160.

E-05a creates only:

- [`e04-evidence-synthesis.md`](e04-evidence-synthesis.md);
- [`provider-neutral-extraction-contract.md`](provider-neutral-extraction-contract.md);
- this phase-orientation update.

It deliberately does **not** freeze JSON Schema, Python classes, REST resources,
database tables, Adapter SDK, plugin transport or Provider selection.

The conceptual contract explores evidence-backed distinctions around:

- `ProviderRef` versus `RouteProfileRef`;
- `ProcessingOutcome` technical/orchestration state rather than `success: bool`;
- explicit produced-output references and evidence-state/value-state semantics;
- scoped completeness and integrity with explicit runtime basis;
- `ProviderEvidence` / Raw Extraction versus `NormalizedRepresentation`;
- typed/extensible Source Coordinates for PDF and EPUB;
- ContentUnits, relations, embedded assets and sparse structured evidence;
- OCR/fallback ProcessingStage lineage;
- diagnostics and provenance;
- Core-owned RightsDecision/policy authority kept separate from technical
  ProcessingOutcome.

#147 `ExtractorPlugin` is a downstream consumer of E-05 semantics. Plugin
manifest, lifecycle, permissions, isolation and transport remain separate design
work and must not introduce a parallel extraction result model.

## E-02 survey candidates and current evidence boundary

The accepted survey records primary-source evidence for:

- Docling;
- Marker;
- MinerU;
- Unstructured;
- Apache Tika;
- GROBID;
- OCRmyPDF + Tesseract;
- PaddleOCR / document-VL routes;
- Pandoc;
- EPUB-specific parsing options.

E-04 measured only bounded, reproducible routes justified by its child issues.
Unmeasured survey candidates remain candidates, not implicit failures and not
selected Providers. New Provider measurements require a separate evidence-based
promotion; E-05a does not add routes merely to enlarge the matrix.

## Elaboration sequence

The accepted Inception Review authorizes a bounded sequence:

1. source taxonomy + rights/threat boundary — **completed** (#123/#124);
2. current technology survey/build-buy-reuse — **completed** (#125/#126);
3. rights-safe benchmark corpus/fixture/gold-data design — **completed** (#127/#128);
4. source-class benchmark contract and baseline measurements — **measured child evidence; parent #129 open pending synthesis/closure**;
5. Provider-neutral P0 contract exploration — **current** (#159; E-05a #160);
6. Alfred reconciliation/integration evidence — after the relevant E-05 contract boundary is accepted;
7. evidence packages for G-01..G-07;
8. separate first-slice promotion decision.

## Invariants

- P0 is planned, not implemented.
- Source is a workflow/evidentiary role, not a universal file/catalog entity.
- Location/path is not Logical Identity.
- Alfred Observation does not grant processing or mutation authority.
- Provider and Adapter are distinct.
- Provider and RouteProfile are distinct.
- Provider-native status is evidence, not Raiatea completeness/integrity truth.
- ProcessingOutcome does not replace produced-output/field-level evidence state.
- Raw Extraction / Provider Evidence and Normalized Representation are distinct.
- Provider-native and Raiatea-derived facts retain distinct evidence basis.
- Missing/partial/unavailable/ambiguous evidence is never silently converted to
  empty, zero or success.
- Explicit empty is present evidence with an empty value, not unavailable
  evidence.
- Completeness is scoped and requires an explicit runtime basis; it never implies
  universal document completeness.
- Benchmark gold does not become hidden production runtime knowledge.
- PDF and EPUB Source Coordinate semantics remain distinct and extensible.
- OCR/fallback stages preserve route/profile and lineage.
- Processing Authority, Processing Rights and Redistribution Rights are
  distinct.
- Rights evidence does not authorize processing; Raiatea Core owns the policy
  decision.
- No Provider, database, vector store, graph store or public schema is selected
  by E-01..E-05a evidence/model exploration.
- Externally hosted Provider routes mentioned by E-02 are existence evidence
  only and remain ineligible until the remote-route rule above is satisfied.
- Provider-native representations such as DoclingDocument, Marker JSON, MinerU
  middle JSON, Unstructured Elements, Pandoc AST or GROBID TEI do not become
  Raiatea's public/core contract merely because an Adapter or benchmark mapper
  consumes them.
- Benchmark gold and benchmark result JSON are not the future P0 public schema.
- No universal weighted extraction quality score is introduced.
- Automatic organization, NL search, translation/layout, multi-output DAG,
  Durex integration, physical-holding linking, TheBitLab projection and P1-P7
  remain behind their accepted gates.
