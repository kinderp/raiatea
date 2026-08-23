# Raiatea Plugin Manifest v1 candidate

Status: **Draft / internal / transport-neutral**.

This contract is the first executable slice of #147. It defines what Raiatea can validate **before executing plugin code**. It does not define JSON-RPC, stdio framing, supervision, cancellation, sandbox enforcement, installation/update, marketplace behavior or cross-project runtime abstractions.

## Core ownership

Raiatea Core owns domain meaning, rights decisions, provenance policy, E-05 extraction semantics, normalized representations and state mutation rules.

Plugins declare capabilities and profiles. A manifest is evidence about what code claims it can do; it is not authorization and it is not a benchmark-quality guarantee.

## Identity and compatibility

- `manifest_version` versions this manifest schema.
- `plugin.plugin_id` is stable plugin identity.
- `plugin.version` is the plugin release version.
- `raiatea_plugin_api` is an explicit compatible range; incompatible major ranges fail before execution.
- Domain contract compatibility is declared per capability profile.

Extractor profiles reference `raiatea.extraction.processing-run` 0.1.x rather than restating ProcessingRun/ProviderEvidence/NormalizedRepresentation fields. The plugin API therefore consumes E-05 and does not create a parallel extraction domain model.

## Families and capabilities

V1 families are limited to:

- `source`
- `extractor`
- `transformer`

Capabilities are not brand-level booleans. Each capability contains one or more named profiles. Profile identity is the routing unit.

Example:

```text
plugin org.raiatea.benchmark-extractor
  extract.run / pdf-native-no-ocr
  extract.run / pdf-rapidocr-torch-en
```

These profiles may differ in backend, mode, model payload and observed benchmark evidence. Manifest presence does not assert completeness, accuracy or quality equivalence.

## Permissions

Permissions are declarations only in v1a:

- network hosts/scopes;
- filesystem root + `read` or `read-write` mode;
- secret **names**, never values;
- temporary workspace requirement;
- optional CPU/memory/timeout hints.

A declared permission is not an authorization grant. Core rights/policy remains separate. Trust tier (`official`, `verified`, `community`, `local`) is metadata and never grants network, filesystem, acquisition or Processing Rights.

V1a forbids wildcard network hosts. Later runtime work must state which declarations are technically enforced versus merely inspected.

## Entrypoint

`entrypoint.kind=process` plus a command is only launch metadata for future runtime binding. It intentionally does not choose stdio/JSON-RPC, HTTP, gRPC or any protocol.

## Examples

- `local-read-only-source.json` — SourcePlugin proof manifest, local read-only scope, no network.
- `benchmark-backed-extractor.json` — ExtractorPlugin proof manifest with two distinct profiles and E-05 contract references.
- `minimal-transformer.json` — deterministic TransformerPlugin proof manifest with no broad authority.

## Validation

`validate_manifest.py` enforces cross-field invariants that are awkward or overly speculative to encode only in JSON Schema: API range intersection, family/capability consistency, unique capability/profile identity, E-05 reference rules, wildcard-network rejection, secret-value rejection and separation of trust/rights authority.

`test_manifest.py` contains positive and negative conformance tests. Dedicated CI also validates the schema and examples with pinned JSON Schema Draft 2020-12 support on Linux/Windows and Python 3.10/3.12.

## Deferred

- transport and request/response envelopes;
- process lifecycle/supervisor;
- timeout/cancellation protocol;
- OS/container/WASM sandboxing;
- signature PKI/marketplace;
- plugin installation/update repository;
- real Source/Extractor/Transformer plugin implementations;
- shared Alfred/FARO/TheBitLab runtime.
