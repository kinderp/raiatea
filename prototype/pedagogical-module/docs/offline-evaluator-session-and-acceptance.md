# Offline evaluator session record and cross-platform acceptance contract

Status: initial implementation contract for issue #82 under parent #78.

## Goal

Add an optional local evaluator-session record and one closed acceptance matrix for the verified desktop field-pilot package without collecting learner identity, analytics or remote feedback.

## Session record

The evaluator may explicitly create one local JSON record after a field-pilot session. The record is separate from learner evidence and contains only:

- the fixed record format and version;
- evaluator-release version;
- platform class: `linux`, `macos` or `windows`;
- launcher used: `posix` or `powershell`;
- deterministic acceptance-result keys;
- optional bounded free-text observations entered by the evaluator;
- an explicit local-only and non-identifying declaration.

The record must not contain names, email addresses, account IDs, learner answers, browser storage, IP addresses, hostnames, usernames, absolute paths, timestamps, analytics identifiers or automatically collected machine details.

## Acceptance matrix

The matrix covers, where the CI platform is available:

1. deterministic desktop archive build and independent verification;
2. helper presence and checksum coverage;
3. release preflight and identity validation;
4. loopback launch and launcher page response;
5. stop and owned-state cleanup;
6. invalid-port, stale-state and foreign-process diagnostics;
7. no installer, elevation, service, registry, firewall, remote request or persistence behavior;
8. session-record structural validation and privacy exclusions.

Linux and Windows receive executable CI acceptance. macOS receives the same POSIX contract tests plus a documented manual acceptance row unless a hosted macOS job is explicitly added within the bounded workflow.

## Determinism and validation

The record schema is closed and fail-closed. Acceptance-result keys and enum values are canonical and sorted. Free text has an explicit byte/character limit and is never inferred or populated automatically. The validator refuses unsupported fields, identifiers, path-like values and privacy-sensitive keys.

## Lifecycle

Creating, viewing, exporting or deleting the session record is always an explicit evaluator action. No automatic upload, synchronization, telemetry, aggregation or retention policy is introduced. Deleting the local file fully removes the session record.

## Boundary

No learner identity, remote submission, analytics, telemetry, account, cloud storage, LMS integration, support ticket creation, automatic upload or new learner-evidence format.
