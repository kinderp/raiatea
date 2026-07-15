# Federated Knowledge Network

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Explore how knowledge discovered by one Raiatea user can become part of a shared, resilient, verifiable network without forcing every node to hold every private or restricted source.

## Core question

When an explorer investigates a domain, Raiatea may discover new sources, extract previously unseen evidence, build new models, identify relationships, or revise an existing explanation.

How should this new knowledge become available to other explorers?

## Foundational hypothesis

Raiatea should not be designed as one central database containing all knowledge, nor as a collection of isolated personal notebooks.

It should evolve toward a **federated knowledge network** in which:

- private corpora remain under user control;
- shareable knowledge can propagate across nodes;
- every contribution retains provenance, authorship, transformations, confidence, and review history;
- no single operator is required to possess or control the entire knowledge base;
- nodes can reconstruct a useful global view from distributed fragments;
- the network can detect tampering, conflicting histories, and selective rewriting.

## What must be shared

When a journey creates new knowledge, the system should distinguish at least four layers.

### 1. Private source material

Examples:

- purchased books;
- private documents;
- personal notes;
- restricted transcripts;
- private messages;
- unpublished research.

This material remains private unless its owner explicitly grants access.

### 2. Source references and attestations

Shareable records may include:

- title, author, date, identifiers, and canonical URL;
- content hash;
- acquisition timestamp;
- licence and access policy;
- page, timestamp, or fragment coordinates;
- proof that a particular version was observed;
- independent attestations by other nodes.

These records can be shared even when the full source cannot be redistributed.

### 3. Derived knowledge

Examples:

- concepts;
- entities;
- claims;
- events;
- timelines;
- process models;
- causal hypotheses;
- contradictions and consistencies;
- summaries and explanations written in original form;
- uncertainty assessments;
- links between sources and models.

This is the main shareable layer of Raiatea.

### 4. Personal learning state

Examples:

- what the explorer has studied;
- private doubts;
- annotations;
- personal hypotheses;
- preferences and goals.

This remains private by default and is shared only by explicit choice.

## Contribution flow

A new discovery should not silently overwrite shared knowledge.

A possible flow is:

```text
local observation
→ local extraction
→ candidate contribution
→ provenance and integrity checks
→ licence and privacy checks
→ peer or expert review when required
→ signed knowledge bundle
→ network publication
→ replication and indexing
→ later correction or supersession
```

A contribution is therefore closer to a signed pull request than to an anonymous edit.

## Knowledge bundles

The unit of exchange should not be an entire database. It should be a portable, signed **Knowledge Bundle**.

A bundle may contain:

```text
Bundle identity
Contributor identity or pseudonymous key
Creation time
Source references
Content hashes
Extracted claims
Entities and events
Relations
Process or causal hypotheses
Confidence values
Rights metadata
Review records
Dependencies on previous bundles
Supersedes / contradicts / confirms links
Digital signature
```

Bundles should be content-addressed, immutable after publication, and superseded rather than overwritten.

## Distribution alternatives

### Alternative A — Every node stores everything

Advantages:

- simple global queries;
- high redundancy;
- every node can operate independently.

Problems:

- unrealistic storage and bandwidth growth;
- privacy and licensing conflicts;
- unnecessary replication of large media;
- difficult deletion and retention requirements;
- many users do not need the full corpus.

This should not be the default.

### Alternative B — Every node stores only one fragment

Advantages:

- no single node holds the whole dataset;
- storage cost is distributed;
- resilient to some forms of central control.

Problems:

- data availability depends on enough replicas remaining online;
- difficult offline use;
- expensive global queries;
- complicated access control and deletion;
- an adversary may target rare fragments;
- distributing encrypted fragments does not by itself solve key management or legal responsibility.

This may be useful for selected public data, but not as the only model.

### Alternative C — Hybrid replication and sharding

This is the current preferred direction.

Each node may keep:

- its complete private corpus;
- a local working set of domains it follows;
- widely replicated public metadata and knowledge bundles;
- selected cached or pinned public source artefacts;
- indexes sufficient to discover bundles stored elsewhere;
- compact summaries of remote parts of the graph.

Large public artefacts can be content-addressed and replicated by interested nodes. Rare but important material can be deliberately pinned by libraries, universities, journalists, communities, or preservation nodes.

## Inspiration from IPFS

IPFS demonstrates useful principles for Raiatea:

- content-based rather than location-based identity;
- Merkle-DAG structures;
- retrieval from any peer that possesses a matching block;
- deduplication of identical content;
- separation between naming, discovery, and storage.

IPFS alone is not a knowledge system. It does not decide which evidence is trustworthy, how claims relate, or how conflicting interpretations should be represented. Raiatea may use IPFS or a similar content-addressed layer as one storage adapter, not as its complete architecture.

## Inspiration from Netsukuku

Netsukuku explored hierarchical and recursive network organisation to avoid every routing node storing a flat global routing table.

The relevant inspiration is not to copy its routing protocol directly, but to ask whether Raiatea can maintain **multi-resolution knowledge indexes**:

```text
local detailed knowledge
→ domain-level summaries
→ summaries of domain clusters
→ compact global navigation index
```

A node interested in AI inference might keep high-resolution data for that domain, medium-resolution summaries for adjacent fields, and only a compact global index for the rest of Raiatea.

