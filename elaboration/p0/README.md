# P0 Elaboration

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 2.0.0
>
> Last reviewed: 21 August 2026
>
> Accepted through: [PR #126](https://github.com/kinderp/raiatea/pull/126)
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

Accepted through #125 / PR #126:

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
remain documented claims until Raiatea runs E-04 fixtures. Mutable `main`/
`master` links in narrative text are convenience references only; the evidence
snapshot is authoritative for the version observed by E-02. Maintenance signals
such as release frequency or major transitions are architecture inputs, not
quality scores or proof of stability.

### Remote-route eligibility rule

The survey may record that a hosted/API/external service exists, but **existence
is not route eligibility**. E-02 admits only local/self-hosted routes to the
candidate E-04 benchmark set. An externally hosted Provider route remains
blocked until a separate, current evidence record covers the Provider data-policy
attributes required by E-01 — retention, training/improvement use, logging,
region/data residency, subprocessors and deletion controls as applicable — and
the rights/sensitivity policy explicitly makes that route eligible.

A self-hosted HTTP/service process inside the user's controlled environment is
not treated as an external remote Provider merely because it uses a network
protocol locally.

## E-02 survey candidates

The accepted survey records current primary-source evidence for:

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

The list is not a product endorsement and remains subject to E-03/E-04 evidence.

## Elaboration sequence

The accepted Inception Review authorizes a bounded sequence:

1. source taxonomy + rights/threat boundary — **completed** (#123/#124);
2. current technology survey/build-buy-reuse — **completed** (#125/#126);
3. rights-safe benchmark corpus/fixture design — **next**;
4. source-class benchmark contract and baseline measurements;
5. Provider-neutral P0 contract exploration;
6. Alfred reconciliation/integration evidence;
7. evidence packages for G-01..G-07;
8. separate first-slice promotion decision.

## Invariants

- P0 is planned, not implemented.
- Source is a workflow/evidentiary role, not a universal file/catalog entity.
- Location/path is not Logical Identity.
- Alfred Observation does not grant processing or mutation authority.
- Provider and Adapter are distinct.
- Raw Extraction and Normalized Representation are distinct.
- Processing Authority, Processing Rights and Redistribution Rights are
  distinct.
- No Provider, database, vector store, graph store or public schema is selected
  by the E-01/E-02 evidence packages.
- Externally hosted Provider routes mentioned by E-02 are existence evidence
  only and remain ineligible for E-04 until the remote-route rule above is
  satisfied.
- Provider-native representations such as DoclingDocument, Marker JSON, MinerU
  middle JSON, Unstructured Elements or GROBID TEI do not become Raiatea's
  public/core contract merely because an Adapter consumes them.
- Automatic organization, NL search, translation/layout, multi-output DAG,
  Durex integration, physical-holding linking, TheBitLab projection and P1-P7
  remain behind their accepted gates.
