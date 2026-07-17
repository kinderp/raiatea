# Module evolution: future test responsibilities

Status: normative test appendix to [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md).

This appendix assigns every required module-evolution scenario to the future fixture, validator, compatibility classifier, migration preview, and state-transition test that must own it. It does **not** claim that the current repository already implements stable IDs, revisions, manifests, evidence v2, or migrations.

## Responsibility matrix

| Scenario | Future fixture | Validator responsibility | Compatibility / preview responsibility | State-changing responsibility | Current implementation status |
| --- | --- | --- | --- | --- | --- |
| Title rename, same concept | `rename-same-step-id` old/new module pair | Accept same valid stable step ID in both revisions; validate explicit revision increase | Classify as lossless only when authored identity is preserved; show title change | Preserve evidence only after explicit future migration confirmation | Contract only; no current fixture or migration runtime |
| Reorder existing steps | `reorder-stable-step-ids` pair | Validate unique IDs and canonical order within each revision | Map by stable ID, show old/new positions, classify lossless when semantics are unchanged | Move `currentStep` using authored policy after preview | Contract only |
| Insert new step | `insert-new-step` pair | Require a new unique ID and reject reuse of retired IDs | Preserve existing mapped evidence; show new step initialized empty | Write empty evidence for the introduced step only after confirmation | Contract only |
| Content correction without changed diagnostic meaning | `content-correction-same-meaning` pair | Validate revision change and stable identity | Require an authored declaration that evidence meaning is unchanged; preview the correction | Preserve mapped evidence after confirmation | Contract only |
| Changed diagnostic meaning | `diagnostic-meaning-changed` pair | Validate revision and IDs but do not infer evidence validity | Classify as partial or incompatible according to authored reset/archive policy | Reset or archive affected evidence; never preserve correctness by default | Contract only |
| One-to-many split | `split-one-to-many` old/new pair plus manifest | Validate source ID, all destination IDs, uniqueness, direction, and explicit split policy | Classify partial; show which destination inherits, resets, or archives evidence | Apply only the authored mapping after confirmation; no automatic fan-out of `correct` | Contract only |
| Many-to-one merge | `merge-many-to-one` pair plus manifest | Validate all sources, one destination, and explicit aggregation policy | Classify partial; preview attempts/correctness aggregation and information loss | Apply only explicit aggregation after confirmation; no universal default | Contract only |
| Step retirement | `retire-step` pair plus manifest | Validate retired ID is reserved and not reused | Show archived/dropped evidence and current-position fallback; classify lossless or partial explicitly | Remove active attachment without reassigning evidence to another step | Contract only |
| Incompatible replacement | `replace-unrelated-step` pair | Validate new unique ID and retirement of old ID | Classify incompatible unless an explicit reviewed migration policy exists | Block restore/migration by default | Contract only |
| Duplicate step IDs | `duplicate-step-id-invalid` module | Reject duplicate IDs deterministically | No preview because structural validation fails first | No state change | Contract only |
| Recycled retired ID | `recycled-retired-step-id-invalid` revision chain | Reject reuse against the route's revision history or registry | No compatible classification | No state change | Contract only |
| Unknown source revision | `unknown-source-revision` evidence/manifest | Reject or mark unsupported before mapping | Report unsupported source revision and no migration path | No state change | Contract only |
| Unknown target revision | `unknown-target-revision` manifest/module | Reject target mismatch | Report unsupported target revision | No state change | Contract only |
| Manifest for another module | `cross-module-manifest-invalid` | Reject exact module-ID mismatch | No mapping preview beyond explicit mismatch | No state change | Contract only |
| Incomplete mapping | `incomplete-manifest-invalid` | Reject missing evidence-bearing or required step decisions | Report every unmapped source/destination | No state change | Contract only |
| Ambiguous mapping | `ambiguous-manifest-invalid` | Reject duplicate destinations, conflicting rules, and non-deterministic policies | Explain ambiguity; never guess from title similarity | No state change | Contract only |
| Unsupported evidence version | `unsupported-evidence-version` | Reject before compatibility or migration analysis | Report unsupported version | No state change | Current v1 tools already reject unsupported versions; stable-ID migration fixture remains future work |
| Unsupported migration-manifest version | `unsupported-manifest-version` | Future manifest validator rejects before mapping | Report unsupported manifest version | No state change | Contract only |
| Malicious or executable manifest content | `manifest-active-content-invalid` | Reject unknown fields, URLs-to-execute, templates, scripts, and arbitrary expressions | No execution and no mapping | No state change | Contract only |
| Obsolete asynchronous preview | `migration-preview-out-of-order` browser fixture | Structural checks remain side-effect free | Only latest selection/revision request may become confirmable | Older completion cannot overwrite newer pending state | Current restore race test is analogous; migration-specific fixture is future work |
| Local progress changes after preview | `migration-preview-stale` browser fixture | Revalidation token/snapshot checked before confirmation | Invalidate preview and require reselection/recalculation | No migration from stale preview | Current v1 restore has analogous coverage; migration-specific fixture is future work |
| Cancel migration | `migration-cancel-no-op` browser fixture | Selected documents may validate | Preview can be dismissed | Original local evidence and source document remain unchanged | Contract only |
| Migration application failure | `migration-atomic-failure` fixture | Validate source, target, manifest, and deterministic output before write | Preview exact replacement and failure recovery | Apply atomically or preserve original evidence; never leave partial state | Contract only |
| Migrated current step removed/split/merged | `current-step-fallback` fixture family | Validate authored fallback references | Preview destination or reviewed fallback and explain why | Write new current position only after confirmation | Contract only |
| V1 evidence against stable-ID module | `v1-unchanged-compatibility` regression | Continue current v1 title/index structural rules | Do not infer stable IDs or revisions from v1 titles | Existing v1 restore behavior remains unchanged | Existing v1 behavior; future schema work must preserve regression |

## Required test layers for future implementation PRs

A future implementation issue must select the relevant rows above and add tests at every applicable layer:

1. **Schema/structural fixtures** — valid and invalid module, evidence, and migration-manifest JSON documents.
2. **Validator unit tests** — exact paths and deterministic reasons for invalid IDs, revisions, versions, and mappings.
3. **Compatibility-classifier tests** — exact, lossless, partial, incompatible, and unsupported outcomes.
4. **Migration-output tests** — deterministic transformed evidence with explicit attempts, correctness, remediation, and current-step semantics.
5. **Preview tests** — human-readable disclosure of preserved, reset, introduced, retired, split, merged, and dropped data.
6. **Browser state-transition tests** — explicit confirmation, cancel/no-op, stale-preview invalidation, out-of-order completion, atomic failure, and original-evidence preservation.
7. **V1 regression tests** — proof that current v1 schema, compatibility, export, and restore behavior has not been silently widened.

## Definition of future completion

No stable-ID or migration implementation PR is complete merely because the architecture document contains examples. Its issue and PR must:

- name the matrix rows in scope;
- add the corresponding repository fixtures;
- show which validator or preview test owns each row;
- link the exact test files and passing CI run;
- record out-of-scope rows explicitly;
- avoid claiming coverage for rows that remain contract-only.

Until those future fixtures and validators are merged, this matrix is a responsibility assignment and acceptance checklist, not evidence of implemented migration support.
