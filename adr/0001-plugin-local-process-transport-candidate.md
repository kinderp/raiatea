# ADR-0001 — Local plugin process transport candidate

Status: **Proposed**

Issue: #168  
Parent: #147

## Context

Plugin Manifest v1a and Plugin Runtime v1b are accepted. Raiatea now needs a local process transport that can carry those accepted records without turning wire framing into a second domain model.

The first implementation must preserve third-party process isolation, crash containment, bounded control-plane messages, structured diagnostics, cancellation semantics and opaque AssetHandle/RecordRef use. A transport decision is premature until real rights-safe SourcePlugin and benchmark-backed ExtractorPlugin proofs exercise it.

## Proposed candidate

Evaluate:

```text
JSON-RPC 2.0
  over local child-process stdin/stdout
  one UTF-8 JSON message per newline-delimited frame
```

For this candidate:

- stdout is protocol-only;
- stderr is non-authoritative process logging only;
- every frame is bounded before JSON decoding;
- large content never appears inline and continues to use v1b AssetHandle/RecordRef;
- JSON-RPC `id` is transport correlation only and is distinct from `invocation_id` and `idempotency_key`;
- JSON-RPC errors represent framing/protocol/method failures only;
- Plugin `RuntimeError`, E-05 `ProcessingOutcome` and Core `RightsDecisionRef` remain separate authorities;
- handshake succeeds before capability invocation;
- runtime records remain validated against the accepted v1b semantics independently of JSON-RPC.

This ADR does **not** accept JSON-RPC/NDJSON as the final transport.

## Alternatives

| Alternative | Advantages | Risks / costs | Current assessment |
| --- | --- | --- | --- |
| JSON-RPC 2.0 + NDJSON | very small dependency-light harness; standard request/error shape; easy cross-platform child-process use; notifications fit diagnostics | newline framing forbids arbitrary protocol stdout; large single messages still need hard cap; no built-in binary/stream framing | **Candidate to test** |
| JSON-RPC 2.0 + Content-Length/LSP-style framing | robust multiline payload framing; familiar language-server pattern | more parser state and header attack surface; little benefit while control plane remains small and assets use handles | Keep as fallback candidate |
| Minimal custom NDJSON envelope | smallest conceptual surface; total control | Raiatea would own correlation/error conventions unnecessarily; easier for wire model to drift into domain model | Do not prefer unless JSON-RPC semantics prove obstructive |
| In-process Python imports | trivial calls and debugging | violates third-party dependency isolation/crash containment; arbitrary code enters Core process | Negative control; reject for third-party V1 |

## Consequences

Positive if the candidate survives the harness:

- domain/runtime schemas stay transport-neutral;
- local process isolation remains possible with standard library only;
- synthetic and later real proof plugins can share a small conformance harness.

Costs/constraints:

- stdout must be reserved exclusively for protocol frames;
- stderr cannot substitute for structured diagnostics;
- process supervision, secret delivery and OS permission enforcement remain separate work;
- stateful idempotency/runtime-instance tracking remains supervisor-owned.

## Evidence required before acceptance

The ADR may move from Proposed to Accepted only after a separate proof-plugin child validates the same candidate with:

1. a rights-safe `LocalReadOnlySourcePlugin`;
2. one benchmark-backed `ExtractorPlugin` that consumes E-05;
3. positive and negative process/failure/cancellation cases without changing the transport except for evidence-forced fixes.

The synthetic plugin in #168 is transport test equipment only and does not satisfy this evidence requirement.

## Superseding decisions

None. If a later candidate replaces this one, preserve this ADR and link the superseding ADR rather than rewriting history.
