# Evaluator release manifest and versioned layout contract

Status: implemented contract for issue #70 under parent #69.

## Goal

Wrap the completed generated pilot in one deterministic versioned evaluator-release directory with a closed metadata manifest and no archive, checksum, installer, or remote-publication behavior.

## 1. Release identity

A release builder receives one explicit opaque release version. The accepted form is 1–64 ASCII lowercase letters, digits, dots, or hyphens, beginning and ending with a letter or digit.

The version is an identity label, not a number: builders and validators do not infer ordering, recency, compatibility, or upgrade direction from it.

## 2. Directory layout

For version `<version>`, the output directory contains exactly:

```text
raiatea-evaluator-<version>/
├── release-manifest.json
└── pilot/
    └── <complete generated pilot payload>
```

The builder receives the parent output path and refuses any existing final destination, including directories, files, and dangling symbolic links.

## 3. Closed manifest

`release-manifest.json` contains exactly:

- `format`: fixed `raiatea-evaluator-release`;
- `contractVersion`: fixed integer `1`;
- `releaseVersion`: the exact caller-supplied opaque version;
- `entrypoint`: fixed relative path `pilot/index.html`;
- `pilotManifest`: fixed relative path `pilot/pilot-manifest.json`;
- `files`: a sorted complete inventory of the pilot payload.

Each `files` entry contains exactly:

- `path`: canonical slash-separated relative path under `pilot/`;
- `size`: non-negative byte length.

The manifest is not self-inventoried. Checksums are deliberately deferred to issue #71.

## 4. Path and file safety

Every inventoried path must:

- be relative and canonical;
- use `/` separators;
- contain no empty, `.` or `..` segment;
- remain under `pilot/`;
- identify one regular non-symlink file;
- be unique.

The builder and validator reject symbolic links, special files, duplicate paths, path traversal, absolute paths, unsupported fields, missing fields, invalid sizes, and unexpected generated-output shapes.

## 5. Determinism

For identical canonical sources and the same release version:

- directory names are identical;
- manifest bytes are identical;
- pilot payload bytes are identical;
- inventory order is lexicographic by canonical relative path;
- no timestamp, hostname, username, absolute path, random identifier, or environment-specific metadata is included.

## 6. Build and installation boundary

The builder:

1. validates the version before creating output;
2. stages under the resolved destination parent;
3. invokes the canonical pilot builder;
4. derives and validates the manifest from the staged payload;
5. verifies the staged release;
6. reserves the final directory without replacement;
7. installs regular files using no-overwrite hard links;
8. verifies the installed release;
9. removes staging on success or failure.

On failure, owned staging and owned partial output are cleaned up, while pre-existing or concurrently created external paths are preserved.

## 7. Privacy and runtime boundary

The release manifest contains no learner evidence, progress, preferences, identity, timestamp, analytics, telemetry, credentials, network destination, or machine-specific path.

The distributed pilot keeps its existing offline, browser-local, module-scoped behavior byte-for-byte unchanged.

## 8. Verification matrix

Tests cover:

- valid release build and exact layout;
- closed manifest key sets;
- canonical sorted complete inventory and exact sizes;
- byte-identical repeated builds;
- pilot payload equality with a direct pilot build;
- invalid release versions;
- malformed, unsafe, duplicate, and unsorted manifest data;
- pre-existing and concurrently created destinations;
- symlink refusal;
- pilot failure cleanup;
- changed-inventory detection;
- CLI success and no-overwrite refusal;
- unchanged prior pilot, evidence, migration, and browser regressions.

## 9. Deferred work

- checksums and archive generation;
- release notes and verification walkthrough;
- CI artifact upload and downstream verification;
- signing, installers, registries, remote hosting, and automatic updates.
