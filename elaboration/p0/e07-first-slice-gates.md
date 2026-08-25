# E-07 — First-slice planning gates G-01..G-07

> Maturity: **Elaboration evidence — final synthesis candidate**  
> Parent: [#106](https://github.com/kinderp/raiatea/issues/106)  
> E-07 issue: [#178](https://github.com/kinderp/raiatea/issues/178)  
> Synthesis date: **25 August 2026**

## 1. Executive decision

E-07 is complete as an **evidence synthesis**, but Raiatea is **not yet authorized
to start vertical slice 1**.

Six planning gates have sufficient bounded evidence for a separate promotion
review. One remains explicitly blocking:

```text
G-01  satisfied
G-02  BLOCKED — maintainer redistribution-rights decision #131
G-03  satisfied-with-bounded-scope
G-04  satisfied-with-bounded-scope
G-05  satisfied-with-bounded-scope
G-06  satisfied-with-bounded-scope
G-07  satisfied-with-bounded-scope
```

The block is not an implementation defect. The repository intentionally cannot
choose a license on behalf of the maintainer. Until #131 is resolved, project-
created benchmark fixture/gold material remains `redistribution:
not-established` / `requires-review` and may not be promoted to a public
rights-safe baseline.

Therefore the next action after E-07 acceptance is **not** product code. It is:

1. resolve #131 through an explicit maintainer decision and evidence update;
2. re-evaluate G-02;
3. open a separate first-slice promotion issue with the exact scope/exit
   criteria;
4. begin vertical slice implementation only if that promotion is accepted.

This preserves the sequencing required by #106.

## 2. Canonical evidence chain

### 2.1 Inception and Elaboration inputs

| Evidence | Issue / PR | Canonical commit | Contribution |
| --- | --- | --- | --- |
| System Context + Product Map | #111 / #112 | `e3b1e40` | ownership, reuse and product/system boundary |
| Use Cases | #113 / #114 | `ed202f2` | P0 consumers and failure paths |
| Risk List + gate definitions | #115 / #116 | `a3ee9f5` | G-01..G-07 and priority risks |
| Glossary | #117 / #118 | `839fa22` | Source/Location/Provenance/Lineage vocabulary |
| Inception Review | #121 / #122 | `6922558` | Elaboration GO only; first slice remains hypothesis |
| E-01 source/rights/threat boundary | #123 / #124 | `c1be73d` | Processing Rights, Redistribution Rights and authority separation |
| E-02 build/buy/reuse survey | #125 / #126 | `18a4b5d` | thin Raiatea layer over replaceable mature Providers |
| E-03 fixture/gold design | #127 / #128 | `1ee0f74` | Provider-neutral B-01/B-02 design; planned material not falsely licensed |
| E-04 measured benchmark workstream | #129; final B-01 #158 | `c8a6d237` final B-01 evidence | measured per-dimension PDF/EPUB evidence; no universal score |
| E-05 conceptual synthesis | #159 / #161 | `e8901a1` | evidence-derived Provider-neutral semantics |
| E-05 machine-readable contract | #159 / #163 | `47dfe5f` | ProcessingRun/Outcome, SourceCoordinate, provenance and failure-state conformance |
| Plugin API v1 design/proofs | #147; final #174/#175 | `7ec5c93` | Source/Extractor/Transformer proof family over accepted runtime/transport semantics |
| E-06 Alfred reconciliation | #176 / #177 | `fae24ad` | Observation boundary, stale/offline/recovery and JSONL delivery semantics |
| E-07a G-03 proof | #179 / #180 | `7ef423e` | conservative identity/reconciliation fixtures |
| E-07b G-06 proof | #181 / #182 | `e856135` | deterministic search/View/Smart Collection integrity |
| E-07c G-07 proof | #183 / #184 | `1ac4f41` | deterministic catalog export/restore + local authority proof |
| Redistribution-rights decision | #131 | **open** | blocking maintainer decision for G-02 |

Short commit prefixes above identify the accepted merge commits; PRs contain the
frozen-head CI/review evidence.

## 3. Gate table

| Gate | Final E-07 status | Evidence | Residual / required containment |
| --- | --- | --- | --- |
| **G-01 Scope containment** | **satisfied** | Inception boundaries #111-#122; E-05 explicitly does not select a Provider/first slice; Plugin API #147/#175 defers production discovery/marketplace/remote/generic-runtime surfaces; E-06 narrows filesystem proof to Linux/inotify | Promotion issue must repeat exclusions; target scope is not “all source classes” |
| **G-02 Rights-safe data boundary** | **BLOCKED** | E-01 #123/#124 separates Processing vs Redistribution Rights and rights evidence vs Core decision; E-03 #127/#128 preserves `not-established` for planned project-created fixtures | #131 must record explicit maintainer terms + visible metadata and update eligible rights-manifest entries. No remote/private Provider authorization is implied |
| **G-03 Conservative identity/reconciliation** | **satisfied-with-bounded-scope** | E-06 #177 + executable #180 (`7ef423e`), workflow `32806328859`, Linux/Windows × Python 3.10/3.12 | Proof model is not production Catalog schema; ambiguous copy/cross-filesystem relations remain reviewable; no destructive auto-merge |
| **G-04 P0 benchmark contract** | **satisfied-with-bounded-scope** | E-03 #128; completed E-04 #129 with final B-01 #158; E-05a #161 consumes measured B-01/B-02 evidence | Applies to measured B-01 born-digital PDF and measured B-02 EPUB evidence; B-03+ remain later; quality/cost/latency/manual repair/degradation stay separate; no universal score |
| **G-05 Minimum provenance/processing state** | **satisfied-with-bounded-scope** | E-05 #159/#163 (`47dfe5f`) + Plugin API source/extractor/transformer proof chain through #175 (`7ec5c93`) | Candidate internal contracts, not public API/DB schema; Core retains rights authority; production handle/storage broker remains first-slice work |
| **G-06 Deterministic search/view integrity** | **satisfied-with-bounded-scope** | executable #182 (`e856135`), workflow `32806514284`, Linux/Windows × Python 3.10/3.12 | Proof does not choose a search engine; NL/LLM interpretation remains outside first slice unless later compiled into inspectable deterministic criteria |
| **G-07 Catalog durability/local security** | **satisfied-with-bounded-scope** | executable #184 (`1ac4f41`), workflow `32806914852`, Linux/Windows × Python 3.10/3.12; E-06 authority boundary | Export/restore and Core-vs-request authority semantics proven; lexical containment is not a production symlink/reparse-point sandbox. Product content access must use OS-aware Core-issued handles/safe-open semantics |

## 4. G-01 — Scope containment

The first implementation must remain an experiment around a narrow local source
path and the accepted P0 contracts. The following do **not** become in scope merely
because E-07 is accepted:

- all source classes at once;
- macOS/Windows filesystem watcher implementation;
- remote Provider authorization;
- private/licensed corpus publication;
- natural-language search, embeddings or vector search;
- automatic filesystem organization or mutation;
- translation/layout reconstruction/multi-output workflow DAG;
- production plugin marketplace/install/update/PKI;
- distributed/remote plugin runtime;
- generic Alfred/Raiatea/FARO runtime extraction;
- Durex coupling;
- Work/Manifestation ontology expansion;
- knowledge graph/forecasting/federation.

**Gate result:** satisfied. The scope exclusions are now concrete enough to be
copied verbatim into a later promotion issue.

## 5. G-02 — Rights-safe data boundary

E-01 and E-03 establish the correct semantics:

```text
Processing Rights      != Redistribution Rights
rights evidence        != Core RightsDecision
project-created        != automatically redistributable
GitHub-public          != licensed for reuse
unknown/review-needed  -> fail closed
```

What is missing is not another schema or test. #131 requires the maintainer to
select the applicable redistribution terms for project-created fixture content,
generator code as applicable, and gold/reference annotations, including visible
license/NOTICE metadata.

### G-02 promotion consequence

While #131 remains open:

- the public benchmark baseline cannot be called rights-safe for redistribution;
- E-07 may be accepted as a synthesis **with G-02 blocked**;
- the first slice may not be promoted under the current #106 rule;
- implementation must not silently choose a license or relabel the material.

**Gate result: BLOCKED.**

## 6. G-03 — Conservative identity/reconciliation

E-06 established the Alfred/Raiatea ownership rule; #180 makes it executable.
The proof demonstrates:

- path is mutable Location evidence, not Logical Identity;
- equal bytes at distinct paths are exact-duplicate evidence but distinct Stored
  Instance candidates;
- rename/move retain Location history and a conservative identity candidate;
- same path + changed bytes triggers content/version reconciliation;
- copy remains a distinct Stored Instance candidate;
- cross-filesystem/copy+delete ambiguity stays unresolved without stronger
  evidence;
- lost/offline scope becomes unavailable/unknown rather than deletion;
- delete is a Location-level fact and does not purge logical/history state;
- outcomes carry an inspectable evidence basis and no destructive merge path.

Workflow `32806328859` passed Ubuntu/Windows on Python 3.10/3.12; #180 has two
clean review rounds on frozen head `eaae637`.

**Gate result:** satisfied-with-bounded-scope.

## 7. G-04 — P0 benchmark contract

The accepted evidence path now covers the bounded source classes for which
measurement exists:

- B-01 born-digital PDF across clean text/order, structure/links,
  figures/captions/assets, tables, formulas, defective native text/OCR fallback
  and malformed/access-controlled negatives;
- B-02 EPUB through direct package and measured conversion-route evidence,
  including logical/package coordinates and negative/security cases.

E-05 derives contract requirements from those measurements rather than selecting
a Provider brand or embedding a universal quality number.

Still deliberately separate are:

- text fidelity;
- structure/relations;
- Source Coordinate quality;
- degradation/partiality;
- cost/latency/resource use;
- manual repair burden;
- route/provider/model/version identity.

B-03 scanned-heavy, B-04 scholarly-heavy and other later classes remain outside
the first bounded evidence claim.

**Gate result:** satisfied-with-bounded-scope.

## 8. G-05 — Minimum provenance/processing state

E-05 and Plugin API v1 jointly prove the required separation:

```text
Source Reference
  -> Processing Run / Provider+route evidence
  -> Raw Extraction / Provider Evidence
  -> Normalized Representation
  -> Derived Artifact / Transformation lineage
```

The model preserves independently:

- Provider/engine/version and route/profile;
- source fingerprint/reference;
- ProcessingOutcome beyond a boolean success;
- measured/partial/not-measured/degraded/ambiguous evidence;
- warnings/diagnostics;
- PDF vs EPUB Source Coordinate families;
- OCR/fallback stage lineage;
- rights-decision reference without plugin rights authority;
- source/input/output refs and transformation lineage.

Plugin API #175 additionally proved deterministic transformation lineage and
closed record shapes while retaining opaque handle ids and rejecting lease/path/
rights authority leakage.

**Gate result:** satisfied-with-bounded-scope.

## 9. G-06 — Deterministic search/View integrity

#182 proves a minimal deterministic truth path before natural-language search:

- normalized inspectable structured criteria;
- explicit metadata/tag/extracted-text filters;
- unknown field/operator/sort fails closed;
- deterministic ordering with explicit `item_id` tie-breaker;
- catalog/index revision mismatch returns stale/blocked results, never false
  freshness;
- View is query + projection, not filesystem organization;
- Smart Collection rule is stored separately from current members and evaluated
  revision;
- recomputation after catalog revision deterministically changes membership;
- no LLM, embeddings or vector database is required.

Workflow `32806514284` passed Ubuntu/Windows on Python 3.10/3.12 with two clean
reviews on frozen head `e2a2d78`.

**Gate result:** satisfied-with-bounded-scope.

## 10. G-07 — Catalog durability/local security

#184 proves two independent bounded properties.

### 10.1 Catalog durability

- canonical versioned export;
- SHA-256 integrity over canonical payload;
- logical identity, Location, provenance, View and Smart Collection rule state;
- deterministic record and normalized-plan criterion ordering;
- round-trip reconstruction;
- corruption, unsupported version, missing/unknown critical state,
  referential invalidity and noncanonical payload fail closed;
- derived Smart Collection members/search index are recomputable, not backup
  authority.

### 10.2 Authority

- Core owns scope root creation;
- external request contains existing `scope_id + path + capability`, not a root
  override;
- component-aware containment rejects sibling-prefix escape;
- `..` and outside-root requests fail closed;
- proof capabilities are only `observe` and `read-for-processing`;
- write/move/delete/organize are rejected;
- authority records do not carry secrets or document bytes;
- authorization is a pure decision and exposes no mutation operation.

### 10.3 Residual security requirement

POSIX lexical containment is intentionally **not** claimed as proof against a
real symlink/reparse-point escape. Before the product slice reads content, the
Core must provide OS-aware safe-open/Core-issued handle semantics bound to the
authorized root. That is implementation work inside the promoted slice, not a
reason to pretend the proof is stronger than it is.

Workflow `32806914852` passed Ubuntu/Windows on Python 3.10/3.12 with two clean
reviews on frozen head `109da73`.

**Gate result:** satisfied-with-bounded-scope.

## 11. Candidate promotion envelope after G-02 is unblocked

E-07 does **not** choose the final first-slice source class or Provider. It does
constrain any acceptable promotion decision to a small envelope.

A lowest-risk implementation should compose only accepted/reviewed boundaries:

```text
Core-owned local scope registration
        |
        +--> Alfred Event Model v0 / structured JSONL
        |       -> AlfredObservationAdapter
        |       -> freshness/reconcile-required state
        |
        +--> bounded inventory/reconciliation
        |       -> conservative Logical Identity + Location evidence
        |
        +--> Core RightsDecision
        |
        +--> accepted Plugin API runtime/transport
        |       -> one explicitly selected local Source/Extractor route
        |
        +--> E-05 ProcessingRun / Outcome / Normalized Representation
        |       -> provenance + Source Coordinates + warnings/degradation
        |
        +--> bounded catalog
        |       -> deterministic structured search / View / Smart Collection
        |
        +--> deterministic catalog export/restore proof path
```

The promotion issue must select **one measured B-01/B-02 profile/route or an even
narrower proof case**, state why it gives the best value/risk reduction, and pin
its exact Provider/route/version evidence. E-07 deliberately does not make that
roadmap decision implicitly.

### Mandatory vertical-slice acceptance properties

If promoted, the first implementation must at minimum demonstrate end-to-end:

1. explicit Core-owned authorized local scope;
2. no root widening from UI/API request data;
3. Alfred observation or bounded inventory produces replay/idempotent Observation
   evidence;
4. stale/overflow/gap state forces reconciliation rather than false freshness;
5. rename/offline/delete semantics obey G-03;
6. Core RightsDecision gates acquisition/processing;
7. plugin invocation uses accepted v1 manifest/runtime/transport semantics;
8. E-05 outcome/provenance/failure semantics survive adapter execution;
9. content access uses OS-aware Core-issued handles that prevent root escape;
10. deterministic query/view result has visible freshness;
11. catalog state can be exported/restored with integrity;
12. no remote Provider, filesystem mutation, NL search or deferred feature is
    required for the proof to pass.

## 12. Deferred features after any first-slice promotion

Promotion of one slice would **not** promote:

- additional source families automatically;
- all PDF/EPUB profiles;
- macOS/Windows Alfred backends;
- remote/hosted Providers;
- secret delivery;
- automatic organization/move/delete;
- natural-language query interpretation;
- embeddings/vector search;
- translation or layout reconstruction;
- multi-output Processing Recipes/DAG orchestration;
- production plugin discovery/install/update/marketplace/PKI;
- distributed plugins;
- cross-project generic runtime;
- Durex integration;
- Work/Manifestation ontology expansion;
- public benchmark redistribution beyond the explicit #131 decision.

## 13. Finding log

| ID | Severity | Status | Finding | Resolution / consequence |
| --- | --- | --- | --- | --- |
| E07-F1 | high | resolved | G-03 had architecture semantics but no deterministic fixture proof. | #180 adds exact duplicate/rename/move/copy/ambiguous/offline/delete evidence. |
| E07-F2 | high | resolved | G-06 had canonical intent but no executable deterministic query/freshness/View/Smart Collection evidence. | #182 supplies a dependency-light cross-platform proof. |
| E07-F3 | high | resolved with residual | G-07 had authority concepts but no deterministic backup/export or executable scope proof. | #184 proves the bounded semantics and records OS symlink/reparse handling as first-slice implementation residual. |
| E07-F4 | **blocking** | **open** | Repository has no explicit maintainer redistribution terms for project-created benchmark fixtures/gold. | #131 remains the only blocking planning gate; E-07 must not invent the license. |
| E07-F5 | medium | contained | Mature proof contracts could tempt implementation to expand scope (remote Providers, NL search, marketplace, generic runtime). | Promotion envelope and deferred list are explicit; separate roadmap decision remains mandatory. |

## 14. Final E-07 disposition

E-07 can be accepted and closed when this synthesis survives review because its
Definition of Done explicitly permits G-02 to remain visibly blocking.

Acceptance of E-07 means:

- the technical evidence gaps found at E-07 opening are closed;
- the remaining policy/maintainer blocker is explicit and isolated;
- the first-slice implementation envelope is constrained by evidence;
- **no first slice has yet been promoted**.

The next repository state should therefore be:

```text
E-07 = completed
G-02 = blocked by #131
first-slice promotion = not opened/accepted yet
vertical slice 1 = not started
```

Only after #131 is explicitly resolved should the maintainer make the separate
promotion decision required by #106.
