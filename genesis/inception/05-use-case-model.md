# Raiatea Use Case Model

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 1.0.0
>
> Last reviewed: 21 August 2026
>
> Accepted through: [PR #114](https://github.com/kinderp/raiatea/pull/114)
>
> Parent issue: [#98](https://github.com/kinderp/raiatea/issues/98)
>
> Child issue: [#113](https://github.com/kinderp/raiatea/issues/113)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Primary canonical sources: [`02-vision.md`](02-vision.md),
> [`03-system-context.md`](03-system-context.md), and
> [`04-product-map.md`](04-product-map.md)

## 1. Purpose

This document defines the significant user goals and external interactions that
must guide Raiatea before detailed domain schemas, APIs or implementation
technology are selected.

It answers **what a person must be able to accomplish and what must remain true
when things go wrong**. It deliberately does not define database tables,
classes, REST endpoints, event schemas, UI routes, parser choices or worker
implementations.

Use-case identifiers such as `UC-01` are editorial references for planning,
review and risk traceability. They are not API identifiers and do not freeze
future package or service boundaries.

## 2. Status rules

> Assertion status: `accepted-decision`

This model preserves the status taxonomy already accepted by Inception:

- `accepted-decision`: the user outcome, product invariant or ownership
  boundary is accepted, but implementation may be absent;
- `planned`: approved implementation work exists with roadmap authority;
- `working-hypothesis`: useful candidate behavior or first-slice composition
  still requires evidence;
- `provisional-decision`: a reversible integration or architecture choice
  remains open;
- `deferred-research`: relevant future work is intentionally outside the
  current roadmap.

P0 Source Ingestion & Extraction is the only platform foundation currently
`planned` through #106. The Universal Document & Asset Library outcomes below
are accepted direction unless a use case says otherwise; accepted does not mean
implemented.

## 3. System boundary and actors

### 3.1 Actor-model rule

> Assertion status: `accepted-decision`

An **actor** is a human role or external system that interacts with Raiatea from
outside the Raiatea boundary. Filesystem events, Processing Recipes, internal
jobs, timers and pipeline stages are **triggers or internal mechanisms**, not
actors. This distinction prevents the use-case model from accidentally fixing a
future internal architecture.

### 3.2 Primary actor — Person / Library owner

> Assertion status: `accepted-decision`

The primary actor is a person who owns or can lawfully access heterogeneous
physical and digital material and wants to inventory, locate, search, organize,
transform and reuse it without losing provenance or control.

The first validation domain remains a self-directed technical learner working
with AI-engineering material, but the use cases must not encode AI-specific
assumptions.

### 3.3 Supporting external system — Alfred

> Assertion status: `accepted-decision`

Alfred supplies filesystem observations within its supported platform/backend
scope. It may report create, ready/change, move/rename, delete and resync facts.
It does not decide document identity, classification, search membership,
organization policy or transformations.

### 3.4 Supporting external system — Filesystem / storage

> Assertion status: `accepted-decision`

Digital representations may live in local, mounted, removable, NAS or future
compatible storage locations. A storage path is a mutable location, not the
canonical identity of the logical asset/source.

### 3.5 Supporting external providers

> Assertion status: `accepted-decision`

Parsers, OCR/VLM engines, translation providers, renderers/converters and
metadata resolvers are replaceable external providers behind Raiatea-owned
contracts. Named products are not selected by this model.

### 3.6 External consumer — TheBitLab

> Assertion status: `accepted-decision`

TheBitLab consumes course-scoped source/provenance projections. It owns
course-specific selection and educational semantics, not Raiatea's universal
source-of-truth library.

### 3.7 Durex is not a required actor yet

> Assertion status: `provisional-decision`

Durex remains candidate Job/Run reuse. No use case in this model requires a
Durex runtime dependency. Long-running processing behavior must remain valid
whether execution is later provided by a generalized Durex contract or a
Raiatea-owned execution plane.

## 4. Cross-cutting invariants

> Assertion status: `accepted-decision`

Every applicable use case must preserve these invariants:

1. **Location is not identity.** Moving or renaming a file does not by itself
   create a new logical asset/source.
2. **Catalog classification is not filesystem organization and is not the
   current UI view.** These can change independently.
3. **Observation is not authority.** A filesystem event or model suggestion
   never grants permission to mutate user files.
4. **Original is not derivative.** Acquisition, extraction, normalization,
   translation, conversion and later interpretation remain distinguishable.
5. **Model output is not trusted identity evidence by default.** AI-generated
   metadata, classifications and query plans remain inspectable and correctable.
6. **Physical holding is not full text.** Cataloging a physical item does not
   imply that its complete digital contents are available.
7. **Course projection is not the universal catalog.** TheBitLab may consume a
   bounded projection without becoming another source of truth.
8. **P0 is not the Document Library UX owner.** P0 owns ingestion/extraction
   orchestration and contracts; catalog, views, organization intent and
   Processing Recipes belong to the document surface.
9. **Failure does not erase history.** Missing files, failed processing or
   rejected organization operations do not silently delete provenance or valid
   prior derivatives.
10. **Consequential mutations remain recoverable and auditable.** Automatic
    organization must expose enough history to diagnose and recover from a bad
    policy or classifier.

## 5. Use-case map

| ID | Use case | Status | Primary product surface |
| --- | --- | --- | --- |
| UC-01 | Inventory an existing digital collection | `accepted-decision` capability; absent | Document & Asset Library |
| UC-02 | Register a physical holding | `accepted-decision` capability; absent | Document & Asset Library |
| UC-03 | Preserve identity across rename or move | `accepted-decision` capability; absent | Registry + Alfred integration |
| UC-04 | Handle missing or deleted locations | `accepted-decision` capability; absent | Registry + provenance |
| UC-05 | Search with deterministic criteria | `accepted-decision` capability; absent | Search & Discovery |
| UC-06 | Search with natural language | `accepted-decision` direction; absent | Search & Discovery |
| UC-07 | Browse through logical views | `accepted-decision` capability; absent | Dynamic Views |
| UC-08 | Save and maintain a Smart Collection | `accepted-decision` capability; absent | Smart Collections |
| UC-09 | Preview an organization policy | `accepted-decision` capability; absent | Organization |
| UC-10 | Apply an authorized managed organization operation | `accepted-decision` capability; absent | Organization |
| UC-11 | Extract a source through P0 | `planned` through #106 | P0 Source Ingestion & Extraction |
| UC-12 | Translate a source without replacing the original | `accepted-decision` capability; absent | Processing Recipes |
| UC-13 | Run a Processing Recipe, including multi-output DAGs | `accepted-decision` capability; absent | Processing Recipes |
| UC-14 | Select and evaluate a visual fidelity objective | `accepted-decision` capability; absent | Processing Recipes |
| UC-15 | Inspect derivative lineage | `accepted-decision` capability; absent | Provenance / document detail |
| UC-16 | Relate physical and digital representations | `accepted-decision` capability; absent | Registry |
| UC-17 | Provide a course-scoped source projection to TheBitLab | `accepted-decision` target; absent | External consumer projection |
| UC-18 | Recover after processing or organization failure | `accepted-decision` safety outcome; absent | Cross-cutting |

## 6. Significant use cases

### UC-01 — Inventory an existing digital collection

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Make an existing user-selected collection visible in Raiatea without
reorganizing it by default.

**Primary actor.** Person.

**Supporting systems.** Filesystem/storage; Alfred where supported; optional
metadata providers; P0 when content extraction is requested.

**Preconditions.** The person selects a location they are authorized to read
and declares an authority mode such as observed, managed, inbox or frozen.

**Trigger.** The person asks Raiatea to inventory the location.

**Main success path.**

1. Raiatea initiates a bounded inventory using the supported scanning/
   observation boundary without introducing a second general-purpose watcher.
2. It records stable logical identities or candidate identities separately from
   path locations.
3. It records basic observable metadata, fingerprints and current locations.
4. Exact duplicates and possible related representations are surfaced without
   destructive automatic merging.
5. Search/indexing work occurs only according to configured policy and rights.
6. The collection becomes navigable through the catalog.
7. No file is moved merely because it was inventoried.

**Alternatives and failures.** Unreadable files, unavailable mounts, unsupported
formats, permission failures and ambiguous duplicate matches remain visible as
states requiring retry, narrower handling or review.

**Postconditions.** The catalog has a recoverable inventory of what was observed
and where it was found. Filesystem layout is unchanged unless separately
authorized.

**Key invariants.** Location is not identity; observation is not authority;
classification is not organization.

**Risk handoff.** False duplicate merges, scale/latency, inaccessible content,
rights leakage, unstable removable/NAS locations.

### UC-02 — Register a physical holding

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Record that the person owns or can access a physical book or other
physical item and can find it again.

**Primary actor.** Person.

**Supporting systems.** Optional ISBN/metadata resolver.

**Preconditions.** The person can identify the holding sufficiently to catalog
it and may specify a physical location such as room, bookcase and shelf.

**Trigger.** The person adds a physical holding.

**Main success path.**

1. Raiatea records a logical holding and its physical location.
2. User-entered metadata remains distinguishable from provider-enriched
   metadata.
3. Optional ISBN or other identifiers may help suggest a relationship to an
   existing work or digital representation.
4. The person can search and browse the holding with digital assets.

**Alternatives and failures.** Missing ISBN, ambiguous edition, conflicting
metadata or an uncertain work relationship remain reviewable instead of being
silently resolved.

**Postconditions.** The physical holding is discoverable without implying that
its full text exists digitally.

**Key invariants.** Physical holding is not full text; model/provider metadata
is not unquestionable identity evidence.

**Risk handoff.** Edition conflation, metadata authority, privacy of physical
location, incorrect work/representation merge.

### UC-03 — Preserve identity across rename or move

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Keep one logical asset/source identity when its digital file is moved
or renamed.

**Primary actor.** Person.

**Supporting systems.** Alfred; filesystem/storage.

**Preconditions.** A digital representation is already known to Raiatea and its
old location is observable or otherwise reconcilable.

**Trigger.** The person moves/renames the file, or an authorized organization
operation causes the filesystem transition.

**Main success path.**

1. Alfred or a supported reconciliation path reports the filesystem transition.
2. Raiatea matches the transition to the known logical identity using the
   available event/fingerprint/location evidence.
3. The current location changes while logical identity remains stable.
4. Location history is preserved when required for provenance/audit.
5. Search results, views and Smart Collections continue referencing the same
   logical item.

**Alternatives and failures.** Move correlation may be incomplete after offline
changes, mount loss, cross-filesystem copy/delete behavior or watcher gaps.
Raiatea marks identity reconciliation as uncertain instead of manufacturing a
confident transition.

**Postconditions.** A successful move or rename does not create a duplicate
logical source.

**Key invariants.** Location is not identity; observation is not mutation
authority.

**Risk handoff.** False identity joins, missed events, cross-filesystem moves,
watcher overflow/resync, concurrent changes.

### UC-04 — Handle missing or deleted locations

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Let the person understand that a known digital location is unavailable
or deleted without silently erasing history and valid derivatives.

**Primary actor.** Person.

**Supporting systems.** Alfred; filesystem/storage.

**Preconditions.** Raiatea knows the logical item and at least one prior
location.

**Trigger.** Alfred or a reconciliation process reports a delete/missing fact,
or a storage location becomes unavailable.

**Main success path.**

1. Raiatea marks the affected location as missing, deleted or unavailable with
   appropriate uncertainty.
2. Other known locations or representations remain usable.
3. Provenance and transformation lineage remain queryable.
4. Derived artifacts are not deleted merely because one source location is no
   longer present.
5. The person can distinguish temporary unavailability from confirmed deletion
   where evidence permits.

**Alternatives and failures.** A disconnected external drive or NAS must not be
silently treated as confirmed deletion when the evidence only proves
unavailability.

**Postconditions.** Current availability changes; historical identity and
lineage remain intact.

**Key invariants.** Failure does not erase history; missing location is not
necessarily source deletion.

**Risk handoff.** False deletion, stale availability, retention requirements,
legal deletion requests versus historical provenance.

### UC-05 — Search with deterministic criteria

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Find material using explicit criteria whose meaning is inspectable and
repeatable.

**Primary actor.** Person.

**Preconditions.** Relevant catalog metadata or extracted content exists.

**Trigger.** The person enters filters or a query.

**Main success path.**

1. The person chooses criteria such as type, format, language, location, author,
   date, processing state, topic or full-text terms.
2. Raiatea executes the criteria against known catalog/index state.
3. Results expose matching logical items rather than opaque generated answers.
4. Active criteria remain visible and editable.
5. The query can be refined or saved.

**Alternatives and failures.** Unsupported fields, incomplete metadata,
unindexed content and ambiguous semantic classifications are visible as limits.

**Postconditions.** The person has a reproducible result set and can inspect why
items matched.

**Key invariants.** Search membership is not filesystem organization; results
refer to logical identities.

**Risk handoff.** Stale indexes, hidden filter semantics, poor ranking, scale,
privacy across mixed collections.

### UC-06 — Search with natural language

> Assertion status: `accepted-decision` for the interaction direction;
> implementation absent

**Goal.** Express a complex search in ordinary language without making the LLM
an opaque retrieval authority.

**Primary actor.** Person.

**Supporting systems.** Replaceable language-model/query-planning provider.

**Preconditions.** Raiatea exposes a structured query model for the currently
supported search capabilities.

**Trigger.** The person enters a request such as “English books and papers about
RAG after 2023 that do not yet have an Italian translation.”

**Main success path.**

1. Raiatea sends only necessary context to the configured interpreter.
2. The interpreter proposes structured criteria.
3. Raiatea displays the interpreted criteria before or with results.
4. The person may edit the criteria.
5. The search engine executes the final structured query.
6. The structured query, not the model prose, may be saved as a Smart
   Collection.

**Alternatives and failures.** Ambiguous prompts, unsupported fields and model
errors produce a visible interpretation gap; the system must not fabricate a
filter that it cannot execute.

**Postconditions.** The result remains reproducible without depending on the
same model response later.

**Key invariants.** Model output is not trusted fact; the model interprets query
intent rather than replacing the index.

**Risk handoff.** Prompt ambiguity, data leakage to remote providers,
unexecutable query plans, inconsistent semantic terminology.

### UC-07 — Browse through logical views

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Explore the same catalog through different organizational lenses
without moving or copying underlying files.

**Primary actor.** Person.

**Preconditions.** Catalog items and relevant metadata/classifications exist.

**Trigger.** The person switches or configures a view.

**Main success path.**

1. Raiatea projects the same logical identities into a selected view such as
   folder/location, table, cover grid, author, language, topic, project, course,
   year/timeline or processing status.
2. One logical item may appear in several views.
3. Changing the view changes presentation/grouping only.
4. The person can navigate from a view item to its detail/provenance.

**Alternatives and failures.** Missing metadata yields an explicit unclassified
or unknown group rather than disappearance.

**Postconditions.** No file location changes because the user changed a view.

**Key invariants.** Location, classification and current view are distinct.

**Risk handoff.** Confusing virtual and physical organization, stale grouping,
classification drift.

### UC-08 — Save and maintain a Smart Collection

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Preserve a dynamic selection rule whose membership updates when the
catalog changes.

**Primary actor.** Person.

**Preconditions.** A valid structured query or selection rule exists.

**Trigger.** The person saves the criteria as a Smart Collection.

**Main success path.**

1. Raiatea stores the durable selection rule separately from current members.
2. Current matching logical identities are shown.
3. New or updated items are evaluated against the same rule.
4. Membership changes are explainable by the criteria and item state.
5. The person can edit, pause, duplicate or delete the Smart Collection without
   deleting underlying assets.

**Alternatives and failures.** If a criterion becomes unsupported after a
schema/search evolution, Raiatea marks the collection degraded and preserves the
rule for repair rather than silently changing its meaning.

**Postconditions.** Collection membership is a projection, not stored ownership
of duplicate files.

**Key invariants.** Smart Collection is not source of truth and is not a folder.

**Risk handoff.** Semantic drift, migration of saved queries, expensive
reevaluation, confusing auto-membership changes.

### UC-09 — Preview an organization policy

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Understand what an organization rule would change before any
filesystem mutation occurs.

**Primary actor.** Person.

**Supporting systems.** Filesystem/storage for collision and destination
checks.

**Preconditions.** The person has a managed-capable scope and a candidate rule
based on supported catalog/content criteria.

**Trigger.** The person asks to preview a policy or policy change.

**Main success path.**

1. Raiatea evaluates the policy against current logical items.
2. It proposes affected files, source locations and destination paths.
3. It explains which criteria caused each proposal.
4. It detects obvious collisions, unsafe destinations and authority violations.
5. The person can exclude items or modify the rule before applying anything.
6. No file changes during preview.

**Alternatives and failures.** Unknown metadata, ambiguous classification or
unavailable destinations produce explicit unresolved proposals rather than
forced moves.

**Postconditions.** A reviewable plan exists; filesystem state is unchanged.

**Key invariants.** Observation is not authority; preview is not execution.

**Risk handoff.** Destructive paths, name collisions, classifier errors,
symlink/path traversal, large batch surprises.

### UC-10 — Apply an authorized managed organization operation

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Move or rename files inside an explicitly managed scope according to
an approved policy while preserving identity and recoverability.

**Primary actor.** Person.

**Supporting systems.** Filesystem/storage; Alfred for resulting observation and
reconciliation.

**Preconditions.** The scope authorizes mutation, a valid preview/plan exists or
an equivalent safe decision has been made, and destinations have passed
applicable checks.

**Trigger.** The person approves the organization operation, or a previously
explicitly authorized policy reaches its defined execution condition.

**Main success path.**

1. Raiatea records the intended operation and affected logical identities.
2. It performs collision-safe move/rename operations only inside authorized
   scope.
3. Resulting filesystem facts are observed/reconciled.
4. Logical identity remains stable while current location and history update.
5. Search/views/Smart Collections remain based on catalog facts rather than the
   old folder path.
6. Enough operation history is retained for recovery or diagnosis.

**Alternatives and failures.** Partial batch failure, unavailable destination,
permission changes or concurrent user moves stop or isolate affected operations
without pretending the full plan succeeded.

**Postconditions.** Successful items have new locations; failed items remain in
known states; no duplicate logical identities are created solely by the move.

**Key invariants.** Mutation requires authority; location is not identity;
consequential actions are auditable/recoverable.

**Risk handoff.** Partial transactions, rollback semantics, recursive move
loops, user/manual conflict, permissions and path safety.

### UC-11 — Extract a source through P0

> Assertion status: `planned` through #106

**Goal.** Let the person obtain structured, source-linked extraction from a
supported source without making one parser or model the Raiatea core.

**Primary actor.** Person.

**Supporting systems.** Replaceable parser/OCR/VLM providers.

**Preconditions.** The source is lawfully available for the requested processing
and a supported/benchmarkable route exists or can fail visibly.

**Trigger.** The person requests extraction, or an already-authorized internal
Processing Recipe reaches an extraction stage on the person's behalf.

**Main success path.**

1. P0 probes the source and selects a permitted extraction route under its
   routing/quality policy.
2. Raw source/reference and raw extraction remain distinguishable.
3. Structure, reading order, coordinates and embedded assets are preserved where
   the source and engine permit.
4. Engine/model/provider, version, parameters, transformations, warnings and
   quality evidence are recorded.
5. A normalized representation or extraction bundle is produced with stable
   source coordinates appropriate to the contract.
6. The result is available for indexing or later transformations without
   replacing the original.

**Alternatives and failures.** Unsupported format, OCR failure, malformed source,
low structural fidelity, provider error or rights restriction yields an
explicit failure/degraded result rather than a fabricated complete extraction.

**Postconditions.** A traceable extraction or a traceable failure exists.

**Key invariants.** Original is not extraction; engine is replaceable; P0 does
not own catalog/view UX.

**Risk handoff.** Extraction fidelity, page/coordinate stability, OCR hidden
errors, cost/latency, provider drift, rights and benchmark representativeness.

### UC-12 — Translate a source without replacing the original

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Produce a translated derivative while preserving original content,
technical terminology policy and transformation provenance.

**Primary actor.** Person.

**Supporting systems.** P0 extraction if needed; replaceable translation
provider; optional glossary/translation-memory capability.

**Preconditions.** The source or reusable structured intermediate is available,
rights permit the requested processing, and source/target languages are known
or reviewable.

**Trigger.** The person chooses an extract+translate or translate recipe.

**Main success path.**

1. Raiatea reuses an existing valid extraction/intermediate when possible.
2. The person or recipe specifies target language and relevant terminology
   policy.
3. Translation preserves non-translatable structure such as code, citations,
   formulas and identifiers according to the recipe contract.
4. The translated representation is stored as a derivative, not as a silent
   replacement.
5. Provider/model/version/parameters, warnings and human corrections remain
   linked in transformation history.

**Alternatives and failures.** Unsupported language, context-window/segmentation
failure, terminology conflict or provider outage yields partial/degraded output
only if explicitly represented as such.

**Postconditions.** Original and translated derivative coexist with a traceable
relationship.

**Key invariants.** Original is not translation; provider is replaceable;
corrections do not rewrite historical lineage.

**Risk handoff.** Hallucinated translation, terminology inconsistency, code or
citation corruption, remote-provider privacy, partial translation presentation.

### UC-13 — Run a Processing Recipe, including multi-output DAGs

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Let the person request one or more derived outputs while computing each
valid intermediate only once when reuse is safe.

**Primary actor.** Person.

**Supporting systems.** P0 and replaceable translation/render/conversion
providers; execution plane remains unresolved.

**Preconditions.** The selected source and desired operations are supported or
can report unsupported stages explicitly.

**Trigger.** The person chooses or creates a Processing Recipe.

**Main success path.**

1. Raiatea validates requested stages, inputs, rights and provider capability.
2. It constructs an inspectable dependency DAG, including the trivial
   single-output case.
3. Existing intermediates are reused only when their source version, operation,
   parameters and validity match the request.
4. Shared extraction/translation stages execute once when reusable.
5. Output branches create one or more derivatives such as Markdown, EPUB, HTML
   or PDF.
6. Each derivative links to the exact intermediate and transformation chain
   that produced it.
7. The user can see per-stage state and final outputs without assuming all
   branches succeeded.

**Alternatives and failures.** One output branch may fail while another succeeds;
retry must not force unrelated valid stages to rerun unless invalidation rules
require it.

**Postconditions.** Successful derivatives and failures share one traceable
recipe/run lineage.

**Key invariants.** DAG reuse does not weaken provenance; one output failure does
not rewrite successful history.

**Risk handoff.** Cache invalidation, stale intermediates, partial-run semantics,
resource exhaustion, execution-plane coupling.

### UC-14 — Select and evaluate a visual fidelity objective

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Choose what “same layout” means for a translated or converted output
and see when the target could not be met.

**Primary actor.** Person.

**Supporting systems.** Replaceable render/layout reconstruction providers.

**Preconditions.** A structured source/intermediate and a target output format
exist.

**Trigger.** The person requests visual reconstruction or conversion.

**Main success path.**

1. The recipe requires or derives an explicit fidelity objective equivalent to
   `facsimile`, `layout-faithful` or `semantic-reflow`.
2. Raiatea explains the practical meaning and trade-offs of the selected goal.
3. Rendering attempts the selected objective without claiming impossible
   pixel-identical translation.
4. Deviations, overflow, missing fonts/assets, pagination changes or other
   quality warnings are recorded.
5. The output remains linked to source and transformation history.

**Alternatives and failures.** If the target cannot be met within acceptable
quality, the person may choose another fidelity mode, repair manually or keep
the result explicitly degraded.

**Postconditions.** The derivative has a declared fidelity goal and visible
quality limits.

**Key invariants.** “Identical” is never an unqualified guarantee; quality
failure is visible.

**Risk handoff.** False visual confidence, font/licensing issues, overflow,
complex tables/formulas, expensive manual repair.

### UC-15 — Inspect derivative lineage

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Reconstruct where a derivative came from and how it was produced.

**Primary actor.** Person.

**Preconditions.** A derivative or processed representation exists.

**Trigger.** The person opens provenance/lineage for the item.

**Main success path.**

1. Raiatea identifies the immediate input(s) and operation that produced the
   derivative.
2. The person can traverse backward through extraction, normalization,
   translation, conversion or other stages to the original/reference.
3. Relevant provider/model/engine versions, parameters, timestamps, warnings,
   rights and human corrections are inspectable where applicable.
4. Historical versions remain distinguishable from current preferred versions.

**Alternatives and failures.** Legacy/imported artifacts may have incomplete
lineage; gaps are explicit rather than filled with guesses.

**Postconditions.** The person can explain the provenance route or identify
where evidence is missing.

**Key invariants.** AI-generated interpretation is not primary evidence;
history is not silently overwritten.

**Risk handoff.** Provenance storage growth, incomplete imported history,
provider-version reproducibility, sensitive parameter leakage.

### UC-16 — Relate physical and digital representations

> Assertion status: `accepted-decision` for the outcome; implementation absent

**Goal.** Show that a physical copy, PDF, EPUB, translation or derivative are
related representations without treating them all as exact duplicates.

**Primary actor.** Person.

**Supporting systems.** Optional metadata resolvers.

**Preconditions.** Two or more holdings/representations exist and sufficient
identity evidence may be available.

**Trigger.** Raiatea proposes or the person creates/reviews a relationship.

**Main success path.**

1. Raiatea distinguishes exact byte duplicate, same edition/representation,
   different format, physical holding, translation, revision and derived output
   where evidence supports those concepts.
2. The person can inspect the evidence used for an automatic suggestion.
3. Ambiguous relationships remain candidate links until accepted or corrected.
4. Search/detail views present related representations together without
   collapsing their separate provenance or locations.

**Alternatives and failures.** Same title/different edition, scans with missing
metadata or unofficial derivatives remain ambiguous rather than force-merged.

**Postconditions.** Related items can be navigated as a family while preserving
separate identities/locations where required.

**Key invariants.** Related representation is not necessarily exact duplicate;
physical holding is not digital full text.

**Risk handoff.** Entity resolution, editions/translations, accidental data
collapse, reversible merge/split semantics.

### UC-17 — Provide a course-scoped source projection to TheBitLab

> Assertion status: `accepted-decision` for the target boundary;
> implementation absent

**Goal.** Let an educational course select and reference Raiatea sources without
creating a second universal library.

**Primary actor.** Course author/teacher.

**Supporting external system.** TheBitLab.

**Preconditions.** Raiatea has relevant source identities/provenance and the
consumer is authorized to see the requested projection.

**Trigger.** The course author asks TheBitLab to use a Raiatea-backed source
selection, or TheBitLab requests an already-defined projection.

**Main success path.**

1. The course defines selection/visibility requirements in its own domain.
2. Raiatea returns a bounded projection/reference containing the general source
   identity and provenance needed by the course contract.
3. TheBitLab owns course-specific labels, visibility, activities and assessment
   semantics.
4. Updates to Raiatea's general source location do not require a second
   independent canonical source record in TheBitLab.
5. Rights constraints remain enforceable across the projection.

**Alternatives and failures.** A source unavailable to the course, rights change
or missing projection field results in an explicit compatibility/availability
failure.

**Postconditions.** The course can reference approved material while Raiatea
remains the general source-of-truth owner.

**Key invariants.** Course projection is not universal catalog; educational
semantics remain TheBitLab-owned.

**Risk handoff.** Contract versioning, rights propagation, offline course
bundles, stale projections and source deletion.

### UC-18 — Recover after processing or organization failure

> Assertion status: `accepted-decision` for the safety outcome;
> implementation absent

**Goal.** Let the person return the system to a known, explainable state after a
partial or failed transformation or filesystem organization operation.

**Primary actor.** Person.

**Supporting systems.** Filesystem/storage, Alfred and processing providers as
applicable.

**Preconditions.** A consequential operation has started and enough intent/state
was recorded to distinguish completed, failed and unknown stages.

**Trigger.** Raiatea detects provider failure, process crash, partial batch
mutation, storage error, cancellation or a reconciliation mismatch and exposes
recovery to the person.

**Main success path.**

1. Raiatea stops unsafe dependent work when required.
2. It determines which stages/files definitely completed, definitely failed or
   remain uncertain.
3. Valid completed derivatives/operations remain recorded instead of being
   silently discarded.
4. Failed or uncertain states are visible with retry/recovery options.
5. For filesystem mutations, current locations are reconciled with observed
   reality before further automated moves.
6. Retrying reuses still-valid intermediates and does not duplicate successful
   work without a reason.
7. Recovery actions append history rather than rewriting the failed attempt.

**Alternatives and failures.** If automatic recovery cannot prove the current
state, the operation becomes a manual-review case rather than guessing.

**Postconditions.** The person can tell what happened, what remains valid and
what action is needed next.

**Key invariants.** Failure does not erase history; recovery is auditable;
unknown state is not promoted to success.

**Risk handoff.** Idempotency, crash consistency, rollback limits, external side
effects, stale caches/intermediates and user edits during recovery.

## 7. Use-case relationships

> Assertion status: `accepted-decision` for conceptual relationships; no API
> implication

The significant relationships are:

```text
UC-01 Inventory digital collection
  -> may request UC-11 Extract source
  -> enables UC-05 Search, UC-07 Views and UC-08 Smart Collections

UC-03 Preserve identity across move/rename
  -> supports UC-01 continuity
  -> is required for safe UC-10 Managed organization

UC-09 Preview organization policy
  -> precedes or informs UC-10 Apply managed organization
  -> UC-10 failure routes to UC-18 Recovery

UC-12 Translate source
  -> may depend on UC-11 Extraction
  -> may participate in UC-13 Processing Recipe
  -> may use UC-14 Visual fidelity
  -> all derivatives require UC-15 Lineage

UC-13 Processing Recipe
  -> reuses UC-11/UC-12 intermediates when valid
  -> may branch to multiple outputs
  -> failures route to UC-18 Recovery

UC-16 Relate physical/digital representations
  -> connects UC-02 physical holding with UC-01 digital inventory

UC-17 TheBitLab projection
  -> consumes catalog/provenance results
  -> does not own UC-01/UC-11 implementations
```

These relationships express user-flow dependencies. They are not UML
`include`/`extend` contracts and do not require one deployment topology.

## 8. First verifiable product slice coverage

> Assertion status: `working-hypothesis`

The Product Map candidate first slice can be tested with a deliberately narrow
subset:

| Candidate first-slice need | Use cases | Why included |
| --- | --- | --- |
| Discover a local PDF/EPUB collection | UC-01 | Proves useful inventory without auto-move |
| Keep identity stable if a test file moves/renames | UC-03 | Proves path-independent identity and Alfred seam |
| Extract PDF/EPUB through benchmark-selected route | UC-11 | Connects the already-planned P0 foundation |
| Find content and metadata | UC-05 | Produces immediate personal value |
| Show more than one logical organization | UC-07 | Proves views are independent from folders |
| Save one self-updating selection | UC-08 | Proves dynamic query state |
| Produce one traced derivative | UC-13 single-output subset + UC-15 | Proves recipe/lineage without requiring multi-output branching |

The first proof **does not require** automatic managed-file organization,
physical holdings, natural-language query interpretation, multi-output
branching, layout-faithful translation or TheBitLab integration. Those remain
accepted destination use cases but can be excluded from the first experiment to
reduce destructive and integration risk.

No row in this section promotes the candidate slice to `planned`. Promotion
requires the evidence gates described by #106 and the upcoming Risk List.

## 9. Actor/use-case matrix

| Use case | Person | Alfred | Filesystem/storage | Processing/metadata providers | TheBitLab |
| --- | --- | --- | --- | --- | --- |
| UC-01 Inventory digital collection | primary | supporting where available | supporting | optional | — |
| UC-02 Register physical holding | primary | — | — | optional metadata | — |
| UC-03 Preserve identity after move | primary | supporting | supporting | — | — |
| UC-04 Missing/deleted location | primary/reviewer | triggering/supporting | supporting | — | — |
| UC-05 Deterministic search | primary | — | — | implementation remains replaceable | — |
| UC-06 Natural-language search | primary | — | — | optional model interpreter | — |
| UC-07 Logical views | primary | — | — | — | — |
| UC-08 Smart Collection | primary | — | — | optional model only during query interpretation | — |
| UC-09 Organization preview | primary | — | supporting | optional classification provider | — |
| UC-10 Managed organization | primary/authorizer | observing | supporting | optional classification provider | — |
| UC-11 P0 extraction | primary | — | source access | parser/OCR/VLM | — |
| UC-12 Translation | primary | — | — | translation provider | — |
| UC-13 Processing Recipe | primary | — | output storage | extraction/translation/rendering | — |
| UC-14 Fidelity objective | primary | — | — | renderer/layout provider | — |
| UC-15 Inspect lineage | primary | — | — | provider metadata is evidence | possible later consumer |
| UC-16 Relate representations | primary/reviewer | — | — | optional metadata resolver | — |
| UC-17 Course projection | course author/teacher | — | — | — | supporting external consumer/system |
| UC-18 Recovery | primary/reviewer | supporting for filesystem truth | supporting | failed provider may participate | — |

Internal triggers such as a Processing Recipe reaching a stage or a recovery
condition becoming true are intentionally absent from the actor columns.

## 10. Inputs to the Risk List

> Assertion status: `accepted-decision` for handoff; risk severity/priorities are
> not decided here

The next Risk List must evaluate at least these clusters derived from the use
cases:

1. **Identity and reconciliation** — false duplicate merge, wrong move
   correlation, edition/representation conflation, reversible split/merge.
2. **Filesystem safety** — destructive moves, path traversal, symlinks,
   collision handling, partial batches, rollback and user/manual conflict.
3. **Observation reliability** — missed events, overflow, offline changes,
   removable/NAS ambiguity and cross-platform Alfred coverage.
4. **Extraction quality** — OCR/layout/formula/table errors, coordinate
   stability, parser disagreement and source-class benchmark coverage.
5. **Translation and rendering quality** — fluent but wrong translation,
   terminology drift, code/citation corruption, visual overflow and expensive
   manual repair.
6. **Transformation reproducibility** — provider/model/version drift,
   parameter capture, cache/intermediate invalidation and partial DAG failure.
7. **Rights and privacy** — private-corpus leakage, remote-provider exposure,
   retention/deletion propagation and course projection rights.
8. **Search/query integrity** — stale indexes, ambiguous natural-language plans,
   saved-query migration and semantic drift.
9. **Execution and recovery** — idempotency, crash consistency, cancellation,
   retries, resource exhaustion and unresolved Durex boundary.
10. **Product value** — first-slice complexity, time-to-inventory, search value,
    manual correction burden and whether a simpler toolchain is better.

## 11. Out of scope for this artifact

This Use Case Model does not:

- stabilize the final definitions of `Asset`, `Source`, `Work`, `Manifestation`,
  `Derivative` or `Fragment`;
- define database or index technology;
- define REST, event or adapter schemas;
- select Docling, OCR, VLM, translation or rendering providers;
- select or generalize Durex;
- define final desktop/web UI component trees;
- set quantitative benchmark thresholds;
- schedule P1-P7;
- promote the first product slice to `planned`.

## 12. Decisions passed forward

### Risk List

Use the risk clusters in section 10 and each use case's failure alternatives to
rank what could invalidate the product or make implementation unsafe.

### Glossary

Stabilize only the vocabulary needed to make the accepted boundaries precise,
especially the distinctions among logical identity, source, holding,
representation/manifestation, location, derivative, collection, view and
Processing Recipe.

### P0 #106

Use UC-11 and the dependent portions of UC-12/UC-13 to derive extraction
contract and benchmark scenarios. P0 should not absorb catalog, view,
organization or product-query ownership merely because those use cases consume
its output.

### Future implementation planning

Implementation epics should cite these use cases as user outcomes and then add
separate technical acceptance criteria. A use-case ID is not sufficient evidence
that a particular architecture, repository, database or framework has been
approved.
