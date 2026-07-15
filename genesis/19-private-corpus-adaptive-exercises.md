# Adaptive Exercises from Private Corpora

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Define how Raiatea creates personalised exercises from lawfully owned private books and documents, uses the results to update the learner model, and shares only independently created reusable educational knowledge.

---

## 1. Core idea

Raiatea should not stop at translating, summarising, and organising a private book.

It should transform the material into active learning experiences tailored to:

- the user's current expedition;
- prior knowledge;
- detected misconceptions;
- professional or academic goal;
- available time;
- preferred level of difficulty;
- concepts actually covered by the user's sources.

> A private book should become not only readable, but teachable, testable, and usable for constructing new knowledge.

---

## 2. Why this adds value beyond a general LLM

A general LLM can generate exercises from a prompt or from an uploaded excerpt.

Raiatea should add a persistent closed loop:

```text
Private source
→ concept and prerequisite model
→ learner state
→ targeted exercise
→ submitted solution
→ evaluation and explanation
→ updated learner model
→ revised expedition
→ next exercise
```

The value is not the isolated exercise. It is the continuing connection between source, learner, evidence of mastery, route, and future updates.

---

## 3. Exercise types

Raiatea may generate:

- recall questions;
- conceptual explanations;
- worked examples with missing steps;
- multiple-choice questions with diagnostic distractors;
- true/false questions requiring justification;
- code completion;
- debugging tasks;
- implementation projects;
- mathematical derivations;
- diagram reconstruction;
- comparison between approaches;
- source criticism;
- claim-and-evidence analysis;
- timeline ordering;
- case studies;
- oral examination simulations;
- flashcards;
- spaced-repetition prompts;
- research questions;
- replication exercises;
- counterfactual and scenario analysis.

Exercises should be chosen according to the kind of understanding required, not generated uniformly for every chapter.

---

## 4. Source grounding

Every private-corpus exercise should record:

- source or sources used;
- edition and version;
- chapter, section, page, timestamp, or code commit;
- concepts assessed;
- prerequisites;
- expected difficulty;
- exercise-generation method;
- whether the answer is explicit in the source or requires synthesis;
- evaluation rubric;
- confidence and known ambiguities.

The user should be able to return from the exercise to the exact private source location.

---

## 5. Diagnostic adaptation

Raiatea should use mistakes diagnostically.

A wrong answer may indicate:

- missing prerequisite;
- confusion between similar concepts;
- memorisation without causal understanding;
- inability to transfer theory to practice;
- outdated or unclear source explanation;
- translation problem;
- ambiguous exercise;
- actual error in the book or Raiatea's model.

The system should not simply assign a score. It should decide what the error changes in the route.

Example:

```text
Exercise failed
→ inspect reasoning
→ identify missing prerequisite on matrix dimensions
→ insert short remedial module
→ generate simpler transfer exercise
→ retry original concept later
```

---

## 6. Assessment evidence

Raiatea should distinguish:

- exposure: the source was opened;
- completion: the section was read;
- recall: key facts can be retrieved;
- comprehension: the concept can be explained;
- application: it can be used in a new problem;
- analysis: alternatives and limitations can be compared;
- creation: the learner can build something new;
- durable mastery: performance remains after time has passed.

The learner profile should avoid claiming mastery based only on reading time or one correct answer.

---

## 7. Automatic and human evaluation

Evaluation may combine:

- deterministic tests;
- unit tests and sandboxed execution;
- symbolic or numerical checking;
- rubric-based LLM review;
- comparison between multiple models;
- self-explanation analysis;
- peer review;
- teacher or expert review;
- delayed retesting.

High-stakes assessment should not depend solely on one model's judgment.

Raiatea must preserve:

- the learner's original answer;
- evaluation version;
- rubric;
- feedback;
- appeals and corrections;
- later evidence that changes the assessment.

---

## 8. Private and shareable layers

### Private layer

Contains:

