# Pedagogical module architecture decisions

This directory collects the stable architecture and privacy decisions that govern the pedagogical-module prototype. These documents describe current boundaries and future implementation constraints; they are not substitutes for schemas, validators, tests, or executable examples.

## Current decisions

- [`learner-evidence-boundaries.md`](learner-evidence-boundaries.md) — current retention, deletion, privacy, local-first, adapter, and external-integration boundaries for learner evidence.
- [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md) — durable module identity, explicit revisions, future immutable step identity, compatibility classes, and authored migration responsibilities.
- [`module-revision-immutability-amendment.md`](module-revision-immutability-amendment.md) — normative correction making every published `(moduleId, revision)` binding immutable, non-reusable, and fail-closed on divergent republishing.
- [`module-evolution-test-responsibilities.md`](module-evolution-test-responsibilities.md) — normative responsibility matrix for future fixtures, validators, compatibility previews, migration state changes, and v1 regressions.
- [`module-revision-authoring.md`](module-revision-authoring.md) — executable authoring boundary for required canonical module revisions and durable pedagogical step IDs, including the unchanged learner-evidence v1 boundary.
- [`learner-evidence-v2-stable-identity.md`](learner-evidence-v2-stable-identity.md) — separately versioned evidence contract carrying exact module revision, stable step IDs, explicit source order, privacy exclusions, and the initial structural-only boundary.

The immutability amendment, test-responsibility matrix, canonical authoring rules, and evidence v2 contract are normative parts of the module-evolution decision set. They must be read together with the main decision.

## Reading order for evidence work

1. Read the retention and privacy boundary to understand what data exists today, where each copy lives, and which operations may mutate or transmit it.
2. Read the module-evolution decision before changing step identity, module revisions, evidence versions, compatibility policy, or migration behavior.
3. Read the revision-immutability amendment and test-responsibility matrix before designing publication history, revision validation, or migration fixtures.
4. Read the canonical revision and step-identity authoring rules before creating or changing a buildable module.
5. Read the evidence v2 stable-identity contract before adding v2 exporters, compatibility checks, or migration behavior.
6. Read the current schemas, validators, examples, tests, and prototype README before implementing a micro-step.

## Current implementation boundary

Canonical pedagogical modules require a positive integer `revision` and one unique lowercase/digit/hyphen `id` for every pedagogical step. Learner-evidence v1 remains frozen under its exact module-ID, ordered-index, and authored-step-title compatibility rules. Learner-evidence v2 now has a separate closed schema, example, and side-effect-free structural validator carrying exact revision identity and stable step IDs. Browser export/import, contextual compatibility against an installed module revision, migration manifests, compatibility previews, and state-changing migrations remain separate increments.
