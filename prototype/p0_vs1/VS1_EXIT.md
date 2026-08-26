# Vertical Slice 1 exit — accepted local EPUB product slice

> Exit issue: #201  
> Promotion parent: #187  
> P0 parent: #106  
> Accepted implementation baseline: `cc2be6b541342489a4d865d2188840a18177d0db`  
> Scope: **local EPUB / `direct-epub-stdlib` / local-only**

## 1. Exit decision

Vertical Slice 1 is ready to be accepted as one bounded end-to-end product slice.

The accepted functional claim is:

> **Raiatea can take an explicitly authorized local EPUB collection, maintain a
> conservative live catalog, expose current Sources through a replaceable local
> SourcePlugin, extract current document content through an official local
> ExtractorPlugin, retain E-05 provenance and EPUB logical source coordinates,
> search current content deterministically, evaluate reusable Views and Smart
> Collections, export authoritative knowledge state deterministically, restore
> it against the real local collection, and reproduce the same bounded
> user-visible knowledge results without remote Providers or filesystem
> mutation.**

This is the first accepted product slice. It is not a claim that the full Raiatea
vision is complete.

## 2. Accepted implementation chain

| Step | Accepted evidence | Functional capability added |
| --- | --- | --- |
| VS1a | #188 / PR #189 / `0bd70df` | Core-owned local scope, safe opaque AssetHandles, write-once outputs, integrity-checked catalog store |
| VS1b | #190 / PR #191 / `8321d22` | Alfred JSONL adapter, bounded EPUB inventory, conservative identity/Location reconciliation, stale/reconcile-required state |
| VS1c | #192 / PR #193 / `188fa08` | replaceable out-of-process LocalSourcePlugin and path-free SourceReferences over current catalog truth |
| VS1d | #195 / PR #196 / `e087da39` | direct EPUB provider observation, Core-owned E-05 normalization, persistent text/structure/coordinates/provenance |
| VS1e | #197 / PR #198 / `aeb7149` | deterministic structured search, Views, Smart Collections and freshness fencing |
| VS1f | #199 / PR #200 / `cc2be6b5` | deterministic authority backup, fail-closed physical restore and complete end-to-end reproducibility |

All six implementation issues are closed as completed. No VS1 implementation PR
remains open. PR #95 is part of the separate classroom-pilot stream #93 and is
not a dependency of this slice.

## 3. What a user can now do functionally

Within the supported first-slice boundary, Raiatea can execute this chain:

```text
explicitly authorize a local folder
        ↓
discover current EPUB files safely
        ↓
retain conservative Stored Instance / Logical Identity candidates
        ↓
track Location changes without making path the identity
        ↓
expose current items as path-free SourceReferences
        ↓
apply Core-owned rights/policy decisions
        ↓
run the official direct EPUB ExtractorPlugin out of process
        ↓
retain provider observation separately from Core normalization
        ↓
persist text, structure, reading order and EPUB logical coordinates
        ↓
search current extracted content with structured deterministic filters
        ↓
save a View
        ↓
save/re-evaluate a Smart Collection
        ↓
export authoritative catalog knowledge deterministically
        ↓
restore into an empty catalog
        ↓
reconcile against the real local files
        ↓
rebuild derived search/Smart state
        ↓
reproduce the same bounded user-visible results
```

Examples already exercised in product tests include finding content such as
`Introduction` and `Details`, searching semantic heading units, filtering EPUB
logical resources, and changing Smart Collection membership after a legitimate
new EPUB enters the collection.

## 4. Correctness and freshness semantics

### Filesystem truth

- pathname is mutable `Location`, not logical identity;
- equal bytes at distinct Locations do not cause destructive auto-merge;
- rename/move preserves identity candidates and Location history when evidence
  is consistent;
- delete is Location-level missing evidence, not logical purge;
- lost/offline scope remains unavailable/unknown rather than mass deletion;
- Alfred overflow/stale/sequence gaps force bounded reconciliation;
- successful observer recovery alone does not assert catalog equality.

### Source and extraction truth

- SourcePlugin does not rescan the user filesystem and cannot become catalog
  truth;
- SourceReference carries opaque catalog identity/fingerprint facts, not host
  path authority;
- extractor receives a Core-private source copy through an opaque handle, not
  the user's source path;
- Runtime `completed` is not confused with an accepted extraction outcome;
- provider observation is distinct from Core-owned E-05 normalization;
- source bytes are verified again before extraction publication so a physical
  change cannot silently publish stale content;
- catalog-revision fences reject results produced against stale catalog state.

### Search truth

- index freshness is based on current search-relevant upstream facts, not merely
  raw store revision;
- stale search returns no current source ids/hits and an explicit stale reason;
- Views are query + projection only;
- Smart Collection rule is authority, while current members are derived state;
- saving a View does not itself stale a current index;
- changing source/content/reconciliation truth does.

### Restore truth

- backup is knowledge/catalog backup, not document-byte backup;
- search index and Smart member cache are not backup authority;
- restore is empty-store-only for VS1;
- restored source state is forced unverified/reconcile-required;
- real bounded inventory must succeed before publication;
- changed, missing or unexpected physical sources prevent a false successful
  restore;
- search index and Smart members are rebuilt from restored authority + current
  physical truth.

## 5. Rights and authority boundary

VS1 preserves the distinctions:

```text
Processing Authority
!= Processing Rights evidence
!= Redistribution Rights
```

