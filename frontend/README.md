# Raiatea frontend renderer

The React/TypeScript renderer consumes only Raiatea Application Layer read models.

## Current boundary

```text
React / TypeScript renderer
        |
        v
RaiateaGateway
        |
        +-- DemoRaiateaGateway        [normal Vite/browser development]
        |
        +-- LiveRaiateaGateway        [Tauri live demo]
                |
         ApplicationTransport
                |
         TauriApplicationTransport
                |
        Rust / Tauri Desktop Core
                |
        local ApplicationFacade sidecar
                |
        RaiateaApplicationFacade
```

The renderer does not import Python persistence, SourcePlugin, Provider-native or E-05 records and does not own process launch, JSON-RPC framing or sidecar lifecycle.

`DemoRaiateaGateway` remains deterministic renderer-development data and is visibly labelled **Prototype data**. `LiveRaiateaGateway` consumes an abstract `ApplicationTransport` and validates every returned bridge payload at runtime before exposing it to components.

The Tauri demo selects live mode through `.env.tauri`; normal `npm run dev` stays in demo mode. Components do not import Tauri.

## Live desktop authority boundary

- Python process lifecycle and trusted bootstrap belong to Rust/Desktop Core;
- the main Tauri window has one custom application permission only: `raiatea_application_request`;
- no shell, filesystem or HTTP plugin is installed or granted;
- the Rust command accepts only the five ADR-0004 read methods;
- host filesystem/root authority never belongs to renderer requests or results;
- stale Search cannot carry current rows;
- non-fresh catalog/source state cannot be upgraded into current Source/content claims;
- retained representation ids still pass through the Python ApplicationFacade currentness fence;
- bridge/process success does not establish knowledge truth.

## Truth-state rendering

The renderer distinguishes an empty current result from an unavailable current result:

- a fresh search with no matches may display `0 match(es)`;
- a stale/blocked search displays the `blocked_reason`, renders no current rows and does not promote a Source into the Inspector;
- a non-fresh Library may show last-known catalog rows, but it displays a prominent last-known notice rather than implying current Source/content access;
- live adapters must not turn `stale`, `not-established` or last-known state into empty/current UI claims.

## Browser/demo development

Requires Node 22.12+.

```bash
cd frontend
npm ci
npm run dev
```

Validation:

```bash
npm run typecheck
npm run test
npm run build
```

`package-lock.json` is committed and CI installs strictly through `npm ci`.

## Live Tauri demo

See `architecture/tauri-live-demo.md` for prerequisites, the disposable demo-state contract and the CI-proven local flow.

Both dependency graphs are committed: `frontend/package-lock.json` for React/Vite and `frontend/src-tauri/Cargo.lock` for the Desktop Core. The preparation command verifies them instead of resolving an unreviewed graph.

From the repository root, once prerequisites are installed:

```bash
python3 -m prototype.p0_vs1.gui_demo_prepare
cd frontend
npm run tauri:dev
```

Windows uses `python` instead of `python3` for the preparation command.

## Panel architecture

The visual layout is still static, but content is separated as:

```text
DockLayout
  -> PanelHost
       -> Panel
```

Each panel carries explicit capability flags for resize/move/dock/tab/close/float. All remain `false`. Future drag/drop changes layout behavior, not knowledge/read-model semantics inside a panel.

Dockview remains a compatible future candidate but is not yet a dependency.

## Deliberately absent

- production installers/signing/notarization;
- bundled standalone Python;
- real user filesystem-scope onboarding;
- generic renderer shell/process authority;
- localhost HTTP/WebSocket API;
- drag/drop or saved layouts;
- Explore / Observatory / Horizon / Agora logic;
- graph/map/timeline engines;
- Source Plane operations/dashboard;
- mutations.
