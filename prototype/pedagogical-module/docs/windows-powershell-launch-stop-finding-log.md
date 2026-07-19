# Windows PowerShell launch and stop finding log

Issue: #81  
Parent: #78  
PR: #85

## Resolved findings

- **F1 — Runtime discovery could ignore the canonical Windows order.** Resolved by trying `py -3` before `python` and requiring Python 3.10+.
- **F2 — The server could bind beyond the local machine.** Resolved by fixing `127.0.0.1` in launch, state and smoke tests.
- **F3 — Helper state could overwrite existing state.** Resolved by refusing an existing state file and publishing state only after readiness.
- **F4 — Stop could terminate an unrelated PID.** Resolved by validating marker, state shape, port, loopback host, entrypoint and the live Win32 command line.
- **F5 — Windows support could require machine changes.** Resolved by forbidding execution-policy, registry, firewall, service and scheduled-task mutations.
- **F6 — Platform packaging could diverge from POSIX.** Resolved by composing Windows helpers on top of the verified POSIX archive and regenerating checksums and deterministic tar metadata.
- **F7 — Static checks could miss runtime incompatibility.** Resolved by a dedicated `windows-latest` launch, loopback smoke and stop acceptance job.
- **F8 — Paths containing spaces could break commands.** Resolved by passing paths as PowerShell arguments and testing under runner temporary directories containing spaces.

## Open findings

None.
