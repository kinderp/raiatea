# P0 Provider Evidence Snapshot

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Observation date: **21 August 2026**
>
> Parent issue: [#125](https://github.com/kinderp/raiatea/issues/125)
>
> Survey: [`technology-survey.md`](technology-survey.md)
>
> Matrix: [`provider-matrix.md`](provider-matrix.md)

## 1. Purpose

This file is the **reproducible evidence index** for rapidly changing Provider
claims in E-02. The narrative survey may include convenient links to a project's
current documentation, but version-sensitive claims used for acceptance must be
traceable to an immutable release tag, commit, or stable official release
artifact listed here.

This snapshot records documented state only. It does not mean Raiatea has
installed, tested, benchmarked, security-reviewed or license-approved a route.

## 2. Evidence rules

1. A release/tag/commit reference is authoritative for **what E-02 observed**.
2. A mutable `main`/`master` link is supplementary only.
3. Code license, model-weight license, hosted-service terms and dependency
   licenses are separate evidence classes.
4. Provider self-benchmarks remain Provider claims even when pinned.
5. A release can be current on the observation date and later become outdated;
   E-04 must pin the exact version it executes.
6. Current security issues/provider policies that are not repository-versioned
   must retain observation date and are not promoted to immutable software
   behavior.

## 3. Pinned Provider baseline

| Candidate | E-02 version | Immutable/stable baseline evidence | Version-sensitive supporting evidence |
| --- | --- | --- | --- |
| Docling | `v2.117.0` | [release tag](https://github.com/docling-project/docling/releases/tag/v2.117.0), release commit `f2683c0` | [tagged package metadata](https://github.com/docling-project/docling/blob/v2.117.0/packages/docling/pyproject.toml), [tagged supported-formats docs](https://github.com/docling-project/docling/blob/v2.117.0/docs/usage/supported_formats.md) |
| Marker | `v2.0.0` | [release tag](https://github.com/datalab-to/marker/releases/tag/v2.0.0), release commit `947d768` | [tagged README](https://github.com/datalab-to/marker/blob/v2.0.0/README.md), [tagged pyproject](https://github.com/datalab-to/marker/blob/v2.0.0/pyproject.toml) |
| MinerU | `3.4.4` | release workflow/tag `mineru-3.4.4-released` at commit [`0dfc946`](https://github.com/opendatalab/MinerU/commit/0dfc946) | [license at release commit](https://github.com/opendatalab/MinerU/blob/0dfc946/LICENSE.md), [pyproject at release commit](https://github.com/opendatalab/MinerU/blob/0dfc946/pyproject.toml) |
| Unstructured | `0.25.0` | [release tag](https://github.com/Unstructured-IO/unstructured/releases/tag/0.25.0), release commit `c38745b` | [license at tag](https://github.com/Unstructured-IO/unstructured/blob/0.25.0/LICENSE.md), [PDF partitioner at tag](https://github.com/Unstructured-IO/unstructured/blob/0.25.0/unstructured/partition/pdf.py) |
| Apache Tika | `3.3.2` | [official 3.3.2 release page](https://tika.apache.org/3.3.2/), [official download page](https://tika.apache.org/download) | Apache project release documentation is the stable baseline; `4.0.0-beta-1` is not used as E-02 stable baseline |
| GROBID | `0.9.0` | [release tag](https://github.com/grobidOrg/grobid/releases/tag/0.9.0) | [install documentation at tag](https://github.com/grobidOrg/grobid/blob/0.9.0/doc/Install-Grobid.md), [license at tag](https://github.com/grobidOrg/grobid/blob/0.9.0/LICENSE) |
| OCRmyPDF | `17.10.0` | [release tag](https://github.com/ocrmypdf/OCRmyPDF/releases/tag/v17.10.0), [PyPI 17.10.0](https://pypi.org/project/ocrmypdf/17.10.0/) | [documentation](https://ocrmypdf.readthedocs.io/) is supplementary unless a version-specific page is cited |
| Tesseract | `5.5.3` | [release tag](https://github.com/tesseract-ocr/tesseract/releases/tag/5.5.3), release commit `db0ec62` | [license at tag](https://github.com/tesseract-ocr/tesseract/blob/5.5.3/LICENSE) |
| PaddleOCR | `v3.7.0` | [release tag](https://github.com/PaddlePaddle/PaddleOCR/releases/tag/v3.7.0), release commit `b03f464` | [tagged pyproject](https://github.com/PaddlePaddle/PaddleOCR/blob/v3.7.0/pyproject.toml) |
| Pandoc | `3.10.2` | [official release history](https://pandoc.org/releases.html#pandoc-3102-2026-08-11) | [official User Guide license statement](https://pandoc.org/MANUAL.html#authors) states GPL version 2 or greater; a packaging decision must still review the exact distributed artifact/dependencies |
| EbookLib | `v0.20` | [release tag](https://github.com/aerkalov/ebooklib/releases/tag/v0.20) | [license at tag](https://github.com/aerkalov/ebooklib/blob/v0.20/LICENSE.txt); current security issue evidence is time-scoped separately below |

## 4. Pinned findings that materially affect E-02 interpretation

### Marker 2 code versus model-weight license

At `v2.0.0` the tagged `pyproject.toml` declares Apache-2.0 for the code, while
the tagged README states that model weights use a modified AI Pubs Open Rail-M
license with separate commercial conditions. E-02 therefore treats code and
weights as separate license evidence and does not call “Marker” as a whole
license-neutral.

### MinerU custom license

MinerU 3.4.4 is pinned to commit `0dfc946`. `LICENSE.md` at that commit is the
MinerU Open Source License rather than unmodified Apache-2.0. The survey's
commercial-threshold/online-service-attribution notes must be read against that
pinned license, not a future `master` revision.

### Unstructured 0.25.0

The release page identifies tag `0.25.0` at commit `c38745b`; the tag license is
Apache-2.0. Hosted-platform data policy is **not** accepted by this snapshot and
remains outside E-04 eligibility until a separate current remote-route evidence
record exists.

### PaddleOCR 3.7.0

The tagged release `v3.7.0` is dated 11 June 2026 and identifies commit
`b03f464`. The tagged `pyproject.toml` declares Apache License 2.0 for the Python
package and lists document parsing/translation-related optional dependencies.
This does not automatically establish licenses for every downloaded model or
external runtime.

### Pandoc

The official release history identifies 3.10.2 on 11 August 2026. The official
User Guide states GPL version 2 or greater. E-02 therefore uses that wording
rather than an inferred SPDX variant as the authoritative survey statement.

## 5. Current, non-immutable risk observations

Some useful facts are current-state observations rather than release contents.
They are allowed only with their observation date and do not redefine the pinned
software release.

- **Marker macOS:** issue
  [#1065](https://github.com/datalab-to/marker/issues/1065), opened 21 July 2026,
  reports Marker 2.0.0 failing on a clean macOS installation when a required
  external `llama-server` binary is absent. E-02 uses this only as installation
  risk evidence to reproduce/resolve during benchmark setup.
- **EbookLib:** issue
  [#359](https://github.com/aerkalov/ebooklib/issues/359), observed 21 August
  2026, reports a path-traversal concern in directory-mode reading. E-02 uses
  this as threat-review evidence and does not claim a fixed/unfixed state without
  re-checking the issue at implementation time.

## 6. Remote Provider evidence boundary

This snapshot intentionally does **not** attempt to freeze data-policy terms for
Marker/Datalab hosted APIs, Unstructured hosted platform, Paddle-related remote
services or another external hosted route.

Therefore:

```text
hosted service existence
    != remote route eligibility
```

All externally hosted routes remain outside E-04 until a dedicated current
Provider-policy snapshot covers the E-01-required attributes and the rights/
sensitivity route policy explicitly permits that route.

## 7. Hand-off to E-03/E-04

Before a benchmark run, record an execution manifest containing at least:

- Provider/tool version or immutable commit;
- model/backend identifier and revision where relevant;
- code/model license evidence used for that route;
- local/self-hosted versus external remote boundary;
- dependency/environment lock information sufficient to reproduce the route;
- fixture identifier/version;
- material route parameters.

E-04 measurements must not silently reuse the generic E-02 version if the
executed route has moved to a newer release.
