# G-06 deterministic search, View and Smart Collection proof

> Evidence child: [#181](https://github.com/kinderp/raiatea/issues/181)  
> E-07 parent: [#178](https://github.com/kinderp/raiatea/issues/178)  
> P0 parent: [#106](https://github.com/kinderp/raiatea/issues/106)

This directory contains a **proof-only** deterministic catalog/search model for
G-06. It deliberately comes before natural-language search so a future LLM
interpreter can only compile into inspectable deterministic criteria rather than
becoming the source of catalog truth.

## Invariants under proof

```text
structured query plan        != natural-language interpretation
View                          != filesystem organization
Smart Collection rule        != evaluated/current members
stale index                   != current catalog truth
unknown criterion             != silently ignored criterion
input iteration order         != result order
```

## Proof behavior

The bounded vocabulary supports explicit filters for:

- item id;
- title;
- media type;
- tag;
- extracted text;
- year.

Plans are normalized into an inspectable criterion tuple. Unknown fields,
operators and sort fields fail closed. Result sorting has an explicit stable
`item_id` tie-breaker and is tested against reversed input ordering.

`CatalogSnapshot` carries both catalog and index revisions. A revision mismatch
returns `freshness=stale`, no result ids and `blocked_reason=index-not-current`;
it can never be labelled fresh accidentally.

A `ViewDefinition` contains only a query plan and projection. It has no path,
move, write, delete or organization fields. `SmartCollection` stores the
normalized rule separately from `current_members` and an `evaluated_revision`;
re-evaluation against a changed fresh snapshot changes members deterministically
without rewriting the rule.

## Run

From this directory:

```bash
python -m unittest test_search_view_proof.py -v
```

The dedicated Actions workflow runs compile + tests on Linux and Windows with
Python 3.10 and 3.12.

## Explicitly absent

- natural-language parser;
- LLM;
- embeddings/vector search;
- relevance/ranking ML;
- production database/search engine choice;
- filesystem mutation;
- production API/schema commitment.

Passing this proof contributes evidence to G-06 only. It does not promote or
implement vertical slice 1.
