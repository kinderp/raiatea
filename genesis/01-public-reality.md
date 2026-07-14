---
status: draft
author: Antonio Caristia and GPT-5.6 Thinking
created: 2026-07-14
version: 0.1.0
purpose: Define how Raiatea should help a person understand complex public events without reducing them to slogans or binary judgments.
audience: Project founders and future contributors
---

# Understanding Public Reality

## The problem

When a major public event occurs, most people encounter it first through fragments:

- news headlines;
- political statements;
- social media posts;
- historical references;
- maps and statistics;
- expert commentary;
- propaganda;
- selective quotations;
- emotionally charged narratives.

A person may reasonably ask:

- What actually happened?
- How did the situation develop?
- Which treaties, declarations, conflicts, interests and decisions shaped it?
- Which claims are well supported?
- Which claims are disputed?
- Which statements are propaganda, simplification or retrospective justification?
- What did the main actors say at different moments?
- When did their positions change?
- What economic, strategic, cultural, security or ideological interests were involved?
- Which alternative paths were possible?
- Which events closed some paths and opened others?

A conventional search engine returns documents.

A conventional chatbot often returns a compressed narrative.

Raiatea should instead reconstruct a navigable history of the problem.

## Core use case

A user should be able to ask a broad and difficult question such as:

> How did the conflict between Russia and Ukraine develop, which agreements and historical events are relevant, which claims are supported or disputed, what interests shaped the decisions of the main actors, and how did the available paths narrow over time?

Raiatea should not answer this with a single verdict or a list of talking points.

It should produce an evidence-backed, temporal and multi-perspective model.

## Required structure of an answer

### 1. Scope and question decomposition

The system should first separate the broad question into smaller questions, for example:

- post-Second World War security order;
- dissolution of the Soviet Union;
- Ukrainian independence;
- NATO enlargement;
- relevant treaties, memoranda and diplomatic assurances;
- domestic politics in Russia and Ukraine;
- economic and strategic interests;
- Crimea and Donbas;
- public declarations by political leaders;
- military events;
- disinformation and propaganda campaigns;
- failed negotiations and unrealized alternatives.

### 2. Chronology

The system should construct a timeline that preserves:

- date;
- event;
- actors;
- source;
- direct consequences;
- longer-term consequences;
- disputed interpretations;
- confidence and evidential status.

### 3. Claims and evidence

Every important claim should be represented independently.

Example structure:

```yaml
claim:
  text: "..."
  asserted_by: "..."
  asserted_at: "..."
  claim_type: fact | interpretation | causal_claim | prediction | justification | accusation
  supporting_evidence: []
  contrary_evidence: []
  primary_sources: []
  secondary_sources: []
  status: supported | disputed | unsupported | unresolved | misleading_without_context
  confidence: 0.0-1.0
```

The system must distinguish between:

- a signed treaty;
- a diplomatic assurance;
- an oral statement;
- a later interpretation;
- a political slogan;
- a legal obligation;
- a strategic expectation;
- a propaganda claim.

These categories must never be silently collapsed into one another.

### 4. Actor models

For every major actor, the system should represent:

- declared goals;
- observable actions;
- strategic interests;
- economic interests;
- security concerns;
- domestic political pressures;
- alliances;
- contradictions between words and actions;
- changes in position over time.

The system should not infer hidden motives as facts.

It may present inferred motives only when they are clearly marked as interpretations and linked to evidence.

### 5. Position timelines

For people, governments and organizations, Raiatea should preserve historical statements rather than overwrite them.

```text
Actor
├── Position at time A
├── Position at time B
├── Position at time C
└── Possible explanation for change
```

A change of position may be explained by:

- new evidence;
- strategic adaptation;
- domestic political pressure;
- economic incentives;
- military developments;
- leadership change;
- audience change;
- rhetorical repositioning;
- contradiction or bad faith.

The explanation itself must remain a hypothesis unless directly documented.

### 6. Alternative paths

