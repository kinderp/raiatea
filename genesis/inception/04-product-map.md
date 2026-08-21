# Raiatea Product Map

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
> Child issue: [#111](https://github.com/kinderp/raiatea/issues/111)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Primary canonical sources: [`00-why-raiatea.md`](00-why-raiatea.md),
> [`01-manifesto.md`](01-manifesto.md), [`02-vision.md`](02-vision.md), and
> [`03-system-context.md`](03-system-context.md)

## 1. Purpose

This Product Map separates **user-visible products and experiences** from the
**shared capabilities** that make them possible. Its purpose is to prevent
three recurring architecture mistakes:

1. treating every reusable capability as a separate product or repository;
2. letting one consumer such as a learning environment create its own source
   library, provenance model or filesystem watcher;
3. presenting the long-term Raiatea destination as if every capability were
   already planned for simultaneous implementation.

The Product Map is intentionally technology-agnostic. It does not choose the
P0 extraction engine, database, vector store, graph database, desktop shell or
job runner.

## 2. Product hierarchy

> Assertion status: `accepted-decision`

The product hierarchy accepted by the maintainer on 21 August 2026 is:

```text
RAIATEA
│
├── Universal Document & Asset Library
│     ├── Inventory / Catalog
│     ├── Search & Discovery
│     ├── Dynamic Views & Smart Collections
│     ├── Organization
│     └── Transformations / Processing Recipes
│
├── Research & Learning Workspace
│     └── AI Research Notebook
│          first AI-engineering experience / vertical
│
├── Future knowledge and intelligence products
│     ├── Field Intelligence Maps / Reality Observatory
│     ├── identity / claim / change experiences
│     ├── forecasting / calibration experiences
│     └── future federated experiences
│
└── External consumers
      └── TheBitLab / Learning Lab
           consumes Raiatea source/provenance projections
```

This hierarchy does not mean that all products exist today. The current
implementation remains the pedagogical vertical described in
[`02-vision.md`](02-vision.md). The Universal Document & Asset Library is an
accepted product surface but is not yet an implemented application.

## 3. Shared capability foundations

> Assertion status: `mixed`

The following capabilities are shared foundations. A product may expose them
through its own UX, but should not create a competing canonical implementation.

| Shared capability | Status | Primary owner | Consumers |
| --- | --- | --- | --- |
| Logical Asset / Source Registry | accepted product requirement; absent | Raiatea | Document Library, Research & Learning, future products, TheBitLab projection |
| Filesystem observation | existing reusable capability on supported platforms | Alfred | Raiatea and other ecosystem projects |
| P0 Source Ingestion & Extraction | `planned` in #106 | Raiatea orchestration + replaceable adapters | All source-aware products |
| Provenance / transformation lineage | accepted requirement; partial provenance exists in pedagogical vertical | Raiatea | All products |
| Search and logical views | accepted requirement; general implementation absent | Raiatea | Document Library and later workspaces |
| Organization policy | accepted requirement; absent | Raiatea | Document Library |
| Processing Recipes / transformation DAG | accepted requirement; absent | Raiatea | Document Library and later publishing workflows |
| General Job/Run execution plane | unresolved reuse decision | Durex candidate or Raiatea | long-running extraction/transformation jobs |
| Temporal canonical knowledge core | accepted destination; no implementation issue | Raiatea | Research/Learning and future intelligence products |
| Course-specific source projection | accepted target | TheBitLab | courses and learning activities |

The table distinguishes ownership from implementation location. A future
package may be extracted from Raiatea only after its contract is sufficiently
stable and independently reusable; a speculative package is not a reason to
create a repository now.

## 4. Universal Document & Asset Library

> Assertion status: `accepted-decision` for the product surface;
> implementation remains absent

The Universal Document & Asset Library is the first Raiatea surface dedicated
to the material the person already owns, can lawfully access or deliberately
adds.

Its product question is:

> **What material do I have, where is it, what is it about, how is it related,
> and what do I want Raiatea to do with it?**

It is broader than a book catalog and narrower than the entire Raiatea
knowledge system.

### 4.1 Inventory and Catalog

The inventory must eventually make visible:

- physical books and other physical holdings;
- PDF, EPUB, DOCX, Markdown, HTML, images and other supported digital assets;
- current filesystem/storage locations;
- related copies or manifestations;
- exact duplicates and candidate near-duplicates;
- versions and revisions;
- original and derived representations;
- language, format, type, author/publisher and other metadata when known;
- indexing, extraction, translation and transformation state;
- rights, retention and provenance information.

The canonical item must survive a file rename or move. Folder structure is a
projection of organization, not the identity model.

### 4.2 Search and Discovery

The user must be able to find material through combinations of:

- exact metadata;
- format and file characteristics;
- physical or digital location;
- language;
- date and version;
- full-text content;
- topic and semantic similarity;
- project/course relationships;
- processing status;
- later knowledge relationships when available.

Natural-language search is an additional interface over these capabilities,
not an opaque replacement for them. A prompt such as:

> show English books and papers about RAG published after 2023 that do not yet
> have an Italian translation

should become an inspectable query plan whose structured criteria can be edited
and saved.

### 4.3 Dynamic Views and Smart Collections

> Assertion status: `accepted-decision`

Views are a first-class product feature rather than a cosmetic presentation
option. They allow the same source inventory to be navigated through different
mental models without moving or duplicating files.

Candidate view families include:

- physical/folder location;
- table/list;
- cover/card grid;
- type and format;
- author or publisher;
- language;
- topic/domain;
- project;
- course;
- year/timeline;
- processing state;
- translation state;
- recently added or changed;
- duplicate/related representation review;
- later graph/relationship views.

A **Smart Collection** is a saved query or selection rule. Its membership
updates automatically when the catalog changes. A normal/manual collection may
also exist when the user wants explicit membership rather than a query.

Views never become a second source of truth. They project catalog identities
and relationships.

### 4.4 Organization

> Assertion status: `accepted-decision`

Organization answers a different question from search:

> **Where should the managed digital file live?**

The product must preserve a distinction equivalent to:

- inbox;
- managed;
- observed;
- manual/frozen.

Only managed authority permits automatic filesystem reorganization. The user
should be able to define or edit policies based on metadata, content,
classification and other safe criteria.

Example policy intents include:

```text
book + AI + LLM
  -> Books/Computer Science/Artificial Intelligence/LLM/{author}/{title}/

paper + RAG
  -> Papers/AI/RAG/{year}/

school document + TPSI + school year
  -> Teaching/{school_year}/TPSI/{class}/
```

The concrete rule language remains future work. Organization operations must
be explainable, collision-safe and recoverable. Raiatea should not repeatedly
fight a user's manual decisions when a scope is observed or frozen.

### 4.5 Transformations and Processing Recipes

> Assertion status: `accepted-decision`

A selected asset or batch should expose a product action equivalent to:

> **What do you want to produce from this material?**

Candidate processing intents include:

```text
Catalog / index only
Extract text
Extract text + document structure
Extract + translate
Translate + rebuild document
Convert format
Create multiple outputs
Custom recipe
```

Recipes should be composable and inspectable. The user should be able to save
common recipes such as:

```text
Technical Book — Personal Italian Edition
  extract structure
  -> translate EN→IT with glossary
  -> create Markdown IT
  -> create EPUB IT
  -> create layout-faithful PDF IT
  -> index resulting derivatives
```

or:

```text
Research Paper
  extract scholarly structure
  -> Markdown
  -> citations / references
  -> index
  -> later knowledge projection
```

A multi-output recipe is a DAG, not several unrelated conversions. One valid
extraction or translation intermediate should be reusable by dependent outputs.

### 4.6 Visual fidelity choices

> Assertion status: `accepted-decision`

The transformation UX must not offer a vague promise of an "identical"
translated document without explaining the target.

The product must distinguish at least:

| Goal | Intended result |
| --- | --- |
| Facsimile | Preserve page geometry and visual appearance as closely as practical, adapting translated text within explicit tolerances |
| Layout-faithful | Preserve typography hierarchy, figures, tables, columns and visual structure while allowing pagination/flow to change |
| Semantic reflow | Preserve semantic hierarchy and assets while allowing responsive/reflowable output such as EPUB or HTML |

The quality profile must expose where the selected fidelity target could not be
met.

### 4.7 Document detail surface

> Assertion status: `working-hypothesis`

A useful asset-detail page should eventually bring together:

- title and descriptive metadata;
- physical holdings and digital locations;
- representations and derivatives;
- original/extracted/translated content where rights allow;
- related assets;
- topics and later knowledge links;
- provenance and transformation history;
- processing status and warnings;
- actions such as open, transform, organize and ask/query against the source.

This is a UX hypothesis, not a committed screen layout.

### 4.8 Job Center

> Assertion status: `working-hypothesis`

OCR, translation, layout reconstruction and batch conversion may be long-running
and need an observable execution surface. A Job Center should eventually show:

- stage and progress where measurable;
- pending/running/completed/failed/cancelled state;
- retry and cancellation;
- warnings and logs;
- produced artifacts;
- resource/provider/cost observations when available;
- provenance from recipe to outputs.

The product requires the behavior; whether its execution plane is a generalized
Durex Job/Run core or a Raiatea-owned service remains unresolved.

## 5. Research & Learning Workspace

> Assertion status: `accepted-decision` as product surface;
> long-term capability remains largely absent

The Research & Learning Workspace asks a different question:

> **How do I turn selected sources into an evolving route for understanding,
> research, practice and verification?**

It consumes the common Asset/Source Registry, extraction and provenance
foundation. It must not maintain an independent canonical library.

Future workspace capabilities may include:

- source selection for an objective;
- prerequisite and concept maps;
- reading/research routes;
- bilingual living material;
- pedagogical explanations and semantic visuals;
- exercises, experiments and remediation;
- research notes and open questions;
- change-aware updates to an existing route.

The current pedagogical prototype is evidence for part of this product, not the
complete workspace.

## 6. AI Research Notebook

> Assertion status: `working-hypothesis` for public naming;
> `accepted-decision` for its role as an experience/vertical

AI Research Notebook is the candidate first AI-engineering experience inside
the Research & Learning Workspace.

It may curate and connect:

- owned/licensed AI books;
- papers and preprints;
- official documentation;
- code and repositories;
- experiments and notebooks;
- concepts and glossary terms;
- reading/practice routes;
- exercises and research questions.

The experience should consume the Universal Document & Asset Library rather
than build a separate AI-only corpus manager.

## 7. TheBitLab / Learning Lab as an external consumer

> Assertion status: `accepted-decision`

TheBitLab is not another Raiatea product surface inside the same runtime. It is
an educational consumer that can request a course-scoped projection of Raiatea
sources and provenance.

TheBitLab continues to own:

- course design;
- Content Pack and Activity contracts;
- student/teacher visibility;
- assignment and assessment semantics;
- sandbox/runtime interaction for educational tasks.

Raiatea owns the general source/document identity, locations, extraction,
transformations and provenance. Existing TheBitLab `CourseSourceCatalog`
behavior is compatibility and migration evidence, not a reason to duplicate
the universal catalog.

## 8. Future product families

> Assertion status: `accepted-decision` for inclusion in the destination;
> implementation order after P0 remains `provisional-decision`

The accepted Vision includes capability families that may support future
product surfaces such as:

- identity, claim, position and change timelines;
- field intelligence maps and reality observatory views;
- forecasting and calibration workspaces;
- federated/shared knowledge experiences.

This Product Map does not schedule them. P1-P7 ordering remains provisional and
must be refined by risk, dependencies and validated user value.

## 9. Product/capability ownership matrix

| User-visible need | Product surface | Shared capability owner | Reuse / external dependency |
| --- | --- | --- | --- |
| Know what I own/have access to | Document & Asset Library | Raiatea Asset/Source Registry | metadata adapters |
| Know where a file is | Document & Asset Library | Raiatea registry consumes filesystem observations | Alfred |
| Keep filesystem state updated | invisible supporting capability | Alfred | OS/backend events |
| Search by metadata/content/topic | Document & Asset Library | Raiatea discovery/query | search/embedding engines remain implementation choices |
| Browse by many organizations without copying | Dynamic Views | Raiatea | none required |
| Save self-updating selections | Smart Collections | Raiatea | optional AI query interpreter |
| Move managed files into useful folders | Organization | Raiatea policy + filesystem operation | Alfred observes/reconciles effects |
| Extract PDF/EPUB/scans/etc. | Processing / P0 | Raiatea orchestration | replaceable parsers/OCR/VLM |
| Translate source | Processing | Raiatea transformation contract | local/remote translation providers |
| Rebuild layout / convert format | Processing | Raiatea transformation contract | replaceable renderers/converters |
| Run long processing reliably | Job Center | unresolved | Durex candidate reuse |
| Trace where an output came from | all products | Raiatea provenance | engine/model metadata |
| Build a research/study route | Research & Learning Workspace | later Raiatea knowledge capability | source foundation |
| Build an AI-engineering notebook | AI Research Notebook | Research & Learning Workspace | document + knowledge foundations |
| Select approved sources for a course | TheBitLab | TheBitLab projection | Raiatea catalog/provenance |

## 10. First verifiable product slice

> Assertion status: `working-hypothesis`

The first slice should be small enough to test user value before building the
complete knowledge system, but large enough to prove the document boundary is
useful on its own.

A candidate vertical is:

```text
one user-selected local collection
  -> discover PDF + EPUB assets
  -> stable identity independent of pathname
  -> basic metadata + location + fingerprint
  -> P0 extraction route selected through benchmarked adapters
  -> searchable extracted content
  -> table/list + folder + one dynamic topic/language/status view
  -> one saved Smart Collection
  -> one on-demand Processing Recipe producing a traced derivative
  -> no automatic managed-file move required for the first proof
```

Why this candidate is useful:

- it joins the already-planned PDF/EPUB P0 slice to immediate personal value;
- it tests Asset identity and location before complex knowledge graphs;
- it tests search and views without requiring auto-organization;
- it tests transformation lineage with one derivative rather than a full
  publishing system;
- it creates the first integration seam with Alfred without making Alfred a
  document classifier.

The Product Map does not promote this slice to `planned` implementation. #106
survey/benchmark work and the later Use Case/Risk artifacts must validate it.

## 11. Product evolution after the first slice

> Assertion status: `working-hypothesis`

A possible value-ordered evolution is:

```text
A. Inventory & identity
   -> location tracking / duplicate detection / metadata

B. Search & views
   -> full text / filters / Smart Collections / natural-language query planner

C. Controlled organization
   -> inbox / managed / observed / frozen / policy previews

D. Rich processing
   -> OCR / translation / format conversion / layout reconstruction / batch DAG

E. Research & learning reuse
   -> source selection / concepts / routes / living bilingual material

F. Broader knowledge products
   -> temporal claims / field intelligence / forecasting / federation
```

This is a product hypothesis, not a fixed P1-P7 implementation sequence.
Dependencies may force a different engineering order.

## 12. Interface direction

### 12.1 Web workspace

> Assertion status: `accepted-decision`

The primary UI direction is a local web application. This keeps the user
experience independent from a single desktop toolkit and allows the same
backend contracts to serve future local or remote-safe surfaces.

The web UI must not become the owner of catalog, search or transformation
business logic.

### 12.2 Desktop packaging

> Assertion status: `working-hypothesis`

A desktop shell such as Tauri may later package the same web UI and expose safe
local integrations. Tauri is a candidate, not an accepted dependency. The
browser-accessible application and backend contracts should remain useful
without it.

## 13. Views are product state, not filesystem state

> Assertion status: `accepted-decision`

The product must maintain three distinct concepts:

```text
Physical / digital location
        ≠
Catalog classification and relationships
        ≠
Current UI view or Smart Collection
```

Changing a view must not move a file. Changing a folder policy must not erase
classification. Moving a file must not remove the asset from topic/project
views unless the underlying facts actually changed.

This separation is a central product invariant.

## 14. Reuse and repository strategy

> Assertion status: `accepted-decision`

Before implementing a cross-cutting capability, Raiatea must check whether it
already exists in Alfred, Durex, TheBitLab, DNA, Iberna or another project in
the ecosystem.

Current decisions:

- **Alfred:** reuse is explicit for filesystem observation; improve its contract
  rather than introduce a second watcher.
- **Durex:** audit before reuse; do not import its coding-agent internals into
  document processing.
- **TheBitLab:** reuse/migrate source-catalog lessons while keeping TheBitLab a
  consumer.
- **DNA:** no document ownership.
- **Iberna:** future multi-host/workspace research only.

Do not create repositories such as `asset-manager`, `open-content-ir` or
`document-ingestion-hub` merely to reflect conceptual boxes in this map. Begin
inside Raiatea with bounded modules/contracts. Extract a repository only when
an interface becomes independently useful, stable enough to version and safe
to publish.

## 15. Success measures by product surface

> Assertion status: `working-hypothesis`

### Document & Asset Library

Useful measures include:

- time to inventory a bounded collection;
- percentage of assets whose identity survives moves/renames correctly;
- duplicate/representation precision and manual correction rate;
- query success and time to find a known source;
- Smart Collection explainability and stability;
- organization-policy correction/rollback rate;
- extraction quality by source class;
- translation/layout manual repair;
- time and compute cost per Processing Recipe;
- ability to reconstruct any derivative from recorded lineage.

### Research & Learning Workspace

Measures remain those accepted in the Vision: navigation effort, explanation,
application/transfer, delayed recall, provenance correctness and repeated reuse
of durable artifacts.

A successful document library does not prove the learning thesis, and a useful
learning module does not prove the universal catalog architecture. Each surface
requires evidence for its own claims.

## 16. Out of scope for this Product Map

This artifact does not:

- define final domain schemas;
- choose implementation frameworks or storage;
- choose Docling/Tesseract/PaddleOCR/VLM/provider defaults;
- promise automatic organization in the first slice;
- generalize Durex;
- merge TheBitLab into Raiatea;
- define final public product names;
- schedule P1-P7;
- define pricing, licensing or hosted-service packaging;
- define the complete Use Case Model.

## 17. Decisions passed forward

The next canonical artifacts should use this map as follows:

### Use Case Model

Derive significant scenarios such as:

- inventory and locate an existing document;
- recover identity after a rename/move;
- search and save a Smart Collection;
- preview and apply a managed organization rule;
- extract and translate one source;
- produce multiple derivatives through one recipe;
- trace a derivative to source and transformation;
- hand a course-scoped source projection to TheBitLab.

### Risk List

Prioritize risks including:

- false identity/duplicate merges;
- destructive file organization;
- OCR/layout error hidden by fluent translation;
- rights leakage from private corpora;
- non-reproducible model transformations;
- watcher/platform gaps;
- Durex coupling without a generic contract;
- search/index cost or quality that fails on real collections;
- layout reconstruction cost exceeding user value.

### P0 #106

Use the Product Map to keep P0 focused on replaceable ingestion/extraction
contracts and quality evidence while the Document & Asset Library owns catalog,
views, organization and transformation intent.
