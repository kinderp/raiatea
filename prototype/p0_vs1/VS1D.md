# VS1d — Local EPUB extraction into persistent E-05 records

> Parent vertical slice: #187  
> Micro-step: #195  
> Status: implementation in progress

## Functional increment

VS1c gave Raiatea a replaceable, path-free `SourceReference` for each current
local EPUB source. VS1d adds the next product capability:

> **Raiatea can resolve an accepted SourceReference to the current local EPUB,
> extract its content and structure through a replaceable ExtractorPlugin, and
> retain the resulting E-05 records with provenance and EPUB source coordinates
> in the persistent catalog.**

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
E-05 ProcessingRun / ProviderEvidence / NormalizedRepresentation
        ↓
Core validation + revision-fenced persistence
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

## Rights boundary

VS1d crosses document bytes into the local extractor process, so it is stricter
than the reference-only VS1c discovery step.

For the promoted first slice, `extract.run/epub-direct-stdlib` requires
`rights_evidence_state = known-permitted`. `unknown`, `requires-review` and
`known-restricted` fail closed. Redistribution remains false and source bytes
remain local to the same host.

This is a product policy gate, not a legal conclusion. The benchmark/project-
created EPUB fixtures covered by the accepted CC BY 4.0 overlay provide the
first known-permitted test path.

## Extraction route

The first product extractor is exactly the route promoted in #187:

```text
extract.run / epub-direct-stdlib
```

It reuses the accepted direct stdlib EPUB parsing and E-05 adaptation logic, but
runs as product code with the VS1 process client/private broker instead of the
proof broker/harness.

Expected accepted records are:

- `ProcessingRunRecord`;
- `ProviderEvidenceRecord`;
- `NormalizedRepresentationRecord` when the route produces one.

Provider/native evidence stays distinct from normalized representation. A
successful process execution is never rewritten as a claim of complete or
perfect extraction.

## Source coordinates

EPUB coordinates remain package/resource/logical coordinates. VS1d must never
invent PDF-like page numbers for EPUB content. Source coordinates and provenance
must remain sufficient to trace extracted content back to the EPUB resource
that produced it.

## Persistence

VS1d extends the internal/revisable VS1 catalog payload with current extraction
state keyed by `source_ref_id`. The catalog retains the accepted E-05 records,
route/profile/plugin identity, source fingerprint and RightsDecision reference.

Persistence is revision-fenced. If observation/reconciliation/source discovery
changes the catalog while extraction is running, stale extractor output is
rejected rather than published.

## Functional boundary after VS1d

After VS1d Raiatea can know both:

```text
THIS source exists and is currently valid
```

and:

```text
THIS is the content/structure extracted from that exact source,
by this extractor route, with this provenance and these source coordinates.
```

It still cannot provide product search, Views or Smart Collections. Those are the
functional increment of VS1e.