The benchmark licensing decision for project-created fixtures remains
benchmark-scoped. It does not silently license Raiatea Core or authorize remote
processing.

For the promoted extraction path, byte processing is Core-gated and
fail-closed. `unknown`, `requires-review` and `known-restricted` are not silently
converted to `known-permitted` for extraction.

No SourcePlugin or ExtractorPlugin may create or widen a RightsDecision.

## 6. Security and platform boundary

Accepted claims:

- Core owns the authorized filesystem scope;
- external/plugin records cannot widen the scope root;
- POSIX reads use root-FD/component no-follow behavior;
- Windows reads use opened-handle final-path/reparse checks;
- opaque public handles expose no host source path;
- plugin source/output I/O is Core-owned, bounded and tamper-checked;
- child environment is intentionally bounded so ambient Core credentials are
  not inherited through the VS1 product process boundary;
- source filesystem mutation authority is absent.

Important residuals:

- live Alfred Observation evidence is currently **Linux/inotify** only;
- Windows CI proves Raiatea product/contracts and Windows safe-file behavior,
  not a Windows Alfred backend;
- official Source/Extractor plugins are same-user local processes; VS1 does not
  claim an OS-level hostile third-party plugin sandbox;
- production authentication/ACLs, marketplace/PKI and stronger untrusted-plugin
  isolation remain future work.

## 7. Integrated positive evidence

The accepted VS1f E2E test exercises the entire product path over real
project-created EPUB fixtures:

1. register explicit Core scope;
2. generate real B-02 EPUB fixtures;
3. inventory/reconcile;
4. discover path-free Sources through LocalSourcePlugin;
5. apply local processing rights decision;
6. extract through the real official direct EPUB ExtractorPlugin;
7. persist Core-owned E-05 content/provenance;
8. build deterministic search index;
9. execute known content queries;
10. save/evaluate a View;
11. save/evaluate a Smart Collection;
12. rename a real EPUB;
13. observe stale search rather than false-current results;
14. reconcile while preserving identity + Location history;
15. rebuild search/Smart derived state;
16. export byte-deterministic authority backup;
17. restore into a new empty CatalogStateStore bound to the existing Core scope;
18. perform real physical reconciliation before publication;
19. rebuild derived search/Smart state;
20. reproduce the same query, View and Smart Collection results while preserving
    current identity candidates, SourceReference ids and E-05 records.

## 8. Integrated negative evidence families

Accepted child regressions cover the required first-slice negative families:

- root/path traversal and sibling escape;
- symlink/reparse escape at real content access boundaries where platform
  support permits testing;
- unknown/expired/wrong-access/tampered handles;
- output overwrite and byte-budget violations;
- malformed/out-of-scope Alfred records;
- observation sequence gaps/out-of-order/missing sequence evidence;
- plugin crash, hang, malformed frame and excessive notification/output behavior;
- ambient credential inheritance at the official plugin boundary;
- malformed/unsafe EPUB package members;
- extraction rights unknown/review/restricted denial;
- source change after discovery and during extraction;
- catalog change during plugin/extraction execution;
- stale search index;
- unsupported/malformed QueryPlan/View/Smart rules;
- corrupt/noncanonical/unsupported backup;
- restore into non-empty target;
- restore scope mismatch;
- changed/missing/extra physical source on restore.

## 9. Explicitly not implemented by VS1

VS1 acceptance does **not** promote or imply:

- PDF/Docling extraction;
- OCR/scanned-document support;
- remote Providers or remote source/extraction routes;
- secret delivery to Providers;
- natural-language search;
- LLM query interpretation;
- embeddings/vector/semantic-similarity search;
- automatic filesystem organization, move or delete;
- translation/layout reconstruction;
- multi-output recipe/DAG orchestration;
- production plugin marketplace/install/update/PKI;
- hostile third-party plugin sandboxing;
- Durex integration;
- a generic cross-project Module Runtime;
- a stable public Catalog/Search API;
- complete Work/Manifestation ontology;
- source/document-byte backup.

## 10. Next-increment candidates

VS1 does not automatically select the next roadmap item. The strongest candidate
from the already accepted evidence is the **second source-class increment:
PDF/Docling**, because VS1 deliberately chose EPUB first and #187 explicitly kept
PDF/Docling as the next source-class candidate.

A separate promotion decision should compare at least:

1. **PDF/Docling source-class increment** — extend the proven Core/Source/
   Extractor/E-05/search path to PDF while retaining provider-native evidence,
   page/geometric coordinates, dependency/resource budgets and local-only rights
   policy;
2. **product/library UI increment** — expose the already-working VS1 catalog,
   search, Views, Smart Collections, freshness and provenance in an interactive
   library UI without changing underlying authority semantics;
3. **metadata/ontology enrichment** — title/author/edition/tag facts only where
   evidence is actually available, instead of inventing fields in search;
4. **operational hardening** — persistence/database scaling, authentication,
   plugin sandboxing/supervision and lifecycle management before broader plugin
   ecosystems.

Natural-language/vector search should remain layered *after* deterministic
structured search, not replace the current truth/freshness boundary.

## 11. Exit disposition

**Candidate disposition: ACCEPT VS1.**

Reason: all promoted implementation children are completed; the integrated E2E
acceptance scenario exercises the full promoted path; required negative families
are covered across accepted regressions; current scope limitations remain
explicit; no deferred feature has been silently promoted.
