# Offline evaluator session record and cross-platform acceptance

Status: implemented contract for issue #82 under parent #78.

## Separation from learner evidence

The evaluator-session record is an optional local JSON document created only by an explicit evaluator command. It is not learner evidence, is not read by the pilot, and is not written by the launch helpers. It contains no learner interaction details and introduces no evidence-format change.

## Closed record contract

Canonical format: `raiatea-evaluator-session`, version `1`.

Required fields are limited to release version, platform class, launcher class, eight canonical boolean acceptance results, optional bounded observations and the exact local-only declaration. Unknown fields and unsupported platform/launcher pairs fail closed.

Observations are limited to 1000 characters and 2000 UTF-8 bytes. Email-like values, IP-address-like values, absolute paths and explicit privacy-sensitive wording are rejected. No timestamp, machine fingerprint, hostname, username or automatically detected environment value is added.

## Explicit lifecycle

The packaged `evaluator-session-record.py` tool supports only:

1. `create` — creates a new no-replace local record with all results initially false;
2. `validate` — reads and validates one supplied record;
3. `export` — creates a byte-equivalent validated copy at a new path;
4. `delete` — deletes only one structurally valid regular record file.

There is no background save, auto-discovery, upload, synchronization, account, analytics or retention service.

## Cross-platform acceptance matrix

The machine-readable matrix contains exactly three rows:

| Platform | Launcher | Execution | Responsibility |
| --- | --- | --- | --- |
| Linux | POSIX | CI | Archive verification, checksums, launch/stop contract regressions and session-record tests. |
| macOS | POSIX | Manual parity | Run the same verified archive and POSIX commands; confirm all eight result keys before marking them true. |
| Windows | PowerShell | CI | Field archive verification, PowerShell launch/smoke/stop, failure diagnostics and session tooling presence. |

The manual macOS row exists because this bounded increment does not add a paid hosted macOS runner. It does not claim executable macOS CI coverage.

## macOS manual parity procedure

1. Verify and extract the field-pilot archive using the existing independent verifier.
2. Confirm checksum coverage of `launch-posix.sh`, `stop-posix.sh`, the session tool, fixture and matrix.
3. Run `sh ./launch-posix.sh --no-open` from the verified release root.
4. Open the printed loopback URL and confirm the launcher page.
5. Run `sh ./stop-posix.sh` and confirm `.raiatea-runtime/server-state.json` is removed.
6. Confirm an invalid port is rejected and no service, installer, login item or machine-wide setting was created.
7. Explicitly create and validate a macOS/posix session record only when desired.

## Packaged field-pilot archive

`build_field_pilot_archive.py` composes the verified desktop archive with the session tool, canonical fixture, acceptance matrix and `EVALUATOR-SESSION.md`. It regenerates `SHA256SUMS`, rebuilds the normalized deterministic tar and independently verifies the final archive before no-replace installation.

## Boundary

No learner identity, remote feedback, telemetry, analytics, cloud storage, account, support-ticket integration, LMS integration, automatic upload or new learner-evidence format.
