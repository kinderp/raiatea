# Contextual migration-manifest validation contract

Status: design and implementation contract for issue #43.

This increment validates one closed learner-evidence migration manifest against the two exact canonical module revisions supplied by the caller. It does not receive learner evidence, classify compatibility, choose a migration path, generate a learner-facing preview, or mutate progress.

## Inputs

The checker receives exactly three caller-supplied JSON documents:

1. `sourceModule`: the canonical module revision named by `manifest.source`;
2. `targetModule`: the canonical module revision named by `manifest.target`;
3. `manifest`: one learner-evidence migration manifest v1.

Each document is structurally validated by its existing validator before contextual comparison. Structural failure is reported under the corresponding input namespace and prevents contextual claims about that invalid input.

## Authoritative identity

The contextual checker requires:

- `manifest.source.moduleId == sourceModule.id`;
- `manifest.source.revision == sourceModule.revision`;
- `manifest.source.stepIds` exactly equals the ordered `id` sequence authored in `sourceModule.steps`;
- `manifest.target.moduleId == targetModule.id`;
- `manifest.target.revision == targetModule.revision`;
- `manifest.target.stepIds` exactly equals the ordered `id` sequence authored in `targetModule.steps`.

The two module inputs must therefore describe the same route already required by the structural manifest contract. Direction comes only from the explicit `source` and `target` roles. Revision values remain opaque and are never interpreted as chronological, numeric, lexical, semantic, adjacent, older, newer, higher, or lower.

Module titles, language, source metadata, authored step titles, visual node IDs, concept IDs, and provenance remain explanatory or domain-specific context. They are not migration-manifest identity keys.

## Error paths and deterministic ordering

Contextual mismatches are rooted at the manifest field that makes the false declaration and reference the compared module field in the message. The initial order is fixed:

1. `$.manifest.source.moduleId`;
2. `$.manifest.source.revision`;
3. `$.manifest.source.stepIds`;
4. `$.manifest.target.moduleId`;
5. `$.manifest.target.revision`;
6. `$.manifest.target.stepIds`.

An ordered inventory mismatch produces one deterministic issue at the inventory path. When endpoint module ID and revision already match, the issue describes the directly observable difference:

- different inventory lengths, including missing and unknown IDs;
- equal-length replacement, including missing and unknown IDs;
- the exact same IDs in a different order.

When endpoint identity itself is mismatched, the checker keeps the inventory diagnostic conservative and reports only the two compared sequences. These messages describe factual set, length, and order differences; they do not classify compatibility, infer author intent, choose a preserve/retire/introduce operation, or decide whether a migration is safe.

Structural failures are prefixed by input namespace in source-module, target-module, manifest order. Contextual comparison runs only when all three inputs are structurally valid.

## API and CLI behavior

The side-effect-free API returns a deterministic list of contextual issues. A convenience loader validates and reads the three files without modifying them.

The CLI accepts arguments in this order:

```text
check_evidence_migration_manifest_context.py SOURCE_MODULE TARGET_MODULE MANIFEST
```

It exits `0` only when every input is structurally valid and all six contextual comparisons match. It exits `1` for malformed JSON, structural validation failure, unsupported formats or versions, or contextual mismatch. Success output identifies the exact source and target module/revision pairs without deriving ordering from revision values.

## Explicit boundary

This checker proves only that one internally valid manifest truthfully describes the two exact canonical revisions supplied by the caller. It does not prove publication, immutability, registry membership, uniqueness among manifests, path completeness, path selection, or applicability to a learner-evidence document.

Deferred work includes:

- publication registry lookup and immutable revision retrieval;
- compatibility classes B–E;
- learner-evidence classification;
- migration path lookup or chaining;
- human-readable preview;
- split or merge policy;
- browser v2 import/export;
- confirmation, original-copy preservation, and migration application.
