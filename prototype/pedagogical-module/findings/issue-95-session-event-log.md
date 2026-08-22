# Session event finding log

Issue: #95
Parent: #93
PR: #95

## Resolved findings

- F1: closed top-level fields and fixed format/version prevent silent expansion.
- F2: severity, privacy-boundary and unsafe-runtime rules determine stop behavior.
- F3: stop-required values must include the canonical stop action.
- F4: action arrays are validated as strings before ordering and vocabulary checks.
- F5: the record has no free-text or identifying fields.
- F6: deterministic no-replace writes prevent accidental replacement.
- F7: regular-file validation rejects symbolic links before lifecycle operations.
- F8: release identity and checklist SHA-256 preserve local provenance.

## Open findings

None.
