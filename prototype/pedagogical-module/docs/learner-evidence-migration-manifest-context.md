# Contextual migration-manifest validation

Status: implementation contract for issue #43. This increment checks one structurally valid migration manifest against two supplied structurally valid canonical module revisions without selecting a migration path, previewing evidence, or mutating progress.

## Inputs

The checker receives three explicit local files:

- the canonical source module revision;
- the canonical target module revision;
- one migration manifest.

Each file is validated through its existing structural loader before contextual comparison begins.

## Exact contextual match

The manifest is contextually valid for the supplied modules only when:

- source and target modules have the same exact module ID;
- source and target revisions are distinct exact identities;
- manifest source module ID and revision equal the supplied source module;
- manifest target module ID and revision equal the supplied target module;
- manifest source `stepIds` exactly equal the source module's ordered active stable-ID sequence;
- manifest target `stepIds` exactly equal the target module's ordered active stable-ID sequence.

Stable IDs carry identity. Ordered inventories additionally bind the manifest to the authored route of each exact immutable revision.

## Explanatory fields

Module titles, language, source metadata, step titles, visual content, quizzes, and provenance are not contextual manifest keys.

## Failure semantics

The checker reports every deterministic contextual mismatch after all three inputs pass structural validation. It does not mutate files or browser state. Revision mismatch indicates inequality only; no older/newer, higher/lower, chronological, semantic, or precedence ordering is inferred.

## Out of scope

- publication registries and proof that either revision was historically published;
- divergent revision-reuse detection;
- manifest path selection or multiple candidates;
- compatibility classes B–E;
- human-readable evidence preview;
- migration application, confirmation, browser integration, and storage mutation;
- split/merge evidence policy.
