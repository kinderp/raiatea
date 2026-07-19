# Field-pilot synthesis kit

Issue: #91  
Parent: #87

Package the completed local batch manifest, contextual intake validator and deterministic aggregate generator into the verified field-pilot archive.

The kit must include the three local tools, canonical contracts/fixtures, evaluator instructions, one reproducible example batch, explicit cleanup steps and cross-platform acceptance. Linux and Windows run executable CI; macOS remains documented POSIX parity unless a bounded hosted job is added.

The archive remains deterministic, independently verified and no-replace. Every added file is checksummed before the final tar is written.

The kit performs no remote collection, automatic submission, learner-evidence import, analytics service, account creation, cloud storage or background persistence.
