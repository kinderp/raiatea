# Dynamic Systems and Stochastic Processes

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Define a domain model that preserves identifiable objects while explaining their evolution through processes, events, uncertainty, and partial observation.

## Question

How should Raiatea represent a world in which people, ideas, institutions, technologies, scientific fields, public debates, and historical situations are identifiable objects, but also parts of systems that continuously change?

## Working hypothesis

Raiatea should not choose between objects and processes.

> **Objects are identifiable states and participants within systems; processes explain how those systems evolve.**

Many relevant processes are neither fully deterministic nor fully observable. Raiatea must therefore be able to represent stochastic evolution, hidden state, incomplete evidence, alternative explanations, and multiple plausible futures.

## Core model

A domain can be represented through six foundational concepts.

### Entity

An identifiable object that persists through time despite change.

Examples:

- person;
- organization;
- publication;
- theory;
- technology;
- law;
- institution;
- event series;
- research field.

An entity is not assumed to be static. Identity allows observations made at different times to be connected.

### State

A time-bounded description of an entity or system.

Examples:

- a person's publicly expressed position in 2023;
- the architecture of a software project at a given release;
- the accepted state of a scientific field in a certain period;
- the membership and strategy of an organization at a given date.

A profile is primarily a human-readable view over selected states.

### Event

A recorded occurrence that may alter one or more states.

Examples:

- publication of a paper;
- election result;
- policy decision;
- acquisition;
- public statement;
- experiment;
- retraction;
- release of a model;
- crisis or external shock.

An event is not automatically a cause. Causal relevance must be supported separately.

### Process

A dynamic pattern or mechanism through which states change over time.

Examples:

- scientific adoption;
- opinion change;
- diffusion of a narrative;
- technological maturation;
- organizational restructuring;
- learning;
- political realignment;
- propagation and correction of misinformation.

A timeline lists events. A process model attempts to explain the transitions between them.

### Observation

Evidence through which Raiatea learns about an entity, event, state, or process.

Examples:

- document;
- interview;
- vote;
- source code;
- dataset;
- photograph;
- social post;
- transcript;
- experiment;
- measurement.

Observations are always distinct from the underlying reality they describe.

### Hypothesis

A proposed explanation, causal relation, interpretation, counterfactual, or forecast.

Every hypothesis should preserve:

- supporting evidence;
- counter-evidence;
- assumptions;
- scope;
- uncertainty;
- author or generating process;
- review status;
- alternatives.

## Dynamic-system representation

At time \(t\), a system has a state \(X_t\). Its evolution may depend on actions, external events, internal dynamics, and uncertainty:

\[
X_{t+1} \sim P(X_{t+1} \mid X_t, A_t, E_t, C_t)
\]

where:

- \(X_t\): current system state;
- \(A_t\): actions and decisions by actors;
- \(E_t\): external events or shocks;
- \(C_t\): social, technical, historical, economic, and institutional context;
- \(P\): distribution over possible subsequent states.

This is a conceptual model, not a requirement that every Raiatea domain use the same mathematical implementation.

## Partial observability

Raiatea rarely observes a system directly.

For a public person, it may observe statements, votes, publications, employment, declared interests, and documented decisions. It does not directly observe intentions, private pressures, internal beliefs, or undisclosed information.

A useful conceptual distinction is therefore:

\[
X_{t+1} = f(X_t, U_t) + W_t
\]

\[
Y_t = g(X_t) + V_t
\]

where:

- \(X_t\): partially hidden state;
- \(Y_t\): available observations;
- \(U_t\): actions and inputs;
- \(W_t\): uncertainty in system evolution;
- \(V_t\): noise, omission, distortion, or measurement error.

Raiatea must never silently equate observed evidence with inferred inner state.

## Types of relationships

Relations should be explicitly classified rather than reduced to `related_to`.

### Deterministic or documentary

Examples:

- authored;
- published-on;
- voted-for;
- employed-by;
- occurred-before.

### Structural or semantic

Examples:

- component-of;
- prerequisite-of;
- implementation-of;
- contradicts-by-definition.

### Causal

Examples:

- enabled;
- inhibited;
- triggered;
- contributed-to;
- changed-the-probability-of.

Causal relations must expose evidence and alternative explanations.

