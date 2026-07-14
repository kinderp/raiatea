# Evidence Integrity and User Contribution

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Created:** 2026-07-14  

## Purpose

This document defines how Raiatea should behave when evidence is incomplete, how it should preserve the integrity of acquired data, and how discoveries made by users should become part of the shared knowledge system.

## Foundational question

> What should Raiatea do when the route is uncertain, the available evidence may be manipulated, and explorers discover new information during the journey?

## 1. When there is not enough evidence

Raiatea must never manufacture a complete route from incomplete data.

When the available evidence is insufficient, the system should enter a **reconnaissance state** rather than pretending that a reliable explanation already exists.

A reconnaissance state should make visible:

- what is known;
- what is only claimed;
- what is inferred;
- what is disputed;
- what is missing;
- which sources would reduce uncertainty;
- which questions cannot yet be answered responsibly.

The system should be able to say:

> There is not enough evidence to support a reliable conclusion. These are the missing observations, documents, testimonies, measurements, or replications needed to continue.

An expedition may therefore have several states:

```text
ready
reconnaissance_required
evidence_incomplete
conflicting_evidence
temporarily_blocked
open_question
```

Lack of evidence is not failure. It is itself useful knowledge.

## 2. Evidence must remain separable from interpretation

Raiatea must preserve a strict distinction between:

```text
raw source
extracted fragment
normalized representation
claim
interpretation
causal hypothesis
summary
recommendation
```

A later interpretation must never silently replace the original source.

Corrections, normalizations, translations, summaries, and AI-generated transformations must be stored as additional layers with their own provenance.

## 3. Protecting data integrity

Raiatea cannot guarantee that a source is truthful merely because it has been stored correctly. It can, however, guarantee that the stored representation has not been silently altered after acquisition.

For every acquired source or fragment, the system should preserve when legally and technically possible:

- source identifier and canonical location;
- acquisition timestamp;
- publication timestamp;
- content hash;
- source metadata;
- acquisition method;
- parser and model versions;
- transformation history;
- digital signature when available;
- archive snapshot or authorized reference;
- chain of custody;
- access and rights policy.

The raw acquired object should be immutable or append-only.

If a source later changes, Raiatea should preserve both versions and represent the change as an event.

```text
Source version A
        ↓ modified at time T
Source version B
```

The system must never overwrite history merely because a webpage, post, document, or public statement has been edited or deleted.

## 4. Authenticity is different from truth

Raiatea must distinguish at least four questions:

1. **Integrity:** Is this stored object unchanged since acquisition?
2. **Authenticity:** Did it originate from the claimed source or author?
3. **Accuracy:** Does the claim correspond to available evidence?
4. **Interpretation:** What meaning or causal explanation should be assigned to it?

A cryptographic hash can support integrity. It cannot prove truth.

An official account can support authenticity. It cannot guarantee accuracy.

A widely repeated statement can indicate diffusion. It cannot prove independent confirmation.

## 5. Independent corroboration

Important claims should not be promoted to canonical knowledge solely because they appear frequently.

Raiatea should detect when many sources depend on the same origin.

```text
100 articles
   ↓
3 news agencies
   ↓
1 original anonymous claim
```

The system should prefer independent corroboration over raw repetition.

For every significant claim it should show:

- primary sources;
- independent confirmations;
- dependent repetitions;
- counter-evidence;
- unresolved conflicts;
- confidence in extraction;
- confidence in attribution;
- confidence in the claim itself.

## 6. Contradictions must be preserved

Conflicting evidence should not be deleted or averaged into a misleading consensus.

Raiatea should maintain a contradiction ledger containing:

- the competing claims;
- their sources;
- their dates and contexts;
- the evidence supporting each;
- possible explanations for the conflict;
- the current resolution status.

```text
unresolved
partially_resolved
resolved_by_new_evidence
contextual_difference
source_error
possible_manipulation
```

## 7. User discoveries are part of the voyage

An explorer may discover:

- a missing source;
- a factual error;
- a new relation;
- a contradiction;
- an overlooked person;
- a better explanation;
- an experiment;
- a failed reproduction;
- an original hypothesis;
- a personal insight.

These discoveries should not remain trapped in a private interaction, but they should also not automatically become canonical knowledge.

Raiatea therefore needs three distinct layers.

