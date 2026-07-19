# Field-pilot synthesis kit finding log

Issue: #91  
Parent: #87  
PR: #91

## Resolved findings

- **F1 — Packaging could omit one synthesis component.** Resolved by a closed installed-tool list and required canonical example files.
- **F2 — The final archive could diverge from the verified field-pilot package.** Resolved by compositional build from the independently verified field-pilot archive.
- **F3 — Added files could escape integrity coverage.** Resolved by deleting stale checksums, installing all kit files, then regenerating `SHA256SUMS` before tar creation.
- **F4 — The packaged example could be internally inconsistent.** Resolved by generating records, manifest digests, themes and aggregate through the production validators/builders.
- **F5 — Repeated builds could differ.** Resolved by canonical JSON, deterministic content, normalized tar metadata and byte-equality regression tests.
- **F6 — The evaluator could need repository knowledge.** Resolved by packaged importable tools, `SYNTHESIS-KIT.md` commands and an executable complete example.
- **F7 — Local files could accumulate implicitly.** Resolved by explicit cleanup instructions and no cache, database, service, upload or retention mechanism.
- **F8 — Platform claims could exceed tested behavior.** Resolved by Linux build regressions, Windows end-to-end packaged acceptance and explicit macOS POSIX manual-parity wording.

## Open findings

None.
