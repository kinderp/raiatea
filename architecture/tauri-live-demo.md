# Raiatea first live desktop demo

Status: **Prototype / PR #224**  
Issue: #223  
Depends on: ADR-0003 (React renderer), ADR-0004 (local GUI Application Bridge)

## What this demo proves

This is the first Raiatea GUI that is intended to render **real local Raiatea Application Layer state** rather than TypeScript demo fixtures.

```text
.raiatea-demo/
  real VS1 catalog + SourceReferences + extraction + search index
        |
        v
Python application_bridge_sidecar
        |
        v
Rust / Tauri Desktop Core
  owns process lifecycle and trusted bootstrap
        |
        |  one allowed command:
        |  raiatea_application_request
        v
TauriApplicationTransport
        |
        v
LiveRaiateaGateway
        |
        v
existing React AppShell
```

The demo is deliberately disposable. It does **not** import, scan, overwrite or mutate a user's real Raiatea Library.

## Authority boundary

The web renderer does not receive:

- filesystem or catalog-store paths;
- generic process launch or shell APIs;
- filesystem or HTTP plugins;
- the Python process handle;
- JSON-RPC framing/correlation authority.

The main Tauri window is associated with one custom capability whose only permission enables the application command `raiatea_application_request`. The Rust command itself accepts only the five ADR-0004 read methods:

- `gateway.status`;
- `library.page`;
- `source.detail`;
- `search.page`;
- `representation.page`.

The Rust Desktop Core owns the Python child and checks method allowlisting, request/response framing, JSON-RPC version/correlation and a 1 MiB frame limit before a result reaches TypeScript. TypeScript then performs its existing runtime Application Layer validation again.

## Disposable demo state

`python -m prototype.p0_vs1.gui_demo_bootstrap` creates `.raiatea-demo/` at the repository root using first-party deterministic EPUB fixtures and the accepted VS1 product path:

1. catalog reconciliation;
2. SourceReference discovery;
3. known-permitted **demo** rights evidence;
4. local EPUB extraction;
5. deterministic search-index rebuild;
6. ApplicationFacade read-back validation.

The bootstrap writes a marker before it owns a workspace. If an existing non-empty target directory does not carry the exact Raiatea demo marker, bootstrap fails instead of deleting it.

The trusted `.raiatea-demo/manifest.json` contains Desktop Core startup information including the absolute local catalog path. This manifest is consumed by Rust and never sent to the renderer.

## Prerequisites

Common:

- Git;
- Python 3.10 or newer;
- Node.js 22.12 or newer and npm;
- Rust stable 1.90 or newer with Cargo;
- `tauri-cli` exactly 2.11.4 for this proof.

Install the exact CLI after Rust is available:

```bash
cargo install tauri-cli --version 2.11.4 --locked
```

### macOS

For desktop-only development, install the Xcode Command Line Tools:

```bash
xcode-select --install
```

Full Xcode is not required for this desktop-only demo.

### Debian / Ubuntu Linux

```bash
sudo apt update
sudo apt install -y \
  libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

### Windows

Install Microsoft C++ Build Tools with **Desktop development with C++** selected. Tauri also requires Microsoft Edge WebView2; it is normally already present on current Windows 10/11 systems. Use the stable MSVC Rust toolchain.

## Prepare the demo

From the repository root:

macOS / Linux:

```bash
python3 -m prototype.p0_vs1.gui_demo_prepare
```

Windows PowerShell:

```powershell
python -m prototype.p0_vs1.gui_demo_prepare
```

The preparation command:

- verifies Node, Rust and exact Tauri CLI versions;
- creates/recreates only the marked `.raiatea-demo/` workspace;
- runs `npm ci` against the committed renderer lockfile;
- verifies the **committed** `src-tauri/Cargo.lock` against the reviewed cross-platform SHA-256 evidence in `src-tauri/lock-evidence.json`;
- asks Cargo to validate the committed dependency graph with `--locked` and never rewrites the lockfile;
- prints the next command.

Both JavaScript and Rust dependency graphs are therefore versioned in the repository before the demo starts.

## Run the live GUI

```bash
cd frontend
npm run tauri:dev
```

Expected visible evidence:

- a native window titled **Raiatea — Live Demo**;
- gateway badge **Local Raiatea / live**;
- **no** `Prototype renderer data` banner;
- two EPUB Sources in Library;
- Source Detail with current extraction/representation information;
- searching for `Introduction` returns at least one result backed by the real demo search index.

Closing the Tauri app drops the Desktop Core process state and terminates/waits for the owned Python child.

## Build proof without an installer

The CI-proven non-bundled build command is:

```bash
cd frontend
cargo tauri build --no-bundle --ci
```

Tauri uses `npm run build:tauri`, so the desktop build is compiled with `VITE_RAIATEA_GATEWAY=tauri`; it cannot silently fall back to the TypeScript DemoGateway.

Production installers/signing/notarization are outside this slice.

## Troubleshooting

### `gui-demo-required-command-missing:*`

Install the named prerequisite and reopen the terminal so PATH is refreshed.

### `gui-demo-tauri-cli-version-mismatch`

Install the exact proof version:

```bash
cargo install tauri-cli --version 2.11.4 --locked --force
```

### `desktop-demo-manifest-missing-run-bootstrap`

Run the preparation command again from the repository root.

### `gui-demo-cargo-lock-missing` / `gui-demo-cargo-lock-drift`

Do not generate or bypass the lock locally. Restore the reviewed `frontend/src-tauri/Cargo.lock` from Git. The preparation command intentionally refuses a missing or changed Rust dependency graph.

### Tauri cannot find the intended Python interpreter

macOS / Linux:

```bash
RAIATEA_PYTHON="$(command -v python3)" npm run tauri:dev
```

Windows PowerShell:

```powershell
$env:RAIATEA_PYTHON=(Get-Command python).Source
npm run tauri:dev
```

### Port 5173 is already in use

The demo intentionally uses a fixed loopback Vite port and `strictPort`. Stop the process using port 5173 rather than silently moving Raiatea to a different origin.

## CI evidence required before merge

- disposable bootstrap on macOS/Linux/Windows, Python 3.10/3.12;
- browser renderer and live Tauri renderer mode build from committed npm lock;
- committed Cargo lock hash validated across desktop targets;
- Rust method/frame tests on macOS/Linux/Windows;
- real Rust-managed Python sidecar smoke through Representation;
- `cargo check --locked` on all desktop targets;
- exact documented macOS prepare flow via `gui_demo_prepare`;
- `cargo tauri info` and `cargo tauri build --no-bundle --ci` with tauri-cli 2.11.4;
- all prior GUI/bridge/VS1/PDF regressions;
- two consecutive clean reviews on the frozen final head.

## Finding log

- **TD-F1 resolved:** Windows `tauri-build` required `src-tauri/icons/icon.ico`; a valid project icon is now committed. This changes packaging metadata only and does not alter the Desktop Core, bridge, renderer authority, or knowledge semantics.
- **TD-F2 resolved:** #223 required a committed Cargo lock, while the first proof retained only cross-platform hash evidence. CI demonstrated one identical resolution on Linux/macOS/Windows; that exact `Cargo.lock` is now committed, removed from `.gitignore`, verified read-only by `gui_demo_prepare`, and consumed with Cargo `--locked`.
