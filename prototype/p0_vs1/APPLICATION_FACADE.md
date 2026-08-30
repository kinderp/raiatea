# Raiatea Application Facade — first executable GUI read boundary

Status: **Prototype / review in progress**  
Issue: #214  
PR: #215  
Architecture input: `architecture/gui-application-boundary.md`

## Purpose

This slice turns the accepted GUI/Application architecture boundary into executable first-party Python without selecting a frontend framework or transport.

The facade is deliberately small in authority:

```text
future GUI / transport adapter
          |
          v
RaiateaApplicationFacade
          |
          +-- Raiatea catalog / reconciliation truth
          +-- deterministic SearchViewService
          +-- ExtractionReader
                 |
                 +-- current InRepoExtractionReader
                 \-- future Source Plane client
```

The facade **composes** accepted truth. It does not create a second catalog, extraction model or search engine.

## Current supported read surfaces

### Library

`library_page()` exposes paginated catalog items with:

- application navigation ref;
- catalog entry ref;
- current `logical_candidate_ref`, explicitly not a final universal Logical Identity;
- stored-instance ref;
- optional current SourceReference id;
- user-facing fallback name;
- media type;
- authorized-scope **relative** Location;
- availability and history count;
- byte-length/fingerprint summary;
- extraction/current-representation summary when established;
- catalog/content freshness;
- warning assessment only when measured;
- capability declarations.

Absolute host roots/paths are not part of this read model.

### Source Detail

`source_detail()` composes one capability-driven object for EPUB and PDF rather than exposing format-specific frontend pages.

Potential panels are derived from current evidence:

```text
original
semantic
provider-evidence
processing
provenance
history
```

The first implementation uses the same shape for current VS1d EPUB extraction and PDF1b Poppler extraction.

### Representation content

`representation_page()` exposes bounded pages of normalized content units. Each unit contains only the first application projection required by the GUI:

```text
unit_ref
surface
semantic_role
coordinate
```

Provider-native records and E-05 record maps remain behind `ExtractionReader`.

The cursor is bound to the representation content basis, so a changed representation invalidates an old cursor instead of silently continuing over different content.

A representation id is not sufficient authority to read old content. Before delegating to `ExtractionReader`, the facade re-composes current catalog/Source/extraction truth and requires the requested representation to remain reachable from a current SourceReference. A stale catalog or a superseded extraction therefore blocks a direct representation read even if the caller retained an older id.

### Search

`search_page()` delegates actual query semantics to accepted `SearchViewService` and adds application-level pagination/composition.

Important fences:

- no separate GUI search semantics;
- stale VS1 index => no current hits;
- non-current upstream => no current hits;
- a search/catalog composition-basis race => no current hits;
- a source id missing from the current Library projection => no current hits;
- index not yet built => explicit blocked state rather than fabricated empty current search.

PDF search is **not** invented here. Until PDF1d extends the accepted source-agnostic search path, the facade returns exactly what current `SearchViewService` can establish.

## Current extraction adapter

`InRepoExtractionReader` is a temporary compatibility adapter over:

- accepted `vs1d.extractions` for EPUB;
- accepted `pdf1b.current_extractions` for Poppler PDF.

It validates the existing product state, locates the E-05 ProcessingRun / ProviderEvidence / NormalizedRepresentation records and projects only application-safe summaries.

This knowledge of current persistence layout is intentionally concentrated in one adapter.

A future Source Plane client must implement the same `ExtractionReader` read seam rather than forcing the GUI to know whether execution came from:

```text
local child process
local Source Plane daemon
container worker
replicated worker pool
managed Source Plane service
```

Deployment topology is not GUI knowledge semantics.

## Freshness and SourceReference rule

A persisted SourceReference may remain structurally valid after filesystem activity. The facade therefore promotes it to **current application content** only while Raiatea catalog reconciliation is `fresh` and the reference still matches the current known-present catalog entry.

When the catalog is stale/reconcile-required:

- Library entries may remain visible as last-known catalog state;
- counts are marked `last-known`;
- current SourceReference is withheld;
- current extraction is not claimed through that Source;
- `view-original` / the `original` panel are withheld;
- direct normalized-representation reads are rejected;
- search is blocked from returning current hits.

Last-known Location remains displayable as catalog history/state evidence; it does not imply that current source bytes are readable.

## Warning / diagnostic rule

Zero is a claim.

The facade therefore reports warning count `0` only when ProviderEvidence contains a measured diagnostics list and no warning-severity entry is present.

If warning evidence is not established, the result is:

```text
state = not-established
count = null
```

rather than an invented zero.

## Pagination

Application cursors are opaque, versioned and bound to a deterministic **application-visible result basis**. They are not filesystem paths, store offsets or VS1 proof-limit leakage.

The basis includes the composed rows, not only the catalog entry list or search source ids. This matters because SourceReference state, extraction status, provider/profile summaries, warnings and capabilities can change without changing the catalog row identity. Continuing with an old cursor after such a change fails as `application-cursor-stale` rather than mixing two result snapshots.

Representation cursors remain independently bound to the exact representation-unit basis.

Current maximum page size is a facade safety bound, not a claim that the whole Library fits in memory or that future remote/federated paging will use the same storage strategy.

## Explicitly not a public API freeze

This prototype does **not** decide:

- REST vs GraphQL vs local IPC;
- final JSON field compatibility/versioning;
- frontend technology;
- public authentication/multi-user semantics;
- remote/federated Library behavior;
- natural-language/vector search;
- GUI command/write surface;
- drag/drop docking implementation.

The evidence sought by #214 is narrower: prove that a truthful, source-agnostic, paginable application facade can sit above the existing product without exposing prototype internals and can later substitute Source Plane behind one extraction-read seam.

## Validation strategy

`test_application_facade.py` covers:

- real accepted EPUB catalog/discovery/extraction/search behavior;
- application-level Library and search pagination;
- stale catalog/search fences;
- cursor invalidation after catalog-basis change;
- absence of raw persistence/Provider authority and absolute temporary paths in public models;
- replacement of extraction with a fake Source Plane-compatible reader;
- dependency-light PDF1b contract state proving the same Source Detail/Representation shape without requiring a real Poppler executable.

`test_application_facade_freshness.py` covers the explicit current-original capability fence: stale catalog state may expose last-known relative Location but not `view-original`, an `original` panel, current SourceReference or current extraction.

`test_application_facade_result_basis.py` covers the review findings that are easy to miss in a happy path:

- direct reads through a retained representation id are blocked after catalog freshness is lost;
- a superseded extraction representation id is not accepted merely because its Provider data still exists;
- Library cursors invalidate when visible extraction state changes without a catalog-row change;
- Search cursors invalidate when composed Library/extraction rows change while the deterministic search source-id set remains the same.

Real Poppler execution remains the responsibility of the existing PDF1b real-provider acceptance workflow; the facade test does not counterfeit that evidence.
