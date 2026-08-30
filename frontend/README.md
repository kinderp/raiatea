# Raiatea frontend renderer — GUI slice #217

This directory contains the first **renderer-only** Raiatea GUI vertical slice.

## Current boundary

```text
React / TypeScript renderer
        |
        v
RaiateaGateway
        |
        +-- DemoRaiateaGateway       [current renderer proof only]
        \-- live application bridge  [next decision / not implemented here]
                |
                v
        RaiateaApplicationFacade
```

The renderer does not import Python persistence, SourcePlugin, Provider-native or E-05 records. It speaks only application read-model shapes.

## Why demo data exists

The first renderer slice intentionally does **not** choose the Python/desktop transport. `DemoRaiateaGateway` is deterministic development data and the UI labels it visibly as **Prototype data**. It must never be represented as the user's current Raiatea Library or as Observatory knowledge.

The next bridge can replace the gateway without rewriting panels or screens.

## Run locally

Requires Node 22.12+.

```bash
cd frontend
npm install
npm run dev
```

Validation:

```bash
npm run typecheck
npm run test
npm run build
```

A committed lockfile becomes mandatory before #217 can merge. The initial CI may generate the first lockfile artifact from these exact top-level dependency pins; once committed, CI switches to `npm ci` only.

## Panel architecture

The first visual layout is static, but content is already separated as:

```text
DockLayout
  -> PanelHost
       -> Panel
```

Each panel carries explicit capability flags for resize/move/dock/tab/close/float. All are `false` in this slice. Future drag/drop must change the layout implementation, not knowledge/read-model semantics inside a panel.

Dockview is a compatible future candidate but is deliberately **not a dependency** yet.

## Deliberately absent

- Tauri / desktop packaging;
- Python sidecar or HTTP/IPC bridge;
- real filesystem-scope onboarding;
- drag/drop or saved layouts;
- Explore / Observatory / Horizon / Agora logic;
- graph/map/timeline engines;
- Source Plane operations/dashboard;
- mutations.
