# Raiatea GUI Application Boundary — first executable product slice

Status: **Draft / architecture planning**

Issue: #211

## Purpose

Define the first stable boundary between a future Raiatea GUI and the currently accepted VS1/PDF product capabilities without exposing prototype storage shapes, Plugin API records or future Source Plane deployment details directly to the frontend.

The GUI consumes Raiatea-owned application read models. It does not query `CatalogStateStore`, E-05 records, SourcePlugin records or Source Plane worker/provider schemas directly.

## Architectural boundary

```text
Raiatea GUI
    |
    v
Raiatea Application Layer
    |
    +-- Library / Catalog read service
    +-- Search / View / Smart Collection service
    +-- Source Detail composition service
    +-- Activity / Freshness service
    +-- Processing / Source Plane gateway
    |
    +-- current Raiatea catalog authority
    +-- current deterministic search authority
    +-- current extraction/provenance authority
```

After the Source Plane product split, the same GUI boundary remains:

```text
GUI -> Raiatea Application Layer -> Raiatea Catalog/Knowledge
                              \-> Source Plane client
```

The GUI must not change because an extraction route moves from a local child process to a Source Plane daemon or a replicated worker pool.

## Invariants

1. Prototype/internal records are not frontend contracts.
2. A `SourceReference` remains path-free; first-party display Location comes from Raiatea catalog authority, never from a Provider or plugin record.
3. The initial Location projection is the authorized-scope relative Location. Absolute host roots/paths are not a general frontend contract.
4. Search freshness is explicit. A stale index cannot be rendered as current search truth.
5. Smart Collection rule is authority; current membership is derived state.
6. ProviderEvidence and NormalizedRepresentation remain distinguishable in Source Detail.
7. Missing/partial/unknown evidence stays visible as such; the GUI must not manufacture completeness.
8. Read models are paginable and must not inherit VS1 internal collection limits as product UX limits.
9. UI layout/docking state is local presentation state and never mutates Raiatea knowledge authority.
10. The frontend requests capabilities and application actions, not concrete parser/provider behavior.
11. Current `logical_candidate_ref` remains explicitly provisional; the Application Layer must not relabel it as a finalized universal Logical Identity.

## First read models

### `HomeSummary`

Purpose: safe orientation over real current capabilities.

```text
HomeSummary
  catalog_freshness
  counts_basis                 # current / last-known / unavailable
  source_counts_by_media_type[]
  current_source_count?
  available_source_count?
  missing_or_unknown_count?
  processing_summary
  warning_summary
  recent_activity[]
  saved_view_count
  smart_collection_count
  backup_status?
```

Counts must be qualified by catalog freshness. A stale/reconcile-required catalog cannot be summarized as if the counts were guaranteed current.

No Observatory/Horizon/public-world metrics belong in this first read model.

### `LibraryItem`

The first reusable row/card model for Library, search results and collection membership.

```text
LibraryItem
  item_ref                    # application navigation ref; no final ontology claim
  catalog_entry_ref
  source_ref_id?              # processing/evidence ref; not primary display identity
  logical_candidate_ref       # current revisable catalog candidate
  stored_instance_ref
  display
    title?
    fallback_name
    media_type
    kind
  location
    scope_ref
    current_relative_location?
    availability
    history_count
  content
    byte_length?
    fingerprint_summary?
  extraction
    state
    current_representation_id?
    provider_profile_summary?
  freshness
    catalog
    content
  warnings
    count
    highest_severity?
  capabilities[]
```

`item_ref` exists for application navigation and must not silently become a universal Work/Manifestation/Logical Identity ontology. Its exact durable basis is a later contract decision.

`current_relative_location` is a Raiatea catalog projection inside an authorized scope. It must never be sourced from `SourceReference` or ProviderEvidence. A future local-only action such as `Reveal in filesystem` may resolve a host path through a Core-owned command without making that path part of the generic read contract.

`title` is optional until Raiatea has attributable title metadata. The UI uses `fallback_name` rather than pretending a filename-derived value is authoritative bibliographic metadata.

### `SourceDetail`

Composition root for the first important GUI screen.

