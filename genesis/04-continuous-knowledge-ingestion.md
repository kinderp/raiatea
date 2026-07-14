# Continuous Knowledge Ingestion

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Created:** 2026-07-14

## Purpose

Define Raiatea as a continuously updated knowledge system rather than a static archive.

## Core idea

Raiatea must continuously observe selected sources, acquire new material through authorized means, preserve the original evidence, detect changes, extract structured information, and update its models of domains, people, claims, events, and trends.

It must not simply accumulate documents. It must transform incoming material into traceable, revisable, time-aware knowledge.

## Continuous cycle

```text
Discover
→ Acquire
→ Preserve
→ Parse
→ Segment
→ Extract
→ Reconcile
→ Evaluate
→ Integrate
→ Review
→ Recompute
→ Notify
```

## Source families

Raiatea should support, through independent source adapters:

- books and ebooks;
- scanned books and historical archives;
- papers, preprints, conference proceedings, and datasets;
- official documents, laws, treaties, reports, and institutional records;
- websites, blogs, RSS feeds, and news outlets;
- GitHub repositories, commits, issues, pull requests, releases, and discussions;
- YouTube videos, podcasts, interviews, and transcripts;
- X, LinkedIn, Reddit, Hacker News, forums, and public social conversations;
- newsletters, email archives, and mailing lists;
- user-provided notes, documents, recordings, and observations.

## Acquisition constraints

“Continuous acquisition” does not mean indiscriminate scraping or unauthorized downloading.

Every Source Provider must declare:

- permitted acquisition method;
- authentication requirements;
- applicable API or feed;
- rate limits;
- license and terms of use;
- retention policy;
- whether full content, excerpts, metadata, or links may be stored;
- whether downstream sharing is allowed;
- whether deletion or correction requests must be propagated.

Raiatea should prefer official APIs, feeds, licensed datasets, user uploads, and explicitly permitted archives.

## Preservation layers

Incoming content must remain separated into distinct layers:

```text
Original artifact
Raw extraction
Normalized representation
Structured entities and claims
AI-generated interpretation
Human-reviewed synthesis
```

No transformation may silently replace the layer before it.

## Change detection

Raiatea must treat change as a first-class event.

Examples:

- a paper is revised;
- a post is edited or deleted;
- a public figure changes a statement;
- a repository releases a new version;
- a news article changes its headline;
- a scientific claim is replicated, corrected, or retracted;
- a law or policy enters into force;
- a video transcript is corrected.

The previous state must remain recoverable.

## From content to knowledge

The ingestion pipeline should extract candidate:

- entities;
- concepts;
- claims;
- events;
- actions;
- decisions;
- relationships;
- causes and contributing factors;
- evidence and counter-evidence;
- predictions;
- changes of position;
- conflicts of interest;
- references to papers, people, organizations, repositories, and other sources.

These outputs are hypotheses produced by the pipeline, not automatically accepted truths.

## Reconciliation

New material must be compared with existing knowledge to determine whether it:

- confirms an existing claim;
- contradicts it;
- narrows or expands its scope;
- changes its confidence;
- introduces a new interpretation;
- creates a new event;
- changes a person’s position timeline;
- updates a field map or reading path;
- invalidates a previous recommendation.

## Prioritization

Raiatea cannot process the entire world with equal depth.

It must prioritize sources according to:

- user-selected fields and people;
- relevance to active expeditions;
- authority and originality of the source;
- novelty;
- expected impact;
- uncertainty reduction;
- recency;
- risk of manipulation;
- available rights and processing cost.

## Knowledge sensors

A source adapter retrieves content. A knowledge sensor observes a domain continuously and produces events.

Examples:

```text
PaperSensor
RepositorySensor
NewsSensor
YouTubeSensor
SocialSensor
PersonSensor
PolicySensor
RetractionSensor
```

Sensors should be configurable, pausable, auditable, and replaceable.

## Notifications

Raiatea should notify users only when incoming material meaningfully changes their map.

Examples:

- a foundational paper is corrected;
- a tracked person changes position;
- new evidence weakens a prior conclusion;
- a new source closes an important evidence gap;
- a field develops a new research direction;
- an active reading path should be revised.

The goal is not more notifications. It is less noise and more orientation.

## Integrity

Every acquired artifact should receive:

- content hash;
- acquisition timestamp;
- source identifier;
- acquisition method;
- rights metadata;
- parser and model versions;
- transformation history;
- transparency-log inclusion proof where applicable.

The transparency log proves that a representation existed in a given form at a given time. It does not prove that the representation is true.

## Human contribution

Users may contribute:

- missing sources;
- corrected transcripts;
- alternative interpretations;
- experiments;
- annotations;
- relationship proposals;
- contradiction reports;
- historical context;
- new field maps.

Shared contributions must enter a review workflow and preserve authorship, evidence, confidence, and dissent.

## Architectural implication

Continuous ingestion requires at least:

```text
Source Registry
Scheduler
Source Providers
Knowledge Sensors
Rights Policy Manager
Raw Artifact Store
Parsing and OCR Layer
Transcription Layer
Semantic Extraction Layer
Entity Resolution
Claim and Event Store
Temporal Knowledge Graph
Transparency Log
Review Queue
Notification Engine
```

## Principle

> Raiatea does not continuously download the world. It continuously observes selected parts of the world, preserves what it is allowed to preserve, and updates its maps when the evidence changes.

## Open questions

- How should source selection balance breadth and depth?
- How should Raiatea detect coordinated manipulation across platforms?
- Which transformations require mandatory human review?
- How long should raw source material be retained?
- How should deletions and legal removal requests affect historical provenance?
- How should source trust evolve after corrections, retractions, or repeated errors?
- How should the system avoid reinforcing popularity bias?
