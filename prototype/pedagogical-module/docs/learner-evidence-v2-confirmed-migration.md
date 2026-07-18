# Confirmed learner-evidence v2 migration application contract

Status: initial normative design for issue #48.

This increment applies one already classifiable direct learner-evidence v2 transition only after explicit caller confirmation. Application creates one new evidence copy, never overwrites or deletes the original, never changes browser storage, and never treats a compatibility preview as authorization by itself.

## 1. Scope and inputs

The application boundary receives local caller-supplied paths for:

1. one learner-evidence v2 source document;
2. one exact target canonical module revision;
3. one exact canonical source module revision;
4. one direct migration manifest from the source revision to the target revision;
5. one destination path that does not already exist;
6. an explicit confirmation token for the exact prepared application.

The existing preview engine is authoritative for classification and candidate construction. Application never reimplements mapping policy. Immediately before any write it reruns structural validation, exact source matching, contextual manifest validation, classification, preview generation, and candidate invariants from the current bytes on disk.

The initial application increment accepts only:

- `declared-lossless` with `candidateAvailable: true`; or
- `declared-partial` with `candidateAvailable: true` because the current stable step is preserved and deterministically remapped.

It refuses:

- `exact`, because no migration is required;
- `incompatible` or `unsupported`;
- every result with no candidate;
- `unresolved-retired` current position;
- incomplete source/manifest context;
- malformed, stale, or changed inputs;
- any source and destination alias;
- any destination that already exists.

## 2. Two-phase API

Application is split into preparation and commit. Preparation is side-effect free.

### 2.1 Prepare

`prepare_migration(...)`:

- reads and validates the current source, source module, target module, and manifest;
- obtains the authoritative compatibility preview;
- refuses any non-applicable classification or unavailable candidate;
- computes deterministic hashes and a confirmation token;
- returns a closed preparation object;
- creates no file and changes no input object or browser state.

The preparation object contains only:

- classification;
- source module ID and opaque revision;
- target module ID and opaque revision;
- source evidence SHA-256 digest over the exact source file bytes;
- source module, target module, and manifest SHA-256 digests over their exact input bytes;
- candidate SHA-256 digest over canonical UTF-8 JSON bytes;
- candidate byte length;
- deterministic confirmation token;
- read-only preview summary and current-position status;
- `applicable: true`.

No learner identity, timestamp, account, device identifier, analytics value, free-form learner text, diagnosis, inferred mastery, network destination, or hidden telemetry is added.

### 2.2 Commit

`apply_confirmed_migration(...)` receives the same paths, destination, and confirmation token. It:

1. validates invocation shape and path safety;
2. refuses an existing destination before preparation;
3. reruns preparation from the current bytes;
4. compares the supplied token with the freshly computed token using constant-time equality;
5. rechecks source/destination non-aliasing and destination absence;
6. serializes the already validated candidate using the documented canonical JSON encoding;
7. writes and fsyncs a private temporary file in the destination directory;
8. reparses and structurally/contextually validates the temporary file;
9. verifies the source evidence bytes still match the preparation digest;
10. publishes the completed temporary file to the new destination without replacing any existing path;
11. verifies the published bytes and exact target compatibility;
12. removes temporary state and returns a closed application receipt.

No write occurs before the fresh token comparison succeeds.

## 3. Confirmation binding

Confirmation is explicit but is not a digital signature or authentication mechanism.

The confirmation token is:

```text
raiatea-confirm-v1:<hex sha256>
```

The hash input is canonical JSON with the exact allowlist:

- confirmation contract version;
- classification;
- source and target module identities;
- exact source evidence digest;
- exact source module digest;
- exact target module digest;
- exact manifest digest;
- exact candidate digest;
- candidate byte length.

Object keys are sorted, separators are compact, Unicode is encoded as UTF-8, and no path or timestamp participates. Excluding paths makes the token a confirmation of the exact evidence transition rather than a disclosure of local directory names. Destination safety is enforced independently at commit time.

A token from an earlier preparation fails if any source evidence, source module, target module, manifest, classification, candidate, or contract version changes. The token is deterministic and reviewable, but it provides no signer identity or anti-forgery guarantee; signing remains out of scope.

## 4. Candidate serialization

The migrated copy contains only the closed learner-evidence v2 candidate returned by the preview engine.

Canonical serialized form:

- UTF-8 without a byte-order mark;
- JSON object keys sorted recursively;
- indentation of two spaces;
- `ensure_ascii` disabled;
- one final newline;
- no additional application or provenance fields inside learner evidence.

Preserved observations are copied by exact stable step ID. Introduced target steps remain explicit empty observations. Retired source observations remain available only in the source evidence and read-only preview; they are not inserted into active target evidence.

## 5. Original-copy preservation

The source evidence path is opened only for reading. Application never renames, truncates, rewrites, deletes, chmods, or replaces it.

Before publication, the source bytes are reread and must match the freshly prepared digest. After publication, the source bytes are reread again and must still match. A mismatch fails closed and removes any newly created destination.

