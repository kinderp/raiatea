# Source Citation and User Knowledge Profiles

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Define how Raiatea cites private and public sources, how users discover which materials shaped a body of knowledge, and how a user's learning and research history can be represented without exposing protected source content.

---

## 1. Core principle

Raiatea must never hide the intellectual route that produced a model, explanation, profile, or expedition.

Even when the underlying source is private, protected, purchased, unavailable, or inaccessible to another user, its bibliographic existence and role in the construction of knowledge should remain visible whenever lawful and safe.

> The source may remain private, but its place in the route of understanding should remain visible.

---

## 2. Private sources are cited, not distributed

For a privately owned source, Raiatea should normally share only its reference and contribution role.

Possible shared metadata:

- title;
- author or creator;
- publisher or platform;
- edition or version;
- publication date;
- ISBN, DOI, repository identifier, video ID, or equivalent;
- chapter, section, page, timestamp, commit, or fragment reference;
- language;
- source type;
- acquisition status such as purchased, borrowed, institutionally licensed, or user-created;
- topics supported;
- claims, explanations, or process models derived from it;
- verification status;
- public purchase, library, publisher, or catalogue link when available.

The following remain private unless separately authorised:

- original file;
- full extracted text;
- complete translation;
- OCR output;
- private annotations;
- personal highlights;
- access credentials;
- proof of purchase;
- sensitive ownership information.

---

## 3. Public and openly distributable sources

For public, open-access, public-domain, or compatibly licensed sources, Raiatea may also expose:

- direct download link;
- archive mirror;
- full public text when permitted;
- public transcript;
- repository link;
- dataset link;
- licence;
- integrity hash;
- preserved versions;
- machine-readable citation;
- derived knowledge and verification history.

The interface should make the distinction explicit:

```text
Private source
→ bibliographic reference and lawful access options

Public source
→ bibliographic reference + direct access or download
```

A user should immediately understand whether a source can be opened, purchased, borrowed, requested through a library, or only verified by authorised readers.

---

## 4. Bibliography as part of the knowledge model

A bibliography is not an appendix generated after the explanation. It is part of the explanation itself.

Every expedition, process model, profile, dossier, and living document should support:

- complete source inventory;
- source grouping by topic;
- source grouping by historical phase;
- source grouping by evidential role;
- recommended acquisition order;
- prerequisites;
- foundational versus optional material;
- source conflicts;
- outdated or superseded sources;
- coverage gaps;
- public alternatives to private sources when available.

Example:

```text
Understanding LLM inference

Foundational books
Research papers
Implementation repositories
Lectures and videos
Historical sources
Current discussions
Contrary or critical sources
Sources not yet acquired
```

This allows another user to reconstruct or improve the route rather than merely consume its conclusion.

---

## 5. Source roles

Raiatea should describe why a source matters.

Possible roles include:

- foundational;
- historical;
- primary evidence;
- explanatory;
- technical implementation;
- empirical validation;
- criticism;
- replication;
- contrary evidence;
- contextual;
- spiritual or philosophical interpretation;
- current update;
- superseded but historically important.

A source entry should answer:

```text
Why was this source used?
Which part of the model depends on it?
How strong is that dependence?
Is it replaceable by a public source?
Does it disagree with other sources?
```

---

## 6. User knowledge profile

A Raiatea user may maintain a knowledge profile describing the routes they have explored and the understanding they have constructed.

This is not merely a social profile and should not be reduced to achievements or gamification.

Possible sections:

### Identity and declared interests

- public name or pseudonym;
- biography;
- professional or learning roles;
- interests;
- languages;
- domains followed;
- declared goals.

### Knowledge timeline

A chronological record of:

- expeditions started;
- expeditions completed;
- important sources studied;
- concepts mastered or questioned;
- models constructed;
- position changes;
- experiments performed;
- contributions accepted;
- corrections made;
- unresolved questions;
- followed domains and people.

### Topic map

The same history organised by topic rather than time:

```text
Artificial Intelligence
├── Machine Learning
├── Deep Learning
├── Transformers
├── LLM Inference
└── AI Safety
```

Each topic may show:

- current level of understanding;
- completed routes;
- active routes;
- public contributions;
- source bibliography;
- open questions;
- models built;
- last meaningful update.

### Constructed knowledge

The profile may expose knowledge artefacts created by the user:

