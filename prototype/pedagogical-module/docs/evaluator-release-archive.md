# Reproducible evaluator release archive and checksum contract

Status: initial implementation contract for issue #71 under parent #69.

## Goal

Package one validated evaluator-release directory from #70 into a reproducible archive and add deterministic SHA-256 integrity metadata without changing the release payload or pilot runtime.

## Archive boundary

The initial archive format is a deterministic POSIX tar archive with a fixed `.tar` suffix. The archive contains exactly one top-level `raiatea-evaluator-<version>/` directory and all regular files from the validated release directory.

Archive member paths are canonical relative POSIX paths. Absolute paths, `.`/`..`, backslashes, duplicate members, symlinks, hard-link members, devices, FIFOs, sockets, sparse entries, and files outside the one release root are forbidden.

## Normalized metadata

Every archive member uses fixed metadata independent of the build machine:

- modification time `0`;
- uid/gid `0`;
- empty user/group names;
- deterministic modes: `0755` for directories and `0644` for regular files;
- lexical member ordering;
- no PAX environment metadata.

For identical canonical sources and release version, repeated archive bytes must be identical.

## Checksums

The release directory gains one deterministic `SHA256SUMS` file before archiving. It contains one lowercase SHA-256 digest and two spaces followed by the canonical relative path for every distributed regular file except `SHA256SUMS` itself.

The inventory includes `release-manifest.json` and every file under `pilot/`. Paths are lexicographically sorted and each file appears exactly once.

## Verification

Independent verification must:

1. validate the archive member set and normalized metadata before extraction;
2. extract only into a new destination;
3. reject pre-existing output, unsafe members, links, duplicates, and unsupported types;
4. validate the release manifest and version after extraction;
5. parse `SHA256SUMS` as a closed sorted inventory;
6. recompute every digest and reject missing, extra, or changed files.

## Installation and cleanup

Archive and checksum outputs are never overwritten. Staging lives under the output parent. Failure removes owned temporary and partial outputs while preserving pre-existing or concurrently created paths.

## Privacy and deferred work

Checksums describe only distributed static files. No learner data, timestamp, machine identity, absolute path, secret, network destination, analytics, or signature is added.

Release notes and non-developer verification instructions remain in #72. CI artifact publication remains in #73.