- exact source text;
- complete translation;
- personal mistakes;
- scores;
- learning weaknesses;
- private solutions;
- detailed adaptation history;
- sensitive educational data.

### Shareable layer

May contain, after rights and quality review:

- independently authored exercise templates;
- original problem statements;
- generic rubrics;
- concept and prerequisite mappings;
- common misconceptions in anonymised form;
- newly created examples;
- code tests;
- improved explanations;
- evidence that an exercise is effective;
- source references without protected content.

An exercise that closely reproduces a protected book's questions, examples, figures, or expressive structure should remain private unless licensed.

---

## 9. Community improvement

Exercises can improve through use.

Raiatea may learn:

- which distractors reveal real misconceptions;
- which wording is ambiguous;
- which prerequisite is usually missing;
- which exercise predicts later success;
- which examples work for different backgrounds;
- where a source explanation is consistently insufficient.

Reusable findings should be aggregated without exposing individual learners.

A public exercise may move through states such as:

```text
draft
→ privately tested
→ anonymised community evidence
→ peer reviewed
→ validated for a topic and learner level
→ revised or retired
```

---

## 10. Exercises as new knowledge construction

The strongest exercises should not merely test whether the learner remembers a book.

They should ask the learner to:

- combine several sources;
- reproduce an experiment;
- challenge a claim;
- compare implementations;
- construct a process model;
- detect a contradiction;
- formulate a new hypothesis;
- explain why a historical path prevailed;
- build a project whose result becomes evidence.

The learner may therefore create new knowledge during the expedition.

After consent and review, shareable results may become:

- public experiments;
- corrections;
- new examples;
- improved explanations;
- reusable code;
- verified knowledge bundles.

---

## 11. Example: LLM inference book

A user owns a technical book on LLM inference.

Raiatea may create:

```text
Chapter 3 — KV cache

1. Explain why the cache changes time and memory complexity.
2. Calculate memory use for a specified model and sequence length.
3. Find the bug in a cache implementation.
4. Compare multi-head and multi-query attention for this workload.
5. Run a small benchmark and record the evidence.
6. Read a newer public paper and identify which parts of the chapter are outdated.
7. Update the shared process model with the verified result.
```

The first exercises assess comprehension. The later ones connect the private book to current research and potentially produce public knowledge.

---

## 12. Immediate product value

This capability creates immediate value because a purchased book becomes:

- an adaptive course;
- a tutor-guided practice environment;
- an examination simulator;
- a project generator;
- a diagnostic tool;
- a bridge to newer papers and code;
- a source of reusable contributions.

It also addresses a major weakness of passive reading: users often feel they understood a chapter without being able to recall, apply, or transfer it.

---

## 13. Business-model implications

Possible paid services include:

- high-volume exercise generation;
- private adaptive tutoring;
- code sandbox and compute;
- expert-reviewed assessments;
- examination simulations;
- professional project reviews;
- certificates based on transparent evidence;
- teacher and institutional dashboards;
- custom curricula from licensed corpora.

The shared exercise core and public educational knowledge may remain open, while payment covers private adaptation, compute, storage, expert review, and institutional services.

---

## 14. Domain concepts introduced

- `Exercise`;
- `ExerciseTemplate`;
- `AssessmentTarget`;
- `PrerequisiteGap`;
- `LearnerResponse`;
- `EvaluationRubric`;
- `EvaluationResult`;
- `MasteryEvidence`;
- `Misconception`;
- `RemediationStep`;
- `DelayedReview`;
- `ExerciseEffectivenessEvidence`;
- `LearningContribution`.

---

## 15. Provisional decision

Raiatea will treat private sources as foundations for adaptive exercises and projects.

The private source, close derivatives, answers, and learner data remain private. Independently created exercise structures, generic explanations, anonymised learning evidence, and new verified results should be eligible to improve the shared commons.

> Raiatea should not merely help a user read a book. It should help the user prove, apply, challenge, and extend what the book taught.
