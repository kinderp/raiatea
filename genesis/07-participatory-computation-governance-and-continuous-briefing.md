# Participatory Computation, Governance, and Continuous Briefing

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Define how Raiatea users contribute computing resources, influence knowledge construction, discuss disagreements, and remain continuously updated after completing an expedition.

---

## 1. Core idea

Raiatea should not be only a system used by a community. It should be a system partially built, verified, maintained, and improved by that community.

Users may contribute:

- attention;
- expertise;
- observations;
- corrections;
- discussion;
- storage;
- bandwidth;
- CPU, GPU, and accelerator time;
- replication and verification work.

The analogy with Bitcoin is useful only at a high level: many independent participants contribute resources to maintain a shared system. Raiatea should not imitate proof-of-work or deliberately waste computation. Its computation must perform useful knowledge work.

> Raiatea does not mine coins. It mines structure, evidence, context, and understanding.

---

## 2. Participatory computation

A Raiatea node may voluntarily accept tasks from the network according to the user's preferences, hardware, energy limits, privacy policy, and trust level.

Possible task classes include:

### 2.1 Acquisition tasks

- fetch an authorized public source;
- mirror an open-access paper;
- preserve an approved public artifact;
- check whether a source changed or disappeared;
- verify links and identifiers.

### 2.2 Extraction tasks

- OCR scanned pages;
- transcribe user-authorized audio or video;
- detect document layout;
- reconstruct tables;
- recognize formulas;
- segment chapters, sections, and claims;
- extract references and citations.

### 2.3 Knowledge construction tasks

- entity recognition;
- entity resolution;
- claim extraction;
- event extraction;
- temporal ordering;
- topic classification;
- relation proposal;
- contradiction detection;
- source clustering;
- summary generation;
- translation;
- construction of candidate process models.

### 2.4 Verification tasks

- rerun extraction with a different model;
- compare OCR outputs;
- verify a quotation against its source;
- reproduce a calculation;
- validate a citation;
- detect tampering;
- check whether a derived statement is supported by the referenced fragment;
- compare independent source families.

### 2.5 Storage and network tasks

- pin public knowledge bundles;
- replicate transparency-log checkpoints;
- maintain indexes for selected domains;
- serve public artifacts within policy limits;
- participate in distributed search and routing.

---

## 3. Useful work instead of proof-of-work

Raiatea should use a useful-work model rather than proof-of-work.

A task is useful only if its result can be inspected, reproduced, compared, or reused.

Each task should include:

```yaml
job_id: stable identifier
input_hashes: content-addressed inputs
task_type: ocr | transcription | extraction | verification | storage | other
required_capabilities: cpu | gpu | memory | model | language
privacy_class: public | private-local-only | confidential-federated
expected_output_schema: versioned schema
verification_policy: redundancy | challenge | expert_review | deterministic
energy_budget: optional
reward_policy: contribution_credit | reputation | reciprocity | none
```

The first versions of Raiatea should avoid monetary tokens. Incentives can initially be:

- visible contribution history;
- domain reputation;
- reciprocal access to community compute;
- priority for processing personal expeditions;
- acknowledgements;
- badges based on verified work;
- participation in governance;
- direct usefulness to the contributor.

A token or payment system, if ever considered, must be treated as a separate economic and legal research problem.

---

## 4. Preventing malicious or low-quality computation

Distributed computation creates an adversarial environment. A node may be faulty, compromised, careless, or intentionally malicious.

No single untrusted result should silently become canonical knowledge.

Raiatea should combine:

- deterministic tasks where possible;
- content hashes;
- signed outputs;
- sandboxed execution;
- redundant assignment to independent nodes;
- random spot checks;
- comparison between different models and implementations;
- challenge tasks with known answers;
- reputation based on verifiable history;
- human review for consequential claims;
- immutable provenance and rollback.

For example:

```text
Scanned page
→ OCR by node A
→ OCR by node B
→ disagreement detected
→ OCR by node C or human review
→ accepted transcription with confidence and all variants preserved
```

