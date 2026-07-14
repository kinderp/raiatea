# Public Figures: Statements, Actions, Interests, and Accountability

> Status: Draft  
> Version: 0.1.0  
> Project phase: Project Genesis — Leaving the Shore  
> Created: 2026-07-14

## Purpose

This document defines how Raiatea should help a person understand the public history of a politician or other influential public figure without reducing the analysis to praise, condemnation, ideology, or reputation.

The goal is not to decide whether a person is good or bad.

The goal is to reconstruct, with provenance and time, what the person said, what the person did, what changed, what interests and constraints were present, and where statements and actions appear coherent, inconsistent, or unresolved.

## Guiding question

> How can Raiatea make the public record of a person understandable without becoming a judge of that person?

## Core principle

> Raiatea should not label people. It should compare claims, actions, decisions, interests, context, and consequences.

## The public record as a temporal model

A public figure cannot be represented by a static profile.

Raiatea should reconstruct a timeline that includes:

- public statements;
- electoral promises;
- votes;
- decrees and administrative decisions;
- appointments;
- budget choices;
- alliances;
- policy reversals;
- declared and undeclared interests when documented;
- institutional constraints;
- relevant external events;
- measurable consequences;
- corrections, retractions, and changes of position.

Each item must preserve:

- date and time;
- source;
- exact or summarized wording;
- context;
- role held by the person at that time;
- affected policy area;
- confidence and verification status.

## Statements and actions

Raiatea should distinguish at least the following:

- **statement** — what the person publicly asserted;
- **promise** — a future commitment made to voters or stakeholders;
- **proposal** — a policy or action suggested but not yet adopted;
- **vote** — a recorded institutional choice;
- **decision** — an action taken within the person's authority;
- **implementation** — what was actually carried out;
- **outcome** — what followed, without assuming that the decision alone caused it;
- **explanation** — the reason later given for an action or change;
- **position change** — a documented shift over time;
- **contradiction candidate** — an apparent conflict requiring contextual analysis.

A contradiction must never be inferred from two isolated quotations alone.

The system must examine whether:

- the context changed;
- the person's institutional role changed;
- the statement referred to a different scope or condition;
- new evidence emerged;
- the earlier quotation was incomplete or misleadingly edited;
- the later action was constrained by law, coalition, budget, or emergency;
- the person explicitly acknowledged a change of mind.

## Coherence and contradiction

Raiatea may highlight patterns such as:

- statement aligned with subsequent action;
- promise fulfilled;
- promise partially fulfilled;
- promise not fulfilled;
- statement followed by opposite action;
- policy reversal with explicit explanation;
- policy reversal without explanation;
- repeated change of position;
- stable position across changing circumstances;
- discrepancy between public justification and documented evidence.

These are analytical relationships, not moral verdicts.

A useful output should say:

> In 2022 the person stated X. In 2024, while holding role Y, the person approved action Z. The two appear inconsistent under the same interpretation of X. The available sources provide these possible explanations and these unresolved questions.

It should not say:

> This person is a liar.

## Interests and conflicts

Raiatea should represent interests only when supported by evidence.

Possible categories include:

- financial interests;
- family interests;
- business relationships;
- donors and campaign financing;
- party interests;
- electoral incentives;
- institutional interests;
- geopolitical interests;
- ideological commitments;
- professional networks;
- lobbying relationships;
- ownership or control of relevant assets.

The system must distinguish:

- documented conflict of interest;
- declared interest;
- potential conflict;
- allegation;
- inference;
- unsupported accusation.

An interest does not prove corruption or improper intent.

It is relevant context that may help explain decisions and should be shown together with alternative explanations.

## Causality and responsibility

Raiatea must avoid attributing every outcome to a single person.

Public decisions are shaped by:

- institutions;
- coalitions;
- bureaucracies;
- courts;
- economic conditions;
- international events;
- prior laws;
- local implementation;
- public opinion;
- other decision makers.

For every claimed consequence, the system should distinguish:

- direct action;
- formal responsibility;
- political responsibility;
- contribution among several factors;
- temporal association only;
- contested causal interpretation.

## Suggested public-figure view

A Raiatea profile could include:

1. **Verified identity and roles**
2. **Timeline of offices and responsibilities**
3. **Statements by topic**
4. **Decisions and recorded actions**
5. **Promises and implementation status**
6. **Position changes**
7. **Coherence and contradiction candidates**
8. **Declared interests and documented conflicts**
9. **Institutional and historical context**
10. **Consequences and competing causal explanations**
11. **Corrections and unresolved disputes**
12. **Complete provenance**

## Evidence requirements

High-impact claims about a person should prefer:

- primary documents;
- official voting records;
- laws and administrative acts;
- complete speeches or interviews;
- financial disclosures;
- court records;
- official budgets;
- multiple independent and reputable sources.

Social posts, edited clips, anonymous allegations, and partisan summaries may be included as discourse evidence, but not silently promoted to verified fact.

## Fairness safeguards

Raiatea should:

- apply the same analytical criteria across political positions;
- show exculpatory as well as incriminating evidence;
- preserve uncertainty;
- separate documented fact from interpretation;
- avoid psychological diagnosis and speculation about hidden motives;
- make corrections visible;
- allow competing explanations;
- reveal why a contradiction was flagged;
- permit inspection of every source and transformation.

## Example query

> Show me the history of this politician's position on public healthcare. Compare statements, campaign promises, votes, budgets, appointments, and measurable implementation. Highlight coherent periods, changes of position, unresolved contradictions, declared interests, and relevant external constraints. Do not issue a moral judgment.

## Architectural implications

This use case requires first-class support for:

- Person;
- Role;
- Organization;
- Statement;
- Claim;
- Promise;
- Vote;
- Decision;
- Policy;
- Action;
- Outcome;
- Interest;
- ConflictOfInterest;
- Position;
- PositionChange;
- ContradictionCandidate;
- Context;
- Evidence;
- ProvenanceRecord;
- TemporalRelation;
- CausalHypothesis;
- AlternativeExplanation.

## Foundational principle

> Public accountability should emerge from a transparent comparison between words, actions, interests, context, and consequences—not from labels assigned by the system.

## Open questions

- How should promise fulfillment be measured when commitments are vague?
- When does a change of mind represent inconsistency, learning, or adaptation?
- How should the system represent collective decisions?
- How can partisan source imbalance be detected and corrected?
- How should alleged conflicts be shown before legal or institutional verification?
- What minimum evidence is required before highlighting a contradiction?
- How can the system resist coordinated attempts to distort a public figure's record?
