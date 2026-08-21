# Raiatea Inception Review

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.2.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#98](https://github.com/kinderp/raiatea/issues/98)
>
> Child issue: [#121](https://github.com/kinderp/raiatea/issues/121)
>
> Review PR: [#122](https://github.com/kinderp/raiatea/pull/122)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Repository observation baseline: `main` at
> [`839fa22`](https://github.com/kinderp/raiatea/commit/839fa229614dc3590957488380d76c150e33a948),
> observed 21 August 2026
>
> Independent supervised pilot: [#93](https://github.com/kinderp/raiatea/issues/93)
> and [PR #95](https://github.com/kinderp/raiatea/pull/95)
>
> Primary canonical sources:
> [`00-why-raiatea.md`](00-why-raiatea.md),
> [`01-manifesto.md`](01-manifesto.md),
> [`02-vision.md`](02-vision.md),
> [`03-system-context.md`](03-system-context.md),
> [`04-product-map.md`](04-product-map.md),
> [`05-use-case-model.md`](05-use-case-model.md),
> [`06-risk-list.md`](06-risk-list.md),
> [`06-risk-register.md`](06-risk-register.md),
> [`07-glossary.md`](07-glossary.md), and
> [`07-terminology-compatibility.md`](07-terminology-compatibility.md)

## 1. Purpose

This document is the final gate of Project Genesis, Raiatea's Inception phase.
It does not ask whether the complete Raiatea vision is ready to be built. It
asks a narrower risk-driven question:

> **Are purpose, boundaries, significant use cases, risks and vocabulary stable
> enough to enter Elaboration and begin evidence-driven reduction of the most
> important P0 risks without pretending that the first product slice, providers,
> schema or pedagogical thesis have already been validated?**

The review must preserve four distinctions:

1. **phase readiness is not product validation**;
2. **P0 risk-reduction work is not first-slice implementation approval**;
3. **an accepted product direction is not a current software contract**;
4. **open risks are not mitigated merely because their treatment is understood**.

## 2. Review decision

> Assertion status: `accepted-decision` only after maintainer acceptance and
> merge; proposed decision while this document is Draft

### Proposed decision: GO to Elaboration for bounded P0 risk reduction

Raiatea should leave Project Genesis/Inception and enter **Elaboration focused
on P0 risk reduction and architecture**.

This GO authorizes work that produces evidence needed to decide *how* P0 should
be built and whether the candidate first document slice should later become
`planned` implementation work.

It does **not** authorize:

- implementation of the candidate first slice merely because Inception closes;
- automatic filesystem organization;
- natural-language search as a required first-slice feature;
- translation or layout reconstruction;
- multi-output DAG execution/caching;
- Durex integration;
- physical-holding/edition linking in the first slice;
- TheBitLab projection implementation;
- P1-P7 implementation;
- claims that the Research & Learning Workspace improves learning outcomes;
- selection of Docling, an OCR engine, VLM, translation provider, renderer,
  database, vector store or graph store without the required evidence.

### Meaning of the GO

The GO means only that the project now has enough reviewed structure to reduce
its highest risks deliberately instead of continuing broad conceptual
exploration.

The immediate Elaboration question becomes:

> **What evidence and contracts are required for a trustworthy, portable and
> economically viable Source Ingestion & Extraction foundation, and what does
> that evidence imply about the first verifiable Document & Asset Library
> slice?**

## 3. Inception completeness review

> Assertion status: `current-contract` for repository/document state observed at
> the pinned `main` baseline above; conclusions are `provisional-decision` until
> this review is accepted

### 3.1 Canonical artifact status

| Artifact | State at repository baseline / review branch | Review conclusion |
| --- | --- | --- |
| `00-why-raiatea.md` | Accepted on `main` | Purpose, first person, product hypotheses, P0 priority and kill criteria are explicit |
| `01-manifesto.md` | Accepted on `main` | Durable human/product principles constrain later implementation without fixing technologies |
| `02-vision.md` | Accepted on `main` | Long-term direction, P0-P7 inclusion, product hierarchy and current-vs-future state are separated |
| `03-system-context.md` | Accepted on `main` | Raiatea/Alfred/Durex/TheBitLab and external provider boundaries are explicit |
| `04-product-map.md` | Accepted on `main` | Document Library, Research/Learning surfaces and shared capabilities are separated |
| `05-use-case-model.md` | Accepted on `main` | Significant goals, actors, failures and cross-cutting invariants are documented |
| `06-risk-list.md` + register | Accepted on `main` | 23 risks, first-slice gates, feature gates and kill/narrowing criteria are explicit |
| `07-glossary.md` + compatibility map | Accepted on `main` | Minimum ubiquitous language is stable enough for Elaboration without becoming an implicit schema |
| `08-inception-review.md` | Absent on baseline `main`; Draft in PR #122 | This final gate is under review |

The eight accepted artifacts from `00-why-raiatea.md` through
`07-glossary.md` establish enough common context for risk-driven Elaboration.
They do not establish implementation completeness.

### 3.2 Questions now answered well enough

The canonical set provides reviewed answers to these Inception questions:

- Why should Raiatea exist and what would invalidate that reason?
- Who is the first person and what is the initial validation domain?
- Which principles must survive provider, model and architecture changes?
- What exists today versus what is only accepted, planned or hypothetical?
- Why is P0 Source Ingestion & Extraction the first platform foundation?
- Where are the boundaries among the Document & Asset Library, P0,
  Research/Learning surfaces and external consumers?
- Which responsibility belongs to Alfred, which may later reuse Durex, and which
  remains Raiatea-owned?
- What must a user eventually be able to do with inventory, search, views,
  organization and Processing Recipes?
- Which failure modes can invalidate or narrow the first proof?
- Which terms have stable conceptual meaning and which remain deferred?

### 3.3 Questions intentionally not answered in Inception

The following remain deliberately open and are not defects in the Inception
package:

- final domain/storage schema;
- identifier algorithms and persistence technology;
- exact P0 provider/engine choices;
- extraction bundle/API representation;
- quantitative benchmark thresholds;
- first-slice promotion to `planned`;
- cross-platform Alfred implementation strategy;
- Durex Job/Run reuse decision;
- automatic organization design;
- translation/layout provider and quality strategy;
- formal bibliographic Work/Expression/Manifestation/Item model;
- P1-P7 ordering and implementation architecture;
- validated pedagogical benefit.

Those questions now have owners, evidence gates or explicit deferral conditions,
which is the appropriate Inception outcome.

## 4. Current implementation and evidence boundary

> Assertion status: `current-contract` for repository state observed at the
> pinned baseline and pilot references above

Raiatea is **not** yet the Universal Document & Asset Library described by the
Product Map and is **not** yet a general Source Ingestion & Extraction Hub.

The repository already contains a narrower local pedagogical vertical and pilot
infrastructure. That implementation demonstrates feasibility of selected
learning-module mechanics but does not prove the long-term product thesis.

The independent supervised pilot remains open:

- parent issue [#93](https://github.com/kinderp/raiatea/issues/93) is open;
- [PR #95](https://github.com/kinderp/raiatea/pull/95), the incident-log/stop-
  criteria increment, remains open and unmerged at the observation date.

Therefore this Inception Review must **not** claim that Raiatea improves
learning, transfer, retention or study efficiency.

### Consequence

The pedagogical evidence stream and P0 Elaboration may continue independently:

```text
P0 Elaboration
  -> reduce source/identity/provenance/search/rights risks

Pedagogical pilot
  -> test learning/product hypotheses under its own roadmap
```

Progress on one stream does not manufacture evidence for the other.

## 5. What Elaboration is authorized to do

> Assertion status: `provisional-decision` until this review is accepted

The following work is appropriate immediately after the Inception gate because
it **reduces uncertainty** without assuming the desired technical result.

### E-01 — Source taxonomy, rights and threat boundary

Authorized outcome:

- define source classes relevant to P0;
- distinguish Processing Authority, Processing Rights and Redistribution Rights;
- define local versus remote Provider data boundaries;
- identify private-corpus and retention assumptions;
- produce a bounded threat/data-flow model sufficient for benchmark and contract
  work.

Primary gates/risks:

- G-02;
- R-09;
- R-22;
- supporting input for R-05/R-07/R-19.

This work may use specialist legal/security review where needed; the project
must not turn architectural wording into legal advice.

### E-02 — Current technology survey and build/buy/reuse matrix

Authorized outcome:

- survey current parsers, OCR engines, multimodal/VLM approaches and relevant
  conversion/extraction systems;
- include Docling as a candidate suggested by the maintainer, not as a
  preselected winner;
- compare capabilities, supported source classes, provenance/coordinate support,
  deployment/privacy constraints, portability and license/reuse implications;
- audit cross-project reuse before building equivalents.

Primary gates/risks:

- G-04;
- R-05;
- R-06;
- R-19.

A survey may reject or narrow a candidate. It is not a vendor-selection ritual.

### E-03 — Rights-safe benchmark corpus and fixture design

Authorized outcome:

- design representative PDF/EPUB source-class fixtures;
- include structural complexity, malformed/degraded input and known failure
  cases;
- define rights-safe gold/reference data;
- design identity/reconciliation fixtures for exact duplicates, moves/renames,
  ambiguous related material and missing/offline storage;
- define provenance and failure-state fixtures.

Primary gates/risks:

- G-02;
- G-03;
- G-04;
- G-05;
- R-01/R-02/R-04/R-05/R-07/R-09.

### E-04 — Benchmark contract and measurement plan

Authorized outcome:

Define source-class-specific measures for at least:

- text/content fidelity;
- document hierarchy and reading order;
- Source Coordinate stability/accuracy;
- tables/figures/code/formula handling where relevant;
- visible degradation/failure behavior;
- latency;
- compute/storage/cost;
- manual repair/correction burden;
- Provider portability and route replacement.

Quantitative pass/fail thresholds should be declared **after** representative
fixtures and baseline measurements make them defensible, but before a promoted
slice is implemented/tested against those thresholds.

Primary gates/risks:

- G-04;
- R-05;
- R-06;
- R-19;
- R-23.

### E-05 — P0 contract exploration

Authorized outcome:

Explore a provider-neutral contract that preserves the Glossary distinctions:

```text
Source role
  -> Original Artifact or Source Reference
  -> Raw Extraction
  -> Normalized Representation
  -> Source Coordinates
  -> Warning / Degraded Result / failure state
  -> Transformation / Provenance / Lineage
```

The technical representation remains open. The Glossary does not require one
record per term and does not require names to map one-to-one to API resources.

Primary gates/risks:

- G-04;
- G-05;
- R-05;
- R-07;
- R-13;
- R-17;
- R-19.

### E-06 — Alfred integration and reconciliation evidence

Authorized outcome:

- define the stable observation contract Raiatea needs from Alfred;
- verify initial/bounded scan and reconciliation behavior for the chosen test
  environment;
- model observation freshness and missing/offline states;
- demonstrate that Raiatea does not infer mutation authority from an Alfred
  observation;
- identify cross-platform gaps without creating a second hidden watcher/event
  model.

Primary gates/risks:

- G-03;
- R-01;
- R-02;
- R-04.

### E-07 — Evidence packages for G-01 through G-07

Authorized outcome:

For each first-slice planning gate, create explicit evidence or a scoped plan to
produce it. Elaboration should make the eventual first-slice promotion decision
mechanical enough to audit rather than a matter of enthusiasm.

## 6. What remains unauthorized after the GO

> Assertion status: `accepted-decision` for existing feature/evidence gates;
> review restates them without changing their status

### 6.1 Candidate first slice

The current candidate remains a **`working-hypothesis`**, not a planned
implementation:

```text
PDF + EPUB
  + bounded inventory
  + stable Logical Identity independent of Location
  + P0 extraction
  + deterministic search
  + logical views
  + one Smart Collection
  + one single-output Processing Recipe
  + Lineage for one traced Derived Artifact
```

Closing Inception does **not** promote this slice.

A separate roadmap decision may promote it only when G-01 through G-07 have
sufficient evidence and no unresolved Critical contradiction blocks the scope.

### 6.2 Automatic managed organization

Still feature-blocked. It requires explicit authority, preview/dry-run, path and
collision safety, idempotency, journaling, reconciliation and recovery/failure-
injection evidence.

### 6.3 Natural-language query interpretation

Still excluded from the first proof. Deterministic query/filter semantics,
index freshness and an inspectable query model must exist first.

### 6.4 Translation and visual reconstruction

Still feature-blocked. Translation quality, terminology/structure preservation,
Provider privacy/provenance, visual degradation, font/asset rights and repair
cost require dedicated evidence.

### 6.5 Multi-output DAG and intermediate caching

Still feature-blocked. Intermediate validity/invalidation, partial failure,
retry/recovery and complete Lineage must be demonstrated before this becomes
planned product behavior.

### 6.6 Durex integration

Still candidate reuse. A dedicated Job/Run reuse audit is required before
Raiatea couples document processing to Durex.

### 6.7 Physical holding / edition linking

Still outside the candidate first slice. Work/Expression/Manifestation/Item
remain deferred; edition/translation/scan ambiguity requires reversible
relationship evidence before broad linking becomes planned.

### 6.8 TheBitLab projection

Still deferred/feature-blocked until rights propagation, projection versioning,
source unavailability and ownership semantics are explicit.

### 6.9 P1-P7

They remain accepted destination capability groups. Their order and detailed
architecture remain provisional and no P1-P7 implementation is authorized by
this review.

## 7. First-slice planning gates carried into Elaboration

> Assertion status: `accepted-decision`, inherited from the Risk List

### G-01 — Scope containment

Required evidence:

- the first proof stays bounded to PDF/EPUB, inventory/identity, P0 extraction,
  deterministic search, views, one Smart Collection, one single-output recipe
  and lineage;
- excluded capabilities do not re-enter implicitly.

Blocks on R-16.

### G-02 — Rights-safe data boundary

Required evidence:

- explicit processing rights for benchmark/first-slice corpus;
- declared local versus remote Provider flow;
- Redistribution Rights are not inferred from Processing Rights.

Blocks on R-09 and R-22.

### G-03 — Conservative identity and reconciliation

Required evidence:

- exact-duplicate, rename/move and ambiguous-related fixtures;
- no irreversible automatic merge/deletion;
- missing/offline distinct from proven deletion where evidence permits;
- bounded inventory/reconciliation route without a competing watcher.

Blocks on R-01, R-02 and R-04.

### G-04 — P0 benchmark contract

Required evidence:

- source-class metrics and fixtures for PDF/EPUB;
- separate quality, latency/cost/manual-repair and degradation measures;
- Provider/routing selection based on benchmark evidence;
- insufficient quality narrows source-class support instead of being hidden.

Blocks on R-05, R-06 and R-19.

### G-05 — Minimum provenance and processing state

Required evidence:

- Derived Artifact traceable to Source/representation and operations;
- relevant Provider/engine version and Warnings recorded;
- success/failure/unknown/partial states distinct;
- retry/recovery cannot silently duplicate a known successful output.

Blocks on R-07 and R-13 and contains the first-slice part of R-08.

### G-06 — Deterministic search/view integrity

Required evidence:

- inspectable deterministic filter semantics;
- observable inventory-to-index freshness/reconciliation;
- Smart Collection rule stored separately from current membership;
- no dependency on natural-language interpretation.

Blocks on R-10 and defers R-11.

### G-07 — Catalog durability and local security boundary

Required evidence:

- minimum backup/export for irreplaceable catalog/provenance/corrections;
- local web/backend authority assumptions documented before valuable corpus
  access;
- UI cannot grant filesystem scope not authorized by backend policy.

Blocks on R-18 and R-22.

## 8. Critical risks at phase transition

> Assertion status: `current-contract` for risk state inherited from the
> accepted Risk List

Open Critical risks are expected at the start of Elaboration. The phase exists
to reduce them. They must remain visible.

| Risk | Transition treatment |
| --- | --- |
| R-01 false identity/destructive merge | Elaboration blocker for slice promotion; G-03 evidence required |
| R-03 destructive organization | Feature stays excluded; does not block narrower P0 work |
| R-05 structurally wrong extraction | Core P0 Elaboration risk; G-04 benchmark evidence required |
| R-07 insufficient provenance | Core P0 contract/experiment risk; G-05 required |
| R-09 rights/privacy violation | G-02 required before real private corpus/provider flow |
| R-15 lower value than simpler alternative | Slice-exit/kill risk; later experiment must compare a declared baseline |
| R-16 scope grows faster than value | G-01 keeps Elaboration bounded |
| R-18 catalog corruption/unrecoverable state | G-07 required before valuable corpus dependence |
| R-22 unsafe local web/filesystem authority | G-02/G-07 required before valuable corpus/UI authority |

No Critical risk is declared mitigated by this review.

## 9. Phase-exit semantics for Elaboration

> Assertion status: `working-hypothesis` to be refined in the Elaboration roadmap

Elaboration should not end merely because design documents or benchmarks exist.
A future phase review should require at least:

- evidence-backed first-slice scope decision;
- G-01 through G-07 status documented;
- P0 Provider/routing choices justified by benchmark evidence or explicitly
  deferred;
- provider-neutral P0 contract stable enough for the chosen experiment;
- identity/reconciliation and catalog durability/security plans sufficient for
  the bounded environment;
- measurable experiment/exit thresholds declared before claiming slice success;
- open Critical risks either contained for the experiment, feature-deferred, or
  strong enough to invalidate/narrow the direction.

The exact Elaboration exit artifact and Construction entry gate are future
roadmap work; this review does not invent them prematurely.

## 10. Relationship to the pedagogical thesis

> Assertion status: `accepted-decision` for evidence separation

The accepted Why/Manifesto/Vision preserve a Research & Learning direction, but
that direction requires independent evidence.

The supervised pilot roadmap remains open at the review observation date.
Therefore:

- no learning-outcome claim is promoted;
- no pedagogical feature becomes justified merely because P0 enters
  Elaboration;
- pilot evidence may later narrow, strengthen or invalidate parts of the
  Research & Learning Workspace thesis;
- P0 source/provenance components may retain standalone value even if the larger
  pedagogical thesis is narrowed or rejected.

This separation protects both lines of inquiry from circular evidence.

## 11. Repository and project-state decision

> Assertion status: `provisional-decision` until this review is accepted

If this review is accepted and merged:

1. **Project Genesis / Inception is complete.**
2. The repository phase becomes **Elaboration — P0 risk reduction and
   architecture**.
3. Root and Genesis README files should state explicitly that:
   - Inception is complete;
   - P0 remains planned, not implemented;
   - the candidate first product slice remains a working hypothesis;
   - the active objective is evidence generation for P0 and G-01..G-07;
   - the supervised pedagogical pilot continues independently.
4. Parent issue #98 may close as `completed`.
5. P0 issue #106 becomes the primary platform Elaboration roadmap.

A phase transition is a governance/orientation decision, not a software release.

## 12. Immediate Elaboration sequence

> Assertion status: `provisional-decision`; each item still requires a scoped
> issue/PR before work begins

Recommended sequence:

```text
E1  Source taxonomy + rights/threat boundary
    |
    +--> E2 current technology survey / build-buy-reuse
    |
    +--> E3 rights-safe benchmark fixtures/gold data
            |
            v
        E4 benchmark contract and baseline measurements
            |
            v
        E5 P0 provider-neutral contract exploration
            |
            +--> E6 Alfred reconciliation/integration evidence
            |
            v
        G-01..G-07 evidence package
            |
            v
        separate first-slice promotion decision
```

Some work may overlap when dependencies are explicit. Parallelism must not hide
missing evidence or turn candidate technologies into facts.

## 13. Review outcome matrix

> Assertion status: `provisional-decision` until accepted

| Question | Proposed answer | Why |
| --- | --- | --- |
| Is the complete long-term Raiatea vision ready for implementation? | **No** | P1-P7, broader products and many feature gates remain intentionally unresolved |
| Is Project Genesis/Inception complete enough to stop broad conceptual expansion? | **Yes** | Purpose, principles, boundaries, use cases, risks and vocabulary are canonical |
| May P0 enter Elaboration? | **Yes — bounded GO** | The next uncertainties are empirical/architectural and are explicitly captured by #106 and the Risk List |
| Is P0 implemented? | **No** | No general ingestion/extraction implementation is claimed |
| Is PDF+EPUB first slice now planned? | **No** | G-01..G-07 evidence + separate roadmap promotion are still required |
| Are providers/engines selected? | **No** | Survey and benchmarks come first |
| Is automatic organization authorized? | **No** | Critical feature gate remains open |
| Are translation/layout features authorized? | **No** | Dedicated quality/rights/cost gates remain open |
| Is Durex an accepted dependency? | **No** | Candidate reuse pending audit |
| Is the pedagogical thesis validated? | **No** | Independent pilot remains open |
| Can the document/source foundation still create standalone value? | **Working hypothesis worth testing** | P0 and Document Library have independent user outcomes and explicit kill criteria |

## 14. Open decisions carried forward

The following do not block the proposed Elaboration entry but remain visible:

- first supported operating environment and Alfred fallback/reconciliation
  details;
- exact first benchmark corpus and source-class fixture set;
- provider candidates and benchmark harness design;
- P0 technical contract shape;
- database/search technology;
- first-slice measurable thresholds;
- local-web security design;
- catalog backup/rebuild design;
- Durex reuse audit timing;
- physical/bibliographic model timing;
- final public product naming;
- P1-P7 dependency ordering;
- supervised pedagogical pilot outcome.

Each decision must be resolved by evidence or explicitly deferred; none is
silently answered by the phase transition.

## 15. Inception exit criteria

> Assertion status: `provisional-decision` until accepted

Project Genesis may close when all of the following are true:

- [x] Why/problem/first person documented and accepted;
- [x] Manifesto and Vision accepted;
- [x] System Context and Product Map accepted;
- [x] significant Use Case Model accepted;
- [x] Risk List/Evidence Register accepted;
- [x] Glossary and terminology compatibility accepted;
- [x] P0 remains the first priority with ownership boundaries explicit;
- [x] candidate first slice remains distinguishable from planned work;
- [x] Critical risks and evidence gates remain visible rather than declared
  solved;
- [x] pedagogical pilot state is not confused with P0/platform readiness;
- [ ] this Inception Review is accepted and merged;
- [ ] repository orientation is updated to the resulting phase.

## 16. Final proposed decision record

> Assertion status: `provisional-decision` until maintainer acceptance

**Decision:** `GO — enter Elaboration for bounded P0 risk reduction and
architecture.`

**Authorized:** taxonomy/rights/threat-boundary work, current technology survey,
build/buy/reuse analysis, rights-safe benchmark design, P0 benchmark contract,
provider-neutral contract exploration, Alfred reconciliation evidence and
G-01..G-07 evidence production.

**Not authorized by this decision:** first-slice implementation/promotion,
automatic organization, NL search, translation/layout reconstruction,
multi-output DAG execution, Durex integration, physical-holding linking,
TheBitLab projection, P1-P7 or pedagogical efficacy claims.

**Revisit / stop condition:** if Elaboration evidence shows that trustworthy
identity, rights-safe processing, extraction quality, provenance, deterministic
search or product value cannot meet a viable bounded profile, narrow or stop the
direction according to the accepted Risk List and Why Raiatea kill criteria.