Agreement between nodes increases confidence in execution, not necessarily truth. Several nodes can reproduce the same error if they share the same model or source.

---

## 5. Community influence over Raiatea's knowledge

Users must be able to challenge what Raiatea constructs.

They should be able to:

- question a claim;
- add missing evidence;
- propose an alternative interpretation;
- identify a false equivalence;
- challenge a causal relation;
- report an outdated model;
- suggest a missing topic, actor, event, or source;
- dispute a translation or transcription;
- propose a different path through a domain;
- request reprocessing with another method.

However, popularity must not determine truth.

A statement does not become true because most users vote for it, and an unpopular claim must not disappear when it has strong evidence.

Community governance should decide:

- what deserves investigation;
- which sources should be acquired;
- which models require review;
- how interfaces and taxonomies evolve;
- which unresolved disputes should be highlighted;
- how shared resources are allocated.

Evidence and transparent argumentation should determine the epistemic status of claims.

---

## 6. Public deliberation

Every important object should support a public deliberation space when policy permits:

- concept;
- claim;
- event;
- process model;
- public profile;
- expedition;
- translation;
- timeline;
- forecast;
- evidence bundle.

A discussion should not be a flat comment stream. It should be structured around contributions such as:

```text
Question
Evidence for
Evidence against
Alternative explanation
Source criticism
Method criticism
Conflict of interest
Missing data
Suggested experiment
Proposed revision
Minority report
```

Participants should be able to cite exact source fragments and model versions.

The result of deliberation may be:

- consensus;
- provisional consensus;
- multiple compatible interpretations;
- unresolved disagreement;
- evidence insufficient;
- forked models;
- superseded conclusion.

Raiatea must preserve dissent when it is reasoned and sourced.

> Convergence is desirable when evidence supports it, but forced convergence destroys knowledge.

---

## 7. Governance without an authority of truth

Raiatea needs governance, but governance must not become a centralized authority that declares truth.

A possible layered model is:

### Layer 1 — Personal

The user controls private corpus, notes, models, subscriptions, and local priorities.

### Layer 2 — Community

Domain communities curate sources, discuss models, review contributions, and allocate voluntary computation.

### Layer 3 — Expert review

Qualified reviewers examine high-impact or highly technical disputes. Expertise must be transparent, challengeable, and domain-specific.

### Layer 4 — Protocol governance

The wider project governs schemas, protocols, security, interoperability, and minimum provenance requirements.

### Layer 5 — Independent witnesses

Independent nodes mirror transparency logs, detect equivocation, and preserve public history.

Different communities may maintain different interpretations while sharing the same underlying evidence graph.

---

## 8. Expeditions must enrich the shared network

When an expedition causes Raiatea to discover new sources, extract new claims, construct a new process model, or identify a contradiction, the result should be eligible to improve future expeditions.

The flow should be:

```text
Private expedition
→ new observation or model
→ local draft
→ rights and privacy filtering
→ user consent
→ knowledge contribution
→ automated checks
→ community or expert review
→ signed knowledge bundle
→ federation
→ future expeditions benefit
```

Private data, copyrighted full text, personal notes, and sensitive material remain private unless the user explicitly and lawfully shares them.

The shared network receives only what may be distributed, such as:

- derived claims;
- public references;
- source coordinates;
- process relations;
- uncertainty;
- summaries written for redistribution;
- corrections;
- model metadata;
- verification results.

---

## 9. An expedition never truly ends

Completing a learning or research path should produce a stable understanding snapshot, not detach the user from the field.

Every completed expedition may become a **watchable route**.

The user chooses:

- daily briefing;
- weekly briefing;
- monthly review;
- only major changes;
- custom event conditions;
- no updates.

Raiatea continuously observes the relevant field and evaluates whether new material changes the user's existing map.

It should not merely report everything published. It should answer:

