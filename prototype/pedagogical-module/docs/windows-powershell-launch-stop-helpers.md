# Windows PowerShell launch and stop helper contract

Status: initial implementation contract for issue #81 under parent #78.

## Goal

Add PowerShell helpers for supported Windows desktops that match the merged launch-preflight v1 lifecycle and the verified POSIX behavior without requiring installation, elevation or service registration.

## Helper surface

- `Launch-Raiatea.ps1`: validates the verified release, resolves Python 3.10+, validates the requested port, starts a loopback-only server, waits for readiness, optionally opens the browser and writes owned runtime state.
- `Stop-Raiatea.ps1`: validates the owned state and process command line, stops only the matching local server and removes only helper-owned state.

## Runtime and launch rules

The launcher resolves runtime candidates in the canonical Windows order: `py -3`, then `python`. It accepts a decimal port in the configured range and a `-NoOpen` switch. It serves only `pilot/` on `127.0.0.1` and refuses occupied ports, unsafe release files, mismatched release identity and existing runtime state.

The browser is opened only after readiness. Browser-opening failure is non-fatal and does not discard valid server state.

## State and stop rules

State is written atomically below `.raiatea-runtime/server-state.json` and contains only the contract marker, process ID, loopback host, port and fixed entrypoint. The stop helper validates state shape, PID, port and the expected Python HTTP-server command line before signaling. Stale or foreign state never affects another process.

## Diagnostics and cleanup

Failures emit the stable launch-preflight diagnostic codes. Failed launch removes partial state and terminates only a server created by the current invocation. No registry key, scheduled task, firewall rule, service, profile or machine-wide setting is changed.

## Verification

Tests cover PowerShell parsing, runtime candidate order, unsupported runtimes, invalid and occupied ports, successful loopback serving, `-NoOpen`, paths with spaces, state collision, stale and foreign process state, explicit stop and failed-start cleanup. CI runs Windows acceptance where GitHub-hosted Windows runners are available and retains platform-neutral static checks elsewhere.

## Boundary

No installer, elevation, service registration, code signing, execution-policy modification, registry change, telemetry, learner identity, remote feedback, package registry or automatic update.
