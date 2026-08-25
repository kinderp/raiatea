# VS1e — Deterministic search, Views and Smart Collections

> Parent vertical slice: #187  
> Micro-step: #197  
> Pull request: #198  
> Status: final candidate under review

## Functional increment

VS1d made the normalized contents of current local EPUB Sources persistent.
VS1e makes that knowledge directly usable:

> **Raiatea can deterministically find current Sources by facts present in their
> normalized content, explain which normalized units caused a content match,
> save a reusable View, and maintain a Smart Collection whose rule remains
> separate from its evaluated members.**

The first product search is deliberately structured and explainable. Natural-
language/LLM/vector search is not part of VS1e.

## Product path

```text
current VS1b / VS1c / VS1d facts
        ↓
Core validates current-source alignment
        ↓
upstream search-basis fingerprint
        ↓
deterministic path-free search index
        ↓
structured QueryPlan
        ↓
SearchResult
   ├── View = saved query + projection
   └── Smart Collection = saved rule + derived current members
```

## What can be searched now

VS1e exposes only facts actually established by the previous slice:

- `source_ref_id` — exact match;
- `media_type` — exact match;
- `extracted_text` — casefolded substring match over normalized surface text;
- `semantic_type` — membership match for values such as `heading`, `paragraph`
  or `code` when those values exist upstream;
- `resource` — EPUB logical resource match, for example `OEBPS/ch1.xhtml`;
- `provider_id` — exact match;
- `route_profile` — exact match.

`OEBPS/ch1.xhtml` is a coordinate inside the EPUB package. It is not the host
filesystem path of the user's document. User root, Location and host path do not
enter the search index.

VS1e does not invent title, author, year or tag metadata merely to imitate the
older G-06 proof vocabulary. Those fields can become searchable only after a
future upstream contract actually establishes them.

## QueryPlan and fail-closed behavior

The query language is intentionally small:

```text
criteria AND criteria ...
+ one explicit sort field/direction
```

Criteria are canonicalized and sorted, so equivalent criterion order produces
the same normalized plan and the same result. Unsupported fields/operators,
wrong scalar types, regex/script/path actions, natural-language prompts,
embeddings and vector fields fail closed.

This matters for future AI-assisted search: an LLM may later help compile a user
request into this structured language, but it must not bypass the deterministic
query contract.

Results are Source/document-level. When content/unit criteria are involved, each
hit includes bounded `matched_unit_refs` so Raiatea can explain which normalized
content units contributed evidence for that Source-level match.

## Deterministic ordering

The first product sorts by one of:

- `source_ref_id`;
- `media_type`;
- `unit_count`.

An explicit ascending `source_ref_id` tie-break is preserved even when the
primary sort is descending. Result order therefore does not depend on Python
list/dictionary iteration order or the order in which upstream records happened
to be serialized.

## Freshness

The raw `CatalogStateStore` revision is audit evidence, not the sole search
freshness authority. Saving a View increments the catalog revision without
changing source/content truth.

VS1e derives a canonical fingerprint of search-relevant upstream VS1b/VS1c/VS1d
facts. This includes current-source facts and normalized extraction content. A
current Location participates only in the internal freshness basis and is never
exposed in the index.

Consequences:

```text
save View only             -> upstream basis unchanged -> index remains fresh
change Source/content      -> upstream basis changes   -> index becomes stale
observation state not fresh-> search is stale          -> zero current results
rebuild against new truth  -> new matching basis       -> fresh results again
```

A stale search result contains an explicit reason and **no `source_ids` or hits**.
Old results are never returned with a stale label as though callers should decide
whether they are safe enough.

## Single-snapshot consistency

One search/View/Smart operation loads one catalog snapshot and keeps using that
same snapshot for:

- the saved definition/rule;
- the index;
- upstream freshness recomputation;
- result matching;
- View projection;
- Smart Collection membership;
- expected-revision persistence fencing when the operation writes state.

Review finding VS1E-F1 closed an earlier implementation that reloaded the catalog
inside View/Smart evaluation. That could have combined an older saved definition
with a newer index. Dedicated regressions now forbid evaluation from falling
back through the public reloading `search()` method.

## View boundary

A View is a logical lens only:

```text
View = normalized QueryPlan + projection
```

The supported projection can expose Source ref, media type, fingerprint,
provider, route and unit count. A View has no path, move, write, delete,
organization or other filesystem authority.

Saving a View does not rebuild the search index or make it stale merely because
the catalog revision changed. Evaluation does inherit the upstream freshness
fence: a stale index cannot produce a current View result.

## Smart Collection boundary

A Smart Collection persists:

- a stable collection id;
- a normalized QueryPlan rule;
- `current_members` as derived state;
- the upstream basis fingerprint used for that evaluation;
- the catalog revision at which the evaluation was recorded for audit.

The rule is authoritative. Members are not.

The product test creates an initially empty rule for `Inert Active Content`, then
adds a real third EPUB, runs reconciliation -> Source discovery -> extraction ->
index rebuild and re-evaluates the collection. Membership changes to include the
new Source while the rule remains byte-equivalent.

A stale index cannot update Smart Collection members.

## Persisted internal state

VS1e adds an internal/revisable payload containing:

```text
vs1e
  index
  views[]
  smart_collections[]
```

The index contains only path-free Source facts plus bounded searchable normalized
units. `built_from_catalog_revision` is audit metadata; the semantic freshness
authority is `upstream_basis_fingerprint`.

All VS1e writes use the same expected-revision guard already accepted for the
single-Core-owner first slice. A concurrent catalog write rejects a stale index,
View or Smart Collection write instead of overwriting newer state.

## Functional tests

The product suite runs the real upstream path for two generated EPUBs before
searching:

```text
fixture
 -> inventory/reconcile
 -> SourcePlugin
 -> SourceReference
 -> ExtractorPlugin
 -> Core E-05 normalization
 -> VS1e index
```

It proves searches for real content including `Introduction` and `Details`,
semantic headings, EPUB resources, provider and route. It also exercises
fresh/stale transitions, deterministic input reordering, View persistence,
Smart Collection growth, malformed QueryPlans and concurrent writes.

The accepted G-06 proof is re-run as a regression, but the product vocabulary is
restricted to facts actually present after VS1d.

## Resolved findings

- **VS1E-F1 — snapshot consistency:** View/Smart evaluation initially reloaded
  the catalog through public `search()`. Evaluation now uses one loaded snapshot
  end-to-end; dedicated tests forbid the old behavior.
- **VS1E-F2 — malformed query type handling:** non-string operator/sort/field
  shapes could raise incidental Python `TypeError` instead of a controlled
  contract rejection. Query scalar types are now validated before set/map
  membership and hostile-shape regressions require `SearchContractError`.

## Functional boundary after VS1e

After VS1e this statement becomes true:

> **Raiatea can search the actual normalized contents of current local EPUB
> Sources with deterministic structured filters, save those searches as logical
> Views, and maintain dynamic Smart Collections without moving or rewriting the
> underlying documents.**

What it still cannot do in this slice is interpret free-form language, perform
semantic/vector similarity, rank results with ML or expose a complete end-user
UI. Those remain later layers over this deterministic truth-preserving core.

## Explicitly absent

- natural-language query parsing;
- LLM interpretation;
- embeddings/vector similarity;
- relevance ML;
- regex/scripting query execution;
- filesystem organization/mutation;
- title/author/year/tag fields not established upstream;
- a public frozen Catalog/query API;
- a production database/FTS-engine choice;
- PDF/Docling/OCR;
- final export/restore end-to-end evidence (VS1f).
