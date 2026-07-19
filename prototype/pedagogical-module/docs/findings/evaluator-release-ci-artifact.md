# Evaluator release CI artifact finding log

Issue: #73  
Parent: #69  
PR: #77

## Resolved findings

- **F1 — Artifact production could inherit broad repository permissions.** Resolved by workflow-level `contents: read` and no write, deployment, package or identity permissions.
- **F2 — Consumer verification could accidentally reuse producer workspace state.** Resolved by a separate dependent job, artifact download into a clean path, and a distinct extraction destination.
- **F3 — Artifact payload could include checkout or diagnostics.** Resolved by uploading one exact tar path and rejecting every unexpected downloaded entry.
- **F4 — An invalid archive could be uploaded.** Resolved by running the independent verifier before the upload step.
- **F5 — Artifact transport could hide archive mutation.** Resolved by downloading the transported tar and rerunning structure, manifest, release-note and checksum verification.
- **F6 — Extracted files might verify but fail to serve.** Resolved by a bounded loopback server smoke test covering the launcher, both modules and pilot manifest.
- **F7 — CI artifact storage could be confused with public hosting.** Resolved by short three-day retention, deterministic non-public artifact identity and explicit no-deployment boundaries.
- **F8 — Workflow changes could drift silently.** Resolved by static regressions for triggers, permissions, pinned actions, producer/consumer separation, exact payload, retention, verification and loopback smoke endpoints.

## Open findings

None.
