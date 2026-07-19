# POSIX launch and stop helper contract

Status: initial implementation contract for issue #80 under parent #78.

## Goal

Add portable POSIX shell helpers for macOS and Linux that apply launch-preflight v1 to an already verified evaluator release.

## Helper surface

- `launch-posix.sh`: validates release, Python and port; starts the pilot on `127.0.0.1`; waits for readiness; optionally opens the browser; prints URL and stop command.
- `stop-posix.sh`: validates owned runtime state; stops only the matching local server; removes only helper-owned state.

Both scripts use POSIX `sh`. Bash-only syntax and GNU-only assumptions are forbidden.

## Launch rules

The launcher accepts an optional decimal port and `--no-open`. It resolves Python 3.10+ using the ordered POSIX candidates, rejects occupied ports, writes state atomically under `.raiatea-runtime/`, and serves only `pilot/`.

Browser opening uses `open` on macOS or `xdg-open` on Linux after readiness. Failure to open the browser does not lose valid server state.

## Stop rules

The stop helper validates the contract marker, numeric process ID, port and expected local-server identity before requesting termination. Missing, malformed, stale or foreign state never affects another process.

## Diagnostics and cleanup

Failures emit stable launch-preflight diagnostic codes. A failed launch cleans partial state and any server created by that invocation. No file outside the verified release root is changed.

## Verification

Tests cover shell syntax, runtime/version discovery, invalid or occupied ports, successful serving, `--no-open`, state collision, stale/foreign state, explicit stop, failed-start cleanup, paths with spaces and absence of external requests.

## Boundary

No PowerShell, installer, elevation, service registration, machine-wide configuration, telemetry, identity, signing or automatic update.
