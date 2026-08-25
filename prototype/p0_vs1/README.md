# P0 vertical slice 1 prototype

> Parent promotion: [#187](https://github.com/kinderp/raiatea/issues/187)  
> Current micro-step: [#188](https://github.com/kinderp/raiatea/issues/188) — VS1a  
> Status: **implementation in progress**

This directory contains the executable product-prototype path for the first
promoted Raiatea vertical slice.

The first source route selected by #187 is local B-02 EPUB through the accepted
`direct-epub-stdlib` route. VS1a does **not** implement extraction yet; it builds
the Core-owned authority and persistence boundary required before real content
can safely cross the Plugin API.

## VS1a scope

VS1a will provide:

- Core-owned local filesystem scope registration;
- opaque read `AssetHandle` issuance compatible with the accepted Plugin Runtime
  v1b semantics;
- OS-aware safe content access that rejects root/symlink/reparse escape before
  bytes are returned;
- Core-owned write-once output targets with lease and byte-budget enforcement;
- an internal, canonical, atomic, integrity-checked catalog state envelope.

## Explicit boundary

This prototype does not create a second Plugin API contract and does not freeze a
public catalog schema. Accepted contracts under `elaboration/p0/contracts/`
remain authoritative.

Later sequential increments own:

- VS1b — Alfred Observation adapter + inventory/reconciliation;
- VS1c — local SourcePlugin product path;
- VS1d — direct EPUB extraction + E-05 persistence;
- VS1e — deterministic search/View/Smart Collection;
- VS1f — export/restore + complete end-to-end acceptance.

Remote Providers, filesystem organization/mutation, natural-language search,
embeddings/vector search, translation, Durex and a generic cross-project Module
Runtime remain outside VS1.
