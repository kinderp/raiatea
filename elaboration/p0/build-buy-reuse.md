# P0 Build / Buy / Reuse Decisions

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#125](https://github.com/kinderp/raiatea/issues/125)
>
> Survey: [`technology-survey.md`](technology-survey.md)
>
> Matrix: [`provider-matrix.md`](provider-matrix.md)

## 1. Purpose

This artifact converts the technology survey into **capability-level provisional
decisions**. It deliberately does not choose a monolithic Provider stack.

The decision vocabulary is:

- **reuse** — use a mature Provider/tool behind an Adapter;
- **compose** — combine multiple Providers/routes because the capability boundary
  is naturally layered;
- **build thin layer** — implement Raiatea-specific policy/normalization/control
  semantics around Providers, not the underlying recognition engine;
- **benchmark first** — retain multiple candidates until E-04 evidence exists;
- **defer** — relevant but outside the current P0 evidence slice;
- **reject for current scope** — do not use this option for the current bounded
  capability, with rationale.

`Buy` is treated separately as a sourcing/deployment option. A hosted API can be
reused or bought, but remote execution does not bypass rights/data/threat gates.

## 2. Decision principles

> Assertion status: `accepted-decision`, inherited from Inception/E-01

1. Build Raiatea's differentiating contracts, not commodity OCR/parser engines.
2. Keep Provider-native schemas behind Adapters.
3. Prefer deterministic/native extraction when it meets the Benchmark Class;
   VLM/OCR is a route, not a default ideology.
4. Use Source Family + traits + measured evidence for routing.
5. Treat model/license/deployment/security characteristics as part of a route.
6. Do not couple a Provider choice to the public P0 contract before benchmark
   evidence justifies the abstraction.
7. Keep reflowable EPUB semantics distinct from fixed-page PDF semantics.
8. Provider output, even from a local tool, is untrusted data until validated.
9. Remote processing is an explicit policy boundary, never a transparent
   substitute for local execution.
10. A self-reported benchmark cannot promote a candidate to `selected`.

## 3. Capability decision map

| Capability | Provisional decision | Candidate reuse/compose input | Why |
| --- | --- | --- | --- |
| MIME/content probing | **reuse** | Apache Tika; format-native probes | Mature breadth; no value in rebuilding large signature/parser registry |
| broad metadata extraction | **reuse + compose** | Tika + format-specific metadata | Metadata quality/provenance differs by source class |
| B-01 PDF structured extraction | **benchmark first** | Docling, Marker, MinerU, Unstructured, Tika baseline, PaddleOCR route | No measured Raiatea winner yet |
| B-02 EPUB semantic extraction | **benchmark first + build thin Adapter** | Docling, Pandoc baseline, safe direct package parser | Source anchors/spine/nav matter more than page layout |
| scanned-PDF OCR orchestration | **reuse + compose** | OCRmyPDF + Tesseract; later compare Paddle/Docling/Marker/MinerU | Mature OCR/PDF tooling exists |
| raw OCR engine | **reuse** | Tesseract; PaddleOCR and other engines as later benchmark routes | Training an OCR engine is outside P0 |
| scholarly PDF extraction | **defer + reuse later** | GROBID 0.9.0 | Specialist value belongs to B-04, not B-01/B-02 proof |
| semantic format conversion | **reuse + compose** | Pandoc; Provider-native exporters | Mature conversion ecosystem exists |
| page-faithful translated rendering | **defer** | future renderer composition | Translation/layout feature is gated outside current first proof |
| Provider-neutral normalized contract | **build thin layer** | adapt Docling/Marker/MinerU/Unstructured/Tika/GROBID outputs | Raiatea-owned interoperability boundary |
| Source Coordinate normalization | **build thin layer** | Provider bbox/page/DOM/TEI/package coordinates | Must preserve uncertainty; no Provider should define universal coordinates |
| routing policy | **build thin layer** | family/traits + benchmark + rights/security | Core Raiatea orchestration responsibility |
| rights/sensitivity route eligibility | **build thin layer** | E-01 rights/data boundary | Product/control-plane responsibility |
| Warning/Degraded Result normalization | **build thin layer** | Provider errors/confidence/diagnostics | Stable failure semantics are Provider-neutral value |
| Transformation/Provenance capture | **build thin layer** | Provider/model/version/params + input/output identity | Core Raiatea requirement |
| active-content/path/output isolation | **build thin control layer + reuse OS primitives** | process/container/sandbox primitives later | Security boundary cannot be delegated to document content/Provider |
| long-running Job/Run execution | **defer / audit first** | Durex candidate | Accepted boundary requires separate generic Job/Run audit |
| automatic filesystem organization | **defer** | Alfred observation + future Raiatea policy | Feature gate remains closed |
| natural-language query interpretation | **defer** | future LLM Provider | Not a P0 extraction requirement |
| TheBitLab course projection | **defer** | existing CourseSourceCatalog migration evidence | Consumer feature gate remains closed |

## 4. What Raiatea should build

> Assertion status: `provisional-decision`

