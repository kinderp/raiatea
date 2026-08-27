# PDF1c — Local Docling native semantic PDF extraction

> Parent PDF increment: #203  
> Micro-step: #208  
> Draft PR: #209  
> Status: implementation complete; final real-provider acceptance in progress

## Functional increment

PDF1b gave Raiatea a current born-digital PDF extraction through the Poppler
geometry/asset route. PDF1c adds an **independent semantic route** over the same
current PDF Source:

> **Raiatea can run the pinned local Docling 2.118.0 native/no-OCR profile,
> retain Docling's explicit text labels, attributable PDF coordinates,
> picture evidence and explicit picture↔caption relations, then let Core
> normalize only the evidence it can represent truthfully in E-05.**

The two PDF routes are complementary:

```text
current PDF SourceReference
        │
        ├── Poppler PDF1b
        │    ├── text
        │    ├── fine PDF geometry
        │    ├── explicit links
        │    └── explicit image/asset evidence
        │
        └── Docling PDF1c
             ├── text in Provider body order
             ├── explicit Provider labels
             ├── Core-aligned heading/paragraph/list/code/caption types
             ├── PDF geometry when attributable
             ├── explicit pictures
             └── explicit picture↔caption refs
```

## Non-fusion rule

PDF1c does not choose a global PDF truth and does not modify PDF1b state.

```text
Poppler ProviderEvidence != Docling ProviderEvidence
```

Raiatea does **not**:

- split a coarse Docling block with Poppler text boxes;
- copy Poppler bbox values onto Docling semantic blocks;
- align blocks by list position or text similarity;
- repair known Docling semantic mistakes from fixture/gold knowledge;
- infer a picture-caption relation from visual proximity;
- use benchmark gold as runtime truth.

Cross-Provider alignment/fusion remains a separate future increment.

## Exact Provider profile

The promoted route is exactly:

- Provider: Docling `2.118.0`;
- profile: `docling-2.118.0-standard-pdf-native-no-ocr`;
- accepted real runtime platform: Ubuntu 24.04 / CPython 3.12.14 / x86_64;
- top-level wheel SHA-256:
  `fd4962c9a54229bae1eb9b49f7fadb7e7b8affabf7e4fba1aac8cb335f558c8f`;
- accepted environment-freeze SHA-256:
  `54625595793321bdcb4f7b5763122b2c403ce1f4ecbd6d7837ab619a96c39456`;
- layout model payload: 11 files / 342,987,978 bytes;
- layout model payload manifest SHA-256:
  `c9afe973808a41c359c1f270f063097972985c096468089b206031395f8a885e`.

The profile keeps:

- CPU / 4 threads;
- local preloaded model artifacts;
- remote services disabled;
- external plugins disabled;
- OCR disabled;
- table structure disabled;
- code/formula enrichment disabled;
- picture classification/description disabled;
- chart extraction disabled;
- generated page/picture/table images disabled;
- `force_backend_text = false`;
- Hugging Face/Transformers offline controls;
- isolated Provider cache roots.

Changing those materially creates another profile and is outside PDF1c.

## Rights-first product path

The Core path is deliberately ordered so denied rights or a drifted Provider do
not receive source bytes:

```text
current PDF SourceReference
 -> validate fresh current Stored Instance
 -> Core known-permitted RightsDecision
 -> verify exact Docling wheel/dependency/model reference
 -> VS1a safe source read
 -> Core-private PDF AssetHandle
 -> official out-of-process Docling ExtractorPlugin
 -> path-free DoclingObservationBundle
 -> Core E-05 normalization
 -> second physical source verification
 -> expected-revision catalog fence
 -> current extraction OR bounded attempt evidence
```

`unknown`, `requires-review` and `known-restricted` processing evidence fail
before Provider preparation/source-byte access.

## ProviderObservation truth boundary

`DoclingObservationBundle` is closed and path-free. It retains:

- exact Provider/version/profile reference;
- source ref + source fingerprint;
- Provider conversion status and normalized observation status;
- body-order source;
- body text blocks with stable Provider refs;
- Provider label;
- Core-mapped semantic type only for the accepted label map;
- numeric semantic level only when Docling explicitly exposes `level`;
- page + bottom-left PDF bbox only when attributable from Docling provenance;
- provenance count/source;
- picture collection state (`present | unavailable | degraded`);
- explicit picture evidence;
- explicit caption blocks referenced by pictures;
- explicit `docling-picture.captions-explicit-ref` relations;
- bounded warnings;
- fingerprint of the canonical lossless Provider document when available.

Missing evidence remains missing. An unavailable picture collection is not an
explicit zero-picture observation.

### Text surface policy

ProviderObservation preserves Docling's explicit text string without generic
whitespace rewriting. For explicit `list_item` records, when lossless Docling
also exposes `orig`, PDF1c uses `orig` as the visible Provider surface so list
markers such as `1.`/`2.` are not discarded before Core normalization.

