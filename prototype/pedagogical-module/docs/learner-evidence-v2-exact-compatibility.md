# Learner-evidence v2 exact contextual compatibility

Status: implementation contract for issue #38. This increment evaluates Class A exact compatibility between one structurally valid learner-evidence v2 document and one structurally valid canonical module revision.

## Inputs

The checker receives two explicit local files:

- one canonical pedagogical module;
- one learner-evidence v2 document.

Each input is structurally validated by its existing canonical loader before contextual comparison begins. Structural errors stop the operation and are not converted into contextual compatibility reasons.

## Exact compatibility

A document is exactly compatible only when:

- evidence `module.id` equals canonical module `id`;
- evidence `module.revision` equals canonical module `revision` by exact equality;
- evidence `module.stepCount` equals the active canonical step count;
- evidence contains the same ordered stable step-ID sequence as the supplied canonical revision;
- evidence `currentStepId` names the canonical step at `currentStepIndex`.

The ordered sequence check is not an identity inference from indexes. Stable IDs carry conceptual identity; indexes preserve the authored route order of the exact source revision and must agree when the claimed revision is the same immutable published state.

## Explanatory fields

The following are not compatibility keys:

- module title;
- language;
- source metadata;
- step titles.

They remain useful snapshots for people and auditing, but the checker must not infer identity, compatibility, or incompatibility from wording differences.

## Failure semantics

The checker is deterministic, side-effect free, and fail closed. It reports all contextual mismatches after both inputs pass structural validation. It does not mutate files, browser storage, or generated evidence.

Revision values are opaque. A mismatch means only that the supplied evidence and module identify different revisions; the checker must not describe one as older, newer, previous, next, higher, or lower.

## Out of scope

- publication registries and proof that a revision was historically published;
- divergent reuse detection for a published `(moduleId, revision)` pair;
- compatibility classes other than Class A exact;
- authored migration manifests or path selection;
- rename, reorder, insertion, retirement, split, merge, correction, or replacement migration;
- preview, confirmation, restore, browser integration, and state mutation;
- learner-evidence v1 changes.

A contextual mismatch is not automatically Class D incompatible or Class E unsupported. Those classifications require a later classifier with publication and manifest context.
