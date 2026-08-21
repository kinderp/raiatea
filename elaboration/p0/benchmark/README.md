# P0 benchmark harness

> Evidence-only tooling for E-04.
>
> This directory is **not** the production P0 runtime and its JSON manifests are
> **not** Raiatea's public extraction schema.

This harness materializes deterministic fixture subsets and executes bounded
Provider-neutral benchmark routes for P0 evidence. It intentionally keeps the
fixture/gold contract and route observations separate from the future E-05
production contract.

## Current fixture scope

Generated fixtures:

- `B01-PDF-001` — clean born-digital single-column PDF;
- `B01-PDF-002` — deterministic two-column reading-order PDF;
- `B02-EPUB-001` — multi-resource EPUB spine baseline;
- `B02-EPUB-002` — navigation + cross-resource anchor EPUB;
- `B02-EPUB-NEG-001` — inert scripted-content EPUB;
- `B02-EPUB-NEG-002` — inert unsafe ZIP-member/path EPUB.

The complete accepted E-03 fixture plan remains broader. Missing cases are
listed in `manifests/fixtures.json` under `coverage_gaps`.

## Rights state

Raiatea currently has no explicit repository/fixture redistribution license.
Therefore these project-created fixture definitions are **rights pending**:

- redistribution: `not-established`;
- `public_rights_safe`: `false`;
- external remote Provider: `denied`;
- maintainer decision: issue #131.

Do not describe the generated material as a public rights-safe benchmark corpus
until #131 is resolved and the manifest is updated with actual evidence.

## Generate fixtures

From the repository root:

```bash
python elaboration/p0/benchmark/generate_fixtures.py \
  --output /tmp/raiatea-p0-fixtures
```

The output directory contains generated PDF/EPUB fixtures plus
`generated-manifest.json` with SHA-256 fingerprints and generator metadata.
Generated binaries are intentionally not committed: deterministic source, gold
and generator definitions are the reviewable evidence.

## B-01 PDF control routes

E-04c adds two **Poppler control routes** for born-digital PDF. They establish
cheap deterministic baselines and do not select Poppler as a production
Provider:

- `pdftotext-bbox-layout` — maps Poppler bbox-layout XHTML from top-left points
  into bottom-left PDF points;
- `pdftohtml-xml` — maps Poppler XML from its top-left scaled canvas into
  bottom-left PDF points using physical per-page dimensions from `pdfinfo`.

The second route deliberately never uses `-nodrm` or another access-control
override. If page-size evidence is ambiguous for a multi-page source, coordinate
mapping fails closed rather than assuming all pages share one size.

Run a local B-01 control measurement:

```bash
python elaboration/p0/benchmark/routes/measure_b01.py \
  --output /tmp/raiatea-b01-baseline \
  --evidence-source-commit <exact-code-commit>
```

A dedicated GitHub Actions reference job checks out the exact PR head, installs
`poppler-utils`, runs this command and uploads the complete evidence artifact.
The accepted reference source is commit `0e754bc`; its compact evidence is under:

```text
elaboration/p0/benchmark/evidence/
  b01-reference-ubuntu-poppler-24.02.0/
    b01-baseline.json
    b01-summary.md
```

The source run was GitHub Actions run `32525854079`, artifact `9462154504`,
digest `sha256:6a94fe46b7609fefadcf3ff37c8a425d32264a93cc5e32bc294f99f0f2870d44`.
It measured Poppler 24.02.0 on Ubuntu 24.04 / Python 3.12.14.

On `B01-PDF-002` both controls recover all current reference text and coordinate
regions, but they differ in observed reading order: `pdftotext-bbox-layout`
satisfies 3/4 gold edges whereas `pdftohtml-xml` satisfies 4/4. Hierarchy remains
`not-measured`; font/layout cues are not promoted to semantic structure.

## B-01 Apache Tika structured route

E-04d adds a local, hash-verified **Apache Tika 3.3.2 XHTML route** for the same
born-digital fixtures. It is measured as a structured candidate, not selected as
a production Provider.

The route:

- uses the official `tika-app-3.3.2.jar` and verifies the pinned SHA-512 before
  execution;
- uses Temurin `21.0.12+8` with a pinned Java executable SHA-256 in the reference
  job;
- runs with `tika-pdf-native-no-ocr.xml`, where `PDFParser.ocrStrategy=no_ocr`,
  inline-image extraction is disabled and `TesseractOCRParser` is excluded;
- redirects both `java.io.tmpdir` and PDFBox's `pdfbox.fontcache` under the
  controlled benchmark temporary parent;
- accepts local fixture files only and uses no hosted/API Provider route;
- maps only explicit Tika XHTML semantics/page containers and never fabricates
  source geometry.

Run it locally with a verified Tika jar:

```bash
python elaboration/p0/benchmark/routes/measure_tika_b01.py \
  --output /tmp/raiatea-tika-b01 \
  --tika-jar /path/to/tika-app-3.3.2.jar \
  --config elaboration/p0/benchmark/config/tika-pdf-native-no-ocr.xml \
  --evidence-source-commit <exact-code-commit>
```

The canonical source run is commit `14acf44`; compact evidence is stored under:

```text
elaboration/p0/benchmark/evidence/
  b01-reference-ubuntu-tika-3.3.2/
    tika-baseline.json
    tika-summary.md
```

