# Pedagogical module architecture decisions

This directory collects the stable architecture and privacy decisions that govern the pedagogical-module prototype. These documents describe current boundaries and future implementation constraints; they are not substitutes for schemas, validators, tests, or executable examples.

## Current decisions

- [`learner-evidence-boundaries.md`](learner-evidence-boundaries.md) — current retention, deletion, privacy, local-first, adapter, and external-integration boundaries for learner evidence.
- [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md) — durable module identity, explicit revisions, future immutable step identity, compatibility classes, and authored migration responsibilities.
- [`module-revision-immutability-amendment.md`](module-revision-immutability-amendment.md) — normative correction making every published `(moduleId, revision)` binding immutable, non-reusable, and fail-closed on divergent republishing.
- [`module-evolution-test-responsibilities.md`](module-evolution-test-responsibilities.md) — normative responsibility matrix for future fixtures, validators, compatibility previews, migration state changes, and v1 regressions.

The immutability amendment and test-responsibility matrix are normative parts of the module-evolution decision set. They resolve final-head findings that were still open when PR #26 was merged and must be read together with the main decision.

## Reading order for evidence work

1. Read the retention and privacy boundary to understand what data exists today, where each copy lives, and which operations may mutate or transmit it.
2. Read the module-evolution decision before changing step identity, module revisions, evidence versions, compatibility policy, or migration behavior.
3. Read the revision-immutability amendment and test-responsibility matrix before designing publication history, revision validation, or migration fixtures.
4. Read the current schema, validator, examples, tests, and prototype README before implementing a micro-step.

## Current implementation boundary

Learner-evidence v1 remains frozen under its exact module-ID, ordered-index, and authored-step-title compatibility rules. The module-evolution decision set does not add revision fields, step IDs, evidence v2, publication registries, or executable migrations. Those changes require separate issues, contracts, fixtures, review rounds, and green CI.
