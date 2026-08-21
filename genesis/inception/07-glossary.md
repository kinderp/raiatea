# Raiatea Glossary and Initial Ubiquitous Language

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
> Child issue: [#117](https://github.com/kinderp/raiatea/issues/117)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Primary canonical sources: [`01-manifesto.md`](01-manifesto.md),
> [`03-system-context.md`](03-system-context.md),
> [`04-product-map.md`](04-product-map.md),
> [`05-use-case-model.md`](05-use-case-model.md), and
> [`06-risk-list.md`](06-risk-list.md)

## 1. Purpose

This Glossary stabilizes the **minimum language needed to reason consistently**
about Raiatea's accepted product boundaries, use cases and risks. It does not
define a database schema, class hierarchy, JSON model, ontology or public API.

A preferred term in this document means:

- documentation should use it consistently for the stated concept;
- competing terms should not be used as silent synonyms;
- future technical contracts should explain any deliberate departure from it;
- the term does **not** imply that the capability or data structure already
  exists in software.

The Glossary deliberately leaves some bibliographic and knowledge-model terms
provisional. This is how it contains Risk R-17 without pretending that every
future domain distinction is already known.

## 2. Language rules

> Assertion status: `accepted-decision`

### 2.1 Meaning before representation

A glossary definition is conceptual. The implementation may represent one
concept with one record, several records, a relation, a value object or no
persistent object at all.

Do not infer:

```text
Glossary term
    -> class name
    -> database table
    -> API resource
    -> event type
```

without a separate technical decision.

### 2.2 A role is not necessarily an entity

Some important words describe **roles in a workflow**, not permanent kinds of
things. `Source` is the central example: a digital artifact, physical holding,
remote resource or reference can act as a Source when Raiatea uses it as an
origin for extraction, evidence or transformation.

### 2.3 Location is never identity

Filesystem paths, shelf positions, URLs and mount points are locators. They may
change while the logical identity they locate remains stable.

### 2.4 Preserve layer names

`Original Artifact`, `Raw Extraction`, `Normalized Representation` and
`Derived Artifact` are intentionally different terms. They must not be
collapsed into one generic `content` value when the distinction matters to
provenance.

### 2.5 Status vocabulary remains owned by the Inception index

The canonical meanings of `principle`, `current-contract`, `accepted-decision`,
`provisional-decision`, `working-hypothesis`, `planned`, `deferred-research`,
`historical-note` and `rejected` remain defined in
[`README.md`](README.md). This Glossary does not redefine them.

## 3. Preferred vocabulary map

| Preferred term | Status | Do not silently use as synonym | Core distinction |
| --- | --- | --- | --- |
| Raiatea | accepted | Knowledge OS, Knowledge Core | Project/product family, not one runtime component |
| Universal Document & Asset Library | accepted product-surface name | Library Catalog | Manages more than books and more than filesystem folders |
| Catalog | accepted | filesystem, folder tree | Logical inventory and relationships |
| Catalog Entry | accepted conceptual term | Asset entity | A catalog reference to something known; not a schema commitment |
| Logical Identity | accepted | path, filename, hash alone | Stable identity independent of current location |
| Digital Artifact | accepted | file, source, document as universal synonym | Concrete/versioned digital material |
| Stored Instance | accepted | Digital Artifact | One stored occurrence/copy of a digital artifact |
| Physical Holding | accepted | Source, Work | A physical copy/item the person can locate/access |
| Location | accepted | identity | Where a holding/instance/reference can currently be found |
| Source | accepted as role | file, Work, Catalog Entry | Something used as an origin/input/evidence source in a workflow |
| Original Artifact | accepted | raw extraction | Acquired/referenced material before Raiatea extraction/normalization |
| Raw Extraction | accepted | normalized text | Direct extractor output before Raiatea normalization/correction |
| Normalized Representation | accepted | original | Structured/normalized form derived from extraction |
| Derived Artifact | accepted | original | Output produced by a transformation |
| Transformation | accepted | Processing Run | Recorded derivation from input(s) to output(s) |
| Processing Recipe | accepted | Processing Run | Declarative processing intent/template |
| Processing Run | accepted conceptual term | Recipe | One execution/attempt of a recipe or operation set |
| View | accepted | folder, Collection | Presentation/projection over catalog state |
| Collection | accepted | Smart Collection | Explicit membership selected by user/system action |
| Smart Collection | accepted | folder | Query-defined dynamic membership |
| Organization Policy | accepted | Classification | Policy deciding intended physical placement in managed scope |
| Authority Scope | accepted | rights/license | What Raiatea is operationally authorized to observe/change |
| Provider | accepted | Adapter | External engine/service/capability provider |
| Adapter | accepted | Provider | Raiatea integration boundary for a provider/system |
| Projection | accepted | duplicate catalog | Bounded consumer-facing representation of canonical data |
| Provenance | accepted | truth, confidence | Record of origin/context/transformations |
| Lineage | accepted | provenance as total synonym | Navigable derivation chain through transformations |
| Evidence | accepted minimal meaning | Source, Claim | Material/context offered in support/against a claim |
| Claim | accepted minimal meaning | fact, source | An assertion that may be supported/disputed; not automatically true |
| Work | deferred/provisional | canonical library root | Bibliographic abstraction not yet required by first slice |
| Manifestation | deferred/provisional | Digital Artifact | Bibliographic term not adopted as current core vocabulary |
| Asset | broad product term only | domain entity | General user-facing umbrella, not preferred entity name |

## 4. Project and product terms

### Raiatea

> Assertion status: `accepted-decision`

**Definition.** The overall project and product family whose purpose is to help
people navigate heterogeneous sources and evolving knowledge while preserving
provenance, uncertainty, personal control and portability.

**Not.** A parser, LLM, database, graph, single desktop app or one knowledge
store.

**Usage.** “Raiatea owns the general source/provenance boundary.”

### Universal Document & Asset Library

> Assertion status: `accepted-decision` for product role; public naming may
> still be refined

**Definition.** Raiatea's document/material surface for inventorying, locating,
searching, viewing, organizing and transforming physical holdings and digital
artifacts.

**Not.** A folder tree, book-only catalog, filesystem watcher or P0 extractor.

**Preferred short form in prose.** `Document & Asset Library` when context is
unambiguous.

### Research & Learning Workspace

> Assertion status: `accepted-decision` for product role; implementation largely
> absent

**Definition.** Higher-level Raiatea surface that consumes source/provenance and
later knowledge capabilities to build research/study routes, explanations,
practice and durable research artifacts.

**Not.** The owner of a second document catalog.

### AI Research Notebook

> Assertion status: `accepted-decision` for role; `working-hypothesis` for final
> public name

**Definition.** Candidate AI-engineering experience/vertical inside the Research
& Learning Workspace.

**Not.** Raiatea itself or the universal document platform.

### P0 — Source Ingestion & Extraction Hub

> Assertion status: `planned`

**Definition.** Raiatea's first planned platform foundation. It orchestrates
replaceable acquisition/extraction routes and produces structured,
source-linked, provenance-rich output with visible failure/degradation.

**Not.** The Catalog, filesystem watcher, Search/View product surface,
Organization Policy owner or Processing Recipe UX.

## 5. Catalog, identity and storage terms

### Catalog

> Assertion status: `accepted-decision`

**Definition.** Raiatea's logical inventory of known material, identities,
relationships, locations, states and relevant metadata.

**Not.** The filesystem tree. The Catalog may describe material across many
locations and may show the same material in many views.

**Implementation note.** `Catalog` is a conceptual boundary. It does not select
one database.

### Catalog Entry

> Assertion status: `accepted-decision` as editorial/conceptual term

**Definition.** A catalog-visible reference to something Raiatea knows about and
can address in user workflows.

A Catalog Entry may describe, depending on the future domain model, a digital
artifact, stored instance, physical holding or another catalogued object.

**Why this term.** It allows current documentation to speak about catalog
membership without declaring that every entry is one universal `Asset` entity.

**Not.** A promise of a `catalog_entry` table or API resource.

### Asset

> Assertion status: `provisional-decision` as broad product vocabulary; not a
> preferred core entity term

**Definition.** Broad user-facing umbrella for material of value managed or
referenced by the Document & Asset Library.

**Use carefully.** `Asset` is useful in the product name and informal product
language, but is too broad to carry precise identity semantics by itself.

Prefer `Digital Artifact`, `Stored Instance`, `Physical Holding`, `Catalog
Entry` or `Source` when one of those meanings is intended.

### Logical Identity

> Assertion status: `accepted-decision`

**Definition.** The stable identity by which Raiatea treats something as the
same catalogued thing across changes that should not create a new identity,
such as a simple path rename/move.

**Not determined here.** The identifier format, identity algorithm and exact
identity levels.

**Not.** Filename, current path or content hash alone.

### Digital Artifact

> Assertion status: `accepted-decision`

**Definition.** Concrete, versioned digital material that can be stored,
referenced, processed or produced: for example a PDF, EPUB, image, Markdown
artifact or generated PDF derivative.

A Digital Artifact is conceptually independent from where copies of it are
stored.

**Not.** A `Source` by definition. It assumes the Source role when a workflow
uses it as an origin/input/evidence source.

### Stored Instance

> Assertion status: `accepted-decision`

**Definition.** One concrete stored occurrence/copy of a Digital Artifact at a
Location.

Two Stored Instances can be exact duplicates of the same bytes while remaining
separate storage occurrences, for example one copy on a laptop and another on
a NAS.

**Why needed.** It separates “same material” from “where/how many copies exist”.

### Physical Holding

> Assertion status: `accepted-decision`

**Definition.** A physical copy/item that the person owns, controls or can
lawfully access and wants Raiatea to locate/catalogue.

Examples include one particular printed book on a shelf.

**Not.** Full-text content. A Physical Holding can exist without a digital
artifact or extractable text.

### Holding

> Assertion status: `provisional-decision`

**Definition.** General ownership/access notion for a copy/item available to the
person.

**Preferred current usage.** Use `Physical Holding` for physical material. For
digital material prefer `Digital Artifact` + `Stored Instance` until real use
cases show that a single cross-media `Holding` abstraction adds value.

### Location

> Assertion status: `accepted-decision`

**Definition.** A current or historical locator for a holding, stored instance or
external reference.

Examples:

- filesystem path + storage/mount identity;
- shelf/bookcase position;
- URL or repository coordinate where only a reference is retained.

**Invariant.** Location is mutable and is not Logical Identity.

### Current Location

> Assertion status: `accepted-decision`

**Definition.** Location currently believed/observed to be valid for an item or
instance, with appropriate availability/freshness state.

### Location History

> Assertion status: `accepted-decision` for need; exact retention is future work

**Definition.** Historical record of prior relevant locations needed for
reconciliation, provenance or recovery.

**Not.** An obligation to preserve every transient path forever.

### Exact Duplicate

> Assertion status: `accepted-decision`

**Definition.** Two stored/digital instances determined to contain the same
exact content under the project's chosen exact-content criterion, typically a
cryptographic content fingerprint plus relevant safeguards.

**Not.** The same as “same book”, “same meaning”, “same edition” or “related
representation”.

### Related Representation

> Assertion status: `accepted-decision` for relationship concept; detailed
> relation taxonomy remains provisional

**Definition.** A relationship indicating that two items are alternate or
related embodiments/derivations of substantially related intellectual material,
without claiming byte identity.

Examples may include PDF vs EPUB, original vs translation, scan vs born-digital
edition or revision relationships.

**Important.** The relationship may be uncertain/reviewable. It does not require
an adopted bibliographic `Work` entity.

### Representation

> Assertion status: `provisional-decision`

**Definition.** General term for one form/embodiment in which content is
represented.

**Preferred current use.** Use it in relationship/explanatory language when
format/language/embodiment matters. For concrete digital material prefer
`Digital Artifact`.

### Version

> Assertion status: `accepted-decision` conceptually

**Definition.** A distinguishable state of an item/artifact whose differences
matter to processing, identity or provenance.

**Not fixed here.** Semantic versioning, integer revision numbers or content
hashes as the version identifier.

### Revision

> Assertion status: `accepted-decision` conceptually

**Definition.** A later changed state in the history of material. A Revision may
create a new Version or relationship depending on the future domain contract.

### Present, Unavailable, Missing and Deleted

> Assertion status: `accepted-decision` for distinction; exact state machine is
> future work

- **Present** — the relevant Location was verified/observed as available under
  the declared freshness model.
- **Unavailable** — Raiatea cannot currently access/verify the Location, but has
  insufficient evidence to say the material was deleted.
- **Missing** — expected material is not found at a Location after a relevant
  reconciliation check; this still does not by itself prove logical deletion.
- **Deleted** — deletion is known/recorded strongly enough to distinguish it
  from temporary unavailability under the applicable contract.

These are evidence states, not reasons to erase history.

## 6. Source, extraction and provenance terms

### Source

> Assertion status: `accepted-decision` as a **role**

**Definition.** Something used as an origin or evidentiary input in a Raiatea
workflow.

A Source can be:

- a Digital Artifact;
- a rights-safe reference to remote material;
- a repository/notebook/resource;
- a Physical Holding when only metadata/observation is sourced from it;
- later, other supported media.

**Important.** `Source` does not mean “file”, “path”, “book Work” or “catalog
record”. One thing can be catalogued without currently playing a Source role,
and the same thing can be a Source in several transformations.

### Source Reference

> Assertion status: `accepted-decision`

**Definition.** A durable reference to source material when Raiatea does not or
cannot retain the full original bytes/content.

It should retain enough identity/location/rights context to make the limitation
explicit.

### Original Artifact

> Assertion status: `accepted-decision`

**Definition.** Original digital material acquired/provided to a processing
workflow before Raiatea extraction, normalization, translation or adaptation.

Where rights/storage constraints prohibit preservation, a Source Reference may
stand in place of retained original bytes.

**Not.** Proof that the source is authentic or true.

### Source Coordinate / Locator

> Assertion status: `accepted-decision` for concept; preferred short term
> `Source Coordinate`

**Definition.** Address within a Source that lets later material point back to a
specific region or interval.

Examples include page + bounding box, section/paragraph anchor, timecode,
repository file + line range or another source-class-specific coordinate.

**Not.** The same as a storage Location.

### Raw Extraction

> Assertion status: `accepted-decision`

**Definition.** Direct output produced by an extraction engine/provider before
Raiatea normalization/correction changes it.

It preserves evidence about what the engine actually returned.

### Normalized Representation

> Assertion status: `accepted-decision`

**Definition.** Structured/normalized form derived from Raw Extraction (or a
native parse) for consistent downstream use while retaining a route back to the
raw/source layer.

**Not.** The original source and not automatically “corrected truth”.

### Intermediate

> Assertion status: `accepted-decision` conceptually

**Definition.** A transformation output intended primarily for reuse by later
processing stages rather than as the final user-requested artifact.

An Intermediate still requires provenance and validity/invalidation semantics
when reused.

### Derived Artifact / Derivative

> Assertion status: `accepted-decision`; preferred formal term `Derived Artifact`

**Definition.** Digital artifact produced from one or more inputs by a recorded
Transformation.

Examples: translated Markdown, converted EPUB, generated PDF, extracted
structured bundle.

`Derivative` is acceptable shorthand in prose.

### Transformation

> Assertion status: `accepted-decision`

**Definition.** Recorded derivation that takes one or more identified inputs and
produces one or more outputs under a declared operation/intent and processing
context.

A Transformation records history; it is not synonymous with the runtime object
that executed it.

### Provenance

> Assertion status: `accepted-decision`

**Definition.** Information needed to understand where material/assertions came
from and the relevant context, transformations, actors/providers, time and
uncertainty around that origin.

**Not.** Proof of truth, authenticity or correctness. Provenance can tell us
where a false claim came from.

### Lineage

> Assertion status: `accepted-decision`

**Definition.** Navigable chain of derivation relationships connecting an
artifact/state backward and/or forward through Transformations and inputs.

**Relationship to Provenance.** Lineage is a derivation-focused part/view of the
broader provenance record. Do not use the two terms as perfect synonyms when
that distinction matters.

### Evidence

> Assertion status: `accepted-decision` for minimal conceptual distinction;
> detailed knowledge model deferred

**Definition.** Source-linked material, observation or result offered in support
of, against or relevant to a Claim.

**Not.** A Source itself. Evidence is the evidentiary use/context of source
material.

### Claim

> Assertion status: `accepted-decision` for minimal conceptual distinction;
> detailed claim model deferred

**Definition.** An assertion that can be attributed, supported, contradicted,
qualified or remain unresolved.

**Not.** Automatically a fact or truth merely because it is stored by Raiatea.

### Source ≠ Evidence ≠ Claim

> Assertion status: `accepted-decision`

Example:

```text
Source
  a published paper

Evidence
  a specific figure/result/statement from that paper used in an inquiry

Claim
  the proposition that the evidence is being used to support or challenge
```

This distinction does not yet define the future Knowledge Core schema.

## 7. Search, views and organization terms

### Classification

> Assertion status: `accepted-decision`

**Definition.** Descriptive assignment of categories, topics, metadata or
relationships that helps identify/organize material conceptually.

**Not.** A filesystem placement decision.

### Search Query

> Assertion status: `accepted-decision`

**Definition.** Criteria used to retrieve/select catalog material.

### Structured Query

> Assertion status: `accepted-decision`

**Definition.** Inspectable query criteria expressed in the supported query
model rather than opaque natural-language prose.

It may combine deterministic fields and supported retrieval semantics.

### Natural-language Query Interpretation

> Assertion status: `accepted-decision` for interaction direction; feature
> deferred from first slice

**Definition.** Process in which a model/interpreter proposes a Structured Query
from ordinary language.

**Invariant.** The model does not replace the index/search engine; the resulting
criteria must be inspectable/editable and unsupported meaning must be visible.

### View

> Assertion status: `accepted-decision`

**Definition.** User-facing presentation/projection of Catalog state using a
particular grouping, layout or perspective.

Examples: table, folder/location view, author grouping, timeline or topic view.

**Not.** A filesystem folder and not a separate source of truth.

### Dynamic View

> Assertion status: `accepted-decision`

**Definition.** View whose content/grouping is computed from current catalog
criteria/state and therefore changes as the underlying catalog changes.

### Collection

> Assertion status: `accepted-decision`

**Definition.** Named set of catalog references with explicit membership.
Membership is not necessarily derived from a query.

Deleting a Collection does not delete its underlying material.

### Smart Collection

> Assertion status: `accepted-decision`

**Definition.** Named dynamic selection whose membership is determined by a
stored query/rule and recomputed as relevant Catalog state changes.

**Invariant.** Store/understand the rule separately from its current members.

**Not.** A filesystem folder or duplicate copy of its members.

### Organization Policy

> Assertion status: `accepted-decision`

**Definition.** Rules/intent determining where managed Stored Instances should
be placed/renamed in authorized storage based on allowed criteria.

**Not.** Classification, View or Search Query.

### Authority Scope

> Assertion status: `accepted-decision`

**Definition.** Operational boundary declaring what Raiatea may do with material
or a Location, independent of whether doing it is otherwise lawful/technically
possible.

The current product requires semantics equivalent to:

- **Inbox** — intentionally submitted area in which material may be classified
  and proposed for placement according to policy;
- **Managed** — Raiatea may perform authorized placement/move/rename operations
  under applicable safeguards;
- **Observed** — Raiatea may observe/index according to policy but must not
  reorganize merely because it knows the location;
- **Manual/Frozen** — location/placement is user-controlled and automatic
  organization is disabled.

The labels may evolve; the authority distinction is stable.

### Observation

> Assertion status: `accepted-decision`

**Definition.** Fact/information received about external state, such as a
filesystem event or scan result.

**Invariant.** Observation does not grant Authority Scope.

## 8. Processing terms

### Processing Recipe

> Assertion status: `accepted-decision`

**Definition.** Declarative user/product intent describing desired processing
stages/outputs and relevant options for one source or batch.

Examples: extract only; extract+translate; create Markdown+EPUB; convert format.

**Not.** One actual execution attempt.

### Processing Run

> Assertion status: `accepted-decision` conceptually; execution implementation
> unresolved

**Definition.** One bounded attempt/execution of a Processing Recipe or related
operation set against identified input versions.

A Processing Run may succeed, fail, be cancelled or become partially/unknown
according to a future runtime contract.

**Not.** A commitment to Durex. Durex remains candidate execution reuse.

### Operation

> Assertion status: `accepted-decision`

**Definition.** One semantically meaningful transformation/action such as
extract, normalize, translate, render or convert.

### Stage

> Assertion status: `provisional-decision`

**Definition.** User/implementation-oriented grouping or position of Operations
inside a Processing Recipe/Run.

Use `Operation` when precise provenance semantics are intended; `Stage` may be
used for UX/progress grouping without implying a stable domain entity.

### Processing State

> Assertion status: `accepted-decision` for need; exact state machine future

**Definition.** Recorded state needed to distinguish progress/outcome of a
Processing Run/Operation, including at minimum the conceptual distinction
between not completed, succeeded, failed and unknown/partial where relevant.

**Invariant.** Unknown is not silently promoted to success.

### Warning

> Assertion status: `accepted-decision`

**Definition.** Structured indication that processing completed or partially
completed with a material limitation, uncertainty, degradation or condition the
consumer should not ignore.

**Not.** The same as a fatal error.

### Degraded Result

> Assertion status: `accepted-decision`

**Definition.** Output that remains usable for a bounded purpose but failed to
meet one or more declared quality/structure/fidelity expectations.

Degradation must be visible and linked to relevant Warnings.

### Facsimile

> Assertion status: `accepted-decision` for fidelity semantics

**Definition.** Output goal that prioritizes preserving page geometry and visual
appearance as closely as practical, with explicit tolerances/limitations.

**Not.** An unconditional pixel-identical promise, especially after translation.

### Layout-faithful

> Assertion status: `accepted-decision` for fidelity semantics

**Definition.** Output goal that preserves visual hierarchy, figures, tables,
columns and overall design structure while permitting text flow/pagination to
change.

### Semantic Reflow

> Assertion status: `accepted-decision` for fidelity semantics

**Definition.** Output goal that prioritizes semantic hierarchy/content/assets
while allowing responsive/reflowable presentation such as HTML/EPUB.

## 9. Integration and extensibility terms

### Provider

> Assertion status: `accepted-decision`

**Definition.** External or independently replaceable engine/service/component
that supplies a capability such as parsing, OCR, translation, metadata lookup
or rendering.

Provider identity/version belongs in provenance where materially relevant.

### Adapter

> Assertion status: `accepted-decision`

**Definition.** Raiatea-owned integration boundary translating between a
Provider/external system and Raiatea's own contract/semantics.

**Not.** The Provider itself.

Example:

```text
Provider: OCR engine X
Adapter: Raiatea component mapping X input/output into the P0 contract
```

### Consumer

> Assertion status: `accepted-decision`

**Definition.** Product/system that uses a Raiatea capability or bounded data
projection without owning the canonical source-of-truth responsibility.

### Projection

> Assertion status: `accepted-decision`

**Definition.** Bounded representation/selection of canonical Raiatea data
prepared for a consumer/use case.

**Not.** A second independent source of truth.

### Course-scoped Source Projection

> Assertion status: `accepted-decision` target; implementation absent

**Definition.** Projection containing the source/provenance references needed by
a particular TheBitLab course while leaving course-specific semantics owned by
TheBitLab and general source identity owned by Raiatea.

## 10. Rights and data-boundary terms

### Processing Authority

> Assertion status: `accepted-decision`

**Definition.** Product/user authorization for Raiatea to perform a particular
operation on particular material/scope.

**Not.** Proof that the user holds every legal right needed for the operation.
Operational authority and legal/licensing rights must both be satisfied where
applicable.

### Processing Rights

> Assertion status: `accepted-decision` conceptually; legal interpretation may
> require specialist review

**Definition.** Rights/permissions under which the requested processing is
allowed for the relevant material, jurisdiction/license/context.

**Not.** Redistribution Rights.

### Redistribution Rights

> Assertion status: `accepted-decision` conceptual distinction

**Definition.** Rights/permissions to share, publish or redistribute source or
derived material to others.

**Invariant.** Ability to process privately does not imply redistribution
permission.

### Corpus

> Assertion status: `accepted-decision`

**Definition.** Bounded set of source/material selected for a particular
processing, benchmark, research or learning context.

**Not.** The entire Catalog by definition.

### Private Corpus

> Assertion status: `accepted-decision`

**Definition.** Corpus whose material/state is private to the user/project and
must not be treated as public/shareable merely because Raiatea can process it.

### Retention Policy

> Assertion status: `accepted-decision` for concept; implementation future

**Definition.** Rules governing how long source material, intermediate layers,
logs/provenance or derived artifacts may/should be retained and how deletion or
expiry is propagated where required.

## 11. Terms deliberately deferred or constrained

### Work

> Assertion status: `deferred-research`

Bibliographic abstraction representing a distinct intellectual/artistic
creation is useful in standards such as library models, but Raiatea does not yet
adopt `Work` as a core entity.

**Reason.** The first slice can validate digital artifact identity, duplicates,
locations and related-representation links without solving the full
book/edition/translation ontology.

**Reconsider when.** Physical holdings, edition-aware cataloging or cross-format
bibliographic grouping becomes active product scope.

### Expression / Manifestation / Item

> Assertion status: `deferred-research`

Formal bibliographic concepts are not adopted wholesale in Inception. They may
be evaluated against actual UC-02/UC-16 needs before the physical/bibliographic
feature is planned.

Do not use `Manifestation` as a casual synonym for every PDF/EPUB in current
technical contracts.

### Document

> Assertion status: `accepted-decision` as ordinary category word, not universal
> ontology root

`Document` describes many important inputs, but Raiatea's destination includes
code, audio/video, datasets, images and other source families. Do not design the
entire Catalog as if every future item must be a document.

### Knowledge Core / Knowledge OS / Memory Graph

> Assertion status: `deferred-research` / historical exploratory language

These names do not currently identify an accepted bounded context or product.
Use concrete accepted capability names until later architecture justifies a
stable boundary.

### Truth / Fact / Trust

> Assertion status: constrained language

Do not use these as generic stored states without an operational definition.
Raiatea records sources, claims, evidence, provenance, uncertainty and review;
it does not turn repetition, popularity or provenance into automatic truth.

### Confidence

> Assertion status: constrained language

Confidence must always identify **confidence in what** and where the value came
from (engine score, calibrated estimate, human judgment, etc.). Avoid one global
`confidence` field that collapses extraction quality, claim support, identity
matching and trust into one number.

## 12. Critical distinctions at a glance

### Identity and storage

```text
Logical Identity
    ≠ Location
    ≠ filename/path

Digital Artifact
    ≠ Stored Instance

Exact Duplicate
    ≠ Related Representation
```

### Physical and digital

```text
Physical Holding
    ≠ Digital Artifact
    ≠ full-text availability
```

### Source and knowledge roles

```text
Source
    ≠ Evidence
    ≠ Claim
```

### Processing layers

```text
Original Artifact
    -> Raw Extraction
    -> Normalized Representation
    -> Intermediate(s)
    -> Derived Artifact
```

The arrow means derivation only when supported by recorded Transformations; it
does not mean every workflow contains every layer.

### Provenance

```text
Provenance
    ≠ truth
    ≠ correctness

Lineage
    ⊂ derivation-focused provenance
```

### UI/catalog organization

```text
Classification
    ≠ Organization Policy

View
    ≠ Collection
    ≠ Smart Collection
    ≠ filesystem folder
```

### Processing

```text
Processing Recipe
    ≠ Processing Run

Provider
    ≠ Adapter
```

### Authority and rights

```text
Observation
    ≠ Authority Scope

Processing Authority
    ≠ Processing Rights
    ≠ Redistribution Rights
```

## 13. Guidance for P0 #106

> Assertion status: `accepted-decision` for vocabulary guidance; P0 schema
> remains future planned work

P0 contract/survey documentation should prefer:

- `Source` for the workflow role, not for every file record;
- `Original Artifact` / `Source Reference` for the preserved/referenced input
  boundary;
- `Raw Extraction` for engine-native output;
- `Normalized Representation` for Raiatea-normalized structured output;
- `Source Coordinate` for page/bbox/time/file-line anchors;
- `Provider` and `Adapter` as distinct terms;
- `Warning` / `Degraded Result` for visible non-fatal quality limitations;
- `Transformation` / `Provenance` for derivation history.

P0 should avoid locking its first public contract to `Work`, `Manifestation` or
one universal `Asset` entity until later domain evidence requires them.

The exact names used in a future schema may differ if a technical ADR explains
why, but the conceptual distinctions above must remain visible.

## 14. R-17 containment

> Assertion status: `provisional-decision`

Risk R-17 (premature vocabulary/schema freeze) is **contained for Inception**
when:

1. accepted terms are used consistently in canonical documentation;
2. deferred bibliographic/knowledge terms are not introduced as core entities
   without a later decision;
3. schema/API work cites this Glossary but remains free to choose a technical
   representation;
4. semantic changes to accepted terms require visible review/migration rather
   than silent reuse with a new meaning.

This does not mark R-17 permanently `mitigated`. Real implementation may expose
new domain distinctions and force the Glossary to evolve.

## 15. Out of scope

This Glossary does not:

- define an ER model, ontology, JSON Schema or OpenAPI contract;
- choose a database or identifier format;
- adopt FRBR/LRM or another bibliographic model wholesale;
- define the future Knowledge Core ontology;
- select providers/engines;
- define final public branding for every product surface;
- promote the first slice to `planned`;
- schedule P1-P7.

## 16. Decisions passed forward

### P0 #106

Use section 13 as vocabulary input for source taxonomy, survey, extraction
contracts and benchmark artifacts. Any technical schema should map back to these
concepts and explicitly document deliberate divergences.

### First-slice planning

Use `Digital Artifact`, `Stored Instance`, `Location`, `Logical Identity`,
`Source`, `Original Artifact`, `Raw Extraction`, `Normalized Representation`,
`Derived Artifact`, `Transformation`, `Provenance`, `View`, `Smart Collection`,
`Processing Recipe` and `Processing Run` as the initial conceptual language.
Do not require `Work`/`Manifestation` for the candidate PDF/EPUB slice.

### Inception Review

Verify that the accepted documents use these concepts consistently or document
intentional historical/provisional language. The review should also identify
terms that remain too ambiguous to support Elaboration safely.
