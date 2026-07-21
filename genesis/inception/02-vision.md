# Raiatea Vision

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 July 2026
>
> Parent issue: [#98](https://github.com/kinderp/raiatea/issues/98)
>
> Child issue: [#109](https://github.com/kinderp/raiatea/issues/109)
>
> Primary sources: [`00-why-raiatea.md`](00-why-raiatea.md),
> [`01-manifesto.md`](01-manifesto.md),
> [`genesis/08`](../08-independence-business-model-and-failure-analysis.md),
> [`genesis/10`](../10-immediate-value-thesis.md),
> [`genesis/18`](../18-why-raiatea-not-just-an-llm.md),
> [`genesis/19`](../19-private-corpus-adaptive-exercises.md) and
> [`genesis/20`](../20-pedagogical-visual-standard.md)

## 1. Vision statement

> Assertion status: `accepted-decision`

Raiatea will attempt to help a person become genuinely oriented in a complex
field by turning heterogeneous lawful sources into a durable, source-linked
and evolving route for study, research, verification and later action.

The route should answer more than "what should I read?" It should make visible:

- what the person already has and still lacks;
- which concepts and prerequisites organize the field;
- which sources, people, projects and events matter, and why;
- where evidence, interpretation, disagreement and uncertainty differ;
- what changed over time;
- what the person can explain, apply, reproduce or challenge;
- which update should alter the route and which noise can be ignored.

## 2. First person and first domain

> Assertion status: `accepted-decision`

The first target is a self-directed technical learner and practitioner who
wants to become an AI engineer while developing the ability to understand LLM
research, code and systems deeply.

This person may already own books, maintain repositories, collect papers and
videos, and use general-purpose LLMs, but lacks a coherent route across those
materials and cannot afford to reconstruct the field repeatedly.

The initial AI-engineering beachhead is a validation domain, not a permanent
limit on Raiatea.

## 3. Current reality

> Assertion status: `current-contract`

Raiatea is not yet a general knowledge platform or ingestion hub. The current
implementation is a local, supervised vertical slice of the pedagogical
hypothesis. It includes, at different levels of maturity:

- declarative self-contained HTML learning modules;
- calm reading controls and step-by-step semantic visuals;
- linked concepts, diagnostic questions and deterministic remediation;
- local observed-learning evidence without automatic mastery claims;
- module- and step-level provenance;
- schema validation, Python tests, browser tests and reproducible evaluator
  artifacts;
- a supervised pilot workflow that is not yet fully closed.

It does not currently provide general extraction, a temporal knowledge core,
identity and claim intelligence, a container execution lab, forecasting,
federation or participatory governance.

Observation basis: repository and GitHub state reviewed on 21 July 2026; see
the canonical [Genesis audit](00-genesis-audit-and-traceability.md).

## 4. First required foundation: sources

> Assertion status: `accepted-decision` for priority; `planned` for capability

The first platform foundation is **P0 — General Source Ingestion & Extraction
Hub**. Without reliable sources and stable coordinates, later knowledge,
teaching and intelligence layers cannot remain verifiable.

P0 must progressively support user-selected classes such as:

- born-digital PDF, EPUB and selected document formats;
- scans, photographed pages and image-only documents;
- scholarly material with sections, citations, formulas, tables, charts and
  figures;
- authorized web pages, documentation, feeds and platform content;
- audio and video through existing captions or authorized transcription;
- source code, repositories and notebooks;
- everyday visual sources such as receipts, labels and shopping flyers;
- barcodes and QR codes with decoded value and source location.

Raiatea should provide an orchestration hub rather than recreate mature
parsers, OCR systems, speech-to-text engines, barcode decoders or multimodal
models without evidence. Adapters must preserve the selected engine, version,
parameters, transformations, warnings, rights and quality evidence.

The destination is broad; the first implementation must remain a bounded,
benchmarked vertical slice. **Digital PDF + EPUB** is the current candidate,
not yet a confirmed technical choice.

Roadmap authority: milestone
[#2 — Source Ingestion Foundation v0](https://github.com/kinderp/raiatea/milestone/2)
and issue [#106](https://github.com/kinderp/raiatea/issues/106).

## 5. Required capability sequence

> Assertion status: `accepted-decision` for inclusion; `provisional-decision`
> for the order after P0; all capabilities are currently `planned`

All capability groups below belong to the intended long-term system. Their
presence in this Vision does not mean that their final boundaries or
architectures are known.

| Priority | Required capability | Outcome it must eventually enable |
| --- | --- | --- |
| P0 | General Source Ingestion & Extraction Hub | Acquire heterogeneous sources with structure, coordinates, provenance, rights and visible failure modes |
| P1 | Temporal provenance and canonical knowledge core | Preserve source-linked concepts, claims, events, revisions and time without overwriting history |
| P2 | Validated adaptive Research & Learning Workspace | Build routes, explanations, exercises and recovery from sources and observed learning evidence |
| P3 | General isolated Execution Lab | Run reproducible code, tests and experiments across languages and environments |
| P4 | Identity, claim, position and change intelligence | Reconstruct what people and organizations stated, when and in which context |
| P5 | Field Intelligence Maps and Reality Observatory | Orient a person in a field through people, literature, projects, debates, events and current change |
| P6 | Forecasting and calibration | Register probabilistic forecasts, evidence, resolution criteria and retrospective calibration |
| P7 | Federation, distributed computation and participatory governance | Make shared knowledge portable, independently verifiable and governable without one indispensable provider |

Product Map and System Context must refine these groups before they become
bounded contexts or implementation epics.

## 6. First product hypothesis

> Assertion status: `working-hypothesis`

The first coherent product category is a **private Research & Learning
Workspace**. **AI Research Notebook** remains the candidate name for its first
visible AI-engineering experience.

Given a real goal and a lawful private corpus, the workspace should eventually
produce a staged set of durable outcomes:

1. a source inventory with duplicates, quality limits and coverage gaps;
2. a prerequisite and concept map;
3. an ordered, explainable reading and practice route;
4. bilingual living material that keeps source and adaptation distinct;
5. pedagogical explanations, visuals, code and targeted exercises;
6. a map of important papers, people, organizations and projects;
7. explicit open questions, contradictions and research directions;
8. later updates expressed as changes to the existing route, not a generic
   feed.

This product hypothesis must be tested against the original sources and a
well-prompted general-purpose LLM workflow. Naming remains open until the
Product Map distinguishes product, experience, deliverable and capability.

## 7. Value timeline

> Assertion status: `working-hypothesis`

### First session

The user should receive an immediately usable and exportable artifact before
being asked to configure an ontology or wait for a mature community network.
Candidate early results include a corpus inventory, missing-prerequisite map,
provisional route or one complete source-linked learning module.

### Repeated use

Raiatea should compound value by preserving corrections, source coordinates,
routes, experiments, observed learning evidence and historical versions. The
value should come from continuity and reuse, not from making export or exit
difficult.

### Long-term use

The same source and provenance foundations should support field orientation,
continuous monitoring, public claim histories, calibrated forecasts and
federated knowledge. These outcomes must not be treated as validated merely
because they fit the same conceptual direction.

## 8. Measures and validation

> Assertion status: `accepted-decision`

Each capability must define which user outcome changes and how the project can
discover that it failed. Relevant measures include:

- structural fidelity and manual repair by source class;
- time to first useful artifact;
- hours and navigation effort saved;
- source coverage, citation accuracy and unsupported-claim rate;
- quality of explanation, transfer to new tasks and delayed recall;
- ability to reconstruct a result and identify exactly what changed;
- correction cost when a source or conclusion is revised;
- portability across models and providers;
- latency, compute, storage, energy and monetary cost;
- privacy, rights and security incidents;
- user ability to proceed without treating Raiatea as an authority.

The first pedagogical validation should compare equal-time use of:

1. the original source;
2. the source plus ordinary LLM assistance;
3. the Raiatea learning environment.

The P0 extraction validation must publish a separate quality profile for each
source class. A universal extraction score would hide materially different
failure modes.

## 9. Product constraints

> Assertion status: `mixed`

The following constraints are already accepted through the Why and its
principles:

- No output may imply rights to redistribute a source merely because private
  processing was lawful.
- Raw acquisition, extraction, normalization and later interpretation must
  remain separable.
- Important outputs must retain provenance and visible uncertainty.
- User data, private corpora and observed learning evidence are private by
  default.
- No feature should optimize primarily for engagement or notification volume.

The following remain `working-hypothesis` or `provisional-decision` constraints
to test and refine in Product Map and Risk List:

- Raiatea must create useful private value before network effects exist.
- LLM, extraction and execution providers must remain replaceable behind
  explicit contracts where feasible.
- Advanced models and graphs should use progressive disclosure rather than
  overwhelm the first workflow.
- High-stakes domains require separate controls and cannot inherit confidence
  from an AI-engineering pilot.

## 10. Scope boundaries

> Assertion status: `accepted-decision`

Raiatea is not currently attempting to:

- ingest all human knowledge in one release;
- define a universal ontology before concrete verticals;
- replace authors, teachers, researchers or professional judgment;
- become a new foundation-model provider;
- scrape platforms indiscriminately or bypass rights and access controls;
- infer truth, causality, influence or competence from popularity alone;
- merge Alfred, Learning Lab and Raiatea into one runtime without validated
  use cases and boundaries;
- implement P1-P7 before the contracts and evidence needed by the prior
  capability exist.

## 11. Relationship to existing tools

> Assertion status: `accepted-decision`

Raiatea should use capable LLMs, extraction engines, editors, repositories,
learning tools and execution infrastructure rather than imitate them. Its
reason to exist is the durable coordination of work across sources, time,
people, rights, evidence, models and revisions.

An adapter, schema, benchmark harness or pedagogical component that is useful
outside Raiatea should be published independently when it is safe and lawful
to do so. Open source is a means of reuse, verification and continuity, not a
claim that private corpora or every hosted service must be public.

## 12. Decisions updated from the Genesis audit

> Assertion status: `mixed`

| Audit decision | Vision status on 21 July 2026 |
| --- | --- |
| D1 — first product name and boundary | Still open: Research & Learning Workspace is the product category; AI Research Notebook is a candidate experience name |
| D2 — long-term core name | Provisional: use Raiatea for the project and descriptive capability names until System Context defines a real core boundary |
| D3 — Alfred and Learning Lab | Still open: related projects and possible consumers or integrations, not declared subproducts or shared runtimes |
| D4 — pilot versus new infrastructure | Updated by maintainer priority: P0 design may proceed through Genesis, survey and benchmark work; new pedagogical hardening should still follow pilot evidence |
| D5 — federation, governance and forecasting | Updated by maintainer decision: required long-term capability groups P6-P7, absent today; their order and design remain provisional |
| D6 — navigation and cultural references | Navigation may guide internal language; external historical and cultural claims remain outside canonical branding until dedicated research |

## 13. Next decisions

System Context and Product Map must decide or narrow:

1. the exact boundary between the P0 hub and consumers of extracted content;
2. which P0 artifact is useful as a standalone open-source product;
3. whether AI Research Notebook names a product, experience or curated
   expedition;
4. the smallest workflow that joins P0 sources to the current pedagogical
   vertical without creating the complete P1 core;
5. ownership boundaries among Raiatea, Alfred and Learning Lab;
6. which measures gate entry from Inception into Elaboration for P0.

## 14. Vision exit criteria

This Vision is useful only if it lets the next artifacts:

- define actors and external systems without inventing implementations;
- separate shared capabilities from products and experiences;
- derive significant use cases from real user outcomes;
- prioritize risks that could invalidate P0 or the pedagogical thesis;
- create a glossary that does not confuse roadmap language with current
  contracts;
- reject scope that does not improve a measurable route toward understanding.
