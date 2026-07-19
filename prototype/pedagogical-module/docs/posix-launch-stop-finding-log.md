# POSIX launch and stop helper finding log

Issue: #80  
Parent: #78  
PR: #84

## Resolved findings

- **F1 — A launcher could expose the pilot beyond the local machine.** Resolved by fixed `127.0.0.1` binding and loopback-only readiness checks.
- **F2 — Runtime discovery could silently accept an unsupported Python.** Resolved by ordered `python3`/`python` discovery with an explicit Python 3.10 minimum check.
- **F3 — Port text could be interpreted inconsistently by shells.** Resolved by decimal-only syntax and the closed 1024–65535 range before process creation.
- **F4 — Failed startup could leave a server or state file behind.** Resolved by owned cleanup traps, readiness timeout and removal of partial state.
- **F5 — Stop could terminate an unrelated process after PID reuse.** Resolved by marker, PID, port and expected `http.server` command-line validation before signaling.
- **F6 — Browser opening could become a launch dependency.** Resolved by opening only after readiness and treating opener failure as non-fatal.
- **F7 — Paths with spaces could break lifecycle commands.** Resolved by quoting every release, state, pilot and helper path and by an end-to-end space-path regression.
- **F8 — Helpers could escape release integrity coverage.** Resolved by composing a new verified archive, regenerating `SHA256SUMS`, and independently verifying the final tar.

## Open findings

None.
