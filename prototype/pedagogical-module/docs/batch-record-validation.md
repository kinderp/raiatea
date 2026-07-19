# Batch record validation

Issue: #89  
Parent: #87

Validate one explicitly supplied local batch manifest against evaluator-session v1 files below one supplied root.

Every listed path must remain below the root, avoid symbolic links, resolve to one regular JSON file, match its SHA-256 digest, and pass the existing evaluator-session validator.

Reject missing files, path escape, links, non-regular files, digest mismatch, malformed records, duplicate digests, duplicate canonical values, and divergent bytes for the same validated value.

Successful validation returns an ordered immutable list of record snapshots with path and digest provenance. It does not modify files, aggregate results, create summaries, retain state, scan unrelated files, use learner evidence, or access a network.

Tests cover success, deterministic order, missing and malformed inputs, digest mismatch, links, root escape, duplicate bytes and values, preservation of original inputs, and no unrelated-file access.
