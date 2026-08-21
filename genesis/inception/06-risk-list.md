# Raiatea Risk List and Evidence Gates

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#98](https://github.com/kinderp/raiatea/issues/98)
>
> Child issue: [#115](https://github.com/kinderp/raiatea/issues/115)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Primary canonical sources: [`00-why-raiatea.md`](00-why-raiatea.md),
> [`01-manifesto.md`](01-manifesto.md), [`02-vision.md`](02-vision.md),
> [`03-system-context.md`](03-system-context.md),
> [`04-product-map.md`](04-product-map.md), and
> [`05-use-case-model.md`](05-use-case-model.md)

## 1. Purpose

This artifact turns the failure paths and uncertainty exposed by Raiatea's
canonical use cases into **decision gates**. It is not a catalogue of everything
that might go wrong and it is not a substitute for implementation threat
models, legal review or source-class benchmarks.

The Risk List answers five practical questions:

1. What could invalidate the product or make a capability unsafe?
2. Which risks must be reduced before the candidate first slice may become
   `planned` implementation work?
3. Which severe risks can be deferred because the first slice deliberately does
   not exercise the capability that creates them?
4. What evidence would narrow, pause, reject or change a direction?
5. Which later artifact owns the next decision without prematurely selecting a
   technology?

## 2. Risk language

> Assertion status: `accepted-decision`

### 2.1 Severity is not probability

Severity describes the plausible consequence **if the failure occurs**. The
current project does not yet have enough measured operational data to assign
credible numerical probabilities to most risks.

This document therefore uses qualitative severity:

- **Critical** — could cause data loss, rights/privacy breach, materially false
  evidence, or invalidate the product/P0 thesis;
- **High** — could make a major workflow unreliable, misleading or uneconomic;
- **Medium** — important but containable without invalidating the first product
  proof;
- **Low/Monitor** — track, but do not spend current Inception effort unless new
  evidence raises it.

Severity labels in this Draft are `working-hypothesis` assessments unless an
accepted principle makes the consequence intrinsically blocking.

### 2.2 Treatment class

Treatment class answers **when the risk must be addressed**:

- **Slice-blocking** — evidence is required before the candidate first slice may
  be promoted from `working-hypothesis` to `planned`;
- **Slice-exit** — implementation may begin under bounded controls, but the
  first slice cannot be declared successful without measured evidence;
- **Feature-blocking** — the first slice can proceed because that feature is
  excluded, but the feature may not be enabled/planned before its gate is met;
- **Deferred** — belongs to a later product/integration and must not enlarge the
  first slice;
- **Monitor** — record and revisit when its trigger appears.

A Critical risk can therefore be `Feature-blocking` rather than
`Slice-blocking` when the risky feature is deliberately absent from the first
proof.

### 2.3 Risk state

Risks may later be marked:

- `open` — insufficient evidence;
- `contained` — bounded enough for the relevant experiment, residual risk
  remains;
- `mitigated` — evidence shows the planned control materially reduces it;
- `accepted-residual` — remaining risk is consciously accepted for a stated
  scope;
- `transferred` — responsibility moves to a provider/consumer but remains
  visible;
- `invalidated-direction` — evidence requires narrowing, replacing or stopping
  the direction.

This Draft begins with risks `open` unless stated otherwise.

## 3. Current risk priorities

> Assertion status: `working-hypothesis` for priority ordering

| ID | Risk | Severity | Treatment class | First-slice relation | Primary use cases |
| --- | --- | --- | --- | --- | --- |
| R-01 | False logical identity / destructive merge | Critical | Slice-blocking | Must be contained | UC-01, UC-03, UC-16 |
| R-02 | Missing/offline location misclassified as delete or move | High | Slice-blocking | Must be contained | UC-03, UC-04 |
| R-03 | Destructive or irrecoverable automatic filesystem organization | Critical | Feature-blocking | Explicitly excluded | UC-09, UC-10, UC-18 |
| R-04 | Filesystem observation gaps and cross-platform mismatch | High | Slice-blocking with bounded fallback | Must have verifiable inventory/reconciliation path | UC-01, UC-03, UC-04 |
| R-05 | Extraction looks usable while structure/evidence is wrong | Critical | Slice-blocking | Benchmark gate | UC-11, UC-05, UC-13, UC-15 |
| R-06 | P0 cost/latency/manual-repair makes source class uneconomic | High | Slice-blocking + Slice-exit | Benchmark/value gate | UC-11 |
| R-07 | Provenance is insufficient to reconstruct a derivative's route | Critical | Slice-blocking | Required by traced derivative | UC-11, UC-13, UC-15 |
| R-08 | Stale or invalid intermediate is reused | High | Feature-blocking; minimal subset in slice | Single-output scope reduces exposure | UC-13, UC-18 |
| R-09 | Rights/privacy boundary is violated | Critical | Slice-blocking | Rights-safe corpus/provider boundary required | UC-01, UC-06, UC-11-17 |
| R-10 | Deterministic search/index results are stale or unexplained | High | Slice-blocking + Slice-exit | Core first-slice value | UC-05, UC-07, UC-08 |
| R-11 | Natural-language query plan silently changes user intent | High | Deferred/Feature-blocking | Excluded | UC-06, UC-08 |
| R-12 | Translation/rendering is fluent or attractive but materially wrong | High/Critical by content | Deferred/Feature-blocking | Excluded | UC-12, UC-14, UC-15 |
| R-13 | Processing/recovery leaves unknown or duplicated state | High | Slice-blocking for minimal processing; Feature-blocking for destructive jobs | Minimal failure state required | UC-13, UC-18 |
| R-14 | Premature Durex coupling freezes a coding-agent runtime into document processing | Medium/High | Feature-blocking | No Durex dependency required | UC-13, UC-18 |
| R-15 | Product value is lower than simpler transparent alternatives | Critical | Slice-exit / Kill criterion | Must be measured | All first-slice UC |
| R-16 | Scope/architecture grows faster than validated value | Critical | Slice-blocking governance gate | Keep first slice narrow | Cross-cutting |
| R-17 | Vocabulary/schema freezes before evidence and Glossary | Medium | Feature-blocking | Use provisional language | Cross-cutting |
| R-18 | Catalog/source-of-truth corruption or unrecoverable migration | Critical | Slice-blocking | Minimum backup/recovery contract needed before valuable corpus | UC-01, UC-03-05, UC-15 |
| R-19 | Provider/model lock-in defeats portability principle | High | Slice-blocking design constraint; Slice-exit evidence | Replaceable route required | UC-06, UC-11-14 |
| R-20 | TheBitLab projection leaks rights or becomes a second source of truth | High | Deferred/Feature-blocking | Excluded | UC-17 |
| R-21 | Physical/digital/edition relationships are falsely conflated | High | Deferred/Feature-blocking | Physical holdings excluded | UC-02, UC-16 |
| R-22 | Local web workspace exposes filesystem/corpus authority unsafely | Critical | Slice-blocking before real local files/UI | Security-boundary gate | UC-01, UC-05, UC-13 |
| R-23 | Storage/compute/energy growth becomes disproportionate | Medium | Slice-exit / Monitor | Measure rather than optimize prematurely | UC-11-15 |

## 4. Identity and reconciliation risks

### R-01 — False logical identity or destructive merge

> Risk state: `open`
>
> Priority: `working-hypothesis` — Critical / Slice-blocking

**Scenario.** Two different documents, editions, scans or representations are
mistaken for one logical item, or one item is automatically merged based on
weak metadata/semantic evidence.

**Impact.** Provenance can point to the wrong source, later derivatives may be
attributed incorrectly, and a future deduplication/organization feature could
remove or overwrite valuable files.

**Evidence already available.** The canonical model separates logical identity,
location and related representations; UC-01 and UC-16 require ambiguous matches
to remain reviewable.

**Evidence missing.** A rights-safe identity fixture containing exact
duplicates, renames, copies, revised files, same-title/different-edition cases,
PDF/EPUB pairs and deliberately ambiguous examples.

**Leading indicators.** Manual split corrections, low-confidence joins, identity
changing after metadata enrichment, two content hashes collapsed without an
explicit relationship rule.

**Invalidation/narrowing criterion.** If identity cannot be kept stable under
ordinary rename/move and obvious ambiguity cannot be surfaced without high
manual repair, the first slice must narrow to a simpler file-instance catalog
before claiming work-level identity.

**Gate.** Before first-slice promotion, define a conservative identity strategy
that is non-destructive and testable. No automatic content deletion or
irreversible merge is permitted by the first slice.

**Mitigation direction.** Prefer conservative matching, explicit uncertainty,
separate exact-duplicate and related-representation concepts, and reversible
merge/split history. The exact schema is deferred to Glossary/domain work.

**Residual risk.** Entity resolution remains probabilistic for editions,
translations and scans; human correction will remain necessary.

### R-02 — Missing/offline location mistaken for deletion or identity change

> Risk state: `open`
>
> Priority: `working-hypothesis` — High / Slice-blocking

**Scenario.** A removable disk, NAS or temporarily unavailable mount disappears;
Raiatea treats every path as deleted, or an offline move later appears as a new
asset.

**Impact.** False deletion warnings, duplicate identities, unnecessary
reprocessing, broken Smart Collections and misleading provenance.

**Evidence missing.** Reconciliation fixtures for disconnected storage, offline
renames/moves, cross-filesystem copy+delete and later rescan.

**Gate.** The first slice needs at least three distinguishable states where
supported: known-present, unavailable/unknown, and confirmed missing/deleted.
It must not use path absence alone as proof of logical deletion.

**Mitigation direction.** Reconciliation based on multiple signals and explicit
uncertainty; retain location history.

**Residual risk.** Some offline transitions are inherently ambiguous and must
remain unresolved rather than guessed.

## 5. Filesystem mutation and observation risks

### R-03 — Destructive or irrecoverable organization operation

> Risk state: `open`
>
> Priority: Critical / `Feature-blocking`

**Scenario.** A policy, classifier or path bug moves files incorrectly,
overwrites a collision, creates a loop, follows an unsafe symlink, or completes
only part of a batch.

**Impact.** Direct user data loss or a filesystem/catalog divergence.

**Current containment.** UC-09/UC-10 are accepted destination behavior but
**automatic managed organization is excluded from the candidate first slice**.

**Gate before this feature becomes planned.** Evidence for explicit authority,
preview/dry-run, destination/path safety, collision policy, idempotency,
operation journal, reconciliation and bounded recovery. A failure-injection test
must demonstrate that partial operations are visible rather than reported as
success.

**Invalidation criterion.** If the chosen filesystem operation design cannot
provide recoverable intent/history under realistic crash and concurrent-user
cases, automatic organization must remain manual-preview-only.

**Residual risk.** External applications and users can always change files
outside Raiatea; recovery cannot promise transactional semantics across every
filesystem/provider.

### R-04 — Alfred/platform observation gap

> Risk state: `open`
>
> Priority: `working-hypothesis` — High / Slice-blocking with bounded fallback

**Scenario.** Alfred cannot observe the user's target platform, misses events,
overflows, or cannot correlate cross-filesystem moves.

**Impact.** Catalog state drifts from storage reality.

**Accepted boundary.** Raiatea does not create a competing general-purpose
watcher merely to close the gap.

**Gate.** The first slice may proceed only if a **verifiable bounded inventory
and reconciliation route** exists for its chosen environment. Continuous event
coverage on all target operating systems is not required to prove the product
hypothesis.

**Mitigation direction.** Use Alfred where supported; treat rescan/reconcile as
a first-class truth-recovery mechanism; make observation freshness visible.

**Invalidation/narrowing criterion.** If no bounded scan/reconciliation path can
maintain trustworthy catalog state without a second hidden event model, narrow
the first platform/environment rather than duplicate Alfred.

**Residual risk.** Real-time freshness varies by platform/backend; eventual
reconciliation remains necessary.

## 6. P0 extraction viability risks

### R-05 — Structurally wrong extraction presented as trustworthy content

> Risk state: `open`
>
> Priority: Critical / Slice-blocking

**Scenario.** Text looks plausible while reading order, headings, captions,
formulas, tables, code or page coordinates are wrong or missing.

**Impact.** Search, translation, citations, teaching material and derivative
lineage become confidently wrong.

**Evidence missing.** Source-class-specific gold fixtures and metrics for at
least the candidate PDF/EPUB first class. A single aggregate quality score is
insufficient.

**Gate.** #106 must define benchmark dimensions and acceptance/degradation
rules before an extraction route is selected for the first slice. The product
must preserve warnings and source coordinates appropriate to the class.

**Invalidation/narrowing criterion.** A source class whose useful structure
requires unsustainable manual repair is narrowed, delayed or rejected rather
than hidden behind fluent downstream output.

**Mitigation direction.** Compare mature engines/routes, preserve raw output,
benchmark representative failure cases, and make degradation explicit.

**Residual risk.** No parser/OCR route is perfect; downstream consumers must be
able to inspect source evidence.

### R-06 — Extraction cost, latency or manual repair exceeds user value

> Risk state: `open`
>
> Priority: `working-hypothesis` — High / Slice-blocking and Slice-exit

**Scenario.** A high-quality route is too slow, expensive or repair-heavy for a
real personal collection.

**Impact.** Time-to-first-value collapses and users continue using simpler tools.

**Evidence missing.** Benchmark data for wall-clock time, compute, monetary
cost, storage expansion and human correction by source class.

**Gate.** Survey/benchmark must capture quality **and** cost/latency/repair. The
first route is selected on a quality profile, not accuracy alone.

**Slice-exit signal.** If inventory/extraction takes materially more effort than
the user saves when finding and reusing documents, the route or scope must be
narrowed.

**Residual risk.** Expensive source classes may remain opt-in high-quality
routes rather than defaults.

## 7. Provenance and transformation risks

### R-07 — Provenance cannot reconstruct the route to a derivative

> Risk state: `open`
>
> Priority: Critical / Slice-blocking

**Scenario.** A derivative exists but the project cannot identify its exact
source version, extraction route, operation, provider/model version, material
parameters or warnings.

**Impact.** Raiatea violates its core principle that important conclusions and
transformations have a route back.

**Gate.** The first slice's one derivative must carry enough lineage to answer:
**which source/representation and which recorded transformations produced this
artifact?** Bit-for-bit reproduction is not required when external/model
nondeterminism prevents it, but the provenance route is.

**Invalidation criterion.** If a proposed processing shortcut cannot preserve
this route, it is not acceptable as a Raiatea derivative path.

**Mitigation direction.** Immutable/append-style transformation records and
explicit gaps for imported legacy artifacts; exact schema remains later work.

**Residual risk.** Provider-side models may disappear or be nondeterministic;
route reproducibility is stronger than result reproducibility.

### R-08 — Invalid intermediate/cache reuse

> Risk state: `open`
>
> Priority: High / Feature-blocking; reduced first-slice exposure

**Scenario.** A previous extraction or translation is reused after source,
parameters, glossary, engine or validity changed.

**Impact.** Outputs appear current but derive from stale evidence.

**Current containment.** The first proof requires only the **single-output
subset** of UC-13, not multi-output branching or aggressive cache reuse.

**Gate before generalized DAG reuse.** Define validity/invalidation evidence for
source version + operation + material parameters; failure/retry semantics must
not silently reuse unknown intermediates.

**Residual risk.** Some semantic invalidation rules cannot be inferred
perfectly; manual forced-recompute must remain possible.

### R-13 — Processing/recovery leaves unknown or duplicated state

> Risk state: `open`
>
> Priority: High / Slice-blocking for minimal processing

**Scenario.** A process crashes or is cancelled and the catalog cannot tell
whether an output completed, is partial, or was registered twice.

**Impact.** Broken lineage, duplicate derivatives and unsafe retry.

**Gate for first slice.** The one Processing Recipe must expose at least
pending/running/succeeded/failed-or-unknown semantics sufficient to prevent an
unknown state from being silently promoted to success. Retrying must not
silently duplicate a valid completed derivative.

**Feature gate for destructive/complex jobs.** Stronger idempotency, partial-DAG
and recovery evidence is required before multi-output or filesystem mutation.

**Residual risk.** External provider side effects may not be transactionally
reversible.

### R-14 — Premature Durex coupling

> Risk state: `open`
>
> Priority: Medium/High / Feature-blocking

**Scenario.** Raiatea depends on Durex's current coding-agent database or
lifecycle simply because it already has worker/run concepts.

**Impact.** Hidden coupling, wrong abstractions and migration cost.

**Gate.** No first-slice requirement may depend on Durex internals. Reuse needs
a separate audit choosing among a generalized contract/core or independent
execution with shared patterns.

**Residual risk.** A later generalized Durex core can still evolve; contracts
need versioning.

## 8. Rights, privacy and security risks

### R-09 — Rights/privacy boundary violation

> Risk state: `open`
>
> Priority: Critical / Slice-blocking

**Scenario.** A private/licensed source, extracted text, physical location or
prompt context is stored, sent to a remote provider or projected to a consumer
outside the user's authority.

**Impact.** Privacy breach, rights violation and loss of trust; potentially
legal consequences requiring specialist review.

**Gate before first slice on real material.** Use a rights-safe corpus or
explicitly authorized private corpus and define, at minimum, which operations
are local versus remote and what data each provider receives. Processing rights
must remain distinct from redistribution rights.

**Gate before remote-provider use.** Explicit data boundary and user authority;
no prompt/content can silently elevate permissions.

**Gate before TheBitLab projection.** Rights and visibility semantics must be
propagated; UC-17 remains deferred from the first proof.

**Specialist review trigger.** Unclear copyright/licensing, retention or legal
deletion obligations are escalated rather than guessed by architecture.

**Residual risk.** Rights can differ by source/jurisdiction/license and can
change over time.

### R-22 — Local web workspace exposes filesystem or corpus authority unsafely

> Risk state: `open`
>
> Priority: Critical / Slice-blocking before a real local UI controls files

**Scenario.** The local web app is reachable by an unintended origin/process,
accepts untrusted content as commands, leaks files, or lets browser/UI state
bypass backend authority checks.

**Impact.** Local file disclosure or mutation and private-corpus exposure.

**Gate.** Before the first slice handles valuable real files through a web UI,
define a minimal local threat boundary: authentication/origin assumptions,
backend-owned authorization, path/scope checks, and separation of displayed
source text from executable control input. The final security architecture is
not selected here.

**Current containment.** The first slice need not expose automatic filesystem
mutation.

**Residual risk.** Desktop packaging does not automatically make a web surface
safe; the same authority boundary must survive packaging.

## 9. Search and view integrity risks

### R-10 — Deterministic search or view state is stale/unexplained

> Risk state: `open`
>
> Priority: High / Slice-blocking and Slice-exit

**Scenario.** A known matching document is missing, a stale document remains,
or the user cannot understand why an item is in a result/view/Smart Collection.

**Impact.** The central “find what I have” value becomes unreliable.

**Gate.** Before first-slice promotion, define observable index freshness and a
way to reconcile inventory→index state. Deterministic filters used by the first
proof must have inspectable semantics.

**Slice-exit evidence.** A test corpus with known queries should measure known
item retrieval, false/missing membership and update behavior after add/change/
move/delete/reconcile.

**Residual risk.** Semantic topic classification remains less deterministic
than exact metadata/full text and must expose that distinction.

### R-11 — Natural-language query silently changes intent

> Risk state: `open`
>
> Priority: High / Deferred + Feature-blocking

**Scenario.** A model converts a prompt into wrong filters and the user trusts
the result.

**Current containment.** Natural-language query interpretation is excluded from
the first proof; deterministic search comes first.

**Gate before feature planning.** Query plans remain visible/editable and the
system can reject unsupported criteria instead of fabricating executable
meaning. Remote-model privacy boundary must also pass R-09.

**Residual risk.** Natural language remains ambiguous; the product can expose,
not eliminate, that ambiguity.

## 10. Translation and rendering risks

### R-12 — Fluent/beautiful derivative is materially wrong

> Risk state: `open`
>
> Priority: High, potentially Critical for evidence-bearing content /
> Feature-blocking

**Scenario.** Translation changes technical meaning, corrupts code/citations/
formulae, or layout reconstruction hides missing/overflowing content while
looking polished.

**Current containment.** Translation, facsimile and layout-faithful generation
are excluded from the first proof.

**Gate before translation planning.** Define quality dimensions, terminology
policy, preserved-structure requirements and explicit partial/degraded state.

**Gate before facsimile/layout-faithful planning.** Define visual fidelity checks
and acceptable/manual-repair evidence. Never promise unqualified pixel identity
for translated text.

**Invalidation/narrowing criterion.** If manual repair cost dominates reading or
source use, offer semantic-reflow/translation as a different product mode or
defer the class.

**Residual risk.** Linguistic correctness remains partly judgment-dependent;
high-stakes use requires stronger domain controls.

## 11. Product and architecture risks

### R-15 — Product value is below simpler alternatives

> Risk state: `open`
>
> Priority: Critical / Slice-exit and kill criterion

**Scenario.** A file manager/search index plus ordinary LLM or existing document
tools gives equal/better value with less setup and maintenance.

**Impact.** The product thesis is invalid even if the architecture is elegant.

**Evidence required.** Measure at least:

- time to inventory a bounded real collection;
- time/steps to find known material and resume prior work;
- correction burden for identity/index/provenance errors;
- reuse of saved views/Smart Collections/derivatives;
- time to first useful artifact;
- comparison with a transparent simpler baseline.

**Kill/narrow criterion.** If the first slice cannot provide a more durable,
inspectable or materially easier result than the simpler baseline under similar
effort, narrow or stop the document-surface direction rather than add more
infrastructure.

**Residual risk.** Maintainer value may not generalize to other users; later
supervised users are needed before broad product claims.

### R-16 — Scope and architecture grow faster than validated value

> Risk state: `open`
>
> Priority: Critical / Slice-blocking governance gate

**Scenario.** The first proof accumulates automatic organization, translation,
GraphRAG, knowledge graph, multi-host execution, TheBitLab integration and agent
orchestration before validating inventory/search/value.

**Impact.** Long feedback loops, sunk cost and an architecture that obscures
product failure.

**Gate.** The candidate first slice remains exactly bounded to PDF/EPUB inventory,
path-independent identity, benchmarked P0 extraction, deterministic search,
logical views, one Smart Collection, one single-output recipe and lineage unless
a new explicit roadmap decision changes it.

**Invalidation signal.** A “required” dependency appears that cannot be traced
to a first-slice use case or to a blocking risk control.

**Residual risk.** Some foundational work may appear larger than its visible
feature; it needs evidence and scope boundaries rather than arbitrary line-count
limits.

### R-17 — Premature vocabulary/schema freeze

> Risk state: `open`
>
> Priority: Medium / Feature-blocking

**Scenario.** Provisional terms such as Asset, Source, Work or Manifestation
become database/API contracts before ambiguous use cases and Glossary resolve
their meaning.

**Impact.** Expensive migrations and conceptual coupling.

**Gate.** The first slice may use internal provisional names, but public/stable
schema contracts wait for Glossary/domain review. Use-case IDs are not schema
identifiers.

### R-19 — Provider/model lock-in despite an adapter surface

> Risk state: `open`
>
> Priority: High / Slice-blocking design constraint and Slice-exit evidence

**Scenario.** The “generic” contract leaks one provider's concepts so deeply that
replacing the engine changes the core model or loses provenance.

**Gate.** The #106 survey should compare at least two routes/providers where a
comparison is meaningful and ensure provider-specific data can be preserved as
extension metadata rather than core truth.

**Slice-exit evidence.** Demonstrate that the first extraction/processing route
is identified by a replaceable adapter boundary and that provenance records the
provider rather than hiding it.

**Residual risk.** Some source-class features will remain provider-specific;
replaceability does not mean lowest-common-denominator behavior.

### R-23 — Storage/compute/energy growth becomes disproportionate

> Risk state: `open`
>
> Priority: Medium / Monitor + Slice-exit

**Scenario.** Raw copies, OCR layers, indexes, embeddings and derivatives multiply
storage or compute beyond the benefit.

**Gate.** Do not optimize speculatively, but measure source bytes, derived bytes,
processing time and compute/provider cost for the first corpus. Retention of
provenance-critical data must not be silently sacrificed to reduce cost.

## 12. Data durability and migration risk

### R-18 — Catalog/source-of-truth corruption or unrecoverable migration

> Risk state: `open`
>
> Priority: Critical / Slice-blocking before valuable corpus dependence

**Scenario.** Raiatea's catalog is the source of truth for logical identity and
lineage, but a database corruption, bad migration or application bug destroys
that state even though files remain.

**Impact.** Views, Smart Collections, identity relationships and provenance may
be lost; the user may have to reconstruct the entire library.

**Gate.** Before the first slice is trusted with a valuable corpus, define a
minimal export/backup/rebuild story for catalog state. At minimum distinguish
what can be regenerated from files from what is user-authored or provenance
state that requires durable backup.

**Invalidation criterion.** A storage design that cannot safely version/migrate
or export irreplaceable state conflicts with the Manifesto portability
principle.

**Residual risk.** Rebuilding indexes may be possible while restoring user
corrections/history requires backups; the distinction must remain explicit.

## 13. Deferred integration risks

### R-20 — TheBitLab projection leaks rights or becomes a second source of truth

> Risk state: `open`
>
> Priority: High / Deferred + Feature-blocking

**Current containment.** UC-17 is excluded from the first proof.

**Gate.** Before integration, define projection/versioning, rights propagation,
source unavailability behavior and which fields remain owned by TheBitLab versus
Raiatea. No copied universal catalog becomes authoritative in the consumer.

### R-21 — Physical/digital/edition relationships are falsely conflated

> Risk state: `open`
>
> Priority: High / Deferred + Feature-blocking

**Current containment.** Physical holdings are excluded from the first proof.

**Gate.** Before broad physical catalog linking, test ISBN/edition/translation/
scan ambiguity and preserve reversible candidate relationships. A physical
holding never implies full-text availability.

## 14. First-slice promotion gate

> Assertion status: `provisional-decision`

The candidate first slice remains a `working-hypothesis` until the following
**planning gates** are satisfied. These gates authorize planning/implementation;
they do not prove the slice successful.

### G-01 — Scope containment

Required:

- first slice remains PDF/EPUB + inventory + identity + P0 extraction +
  deterministic search + logical views + one Smart Collection + one
  single-output Processing Recipe + lineage;
- automatic managed organization, physical holdings, NL search, translation,
  layout reconstruction, multi-output branching, TheBitLab and generalized
  Durex are excluded unless a separate roadmap decision adds them.

Blocks on: R-16.

### G-02 — Rights-safe data boundary

Required:

- benchmark/first-slice corpus has explicit processing rights;
- local versus remote provider data flow is declared before real corpus use;
- redistribution is not inferred from processing permission.

Blocks on: R-09, R-22.

### G-03 — Conservative identity/reconciliation plan

Required:

- exact duplicate, rename/move and ambiguous-related cases are represented in a
  test fixture;
- no irreversible automatic merge/deletion;
- missing/offline is distinguishable from proven deletion where evidence allows;
- inventory/reconciliation path works in the chosen first environment without a
  second general-purpose watcher.

Blocks on: R-01, R-02, R-04.

### G-04 — P0 benchmark contract

Required:

- source-class metrics/fixtures for candidate PDF/EPUB are declared;
- quality, latency/cost/manual repair and degradation are measured separately;
- routing/provider choice follows benchmark evidence rather than preference;
- insufficient source-class quality narrows the class instead of being hidden.

Blocks on: R-05, R-06, R-19.

### G-05 — Minimum provenance/processing state

Required:

- derivative can be traced to source/representation and recorded operations;
- provider/engine version and material warnings are recorded where applicable;
- success, failure and unknown/partial state cannot be silently conflated;
- first recipe has a retry/recovery behavior that cannot silently duplicate a
  known successful output.

Blocks on: R-07, R-13; contains first-slice part of R-08.

### G-06 — Deterministic search/view integrity plan

Required:

- exact filter semantics used by the proof are inspectable;
- inventory→index freshness/reconciliation is observable;
- Smart Collection stores its rule separately from current membership;
- NL query interpretation is not required.

Blocks on: R-10; defers R-11.

### G-07 — Catalog durability and local security boundary

Required:

- irreplaceable catalog/provenance/user corrections have a minimal backup/export
  strategy;
- local web/backend authority assumptions are documented before accessing a
  valuable corpus;
- UI cannot grant filesystem scope that backend policy has not authorized.

Blocks on: R-18, R-22.

When G-01 through G-07 have evidence and no unresolved Critical contradiction,
#98/#106 may consider promoting the candidate first slice to `planned` through
a separate explicit roadmap decision. This Risk List does **not** perform that
promotion itself.

## 15. First-slice exit and kill criteria

> Assertion status: `working-hypothesis` pending measured thresholds

Once implemented, the first slice must not be declared validated merely because
it runs. Before implementation, its experiment plan should predeclare concrete
thresholds for the following dimensions:

1. **Identity stability** — controlled moves/renames do not create false new
   logical identities; ambiguous cases are surfaced rather than force-merged.
2. **Extraction quality** — candidate source classes meet their declared
   structural/content/coordinate quality profile with visible degradation.
3. **Search usefulness** — known items can be found and catalog changes become
   searchable within the declared freshness/reconciliation model.
4. **Lineage completeness** — the test derivative's route back to the source and
   transformations is reconstructable.
5. **Correction burden** — identity/extraction/search errors do not require more
   manual maintenance than the value produced.
6. **Time to first useful result** — inventory and first useful search/artifact
   are competitive with the predeclared simpler baseline.
7. **Portability/recovery** — irreplaceable catalog state can be exported/backed
   up and restored/rebuilt according to the declared contract.
8. **Privacy/rights** — no operation crosses the declared provider/storage/data
   boundary without authority.

### Narrow/pause/kill signals

The direction must be narrowed, paused or rejected when sustained evidence
shows one or more of these:

- false identity merges cannot be kept rare/reviewable without excessive manual
  repair;
- P0 quality for the priority source class is materially below what search and
  provenance need, or repair cost is unacceptable;
- the product cannot maintain a trustworthy catalog when the filesystem changes
  under the chosen bounded environment;
- the derivative route cannot preserve meaningful provenance;
- private/rights-safe use requires operational assumptions the project cannot
  enforce;
- time-to-first-value and correction burden are worse than a simpler baseline
  without a compensating durable benefit;
- additional infrastructure is repeatedly proposed because the narrow product
  does not create value.

Threshold values belong in the benchmark/experiment plan after representative
fixtures and baseline measurements exist. Inventing numbers in Inception would
create false precision.

## 16. Capability gates outside the first slice

> Assertion status: `accepted-decision` for the need for a gate;
> exact thresholds remain future evidence

| Capability | Must remain out until | Primary risks |
| --- | --- | --- |
| Automatic managed organization | authority + preview + collision/path safety + idempotency + recovery/failure injection demonstrated | R-03, R-04, R-13, R-18, R-22 |
| Natural-language search | deterministic query model stable + inspectable plans + privacy boundary | R-09, R-10, R-11 |
| Translation | translation quality dimensions + terminology/structure preservation + provider privacy/provenance | R-09, R-12, R-19 |
| Facsimile/layout-faithful generation | visual quality/degradation checks + font/assets rights + repair cost evidence | R-12, R-23 |
| Multi-output DAG/caching | validity/invalidation + partial failure/retry + lineage evidence | R-07, R-08, R-13 |
| Durex integration | dedicated Job/Run reuse audit shows a stable boundary | R-14 |
| Physical holding/work linking | edition/identity ambiguity fixtures + reversible relationships | R-01, R-21 |
| TheBitLab projection | rights/versioning/ownership contract | R-09, R-20 |

## 17. Risk ownership and next evidence

> Assertion status: `provisional-decision`

| Risk area | Next owner / evidence surface |
| --- | --- |
| Identity/reconciliation | Glossary/domain contract + first-slice fixture/experiment |
| Filesystem observation | Alfred integration evidence + reconciliation tests |
| Filesystem mutation | Later organization design/threat model; not first slice |
| P0 extraction | #106 survey, benchmark corpus and quality profile |
| Provenance/processing | P0/Processing contract and first derivative experiment |
| Rights/privacy | source/rights taxonomy + provider-boundary review; specialist review when needed |
| Search/views | first-slice deterministic query/index experiment |
| Translation/rendering | later benchmark/profile; excluded first slice |
| Job/run/recovery | first-slice minimal run-state experiment; Durex audit later |
| Product value | first-slice experiment against simpler baseline |
| Vocabulary/schema | `07-glossary.md` and later domain model |
| Catalog durability/security | first-slice architecture/threat model before valuable corpus |

## 18. Out of scope

This Risk List does not:

- choose database, search engine, vector store or graph store;
- select Docling, OCR, VLM, translation or rendering providers;
- define a complete cybersecurity threat model;
- issue legal advice or replace specialist rights review;
- generalize Durex;
- modify Alfred or TheBitLab;
- define the final Asset/Source/Work schema;
- set fabricated numerical thresholds before benchmark fixtures exist;
- promote the candidate first slice to `planned`;
- schedule P1-P7.

## 19. Decisions passed forward

### Glossary

Stabilize enough vocabulary to prevent identity/representation/location and
source/derivative ambiguity without turning provisional words into premature
storage schemas.

### P0 #106

Use G-02/G-04/G-05 and R-05/R-06/R-07/R-09/R-19 to structure source taxonomy,
survey, benchmark, extraction bundle and degradation criteria.

### First-slice planning

Only after G-01 through G-07 receive explicit evidence should a separate
roadmap issue promote the candidate slice to `planned`. That planning issue must
predeclare measurable exit/kill thresholds rather than weakening this Risk List.

### Inception Review

The final review must check whether Critical risks are either contained for the
first experiment, deliberately deferred with their feature, or strong enough to
invalidate the proposed direction. Open Critical risks must not disappear from
the roadmap merely because implementation work has started.
