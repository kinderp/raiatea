# Evaluator release archive finding log

Issue: #71  
Parent: #69  
PR: #75

## Resolved findings

- **F1 — Archive metadata could inherit host-specific values.** Resolved by forcing mtime, uid/gid, names, modes, format, and lexical order.
- **F2 — Integrity metadata could omit release metadata.** Resolved by covering `release-manifest.json` and every pilot regular file.
- **F3 — Checksum inventory could be ambiguous.** Resolved by a closed lowercase SHA-256 plus two-space canonical-path grammar, sorted and duplicate-free.
- **F4 — Generic tar extraction could permit traversal or links.** Resolved by validating all members before manually extracting only directories and regular files.
- **F5 — Archive verification could trust producer state.** Resolved by reopening the tar, validating metadata, extracting to a new destination, validating the release manifest, and recomputing all checksums.
- **F6 — Existing or concurrent outputs could be overwritten.** Resolved by preflight checks and no-replace hard-link publication.
- **F7 — Failed verification could leave partial output.** Resolved by owned temporary extraction and cleanup before final rename.
- **F8 — Reproducibility and tamper handling lacked executable proof.** Resolved by repeated-build, metadata, checksum, tamper, unsafe-member, collision, parser, and prior-regression tests.

## Open findings

None.

## Final gate

Pending green GitHub Actions and two consecutive clean review rounds on the unchanged final head.
