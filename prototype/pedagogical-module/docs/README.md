# Pedagogical module architecture decisions

This directory collects the stable architecture and privacy decisions that govern the pedagogical-module prototype. These documents describe current boundaries and future implementation constraints; they are not substitutes for schemas, validators, tests, or executable examples.

## Current decisions

- [`learner-evidence-boundaries.md`](learner-evidence-boundaries.md) — current retention, deletion, privacy, local-first, adapter, and external-integration boundaries for learner evidence.
- [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md) — durable module identity, immutable published revisions, future immutable step identity, compatibility classes, and authored migration responsibilities.
- [`module-evolution-test-responsibilities.md`](module-evolution-test-responsibilities.md) — subordinate acceptance matrix assigning future evolution scenarios to fixtures, publication-history checks, validators, previews, and state-transition tests.

## Reading order for evidence work

1. Read the retention and privacy boundary to understand what data exists today, where each copy lives, and which operations may mutate or transmit it.
2. Read the module-evolution decision before changing step identity, module revisions, evidence versions, compatibility policy, or migration behavior.
3. Use the test-responsibility appendix to select the fixtures and test layers required by a future implementation issue. The architecture decision prevails if wording conflicts.
4. Read the current schema, validator, examples, tests, and prototype README before implementing a micro-step.

## Current implementation boundary

Learner-evidence v1 remains frozen under its exact module-ID, ordered-index, and authored-step-title compatibility rules. The module-evolution documents do not add revision fields, step IDs, publication history, evidence v2, or executable migrations. Those changes require separate issues, contracts, fixtures, review rounds, and green CI.
