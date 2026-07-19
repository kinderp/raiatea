# Evaluator session record and acceptance finding log

Issue: #82  
Parent: #78  
PR: #86

## Resolved findings

- **F1 — Evaluator notes could be confused with learner evidence.** Resolved by a separate format, tool, files and documentation with no pilot read/write path.
- **F2 — A record could silently collect identifying metadata.** Resolved by a closed schema with no timestamps, names, accounts, machine details, browser state or automatic environment discovery.
- **F3 — Free text could contain direct identifiers or machine paths.** Resolved by length limits and fail-closed rejection of email-like, IP-like, absolute-path and explicit privacy-sensitive values.
- **F4 — Lifecycle operations could overwrite or delete unrelated files.** Resolved by no-replace create/export and delete only after structural validation of one regular record file.
- **F5 — Platform claims could exceed tested coverage.** Resolved by explicit Linux/Windows CI rows and a separate `manual-parity` macOS row.
- **F6 — Session tooling could be omitted from the distributed archive or checksum inventory.** Resolved by compositional field-pilot packaging, regenerated `SHA256SUMS` and independent final archive verification.
- **F7 — Acceptance keys could drift between record and matrix.** Resolved by one canonical sorted key tuple exercised against every matrix row.
- **F8 — Local evaluation could imply telemetry or remote submission.** Resolved by explicit-only create/validate/export/delete commands and no networking, account, analytics, upload or synchronization behavior.

## Open findings

None.
