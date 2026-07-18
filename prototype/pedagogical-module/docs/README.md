# Pedagogical module architecture decisions

This directory collects the stable architecture and privacy decisions that govern the pedagogical-module prototype. These documents describe current boundaries and future implementation constraints; they are not substitutes for schemas, validators, tests, or executable examples.

## Current decisions

- [`learner-evidence-boundaries.md`](learner-evidence-boundaries.md) — current retention, deletion, privacy, local-first, adapter, and external-integration boundaries for learner evidence.
- [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md) — durable module identity, explicit revisions, future immutable step identity, compatibility classes, and authored migration responsibilities.
- [`module-revision-immutability-amendment.md`](module-revision-immutability-amendment.md) — normative correction making every published `(moduleId, revision)` binding immutable, non-reusable, and fail-closed on divergent republishing.
- [`module-evolution-test-responsibilities.md`](module-evolution-test-responsibilities.md) — normative responsibility matrix for future fixtures, validators, compatibility previews, migration state changes, and v1 regressions.
- [`module-revision-authoring.md`](module-revision-authoring.md) — executable authoring boundary for required canonical module revisions and durable pedagogical step IDs, including the unchanged learner-evidence v1 boundary.

The immutability amendment, test-responsibility matrix, and canonical authoring rules are normative parts of the module-evolution decision set. They must be read together with the main decision.

## Reading order for evidence work

1. Read the retention and privacy boundary to understand what data exists today, where each copy lives, and which operations may mutate or transmit it.
2. Read the module-evolution decision before changing step identity, module revisions, evidence versions, compatibility policy, or migration behavior.
3. Read the revision-immutability amendment and test-responsibility matrix before designing publication history, revision validation, or migration fixtures.
4. Read the canonical revision and step-identity authoring rules before creating or changing a buildable module.
5. Read the current schema, validator, examples, tests, and prototype README before implementing a micro-step.

## Current implementation boundary

Canonical pedagogical modules now require a positive integer `revision` and one unique lowercase/digit/hyphen `id` for every pedagogical step. Learner-evidence v1 remains frozen under its exact module-ID, ordered-index, and authored-step-title compatibility rules and does not export the new canonical fields. Evidence v2, publication registries, migration manifests, compatibility previews based on stable IDs, and executable migrations remain separate increments.
