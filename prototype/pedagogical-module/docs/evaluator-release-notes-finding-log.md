# Evaluator release notes finding log

Issue: #72  
Parent: #69  
PR: #76

## Resolved findings

- **F1 — Release instructions could drift from the requested version.** Resolved by rendering archive name, release root and verification commands from one validated version token.
- **F2 — Documentation could omit integrity coverage.** Resolved by including `RELEASE-NOTES.md` in the deterministic `SHA256SUMS` inventory and archive.
- **F3 — Checksum wording could imply publisher authentication.** Resolved by explicitly stating that SHA-256 detects changes but does not authenticate the publisher or provide a signature.
- **F4 — Evaluators could serve the wrong directory or interface.** Resolved by pinning the loopback command to the extracted `pilot/` directory and fixed `pilot/index.html` entrypoint.
- **F5 — Cleanup could be mistaken for an uninstall flow.** Resolved by documenting explicit server shutdown and ordinary removal while stating that no service or installer is present.
- **F6 — Stale commands or filenames could silently ship.** Resolved by deterministic-template validation for archive name, verifier flag, checksum file, entrypoint, loopback host and shutdown instruction.
- **F7 — Notes could include machine-specific or temporal metadata.** Resolved by a static template containing no timestamp, CI run, username, hostname, absolute build path or random value.
- **F8 — Producer verification could ignore misleading notes.** Resolved by validating exact release-note bytes after safe extraction and checksum recomputation.

## Open findings

None.
