# Why Raiatea

> Document maturity: `In review`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 July 2026
>
> Parent issue: [#98](https://github.com/kinderp/raiatea/issues/98)
>
> Child issue: [#104](https://github.com/kinderp/raiatea/issues/104)
>
> Maintainer value review: [PR #105 decision](https://github.com/kinderp/raiatea/pull/105#issuecomment-5040031548)

## 1. The problem

People who want to understand a difficult field rarely suffer from a lack of
material. They face the opposite problem: books, papers, repositories, videos,
courses, discussions and news arrive faster than they can evaluate or connect
them.

Access is abundant; orientation is scarce.

A motivated learner or researcher must repeatedly answer questions such as:

- What should I study first for my actual goal?
- Which prerequisites am I missing?
- Which sources are foundational, current, practical or merely popular?
- Who has made the important contributions, and on which subproblem?
- What is established knowledge, what is disputed and what is only a forecast?
- How does a dense formula, diagram or code example become something I can
  explain and apply?
- What changed since I last studied this topic?
- Where did a conclusion come from, and can I inspect the evidence again?
- How do I resume after an interruption without reconstructing the entire
  context?

Today the person performs most of this integration manually. Information is
distributed across tools, source formats and moments in time. The work spent
organising the field competes directly with the work required to understand
it.

## 2. The first person Raiatea must help

> Assertion status: `accepted-decision`

Raiatea's first target is not every learner and not every domain. It is a
self-directed technical learner or practitioner who:

- has a concrete objective rather than casual curiosity;
- already owns or can legally access high-quality sources;
- has limited and interruptible study time;
- wants explanation, mathematics, code and historical context together;
- needs to preserve English technical terminology while understanding through
  another language;
- wants to progress from use of existing tools toward engineering and research;
- is willing to inspect sources and correct the system rather than delegate
  judgement completely.

The first supervised case is AI engineering and the internal mechanics of
large language models. It is a beachhead used to test the product thesis, not a
claim that Raiatea is limited to AI.

## 3. Why current tools do not solve the whole problem

> Assertion status: `working-hypothesis`

Existing tools are valuable and should remain part of the route.

### Search and recommendation systems

They help discover material, but ranking is not a personal curriculum. They
rarely preserve why a source was selected, what prerequisite it assumes or how
it changes the learner's next step.

### Books, papers and courses

They provide authority, depth and coherent authorship. They cannot adapt their
sequence, explanation or recovery path to one reader, and they become harder to
navigate when knowledge must be combined across many sources and dates.

### Note-taking and knowledge-graph tools

They preserve personal material and links. The user still performs most
diagnosis, source comparison, pedagogical transformation and maintenance.

### General-purpose LLM conversations

They can explain, translate, compare and generate exercises quickly. A chat is
usually an ephemeral synthesis rather than a durable, versioned and
source-governed learning environment. It may lose provenance, flatten
disagreement, forget earlier state or express unjustified confidence.

### Learning-management systems

They can deliver structured courses and assessments. Their content and route
are normally prepared in advance and are not designed to maintain a living,
cross-source model of a field or of one learner's evolving questions.

Raiatea should not replace these tools. Its reason to exist is to coordinate
their strengths while preserving source authority, personal state and
reversibility.

## 4. The product thesis

> Assertion status: `working-hypothesis`

Raiatea can reduce the effort required to move from **available material** to
**durable understanding** without hiding the evidence or taking judgement away
from the person.

It attempts to do this by maintaining four connected things:

1. a source-linked representation of what material says;
2. an explicit learning or research route for a particular objective;
3. pedagogical transformations that improve explanation, practice and recall;
4. observed evidence about what remains clear, fragile, untested or disputed.

The essential transformation is:

```text
scattered sources
    -> structured evidence
    -> connected concepts and claims
    -> guided explanation and practice
    -> observed learning evidence
    -> a revised route
```

Raiatea must not produce more material merely because it can. It must reduce
the cognitive and organisational cost of turning material into understanding.

## 5. The first-session promise

> Assertion status: `working-hypothesis`

Within one useful session, Raiatea should transform a bounded body of material
and a concrete goal into an output that the person can use immediately.

For the current pedagogical vertical, that output should be:

- source-linked and explicit about transformations;
- readable in the learner's preferred language without hiding original
  terminology;
- pedagogically reorganised rather than mechanically translated;
- able to decompose dense figures and procedures into controllable steps;
- connected to prerequisites, misconceptions and the next route;
- accompanied by active checks and targeted recovery;
- usable locally without requiring a remote account;
- exportable and inspectable outside a single chat session.

The promise is not "Raiatea makes you an expert in one session". It is:

> Raiatea should leave you with a clearer, more usable and more verifiable next
> state than the sources and tools could provide separately in the same time.

## 6. The compounding promise

> Assertion status: `working-hypothesis`

Repeated use should create value that a one-off answer cannot provide:

- stable memory of sources, decisions, questions and corrections;
- a route that changes as evidence about the learner changes;
- reusable concept pages rather than repeated explanations;
- longitudinal views of a field, person, claim or debate;
- explicit history instead of silent overwriting;
- the ability to update a derived explanation when its sources change;
- a personal body of work that can remain private or contribute safe derived
  knowledge under clear rights.

Immediate utility earns the next session. Compounding utility must justify
continued use. Raiatea needs both; future network effects cannot excuse weak
individual value.

## 7. What exists now

> Assertion status: `current-contract`

The implemented vertical slice is intentionally narrower than the thesis. It
currently demonstrates a local pedagogical module system with:

- declarative, self-contained HTML modules;
- stepwise semantic and procedural visuals;
- Focus UI and controllable reading preferences;
- linked concepts and glossary recovery;
- deterministic remediation after selected errors;
- local persistence of observed interactions;
- module- and step-level provenance;
- two LLM-learning examples: self-attention and Query/Key/Value;
- validation, browser tests and reproducible evaluator packaging;
- supervised pilot record contracts, runbook/checklist and synthesis tools.

This proves that the proposed learning experience can be built. It does not yet
prove that it improves understanding, transfer, retention or study efficiency.

The active pilot roadmap exists to collect that evidence before the project
expands its infrastructure.

## 8. Required long-term capabilities and priority

> Assertion status: `mixed`

Raiatea does not currently provide the general capabilities in this section.
That absence is a `current-contract` observation. Their inclusion in the
long-term destination is an `accepted-decision`; it must not be represented as
present functionality.

Priority P0 is fixed by maintainer decision. The order from P1 to P7 is a
`provisional-decision` to refine in the Product Map and Risk List. These
capabilities must not be started in parallel merely because they are all part
of the destination.

| Priority | Required capability | Why it follows in this order |
| --- | --- | --- |
| **P0** | General Source Ingestion & Extraction Hub | Raiatea cannot teach, connect or verify material that it cannot acquire and structure reliably. The hub is also independently useful and can produce reusable open-source components. |
| **P1** | Temporal provenance and canonical knowledge core | Extracted content must become addressable evidence with identity, time, structure, transformations and reversible links to sources rather than an ungoverned pile of text. |
| **P2** | Validated adaptive Research & Learning Workspace | The source and provenance foundation must improve routes, explanations, remediation and observed learning evidence without declaring unvalidated mastery. |
| **P3** | General isolated Execution Lab | Code, notebooks, tests and reproducible environments must connect explanation to real execution across languages and runtimes. |
| **P4** | Identity, claim, position and change intelligence | People, organisations, publications, claims and changes of position require explicit identity resolution, attribution, context and time. |
| **P5** | Field Intelligence Maps and Reality Observatory | Sources, concepts, people, events and debates become navigable views of a field and of its evolution without flattening disagreement into one answer. |
| **P6** | Forecasting and calibration | Forecasts require evidence, counter-evidence, horizons, resolution criteria and measured calibration; they cannot precede reliable temporal data. |
| **P7** | Federation, distributed compute and participatory governance | Sovereign nodes, shared bundles, useful distributed work and governance become justified only after valuable local workflows and stable contracts exist. |

### P0 — General Source Ingestion & Extraction Hub

> Assertion status: `accepted-decision`

The first platform capability must accept arbitrary **user-selected** sources
through rights-aware adapters and produce high-quality, structured and
traceable extraction. The intended source classes include, progressively:

- born-digital PDF, EPUB and other book or document formats;
- scanned books, photographed pages and image-only PDF;
- scholarly papers containing sections, citations, formulae, tables, charts
  and figures;
- web articles, documentation, feeds and permitted content from selected social
  platforms;
- audio and video with existing captions or authorised transcription;
- source code, repositories, notebooks and technical artefacts;
- photographs of receipts, shopping flyers, labels and other everyday printed
  material;
- barcodes and QR codes, retaining both decoded values and their visual/source
  location.

"General" means extensible across heterogeneous classes, not a claim that one
engine can understand every possible input. Each supported class needs an
explicit quality profile, representative test corpus, known failure modes and
acceptance metrics.

The hub should integrate, compare and orchestrate existing parsers, OCR
engines, speech-to-text systems, barcode decoders and suitable models. Raiatea
should implement adapters, routing, provenance, quality evaluation and missing
transformations; it should not recreate mature extraction engines without
evidence that doing so is necessary.

Every extraction route should preserve, where the source permits:

- the untouched source or a rights-safe reference to it;
- document hierarchy, reading order and page or time coordinates;
- text plus tables, formulae, figures, captions, code and embedded assets;
- the engine, model, version, parameters and transformations used;
- confidence, warnings and alternative interpretations where available;
- language and normalisation decisions without silently replacing raw output;
- ownership, licence, storage and publication policy;
- stable fragment identifiers that later knowledge and learning artefacts can
  cite precisely.

Reusable adapters, schemas, evaluation harnesses and non-proprietary test
fixtures should be open sourced when they can help other projects without
exposing private corpora, credentials or restricted content. This makes the
first foundation valuable even before the rest of Raiatea exists.

### Sequencing rule

> Assertion status: `accepted-decision`

P0 is the first platform foundation, but it must still begin with a bounded
vertical slice. A plausible sequence is digital PDF and EPUB, followed by
scanned documents and scholarly layout, then web/media and everyday visual
sources. The exact slice belongs in the Product Map and Source Ingestion
roadmap after a current technology survey and benchmark design.

## 9. Non-goals

> Assertion status: `accepted-decision`

Raiatea is not intended to be:

- an oracle that declares a single final truth;
- an assistant that removes the person's responsibility to judge;
- a replacement for authors, teachers, researchers or primary sources;
- an indiscriminate copy of private or copyrighted corpora;
- a system that equates clicks, quiz answers or confidence with competence;
- a feed optimised for attention rather than understanding;
- a universal platform built before one narrow product proves value;
- a monolith that forces Alfred, Learning Lab and other projects into one
  runtime merely because their ideas are related;
- a prediction engine that hides assumptions or cannot resolve its forecasts;
- an AI-branded interface whose novelty matters more than legibility and calm.

## 10. Principles that justify beginning

This document does not replace the future Manifesto. It records only the
minimum commitments required to explain why the work should start.

### The person remains the navigator

> Assertion status: `principle`

Raiatea may suggest routes, surface contradictions and explain trade-offs. The
person retains authority over goals, private state, publication and decisions.

### No important conclusion without a route back

> Assertion status: `principle`

A useful synthesis must remain connected to sources, transformations,
uncertainty and time. Verifiability is part of the product, not an optional
bibliography added at the end.

### Understanding must be demonstrated through use

> Assertion status: `principle`

Raiatea should prefer explanation, reconstruction, application and recovery
over the appearance of fluent completion. Observed interactions are evidence,
not proof of mastery.

### Private material is not automatically publishable material

> Assertion status: `principle`

The ability to process a source for personal use does not grant the right to
redistribute it. Private corpora, citations, derived knowledge and public
artifacts require explicit boundaries.

### Architecture must follow validated value

> Assertion status: `principle`

Federation, knowledge graphs, sensors and distributed execution are means. They
are justified only when a validated user need requires them.

## 11. Hypotheses and tests

> Assertion status: `working-hypothesis`

| ID | Working hypothesis | Evidence needed | Invalidation signal |
| --- | --- | --- | --- |
| H1 | A Raiatea module improves conceptual explanation and transfer compared with source-only study and ordinary LLM assistance | Supervised three-condition comparison using equivalent time and delayed/application questions | No meaningful benefit, or benefit explained only by additional study time |
| H2 | Integrated prerequisites, visuals, remediation and provenance reduce navigation effort | Observation of interruptions, recovery time, source switching and user explanation | Learners ignore the integrated route or prefer independent tools with less friction |
| H3 | A source-linked persistent artifact is more valuable than repeated chat answers | Return use, corrections, reuse and ability to recover prior reasoning | Users consistently discard the artifact and restart in chat |
| H4 | Immediate utility can coexist with long-term knowledge accumulation | First-session usefulness plus repeated-session value without mandatory setup | Value appears only after extensive ingestion or configuration |
| H5 | Manual, reviewed content is the right way to discover automation requirements | Repeated authoring tasks, measured cost and stable patterns across different modules | Every module needs bespoke work, or automation lowers quality below the source |
| H6 | The first AI-engineering beachhead exposes reusable needs without forcing a universal model | A second domain reuses the contracts with limited change | Reuse requires domain-specific exceptions that dissolve the common product thesis |

## 12. Kill criteria

> Assertion status: `accepted-decision`

Raiatea should narrow, pause or stop the current direction if sustained evidence
shows that:

1. a learner using the source plus an ordinary LLM achieves equivalent or
   better understanding with materially less effort;
2. pedagogical transformation costs more than the value users assign to the
   result and cannot be reduced without losing quality;
3. provenance and rights requirements make the useful output impractical or
   legally unsafe;
4. users do not return to, correct or build upon the persistent artifacts;
5. observed learning evidence cannot support better routing than simple user
   choice;
6. the product works only for its maintainer and cannot survive supervised use
   by people with different backgrounds;
7. platform infrastructure grows faster than validated user value;
8. the project cannot maintain a meaningful advantage over a transparent set
   of existing tools used together.

Failure of the broad vision does not invalidate every artifact. The pedagogical
renderer, provenance contracts or research methods may remain useful
independently. The purpose of kill criteria is to prevent attachment to the
largest story from hiding evidence about the product.

## 13. Why the name is not yet the argument

> Assertion status: `accepted-decision`

Raiatea is the current project name. The founding conversation connects it to
navigation, long voyages, curiosity and the idea that understanding is a route
rather than a race.

Those metaphors can guide tone and identity, but they are not the reason the
product deserves to exist. Historical quotations, Polynesian navigation,
cultural references, constellations and possible mascot concepts require a
separate, source-based and culturally respectful review before public use.

## 14. Open decisions

- Whether **AI Research Notebook** is the public name of the first vertical or
  an experience inside a broader private Research & Learning Workspace.
- How the first supervised pilot will compare Raiatea with the original source
  and with ordinary LLM assistance.
- Which minimum outcome is valuable enough to justify authoring a second full
  module sequence.
- What minimum temporal provenance and knowledge model P1 requires after the
  first extraction vertical, without designing the complete core in advance.
- Which existing extraction engines should be reused for each P0 source class
  after a current capability, licence and benchmark survey.
- How Raiatea relates to Alfred and Learning Lab without assuming premature
  runtime or repository convergence.
- Which elements of the navigation metaphor can be used publicly after
  historical and cultural review.

## 15. Sources and provenance

This canonical statement derives primarily from:

- [`genesis/00-understanding.md`](../00-understanding.md);
- [`genesis/08-independence-business-model-and-failure-analysis.md`](../08-independence-business-model-and-failure-analysis.md);
- [`genesis/10-immediate-value-thesis.md`](../10-immediate-value-thesis.md);
- [`genesis/18-why-raiatea-not-just-an-llm.md`](../18-why-raiatea-not-just-an-llm.md);
- [`genesis/19-private-corpus-adaptive-exercises.md`](../19-private-corpus-adaptive-exercises.md);
- [`genesis/20-pedagogical-visual-standard.md`](../20-pedagogical-visual-standard.md);
- the accepted [Genesis audit](00-genesis-audit-and-traceability.md);
- the accepted [canonical Inception contract](README.md);
- the founding conversation supplied by the maintainer.

Repository and pilot-state claims reflect the state observed on 21 July 2026.
This document intentionally leaves cultural and external factual claims for
separate sourced research.
