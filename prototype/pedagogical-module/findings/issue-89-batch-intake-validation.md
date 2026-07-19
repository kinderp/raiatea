# Batch intake validation finding log

Issue: #89  
Parent: #87  
PR: #89

## Resolved findings

- **F1 — Manifest paths could resolve outside the supplied intake root.** Resolved by canonical relative paths and explicit root containment checks.
- **F2 — A symbolic link could redirect validation to an unrelated file.** Resolved by rejecting symlinks at every listed path component.
- **F3 — Missing or non-regular files could be treated as records.** Resolved by requiring one existing regular file for every manifest entry.
- **F4 — Manifest metadata could disagree with file bytes.** Resolved by recalculating SHA-256 before parsing the record.
- **F5 — Structurally malformed or privacy-invalid records could enter the batch.** Resolved by reusing the closed evaluator-session v1 validator.
- **F6 — Byte-identical records could be counted more than once.** Resolved by duplicate payload detection.
- **F7 — Semantically identical records with different JSON formatting could be counted more than once.** Resolved by canonical-value duplicate detection.
- **F8 — Intake could mutate or scan unrelated files.** Resolved by read-only access limited to manifest-listed paths and immutable ordered snapshots.

## Open findings

None.
