# VS1d — Local EPUB extraction into persistent E-05 records

> Parent vertical slice: #187  
> Micro-step: #195  
> Status: **final candidate under PR #196**

## Functional increment

VS1c gave Raiatea a replaceable, path-free `SourceReference` for each current
local EPUB source. VS1d adds the next product capability:

> **Raiatea can resolve an accepted SourceReference to the current local EPUB,
> extract its content and structure through a replaceable ExtractorPlugin, and
> retain the resulting E-05 records with real product provenance and EPUB source
> coordinates in the persistent catalog.**

Before VS1d:

```text
local EPUB
  -> safe inventory/reconciliation
  -> SourcePlugin
  -> SourceReference
```

After VS1d:

```text
SourceReference
        ↓
Core current-source resolution
        ↓
known-permitted extraction RightsDecision
        ↓
VS1a safe source read
        ↓
Core-private extractor workspace copy
        ↓
official direct EPUB ExtractorPlugin
        ↓
product direct EPUB parser + product E-05 adapter
        ↓
E-05 ProcessingRun / ProviderEvidence / NormalizedRepresentation
        ↓
Core validation + physical-source fence + revision-fenced persistence
```

## Path and byte boundary

A `SourceReference` remains path-free. Core alone maps its opaque
`stored_instance_ref` to the current VS1b catalog entry and Location. Core reads
the source through the VS1a safe broker and copies the verified bytes into a
private temporary extractor workspace.

The ExtractorPlugin therefore receives:

- one opaque read AssetHandle for the private EPUB copy;
- one Core-issued write-once output target;
- one `rights_decision_ref`;
- extraction route/profile metadata carried by the accepted runtime request.

It does **not** receive:

- the user-authorized root;
- the original relative or absolute source path;
- Location history;
- filesystem mutation authority;
- ambient Core credentials;
- remote/network authority;
- permission to broaden the Core RightsDecision.

The source is verified twice through the VS1a broker: once before the private
copy is created and once after the ExtractorPlugin returns but before the
representation is published. This closes the window in which the physical file
could change before Alfred/catalog state catches up.

## Rights boundary

VS1d crosses document bytes into the local extractor process, so it is stricter
than the reference-only VS1c discovery step.

For the promoted first slice, `extract.run/epub-direct-stdlib` requires
`rights_evidence_state = known-permitted`. `unknown`, `requires-review` and
`known-restricted` fail closed. Redistribution remains false and source bytes
remain local to the same host.

This is a Core product-policy gate, not a legal conclusion. The benchmark
licensing decision remains a **redistribution** decision and is not treated as
a substitute for Processing Rights. VS1d test setup supplies the known-permitted
local-processing policy for project-created fixture material independently of
the CC BY 4.0 redistribution overlay.

The architectural distinction remains:

```text
Processing Authority != Processing Rights != Redistribution Rights
```

A later product increment must bind `known-permitted` to richer persisted rights
evidence rather than infer it from a redistribution license or Provider policy.

## Product extraction route

The first product extractor is exactly the route promoted in #187:

```text
extract.run / epub-direct-stdlib
```

The product implementation carries forward the behavior previously proven by
the benchmark route, but runtime product code no longer imports the benchmark
parser or the benchmark-only E-05 adapter.

Product-owned components are:

```text
prototype/p0_vs1/plugins/direct_epub/route.py
prototype/p0_vs1/plugins/direct_epub/e05_adapter.py
prototype/p0_vs1/plugins/direct_epub/plugin.py
```

The benchmark generator remains test-fixture infrastructure only.

The parser:

- reads EPUB ZIP members in place rather than extracting the package to disk;
- rejects absolute, traversal, backslash and other unsafe package-member names;
- parses container, OPF manifest/spine, XHTML blocks and navigation;
- records active-content presence without executing it;
- emits package/resource/fragment evidence for later E-05 normalization.

The product E-05 adapter emits the `official-local-extractor` channel and uses
real extraction start/end timestamps. No `benchmark-normalized-view`, benchmark
payload locator or fixed benchmark timestamp is allowed in persisted product
provenance.

## Publishable E-05 boundary

A Runtime result with `status = completed` only means the plugin process answered
successfully. It does **not** mean the document produced publishable content.

VS1d distinguishes:

```text
Runtime process completed
        !=
E-05 ProcessingRun execution completed
        !=
publishable current representation
```

For the promoted direct EPUB product route, the persistent current extraction
requires:

- valid `ProcessingRunRecord`;
- valid `ProviderEvidenceRecord`;
- `ProcessingRun.outcome.execution = completed`;
- one valid `NormalizedRepresentationRecord`;
- exact source-ref/fingerprint binding;
- exact promoted provider/route/profile;
- product provenance and no path authority;
- semantic E-05 validation and JSON Schema reference validation.

A rejected/failed EPUB is therefore observable as a failed extraction attempt at
the process boundary but is never silently published as current catalog
content.

## Source coordinates

EPUB coordinates remain package/resource/logical coordinates. VS1d never invents
PDF-like page numbers or PDF geometry for EPUB content.

For the canonical B-02 fixture, the end-to-end product test proves persisted
content including the first and second chapter surfaces, reading-order
relations, and `epub-logical` coordinates back to resources such as
`OEBPS/ch1.xhtml` and `OEBPS/ch2.xhtml`.

## Persistence and stale-output fences

VS1d extends the internal/revisable VS1 catalog payload with current extraction
state keyed by `source_ref_id`. The catalog retains:

- source fingerprint;
- catalog basis revision;
- RightsDecision;
- product plugin/route identity;
- E-05 record refs and records;
- Runtime provenance including the RightsDecision reference.

Publication is blocked when:

- the upstream VS1b catalog is not `fresh`;
- the SourceReference is no longer current;
- Stored Instance identity/fingerprint/length/media no longer match;
- the physical source changes before or during plugin execution;
- the catalog revision changes while the plugin is running;
- the plugin output is tampered, noncanonical, semantically invalid or
  schema-incompatible;
- E-05 reports a non-publishable execution outcome.

## Validation evidence

The final-candidate CI covers:

- Ubuntu and Windows;
- Python 3.10 and 3.12;
- real out-of-process product extraction;
- source-version publication fence;
- product provenance fence;
- product manifest schema validation;
- actual product-generated E-05 JSON Schema validation;
- VS1a/VS1b/VS1c regressions;
- accepted Plugin Runtime/transport/manifest and v1d proof regressions.

## Functional boundary after VS1d

After VS1d Raiatea can know both:

```text
THIS source exists and is currently valid
```

and:

```text
THIS is the current content/structure extracted from that exact source,
by this extractor route, with this provenance and these source coordinates.
```

It still cannot expose product search, Views or Smart Collections. Those are the
functional increment of VS1e.

## Explicit residuals / out of scope

- PDF/Docling/OCR;
- remote providers/extractors;
- natural-language or vector search;
- Views/Smart Collections;
- filesystem organization/mutation;
- richer persisted Processing Rights evidence resolution;
- large-input/resource-budget hardening beyond the bounded first-slice fixture;
- arbitrary untrusted third-party plugin sandboxing;
- generic cross-project Module Runtime;
- Durex.