### 4.1 Adapter interface

Build a small Provider boundary that can express at least:

```text
Provider identity/version
supported Source Family/traits/Benchmark Classes
input reference/version
route/options/model identity
Raw Extraction reference
Normalized result or mapping input
Source Coordinates / coordinate provenance
Warnings / degraded / failure / unknown state
resource/latency observations
rights/data-flow route class
```

This list is conceptual. E-05 will define the actual Provider-neutral contract.
Do not convert it directly into JSON/API classes from this document.

### 4.2 Route selector

Build routing around:

```text
Source family + traits
+ requested operation/output
+ Source Coordinate requirements
+ rights/sensitivity/retention policy
+ security/isolation eligibility
+ measured Benchmark Class evidence
+ resource/cost constraints
-> eligible route set
```

Do not implement:

```text
.pdf -> Docling
.epub -> Library X
```

as the durable architecture.

### 4.3 Normalization layer

Build a Raiatea-owned mapping from Provider outputs into the future normalized
contract while preserving access to Raw Extraction evidence under Retention
Policy.

Normalization must not:

- invent page/bbox data for formats without canonical pages;
- collapse Source and Catalog Entry;
- discard Provider/model/version provenance;
- silently convert unknown structure to a successful guessed hierarchy;
- hide Provider-specific warnings;
- conflate byte identity with semantic similarity.

### 4.4 Provenance and quality envelope

Build a stable envelope around every processing result that can later answer:

- which Source/version was processed;
- by which Provider/Adapter/model/version;
- with which material parameters/route;
- which output was produced;
- which Source Coordinates are supported and how;
- what degraded/failed/unknown;
- which rights/data/security route was used;
- whether an intermediate can be safely reused or must be invalidated.

The envelope is a Raiatea responsibility even if a Provider exposes its own
provenance metadata.

## 5. What Raiatea should not build now

> Assertion status: `accepted-decision` for current bounded scope

Do **not** build from scratch:

- PDF text/layout engine;
- OCR recognition model;
- table recognition model;
- formula recognition model;
- general MIME detector;
- universal Office parser;
- scholarly citation parser;
- EPUB renderer/converter;
- PDF/A OCR writer;
- general document converter;
- VLM foundation model.

The burden of proof is reversed: a new custom engine requires evidence that no
mature Provider can satisfy the bounded requirement behind an Adapter.

## 6. B-01 candidate route decision

> Assertion status: `working-hypothesis`

E-04 should compare **routes**, not brand names only.

Suggested B-01 route set:

1. `docling-native-pdf`;
2. `marker-fast`;
3. `marker-balanced` if model license/runtime is eligible for the benchmark;
4. `mineru-pipeline`;
5. `mineru-hybrid` or current recommended complex-document route;
6. `unstructured-fast`;
7. `unstructured-hi-res`;
8. `tika-native-baseline`;
9. one `paddleocr-document-parse` route if setup/fixture rights permit.

The exact list may be narrowed by E-03 fixture/runtime constraints. Each route
must record its Provider and model/backend separately.

### Why Docling receives priority, not selection

Docling has the closest documented alignment with:

- hierarchy;
- layout;
- page/bbox Provenance;
- lossless structured representation;
- broad local formats including EPUB;
- multiple OCR engines;
- permissive core code license.

That makes it an efficient **first benchmark implementation**, but only E-04 can
decide whether it meets the quality/manual-repair/resource gates.

## 7. B-02 candidate route decision

> Assertion status: `working-hypothesis`

Suggested B-02 route set:

1. `docling-native-epub`;
2. `direct-epub-package` — thin, non-executing container/manifest/spine/nav/XHTML
   parser with safe path handling;
3. `pandoc-epub-reader` semantic baseline;
4. optional Unstructured/Marker route only if it preserves enough original
   package/anchor evidence to compare meaningfully.

### Direct EPUB parser policy

The capability is approved for benchmarking; a library is **not** selected.
EbookLib proves that mature EPUB read/write libraries exist, but its AGPL license
and current path-traversal security issue make it unsuitable to silently adopt
as a neutral core dependency without review.

A direct route may instead use another maintained package library plus hardened
ZIP/XML/HTML primitives. That choice belongs after E-03 threat/fixture design.

## 8. OCR composition decision

> Assertion status: `provisional-decision`

Use OCR only when Source evidence indicates it is needed.

Possible layered flow:

```text
probe native text/layout
    |
    +-- usable native content -> native route
    |
    +-- image-only / bad OCR / mixed region
            -> OCR route
            -> layout/normalization route
```

OCRmyPDF/Tesseract provides a mature baseline for scanned PDF handling and
searchable PDF generation. PaddleOCR, Docling OCR backends, Marker/Surya and
MinerU are independent comparison routes for later scanned/complex classes.

Do not score B-01 by forcing OCR over good born-digital text.

## 9. Buy / hosted-service policy

> Assertion status: `provisional-decision`

No hosted Provider is selected in E-02.

A hosted service may later be evaluated only as a distinct route with:

