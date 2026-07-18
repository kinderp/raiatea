# Evaluator release layout finding log

Issue: #70  
Parent: #69  
PR: #74

## Review scope

- closed release metadata;
- version validation;
- canonical path handling;
- pilot payload preservation;
- deterministic inventory and bytes;
- no-replace installation;
- failure cleanup and concurrent-path preservation;
- privacy and deferred-work boundaries.

## Findings

### F1 — Release identity could become a path injection surface

**Risk:** a caller-supplied version containing separators, traversal, whitespace, uppercase aliases, or unbounded text could escape or ambiguously name the release directory.

**Resolution:** `validate_release_version` accepts only 1–64 lowercase ASCII letters, digits, dots, or hyphens and requires an alphanumeric first and last character. Validation runs before staging or output creation.

**Status:** resolved.

### F2 — A hand-maintained inventory could drift from the distributed pilot

**Risk:** release metadata could omit or invent files when the pilot evolves.

**Resolution:** `_inventory` derives the sorted inventory from the completed canonical pilot output. Tests compare the complete release payload byte-for-byte with an independent direct pilot build.

**Status:** resolved.

### F3 — Unsafe or ambiguous relative paths could enter the manifest

**Risk:** absolute paths, backslashes, empty segments, `.`/`..`, non-pilot roots, duplicates, or unsorted entries could create traversal or platform-dependent interpretation.

**Resolution:** `_canonical_relative_path` and `validate_release_manifest` enforce canonical POSIX paths rooted under `pilot/`, uniqueness, and lexical ordering. The malformed-manifest matrix covers unsafe, duplicate, and unsorted cases.

**Status:** resolved.

### F4 — Symlinks could copy or expose files outside the release payload

**Risk:** recursive inventory or installation might follow a symbolic link to external data.

**Resolution:** inventory and installation reject symlinks before treating entries as files or directories. Tests prove a linked external target remains untouched and is not inventoried.

**Status:** resolved.

### F5 — Existing or concurrent destinations could be overwritten or removed

**Risk:** a build could replace an evaluator's prior release or delete a path created by another actor during installation.

**Resolution:** final output is reserved with `os.mkdir`, files are installed through no-overwrite hard links, and cleanup removes only files/directories created by the current operation. Existing and concurrently created destination tests preserve foreign marker files.

**Status:** resolved.

### F6 — Failure could leave partial release or staging data

**Risk:** pilot-build, manifest, or installation failure could leave a misleading partial release.

**Resolution:** same-parent staging is always removed in `finally`; owned partial output is rolled back on installation failure. Pilot failure and concurrent collision tests assert no owned staging remains.

**Status:** resolved.

### F7 — Release metadata could leak machine or learner information

**Risk:** timestamps, absolute paths, usernames, learner progress, analytics, or environment identifiers could make releases non-reproducible or privacy-sensitive.

**Resolution:** the closed manifest contains only fixed format/version fields, opaque release version, two fixed relative targets, canonical paths, and byte sizes. Pilot bytes remain unchanged and browser-local. No machine or learner fields are introduced.

**Status:** resolved.

### F8 — This increment could prematurely absorb archive or integrity behavior

**Risk:** adding checksums, archives, release notes, or CI publication now would enlarge the trust boundary and violate ordered child increments.

**Resolution:** implementation stops at a validated versioned directory and size inventory. Checksums/archive, release notes, and CI artifact work remain explicitly assigned to #71, #72, and #73.

**Status:** resolved.

## Open findings

None.

## Final review gate

Final review rounds must target one unchanged head after the complete unit/build/browser workflow is green.
