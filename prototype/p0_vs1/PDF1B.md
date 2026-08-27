# PDF1b — Local Poppler born-digital PDF extraction

> Parent PDF increment: #203  
> Micro-step: #206  
> Product PR: #207  
> Scope: local born-digital PDF, Poppler `pdftohtml-xml`, no OCR.

## Functional increment

PDF1a made PDF a current Source in the same local catalog as EPUB. PDF1b adds the
first ability to know what is inside a PDF:

```text
current PDF SourceReference
        ↓
Core current-source validation
        ↓
Core known-permitted RightsDecision
        ↓
exact accepted Poppler reference check
        ↓
VS1a safe PDF read + private copy
        ↓
official Poppler ExtractorPlugin
        ↓
path-free PopplerObservation
        ↓
Raiatea Core E-05 normalization
        ↓
second physical source-version fence
        ↓
current PDF extraction OR failed/restricted attempt evidence
```

For a successful born-digital PDF Raiatea can retain:

- extracted text surface;
- physical PDF page index;
- attributable bottom-left PDF-point bounding boxes;
- explicit URI links exposed by `pdftohtml`;
- explicit image evidence exposed by `pdftohtml`, including image bbox, generated
  asset byte length/SHA-256 and decoded pixel fingerprint when the bounded PNG
  decoder can establish it;
- Provider/version/profile and attempted-run provenance.

PDF1b does **not** invent heading/list/table/formula semantics from typography or
geometry. Poppler text units therefore enter the normalized representation with
semantic role `unknown`.

## Provider and platform boundary

The real Provider profile is deliberately exact:

- Poppler `24.02.0`;
- Ubuntu 24.04 reference environment;
- `pdftohtml` SHA-256
  `70bd5fbb655a14d0b02cb32cb53a601d3b0842a63553a24d1a6a612cf9f0624e`;
- `pdfinfo` SHA-256
  `3293dda06d80e1e38dab859aa47368c2876aedc41cbc2e24e8fb9a4e66392078`;
- `pdftohtml -xml -hidden -q`;
- no `-nodrm`;
- no remote Provider.

Core checks the exact local reference before source bytes cross the Provider
boundary; the plugin verifies it again; persisted product state revalidates the
same reference on reload.

Windows/Python matrix jobs validate contracts, Core normalization, RightsDecision
ordering and PDF1a compatibility. They do **not** constitute a Windows Poppler
runtime claim. A Windows Provider build needs its own measured pin before it can
be promoted.

## Rights-first behavior

The public PDF1b product facade establishes:

```text
current Source
 -> RightsDecision
 -> only if allowed: Provider preparation
 -> source-byte processing
```

`unknown`, `requires-review` and `known-restricted` stop before Poppler probing or
source-byte access. Allowed processing remains same-host, supplies no credential,
does not request an access-control override and does not authorize redistribution.

The lower-level orchestrator repeats the decision and all source/catalog fences;
the facade changes ordering, not authority.

## Provider evidence versus Core meaning

The official plugin emits only a closed `PopplerObservationBundle`. It does not
claim Core E-05 record ownership.

Core creates:

- `ProcessingRunRecord`;
- `ProviderEvidenceRecord`;
- `NormalizedRepresentationRecord` only for a publishable completed extraction.

Explicit links and image records remain in the persisted ProviderObservation
because the accepted normalized content schema does not yet have a truthful
first-class slot for those structures. They are not discarded and are not
coerced into unrelated text/semantic unit types.

Reading-order relations in the normalized representation preserve the emitted
Poppler block sequence and explicitly record that derivation basis. No stronger
semantic reading-order claim is made.

## Current extraction versus attempt evidence

PDF1b distinguishes:

```text
ProviderObservation produced
!=
Provider/domain extraction completed
!=
current normalized PDF content published
```

A successful route can populate `pdf1b.current_extractions`.

A malformed, restricted or otherwise non-completed Provider observation is kept
as bounded `pdf1b.attempts` evidence and cannot populate current normalized
content. Attempts retain source fingerprint, rights decision, route/plugin,
ProviderObservation, ProcessingRun/ProviderEvidence and invocation provenance.

