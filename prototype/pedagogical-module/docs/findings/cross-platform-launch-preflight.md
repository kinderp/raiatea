# Cross-platform launch and preflight finding log

Issue: #79  
Parent: #78  
PR: #83

## Resolved findings

- **F1 — Launchers could operate on unverified or malformed release trees.** Resolved by requiring one extracted `raiatea-evaluator-<version>` directory with exact regular non-symlink files and matching manifest identity.
- **F2 — Platform helpers could silently choose incompatible runtimes.** Resolved by pinning Python 3.10+ and ordered platform-specific runtime candidates.
- **F3 — A launcher could expose the pilot beyond the local machine.** Resolved by fixing the host to `127.0.0.1` and rejecting alternative bind addresses.
- **F4 — Port handling could be ambiguous or unsafe.** Resolved by a decimal-only 1024–65535 range, explicit default 8000 and stable `PORT_INVALID`/`PORT_IN_USE` diagnostics.
- **F5 — Stop helpers could terminate unrelated processes.** Resolved by defining owned state, a fixed marker and fail-closed stale/foreign-process outcomes.
- **F6 — Runtime state could become a new learner-data store.** Resolved by limiting it to process, port and contract marker data with no progress, evidence, identity or telemetry.
- **F7 — POSIX and Windows helpers could diverge semantically.** Resolved by one machine-readable platform-neutral contract and a shared diagnostic vocabulary.
- **F8 — Contract drift could remain undetected.** Resolved by a closed validator and malformed fixture tests for field sets, paths, platforms, runtimes, ports, state and diagnostics.

## Open findings

None.
