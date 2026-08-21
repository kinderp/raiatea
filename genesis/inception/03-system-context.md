# Raiatea System Context

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 1.0.0
>
> Last reviewed: 21 August 2026
>
> Accepted through: [PR #112](https://github.com/kinderp/raiatea/pull/112)
>
> Parent issue: [#98](https://github.com/kinderp/raiatea/issues/98)
>
> Child issue: [#111](https://github.com/kinderp/raiatea/issues/111)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Primary canonical sources: [`00-why-raiatea.md`](00-why-raiatea.md),
> [`01-manifesto.md`](01-manifesto.md), [`02-vision.md`](02-vision.md),
> [`COMPASS.md`](../../COMPASS.md), and
> [`genesis/04`](../04-continuous-knowledge-ingestion.md)
>
> Ecosystem observation date: **21 August 2026**
>
> Pinned evidence snapshots:
> [Alfred `9e0e59e`](https://github.com/kinderp/alfred/tree/9e0e59e4232b8b173f1ae44a409c7d06f72f6c02),
> [Durex `5ae87b1`](https://github.com/kinderp/durex/tree/5ae87b11917b8d1bf5e15b1f418e856f42911d92), and
> [TheBitLab/2cornot2c `5472eef`](https://github.com/TheBitPoets/2cornot2c/tree/5472eef86568a4e7ce59ad34ba937220df27efd7)

## 1. Purpose

This document defines the system boundary that the next Raiatea work may rely
on. It does not define a database schema, deployment topology, parser, OCR
engine, vector store, graph store or network protocol.

Its job is narrower:

- identify the person Raiatea serves first;
- distinguish Raiatea from neighbouring projects and external tools;
- assign or defer ownership of cross-cutting responsibilities;
- define which information must remain stable across implementations;
- prevent the Universal Document & Asset Library from becoming a second,
  disconnected product architecture beside the rest of Raiatea.

The corresponding product surfaces and user-visible hierarchy are defined in
[`04-product-map.md`](04-product-map.md).

## 2. Accepted context decisions

> Assertion status: `accepted-decision`

The System Context inherits these decisions from the accepted Why, Manifesto,
Vision and maintainer review on 21 August 2026:

1. **Raiatea is the product and knowledge boundary, not a parser or an LLM.**
   Mature engines should be reused behind replaceable contracts when evidence
   supports them.
2. **P0 Source Ingestion & Extraction remains the first required platform
   foundation.** P1-P7 remain required destination capabilities, but their
   ordering and dependencies after P0 are provisional.
3. **The Universal Document & Asset Library is a fundamental document surface
   of Raiatea.** It is not a separate competing library or a new repository by
   default.
4. **Filesystem path is location, not identity.** Moving or renaming a digital
   file must not create a new logical source merely because its pathname
   changed.
5. **Physical and digital holdings belong in one navigable inventory.** A
   physical copy, PDF, EPUB, translation or derived Markdown may be related
   without being treated as byte-identical duplicates.
6. **Original evidence and transformations remain distinguishable.** Raw
   acquisition, extraction, normalization, translation, adaptation, derived
   artifacts and interpretation must not silently overwrite one another.
7. **Automation acts only inside explicit authority.** Search, classification
   and proposals may span observed material; destructive organization or
   mutation requires a declared managed scope and reversible policy.
8. **Products share one navigable memory.** Research, learning and future
   intelligence surfaces should consume shared source/provenance foundations
   rather than build independent libraries.

## 3. Primary actor

> Assertion status: `accepted-decision`

The first actor is a **self-directed technical learner or practitioner** who
owns or can lawfully access a heterogeneous body of material and wants to turn
it into an inspectable, durable route for study, research and later work.

For the first validation domain this person studies AI engineering and LLM
systems, but the document-management boundary must not encode AI-specific
assumptions.

The person must be able to:

- see what material is available and where it is located;
- find material by metadata, content and meaning;
- understand why a result or view contains a particular asset;
- change organization rules without losing identity or provenance;
- choose whether a document is merely indexed, extracted, translated,
  converted or transformed into several outputs;
- inspect and reverse consequential automated decisions;
- continue using durable artifacts when a model, provider or interface changes.

## 4. Context map

> Assertion status: `accepted-decision` for ownership boundaries already
> decided; `provisional-decision` where explicitly marked

```text
                                PERSON
                                  |
                    Browser / future desktop shell
                                  |
                                  v
+-----------------------------------------------------------------------+
|                               RAIATEA                                 |
|                                                                       |
|  Universal Document & Asset Library                                   |
|      |                                                                |
|      +-- Asset / Source Registry                                      |
|      +-- Search, Views & Smart Collections                            |
|      +-- Organization Policy                                          |
|      +-- Processing Recipes                                           |
|                                                                       |
|  P0 Source Ingestion & Extraction                                     |
|      +-- routing / adapters / quality / rights / extraction bundles   |
|                                                                       |
|  Provenance & Transformation lineage                                  |
|                                                                       |
|  Later shared knowledge capabilities                                  |
|      +-- Research & Learning Workspace                                |
|      +-- future intelligence products                                 |
+-----------------------------------------------------------------------+
        ^                         ^                         |
        |                         |                         v
        |                         |                   THEBITLAB
        |                         |                educational consumer
        |                         |
      ALFRED                    DUREX?
 filesystem observation       candidate execution reuse
        |
        v
 local / mounted / future platform filesystems

External replaceable adapters used by Raiatea P0 / Transformation:
PDF/EPUB/document parsers · OCR/VLM · translation providers · renderers ·
repositories/APIs/feeds · metadata services
```

The diagram shows responsibility, not process deployment. Components may run
in one process, several local services or future remote nodes without changing
this context boundary.

## 5. Raiatea-owned responsibilities

### 5.1 Asset and Source Registry

> Assertion status: `accepted-decision` for ownership; terminology remains
> `provisional-decision` until the Glossary

Raiatea owns the logical inventory that tells the system **what exists, what it
is related to and where representations can currently be found**.

The registry must eventually represent, without relying on pathname as
identity:

- stable logical identity;
- one or more locations;
- physical and digital manifestations or copies;
- exact duplicates and related representations;
- versions and revisions;
- original and derived artifacts;
- language, format, type and descriptive metadata;
- rights and retention constraints;
- provenance and transformation relationships;
- indexing and processing state.

The exact names `Asset`, `Source`, `Manifestation`, `Location`, `Derivative`
and `Work` remain candidate vocabulary. #111 may use them to explain the model,
but the future Glossary must stabilize their definitions before a public schema
is declared.

### 5.2 Discovery, Query and Views

> Assertion status: `accepted-decision`

Raiatea owns user-facing discovery across the catalog and extracted content.
The same asset may appear in multiple logical views without copying the
underlying file.

Queries may combine:

- exact metadata and structured filters;
- full-text retrieval;
- semantic retrieval when justified;
- relationships to project, course, topic or later knowledge entities;
- natural-language intent translated into an inspectable structured query.

An LLM may propose a query plan. The durable selection criteria and returned
asset identities must remain inspectable independently of the model response.

Saved queries may become **Smart Collections** whose membership changes when
new or updated assets satisfy the same criteria.

### 5.3 Organization Policy

> Assertion status: `accepted-decision`

Raiatea owns the decision about **where a managed digital representation should
be organized**, not the low-level observation of filesystem changes.

A product implementation must distinguish scopes equivalent to:

- `inbox`: content intentionally submitted for classification and possible
  placement;
- `managed`: Raiatea may rename/move according to explicit policy;
- `observed`: Raiatea may index and track but must not reorganize;
- `manual/frozen`: location is user-controlled even if metadata and content are
  searchable.

Names may change, but the authority distinction is required.

Organization decisions must be previewable or explainable, collision-safe and
reversible enough to recover from a bad classifier or policy. An asset move
changes location history; it does not change the asset's logical identity.

### 5.4 Source Ingestion & Extraction orchestration

> Assertion status: `planned`

P0 [#106](https://github.com/kinderp/raiatea/issues/106) is owned by Raiatea.
It must route heterogeneous sources through replaceable extractors, preserve
raw and normalized layers, expose quality/failure information and return
stable source coordinates and provenance.

P0 owns orchestration and contracts. It does **not** imply that Raiatea owns
or reimplements each parser, OCR engine, speech-to-text engine or visual model.

### 5.5 Processing Recipes and Transformation lineage

> Assertion status: `accepted-decision` for product capability;
> implementation is absent

The user must be able to choose a bounded processing intent for one asset or a
batch. Candidate recipes include:

- index/catalog only;
- extract text only;
- extract text plus structure/assets;
- extract and translate;
- translate and rebuild a visually faithful document;
- convert to another format without translation;
- produce several derived formats or representations in parallel;
- compose a custom recipe from supported stages.

Execution should be representable as a DAG so valid intermediate results can be
reused rather than recomputed for every output.

Layout goals must distinguish at least these semantics or equivalent terms:

- `facsimile`: maximize visual similarity to the source pages;
- `layout-faithful`: preserve design structure while permitting pagination or
  text flow to change;
- `semantic-reflow`: preserve semantic structure while allowing reflow for
  EPUB, HTML, accessibility or responsive reading.

A translated document cannot promise pixel identity when target-language text
has different geometry. The selected fidelity objective and any compromises
must remain visible.

### 5.6 Provenance, rights and transformation history

> Assertion status: `accepted-decision`

Raiatea owns the durable relationship between evidence and derivation. A
transformation record must eventually be able to identify:

- input identities and versions;
- output identities and versions;
- operation and declared intent;
- engine/model/provider and version;
- material parameters;
- timestamps;
- quality evidence, confidence and warnings where meaningful;
- rights/retention constraints;
- human corrections or approvals.

The source, extraction, translation and later AI interpretation remain separate
layers. AI output is not promoted to primary evidence merely because it is
stored by Raiatea.

## 6. Alfred boundary

> Assertion status: `accepted-decision`

At the ecosystem snapshot above,
[`kinderp/alfred`](https://github.com/kinderp/alfred/tree/9e0e59e4232b8b173f1ae44a409c7d06f72f6c02)
is the existing filesystem observation engine and is the explicit reuse path
for supported filesystem event semantics. Raiatea must not create a second
general-purpose watcher merely for this product.

Alfred owns, within its supported platform/backend scope:

- recursive observation and initial/discovery scanning capabilities;
- create, modify, close-write-ready and delete facts/events;
- move, rename and relocation correlation;
- watcher state, resynchronization and observation diagnostics;
- backend-specific normalization into Alfred's structured event model.

Relevant evidence in the pinned snapshot includes the
[README](https://github.com/kinderp/alfred/blob/9e0e59e4232b8b173f1ae44a409c7d06f72f6c02/README.md),
[scanner/resync roadmap](https://github.com/kinderp/alfred/blob/9e0e59e4232b8b173f1ae44a409c7d06f72f6c02/docs/it/21-roadmap-scanner-resync.md),
and
[backend-plugin roadmap](https://github.com/kinderp/alfred/blob/9e0e59e4232b8b173f1ae44a409c7d06f72f6c02/docs/it/23-roadmap-plugin-backend.md).

Raiatea owns the reaction to those observations:

```text
Alfred observation
    -> Raiatea adapter
    -> resolve asset/location identity
    -> decide reindex / version / missing state
    -> evaluate organization policy when authorized
    -> update views and downstream knowledge projections
```

A filesystem event does not authorize Raiatea to move a file. Observation and
organization policy are separate responsibilities.

### 6.1 Platform gap

> Assertion status: `working-hypothesis`

In the pinned snapshot Alfred's implemented/reference backend is Linux-focused,
while its roadmap describes future additional backends. Raiatea's product may
later need macOS and Windows; #111 therefore treats cross-platform observation
as an Alfred capability gap or adapter question, not as permission to fork the
watcher logic inside Raiatea.

A temporary platform fallback is acceptable only if it is explicitly scoped,
replaceable and does not become a second competing event model.

## 7. Durex boundary

> Assertion status: `provisional-decision`

At the ecosystem snapshot above,
[`kinderp/durex`](https://github.com/kinderp/durex/tree/5ae87b11917b8d1bf5e15b1f418e856f42911d92)
contains useful execution patterns: persistent queueing, run lifecycle, worker
ownership, retry/resume, cancellation, bounded live output and typed runtime
events. See the pinned
[README](https://github.com/kinderp/durex/blob/5ae87b11917b8d1bf5e15b1f418e856f42911d92/README.md)
and
[`runtime_contracts.py`](https://github.com/kinderp/durex/blob/5ae87b11917b8d1bf5e15b1f418e856f42911d92/runtime_contracts.py).

Durex is nevertheless currently a coding-agent orchestration product. Raiatea
must not depend directly on its current database, Codex-specific lifecycle or
internal modules merely because the abstractions look similar.

Before document pipelines reuse Durex, a separate audit must decide among:

1. extract/generalize a reusable Job/Run core;
2. expose a stable Durex execution contract that document jobs can consume;
3. reuse only design patterns and keep document execution ownership in Raiatea.

Until that decision, the Product Map may show a **candidate execution plane**,
not a current dependency.

## 8. TheBitLab boundary

> Assertion status: `accepted-decision`

At the ecosystem snapshot above,
[`TheBitPoets/2cornot2c`](https://github.com/TheBitPoets/2cornot2c/tree/5472eef86568a4e7ce59ad34ba937220df27efd7)
contains an existing provider-independent course source catalog and accepted
Content Pack source contracts. Relevant evidence includes
[`course_source_catalog.py`](https://github.com/TheBitPoets/2cornot2c/blob/5472eef86568a4e7ce59ad34ba937220df27efd7/scripts/course_source_catalog.py)
and the
[Content Pack v1 standard](https://github.com/TheBitPoets/2cornot2c/blob/5472eef86568a4e7ce59ad34ba937220df27efd7/doc/architecture/content-pack-standard-v1.md).

TheBitLab remains an educational consumer, not the owner of Raiatea's general
document library. Those existing source contracts are useful migration and
compatibility evidence. The target direction is:

```text
Raiatea Asset / Source catalog
        |
        +-- query / projection for one course
        v
TheBitLab CourseSource selection
        |
        v
content, activities, course runtime and assessment
```

TheBitLab continues to own course-specific selection, visibility, educational
content and assessment semantics. Raiatea owns the general source identity,
location, extraction and provenance foundation. The two systems must not
maintain divergent canonical copies of the same general source metadata.

## 9. Other neighbouring projects

### DNA

> Assertion status: `accepted-decision`

DNA does not own document management. It may consume shared contracts or
Raiatea-derived assets where a real use case appears. Its relationship to
Alfred is context only; no DNA runtime dependency is introduced here.

### Iberna Workspace

> Assertion status: `deferred-research`

Iberna remains relevant to future multi-machine workspace movement and resource
placement, but it is outside the first document-management and P0 boundary.
Asset identity must not depend on Iberna being present.

## 10. Replaceable external systems

> Assertion status: `accepted-decision`

The following are adapter/provider families, not permanent Raiatea core
implementations:

- PDF, EPUB, office-document and scholarly parsers;
- OCR engines and multimodal/VLM extractors;
- translation engines and general-purpose LLM providers;
- PDF/EPUB/HTML/DOCX/Markdown renderers and converters;
- metadata services such as ISBN/DOI or equivalent resolvers;
- Git repositories, APIs, feeds and authorised remote source providers;
- local, mounted, removable, NAS or future remote storage locations.

The P0 survey and benchmarks decide which engines are used for particular
source classes. Docling, Tesseract, PaddleOCR, VLMs or any other named tool are
candidates until that evidence is recorded.

## 11. Information and control flows

### 11.1 Existing digital file enters an observed scope

```text
filesystem
  -> Alfred observes create/ready/move/change
  -> Raiatea resolves location and fingerprint
  -> Asset Registry associates or creates logical identity
  -> metadata/content processing according to configured policy
  -> search indexes and Smart Collections update
  -> no physical move unless the scope is explicitly managed
```

### 11.2 User changes organization policy

```text
user intent
  -> structured policy
  -> preview / affected assets
  -> approved organization operation
  -> filesystem move/rename
  -> Alfred observes resulting facts
  -> Raiatea reconciles location history
```

The system must avoid treating its own expected move event as an unrelated new
asset.

### 11.3 User requests a document transformation

```text
selected assets + recipe
  -> rights / capability / input checks
  -> reusable pipeline DAG
  -> extraction or existing intermediate
  -> optional translation / conversion / layout reconstruction
  -> one or more derived assets
  -> transformation provenance
  -> catalog/search/view update
```

### 11.4 Physical book enters the catalog

```text
user / metadata capture
  -> logical holding and physical location
  -> optional ISBN/metadata enrichment
  -> optional later scan or digital manifestation
  -> relationship to the same work/asset family when evidence is sufficient
```

A physical holding does not imply that its full text is available for search.

## 12. Trust and safety boundaries

> Assertion status: `accepted-decision`

The document workspace manipulates valuable user files, so the following
constraints are architectural, not optional UI details:

- originals are not silently overwritten by transformations;
- managed/observed authority is explicit per location or collection;
- automatic moves have collision handling and recoverable history;
- ingestion respects rights, access and retention policies;
- model output is not trusted as source identity without validation;
- prompts or extracted content cannot silently grant filesystem authority;
- external tools receive only the data required for their declared operation;
- destructive or externally visible actions remain reviewable and auditable;
- missing files and deleted sources do not silently erase historical
  provenance or derived knowledge.

## 13. Current, planned and unresolved boundaries

| Boundary | Status after #110 | Owner / next decision |
| --- | --- | --- |
| Canonical source/document identity independent of path | `accepted-decision` | Raiatea |
| Universal Document & Asset Library product surface | `accepted-decision` | Raiatea / #111 |
| P0 ingestion and extraction orchestration | `planned` | Raiatea / #106 |
| Filesystem observation on supported Alfred platforms | `accepted-decision` reuse | Alfred |
| Cross-platform Alfred coverage | `working-hypothesis` / gap | Alfred roadmap + integration evidence |
| Search, views, Smart Collections | `accepted-decision` capability; absent | Raiatea |
| Managed organization policy | `accepted-decision` capability; absent | Raiatea |
| Processing Recipes and transformation lineage | `accepted-decision` capability; absent | Raiatea |
| Exact Open Content IR/schema | unresolved | P0 contract work after survey |
| Job/Run execution reuse from Durex | `provisional-decision` | audit before implementation |
| Course-specific source projection | `accepted-decision` target | TheBitLab consumes Raiatea |
| Web UI as primary workspace | `accepted-decision` direction from #111 input; absent | Product Map / later implementation |
| Tauri desktop shell | `working-hypothesis` | evaluate after web UI contract |
| Database/vector/graph technology | unresolved | later architecture/benchmark |
| Multi-host workspace / Iberna integration | `deferred-research` | future roadmap |

## 14. Out of scope for this artifact

This System Context does not:

- define the detailed `Asset`, `Source`, `Fragment` or `Transformation` schema;
- select storage engines or search infrastructure;
- choose P0 parsers/OCR/VLMs;
- generalize Durex;
- implement Alfred adapters;
- define the final UI component hierarchy;
- define the complete temporal knowledge graph;
- create new repositories for internal packages;
- settle P1-P7 ordering after P0.

## 15. Decisions handed to the Product Map

[`04-product-map.md`](04-product-map.md) must use this context to make visible:

1. which user-visible surfaces form the Universal Document & Asset Library;
2. which capabilities are shared foundations rather than separate products;
3. how Research & Learning Workspace and AI Research Notebook consume the
   document foundation;
4. which features belong to the first verifiable slice and which remain later;
5. how dynamic views, organization policy and Processing Recipes remain
   distinct user capabilities;
6. where Alfred reuse is mandatory and Durex reuse remains conditional.
