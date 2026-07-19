# Evaluator-session aggregate finding log

Issue: #90  
Parent: #87  
PR: #90

## Resolved findings

- **F1 — Aggregate fields could expand silently.** Resolved by a closed format/version and exact top-level field set.
- **F2 — Input provenance could be incomplete or unstable.** Resolved by sorted unique SHA-256 digests whose count equals `recordCount`.
- **F3 — Counts could use non-canonical keys.** Resolved by exact platform, launcher, result and theme vocabularies.
- **F4 — Boolean result totals could disagree with accepted records.** Resolved by requiring each false/true pair to sum to `recordCount`.
- **F5 — Theme labels could become free text or be inferred automatically.** Resolved by an approved closed vocabulary and explicit digest-scoped assignments only.
- **F6 — Observations or identifying data could leak into the summary.** Resolved by deriving only counts and digests from validated snapshots.
- **F7 — Output could vary with input ordering or overwrite existing files.** Resolved by digest sorting, canonical JSON and no-replace installation.
- **F8 — Aggregate generation could mutate source files.** Resolved by read-only intake snapshots and regression checks preserving manifest, records and theme assignments.

## Open findings

None.
