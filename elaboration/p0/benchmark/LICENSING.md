# Raiatea P0 benchmark licensing

> Maintainer decision: issue #131  
> Decision date: 25 August 2026  
> Scope: **benchmark-only** — this file does not license the Raiatea repository as a whole.

## Decision

The maintainer selected the following split licensing model for the project-created P0 benchmark material:

| Material | License |
| --- | --- |
| Eligible project-created/generated benchmark fixture content and generated fixture documents | **Creative Commons Attribution 4.0 International — CC BY 4.0** |
| Gold/reference data and benchmark fixture/gold manifest data | **Creative Commons Attribution 4.0 International — CC BY 4.0** |
| Fixture-generator source code listed below | **Apache License 2.0 — Apache-2.0** |

This decision is intentionally narrower than a repository-wide licensing decision.

## CC BY 4.0 material

CC BY 4.0 applies to the project-created material identified by the benchmark rights evidence as eligible for public redistribution, including:

- generated B-01/B-02 fixture document content and generated fixture files produced from the project-owned generators;
- `manifests/fixtures.json` as benchmark fixture metadata;
- `manifests/gold.json` as gold/reference data;
- project-created fixture/gold values explicitly covered by the current redistribution-rights overlay.

License identifier: `CC-BY-4.0`  
License information and legal code: <https://creativecommons.org/licenses/by/4.0/>

### Required attribution

A reasonable attribution for redistributed or adapted benchmark fixture/gold material is:

> **Raiatea P0 Benchmark — Raiatea project contributors**  
> Source: <https://github.com/kinderp/raiatea/tree/main/elaboration/p0/benchmark>  
> Licensed under **CC BY 4.0**.

When material is modified, the redistributor must also indicate that changes were made, as required by CC BY 4.0.

CC BY 4.0 permits copying, redistribution, adaptation and commercial use subject to its attribution and related license conditions. It does not grant trademark rights and it does not relicense third-party material.

## Apache-2.0 fixture-generator code

Apache-2.0 applies only to these fixture-generator source files unless a later reviewed decision explicitly adds another path:

- `generate_fixtures.py`;
- `b01_pdf_007_fixture.py`;
- `b01_pdf_negative_fixtures.py`.

License identifier: `Apache-2.0`  
Canonical license information: <https://www.apache.org/licenses/LICENSE-2.0>

The scoped licensing declaration applies to those exact paths. This licensing-only decision intentionally does **not** rewrite historically benchmark-pinned generator source files merely to add SPDX comment headers, because changing those files would change source fingerprints recorded by existing benchmark evidence without changing generator behavior.

Redistribution of the generator code must comply with Apache-2.0, including providing recipients a copy of the Apache License 2.0, preserving applicable notices and marking modified files where required. `NOTICE.md` records this packaging requirement and points to the canonical license text.

## Explicit exclusions

This benchmark-scoped decision does **not** by itself license or relicense:

- Raiatea Core or the future product implementation;
- the Plugin API/runtime implementation outside the generator files listed above;
- benchmark Provider routes, scorers, test code, workflow code, configuration, locks or measured evidence unless a separate file-level or later reviewed license says otherwise;
- Alfred, Durex, TheBitLab, FARO or any other project/repository;
- third-party libraries, tools, fonts, models, Provider outputs or other third-party assets;
- private/non-distributable exploratory corpus material;
- the Raiatea name, logos or other trademarks.

All excluded material retains whatever rights status independently applies to it.

## Rights and remote-processing boundary

This licensing decision establishes **Redistribution Rights** for the eligible project-created fixture/gold material. It does not collapse the other E-01 rights dimensions:

```text
Redistribution Rights != Processing Rights != Provider data-policy eligibility
```

In particular, externally hosted/remote Provider routes remain **not authorized by this decision**. Remote processing still requires the separate Provider-policy and Processing Rights evidence defined by E-01/E-02.

## Third-party/transitive material

CC BY 4.0 applies only where Raiatea has the rights needed to license the material. Any future fixture containing third-party content must retain a separate compatible rights record; committing it under this directory does not automatically make it CC BY 4.0.

The access-controlled negative fixture may use `qpdf` as a generation tool, but this decision licenses Raiatea's project-created fixture content/output, not qpdf itself.

## Verification and historical evidence

Current machine-readable redistribution policy is `manifests/redistribution-rights.json`. The licensing regression suite is `tests/test_benchmark_licensing.py`; it verifies the CC BY/Apache split, exact generator-file scope, attribution requirement, remote denial and explicit exclusions.

Historical E-04 manifests that were hash-pinned at measurement time are not rewritten merely to replace their then-correct `not-established` fields. The current rights overlay explicitly supersedes those historical fields for present redistribution policy while preserving their provenance value.

## Change control

The license grant for material already released under CC BY 4.0 or Apache-2.0 cannot be retroactively withdrawn from recipients who received it under those terms. Future material may use different terms only through a new explicit maintainer decision with updated manifest evidence.