The source evidence itself is the preserved original copy. This increment does not create a second backup automatically and does not delete the source after success.

Source and destination are considered aliases and refused when any of these is true:

- their normalized absolute paths are equal;
- the destination already exists and resolves to the same file;
- the destination parent plus filename would target the source path through symbolic-link resolution;
- a race reveals an existing destination at publication time.

## 6. No-overwrite publication and failure behavior

The destination must be new. An existing file, directory, symbolic link, or other directory entry fails closed.

The reference implementation targets the local POSIX environment used by the prototype and CI:

- create a random private temporary file in the destination directory with exclusive creation and mode `0600`;
- write all canonical candidate bytes and fsync the temporary file;
- validate the complete temporary file;
- publish with an atomic no-overwrite hard-link operation from the temporary file to the destination;
- unlink the temporary name after successful publication;
- fsync the destination directory where supported.

Because publication links a complete fsynced file, readers never observe a partially written destination. The hard-link operation fails rather than replacing a destination created concurrently.

If post-publication verification fails, application removes only the newly created destination, leaves the original untouched, cleans temporary files, and reports failure. It never removes or changes a destination that existed before this invocation.

Unsupported filesystems or platforms that cannot provide the required no-overwrite publication semantics must fail as unsupported rather than fall back to an overwrite-capable operation.

## 7. Application receipt

Success returns an in-memory receipt. It is not embedded in learner evidence and is not written unless a future explicit increment defines a separate receipt export.

The closed receipt contains:

- application contract version;
- `applied: true`;
- classification;
- source and target module identities;
- confirmation token;
- source evidence digest;
- candidate and published destination digest;
- manifest digest;
- published byte length;
- `originalPreserved: true`;
- `browserStateChanged: false`.

The receipt contains no timestamp, local path, learner identity, device data, or inferred educational state.

## 8. CLI

The CLI exposes two explicit modes.

Dry-run preparation:

```bash
python prototype/pedagogical-module/build/apply_evidence_migration_v2.py \
  prepare source-evidence.json target-module.json \
  --source-module source-module.json \
  --manifest migration-manifest.json \
  --json
```

Confirmed new-copy application:

```bash
python prototype/pedagogical-module/build/apply_evidence_migration_v2.py \
  apply source-evidence.json target-module.json \
  --source-module source-module.json \
  --manifest migration-manifest.json \
  --destination migrated-evidence.json \
  --confirm 'raiatea-confirm-v1:...'
```

`prepare` never writes. `apply` requires both `--destination` and `--confirm`; a boolean flag such as `--yes` is insufficient because it would not bind confirmation to the exact prepared transition.

Human output must state whether the operation was preparation-only or applied, whether the original remained unchanged, and whether browser state was untouched. JSON output uses the same closed preparation or receipt model.

## 9. Deterministic failures

The API and CLI fail closed for:

- malformed JSON or structural validation failure;
- unsupported evidence or manifest version or operation;
- exact/no-migration-required result;
- incompatible or unavailable candidate;
- unresolved retired current step;
- missing, malformed, or stale confirmation token;
- destination omission, existence, aliasing, invalid parent, or non-regular publication target;
- source bytes changing between preparation, validation, publication, and final verification;
- temporary write, flush, fsync, validation, link, cleanup, or directory-sync failure;
- post-write digest, structural, or exact contextual verification failure;
- inability to guarantee no-overwrite publication.

Failures return no success receipt. They leave all input files, browser state, and every pre-existing destination unchanged. Temporary files and any destination created solely by the failed invocation are removed on a best-effort basis; cleanup failure is reported explicitly.

## 10. Normative regression matrix

The increment owns fixtures and tests for:

- declared-lossless migration with title changes and reordered stable IDs;
- declared-partial migration with preserved current step and introduced empty observations;
- retired current step refusal;
- exact Class A refusal;
- incompatible and unsupported refusal;
- missing, malformed, and stale confirmation;
- changed source evidence, source module, target module, or manifest after preparation;
- source/destination alias, symbolic-link alias, existing destination, and concurrent destination creation;
- canonical candidate serialization and deterministic token generation;
- private temporary-file mode and cleanup;
- injected write, fsync, publication, and verification failures;
- source byte preservation before and after success and every failure;
- destination structural validity and exact target compatibility;
- no browser storage access or mutation;
- privacy-safe preparation and receipt allowlists;
- learner-evidence v1 unchanged;
- all previous v2 structural, exact compatibility, manifest, contextual validation, classification, and preview regressions unchanged.

## 11. Deferred work

- browser v2 import/export and confirmation UI;
- selecting a target current position for retired source steps;
- registry lookup, manifest path selection, and multi-hop chaining;
- split, merge, fan-in, fan-out, aggregation, or semantic mapping;
- automatic backup creation or source deletion;
- overwrite or in-place migration;
- portable non-POSIX publication fallback;
- signing, authentication, encryption, accounts, cloud sync, LMS transfer, analytics, or telemetry.
