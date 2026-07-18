# Confirmed learner-evidence v2 migration application

Status: design and implementation contract for issue #50.

This increment turns one already validated compatibility preview candidate into a new learner-evidence v2 file only after explicit caller confirmation. It never overwrites, deletes, renames, or edits the source evidence file and never reads or writes browser storage.

## 1. Inputs

The application CLI receives:

1. the source learner-evidence v2 file;
2. the exact target canonical module revision;
3. a direct exact source canonical revision and migration manifest when the transition is non-exact;
4. a caller-selected destination path;
5. the exact confirmation token `APPLY-NEW-COPY`.

The existing preview loader remains authoritative for structural validation, unsupported handling, compatibility classification, candidate construction, and exact target validation.

## 2. Applicability

Application is permitted only when the preview result is `declared-lossless` or `declared-partial`, `candidateAvailable` is true, and the candidate is present.

Application fails closed when:

- the result is `exact`: no migration is required and this command is not a general copy operation;
- the result is `incompatible` or `unsupported`;
- the current source step is retired and remains `unresolved-retired`;
- the optional source/manifest context is incomplete;
- confirmation is missing or differs from `APPLY-NEW-COPY`;
- source and destination resolve to the same path;
- the destination already exists, including a broken symbolic link;
- the destination parent does not exist or is not a directory;
- candidate validation or post-write verification fails.

## 3. Original-copy preservation

Before preparation, the application layer reads and stores the exact source bytes. It reads them again immediately before committing the destination and after post-write verification. Any change aborts the operation. The application never opens the source in write mode and never invokes replacement, rename, unlink, or permission changes on it.

Path equality is checked after non-strict resolution so aliases through `.` and `..` are rejected. An existing destination is never overwritten, even with confirmation.

## 4. Atomic new destination

The candidate is serialized as UTF-8 JSON with stable indentation, sorted keys, and a trailing newline. Application:

1. creates a private temporary file in the destination directory;
2. writes and flushes the complete payload;
3. calls `fsync` on the temporary file;
4. reparses and validates the temporary file as learner-evidence v2;
5. verifies exact compatibility with the target module;
6. rechecks the source bytes and destination non-existence;
7. atomically installs the temporary file at the destination without replacing an existing path;
8. reparses and verifies the installed destination;
9. confirms the source bytes remain unchanged.

The initial implementation uses an atomic hard-link from the private temporary file to the absent destination, followed by removal of the temporary name. This gives create-if-absent semantics on the same filesystem. If hard-link creation is unsupported or fails, application fails closed rather than falling back to an overwrite-capable operation.

The destination directory is flushed when the platform exposes a directory file descriptor. Temporary files are removed on every failure path. A post-install verification failure removes only the newly created destination and leaves the source untouched.

## 5. API result

A successful application returns a closed summary containing:

- `status`: `applied-new-copy`;
- source and destination paths;
- exact target module ID and opaque revision;
- compatibility classification used to prepare the candidate;
- SHA-256 digest of the source bytes before and after;
- SHA-256 digest of the destination bytes;
- `sourceUnchanged: true`;
- `browserStorageChanged: false`.

The result contains no learner identity, timestamps, analytics identifiers, free-form content, inferred mastery, or secret material.

## 6. CLI behavior

```text
apply_evidence_migration_v2.py EVIDENCE TARGET_MODULE DESTINATION \
  --source SOURCE_MODULE --manifest MANIFEST \
  --confirm APPLY-NEW-COPY [--json]
```

Success exits `0`. Any missing confirmation, validation problem, unavailable candidate, path conflict, write failure, verification failure, or cleanup failure exits `1` with deterministic diagnostics. The human output states that a new copy was created and the original remained unchanged.

## 7. Explicit boundary

This increment does not add browser v2 import/export, a confirmation UI, current-position selection for retired steps, registry lookup, manifest chaining, split/merge semantics, cloud transfer, accounts, analytics, signing, encryption, or any learner-evidence v1 change.