- Provider/model/version;
- current terms/data retention/training/logging evidence;
- region/subprocessor information where relevant;
- explicit remote Processing Authority;
- Processing Rights and sensitivity eligibility;
- data-minimization record;
- cost/latency measurements;
- local fallback/replaceability story.

“Better extraction quality” alone cannot authorize private Source transmission.

For private/restricted corpora, a local route remains the conservative default
unless policy explicitly allows otherwise.

## 10. Licensing decisions

> Assertion status: `provisional-decision`; not legal advice

### Low-friction core-code candidates

Docling, Tika, GROBID, Tesseract, PaddleOCR and current Unstructured community
components expose permissive core code licenses. Exact transitive model/data
licenses still need a route manifest.

### Explicit review candidates

- **Marker:** current code files state Apache-2.0, while current model weights
  have modified AI Pubs Open Rail-M commercial conditions. Treat code and
  weights separately.
- **MinerU:** custom Apache-derived MinerU Open Source License includes commercial
  thresholds and online-service attribution obligations.
- **OCRmyPDF:** MPL-2.0 is usable in composition but modifications/distribution
  obligations differ from Apache/MIT.
- **Pandoc:** GPL-2.0-or-later requires ordinary distribution/integration review;
  a process boundary may be architecturally simpler depending on packaging.
- **EbookLib:** AGPL-3.0 plus current security concern; do not preselect.

Before public packaging, create a dependency/model license manifest for the
actual selected routes.

## 11. Security/isolation decision

> Assertion status: `provisional-decision`

Do not choose one sandbox technology in E-02. Do carry these requirements into
Provider benchmark setup:

- bounded input/output roots;
- non-executing active-content handling;
- no Source-controlled path escape;
- network disabled for local routes unless explicitly required;
- per-run resource/time limits where feasible;
- temporary/scratch isolation;
- validated Provider output before control-plane mutation;
- minimal diagnostic logging;
- exact Provider/model/dependency version record.

E-03/E-04 should record when a Provider cannot be evaluated safely under the
bounded environment rather than weakening the threat boundary.

## 12. Reuse architecture hypothesis

> Assertion status: `working-hypothesis`

A likely P0 shape is:

```text
Raiatea P0
  |
  +-- probe/type/metadata Adapter(s)
  |      +-- Tika / native probes
  |
  +-- route policy
  |
  +-- PDF extraction Adapters
  |      +-- Docling
  |      +-- Marker
  |      +-- MinerU
  |      +-- Unstructured
  |      +-- Tika baseline
  |      +-- PaddleOCR route
  |
  +-- EPUB Adapters
  |      +-- Docling
  |      +-- direct package parser
  |      +-- Pandoc baseline
  |
  +-- OCR Adapters
  |      +-- OCRmyPDF/Tesseract
  |      +-- later Paddle/Docling/Marker/MinerU routes
  |
  +-- scholarly Adapter [later]
  |      +-- GROBID
  |
  +-- Provider-neutral normalization
  +-- Source Coordinate mapping
  +-- Warning/degradation normalization
  +-- Provenance/Transformation envelope
```

The diagram is a benchmark/architecture hypothesis, not a package layout or
runtime deployment decision.

## 13. Decision gates before implementation selection

No B-01/B-02 route becomes the implementation default until evidence covers:

1. representative rights-safe fixtures;
2. content fidelity;
3. structural/read-order fidelity;
4. Source Coordinate fidelity;
5. asset/special-structure fidelity where applicable;
6. visible degradation/failure behavior;
7. manual repair burden;
8. CPU/GPU/RAM/disk/latency observations;
9. license/model eligibility;
10. safe local execution/isolation;
11. Adapter complexity and Raw Extraction availability;
12. version/reproducibility behavior.

A route can win one Source Trait profile and lose another. P0 may intentionally
retain multiple routes.

## 14. Outputs handed to E-03 and E-04

### E-03 fixture design

Must create fixtures that discriminate between candidates rather than simply
prove every tool can read a trivial file.

For B-01 include at least:

- clean single-column native PDF;
- multi-column reading order;
- headings/lists/links;
- figures/captions;
- table fixture;
- selected formula/code fixture;
- mixed/bad-text subprofile separated from baseline;
- malformed/restricted inputs outside normal score averages.

For B-02 include at least:

- multi-resource EPUB spine;
- nested navigation;
- internal/external links;
- images/captions;
- footnotes/endnotes;
- CSS/semantic structure;
- stable resource/fragment anchor expectations;
- scripted/unsafe resource fixture handled non-executingly.

### E-04 benchmark contract

Must compare routes using class-specific dimensions and preserve per-dimension
results rather than calculate one authoritative total score.

## 15. Out of scope

This artifact does not:

- select Docling or another Provider as production default;
- approve remote Provider use;
- implement routing/Adapters;
- define normalized JSON/API/database schema;
- implement OCR/translation/layout reconstruction;
- adopt Durex;
- implement auto-organization/NL search/TheBitLab integration;
- promote PDF+EPUB first slice to `planned` work.
