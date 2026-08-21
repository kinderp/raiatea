# P0 Extraction Technology Survey

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 1.0.0
>
> Last reviewed: 21 August 2026
>
> Accepted through: [PR #126](https://github.com/kinderp/raiatea/pull/126)
>
> Observation date: **21 August 2026**
>
> Parent issue: [#125](https://github.com/kinderp/raiatea/issues/125)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Boundary input: [source taxonomy](source-taxonomy.md),
> [rights/data boundary](rights-data-boundary.md), and
> [threat boundary](threat-boundary.md)

## 1. Purpose

This survey records the current documented capabilities, deployment boundaries,
licenses and known constraints of candidate extraction Providers and supporting
tools for Raiatea P0.

It exists to answer a narrower question than a benchmark:

> **Which mature capabilities are worth reusing or composing behind Raiatea
> Adapters, and which candidates deserve source-class benchmark evidence?**

This document does **not** rank extraction quality using Provider-published
scores, select a winning stack, or promote the PDF/EPUB candidate first slice to
`planned` implementation.

## 2. Evidence discipline

> Assertion status: `accepted-decision`, inherited from Inception/E-01

The survey applies these rules:

1. Prefer official project documentation, official repositories, tagged
   releases and official package registries.
2. Pin rapidly changing claims to a version/release and observation date.
3. Distinguish **documented capability** from **Raiatea-measured evidence**.
4. Treat Provider self-benchmarks as hypotheses/inputs to E-04, not as proof of
   superiority.
5. Treat code license, model-weight license and hosted-service terms as separate
   facts.
6. A format listed as “supported” does not prove the Source Coordinates,
   hierarchy, reading order or fidelity required by a Raiatea Benchmark Class.
7. Local installability does not prove safe isolation for untrusted Sources.
8. No remote route is eligible merely because an API exists; E-01 rights/data
   policy still applies.

## 3. Survey snapshot

The following versions/releases are the pinned baseline for this artifact.
A later benchmark must record the exact version actually executed.

| Candidate | Pinned snapshot | Primary evidence | Notes |
| --- | --- | --- | --- |
| Docling | `v2.117.0`, 30 Jul 2026 | [release](https://github.com/docling-project/docling/releases/tag/v2.117.0), [README](https://github.com/docling-project/docling), [DoclingDocument](https://docling-project.github.io/docling/concepts/docling_document/) | Tagged release used rather than newer untagged/dependent-package observations |
| Marker | `v2.0.0`, 20 Jul 2026 | [release](https://github.com/datalab-to/marker/releases/tag/v2.0.0), [README](https://github.com/datalab-to/marker), [pyproject](https://github.com/datalab-to/marker/blob/master/pyproject.toml) | Code/model licensing must be evaluated separately |
| MinerU | `3.4.4`, release workflow 10 Jul 2026 | [repository](https://github.com/opendatalab/MinerU), [release workflow evidence](https://github.com/opendatalab/MinerU/actions/runs/29090728963), [license](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md) | Custom MinerU Open Source License, not plain Apache-2.0 |
| Unstructured | `0.25.0`, observed latest 21 Aug 2026 | [releases](https://github.com/Unstructured-IO/unstructured/releases), [PDF partitioner](https://github.com/Unstructured-IO/unstructured/blob/main/unstructured/partition/pdf.py) | Partition/ETL model is element-oriented rather than a page-faithful document IR |
| Apache Tika | `3.3.2`, 16 Jul 2026 | [official release page](https://tika.apache.org/3.3.2/), [download](https://tika.apache.org/download) | `4.0.0-beta-1` is preview, not survey baseline |
| GROBID | `0.9.0`, 7 Apr 2026 | [release](https://github.com/grobidOrg/grobid/releases/tag/0.9.0), [install docs](https://github.com/grobidOrg/grobid/blob/master/doc/Install-Grobid.md) | Scholarly-specialized route |
| OCRmyPDF | `17.10.0`, 5 Aug 2026 | [release](https://github.com/ocrmypdf/OCRmyPDF/releases/tag/v17.10.0), [PyPI](https://pypi.org/project/ocrmypdf/17.10.0/), [docs](https://ocrmypdf.readthedocs.io/) | PDF OCR orchestration, not general structured-document parser |
| Tesseract | `5.5.3`, 24 Jul 2026 | [releases](https://github.com/tesseract-ocr/tesseract/releases), [tessdoc](https://github.com/tesseract-ocr/tessdoc/blob/main/ReleaseNotes.md) | OCR engine; image input rather than PDF document semantics |
| PaddleOCR | `v3.7.0`, 11 Jun 2026 | [repository](https://github.com/PaddlePaddle/PaddleOCR), [releases](https://github.com/PaddlePaddle/PaddleOCR/releases), [pyproject](https://github.com/PaddlePaddle/PaddleOCR/blob/main/pyproject.toml) | Includes OCR, PP-Structure/PaddleOCR-VL and document parsing capabilities |
| Pandoc | `3.10.2`, 11 Aug 2026 | [official releases](https://pandoc.org/releases.html) | Converter/AST utility; not a visual-layout extractor |
| EbookLib | `0.20`, observed latest 21 Aug 2026 | [release](https://github.com/aerkalov/ebooklib/releases/tag/v0.20), [README](https://github.com/aerkalov/ebooklib) | EPUB2/EPUB3 read/write; AGPL-3.0; security/path handling requires care |

Versions above describe the evidence snapshot only. They are not dependency
pins for implementation.

## 4. Docling

> Assertion status: `working-hypothesis` for P0 fit

### Documented capabilities

Docling is the broadest candidate in this survey for producing a structured,
layout-aware document representation from heterogeneous sources.

The official project documents support for PDF, Office/OpenDocument formats,
HTML/XHTML, EPUB, images, audio/video, Markdown/AsciiDoc/LaTeX, several XML
schemas and other source families. Its `DoclingDocument` can represent text,
tables, pictures, hierarchy/groups, furniture (headers/footers), bounding boxes
and Provenance. PDF processing includes layout, reading order, tables, code and
formula understanding. It can export lossless JSON, Markdown, HTML, text,
DocLang/DocTags and chunks.

Docling also documents local execution for sensitive/air-gapped data, multiple
OCR engines (including RapidOCR, Tesseract variants, EasyOCR and macOS OCR), VLM
options and an optional service layer.

Primary references:

- <https://github.com/docling-project/docling>
- <https://github.com/docling-project/docling/blob/main/docs/usage/supported_formats.md>
- <https://docling-project.github.io/docling/concepts/docling_document/>
- <https://docling-project.github.io/docling/reference/docling_document/>
- <https://docling-project.github.io/docling/concepts/OCR/>

### Source Coordinate fit

Docling's Provenance model includes page number, bounding box and character span
for layout-aware document items when available. This is unusually close to
Raiatea's `Source Coordinate` requirement for B-01 PDF.

For EPUB and other reflowable formats, format support alone is insufficient:
E-04 must verify whether the produced anchors are stable and expressive enough
for B-02's package-resource/logical-anchor requirements. A PDF-style bbox model
must not be assumed for reflowable content.

### Deployment and licensing

- Codebase: MIT.
- Individual model licenses: must be checked separately for the models actually
  selected.
- Runs on macOS/Linux/Windows and x86_64/arm64 according to project docs.
- Can be local/offline; optional remote/service deployments remain separate
  routes under E-01 policy.

### Known survey cautions

- `DoclingDocument` is **not** Raiatea's canonical domain schema. It is a
  Provider representation to adapt into a future Provider-neutral contract.
- Breadth of input support must not hide source-class differences.
- Model/OCR choice changes compute, license and security characteristics.
- Metadata extraction such as title/authors/references/language is still listed
  as coming-soon in the project README, so Raiatea must not assume a universal
  bibliographic metadata solution from Docling alone.

### Preliminary disposition

**Benchmark first + likely reuse behind an Adapter.**

Docling should be in the B-01/B-02 comparison set because its documented
hierarchy, layout and Provenance align strongly with P0 requirements. This is
not a selection decision.

## 5. Marker 2

> Assertion status: `working-hypothesis` for P0 fit

### Documented capabilities

Marker 2 is a document conversion pipeline centered on PDF-to-Markdown/JSON. It
combines embedded PDF text, layout detection, selective OCR/VLM use, equation
recognition, table reconstruction and optional LLM refinement. Version 2.0 adds
separate `balanced`, `fast` and no-OCR modes, with CPU support and an inference
server model for heavier VLM processing.

Its JSON renderer exposes block type, HTML, polygon, bbox, hierarchy, images and
children, which makes it relevant to Source Coordinate and structural-fidelity
experiments.

With the `full` optional dependencies Marker can accept non-PDF inputs including
EPUB/Office formats, but the implementation path may be conversion-oriented.
That must not be treated as proof that original EPUB package/DOM coordinates are
preserved.

Primary references:

- <https://github.com/datalab-to/marker/releases/tag/v2.0.0>
- <https://github.com/datalab-to/marker/blob/master/README.md>
- <https://github.com/datalab-to/marker/blob/master/marker/renderers/json.py>
- <https://github.com/datalab-to/marker/blob/master/pyproject.toml>

### Deployment

- Python >=3.10 and PyTorch.
- Fast/no-OCR modes can run on CPU.
- Surya VLM paths use a local inference backend; current docs identify vLLM for
  NVIDIA and `llama.cpp` for CPU/Apple Silicon.
- A July 2026 issue reports a clean macOS Marker 2 install failing when the
  external `llama-server` binary is absent. That is useful installation-risk
  evidence, not a universal failure claim.

### Licensing

Current `pyproject.toml` and current README state Apache-2.0 for code. The README
states that model weights use a modified AI Pubs Open Rail-M license with a
commercial threshold and separate licensing above that threshold.

Older/stale GitHub renderings have shown conflicting code-license wording. E-02
therefore records the current pinned project files as evidence but requires E-03
or an implementation decision to capture the exact code/model licenses bundled
by the selected route.

### Provider-published benchmark claims

Marker 2 publishes olmOCR-bench scores and throughput comparisons, including a
reproducible benchmark harness. These are valuable candidates for experiment
setup but remain **Provider-published evidence**. Raiatea must re-run relevant
source-class fixtures under E-04.

### Preliminary disposition

**Benchmark first for B-01; defer as B-02 semantic-coordinate solution until
proven.**

Marker may be a strong PDF candidate, especially for complex layout and
selective OCR. Its model-weight license and external inference runtime increase
Adapter/deployment review compared with a pure native parser.

## 6. MinerU

> Assertion status: `working-hypothesis` for P0 fit

### Documented capabilities

MinerU converts PDF/images/DOCX/PPTX/XLSX to Markdown/JSON and offers pipeline,
VLM and hybrid backends. Current source exposes local backends plus client/server
variants; `pyproject.toml` includes optional MLX support on macOS and vLLM/other
backends on other platforms. The CLI can retain intermediate JSON/model output,
draw layout/span boxes, and emit content lists, making it potentially useful for
Raw Extraction and inspection.

The project documents layout/read-order processing, tables, formulas, images,
OCR, multiple output modes and local deployment. Provider-published benchmark
claims must be independently reproduced before influencing a route decision.

Primary references:

- <https://github.com/opendatalab/MinerU>
- <https://github.com/opendatalab/MinerU/blob/master/pyproject.toml>
- <https://github.com/opendatalab/MinerU/blob/master/mineru/cli/common.py>
- <https://github.com/opendatalab/MinerU/blob/master/mineru/cli/backend_options.py>

### Licensing

MinerU 3.1+ uses the **MinerU Open Source License**, described as Apache-2.0 plus
additional terms. The current license permits commercial use without a separate
commercial license below stated consolidated MAU/revenue thresholds, imposes an
attribution obligation for third-party online services, and requires separate
commercial licensing above the thresholds.

This is materially different from plain Apache-2.0 and must be represented as a
license constraint in any reusable/public component decision.

Reference:
<https://github.com/opendatalab/MinerU/blob/master/LICENSE.md>

### Preliminary disposition

**Benchmark first.**

MinerU deserves B-01 complex-layout comparison, especially because it exposes
multiple backends and intermediates. The custom license and model/backend
complexity are explicit architecture/adoption inputs.

## 7. Unstructured

> Assertion status: `working-hypothesis` for P0 fit

### Documented capabilities

Unstructured is an open-source document ETL/pre-processing library designed to
partition heterogeneous files into typed `Element` objects. For PDF it supports
`fast`, `ocr_only`, `hi_res` and automatic routing behavior. Its PDF
implementation can attach page numbers, coordinate metadata, links, language,
detection origin, parent relationships, image metadata and table structure such
as HTML/cell representations depending on route.

The ecosystem separates the main partition library from `unstructured-inference`
layout models. Local model integration is possible; hosted API offerings are a
separate data boundary.

Primary references:

- <https://github.com/Unstructured-IO/unstructured/releases>
- <https://github.com/Unstructured-IO/unstructured/blob/main/unstructured/partition/pdf.py>
- <https://github.com/Unstructured-IO/unstructured-inference>

### Architectural fit

Unstructured's element-oriented output and rich connectors are very useful for
RAG/ETL and can preserve coordinates for PDF elements. It is less obviously a
lossless document-reconstruction IR than Docling's explicit document hierarchy
model. That is a fit question for P0: Raiatea needs Source-linked normalized
content, not only RAG chunks.

### Licensing/deployment

The open-source repositories expose Apache-2.0 licensing for the main community
components/inference ecosystem. Hosted platform/API behavior and data policy
must be considered separately if evaluated.

### Preliminary disposition

**Reuse/benchmark as an element-partition route and possible fallback; do not
assume it should define the canonical normalized document model.**

It belongs in B-01 comparison, and may be particularly valuable for broad
partition/connectors even if another Provider becomes the page-faithful PDF
route.

## 8. Apache Tika

> Assertion status: `working-hypothesis` for P0 fit

### Documented capabilities

Apache Tika is a mature Apache-2.0 toolkit for content detection and extraction
across a very broad format ecosystem. Stable version 3.3.2 (16 Jul 2026) added
SAX-based OOXML parsers as default and tightened server defaults. Tika 4.0.0
beta exists but is explicitly a preview line and is not the survey production
baseline.

Primary references:

- <https://tika.apache.org/>
- <https://tika.apache.org/3.3.2/>
- <https://tika.apache.org/download>

### Architectural fit

Tika is especially attractive for:

- MIME/content-type detection;
- broad metadata extraction;
- native text extraction across many formats;
- conservative `probe`/fallback functionality before a more specialized route.

Tika alone does not document the page-layout/hierarchy/Source Coordinate
fidelity required to make it the default B-01 document-understanding Provider.
Its value is therefore complementary rather than all-or-nothing.

### Preliminary disposition

**Reuse/compose as probe + metadata/native-text breadth.**

Do not build a format detector or broad metadata parser from scratch if Tika can
safely provide the needed capability. Benchmark only the source classes for
which Tika might plausibly serve as an extraction route, not every Tika parser.

## 9. GROBID

> Assertion status: `working-hypothesis` for specialized scholarly fit

### Documented capabilities

GROBID 0.9.0 is a specialized scholarly-document parser producing TEI with
structured headers, full text, bibliographic references/citations and scholarly
entities. The 0.9.0 release adds or improves author-contribution/conflict
statements, figures/tables/equations in annex/back sections, PDF-annotation URLs,
reference/header consolidation markers and ARM64 Docker support.

Earlier/current GROBID capabilities include optional coordinates for relevant
TEI structures and a service-oriented deployment model.

Primary references:

- <https://github.com/grobidOrg/grobid/releases/tag/0.9.0>
- <https://github.com/grobidOrg/grobid/blob/master/CHANGELOG.md>
- <https://github.com/grobidOrg/grobid/blob/master/doc/Install-Grobid.md>

### Architectural fit

GROBID's domain specialization is a strength for future B-04 scholarly PDFs and
a poor reason to force it into generic books/reports/EPUB. Its TEI output is a
Provider representation that would need a Raiatea Adapter.

### Preliminary disposition

**Compose as a future specialized scholarly route; defer from B-01/B-02 first
proof unless fixtures demonstrate direct need.**

## 10. OCRmyPDF + Tesseract

> Assertion status: `working-hypothesis` for OCR/PDF layer

### OCRmyPDF

OCRmyPDF 17.10.0 adds a searchable OCR text layer to PDFs, can preserve original
embedded image resolution, produce validated PDF/PDF-A output, rotate/deskew and
clean pages, distribute work across cores and orchestrate Tesseract. Version
17.x exposes `default`, `force`, `skip` and `redo` processing modes for existing
text/OCR layers.

Code license: MPL-2.0 in current releases.

Primary references:

- <https://github.com/ocrmypdf/OCRmyPDF/releases/tag/v17.10.0>
- <https://pypi.org/project/ocrmypdf/17.10.0/>
- <https://ocrmypdf.readthedocs.io/en/stable/advanced.html>

### Tesseract

Tesseract 5.5.3 (24 Jul 2026) is an Apache-2.0 OCR engine. It operates on image
content rather than understanding a PDF as a complete document container.
Tesseract supports OCR-oriented output formats including coordinate-bearing
formats through its ecosystem, but P0 should treat OCR tokens/lines/regions as
Raw Extraction evidence rather than assume a complete document hierarchy.

Primary references:

- <https://github.com/tesseract-ocr/tesseract/releases/tag/5.5.3>
- <https://github.com/tesseract-ocr/tessdoc/blob/main/ReleaseNotes.md>

### Architectural fit

OCRmyPDF + Tesseract is a strong **compose** candidate for SF-02 scanned/image
PDF preprocessing/searchability and a baseline OCR route. It is not a substitute
for layout/hierarchy extraction.

For B-01 born-digital PDFs, OCR should not be invoked by default merely because
it is available. E-04 must separate native-text and OCR routes.

### Preliminary disposition

**Reuse/compose as OCR/PDF normalization baseline; defer full SF-02 selection to
later benchmark.**

## 11. PaddleOCR / PaddleOCR-VL

> Assertion status: `working-hypothesis` for OCR/VLM/document parsing

### Documented capabilities

PaddleOCR 3.x is an Apache-2.0 document OCR/parsing ecosystem with text
detection/recognition, document preprocessing, layout detection, formula,
table/chart and document-VLM pipelines. Current packaging includes document
parser, translation and document-to-Markdown extras; official project material
advertises PDF/image structured parsing and 100+ language coverage.

The release history is moving quickly: official repository metadata observed on
21 Aug 2026 identifies `v3.7.0` as the latest release (11 Jun 2026), while
individual search snapshots may lag behind. E-04 must therefore pin the exact
model and runtime independently from the Python package version.

Primary references:

- <https://github.com/PaddlePaddle/PaddleOCR>
- <https://github.com/PaddlePaddle/PaddleOCR/releases>
- <https://github.com/PaddlePaddle/PaddleOCR/blob/main/pyproject.toml>

### Architectural fit

PaddleOCR is a strong candidate for OCR and complex-document comparison,
particularly B-03/B-04 later. It may also serve as one OCR engine underneath a
higher-level Provider such as Docling/RapidOCR routes.

The package's breadth makes a component-level decision important: Raiatea does
not need to adopt the complete ecosystem to reuse OCR/layout/table capabilities.

### Preliminary disposition

**Benchmark first for OCR/VLM/document parsing; reuse components where the
benchmark justifies them.**

## 12. Pandoc and EPUB-specific parsing

> Assertion status: `working-hypothesis`

### Pandoc

Pandoc 3.10.2 (11 Aug 2026) is a mature universal document converter with a
well-defined AST and broad reader/writer support, including EPUB/HTML/Markdown,
DOCX/ODT and many publishing formats.

Primary reference: <https://pandoc.org/releases.html>

Pandoc is highly relevant to **conversion/render/export** and semantic reflow,
but it is not a visual page-layout extractor. Its AST can be a useful
intermediate/adapter input without becoming Raiatea's canonical Source model.

### Direct EPUB package parsing

EPUB is a ZIP/package of XML/HTML/CSS/navigation resources whose reading order
and resource identity are meaningful Source Coordinates. A direct EPUB route can
therefore be thinner and more deterministic than sending every ebook through a
vision/layout model.

EbookLib 0.20 can read/write EPUB2/EPUB3 and exposes package items, but it is
AGPL-3.0. An open 2026 issue reports a path-traversal concern in directory-mode
reading; this is threat evidence that must be assessed before use with untrusted
EPUBs. Marker itself lists EbookLib as its optional EPUB dependency.

Primary references:

- <https://github.com/aerkalov/ebooklib/releases/tag/v0.20>
- <https://github.com/aerkalov/ebooklib>
- <https://github.com/aerkalov/ebooklib/issues/359>

The survey therefore does not preselect EbookLib. It records a **capability
requirement**: parse EPUB container/manifest/spine/navigation/XHTML/resources
without executing active content, preserve stable package-resource coordinates,
and feed content through a standard HTML/XML parser/normalizer. E-03/E-04 can
compare Docling's native EPUB route against a thin specialized route.

### Preliminary disposition

- Pandoc: **reuse/compose** for semantic conversion/export where appropriate.
- EPUB parser: **benchmark Docling native route against a thin specialized
  package parser**; select specific library only after license/security review.

## 13. What the survey does not yet know

The following questions intentionally remain for E-03/E-04:

- Which B-01 route best preserves text, hierarchy, reading order, bbox/coordinates
  and assets on Raiatea fixtures?
- Which B-02 route best preserves EPUB spine/navigation/resource anchors and
  semantics without inventing page coordinates?
- How much manual repair does each route require?
- What are CPU/GPU/RAM/disk/latency costs on representative hardware?
- Which routes fail visibly rather than returning plausible but structurally
  wrong output?
- How stable are Provider outputs across version updates?
- Which model licenses are transitively required by each selected mode?
- Which tools require stronger process/network/filesystem isolation?
- Which Raw Extraction fields should be retained to diagnose Adapter bugs while
  respecting retention policy?

## 14. Candidate benchmark set derived from this survey

> Assertion status: `working-hypothesis`

### B-01 born-digital PDF

Core comparison candidates:

1. Docling native PDF pipeline;
2. Marker 2 `fast`/`balanced` modes as separately recorded routes;
3. MinerU pipeline/hybrid mode as separately recorded routes;
4. Unstructured `fast`/`hi_res` as separately recorded routes;
5. Apache Tika/native text as a broad baseline where Source Coordinate demands
   allow it;
6. PaddleOCR document parsing only where it provides a materially distinct
   layout route.

OCRmyPDF/Tesseract is not a default B-01 route; it is useful for mixed/bad text
subprofiles.

### B-02 EPUB

Core comparison candidates:

1. Docling native EPUB parsing;
2. thin direct EPUB package/spine/XHTML parser + normalizer;
3. Pandoc as a semantic conversion baseline;
4. Marker `[full]` only if its route preserves enough original package/anchor
   evidence to be meaningful.

The comparison should privilege stable package/logical Source Coordinates over
visual-layout sophistication that EPUB does not canonically possess.

### Later classes

- B-03 scanned PDF: OCRmyPDF/Tesseract, PaddleOCR, Docling OCR engines,
  Marker/Surya, MinerU.
- B-04 scholarly PDF: GROBID plus best generalist B-01 routes.
- B-05 photographed/curved page: PaddleOCR, Docling OCR/VLM, Marker/Surya,
  MinerU and preprocessing routes.

## 15. Survey-level conclusions

> Assertion status: `provisional-decision`

1. **Do not build parsing/OCR engines from scratch.** Mature Providers already
   cover the core recognition and parsing functions.
2. **Do build the thin Raiatea layer** for routing, Provider-neutral
   normalization, Source Coordinate mapping, rights/policy enforcement,
   provenance, degradation state and Adapter validation.
3. **No single Provider should own the P0 contract.** Even the broadest tool has
   source-class, model-license or output-model limitations.
4. **Docling is the most important generalist benchmark candidate** because its
   documented hierarchy + bbox + Provenance + EPUB breadth aligns unusually
   well with Raiatea's requirements. This is a benchmark priority, not a win.
5. **Tika is a strong complementary probe/metadata/native extraction tool** and
   should be considered for composition rather than judged only as a full
   document-understanding competitor.
6. **Marker, MinerU and PaddleOCR deserve complex-PDF/OCR benchmarks** but their
   model/runtime/license/deployment characteristics must remain visible.
7. **GROBID should remain specialized** for scholarly material rather than become
   a universal route.
8. **OCRmyPDF/Tesseract should be reused as OCR/PDF tooling**, not mistaken for
   the whole document intelligence layer.
9. **EPUB deserves a direct semantic/package route.** Reflowable sources should
   not be forced through a page-oriented visual model.
10. **Provider-published accuracy/throughput numbers are experiment inputs only.**
    E-04 must measure Raiatea fixtures and dimensions independently.

## 16. Hand-off to the next evidence steps

### E-03 — rights-safe fixtures

Use the candidate route set above to create minimal fixtures that expose:

- B-01 single/multi-column, hierarchy, links, images, tables and selected complex
  structures;
- B-02 multi-resource spine/navigation, links, images, footnotes and stable
  resource anchors;
- malformed/restricted/edge fixtures separately from baseline averages;
- explicit source/fixture rights and redistribution records.

### E-04 — benchmark contract

Measure applicable dimensions separately:

- content fidelity;
- structural/read-order fidelity;
- Source Coordinate fidelity;
- table/figure/formula/code fidelity where present;
- degradation/warning quality;
- manual repair burden;
- latency/resource/cost;
- deterministic/reproducible behavior;
- Adapter complexity and Provider replaceability.

Do not collapse these into one universal score.

## 17. Out of scope

This survey does not:

- select a production Provider;
- approve a model license for a future commercial product;
- implement an Adapter;
- define P0 JSON/API/database schema;
- benchmark numerical quality or speed;
- authorize remote Provider processing;
- choose a sandbox;
- generalize Durex;
- implement Alfred integration;
- implement translation/layout reconstruction;
- promote B-01/B-02 or the first slice to `planned` work.