Provider process success therefore never means document completeness. E-05
completeness/integrity remain `unknown` unless stronger evidence exists.

## Password/access-controlled PDFs

PDF1b never supplies a password and never adds `-nodrm` or another restriction
override.

The accepted B-01 evidence shows an important route-specific limitation:
`pdftohtml-xml` may fail on the protected fixture without exposing an explicit
password/encryption signal. PDF1b preserves exactly that evidence as a generic
failed attempt rather than upgrading it to `restricted` merely because the test
harness knows the fixture is encrypted.

This is intentional evidence-first behavior:

> known test-fixture truth is not silently copied into Provider evidence.

If a future Provider/profile exposes a trustworthy restriction signal, that
profile may produce an explicit restricted/rejected processing outcome.

## Image evidence boundary

PDF1b knows that an explicit image exists and can fingerprint/locate the generated
Provider asset while the private Provider workspace exists. Generated image
references must resolve inside that workspace; external absolute paths and
traversal fail closed.

The catalog stores evidence such as asset SHA-256 and decoded pixel SHA-256, not
the PNG/JPEG payload itself. Durable reusable derived-image storage is a later
separately promoted capability.

## Raw output fingerprint boundary

`raw_xml_sha256` is run provenance, not a semantic-determinism promise. Poppler
may embed temporary output references in its raw XML, so byte identity of raw XML
can vary while normalized/provider facts remain equivalent. No host path from the
raw XML is persisted in the product observation.

## Publication fences

Current PDF extraction is rejected when:

- the SourceReference is no longer current;
- VS1b freshness is not `fresh`;
- Stored Instance/media/fingerprint/length no longer align;
- the PDF changes after Source discovery;
- the PDF changes during Provider execution before publication;
- the catalog changes during Provider execution;
- ProviderObservation is malformed/tampered;
- persisted Provider reference no longer matches the promoted Poppler pin.

The plugin receives only a Core-private PDF copy; user root/Location never crosses
the Plugin API boundary.

## Finding log

| ID | Severity | Status | Finding | Resolution |
| --- | --- | --- | --- | --- |
| PDF1B-F1 | moderate | resolved | Initial service probed the local Poppler reference before evaluating the Core processing RightsDecision. No source bytes leaked, but a denied request incorrectly depended on Provider availability. | Added the public rights-first facade. A cross-platform regression patches the Provider probe to fail if it is reached and proves `unknown` rights stop first. |
| PDF1B-F2 | major | resolved | Initial product test expected the password-protected fixture to become `restricted/rejected`, but the exact `pdftohtml-xml` route supplies only a generic failure on that fixture. The test was promoting fixture knowledge into Provider evidence. | Keep the Provider observation as `failed`/attempt-only unless an explicit restriction signal is actually observed. No current content is published; no password/override is supplied. |
| PDF1B-F3 | moderate | resolved | Invocation-time pin validation was strong, but the base persisted-state shape validator did not re-check that retained observations still identify the exact promoted executable hashes. | Product state validator now re-verifies the Poppler reference for both current extraction and attempt history; tamper regressions cover version/hash drift. |

## Bounded residuals carried forward

- PDF1b state is additive (`pdf1b`) rather than generalized into the accepted
  EPUB-specific VS1d extraction wrapper. PDF1d will integrate source-class-
  agnostic search/backup over accepted EPUB and PDF current extractions without
  rewriting Provider-native schemas.
- The PDF1b public product facade wraps the lower-level validated orchestrator to
  enforce rights-first ordering. Before PDF1 exit, this should be folded into the
  general local product path together with PDF1a's bounded `Mixed*` adapters.
- no persistent derived image bytes;
- no Docling evidence yet;
- no automatic Poppler↔Docling alignment/fusion;
- no OCR, table enrichment or formula semantics.

## What becomes true after PDF1b

> Raiatea can take a current authorized born-digital PDF Source and extract its
> text plus attributable page/bbox geometry through the exact promoted local
> Poppler route, retain explicit link/image Provider evidence and E-05 lineage,
> and fail closed without publishing current content when the Provider/source/
> rights/catalog evidence is insufficient.

Search/View/Smart/backup integration for current PDF extraction is deliberately
completed in PDF1d after the complementary Docling profile is accepted.