```text
SourceDetail
  item_ref
  catalog_entry_ref
  logical_candidate_ref
  stored_instance_ref
  source_ref_id?
  display
  locations[]
  availability
  media_type
  content_identity
  catalog_freshness
  current_extractions[]
  representations[]
  evidence_summaries[]
  processing_runs[]
  provenance_summary
  rights_summary
  warnings[]
  available_panels[]
  available_actions[]
```

The model is capability-driven. PDF and EPUB do not require separate page implementations.

Example panels:

```text
original
semantic
provider-evidence
relations
processing
provenance
history
```

A panel is exposed only when its required evidence/capability exists.

### `RepresentationDetail`

```text
RepresentationDetail
  representation_id
  representation_kind
  source_ref_id
  route_profile
  provider
  coordinate_family
  evidence_state_by_family
  warnings[]
  provenance_ref
  content_page
    cursor?
    next_cursor?
    units[]
```

Content units are paged/streamed at the application boundary. The GUI must not receive an unbounded entire extracted book merely because a current prototype stores one representation object.

### `ProcessingStatus`

```text
ProcessingStatus
  item_ref
  source_ref_id?
  current_state
  attempts[]
    run_id
    route_profile
    provider
    execution_state
    result_state
    started_at?
    completed_at?
    warnings[]
  current_representation_refs[]
```

Runtime completion and accepted extraction outcome remain separate concepts.

### `ProvenanceView`

Human-readable drill-down rather than a raw E-05 dump.

```text
ProvenanceView
  subject_ref
  lineage_nodes[]
  lineage_edges[]
  providers[]
  route_profiles[]
  transformations[]
  evidence_refs[]
  source_coordinates[]
  diagnostics[]
```

Every node may retain an advanced/raw-record reference for technical inspection, but raw records are not the default GUI model.

### `SearchRequest`

The first GUI search remains deterministic and inspectable.

```text
SearchRequest
  criteria[]
    field
    operator
    value
  sort
    field
    direction
  page_size
  cursor?
```

Initial application-level filters map to accepted VS1 semantics where supported:

- media type;
- extracted text contains;
- semantic type;
- source resource/anchor family where applicable;
- provider;
- route profile.

The application layer may expose user-friendly names while compiling to the accepted internal QueryPlan. `source_ref_id` remains available for diagnostics/navigation but is not a primary end-user filter.

Natural-language search is a later compiler into an inspectable structured plan; it does not replace this boundary.

### `SearchResultPage`

```text
SearchResultPage
  freshness
  blocked_reason?
  interpreted_plan
  total_known_matches?
  cursor?
  next_cursor?
  items[]
    LibraryItem
    matched_content_refs[]
    match_snippets[]
```

Critical rule: when the accepted search basis is stale, the application layer returns no current hits and surfaces the stale reason, preserving VS1 semantics.

### `SavedView`

```text
SavedView
  view_id
  label?                     # application-owned user metadata when introduced
  request_plan
  projection
  result_summary
  capabilities[]
```

A View remains query + projection. It does not own a separate member list.

The current VS1 View contract does not define a user-facing display name. A persisted `label` therefore requires an explicit Raiatea application-metadata addition; the GUI must not pretend it already exists in the accepted View record.

### `SmartCollectionView`

```text
SmartCollectionView
  collection_id
  label?                     # application-owned user metadata when introduced
  rule
  evaluation_freshness
  evaluated_basis
  evaluated_revision
  member_count
  member_preview[]
```

The rule is authoritative. Membership is derived and must not be hand-edited through this surface.

As with Views, a friendly persisted label is new application metadata unless/until separately accepted.

### `ActivityItem`

Application-level timeline event that may summarize catalog observation, reconciliation, extraction, warning, backup/restore and later Source Plane activity.

```text
ActivityItem
  activity_id
  category
  occurred_at?
  subject_ref?
  title
  summary
  severity
  state
  provenance_refs[]
  available_actions[]
```

Do not expose raw Alfred/plugin stderr as the main activity model. Technical diagnostics remain drill-down evidence.

### `InspectorModel`

The Inspector is schema-driven and object-sensitive.

```text
InspectorModel
  subject_ref
  subject_kind
  sections[]
    section_id
    title
    fields[]
    relations[]
    evidence_refs[]
  available_actions[]
```

