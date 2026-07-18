# Confirmed learner-evidence migration application finding log

Issue: #50  
Pull request: #52

## Scope reviewed

- explicit confirmation and applicability boundary;
- candidate preparation through the authoritative preview engine;
- source/destination path checks;
- private temporary-file creation and same-filesystem atomic create-if-absent installation;
- candidate and installed-output validation;
- original-source byte preservation;
- rollback ownership and cleanup behavior;
- API, CLI, privacy, browser no-mutation, and learner-evidence v1 boundaries.

## Findings

### F1 — major — resolved — rollback could remove a replacement path

The initial rollback unlinked the destination solely because this operation had installed a path earlier. A concurrent local actor could replace that path before post-write verification failed, causing rollback to remove a foreign replacement.

Resolution: the implementation records device/inode identity for the prepared temporary file and installed destination. Rollback removes a path only while it still matches the recorded identity. If ownership is lost, the foreign path is left untouched and the application reports the identity change.

### F2 — major — resolved — cleanup failures were silent

Temporary-file and destination rollback failures were initially swallowed, preventing deterministic diagnosis and weakening the no-partial-output guarantee.

Resolution: cleanup is centralized in an identity-aware helper. Every cleanup failure is appended to the application error. Source bytes are rechecked on every failed application path, and inability to verify source preservation is also reported.

### F3 — minor — resolved — broken symbolic-link destination lacked a regression

The implementation correctly used `lexists`, but the specified broken-link behavior was not executable.

Resolution: a regression creates a broken destination symlink, proves it is treated as existing, and verifies that the link is not replaced.

### F4 — minor — resolved — source drift check lacked a regression

The application checked source bytes before installation, but the race boundary was not covered by a controlled test.

Resolution: a regression changes source bytes immediately after temporary-candidate validation. Application aborts before destination installation, cleans the temporary file, and leaves the changed source untouched.

### F5 — policy — resolved — exact evidence is not a migration copy command

Using the application command as a generic Class A copy operation would blur export and migration responsibilities.

Resolution: exact evidence fails with `exact evidence requires no migration`. Only declared-lossless and declared-partial previews with an available candidate are applicable.

### F6 — policy — resolved — retired current position cannot be guessed

A partial transition whose active source step is retired has no approved target position.

Resolution: `unresolved-retired` remains non-applicable. The application writes no destination until a separate explicit position-selection policy exists.

## Regression matrix

The suite covers:

- confirmed declared-partial migration with introduced empty responsibilities;
- confirmed declared-lossless reorder with stable current-step remapping;
- candidate structural validity and exact target compatibility;
- private `0600` destination and deterministic JSON output;
- missing confirmation, Class A, retired current, source alias, existing file, and broken symlink refusal;
- atomic-link failure and temporary cleanup;
- source drift before installation;
- post-install verification rollback;
- destination identity replacement without foreign-path deletion;
- observable cleanup failure;
- source digest equality and browser no-mutation result;
- learner-evidence v1 unchanged regression.

## Open findings

None. GitHub Actions and two consecutive clean reviews must complete on one unchanged final head before merge.
