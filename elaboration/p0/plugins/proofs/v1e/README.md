# Plugin API v1e — deterministic TransformerPlugin proof

Status: **Draft / proof-only**.

Issue: #174  
Parent: #147

This proof completes the initial Source / Extractor / Transformer architecture set with one intentionally small transformation: UTF-8 newline normalization.

## Operation

```text
transform.run / normalize-newlines-v1
```

The plugin converts CRLF and bare CR to LF. It is deterministic, uses no network, secrets, AI/LLM or layout logic, never mutates its input and writes only to Core-issued output handles.

## Boundary

The proof runs out of process over the accepted ADR-0001 local transport and imports the accepted v1d proof-only broker solely as test equipment. Host paths remain outside public runtime/domain records.

Two Core-issued output targets are used:

1. derived text bytes;
2. a proof bundle containing `TransformationRecord` and `DerivedArtifactRecord`.

The proof bundle is not a production storage format. The domain records are validated against `elaboration/p0/contracts/transformations/0.1.0/`.

## Transformation contract

The candidate/internal 0.1.0 contract exists only because Raiatea had no executable TransformationRecord/DerivedArtifact shape yet. It is deliberately minimal:

- source and derived artifact identities + opaque handle ids;
- media type, byte length and SHA-256;
- `derived-from` lineage;
- transformation/operation/plugin/profile identity;
- invocation id and timing;
- explicit parameters;
- deterministic flag;
- optional Core RightsDecisionRef reference only.

It does not reuse E-05 ProcessingOutcome, does not define workflow orchestration and does not own rights authority.

## Invariants under test

- input bytes remain unchanged;
- output identity differs from input identity even if output bytes could be equal;
- output is written only to a Core-issued write-once handle;
- input/output fingerprints match actual bytes;
- TransformationRecord and DerivedArtifactRecord agree exactly on lineage;
- runtime provenance agrees with input/output handle and record refs;
- identical input/parameters produce byte-identical output;
- public records contain no host path;
- wrong media/profile/expiry/fingerprint/authority fail closed.

## Deferred

Translation, summarization, format conversion, layout reconstruction, transform registry/workflow execution, production handle brokering, remote plugins and cross-project runtime extraction remain out of scope.
