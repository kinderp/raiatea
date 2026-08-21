# P0 benchmark harness

> Evidence-only tooling for E-04.
>
> This directory is **not** the production P0 runtime and its JSON manifests are
> **not** Raiatea's public extraction schema.

This harness materializes the minimal deterministic fixture subset tracked by
issue #130. It intentionally uses the Python standard library so the benchmark
infrastructure does not preselect an extraction Provider.

## Current scope

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

## Generate

From the repository root:

```bash
python elaboration/p0/benchmark/generate_fixtures.py \
  --output /tmp/raiatea-p0-fixtures
```

The output directory contains generated PDF/EPUB fixtures plus
`generated-manifest.json` with SHA-256 fingerprints and generator metadata.

Generated binaries are intentionally not committed: the deterministic source,
gold and generator are the reviewable evidence in this micro-step.

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
- unsafe ZIP path retained as test data without extraction;
- generated fingerprints and rights propagation.

`pdfinfo` and `unzip` may be used as optional manual diagnostics but are not test
dependencies.

## Contract boundary

`manifests/fixtures.json` and `manifests/gold.json` are internal benchmark
contracts, versioned independently from E-05. They may evolve to support scoring
and Provider-output alignment.

They must not be imported by production code as a shortcut for defining:

- `Source`;
- `Normalized Representation`;
- `Processing Run`;
- Provider Adapter APIs;
- the future P0 public JSON/API/database model.
