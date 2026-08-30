# ADR-0004 — Local GUI Application Bridge boundary

Status: **Proposed**

Issue: #220  
Renderer decision: ADR-0003  
Application facade: #214 / PR #216

## Context

Raiatea now has a React/TypeScript renderer behind `RaiateaGateway` and a Python `RaiateaApplicationFacade` that exposes truthful, paginable application read models. The remaining local-product gap is how a future desktop shell connects those two boundaries without giving the web renderer filesystem or process-launch authority and without creating a second application domain model in transport code.

The repository already proved JSON-RPC 2.0 over bounded newline-delimited stdin/stdout for local Plugin processes in ADR-0001. The GUI bridge cannot reuse that Plugin transport contract literally: the Plugin control-plane validator intentionally rejects broad payload keys such as `content`, while `LibraryItem.content` is legitimate Application Layer metadata. The useful evidence is therefore the transport **mechanics**, not the Plugin-specific authority/content rules.

## Decision

Adopt a versioned **local GUI Application Bridge** boundary with these layers:

```text
React renderer
   -> RaiateaGateway
      -> ApplicationTransport
         -> future Desktop Core adapter
            -> local Python ApplicationFacade sidecar
```

For the local sidecar wire, use JSON-RPC 2.0 over one bounded UTF-8 JSON object per newline-delimited frame as the first proven transport binding.

### Renderer authority

The renderer does not:

- launch the Python process;
- receive generic shell/process APIs;
- receive the catalog-store host path or filesystem root;
- own JSON-RPC ids, framing or sidecar lifecycle;
- import prototype persistence, E-05 or Provider-native records.

It sees only `RaiateaGateway` methods and application read models.

### Desktop/Core authority

A trusted future Desktop Core owns sidecar startup, restart, termination and Core-owned bootstrap configuration. The current proof passes the catalog-store path and opaque scope id at process bootstrap; those values are never renderer request parameters or public application results.

### Wire surface

Bridge version `raiatea.gui-application-bridge.0.1.0` exposes only:

- `gateway.status`;
- `library.page`;
- `source.detail`;
- `search.page`;
- `representation.page`.

Requests are closed objects and notifications are not part of v0.1. Responses wrap one application payload in a versioned method envelope. Protocol/correlation ids are transport-only.

### Safety/truth boundary

- frames are size-bounded before JSON decode;
- stdout is protocol-only and stderr is non-authoritative diagnostics;
- renderer-supplied host authority fields fail closed;
- application responses are scanned again by TypeScript runtime validators;
- current relative catalog Location is permitted, absolute host paths are not;
- stale Search cannot carry current rows;
- non-fresh catalog/source models cannot be upgraded to current content;
- retained representation ids still pass through `RaiateaApplicationFacade` currentness fences;
- process completion is not knowledge truth.

### Tauri direction

Tauri 2 remains the preferred next Desktop Core candidate, but is **not selected by this ADR**. A later proof should bind `ApplicationTransport` to narrowly scoped Tauri Commands while Rust/Desktop Core owns the sidecar. The webview should not receive Tauri Shell capability for generic process execution.

## Alternatives considered

| Alternative | Advantages | Risks / costs | Decision |
| --- | --- | --- | --- |
| Versioned local sidecar bridge + abstract renderer transport | isolates Python/process concerns; reuses proven framing mechanics; future Tauri adapter can be narrow | requires cross-language validation and lifecycle work | **Chosen** |
| Localhost HTTP/WebSocket API | easy browser tooling and familiar API model | opens network/listener/auth/CORS/port lifecycle concerns for a local desktop-only boundary | Rejected for first local bridge |
| Renderer launches Python directly | fewer layers | grants process authority to webview and couples React to sidecar protocol/lifecycle | Rejected |
| Tauri Commands + sidecar in the same first step | directly reaches desktop product | mixes wire/domain proof with Rust, packaging and lifecycle decisions | Deferred |
| Direct Python embedding in desktop shell | low wire overhead | strong runtime/ABI coupling; does not fit browser-capable renderer boundary | Deferred/rejected as current default |

## Consequences

Positive:

- renderer remains transport- and deployment-neutral;
- Python ApplicationFacade remains the semantic read authority;
- future Tauri adapter can replace only `ApplicationTransport`;
- no localhost network service is required;
- cross-language runtime validation catches schema/epistemic drift before UI use.

Costs/constraints:

- TypeScript and Python bridge validators must be maintained with explicit compatibility tests;
- sidecar packaging and trusted bootstrap are still future work;
- current 1 MiB wire frame bound requires paginated application surfaces and may need measured revision later;
- Desktop Core must eventually own cancellation, restart and lifecycle failure semantics.

## Acceptance evidence required

This ADR remains Proposed until #220 demonstrates on a frozen head:

1. real Python subprocess sidecar over current VS1 ApplicationFacade data;
2. Library -> Source Detail -> Search -> Representation live read chain;
3. malformed/oversized/host-authority requests fail closed;
4. TypeScript runtime validation of shared bridge fixtures and hostile payloads;
5. `LiveRaiateaGateway` maps all methods through transport-neutral `ApplicationTransport`;
6. Linux/Windows Python 3.10/3.12 bridge tests green;
7. locked frontend typecheck/tests/build green;
8. two consecutive clean review rounds.

## Not decided here

- Tauri acceptance or Rust project layout;
- Python executable bundling;
- sidecar bootstrap transport replacing command-line arguments;
- cancellation/streaming/event notifications;
- write/mutation commands;
- remote/cloud API;
- multi-user authentication;
- Source Plane transport.

## Superseding decisions

None.
