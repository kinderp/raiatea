# Raiatea frontend renderer

The React/TypeScript renderer consumes only Raiatea Application Layer read models.

## Current boundary

```text
React / TypeScript renderer
        |
        v
RaiateaGateway
        |
        +-- DemoRaiateaGateway
        |
        +-- LiveRaiateaGateway
                |
         ApplicationTransport
                |
        future Desktop Core adapter
                |
        local ApplicationFacade sidecar
                |
        RaiateaApplicationFacade
```

The renderer does not import Python persistence, SourcePlugin, Provider-native or E-05 records and does not own process launch, JSON-RPC framing or sidecar lifecycle.

`DemoRaiateaGateway` remains deterministic renderer-development data and is visibly labelled **Prototype data**. `LiveRaiateaGateway` is the #220 transport-neutral live client: it consumes an abstract `ApplicationTransport` and validates every returned bridge payload at runtime before exposing it to components.

## Live bridge truth boundary

The current bridge candidate preserves these rules on both Python and TypeScript sides:

- only Raiatea-specific read methods are exposed;
- host filesystem/root authority never belongs to renderer requests or results;
- current catalog Location is an authorized-scope relative projection only;
- stale Search is blocked and carries no current rows;
- non-fresh catalog/source state cannot be upgraded into current Source/content claims;
- retained representation ids still pass through the Python ApplicationFacade currentness fence;
- bridge/process success does not establish knowledge truth.

The current `App` intentionally instantiates the demo gateway until a trusted Desktop Core/Tauri adapter is proven. Switching to live must be a gateway-composition decision, not a component rewrite.

## Truth-state rendering

The renderer distinguishes an empty current result from an unavailable current result:

- a fresh search with no matches may display `0 match(es)`;
- a stale/blocked search displays the `blocked_reason`, renders no current rows and does not promote a Source into the Inspector;
- a non-fresh Library may show last-known catalog rows, but it displays a prominent last-known notice rather than implying current Source/content access;
- live adapters must not turn `stale`, `not-established` or last-known state into empty/current UI claims.

## Run locally

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

- Tauri / desktop packaging;
- Rust/Desktop Core adapter;
- renderer shell/process permissions;
- localhost HTTP/WebSocket API;
- Python executable bundling;
- real filesystem-scope onboarding;
- drag/drop or saved layouts;
- Explore / Observatory / Horizon / Agora logic;
- graph/map/timeline engines;
- Source Plane operations/dashboard;
- mutations.