- What changed?
- Why does it matter?
- Which part of my previous understanding is affected?
- Is this confirmation, contradiction, correction, extension, or noise?
- Which source deserves my limited attention?
- Does my reading path need revision?
- Did an important person change position?
- Was a paper retracted, replicated, or superseded?
- Did a forecast resolve?

---

## 10. Personal continuous briefing

Raiatea should provide a daily or weekly knowledge briefing that replaces much of the time users spend manually checking blogs, social feeds, journals, newsletters, repositories, and news sites.

A briefing may contain:

```text
Major changes to followed expeditions
New evidence affecting existing models
Important papers and why they matter
Relevant public statements and position changes
New releases, datasets, laws, or standards
Corrections, retractions, and failed replications
Open disputes that gained new evidence
Recommended reading, watching, or experiments
Items intentionally omitted as low-value noise
```

The briefing must be personalized by:

- completed expeditions;
- current goals;
- existing understanding;
- available time;
- preferred depth;
- professional role or current intention;
- trusted and excluded sources;
- tolerance for uncertainty and novelty.

A five-minute briefing and a two-hour research review may be generated from the same underlying changes.

---

## 11. Attention as a scarce resource

Raiatea should optimize not for engagement, scrolling time, or notification frequency, but for **knowledge value per unit of human attention**.

A candidate update may be ranked by:

- novelty;
- evidential strength;
- impact on existing models;
- relevance to the user's goals;
- urgency;
- irreversibility;
- source independence;
- expected learning value;
- cost in reading time;
- uncertainty reduction.

Raiatea should explicitly say when nothing important changed.

> A day without a notification can be evidence that the system respected the user's attention.

---

## 12. Proposed bounded contexts introduced by this note

This proposal suggests at least three bounded contexts.

### Distributed Compute

Owns:

- node capabilities;
- job scheduling;
- execution receipts;
- resource budgets;
- redundancy;
- verification;
- contribution credit.

### Deliberation and Governance

Owns:

- proposals;
- discussions;
- reviews;
- disputes;
- consensus status;
- forks;
- governance rules;
- reviewer credentials.

### Continuous Intelligence

Owns:

- followed expeditions;
- watch policies;
- change detection;
- significance scoring;
- daily and weekly briefings;
- notification thresholds;
- update explanations.

These contexts interact with ingestion, provenance, knowledge modeling, identity, rights, and federation, but should not be collapsed into them.

---

## 13. Principles

1. **Computation must produce inspectable knowledge work, not artificial scarcity.**
2. **No untrusted node can silently alter shared knowledge.**
3. **Popularity can prioritize investigation but cannot establish truth.**
4. **Disagreement must be structured, sourced, and preserved.**
5. **Users decide whether discoveries from private expeditions become shared contributions.**
6. **Completed expeditions remain connected to future change.**
7. **Briefings optimize for understanding and attention saved, not engagement.**
8. **Raiatea may converge on models, but it must also support principled forks.**

---

## 14. Open questions

- How are compute tasks scheduled without creating a central coordinator?
- Which tasks can safely run on anonymous nodes?
- How are private computations performed without exposing source content?
- Can trusted execution environments, secure aggregation, or zero-knowledge methods help?
- How is reputation made resistant to Sybil attacks and wealthy actors?
- Should contribution credit ever have monetary value?
- How are expert credentials verified without creating closed elites?
- What minimum evidence is required before a claim becomes shared?
- How are hostile coordinated communities prevented from overwhelming deliberation?
- How should minority reports be surfaced without creating false balance?
- How is significance calculated for daily briefings?
- Can users inspect why an update was included or omitted?
- How are computational energy and environmental costs budgeted?

---

## 15. Provisional formulation

> Raiatea is a participatory knowledge network in which people contribute evidence, judgment, discussion, storage, and useful computation. The network preserves disagreement, verifies contributions, continuously updates completed expeditions, and returns the most meaningful changes to each user in a briefing designed to save attention rather than capture it.
