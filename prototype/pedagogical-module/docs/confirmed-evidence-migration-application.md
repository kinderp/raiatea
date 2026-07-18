# Confirmed learner-evidence migration application contract

Status: normative implementation contract for issue #48 and PR #51.

This increment applies one eligible learner-evidence v2 migration only after explicit caller confirmation. It preserves the original input object and returns a separately validated migrated copy. The implementation is entirely in memory: it performs no filesystem, browser-storage, network, download, replacement, deletion, or retention operation.

## 1. Two-phase boundary

The authoritative API is deliberately split:

1. `prepare_migration(...)` validates complete current inputs, recomputes the read-only preview, rejects non-applicable outcomes, revalidates the candidate, and returns a closed preparation result containing a versioned confirmation token.
2. `apply_confirmed_migration(...)` requires explicit confirmation, repeats the complete preparation from fresh deep-copied inputs, compares the supplied token with the newly computed token, and only then returns separate `original` and `migrated` copies.

A caller cannot supply or edit a candidate or preview and ask the application layer to trust it. Preparation and application both derive from the authoritative preview engine.

## 2. Structurally valid inputs

The in-memory API receives:

- one learner-evidence v2 object;
- one exact target canonical module object;
- an optional source canonical module and direct migration manifest, supplied together;
- explicit confirmation state and the versioned token for application.

Before classification, the API structurally validates evidence, target module, source module, and manifest in deterministic namespace order. Malformed objects fail as `EvidenceMigrationApplicationError` issues under `evidence`, `targetModule`, `sourceModule`, `manifest`, or `migrationContext`; raw `KeyError` and `TypeError` are not public failure modes.

## 3. Eligible classifications

Preparation is eligible only when:

- classification is `declared-lossless` or `declared-partial`;
- `candidateAvailable` is true and the candidate is an object;
- current position is deterministic and not `unresolved-retired`;
- the candidate is structurally valid learner-evidence v2;
- the candidate is an exact contextual match for the target module revision.

Class A `exact` is a no-op and is refused. `incompatible`, `unsupported`, unresolved, missing-candidate, malformed, or incomplete-context inputs fail closed.

## 4. Exact confirmation projection

The token format is:

```text
raiatea-confirm-v1:<64 lowercase hexadecimal SHA-256 digits>
```

It is computed from canonical UTF-8 JSON with sorted object keys, stable array order, and no insignificant whitespace. The closed projection contains:

- `contractVersion`;
- the complete validated learner-evidence v2 object;
- the complete validated source module or `null`;
- the complete validated target module;
- the complete validated manifest or `null`;
- the complete freshly recomputed preview result, including classification, identities, manifest status, deterministic step outcomes, current position, candidate availability, and candidate.

This binds confirmation to changes that may not affect the migrated candidate, including retired-only evidence and source/target authored metadata. JSON object key ordering is intentionally normalized. The token is a deterministic integrity binding, not a signature, authentication mechanism, identity proof, or non-repudiation claim.

## 5. Closed preparation result

A successful preparation contains exactly:

- `contractVersion`;
- `applicable: true`;
- `classification`;
- `source` and `target` exact identities;
- `manifestStatus`;
- `currentPosition`;
- `candidateDigest` using `sha256:<hex>`;
- `confirmationToken`;
- deterministic `summary`.

It contains no path, timestamp, account, learner identity, analytics, telemetry, browser-storage key, or network destination.

## 6. Closed application result

A successful application contains exactly:

- `contractVersion`;
- `applied: true`;
- exact source and target identities;
- classification and manifest status;
- candidate digest and the matched confirmation token;
- `original`, a deep copy of the validated source evidence snapshot;
- `migrated`, a deep copy of the immediately revalidated candidate;
- deterministic summary.

Mutating any returned nested object cannot change caller inputs, the preparation result, or another returned copy.

## 7. Failure and side-effect semantics

Application refuses:

- missing or false confirmation;
- malformed or stale token;
- partial source/manifest context;
- malformed evidence, module, or manifest objects;
- exact/no-op, incompatible, unsupported, unresolved, or unavailable-candidate outcomes;
- changed evidence, source module, target module, manifest, classification, current position, preview, or candidate after preparation;
- candidate structural or target-compatibility failure.

Preparation and application deep-copy before validation/classification and never mutate supplied objects. Every failure returns no applied result. The implementation reads no browser storage, performs no network access, and writes no file.

## 8. Verification responsibility

Tests own:

- Class B and deterministic Class C success;
- exact and incompatible refusal;
- retired-current refusal;
- confirmation shape and stale-token refusal;
- complete input binding, including retired-only evidence and source/target metadata not represented in the candidate;
- malformed and incomplete-context namespaced failures;
- candidate structural validity and exact target compatibility;
- closed preparation/application key sets and token format;
- deep-copy independence and no mutation on all paths;
- privacy exclusions;
- unchanged learner-evidence v1 and all prior v2, manifest, contextual-validation, preview, layout, CLI, and browser regressions.

## 9. Deferred work

The following require separate child issues and PRs:

- filesystem destination selection and atomic no-overwrite publication;
- collision, symbolic-link, alias, permission, fsync, cleanup, and durability policy;
- browser v2 import/export and confirmation UI;
- downloads, backup, retention, and deletion controls;
- cryptographic signatures or external identity;
- registry lookup, path selection, and multi-hop migration;
- split, merge, fan-in, fan-out, aggregation, or semantic mapping;
- cloud, LMS, accounts, analytics, encryption, telemetry, or remote storage.
