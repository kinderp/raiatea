# Raiatea Plugin Runtime v1 candidate

Status: **Draft / internal / transport-neutral**.

This contract follows the accepted Plugin Manifest v1a. The manifest answers what a plugin claims before execution; this runtime contract answers how Core observes a started instance and invokes a declared capability/profile without making the wire protocol the domain model.

## Boundary

V1b defines semantic records only:

- handshake;
- lifecycle transition;
- invocation request/result;
- cancellation request/acknowledgement;
- structured runtime error;
- `AssetHandle`, `OutputTargetHandle` and domain `RecordRef`;
- diagnostics and health reports;
- invocation provenance.

It does **not** choose JSON-RPC, stdio, HTTP, gRPC, WebSocket or another framing/transport. A later ADR must bind these records to a local transport and validate the choice with proof plugins.

## Handshake

Core validates a manifest before process launch. Runtime handshake must then match:

- plugin id/version;
- canonical validated-manifest fingerprint;
- runtime contract version;
- unique runtime instance id;
- advertised capability/profile pairs that are a subset of the manifest.

A runtime may advertise fewer profiles than its manifest if startup conditions reduce availability, but it may never broaden the manifest dynamically. Incompatible identity/fingerprint/version terminates before invocation.

The manifest fingerprint is SHA-256 over canonical JSON (`sort_keys=true`, compact separators, UTF-8). It is evidence binding the runtime instance to the exact prevalidated manifest, not a signature/trust decision.

## Lifecycle

Core-observable lifecycle states are intentionally small:

```text
starting -> ready -> stopping -> stopped
        \-> failed
        \-> incompatible
        \-> quarantined
ready   \-> failed | quarantined
stopping\-> failed | quarantined
```

`failed`, `incompatible`, `quarantined` and `stopped` are terminal for that runtime instance. Restart creates a new runtime instance id. Health `degraded` is a health/diagnostic condition, not a lifecycle state.

## Invocation

Runtime operation parameters are invocation-time data, not manifest data. A request references a declared capability/profile and a runtime instance that advertised it.

Large or authority-bearing inputs are never represented as inline bytes or host paths. Inputs are either:

- Core-issued `AssetHandle`; or
- versioned domain `RecordRef`.

The semantic validator additionally limits generic parameter JSON to 64 KiB, limits individual strings and rejects payload/path/credential-like parameter keys. This is a control-plane guard, not a substitute for operation-specific schemas.

Runtime context carries Core references such as workspace scope, RightsDecisionRef and **secret lease names/ids only**. Secret values are supplied by a later runtime mechanism and never become contract fields.

`idempotency_key` is Core-issued operation identity. V1b keeps it opaque: detecting reuse/collision requires supervisor state and is intentionally not faked by a stateless JSON Schema validator. A later runtime implementation must reject reuse of the same key for materially different operation intent.

## AssetHandle and output targets

`AssetHandle` is opaque Core-issued invocation authority, not Catalog identity and not a RightsDecision. It contains no host filesystem path.

Candidate access modes:

- `read` — input/read lease;
- `write-once-output` — completed output handle.

A not-yet-produced output is authorized with a separate `OutputTargetHandle`. This avoids overloading one field with two meanings:

- `AssetHandle.byte_length` is the observed/actual content length when known;
- `OutputTargetHandle.max_byte_length` is the Core-authorized output ceiling.

Handle authority is bounded by the invocation:

- a lease with `expires_at` must remain valid through the invocation `deadline_at`;
- the same handle id cannot be both an input read handle and an output target in one invocation;
- the plugin cannot mint a new output handle or change the Core-issued lease id;
- a completed asset output reports its actual `byte_length` and SHA-256 fingerprint;
- actual output length cannot exceed `max_byte_length` when the Core supplied a ceiling;
- result metadata cannot extend a Core-issued expiry or contradict a declared media type.

These checks make expiry/oversize rejection deterministic at the contract level while leaving actual OS/file-descriptor/sandbox enforcement to the later runtime implementation.

## Result and provenance

Plugin runtime status is not E-05 `ProcessingOutcome`. Runtime errors describe the invocation/process layer; extraction output still references accepted E-05 records.

Every invocation result includes provenance tying together plugin/version, runtime instance, invocation id, capability/profile, timing, input refs and output refs. Input/output provenance is checked against the invocation rather than trusted as plugin self-description. For extractor record outputs, `RecordRef.contract_id` must be `raiatea.extraction.processing-run`; Provider-native documents are not returned as a competing public extraction model.

## Cancellation and timeout

Cancellation and timeout remain separate facts:

- Core emits cancel request;
- plugin may acknowledge cooperation;
- terminal invocation status is `cancelled` only after positive acknowledgement plus cancelled runtime-error evidence;
- Core deadline expiration is `timeout`, not a plugin business/domain failure;
- Core may later force-kill a non-cooperative process after its deadline.

Rollback is not implied.

## Diagnostics and secrets

Diagnostics are structured evidence separate from lifecycle and domain outcome. Contract fields never carry a secret value. A runtime implementation that knows injected secret values must redact/reject both diagnostic messages and structured runtime-error messages containing those values before persistence or display.

## Deferred

- JSON-RPC/stdin-stdout or other transport ADR;
- process supervisor implementation, including stateful idempotency collision tracking;
- OS/container/WASM enforcement;
- actual secret delivery;
- installation/update/PKI/marketplace;
- remote/distributed plugins;
- real proof plugin implementation.
