# ADR-0003 — Web-capable React renderer for the Raiatea GUI

Status: **Accepted**

Issue: #217  
Implementation PR: #218  
Architecture input: #211 / PR #213  
Executable application boundary: #214 / PR #216

## Context

Raiatea now has a reviewed application/read-model boundary and an executable first-party `RaiateaApplicationFacade`. The next slice needs a real visible renderer without undoing those ownership boundaries.

No frontend stack already exists in the repository: there is no current `package.json`, Tauri project or PySide application to preserve.

The long-term Raiatea UI is expected to become a dense Knowledge Navigator with Library/Source views first and later graph, timeline, map, Observatory, Horizon and structured deliberation surfaces. Panels should eventually be movable, resizable, dockable and persisted, but the maintainer explicitly does not require drag/drop in the first executable GUI slice.

The renderer decision is separate from the desktop-shell/transport decision. Choosing React must not silently choose HTTP, Tauri IPC or a Python sidecar protocol.

## Decision

Use **React 19 + TypeScript + Vite** as the Raiatea renderer stack.

For the first slice:

- the renderer is browser-capable and lives in `frontend/`;
- TypeScript is strict;
- all backend access crosses a typed `RaiateaGateway` interface;
- the current gateway is deterministic demo data used only to prove renderer structure;
- demo state is visibly labelled and is not Raiatea truth;
- `DockLayout -> PanelHost -> Panel` is implemented as a static layout abstraction;
- panel capability flags exist now, but movement/docking/resizing remain disabled;
- no docking library is selected in this ADR;
- no desktop shell or Python transport is selected in this ADR.

### Desktop direction

**Tauri 2 is the preferred candidate for a later desktop-shell proof**, not a dependency of this decision. Tauri supports web frontends including React and supports bundling external binaries/sidecars, including Python programs packaged as executables. A later ADR/spike must prove the actual RaiateaApplicationFacade lifecycle, packaging, authority and transport boundary before Tauri becomes an accepted product dependency.

The renderer must therefore remain usable both in a normal browser development server and inside a future desktop webview shell.

### Future docking direction

The content boundary must remain compatible with a later docking engine. Dockview is a current candidate because its React package exposes dockable panel/layout primitives and its core/React packages are MIT licensed, but adopting it now would add behavior the first slice explicitly does not need.

## Alternatives considered

| Alternative | Advantages | Costs / risks | Decision |
| --- | --- | --- | --- |
| React + TypeScript + Vite renderer | strong ecosystem for graph/map/timeline/data UI; browser-capable; typed; future Tauri/docking compatible | introduces Node build toolchain and a second language | **Chosen** |
| PySide6 / Qt Widgets | direct Python integration; mature native `QDockWidget`; no renderer bridge needed initially | desktop-only presentation model; richer web-style graph/map ecosystem is less direct; ties panel UX to Qt widget hierarchy | Rejected as primary renderer |
| Electron + React | mature desktop/browser integration; huge ecosystem | bundles a larger runtime and grants more Node/runtime surface than the renderer currently needs | Rejected for current target |
| Immediate Tauri + React + Python sidecar | directly produces a desktop app; strong future packaging story | forces Rust/toolchain, sidecar lifecycle and transport decisions before the application bootstrap boundary is proven | Deferred to dedicated desktop bridge proof |
| Vanilla TypeScript/DOM | minimal framework dependency | application state, composition and future complex panels would require custom infrastructure with little differentiating value | Rejected |

## Consequences

### Positive

- complex future knowledge visualizations can use the mature web ecosystem;
- the same renderer can be tested in a browser and packaged later;
- React components stay isolated from Python persistence and Source Plane deployment;
- future docking can replace only layout composition while preserving panel content;
- the application gateway gives tests a clean seam and prevents accidental backend-schema imports.

### Costs / constraints

- Raiatea gains a Node/npm build toolchain in `frontend/`;
- frontend dependencies require their own lockfile, CI and supply-chain review;
- a live bridge to `RaiateaApplicationFacade` still has to be designed and proven;
- React read models must stay synchronized with the application boundary through explicit contract tests rather than informal copying;
- desktop packaging remains incomplete until a later decision.

## Acceptance evidence

The candidate was accepted after #217 demonstrated the required evidence on reviewed head `b0fc85b1da820b39656d555284fd49ae46318943`:

1. strict TypeScript typecheck — success;
2. deterministic gateway and renderer-policy tests — success;
3. production Vite build — success;
4. executable AppShell with Library, Source Detail, structured Search and Inspector composition;
5. renderer accesses backend semantics only through `RaiateaGateway` application read models;
6. deterministic fixtures are persistently labelled as Prototype data and never presented as user/current Raiatea knowledge;
7. exact `package-lock.json` committed; final CI uses read-only `npm ci` only;
8. stale/blocked and last-known states remain visibly distinct from fresh empty/current states;
9. GUI AppShell workflow run `33301084979` — success;
10. two consecutive clean reviews on unchanged candidate head: review `5060311622`, then review `5060312903`; zero open review threads.

The temporary one-time dependency-lock bootstrap permission was removed before acceptance. The accepted workflow has `contents: read` only and no self-modification path.

## Not decided here

- REST, WebSocket, JSON-RPC or Tauri IPC;
- Tauri acceptance/packaging;
- Python sidecar packaging technology;
- frontend authentication/session model;
- Dockview or another docking engine;
- graph/map/timeline libraries;
- state-management library;
- routing library;
- component library/design system dependency;
- Source Plane operations UI.

## Superseding decisions

None.

If renderer evidence later shows React is the wrong boundary, preserve this ADR and supersede it rather than rewriting its history.
