# Confirmed evidence migration application finding log

Issue: #48  
Pull request: #51

## Reviewed implementation

The first implementation review targeted head `f34edc980100b2a6c8e511735a8fa167b6126051`. Subsequent red-run analysis targeted the pre-rewrite head `d59914ba4e9f7b454448e05f6fc4727505879a27`. The implementation was then rebased onto the unreadable-input correction merged as `4b6caf0` and rewritten around one authoritative two-phase in-memory API.

All findings below are resolved. GitHub Actions and two consecutive clean review rounds must target one unchanged final head before merge.

## Findings

### F1 — major — resolved — confirmation omitted the source module and full manifest

The initial digest accepted evidence, target, preview, and only manifest endpoint identity. A source-module metadata change, retired-only evidence change, or manifest-operation change could leave confirmation insufficiently bound to the exact supplied transition.

Resolution: the versioned canonical projection now contains complete validated evidence, source module, target module, manifest, and the complete freshly recomputed preview, including current position and candidate.

### F2 — major — resolved — malformed direct inputs could escape as raw exceptions

The initial application called the preview core before structurally validating the supplied dictionaries. Missing fields, non-object values, or wrong types could therefore surface raw exceptions instead of deterministic namespaced application errors.

Resolution: preparation and application deep-copy and structurally validate all current inputs in fixed evidence, target-module, source-module, and manifest namespace order before classification. The branch is based on the unreadable-input fail-closed correction from #53 / PR #55.

### F3 — major — resolved — caller-supplied preview was trusted during confirmation creation

The initial public digest helper accepted an arbitrary preview object, weakening the claim that confirmation came from the authoritative current transition.

Resolution: `prepare_migration` recomputes the authoritative preview from current validated inputs and is the only public token-creation boundary. `apply_confirmed_migration` repeats that complete preparation before constant-time token comparison.

### F4 — minor — resolved — public contracts were not explicitly versioned or pinned

The initial result used a raw digest and tests did not pin a closed public shape.

Resolution: `contractVersion: 1`, the `raiatea-confirm-v1:<sha256>` token, `sha256:<candidate>` digest, and exact preparation/application key-set tests define the closed contract.

### F5 — minor — resolved — normative stale-input, privacy, and deep-copy rows were incomplete

The initial tests covered basic Class B/Class C success, cancellation, one stale digest, exact refusal, and retired current position, but not the complete issue-owned matrix.

Resolution: regressions cover Class B and deterministic Class C application, complete source/target/manifest binding, retired-only evidence changes that leave the candidate unchanged, malformed and unsupported evidence, incomplete context, invalid or changed manifests, exact and incompatible refusal, unresolved retired current position, candidate structural and exact-target validity, deterministic token format, nested deep-copy independence, privacy exclusions, and no mutation on failure. The complete repository suite remains the freeze for prior v1, v2, manifest, preview, layout, CLI, and browser contracts.

### F6 — major — resolved — implementation surface and PR text disagreed about a CLI

An early review requested a prepare/apply CLI because the original PR description listed one. During issue refinement, the approved first application increment was deliberately narrowed to an explicit in-memory API; filesystem writes, downloads, browser integration, and an application CLI are deferred with publication policy.

Resolution: issue #48 and the normative contract now define `prepare_migration(...)` and `apply_confirmed_migration(...)` as the complete increment. The final PR description reflects this API-only boundary rather than the superseded CLI plan.

### F7 — major — resolved — unreadable file-backed inputs were not normalized in shared loaders

The application depends on preview/module loaders whose unreadable-path handling initially escaped the closed error model.

Resolution: corrective issue #53 / PR #55 merged as `4b6caf0`; PR #51 was rebased onto that correction before final validation. This in-memory increment itself accepts validated objects and preserves the corrected shared-loader regressions.

### F8 — test — resolved — stale-manifest regression changed eligibility before token comparison

A pre-rewrite stale-token test changed a lossless preserve-only manifest into a transition that retired the active step. The authoritative preview correctly became unresolved and candidate-unavailable before the test could reach stale-token comparison.

Resolution: the rewritten tests separate eligibility refusal from stale-token binding. Manifest changes used for token-binding checks remain structurally and contextually meaningful, while unresolved retired-current behavior has its own fail-closed regression.

### F9 — minor — resolved — token validator accepted uppercase hexadecimal

The token parser used `string.hexdigits`, which accepts uppercase hexadecimal even though the normative contract requires exactly 64 lowercase hexadecimal digits.

Resolution: validation now accepts only `0123456789abcdef`; dedicated regressions refuse otherwise well-shaped uppercase tokens and prove all input objects remain unchanged.

### F10 — major — resolved — omitted confirmation arguments escaped as Python invocation errors

The public application function originally required both confirmation keyword arguments at the Python signature boundary. A caller omitting either value could receive a raw `TypeError` before the deterministic application error contract ran.

Resolution: `confirmed` defaults to `False` and `confirmation_token` defaults to `None`; omitted values now fail under `$.confirmation.confirmed` or `$.confirmation.token` without inspecting, mutating, or applying the migration. A regression calls the API with both values omitted and requires `EvidenceMigrationApplicationError`.

### F11 — major — resolved — a superseded CLI reintroduced the removed confirmation API

After the API-only boundary had been documented and F6 resolved, a later branch commit reintroduced `confirm_evidence_migration_v2.py` and CLI tests that called the removed `confirmation_digest` helper and `confirmed_digest` keyword. GitHub Actions run 621 failed in unit tests, and the CLI also contradicted the approved in-memory API-only increment.

Resolution: the superseded CLI and its tests were removed. The authoritative surface remains only `prepare_migration(...)` and `apply_confirmed_migration(...)`; the next green run must cover the resulting seven-file diff before final reviews.

## Open findings

None. Actions and two consecutive clean review rounds are still required on one unchanged final head before protected squash merge.