The Inspector is the common drill-down surface from visible object to catalog candidate, Source, representation, evidence, processing and provenance.

## First command boundary

The initial GUI keeps writes small and explicit.

Candidate commands:

```text
SaveView
DeleteView
SaveSmartCollection
DeleteSmartCollection
RequestReconciliation
RequestExtraction / Reprocess
CreateBackup
RestoreBackup   # guarded workflow, not a one-click blind mutation
RevealInFilesystem?  # local-only capability; host path stays out of generic read models
```

Commands invoke application services that enforce Core authority. The GUI cannot widen filesystem scope, manufacture Processing Rights or pass Provider-specific command-line options directly.

## Pagination and scale boundary

VS1 internal contracts intentionally bound discovery/search collections to a small proof. Those limits are not product API limits.

The Application Layer must define paging/cursor semantics before a real Library UI is considered scalable. The GUI therefore never assumes:

```text
all Sources fit in one response
all content units fit in one response
all Activity fits in memory
```

This also prepares Raiatea for future Source Plane and remote/federated data without changing panel contracts.

## Panel composition boundary

```text
WorkspaceShell
  -> DockLayout
      -> PanelHost
          -> Panel
```

Panels consume read models or focused subqueries, not shared mutable backend objects.

Candidate descriptor:

```text
PanelDescriptor
  panel_id
  title
  subject_ref?
  data_capability
  resizable = true
  movable = false       # first implementation
  dockable = false      # first implementation
  tabbable = false      # first implementation
  closable
  future
    movable = true
    dockable = true
    tabbable = true
    floatable = optional
```

The first static layout therefore remains compatible with later drag/drop docking without making docking a prerequisite for the first usable GUI.

## First executable GUI vertical slice

```text
Home
  -> Library page
      -> deterministic Search
          -> Source Detail
              -> Original / Semantic / Evidence / Processing / Provenance
      -> Saved Views
      -> Smart Collections
  -> Activity / Freshness
```

Acceptance uses real authorized EPUB/PDF product data and never requires fabricated Observatory or future knowledge objects.

## Current-contract mapping

The first facade maps existing accepted/current behavior rather than replacing it:

| GUI/application concept | Current source of truth |
| --- | --- |
| catalog freshness / availability / relative Location history | Raiatea reconciliation/catalog state |
| path-free processable Source identity | SourceReference contract |
| current revisable logical candidate | Raiatea reconciliation/catalog state |
| deterministic filter semantics | VS1e QueryPlan/search contract |
| View rule/projection | VS1e View contract |
| Smart rule + evaluated members/basis | VS1e Smart Collection contract |
| Provider/run/current representation | E-05 extraction records + product publication fences |
| PDF provider-specific evidence | independent Poppler/Docling evidence routes when promoted |
| future extraction runtime location | hidden behind Source Plane gateway |

The facade is intentionally allowed to compose these truths into one `SourceDetail`; none of the underlying records becomes the public GUI schema merely because it contributes data.

## Explicitly deferred

- final durable basis/versioning for `item_ref`;
- user-label persistence for Views/Smart Collections;
- frontend technology/framework selection;
- REST vs GraphQL vs local IPC protocol;
- drag/drop docking implementation;
- natural-language search;
- embeddings/vector search;
- Actor/Idea/Topic Explore implementation;
- Observatory/Horizon/Agora;
- Source Plane Worker Dashboard;
- public multi-user authentication/authorization UX;
- remote/federated Library UX.

## Next evidence step

Before selecting a UI framework, prototype the Raiatea Application Layer as a thin read/command facade over existing VS1/PDF services and test these invariants:

1. no prototype store object leaks into the read models;
2. no Provider can supply/display catalog Location authority;
3. absolute host path/root is not part of the generic frontend read contract;
4. current logical candidates are not upgraded into a final ontology by naming;
5. stale search remains visibly blocked;
6. Smart rule/member authority remains distinct;
7. PDF/EPUB use one Source Detail composition path;
8. content and Library listing are paginable;
9. Source Plane extraction can later replace current in-repo extraction behind the same application contract.
