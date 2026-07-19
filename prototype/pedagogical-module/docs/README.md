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
- [`evaluator-release-layout.md`](evaluator-release-layout.md) — closed evaluator-release manifest, opaque version identity, deterministic versioned directory layout, regular-file inventory, and no-replace installation boundary.
- [`evaluator-release-archive.md`](evaluator-release-archive.md) — reproducible POSIX tar packaging, normalized member metadata, deterministic SHA-256 inventory, safe extraction, and independent verification boundary.
- [`evaluator-release-notes-and-verification.md`](evaluator-release-notes-and-verification.md) — deterministic version-pinned release notes, non-developer verification/serve/cleanup workflow, unsigned-integrity wording, and stale-document detection.
- [`evaluator-release-ci-artifact.md`](evaluator-release-ci-artifact.md) — least-privilege CI producer/consumer separation, exact one-file artifact transport, independent verification, and loopback smoke-test boundary.
- [`cross-platform-launch-preflight.md`](cross-platform-launch-preflight.md) — verified-release input, supported Python runtime, loopback/port rules, stable diagnostics, owned process state, stop and cleanup lifecycle for future desktop helpers.
- [`posix-launch-stop-helpers.md`](posix-launch-stop-helpers.md) — portable macOS/Linux launch and stop helpers, loopback readiness, atomic local state, process-identity protection and archive composition.
- [`windows-powershell-launch-stop-helpers.md`](windows-powershell-launch-stop-helpers.md) — Windows PowerShell launch and stop helpers, canonical runtime discovery, loopback readiness, owned state and process-command validation.

The pilot contracts define the evaluator-facing local learner journey and its final acceptance path. The evaluator-release contracts wrap that unchanged pilot in a deterministic directory and archive with integrity metadata, evaluator guidance, independently verified CI transport, and desktop launch boundaries. Evidence and migration contracts remain separate and unchanged.

## Reading order for evidence, pilot, and release work

1. Read the retention and privacy boundary before changing stored or exported learner evidence.
2. Read the module-evolution and authoring contracts before changing module revisions or step identities.
3. Read the evidence v2, manifest, preview, and confirmed-application contracts before changing compatibility or migration behavior.
4. Read the first-runnable-pilot contract before packaging canonical modules into a local route.
5. Read the pilot-route-dashboard contract before deriving cross-module route status from browser-local progress.
6. Read the pilot export/summary walkthrough before changing learner-facing guidance or browser download verification.
7. Read the end-to-end acceptance contract before declaring the pilot ready for non-developer evaluation.
8. Read the evaluator-release layout contract before wrapping the pilot in versioned distribution metadata.
9. Read the evaluator archive contract before adding checksums, tar packaging, or extraction verification.
10. Read the release-notes contract before changing evaluator-facing identity, verification, serve, stop, or cleanup instructions.
11. Read the CI artifact contract before changing workflow triggers, permissions, artifact payload, retention, verification, or smoke testing.
12. Read the cross-platform launch/preflight contract before implementing process state, port handling or browser opening.
13. Read the POSIX helper contract before changing macOS/Linux launch, stop, diagnostics or helper packaging.
14. Read the Windows PowerShell helper contract before changing Windows launch, stop, diagnostics or desktop packaging.
15. Read current schemas, validators, examples, tests, and the prototype README before implementing a micro-step.

## Current implementation boundary

Canonical pedagogical modules and learner-evidence v1/v2 contracts remain unchanged. The completed pilot provides a deterministic offline two-module journey, read-only route dashboard, module-scoped v1 export, evaluator guidance, and full browser acceptance. The evaluator release remains reproducible and independently verifiable; the desktop field-pilot archive composes checksummed POSIX and PowerShell launch/stop helpers with local instructions. Both platforms require Python 3.10+, bind only to loopback, use owned runtime state and refuse foreign processes. Accounts, analytics, LMS integration, signing, installers, registries, deployments, services and automatic updates remain deferred.