Understanding the past requires more than recording what happened.

Raiatea should also represent plausible alternatives that were available at key moments:

- negotiations that could have continued;
- treaties that could have been implemented differently;
- reforms that were proposed but rejected;
- diplomatic opportunities that were lost;
- escalatory and de-escalatory paths;
- decisions that narrowed later options.

This does not mean inventing alternate history.

It means documenting contemporaneous options that were genuinely discussed, proposed or available.

### 7. Causal explanation

Raiatea should distinguish:

- trigger events;
- necessary conditions;
- contributing factors;
- structural causes;
- enabling conditions;
- stated justifications;
- retrospective narratives.

A complex event rarely has one cause.

The system should represent causal explanations as competing models where appropriate.

### 8. Propaganda and manipulation analysis

The system should detect and expose patterns such as:

- selective chronology;
- fabricated quotations;
- false equivalence;
- omission of relevant events;
- emotionally loaded framing;
- repeated claims with no independent sources;
- coordinated amplification;
- misleading statistics;
- legal terms used imprecisely;
- claims detached from their original context.

Raiatea should not classify a person or group as inherently truthful or manipulative.

It should analyze observable communication behavior, claim quality and evidential support.

### 9. Uncertainty and disagreement

The system must make disagreement visible.

For each major issue it should show:

- points of broad agreement;
- points of serious dispute;
- unresolved factual questions;
- interpretive disagreements;
- legal disagreements;
- evidence gaps;
- possible biases in the available record.

### 10. Present understanding

The final synthesis should answer:

- what is strongly supported;
- what remains disputed;
- which narratives omit important context;
- which causal explanations have the strongest evidence;
- which questions cannot currently be resolved;
- what information would most improve understanding.

## Why history matters

The present is the visible surface of a process.

To understand a current event, a person needs to see:

```text
past structures
→ decisions
→ reactions
→ feedback loops
→ path dependencies
→ present conditions
```

Without this history, current affairs become a contest between isolated claims.

With it, a person can understand how the available routes changed over time.

## From past to future

The same model that explains the past can support cautious forecasting.

Raiatea may identify:

- persistent trends;
- unresolved tensions;
- actor incentives;
- constraints;
- possible escalation paths;
- possible de-escalation paths;
- indicators that would make one scenario more likely.

Forecasts must be:

- probabilistic;
- time-bounded;
- based on explicit evidence;
- accompanied by counter-evidence;
- associated with resolution criteria;
- evaluated after the forecast horizon.

## Ethical principle

Raiatea should help a person become less dependent on authority, rhetoric and algorithmic persuasion.

It should not tell the user whom to trust.

It should make it easier to inspect:

- who said what;
- when they said it;
- what evidence they offered;
- what they omitted;
- how their position changed;
- whether events supported or contradicted their claims.

## Design principle

> For public reality, Raiatea should reconstruct routes, not compress history into verdicts.

## Implications for the system

This use case requires at least:

- temporal knowledge representation;
- claim extraction;
- source provenance;
- actor identity resolution;
- treaty and document modeling;
- event timelines;
- causal relation modeling;
- position history;
- contradiction detection;
- source diversity;
- uncertainty representation;
- manipulation pattern detection;
- scenario and forecast support;
- transparent synthesis.

## Open questions

- How should legal obligations be distinguished from political assurances?
- How should the system compare primary sources in different languages?
- How should it model missing, classified or deliberately destroyed evidence?
- How can it avoid reproducing the biases of the most available sources?
- How should coordinated information campaigns be detected without overclaiming coordination?
- How should moral judgment relate to factual and causal analysis?
- How should war crimes, aggression, self-defence and other legal categories be represented?
- How can the system preserve empathy for affected populations without sacrificing analytical rigor?
- How should users inspect alternative explanations without creating false balance?

## Working hypothesis

> To understand public reality, a person must be able to reconstruct the history of claims, decisions, interests, events and unrealized alternatives that produced the present.
