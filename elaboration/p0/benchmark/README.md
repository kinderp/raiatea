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

The dedicated `P0 benchmark harness` GitHub Actions matrix runs on Linux and
Windows with supported Python versions. It does not install external Providers,
so external-route measurements remain explicit reference-environment evidence.

`pdfinfo` and `unzip` may be used as optional manual diagnostics but are not test
dependencies.

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
