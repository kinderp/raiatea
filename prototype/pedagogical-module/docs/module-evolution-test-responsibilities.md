# Module evolution: future test responsibilities

Status: acceptance and test-responsibility appendix to [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md).

This appendix is subordinate to the architecture decision. It assigns every required module-evolution scenario to the future fixture, validator, compatibility classifier, migration preview, and state-transition test that must own it. It does **not** claim that the current repository already implements stable IDs, revisions, publication history, manifests, evidence v2, or migrations.

## Responsibility matrix

| Scenario | Future fixture | Validator responsibility | Compatibility / preview responsibility | State-changing responsibility | Current implementation status |
| --- | --- | --- | --- | --- | --- |
| Title rename, same responsibility | `rename-same-step-id` old/new module pair | Accept the same valid stable step ID in both explicit revisions | Classify as lossless only when authored identity and every allowlisted evidence field are preserved; show title change | Preserve evidence only after explicit future migration confirmation | Contract only; no current fixture or migration runtime |
| Reorder existing steps | `reorder-stable-step-ids` pair | Validate unique IDs and canonical order within each revision | Map by stable ID, show old/new positions, and classify lossless only when `currentStep` and every allowlisted field map deterministically | Move progression using the authored target-step/position policy after preview | Contract only |
| Insert new step | `insert-new-step` pair | Require a new unique ID and reject reuse of retired IDs | Preserve existing mapped evidence; show the new step initialized empty | Write empty evidence for the introduced step only after confirmation | Contract only |
| Content correction without changed diagnostic meaning | `content-correction-same-meaning` pair | Validate a new revision and stable identity | Require an authored declaration that evidence meaning is unchanged; preview the correction | Preserve mapped evidence after confirmation | Contract only |
| Changed diagnostic meaning | `diagnostic-meaning-changed` pair | Validate revision and IDs but do not infer evidence validity | Classify as partial or incompatible according to an authored reset/archive policy | Reset or archive affected evidence; never preserve correctness by default | Contract only |
| One-to-many split | `split-one-to-many` old/new pair plus manifest | Validate source ID, all destination IDs, uniqueness, direction, and explicit split policy | Classify partial; show that the source ID is retired by default and that at most one target may preserve identity only with authored same-responsibility rationale; no evidence fan-out | Apply only the authored historical-only/reset/preserve-one mapping after confirmation; never copy `correct` to multiple targets | Contract only |
| Many-to-one merge | `merge-many-to-one` pair plus manifest | Validate all sources, one destination, retired IDs, and any explicitly permitted preserve-one rationale | Classify partial or incompatible; show information loss. No attempts/correctness aggregation exists unless a later closed contract defines an exact field policy | Reset or archive source evidence by default; apply a later explicit field policy only after validation and confirmation | Contract only |
| Step retirement | `retire-step` pair plus manifest | Validate that the retired ID remains reserved and is not reused | Show historical-only/dropped evidence and current-position fallback; classify partial unless every field is deterministically preserved | Remove active attachment without reassigning evidence to another step | Contract only |
| Incompatible replacement | `replace-unrelated-step` pair | Validate a new unique ID and retirement of the old ID | Classify incompatible unless a separate reviewed migration policy safely covers the evidence meaning | Block restore/migration by default | Contract only |
| Duplicate step IDs | `duplicate-step-id-invalid` module | Reject duplicate IDs deterministically | No preview because structural validation fails first | No state change | Contract only |
| Recycled retired step ID | `recycled-retired-step-id-invalid` revision chain | Reject reuse against the route's publication history or registry | No compatible classification | No state change | Contract only |
| Divergent revision republishing | `revision-republish-divergent-invalid` publication history | Reject different authored content under an already published `(moduleId, revision)`, including after retirement | Report immutable revision collision; do not classify against the divergent state | Preserve published history and current evidence unchanged | Contract only |
| Identical deterministic rebuild | `revision-rebuild-identical-valid` publication history | Accept reproduction of the same authored state under the same pair without creating a new revision | Treat as the same published state, not a migration | No evidence change | Contract only |
| Unknown source revision | `unknown-source-revision` evidence/manifest | Reject or mark unsupported before mapping | Report unsupported source revision and no migration path | No state change | Contract only |
| Unknown target revision | `unknown-target-revision` manifest/module | Reject target mismatch | Report unsupported target revision | No state change | Contract only |
| Manifest for another module | `cross-module-manifest-invalid` | Reject exact module-ID mismatch | No mapping preview beyond explicit mismatch | No state change | Contract only |
| Incomplete mapping | `incomplete-manifest-invalid` | Reject missing evidence-bearing or required step decisions | Report every unmapped source, target, and progression field | No state change | Contract only |
| Ambiguous mapping | `ambiguous-manifest-invalid` | Reject duplicate destinations, conflicting rules, and non-deterministic policies | Explain ambiguity; never guess from title similarity | No state change | Contract only |
| Unsupported evidence version | `unsupported-evidence-version` | Reject before compatibility or migration analysis | Report unsupported version | No state change | Current v1 tools already reject unsupported versions; stable-ID migration fixture remains future work |
| Unsupported migration-manifest version | `unsupported-manifest-version` | Future manifest validator rejects before mapping | Report unsupported manifest version | No state change | Contract only |
| Malicious or executable manifest content | `manifest-active-content-invalid` | Reject unknown fields, URLs-to-execute, templates, scripts, and arbitrary expressions | No execution and no mapping | No state change | Contract only |
| Obsolete asynchronous preview | `migration-preview-out-of-order` browser fixture | Structural checks remain side-effect free | Only the latest selection/revision request may become confirmable | Older completion cannot overwrite newer pending state | Current restore race test is analogous; migration-specific fixture is future work |
| Local progress changes after preview | `migration-preview-stale` browser fixture | Revalidation token/snapshot checked before confirmation | Invalidate preview and require reselection/recalculation | No migration from stale preview | Current v1 restore has analogous coverage; migration-specific fixture is future work |
| Cancel migration | `migration-cancel-no-op` browser fixture | Selected documents may validate | Preview can be dismissed | Original local evidence and source document remain unchanged | Contract only |
| Migration application failure | `migration-atomic-failure` fixture | Validate source, target, manifest, and deterministic output before write | Preview exact replacement and failure recovery | Apply atomically or preserve original evidence; never leave partial state | Contract only |
| Migrated current step removed, split, or merged | `current-step-fallback` fixture family | Validate authored fallback references | Preview the destination or reviewed fallback and explain why | Write new current position only after confirmation | Contract only |
| V1 evidence against stable-ID module | `v1-unchanged-compatibility` regression | Continue current v1 title/index structural rules | Do not infer stable IDs or revisions from v1 titles | Existing v1 restore behavior remains unchanged | Existing v1 behavior; future schema work must preserve regression |

