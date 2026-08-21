# P0 Provider Maintenance and Compatibility Snapshot

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 1.0.0
>
> Accepted through: [PR #126](https://github.com/kinderp/raiatea/pull/126)
>
> Observation date: **21 August 2026**
>
> Parent issue: [#125](https://github.com/kinderp/raiatea/issues/125)
>
> Version evidence: [`provider-evidence-snapshot.md`](provider-evidence-snapshot.md)

## 1. Purpose

Issue #125 requires E-02 to compare project maturity, maintenance/release cadence
and compatibility surface as architecture inputs. This artifact records
**observable maintenance/compatibility signals** without inventing a universal
“maturity score”.

A recent release does not prove quality. A slow cadence does not prove
abandonment. These signals matter because they affect:

- environment/version pinning;
- Adapter compatibility burden;
- model/runtime drift;
- re-benchmark triggers;
- packaging/support cost;
- security-update expectations.

## 2. Reading rules

The table below distinguishes:

- **observed release signal** — factual evidence from the project's primary
  release/documentation history at the observation date;
- **compatibility surface** — interfaces/runtime families a Raiatea Adapter must
  isolate or pin;
- **E-02 implication** — Raiatea's architecture assessment, not a Provider claim.

Each release/cadence claim links directly to primary project evidence. The
immutable baseline for the exact E-02 version remains
[`provider-evidence-snapshot.md`](provider-evidence-snapshot.md); release-history
links are observation evidence for cadence/transition context.

No row means “safe”, “stable” or “production-ready” without E-04 evidence.

## 3. Maintenance / compatibility signals

| Candidate | Observed release signal | Primary evidence | Compatibility surface relevant to P0 | E-02 implication |
| --- | --- | --- | --- | --- |
| Docling | `v2.117.0` 30 Jul 2026; release history also shows `v2.116.0` 29 Jul and `v2.115.0` 23 Jul | [official GitHub releases](https://github.com/docling-project/docling/releases), [v2.117.0](https://github.com/docling-project/docling/releases/tag/v2.117.0) | Python package/CLI, `DoclingDocument`, OCR/model packages, optional service/client, model revisions | **High version-motion signal.** Pin package + model/backend and expect re-benchmark on material pipeline/model changes. Adapter must hide `DoclingDocument` version drift from P0 contract. |
| Marker | major `v2.0.0` 20 Jul 2026 | [v2.0.0 release](https://github.com/datalab-to/marker/releases/tag/v2.0.0), [tagged README](https://github.com/datalab-to/marker/blob/v2.0.0/README.md) | Python/PyTorch, Marker JSON/renderers, Surya VLM, vLLM/`llama.cpp` inference server, optional LLM providers | **Major-transition signal.** Benchmark exact `fast`/`balanced` route and model/runtime revision; do not assume v1/v2 output/runtime compatibility. |
| MinerU | `3.4.4` release workflow/tag 10 Jul 2026; adjacent 3.4.x release activity is visible in project release history | [official releases](https://github.com/opendatalab/MinerU/releases), [3.4.4 release workflow](https://github.com/opendatalab/MinerU/actions/runs/29090728963), [release commit `0dfc946`](https://github.com/opendatalab/MinerU/commit/0dfc946) | CLI/API, pipeline/VLM/hybrid backends, model packages, optional MLX/vLLM/server routes, middle/model JSON | **Fast backend/model evolution signal.** Route identity must include backend/model, not just `mineru==3.4.4`; re-benchmark on backend/model changes. |
| Unstructured | `0.25.0` 31 Jul 2026; `0.24.1` 11 Jul and `0.24.0` 6 Jul 2026 visible in release history | [official GitHub releases](https://github.com/Unstructured-IO/unstructured/releases), [0.25.0 release](https://github.com/Unstructured-IO/unstructured/releases/tag/0.25.0) | partition API, `Element`/metadata model, strategy names (`fast`/`ocr_only`/`hi_res`), inference/model package, optional hosted platform | **Fast release cadence.** Pin partition + inference components together; Adapter should isolate Element/metadata evolution and strategy behavior. |
| Apache Tika | stable `3.3.2` 16 Jul 2026; `4.0.0-beta-1` preview line observed separately | [official 3.3.2 release](https://tika.apache.org/3.3.2/), [official downloads/releases](https://tika.apache.org/download) | Java parser API, `tika-app`, `tika-server`, parser/dependency bundle, major-version line | **Stable+preview split.** Use 3.3.2 as E-02 stable baseline; do not mix Tika 4 preview behavior into measurements. Re-test when crossing major line. |
| GROBID | stable `0.9.0` 7 Apr 2026; repository docs describe `0.9.1-SNAPSHOT` as current development | [0.9.0 release](https://github.com/grobidOrg/grobid/releases/tag/0.9.0), [installation/current-development docs](https://github.com/grobidOrg/grobid/blob/master/doc/Install-Grobid.md) | Java 21/Gradle 9, service/TEI contract, pdfalto, optional DeLFT/TensorFlow, optional Crossref/glutton consolidation | **Specialist stable-line signal with material runtime changes at 0.9.0.** Pin TEI/service/runtime stack and keep network consolidation disabled unless separately policy-qualified. |
| OCRmyPDF | `v17.10.0` 5 Aug 2026; release list includes multiple 17.x releases in Jul/Aug 2026 | [official GitHub releases](https://github.com/ocrmypdf/OCRmyPDF/releases), [v17.10.0](https://github.com/ocrmypdf/OCRmyPDF/releases/tag/v17.10.0) | Python API/CLI, pikepdf/qpdf/Ghostscript/Tesseract, PDF/A/output behavior, Docker image | **Active 17.x maintenance signal.** Pin external binary versions as part of route identity; behavior can change with Ghostscript/Tesseract as well as OCRmyPDF. |
| Tesseract | `5.5.3` 24 Jul 2026 | [official GitHub releases](https://github.com/tesseract-ocr/tesseract/releases), [5.5.3](https://github.com/tesseract-ocr/tesseract/releases/tag/5.5.3) | native OCR library/CLI, language `traineddata`, output format options | **Long-lived but model-data-sensitive surface.** Pin engine plus language data revision; do not equate engine version with traineddata version. |
| PaddleOCR | `v3.7.0` 11 Jun 2026, introducing PP-OCRv6; release page notes multiple model tiers and runtime/model changes | [v3.7.0 release](https://github.com/PaddlePaddle/PaddleOCR/releases/tag/v3.7.0), [tagged pyproject](https://github.com/PaddlePaddle/PaddleOCR/blob/v3.7.0/pyproject.toml) | PaddleOCR package, PaddleX dependency range, OCR/layout/VL models, acceleration runtimes, optional document parser/gen-AI clients | **Model/runtime-motion signal.** Route identity must pin package + PaddleX + model revision/backend; package version alone is insufficient. |
| Pandoc | `3.10.2` 11 Aug 2026; `3.10.1` 21 Jul and `3.10` 3 Jun 2026 | [official release history](https://pandoc.org/releases.html) | CLI/library AST, readers/writers, bundled/default templates, extensions | **Active semantic-converter cadence.** Pin Pandoc version for B-02 baseline because readers/writers/extensions can change source normalization. |
| EbookLib | `v0.20` is the latest release; project README states v0.20 is the final Python 2.7-supporting version and that the project is being refreshed for modern Python | [v0.20 release](https://github.com/aerkalov/ebooklib/releases/tag/v0.20), [project README](https://github.com/aerkalov/ebooklib) | Python API, ZIP/package handling, HTML/XML objects, EPUB2/EPUB3 reader/writer behavior | **Transition/modernization signal.** Do not make it a neutral-core dependency without license/security review; a direct EPUB Adapter should isolate whichever package library is chosen. |

## 4. Compatibility categories that E-04 must pin

Regardless of Provider, benchmark execution manifests should treat these as
separate compatibility dimensions when applicable:

1. **Provider package version** — e.g. Docling/Marker/MinerU version.
2. **model revision** — OCR/layout/VLM/model weights.
3. **backend/mode** — e.g. Marker fast vs balanced, MinerU pipeline vs hybrid.
4. **runtime framework** — PyTorch/Paddle/MLX/vLLM/llama.cpp/Java runtime.
5. **external binaries** — Ghostscript/qpdf/Tesseract/pdfalto/LibreOffice.
6. **language/model data** — Tesseract traineddata or equivalent assets.
7. **Provider-native output contract** — DoclingDocument/JSON, Marker JSON,
   MinerU intermediates, Unstructured Elements, GROBID TEI.
8. **service/API protocol** when a self-hosted process boundary is used.

A change in one dimension may require only an Adapter compatibility check or may
require a full source-class re-benchmark. E-04 should record that distinction
rather than treating “same Provider name” as reproducibility.

## 5. Re-benchmark trigger hypothesis

> Assertion status: `working-hypothesis`

A future route should be considered for re-benchmark when one of these changes
materially:

- major/minor Provider pipeline version affecting parsing/layout/output;
- OCR/layout/VLM model family or revision;
- backend/mode used for the route;
- Source Coordinate semantics;
- output schema/element model;
- major runtime/dependency version known to affect results;
- security/isolation boundary;
- license/data-policy constraints that change route eligibility.

Patch releases that provably do not affect the relevant route may need only a
compatibility regression run. The actual policy belongs to E-04/E-05 after
measured evidence exists.

## 6. What this snapshot does not claim

This document does not:

- rank projects by popularity;
- infer quality from stars/downloads;
- equate fast release cadence with instability;
- equate slow cadence with abandonment;
- guarantee semantic-versioning compatibility;
- define supported version ranges for Raiatea;
- select a Provider;
- replace dependency/security monitoring after implementation.
