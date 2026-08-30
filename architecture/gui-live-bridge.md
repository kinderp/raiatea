# GUI live application bridge

Status: **candidate architecture under #220**  
ADR: `adr/0004-gui-local-application-bridge.md`

## Purpose

Connect the React renderer to real `RaiateaApplicationFacade` read models without exposing Python persistence, filesystem authority or sidecar process control to the webview.

## Layering

```text
React panels
    |
RaiateaGateway
    |
LiveRaiateaGateway
    |
ApplicationTransport                 renderer-owned abstraction
    |
----------------------------------   desktop trust boundary
    |
Desktop Core adapter                 future Tauri candidate
    |
versioned local bridge
    |
Python ApplicationFacade sidecar
    |
RaiateaApplicationFacade
    |
Catalog / Search / ExtractionReader
```

The renderer never imports or understands JSON-RPC. The current Python proof binds the local sidecar to bounded JSON-RPC 2.0/NDJSON because that framing has already been exercised cross-platform in Raiatea. A future Tauri adapter may own that process protocol completely behind `ApplicationTransport`.

## Bridge v0.1 methods

```text
gateway.status
library.page
source.detail
search.page
representation.page
```

All are read-only. Pagination remains application-level; the bridge does not expose store offsets or Source Plane worker topology.

## Bootstrap versus renderer authority

Current proof process bootstrap:

```text
python -m prototype.p0_vs1.application_bridge_sidecar \
  --catalog-store <trusted absolute internal path> \
  --scope-id <Core-selected opaque scope id>
```

This is **trusted parent configuration**, not a renderer API. Neither value may appear in renderer requests or results. Future Desktop Core work may replace command-line bootstrap with another private configuration mechanism without changing `RaiateaGateway`.

## Two-sided validation

Python validates:
- closed JSON-RPC request shape;
- supported method and parameter set;
- frame bounds;
- host-authority field exclusion;
- application facade truth/freshness semantics.

TypeScript validates again:
- bridge version + method;
- application model shapes required by the renderer;
- relative Location/fingerprint constraints;
- no recursively supplied host authority;
- stale Search has no current rows;
- non-fresh catalog/source models cannot assert current Source/content.

A shared JSON fixture is consumed by both Python and TypeScript so the languages cannot drift silently on the basic wire envelope.

## Why this is not Plugin transport

ADR-0001 remains evidence for the local process framing mechanics. GUI Application Bridge is a separate contract because Plugin transport has different control-plane restrictions and domain ownership. In particular, `LibraryItem.content` is legitimate application metadata and must not be rejected merely because Plugin transport forbids inline `content` payloads.

## Next step after #220

If the bridge is accepted, perform a dedicated desktop-shell proof:

```text
Tauri Command
   -> Rust/Desktop Core
      -> owns Python sidecar
      -> implements ApplicationTransport for React
```

The proof should grant the webview only named Raiatea commands, not generic shell permissions, and should separately solve Python executable packaging/lifecycle.