## Core E-05 normalization

Core, not the plugin, owns E-05 records.

For a successful ProviderObservation:

- text surface remains `provider-native` evidence;
- normalized semantic type is `raiatea-aligned`, because Raiatea maps Docling's
  explicit Provider label into the accepted semantic vocabulary;
- PDF coordinate is `raiatea-aligned`, because the product parser converts
  Docling provenance into bottom-left PDF points;
- reading-order relations are `raiatea-derived` from the explicit Docling body
  sequence;
- semantic correctness and whole-document completeness remain `unknown` rather
  than inferred from Provider `success`.

Picture/caption evidence remains ProviderObservation-side because the current
E-05 normalized schema has no sufficiently precise first-class slot for it.
PDF1c does not coerce it into unrelated normalized unit types.

## Current vs attempt evidence

PDF1c keeps two distinct product states:

```text
Docling success
 -> ProcessingRun execution=completed
 -> NormalizedRepresentation
 -> eligible for current extraction publication

Docling degraded / failed / restricted / unknown
 -> ProcessingRun + ProviderEvidence attempt
 -> no current NormalizedRepresentation
 -> no current-content publication
```

The Provider result is classified before `document.export_to_dict()` is called.
A normal Docling failure result therefore remains inspectable attempt evidence
instead of turning into a generic plugin crash.

## Source/catalog publication fences

Even after Provider output exists, publication requires:

- the original VS1a source handle still resolves to the same bytes;
- length and SHA-256 still match the SourceReference;
- the captured catalog revision is still current;
- the persisted Provider reference still matches the exact accepted Docling pin;
- the plugin has not claimed Core-owned E-05 record refs.

If any check fails, no stale Docling current extraction is published.

## Findings resolved during PDF1c

### PDF1C-F1 — observation structure could overclaim picture/caption/body order

The first contract shape risked treating an empty picture list as known-empty,
ordering blocks by Provider ref instead of body order, and assuming captions
participated in body order.

Resolution:
- explicit `picture_collection_state`;
- explicit `body_order_index` + `body_order_source`;
- separate `caption_blocks`;
- explicit relation refs and consistency checks.

### PDF1C-F2 — Provider failure could be exported as if a document existed

The first runtime called `result.document.export_to_dict()` before classifying a
normal Docling failure result.

Resolution:
- classify `result.status` first;
- failed/restricted/unknown become attempt observations with zero current blocks;
- only completed/partial observation paths may export the lossless document.

### PDF1C-F3 — dependency verifier compared unrelated environment packages

The first product verifier compared the accepted dependency lock with every
installed distribution, including packaging/admin tools outside the lock.

Resolution:
- verify exactly the constrained package-name set;
- packaging tools such as `pip` are irrelevant unless they are explicitly in the
  accepted lock.

### PDF1C-F4 — normalized semantics could be misattributed or overleveled

The initial mapper inferred `title -> heading level 1`, and E-05 labeled the
Core semantic mapping `provider-native`.

Resolution:
- `title`/`section_header` may map to normalized `heading`, but numeric level is
  retained only from explicit Docling `level` evidence;
- E-05 semantic mapping is `raiatea-aligned`;
- Provider text surface remains `provider-native`.

### PDF1C-F5 — lossless list markers could be discarded

The initial ProviderObservation always used Docling normalized `text`, although
lossless `list_item` records may expose a more faithful visible `orig` surface.

Resolution:
- explicit `list_item` uses non-empty `orig` when available;
- other labels continue to use Docling `text`;
- no typography inference is introduced.

## Platform boundary

Cross-platform Ubuntu/Windows Python 3.10/3.12 tests validate contracts, Core
orchestration, rights ordering, persistence and fail-closed behavior.

A **real Docling runtime claim is limited to the exact Ubuntu 24.04 / CPython
3.12.14 / x86_64 reference environment**. Windows contract CI does not imply a
measured Windows Docling runtime.

## Explicitly out of scope

- automatic Poppler↔Docling alignment/fusion;
- OCR/RapidOCR or scanned/image-only PDF support;
- `do_table_structure=true` or other table enrichment;
- formula enrichment/math semantics;
- picture classification/description;
- durable extracted picture bytes;
- remote Providers;
- password guessing/recovery or access-control override;
- PDF editing/filesystem mutation;
- hostile third-party plugin sandboxing;
- public Catalog/E-05 API freeze.

## Functional state after PDF1c acceptance

After final real-provider acceptance, this bounded statement becomes true:

> **Raiatea can process the same authorized born-digital PDF through an
> independent pinned Docling semantic route, preserve explicit semantic labels,
> attributable PDF coordinates and picture-caption relations, normalize only
> supported evidence through Core-owned E-05, and keep non-success Provider
> outcomes as attempt evidence without contaminating Poppler state.**

PDF1d then makes the accepted PDF extraction routes participate explicitly in
search/View/Smart/backup behavior.