- explanations;
- process models;
- timelines;
- research notes;
- reading paths;
- verified corrections;
- public experiments;
- translations reviewed;
- bibliographies;
- dossiers;
- minority reports.

### Source trail

For each public artefact, the profile can show which sources contributed to it.

Private sources appear as citations only. Public sources include access links where permitted.

---

## 7. Public, shared, and private profile layers

The user controls visibility independently for each layer.

### Private layer

May include:

- exact reading history;
- owned books;
- private notes;
- learning weaknesses;
- political or spiritual interests;
- unfinished hypotheses;
- detailed activity timestamps.

### Shared group layer

May be visible to:

- class;
- research group;
- newsroom;
- organisation;
- selected collaborators.

### Public layer

May include:

- chosen biography;
- topics explored;
- public expeditions;
- public contributions;
- bibliographies;
- models;
- explanations;
- verified expertise evidence;
- optional source citations.

The system must not automatically reveal that a user owns or read a sensitive source.

A private source can support a public artefact while the contributor remains anonymous or while the exact ownership relation remains hidden.

---

## 8. Profiles as navigable routes

A public knowledge profile should allow another user to follow a route.

Example:

```text
User profile
→ topic: LLM inference
→ chronological route
→ key concepts
→ sources used
→ public source links
→ private-source citations
→ constructed models
→ corrections and discussions
→ start a similar expedition
```

This turns profiles into reusable educational and research infrastructure.

A user should be able to choose:

- follow this person;
- follow this topic within the person's work;
- clone the public structure of an expedition;
- acquire the cited bibliography;
- substitute inaccessible private sources with alternatives;
- receive future updates to the route.

---

## 9. Acquisition guidance

Raiatea should help users decide which sources to obtain.

For each cited private source, it may show:

- why it is useful;
- which concepts it covers;
- prerequisites;
- estimated difficulty;
- time commitment;
- relationship to other sources;
- whether a newer edition exists;
- whether an open alternative exists;
- purchase, publisher, library, or legal access options;
- whether other users independently verified the derived claims.

The objective is not to promote consumption indiscriminately. It is to make the provenance route reproducible.

---

## 10. Example

A user completes an expedition on transformer inference using:

- two purchased Manning books;
- three open-access papers;
- a public GitHub repository;
- five YouTube lectures;
- personal experiments.

Their public profile may show:

```text
Expedition: Understanding Transformer Inference

Constructed knowledge
- timeline of inference optimisation
- process model of memory bottlenecks
- comparison of KV-cache strategies
- three reproducible experiments

Private cited sources
- Book A, edition, chapters 3–6
- Book B, edition, chapter 8

Public sources
- Paper 1 [open]
- Paper 2 [open]
- Repository [open]
- Lecture playlist [open]

Start this route
- use the same bibliography
- replace private books with suggested open alternatives
- purchase or borrow the cited books
```

No protected text or complete translation is published.

---

## 11. Architectural implications

This requirement introduces or strengthens the following domain concepts:

- `SourceReference`;
- `AccessPolicy`;
- `SourceRole`;
- `Bibliography`;
- `KnowledgeProfile`;
- `KnowledgeTimeline`;
- `TopicPortfolio`;
- `PublicContribution`;
- `ExpeditionTemplate`;
- `AcquisitionRecommendation`;
- `VerificationAttestation`.

A source reference must be addressable independently of the private source object.

```text
Private Source Object
        ↓ supports
Public Source Reference
        ↓ supports
Derived Knowledge Artefact
        ↓ appears in
Expedition and User Knowledge Profile
```

---

## 12. Principles

1. A public explanation must reveal its source route.
2. A private source is cited, not distributed.
3. A public source should be directly accessible when law and licence permit.
4. Bibliographies are first-class knowledge objects.
5. Profiles represent journeys and contributions, not social popularity.
6. Users control whether their reading and ownership history is public.
7. Another person should be able to reproduce a route by acquiring the cited sources or choosing lawful alternatives.
8. Raiatea should distinguish expertise demonstrated through work from reputation based on followers.

---

## 13. Provisional decision

Raiatea will expose, for each shared knowledge artefact, the bibliography and source roles that contributed to it.

Private sources will appear only as references and lawful acquisition guidance. Public sources will include direct access or download links where permitted.

Users may publish a chronological and topic-based knowledge profile containing routes, models, contributions, and bibliographies, while retaining granular control over private reading history and source ownership.

> Raiatea should make the journey reproducible without giving away the traveller's private library.
