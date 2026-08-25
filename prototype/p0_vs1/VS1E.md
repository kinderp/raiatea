# VS1e — Deterministic search, Views and Smart Collections

> Parent vertical slice: #187  
> Micro-step: #197  
> Status: implementation in progress

## Functional increment

VS1d made the normalized contents of current local EPUB Sources persistent.
VS1e makes that knowledge directly usable:

> **Raiatea can deterministically find current Sources by facts present in their
> normalized content, save a reusable View, and maintain a Smart Collection whose
> rule is separate from its evaluated members.**

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

## Searchable facts

VS1e only exposes facts already established upstream:

- SourceReference id;
- media type;
- normalized surface text;
- normalized semantic unit type (`heading`, `paragraph`, `code` when present);
- EPUB logical resource identifier;
- provider id;
- extraction route profile.

It does not invent title, author, year or tag metadata merely to mimic the G-06
proof vocabulary.

## Freshness

The raw `CatalogStateStore` revision is audit evidence, not the sole search
freshness authority. Saving a View increments the catalog revision without
changing source/content truth.

VS1e therefore derives a canonical fingerprint of search-relevant upstream
VS1b/VS1c/VS1d facts. A search index is current only when its stored basis
fingerprint equals the newly recomputed upstream basis and the upstream source
state is itself current/fresh.

Consequences:

```text
save View only             -> index can remain fresh
change Source/content      -> index becomes stale
stale index                -> no current result ids
rebuild against new truth  -> fresh results again
```

## View boundary

A View is a logical lens only. It stores a normalized query and projection. It
has no path, move, write, delete, organization or other filesystem authority.

## Smart Collection boundary

The Smart Collection rule is authoritative. `current_members` and the evaluated
basis/revision are derived state. Re-evaluation may change membership without
rewriting the rule.

## Explicitly absent

- natural-language query parsing;
- LLM interpretation;
- embeddings/vector similarity;
- relevance ML;
- filesystem organization/mutation;
- a public frozen Catalog/query API;
- a production database/FTS-engine choice.
