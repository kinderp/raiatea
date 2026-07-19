# Evaluator-session batch manifest finding log

Issue: #88  
Parent: #87  
PR: #92

## Resolved findings

- **F1 — Manifest fields could expand silently.** Resolved by closed top-level and entry field sets.
- **F2 — Paths could escape the local intake root.** Resolved by canonical relative POSIX JSON paths with no absolute, backslash, dot or parent segments.
- **F3 — Digest values could be ambiguous.** Resolved by exact 64-character lowercase hexadecimal SHA-256 syntax.
- **F4 — Entry order could make manifests non-deterministic.** Resolved by mandatory lexicographic path ordering.
- **F5 — One record could be referenced more than once.** Resolved by duplicate-path rejection.
- **F6 — One payload could be aliased through different names.** Resolved by duplicate-digest rejection.
- **F7 — Unsupported record contracts could enter later intake.** Resolved by fixed evaluator-session format and version fields on every entry.
- **F8 — Structural validation could accidentally read records.** Resolved by a validator and builder that operate only on manifest values and supplied digest strings.

## Open findings

None.
