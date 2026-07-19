# Evaluator release notes and integrity verification contract

Status: initial implementation contract for issue #72 under parent #69.

## Goal

Add deterministic evaluator-facing release notes and a complete non-developer integrity-verification walkthrough to the reproducible archive introduced by #71, without changing the pilot, evidence, checksum, archive, or runtime contracts.

## Required release documentation

Each evaluator release must include one human-readable document pinned to the exact release version and archive contract. It explains:

- what the release contains;
- the exact release version;
- the fixed pilot entrypoint;
- the archive and checksum formats;
- that the archive is unsigned and local-first;
- that no installer, account, cloud runtime, analytics, telemetry, LMS integration, or auto-update is present;
- that learner evidence remains browser-local and module-scoped.

## Evaluator workflow

The document provides ordered steps for:

1. identifying the archive name and release version;
2. verifying the archive through the supplied Python verifier;
3. optionally checking `SHA256SUMS` after verified extraction;
4. serving only the extracted `pilot/` directory on loopback;
5. running the existing pilot acceptance checklist;
6. stopping the local server;
7. removing the extracted release and downloaded archive when no longer needed.

## Determinism and consistency

Release notes must be deterministic for the same release version and canonical sources. They must not contain timestamps, usernames, hostnames, absolute paths, random identifiers, CI run numbers, secrets, or machine-specific instructions.

Tests must fail when documentation:

- names a different release version;
- points to a wrong entrypoint or checksum filename;
- omits unsigned/local-first boundaries;
- claims signing, installation, remote hosting, or automatic update behavior;
- diverges from the current archive/verifier commands;
- is absent from the checksum inventory or archive.

## Security and privacy wording

The instructions must state that checksum verification detects accidental or malicious file changes but does not authenticate the publisher because this increment does not add signatures. They must avoid promising trust, identity, certification, or tamper-proof distribution beyond local SHA-256 integrity checks.

## Boundary

No CI artifact upload, GitHub Release publication, public hosting, signing, installer, package registry, remote runtime, analytics, learner identity, or automatic update behavior. Those remain issue #73 or separately approved future work.