## Required test layers for future implementation PRs

A future implementation issue must select the relevant rows above and add tests at every applicable layer:

1. **Schema/structural fixtures** — valid and invalid module, evidence, and migration-manifest JSON documents.
2. **Validator unit tests** — exact paths and deterministic reasons for invalid IDs, revisions, versions, and mappings.
3. **Publication-history tests** — immutable `(moduleId, revision)` binding, identical rebuild acceptance, divergent republishing rejection, and retired-identifier non-reuse.
4. **Compatibility-classifier tests** — exact, lossless, partial, incompatible, and unsupported outcomes.
5. **Migration-output tests** — deterministic transformed evidence with explicit attempts, correctness, remediation, and current-step semantics.
6. **Preview tests** — human-readable disclosure of preserved, reset, introduced, retired, split, merged, historical-only, and dropped data.
7. **Browser state-transition tests** — explicit confirmation, cancel/no-op, stale-preview invalidation, out-of-order completion, atomic failure, and original-evidence preservation.
8. **V1 regression tests** — proof that current v1 schema, compatibility, export, and restore behavior has not been silently widened.

## Definition of future completion

No stable-ID or migration implementation PR is complete merely because the architecture documents contain examples. Its issue and PR must:

- name the matrix rows in scope;
- add the corresponding repository fixtures;
- show which validator, publication-history, classifier, output, preview, or browser test owns each row;
- link the exact test files and passing CI run;
- record out-of-scope rows explicitly;
- avoid claiming coverage for rows that remain contract-only.

Until those future fixtures and validators are merged, this matrix is a responsibility assignment and acceptance checklist, not evidence of implemented migration support.