This resembles a map with multiple zoom levels more than a single flat database.

## Multi-resolution knowledge representation

A distributed node should not need every raw fact in order to know that relevant knowledge exists elsewhere.

Possible levels:

1. **Global index** — fields, actors, time ranges, bundle identifiers, availability, trust and rights metadata.
2. **Domain summary** — principal concepts, processes, debates, timelines, and high-value sources.
3. **Detailed graph** — claims, evidence, events, model versions, and relations.
4. **Source fragments** — text, OCR, transcript segments, tables, images, and code.
5. **Original artefacts** — complete files where storage and access are permitted.

The lower levels can be fetched only when needed.

## Replication policy

Replication should be determined by several factors:

- public value;
- rarity;
- legal permission;
- expected demand;
- historical importance;
- risk of disappearance;
- geographic and organisational diversity;
- user subscriptions and domain interests;
- minimum desired replica count.

Knowledge should not survive merely because it is popular. Preservation policies must also protect rare, dissenting, historical, and low-traffic material.

## Synchronisation and conflict

Raiatea should preserve divergent contributions rather than forcing premature consensus.

CRDTs may be useful for some collaborative structures where replicas must converge after concurrent updates, such as:

- sets of references;
- annotations;
- tags;
- subscriptions;
- some graph edges;
- collaborative drafts.

They should not automatically merge competing factual or causal claims into one truth. Conflicting claims must coexist with their evidence and provenance.

The network needs both:

- deterministic convergence for suitable data structures;
- explicit pluralism for disputed knowledge.

## Integrity and transparency

Every published bundle should be signed and included in an append-only transparency log.

Nodes should be able to verify:

- who or which key published it;
- whether its bytes changed;
- which sources and transformations produced it;
- whether it was later corrected or superseded;
- whether different nodes were shown inconsistent histories;
- whether sufficient independent replicas exist.

The transparency log establishes publication history, not truth.

## Trust without a single authority

Raiatea should not require one universal trust score.

Trust may be contextual and user-selectable:

- scientific review networks;
- journalistic verification networks;
- educational curators;
- public institutions;
- domain experts;
- community reviewers;
- personal trust lists;
- algorithmic evidence-quality indicators.

Different communities may maintain different canonical views over the same immutable contribution history.

## Privacy and selective disclosure

A user must be able to contribute derived knowledge without exposing the complete private source corpus.

Examples:

- publish a claim and citation coordinates without publishing the purchased book;
- publish an experiment and its results without exposing personal notes;
- publish a source hash and attestation while restricting the source bytes;
- share a bundle only with a research group;
- later revoke access to private material without rewriting already public derived claims.

## Offline and local-first operation

A Raiatea node should remain useful without permanent network access.

It should be able to:

- search its local corpus and cached knowledge;
- continue a journey;
- create new candidate bundles;
- maintain a local transparency history;
- synchronise when connectivity returns;
- reconcile concurrent contributions without losing their provenance.

## Current architectural direction

```text
Private Corpus per user or organisation
        +
Local-first Raiatea node
        +
Signed immutable Knowledge Bundles
        +
Federated discovery and exchange
        +
Content-addressed distributed artefact storage
        +
Multi-resolution distributed indexes
        +
CRDTs for selected collaborative structures
        +
Append-only transparency logs
        +
Plural review and trust networks
```

## Preliminary principle

> Knowledge discovered during one journey should be able to improve later journeys, but sharing must preserve rights, privacy, provenance, uncertainty, and the possibility of disagreement.

## Decisions not yet made

- Whether Raiatea should use IPFS directly or define a storage abstraction with multiple adapters.
- Whether all public knowledge bundles should be globally replicated or selectively replicated.
- How to guarantee availability for unpopular but important bundles.
- Which structures are safe to model as CRDTs.
- How multi-resolution graph summaries are generated and verified.
- Whether nodes should exchange full graph partitions, event logs, bundles, or all three.
- How identities and pseudonymous contributors are managed.
- How moderation works without recreating a central authority.
- How lawful deletion interacts with immutable public histories.
- How communities form and publish alternative canonical views.
- How incentives for storage, review, and preservation should work.

## Research questions

1. Can a knowledge graph be indexed recursively in a way analogous to hierarchical routing while preserving semantic usefulness?
2. Can compact domain summaries prove which detailed bundles they represent through Merkle commitments?
3. What minimum metadata must every node hold to navigate the global network?
4. How can a node evaluate a remote model without downloading all underlying sources?
5. How should replication policies balance popularity, rarity, diversity, and preservation?
6. Can users contribute useful derived knowledge while revealing only the minimum necessary source information?
7. How can multiple, disagreeing canonical views coexist over one shared immutable evidence history?

## Next validation step

Build a paper design for a small federation of five nodes:

- one personal learner node;
- one university node;
- one journalism node;
- one public preservation node;
- one domain community node.

Simulate:

1. a learner discovers a new paper;
2. the paper is legally shareable;
3. the learner extracts claims and a process model;
4. the contribution is signed and reviewed;
5. the artefact and derived bundle are distributed;
6. another node retrieves only the summary first;
7. a later paper contradicts one claim;
8. both histories remain inspectable;
9. one node goes offline without losing availability;
10. a private purchased book contributes derived knowledge without exposing its full text.
