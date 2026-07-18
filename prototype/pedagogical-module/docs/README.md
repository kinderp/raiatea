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
- [`pilot-route-dashboard.md`](pilot-route-dashboard.md) — learner-facing route status derived only from exact module-local progress keys, closed completion semantics, advisory recommendation, refresh behavior, and privacy limits.
- [`pilot-export-summary-walkthrough.md`](pilot-export-summary-walkthrough.md) — static learner guidance separating route status, module summary, and explicit module-scoped learner-evidence v1 download, including non-destructive and privacy boundaries.
- [`pilot-end-to-end-acceptance.md`](pilot-end-to-end-acceptance.md) — final manual and automated acceptance journey over the generated pilot artifact, including build, remediation, dashboard, summary, export, privacy, and closeout criteria.

The pilot contracts define the evaluator-facing local learner journey, its read-only route dashboard, its explicit per-module evidence walkthrough, and the final acceptance path. Evidence and migration contracts remain separate and unchanged.

## Reading order for evidence and pilot work

1. Read the retention and privacy boundary before changing stored or exported learner evidence.
2. Read the module-evolution and authoring contracts before changing module revisions or step identities.
3. Read the evidence v2, manifest, preview, and confirmed-application contracts before changing compatibility or migration behavior.
4. Read the first-runnable-pilot contract before packaging canonical modules into a local route.
5. Read the pilot-route-dashboard contract before deriving cross-module route status from browser-local progress.
6. Read the pilot export/summary walkthrough before changing learner-facing guidance or browser download verification.
7. Read the end-to-end acceptance contract before declaring the pilot ready for non-developer evaluation.
8. Read current schemas, validators, examples, tests, and the prototype README before implementing a micro-step.

## Current implementation boundary

Canonical pedagogical modules and learner-evidence v1/v2 contracts remain unchanged. The pilot packager builds a deterministic offline two-module route with relative navigation and no-replace output installation. The route dashboard reads only the two exact `raiatea-progress:<module-id>` keys, derives `not-started`, `in-progress`, or `locally-completed`, and recommends the first incomplete module without writing storage or gating navigation. The launcher provides static guidance for interpreting the module-local summary and explicitly downloading the unchanged privacy-safe learner-evidence v1 document for the current module. The final acceptance increment verifies the complete generated journey without adding learner behavior. Multi-module evidence export, accounts, server persistence, analytics, LMS integration, grading, and AI recommendations remain deferred.
