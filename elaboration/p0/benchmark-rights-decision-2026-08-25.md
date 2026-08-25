# P0 benchmark redistribution-rights decision — 25 August 2026

> Status: **maintainer decision / G-02 evidence**  
> Decision issue: [#131](https://github.com/kinderp/raiatea/issues/131)  
> Parent rights manifest: [`benchmark-rights-manifest.md`](benchmark-rights-manifest.md)  
> Current machine-readable overlay: [`benchmark/manifests/redistribution-rights.json`](benchmark/manifests/redistribution-rights.json)

## Decision

The maintainer selected the following benchmark-scoped licensing model:

- eligible project-created/generated fixture content, generated fixture documents, fixture metadata and gold/reference data: **CC BY 4.0**;
- bounded fixture-generator source code identified by the benchmark licensing record: **Apache-2.0**;
- remote/hosted Provider processing remains outside this decision and remains denied/not authorized until separate Processing Rights and Provider-policy evidence exists;
- this decision does not license or relicense Raiatea as a whole.

The human-readable policy and required attribution are recorded in [`benchmark/LICENSING.md`](benchmark/LICENSING.md) and [`benchmark/NOTICE.md`](benchmark/NOTICE.md).

## Why an overlay instead of rewriting historical manifests

E-04 benchmark evidence pins hashes of its measurement-era inputs. Several historical manifest records therefore still contain the then-correct state:

```text
redistribution = not-established
public_rights_safe = false
```

Those values are retained as historical evidence rather than silently rewritten after measurements have been accepted.

`benchmark/manifests/redistribution-rights.json` is the **current authoritative redistribution-rights overlay**. It supersedes the historical inline rights fields for current redistribution policy while preserving benchmark provenance and reproducibility.

This distinction is intentional:

```text
historical manifest state != current redistribution policy
```

## Current eligible material

The overlay records current CC BY 4.0 redistribution status for the project-created B-01/B-02 fixture set through:

- B01-PDF-001..007;
- B01-PDF-NEG-001/002;
- B02-EPUB-001/002;
- B02-EPUB-NEG-001/002;
- project-authored fixture metadata and gold/reference assertions covered by the overlay.

Every listed fixture has:

- explicit origin basis;
- `redistribution = CC-BY-4.0`;
- `public_rights_safe = true` for redistribution;
- attribution required;
- remote Provider state kept separately at `denied`.

Third-party Provider raw outputs, tools, models, libraries, fonts, private corpus material and unrelated measured evidence are not swept into CC BY by this decision.

## Generator code

Apache-2.0 applies only to the exact generator paths named in the overlay and `benchmark/LICENSING.md`:

- `benchmark/generate_fixtures.py`;
- `benchmark/b01_pdf_007_fixture.py`;
- `benchmark/b01_pdf_negative_fixtures.py`.

The generator source files themselves are not rewritten merely to insert licensing comments because their source fingerprints participate in historical benchmark evidence. The scoped license declaration is therefore carried by the adjacent benchmark licensing/NOTICE metadata.

## G-02 consequence

This decision resolves the previously missing **Redistribution Rights** evidence for the eligible project-created benchmark fixture/gold baseline.

It does **not** collapse the other rights dimensions:

```text
Processing Authority
Processing Rights
Redistribution Rights
Provider data-policy eligibility
Retention Policy
```

Therefore G-02 may become `satisfied-with-bounded-scope` only if the accompanying regression tests and documentation verify that:

1. the current rights overlay is explicit and complete for the bounded fixture set;
2. CC BY attribution remains visible;
3. Apache applies only to the declared generator code;
4. repository-wide licensing is not implied;
5. third-party/private material remains excluded;
6. remote Provider authorization remains separate and denied by this decision;
7. historical benchmark inputs remain reproducible.

## Residual boundary

This is a licensing/redistribution decision, not legal advice and not a general legal review of every future benchmark source. Any future fixture with third-party material must establish its own compatible rights evidence before it can inherit a public-rights-safe state.
