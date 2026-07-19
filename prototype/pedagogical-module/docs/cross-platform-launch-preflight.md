# Cross-platform launch and preflight contract

Status: initial implementation contract for issue #79 under parent #78.

## Goal

Define one closed lifecycle for preflighting, launching, stopping and cleaning up an already verified Raiatea evaluator release on supported Windows, macOS and Linux desktops without privileged installation or background persistence.

## Verified release input

Launch helpers operate only on an extracted `raiatea-evaluator-<version>/` directory that has already passed the archive verifier. The directory must contain regular non-symlink files `release-manifest.json`, `RELEASE-NOTES.md`, `SHA256SUMS` and `pilot/index.html`. The release version must match the directory name and manifest identity.

Helpers do not accept archives directly, perform extraction, bypass checksum verification or repair malformed releases.

## Supported runtime boundary

The initial runtime is Python 3.10 or newer with the standard-library HTTP server. Helpers may discover `python3`, `python` or the Windows `py -3` launcher according to platform rules, but must reject missing, unsupported or ambiguous runtimes with an actionable diagnostic.

No package installation, virtual environment, administrator privilege or network dependency is required.

## Network and port boundary

The server binds only to `127.0.0.1`. The default port is `8000`; a caller may supply one decimal port from 1024 through 65535. Invalid or occupied ports fail before starting a persistent process. Helpers never bind to all interfaces, choose a random port silently or contact an external endpoint.

## Lifecycle

A successful launch:

1. validates release shape and identity;
2. resolves a supported Python runtime;
3. validates loopback host and port availability;
4. starts `python -m http.server` with the verified `pilot/` directory;
5. records only owned local process state inside the release runtime area;
6. waits for the fixed `index.html` endpoint;
7. optionally opens the loopback URL using the platform browser mechanism;
8. reports the URL and explicit stop command.

Stop helpers act only on owned state whose process still matches the expected server command. Missing, malformed, stale or foreign PID state fails closed and is never used to terminate an unrelated process.

## Diagnostics

Diagnostics use stable codes and human-readable messages for at least:

- `RELEASE_NOT_FOUND`;
- `RELEASE_IDENTITY_MISMATCH`;
- `RELEASE_FILE_UNSAFE`;
- `PYTHON_NOT_FOUND`;
- `PYTHON_UNSUPPORTED`;
- `PORT_INVALID`;
- `PORT_IN_USE`;
- `SERVER_START_FAILED`;
- `SERVER_NOT_READY`;
- `STATE_ALREADY_EXISTS`;
- `STATE_STALE`;
- `STATE_FOREIGN_PROCESS`;
- `STOP_FAILED`.

No diagnostic includes learner evidence, browser storage, username, hostname, secret or telemetry identifier.

## State and cleanup

Runtime state is local, minimal and disposable. It may contain the selected port, process identifier and a fixed contract marker, but no learner data or machine-wide configuration. Cleanup removes only files created by the helper. The release payload, evaluator archive and browser-local progress remain untouched.

## Test responsibility matrix

- contract parser/fixture tests: closed field sets, stable diagnostic codes and version/port rules;
- POSIX implementation tests: macOS/Linux runtime discovery, launch, stop, stale/foreign state and cleanup;
- PowerShell implementation tests: Windows runtime discovery, launch, stop, stale/foreign state and cleanup;
- acceptance matrix: supported CI platforms where available plus deterministic static validation for unavailable environments.

## Boundary

This increment defines the contract and executable fixtures only. It does not add POSIX or PowerShell launchers, installers, elevation, services, code signing, telemetry, learner identity, remote feedback or automatic updates.
