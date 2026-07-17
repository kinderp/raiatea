# Normative amendment: published module revision immutability

Status: corrective normative amendment to [`module-evolution-and-evidence-compatibility.md`](module-evolution-and-evidence-compatibility.md), created after the final-head findings left unresolved by PR #26.

Related issue: #28.  
Corrective PR: #30.

## Purpose

The module-evolution decision states that `(moduleId, revision)` identifies one published module state and must be unique. This amendment makes the temporal consequence explicit: publication creates a permanent identity binding, not a mutable label that can later point to different authored content.

## Normative invariant

After a module revision is published, the pair:

```text
(moduleId, revision)
```

must identify exactly one immutable authored module state for the lifetime of the route history.

Therefore:

- the published pair must never be overwritten with different authored content;
- the revision value must never be reused within the same module route, including after that revision or the entire route is retired;
- a correction, replacement, restored historical version, translation decision, or later publication must use a new revision identifier whenever its authored state differs;
- deleting a current file or branch does not release the historical identifier for reuse;
- evidence documents and migration manifests that reference a published pair must continue to resolve to the original state, not to whichever file currently carries the same strings;
- revision identifiers remain opaque: immutability does not introduce numeric, lexical, chronological, or semantic ordering.

A rebuild from unchanged authored content may reproduce the same published revision. It must be equivalent to that immutable state; it must not redefine it.

## Future validation and registry responsibility

A future revision-aware implementation needs route history or an equivalent immutable publication registry sufficient to distinguish:

- first publication of a new `(moduleId, revision)` binding;
- reproduction of the same binding from equivalent unchanged authored content;
- an invalid attempt to republish the binding with divergent content;
- an invalid attempt to reuse a retired revision identifier;
- an unknown revision referenced by evidence or a migration manifest.

The exact integrity mechanism is a later implementation decision. It may use reviewed history records, immutable manifests, content digests, a registry, or another auditable method. The architecture requirement is behavioral: divergent republishing and historical collisions must be detected and must fail closed. A validator must not silently replace the historical binding or reinterpret existing evidence.

## Required failure behavior

When a future tool detects reuse or divergent republishing of a published revision pair, it must:

1. reject publication, compatibility classification, or migration before any state change;
2. report the exact module ID and revision involved without reproducing unnecessary learner evidence;
3. preserve the original historical binding, evidence file, current browser progress, and external systems unchanged;
4. require the author to choose a new revision identifier for the changed authored state;
5. avoid selecting a “newer” or “closest” revision because opaque identifiers define no ordering.

## Test responsibility

The normative matrix in [`module-evolution-test-responsibilities.md`](module-evolution-test-responsibilities.md) assigns this invariant to the future fixture:

```text
reused-revision-divergent-content-invalid
```

That fixture must prove that a route history or publication registry rejects a second, different authored state for the same pair, including after retirement. Tests may assert exact equality or difference between identifiers; they must not assert that one opaque revision is greater, newer, or later by parsing the identifier itself.

## Relationship to learner-evidence v1

This amendment changes no current schema or runtime behavior. Learner-evidence v1 remains frozen under its existing module-ID, ordered-index, and authored-step-title compatibility rules. Revision-aware modules, evidence v2, publication registries, migration manifests, and migration runtime remain separate future increments.

## Decision summary

Published revision identity is permanent. `(moduleId, revision)` is an immutable historical binding, never a reusable pointer. Any divergent authored state requires a new revision identifier, and future tooling must fail closed rather than allowing old evidence or manifests to acquire new meaning.
