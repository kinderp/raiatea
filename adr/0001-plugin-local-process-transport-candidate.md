# ADR-0001 — Local plugin process transport

Status: **Accepted**

Issue: #168  
Evidence child: #170 / PR #171  
Parent: #147

## Context

Plugin Manifest v1a and Plugin Runtime v1b are accepted. Raiatea needs a local process transport that carries those accepted records without turning wire framing into a second domain model.

The transport must preserve third-party process isolation, crash containment, bounded control-plane messages, structured diagnostics, cancellation semantics and opaque AssetHandle/RecordRef use.

## Decision

For local V1 plugins, accept:

```text
JSON-RPC 2.0
  over local child-process stdin/stdout
  one UTF-8 JSON message per newline-delimited frame
```

The accepted boundary is deliberately narrow:

- stdout is protocol-only;
- stderr is non-authoritative process logging only;
- every frame is bounded before JSON decoding;
- large content never appears inline and continues to use v1b AssetHandle/RecordRef;
- JSON-RPC `id` is transport correlation only and remains distinct from `invocation_id` and `idempotency_key`;
- JSON-RPC errors represent framing/protocol/method failures only;
- plugin `RuntimeError`, E-05 `ProcessingOutcome` and Core `RightsDecisionRef` remain separate authorities;
- handshake succeeds before capability invocation;
- runtime records remain independently validated against accepted v1b semantics;
- transport framing does not expose host filesystem paths, secret values or rights grants.

This decision is for the local V1 plugin process boundary. It does not make JSON-RPC a Raiatea domain model and does not preclude a future superseding transport if evidence requires one.

## Evidence for acceptance

Synthetic v1c conformance established the candidate mechanics. Plugin API v1d then exercised the **same transport unchanged** with two real out-of-process proofs:

1. `LocalReadOnlySourcePlugin`
   - project-created deterministic local library;
   - no network permission;
   - read-only source scope;
   - private proof-only handle/scope broker kept outside wire records;
   - path/scope escape fails closed;
   - public proof records expose fingerprints/metadata but no host path;
   - subprocess crash is represented as lifecycle/process evidence rather than fabricated Source success.

2. direct EPUB stdlib `ExtractorPlugin`
   - benchmark-backed B-02 route;
   - Core-issued read AssetHandle input and write-once output target;
   - accepted E-05 ProviderEvidence/ProcessingRun/NormalizedRepresentation records cross the process boundary by RecordRef/opaque output bundle;
   - Provider-native schemas remain private;
   - EPUB logical/package SourceCoordinates remain distinct from PDF geometry;
   - wrong media type, expired/wrong-access handle and undeclared profile fail through the accepted runtime/domain layers.

Final proof evidence on head `99eeffdadd8213f70500de45968a03f2d247b5f2`:

- Plugin API v1d workflow `32713762585` — success;
- Linux Python 3.10 / 3.12 — success;
- Windows Python 3.10 / 3.12 — success;
- manifest/E-05 schema reference validation — success;
- accepted v1a/v1b/v1c regression suites — success inside every proof job;
- E-05 workflow `32713762546` — success after the source-class/SourceCoordinate conformance hardening discovered by the real EPUB proof.

No v1c transport change was required by either real plugin.

### Evidence-forced domain finding

The EPUB proof exposed an E-05 conformance gap: a structurally valid PDF coordinate could previously be attached to a known EPUB source class because coordinate shape and source class were validated independently.

That finding is tracked by #172 and fixed in the canonical E-05 semantic validator. It required **no transport change**. This is positive evidence for the layering: wire-valid/runtime-valid output can still be rejected by the domain layer without moving domain semantics into JSON-RPC.

## Alternatives considered

| Alternative | Advantages | Risks / costs | Decision |
| --- | --- | --- | --- |
| JSON-RPC 2.0 + NDJSON | small dependency-light harness; standard request/error shape; easy cross-platform child-process use; notifications fit diagnostics | stdout must remain protocol-only; bounded control-plane frames required; no binary streaming | **Accepted for local V1** |
| JSON-RPC 2.0 + Content-Length/LSP-style framing | robust multiline framing; familiar language-server pattern | more parser state/header attack surface with little current benefit because assets use handles | Deferred fallback |
| Minimal custom NDJSON envelope | minimal implementation surface | Raiatea would own correlation/error conventions unnecessarily and risks wire/domain drift | Rejected for V1 |
| In-process Python imports | trivial calls/debugging | violates third-party dependency isolation/crash containment | Rejected for third-party V1 |

## Consequences

Positive:

- domain/runtime schemas remain transport-neutral;
- third-party plugins remain out of the Raiatea Core process;
- a standard request/response/error envelope is available without duplicating Raiatea semantics;
- Source and Extractor plugins share one small cross-platform local harness;
- large artifacts remain outside control-plane JSON;
- real proof evidence shows the domain validator can reject bad semantic output independently of transport validity.

Costs/constraints:

- stdout is reserved exclusively for protocol frames;
- stderr cannot substitute for structured diagnostics;
- each frame requires an explicit size bound before parsing;
- the production supervisor must own process lifetime, runtime-instance uniqueness, idempotency collision tracking and forced termination;
- production AssetHandle resolution/brokering remains separate from this ADR;
- secret delivery and OS/container/WASM permission enforcement remain separate work.

## Not decided here

- production process supervisor implementation;
- production handle broker/storage binding;
- secret delivery mechanism;
- installation/update/discovery UX;
- OS/container/WASM sandboxing;
- remote/distributed plugin transport;
- marketplace/signature PKI;
- cross-project runtime extraction.

## Superseding decisions

None. If later evidence requires a different framing or transport, preserve this ADR and create a superseding ADR rather than rewriting this decision history.