The source run is GitHub Actions run `32528505169`, artifact `9463033920`,
digest `sha256:4155813b13c67fd3d0334929ebcc81d831fff119de3741dce1dbf2cba99d9d44`.
It measured Tika 3.3.2 on Ubuntu 24.04 / Python 3.12.14 / Temurin 21.0.12+8.

Measured behavior on the current minimal fixtures:

- exact text: `3/3` on B01-PDF-001 and `5/5` on B01-PDF-002;
- reading order: `2/2` and `4/4` respectively;
- explicit `div.page` preserves page identity;
- no bbox/source geometry is exposed by the measured XHTML, so coordinates are
  `not-measured`, not scored as failure or success;
- the visual title is emitted as `<p>`, yielding explicit hierarchy mismatches
  (`2/3` and `4/5` exact semantic types) rather than a typography-based guess;
- 20 metadata keys are visible in each current fixture;
- PDFBox creates `.pdfbox.cache`, but it is redirected to the controlled
  `pdfbox-font-cache/` root; no unexpected files were observed under the
  controlled parent.

Compared with the current Poppler controls, Tika adds explicit page containers,
metadata and explicit paragraph semantics, while Poppler remains stronger for
source geometry. On B01-PDF-002, Tika's current reading order is `4/4`, matching
`pdftohtml-xml` and differing from `pdftotext-bbox-layout` (`3/4`). This is a
per-dimension observation, **not** a total Provider ranking.

Docling and the other structured candidates remain unmeasured by this evidence
step; absence/setup state must not be converted into extraction-quality evidence.

## B-02 baseline routes

E-04b adds two benchmark-only local routes:

- `direct-epub-stdlib` — safe in-memory EPUB package parsing with Python
  `zipfile` + `ElementTree`; validates archive paths before semantic parsing and
  never extracts archive members;
- `pandoc-epub` — invokes a local Pandoc executable with `--sandbox`, using a
  controlled temporary input/work parent, captures exact executable/version/hash,
  raw-output fingerprint, stderr, duration and observable file side effects, then
  maps Pandoc JSON into Provider-neutral benchmark observations.

Run a local B-02 measurement from the repository root:

```bash
python elaboration/p0/benchmark/routes/measure_b02.py \
  --output /tmp/raiatea-b02-baseline \
  --evidence-source-commit <exact-code-commit>
```

Pandoc is optional for the unit-test core. If it is unavailable, its route is
recorded as `not-measured` rather than making the benchmark harness fail.

The reference-environment evidence produced from code commit `1fabcd1` is stored
under:

```text
elaboration/p0/benchmark/evidence/
  b02-reference-linux-pandoc-3.1.11.1/
    b02-baseline.json
    b02-summary.md
```

That record is deliberately scoped to Linux x86_64 / Python 3.13.5 / Pandoc
3.1.11.1. E-02 surveyed Pandoc 3.10.2, so the recorded version mismatch is an
explicit route-selection blocker until a current accepted version is remeasured.
The baseline also remains incomplete for the wider B-02 class.

Negative/security fixture results are never folded into normal quality results.
Security properties that the harness cannot prove remain `partial` or
`not-measured`; `--sandbox` and absence of observed side effects are not promoted
to claims of OS-level filesystem or network isolation.

## Test

```bash
python -m unittest discover \
  -s elaboration/p0/benchmark/tests \
  -v
```

Tests cover:

- benchmark-only contract markers;
- fail-closed rights state;
- deterministic regeneration;
- valid basic PDF structure;
- B-01 Poppler XML/XHTML mappings and top-left → bottom-left coordinate conversion;
- fail-closed multi-page page-size handling;
- no Poppler DRM/access-control override;
- B-01 text/reading-order/coordinate scoring and ambiguous duplicate-text handling;
- structured B-01 scoring where missing geometry remains `not-measured`/`partial`;
- Tika no-OCR configuration, jar verification and conservative XHTML mapping;
- Tika Java/PDFBox runtime filesystem confinement across Linux/Windows path semantics;
- Tika summary/evidence retention of Java hash, controlled cache and semantic limits;
- EPUB `mimetype`/container/OPF/nav structure;
- EPUB no-canonical-page gold invariant;
- cross-resource anchors;
- inert active content;
- unsafe ZIP paths and output confinement;
- generated fingerprints and rights propagation;
- direct EPUB route structure/fragment preservation;
- active-content warning and unsafe-member rejection;
- Pandoc JSON mapping/resource-anchor degradation;
- Pandoc `--sandbox` + controlled-input invocation;
- Provider-neutral B-02 scoring and explicit partial/not-measured negative states;
- dynamic report metadata so reruns cannot inherit stale hard-coded Provider
  versions.

The `P0 benchmark harness` workflow runs the dependency-light contract tests on
Linux and Windows. Provider-specific reference jobs are separate and must pin the
exact source commit/environment used to generate evidence.

`pdfinfo` and `unzip` may be used as optional manual diagnostics but are not
requirements of the dependency-light test matrix.

## Contract boundary

`manifests/fixtures.json`, `manifests/gold.json`, route observations and result
records are internal benchmark contracts, versioned independently from E-05.
They may evolve to support scoring and Provider-output alignment.

They must not be imported by production code as a shortcut for defining:

- `Source`;
- `Normalized Representation`;
- `Processing Run`;
- Provider Adapter APIs;
- the future P0 public JSON/API/database model.

No benchmark record in this directory selects a Provider or promotes the
candidate first slice.