### Probabilistic or predictive

Examples:

- likely-to-adopt;
- plausible-next-state;
- forecast-to-increase;
- risk-of-failure.

They require time horizon, probability or calibrated confidence, assumptions, and resolution criteria.

### Interpretive

Examples:

- appears-consistent-with;
- may-explain;
- interpreted-as;
- apparent-contradiction-with.

Interpretations must remain distinguishable from documentary facts.

## Historical alternatives and counterfactuals

A process should preserve both the realized route and significant alternatives that were available at a decision point.

```text
State at time t
├── route A — realized
├── route B — considered but abandoned
├── route C — prevented by event E
└── route D — reconstructed counterfactual
```

Raiatea must distinguish:

- documented alternatives discussed at the time;
- retrospective interpretations;
- formal simulations;
- speculative counterfactuals;
- forecasts from the present.

## Human-readable views

The underlying dynamic model should support complementary views.

### Profile

A coherent summary of an entity, its roles, interests, works, statements, actions, topics, relationships, and current known state.

### Timeline

Ordered observations, events, states, and changes.

### Map

Relations among entities, concepts, institutions, evidence, and processes.

### Process explanation

A reconstruction of mechanisms, causes, constraints, feedback loops, and turning points.

### Scenario view

Alternative routes, future possibilities, assumptions, probabilities, and signals to monitor.

### Expedition

A user-centered path that combines these views for a concrete purpose such as learning, research, journalism, teaching, verification, or civic decision-making.

## Example: public figure

```text
Entity:
  Person A

Observed state, 2022:
  publicly supports policy X

Observations:
  interview, manifesto, recorded vote

Events:
  election, economic crisis, change of office

Observed state, 2024:
  opposes or modifies policy X

Possible processes:
  - genuine change of belief
  - response to new evidence
  - institutional constraint
  - strategic repositioning
  - constituency pressure

Output:
  documented consistency and contradiction patterns,
  possible explanations,
  missing evidence,
  and uncertainty — without assigning moral labels.
```

## Example: scientific field

```text
Entities:
  papers, researchers, institutions, methods, datasets, benchmarks

States:
  dominant assumptions and available techniques in each period

Events:
  publication, replication, benchmark result, hardware change, retraction

Processes:
  adoption, criticism, refinement, convergence, abandonment, revival

Scenarios:
  competing research directions and signals that would strengthen each one
```

## Architectural implications

Raiatea will likely require a stratified model containing:

```text
Temporal Knowledge Graph
+ Entity and Identity Model
+ State and Event Model
+ Process and Causal Model
+ Probabilistic Inference Layer
+ Evidence and Provenance Layer
+ Transparency Log
+ Human-readable Views
```

The probabilistic layer must be optional and explicit. It should never convert uncertainty into an unexplained score.

## Principles

1. **Entities remain visible.** Processes do not replace profiles, documents, people, concepts, or institutions.
2. **States are time-bounded.** A current profile must not erase previous states.
3. **Events are not causes by default.** Temporal succession is not sufficient evidence of causality.
4. **Observations are not reality itself.** Every observation retains source, method, uncertainty, and transformations.
5. **Hidden state must remain inferred.** Raiatea must not present presumed motives as observed facts.
6. **Probability expresses uncertainty, not truth.** Every prediction must expose assumptions and evidence.
7. **Alternative routes matter.** Understanding includes knowing which paths were available and why one prevailed.
8. **The model must remain inspectable.** Users must be able to move from an explanation or forecast back to observations and sources.

## Open questions

- Which process types deserve first-class domain models?
- Should Raiatea use bitemporal data for both occurrence time and knowledge-acquisition time?
- When is a Markov assumption acceptable, and when must longer history be represented explicitly?
- How should qualitative uncertainty coexist with numerical probability?
- How can causal hypotheses be compared without creating false precision?
- Which domains permit meaningful simulation, and which should remain explanatory only?
- How should the system detect regime changes, feedback loops, and emergent behavior?
- How can user discoveries improve a process model without contaminating the canonical graph?

## Provisional conclusion

> **Raiatea represents identifiable entities and observable states, but understands them within temporal processes. When evolution is uncertain or only partially observable, it preserves explicit probabilistic hypotheses while keeping evidence, inference, and scenario separate.**
