# Plugin API v1d proof plugins

Status: **proof-only / non-production**.  
Issue: #170.  
Parent: #147.

This directory provides the real architecture proofs required before ADR-0001 can move from Proposed to Accepted.

## What is being proved

Two out-of-process plugins use the already merged contracts unchanged:

```text
Manifest v1a
    ↓
Runtime v1b
    ↓
JSON-RPC/NDJSON candidate v1c
    ↓
real proof plugin process
```

The proof does not introduce another transport or extraction model.

### LocalReadOnlySourcePlugin proof

- family: `source`;
- capability/profile: `source.discover/local-read-only`;
- project-created local fixture library only;
- network permission: none;
- filesystem declaration: read-only;
- source files are never modified, moved, deleted or republished;
- public result metadata contains no host path;
- result bundle is written only through a Core-issued write-once output target;
- source-reference record shape is explicitly `proof_only` and does not freeze a production SourceReference schema.

### Direct EPUB stdlib ExtractorPlugin proof

- family: `extractor`;
- capability/profile: `extract.run/epub-direct-stdlib`;
- input: Core-issued read AssetHandle for generated B02-EPUB-001;
- parser: accepted `elaboration/p0/benchmark/routes/epub_routes.py::parse_direct_epub`;
- E-05 adaptation: accepted `elaboration/p0/contracts/extraction/0.1.0/adapt_benchmark.py::adapt_direct_epub_observation`;
- output: E-05 ProcessingRun / ProviderEvidence / NormalizedRepresentation records stored in a Core-issued proof bundle target plus E-05 RecordRefs;
- EPUB coordinates remain logical/package coordinates; no synthetic rendered page numbers.

The generated EPUB is not versioned. Test setup regenerates it from the canonical project-created generator and requires SHA-256 `8a013c2e95ec99e07a29a09072872abe0c7e2fc0ba92378db9088817230be933` before the proof runs.

## Proof-only broker

`proof_broker.py` is intentionally **not** a production handle broker.

The public transport sees only:

- `workspace_scope_id`;
- handle id;
- lease id;
- normal v1b metadata.

A private sidecar under `.proof-runtime/broker.json` maps those opaque ids to relative paths under two fixed proof roots:

- `.proof-runtime/fixtures` — read authority;
- `.proof-runtime/outputs` — write-once proof outputs.

Resolution uses `Path.resolve()` + `relative_to(root)` and fails closed on scope escape. Output uses exclusive create (`xb`). The sidecar is ignored by git and never appears in a public runtime record.

This proves that the transport/contract does not require host paths. It does **not** choose the production mechanism (fd passing, broker service, sandbox mount, etc.).

## Failure evidence

The integration suite covers:

- undeclared Source/Extractor profile rejected before operation;
- Source workspace escape as RuntimeError, not transport error;
- Source process crash mapped to post-handshake `ready -> failed`;
- wrong EPUB media type as structured runtime failure;
- expired or write-mode input handle rejected by accepted v1b semantics;
- E-05 records validated after crossing the process boundary;
- no Provider-native extraction schema exposed in transport output;
- EPUB logical coordinates and negative PDF-coordinate conformance;
- v1a/v1b/v1c regression suites remain green.

## ADR decision rule

ADR-0001 remains **Proposed** until this proof PR reaches its own frozen-head CI and two clean review rounds. If the proof requires a material change to v1c, that change must be recorded and the synthetic v1c suite rerun before any transport acceptance.
