# P0 Elaboration

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
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

## Current micro-step — #123

The first Elaboration child defines the boundary needed before Provider survey
and benchmark design:

- [`source-taxonomy.md`](source-taxonomy.md) — Source Families, non-exclusive
  traits/profiles, candidate benchmark classes, coordinate and quality-profile
  expectations;
- [`rights-data-boundary.md`](rights-data-boundary.md) — Processing Authority,
  Processing Rights, Redistribution Rights, sensitivity, retention and
  local/remote Provider data flows;
- [`threat-boundary.md`](threat-boundary.md) — trust zones, untrusted-content
  boundary, filesystem/path/provider threats and evidence required by G-02/G-03/
  G-04/G-05/G-07.

All three are Draft until #123's review gate is completed.

## Elaboration sequence

The accepted Inception Review authorizes a bounded sequence:

1. source taxonomy + rights/threat boundary — **current**;
2. current technology survey/build-buy-reuse;
3. rights-safe benchmark corpus/fixture design;
4. source-class benchmark contract and baseline measurements;
5. provider-neutral P0 contract exploration;
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
- No Provider, database, vector store, graph store or schema is selected by this
  evidence package.
- Automatic organization, NL search, translation/layout, multi-output DAG,
  Durex integration, physical-holding linking, TheBitLab projection and P1-P7
  remain behind their accepted gates.