### 7.1 Private Journal

The user's personal record of:

- what they studied;
- what they understood;
- questions;
- doubts;
- reflections;
- unfinished hypotheses;
- personal decisions;
- learning progress.

This layer is private by default.

### 7.2 Field Notes

Structured notes that the user intentionally chooses to share with a group, class, research team, or community.

A field note may include:

- observation;
- source reference;
- explanation;
- reproduction attempt;
- correction proposal;
- open question;
- confidence;
- scope and limitations.

### 7.3 Knowledge Contribution

A formal proposal to add or modify shared knowledge.

A contribution should contain:

```yaml
contributor:
contribution_type:
claim_or_relation:
sources:
evidence:
method:
confidence:
known_limitations:
conflicts:
license:
submitted_at:
```

It should move through explicit states:

```text
draft
submitted
automatically_checked
community_reviewed
expert_reviewed
accepted
accepted_with_reservations
rejected
deprecated
superseded
```

## 8. Canonical knowledge must not be edited directly

Users should propose changes rather than silently rewriting shared knowledge.

The canonical graph should be updated through versioned contribution events, preserving:

- previous versions;
- contributor identity or approved pseudonymity;
- review decisions;
- supporting evidence;
- dissenting interpretations;
- rollback capability.

This resembles a pull request more than an editable wiki page.

## 9. Reputation must be contextual and evidence-based

Raiatea should not assign a single global credibility score to a person.

A contributor may be reliable in one domain and inexperienced in another.

Reputation signals should therefore be contextual:

- domain expertise;
- history of corrections;
- quality of cited evidence;
- successful reproductions;
- transparency about uncertainty;
- peer review history;
- conflicts of interest;
- contribution acceptance rate;
- willingness to revise claims.

Reputation should help prioritize review, never replace evidence.

## 10. The system must make manipulation harder

Raiatea should detect and expose patterns such as:

- coordinated repetition;
- circular citation;
- source laundering;
- edited or deleted claims;
- fabricated provenance;
- forged media indicators;
- selective quotation;
- context removal;
- conflicts of interest;
- artificial popularity;
- sudden narrative synchronization.

It should describe the detected pattern and its evidence without automatically declaring malicious intent where intent cannot be established.

## 11. Recommendations under uncertainty

Raiatea may still suggest a route when evidence is incomplete, but the recommendation must expose its basis.

A recommendation should include:

- objective;
- current evidence;
- uncertainty;
- alternatives;
- expected benefit;
- possible risks;
- what new evidence could change the recommendation.

> Raiatea may recommend a route through uncertain waters, but it must never hide the fog.

## 12. Architectural implications

These principles imply the need for:

- immutable raw source storage;
- content-addressed objects or hashes;
- append-only provenance events;
- source versioning;
- claim and evidence entities;
- contradiction tracking;
- contribution workflows;
- private and shared knowledge spaces;
- review policies;
- contextual reputation;
- audit trails;
- rollback;
- rights and privacy controls;
- federation without loss of provenance.

## 13. Candidate domain entities

```text
SourceArtifact
SourceVersion
ContentHash
AcquisitionRecord
TransformationRecord
Claim
Evidence
CounterEvidence
Contradiction
EvidenceGap
ExpeditionState
PrivateJournalEntry
FieldNote
KnowledgeContribution
ContributionReview
ContributorProfile
ReputationSignal
CanonicalRevision
```

## 14. Principles

> Raiatea must never convert missing evidence into false certainty.

> Integrity preserves what was acquired; evidence determines what may reasonably be believed.

> Discoveries belong first to the explorer, then—by deliberate choice and review—to the shared map.

> Shared knowledge grows through attributable, reversible, and inspectable contributions.

> Raiatea should make it easy to contribute, difficult to falsify silently, and always possible to trace how the map changed.

## 15. Open questions

- How long may raw content be retained under different rights policies?
- Which evidence-integrity guarantees can work offline?
- When is anonymity compatible with accountable contribution?
- How should expert and community review interact?
- How can brigading and coordinated manipulation of reviews be detected?
- What is the minimum evidence required before an expedition becomes `ready`?
- How should private discoveries be exported or inherited without violating privacy?
- Can decentralized signatures or transparency logs improve trust without making the system unusable?
- Who defines the canonical graph when federated communities disagree?
