# Pedagogical module architecture decisions

This directory collects the stable architecture and privacy decisions that govern the pedagogical-module prototype. These documents describe current boundaries and future implementation constraints; they are not substitutes for schemas, validators, tests, or executable examples.

## Current decisions

- [`learner-evidence-boundaries.md`](learner-evidence-boundaries.md) — current retention, deletion, privacy, local-first, adapter, and external-integration boundaries for learner evidence.
- [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md) — durable module identity, explicit revisions, future immutable step identity, compatibility classes, and authored migration responsibilities.
- [`module-revision-immutability-amendment.md`](module-revision-immutability-amendment.md) — normative correction making every published `(moduleId, revision)` binding immutable, non-reusable, and fail-closed on divergent republishing.
- [`module-evolution-test-responsibilities.md`](module-evolution-test-responsibilities.md) — normative responsibility matrix for future fixtures, validators, compatibility previews, migration state changes, and v1 regressions.
- [`module-revision-authoring.md`](module-revision-authoring.md) — executable authoring boundary for required canonical module revisions and durable pedagogical step IDs, including the unchanged learner-evidence v1 boundary.
- [`learner-evidence-v2-stable-identity.md`](learner-evidence-v2-stable-identity.md) — separately versioned evidence contract carrying exact module revision, stable step IDs, explicit source order, privacy exclusions, and the initial structural-only boundary.
- [`learner-evidence-v2-exact-compatibility.md`](learner-evidence-v2-exact-compatibility.md) — Class A exact contextual comparison against one supplied canonical module revision, including identity keys, explanatory snapshots, failure semantics, and deferred classifier responsibilities.
- [`learner-evidence-migration-manifest.md`](learner-evidence-migration-manifest.md) — closed directional manifest contract with complete source/target inventories, one-to-one preservation, retirement/introduction operations, and no preview or mutation behavior.
- [`learner-evidence-migration-manifest-contextual-validation.md`](learner-evidence-migration-manifest-contextual-validation.md) — deterministic comparison of one structurally valid manifest with the exact supplied canonical source and target revisions, with namespaced structural failures and no classification or mutation.
- [`learner-evidence-v2-compatibility-preview.md`](learner-evidence-v2-compatibility-preview.md) — deterministic Class A–E precedence, direct-manifest classification, read-only preserved/introduced/retired preview, current-position outcomes, candidate availability, and explicit no-mutation boundary.
- [`confirmed-evidence-migration-application.md`](confirmed-evidence-migration-application.md) — versioned two-phase in-memory preparation and exact-token confirmation contract that freshly recomputes the preview, preserves the original object, and returns a separate validated migrated copy.
- [`first-runnable-pilot.md`](first-runnable-pilot.md) — canonical two-module pilot route, deterministic local build, relative launcher/navigation contract, no-replace installation boundary, and evaluator launch instructions.

The immutability amendment, test-responsibility matrix, canonical authoring rules, evidence v2 contract, exact contextual compatibility contract, migration-manifest contract, contextual manifest-validation contract, compatibility-preview contract, and confirmed-application contract are normative parts of the module-evolution decision set. They must be read together with the main decision. The pilot contract is the normative packaging boundary for the first end-to-end local learner journey.

## Reading order for evidence work

1. Read the retention and privacy boundary to understand what data exists today, where each copy lives, and which operations may mutate or transmit it.
2. Read the module-evolution decision before changing step identity, module revisions, evidence versions, compatibility policy, or migration behavior.
3. Read the revision-immutability amendment and test-responsibility matrix before designing publication history, revision validation, or migration fixtures.
4. Read the canonical revision and step-identity authoring rules before creating or changing a buildable module.
5. Read the evidence v2 stable-identity contract before adding v2 exporters, compatibility checks, or migration behavior.
6. Read the exact v2 compatibility contract before comparing evidence with a canonical revision.
7. Read the migration-manifest contract before authoring or structurally validating revision-transition mappings.
8. Read the contextual manifest-validation contract before comparing a manifest with caller-supplied canonical revisions.
9. Read the compatibility-preview contract before classifying a direct transition, generating a candidate, or presenting preserved, introduced, retired, or unresolved state.
10. Read the confirmed-application contract before creating confirmation tokens or returning migrated evidence copies.
11. Read the first-runnable-pilot contract before packaging canonical modules into the evaluator-facing local route.
12. Read the current schemas, validators, examples, tests, and prototype README before implementing a micro-step.

## Current implementation boundary

Canonical pedagogical modules require a positive integer `revision` and one unique lowercase/digit/hyphen `id` for every pedagogical step. Learner-evidence v1 remains frozen under its exact module-ID, ordered-index, and authored-step-title compatibility rules. Learner-evidence v2 has a separate closed schema, example, and side-effect-free structural validator carrying exact revision identity and stable step IDs. A separate exact contextual checker compares a structurally valid v2 document with one supplied canonical module revision. A closed migration-manifest schema and standalone validator describe complete same-module source/target inventories and `preserve`, `retire`, and `introduce` mappings without applying them. A separate side-effect-free contextual checker verifies that one structurally valid manifest exactly describes two supplied structurally valid canonical revisions, including ordered stable-step inventories. The read-only preview engine classifies exact, declared-lossless, declared-partial, incompatible, and unsupported direct transitions; emits deterministic preserved, introduced, retired, historical-only, and current-position outcomes; and may construct a non-persisted candidate only when current position is deterministic. The confirmed-application layer adds versioned, two-phase, in-memory preparation and application: it binds confirmation to complete validated current inputs and the freshly recomputed preview, rejects stale or ineligible transitions, and returns independent original/migrated copies without writing storage. The pilot packager now builds a deterministic, offline, canonical two-module route with a relative launcher and no-replace output installation. Filesystem publication of migrated evidence, browser v2 export/import and confirmation UI, route-wide progress aggregation, registries, manifest path selection/chaining, and split/merge semantics remain separate increments.
