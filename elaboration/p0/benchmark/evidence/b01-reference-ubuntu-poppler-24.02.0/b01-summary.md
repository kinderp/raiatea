# B-01 PDF Poppler control baseline

> Benchmark control evidence only. Poppler is not selected as the production Provider.
>
> Evidence source code: `0e754bc99d4a4b58b736ed768ef61491d1ffc7c1`.
>
> GitHub Actions run: `32525854079`; artifact `9462154504`, digest `sha256:6a94fe46b7609fefadcf3ff37c8a425d32264a93cc5e32bc294f99f0f2870d44`.
>
> The fixture/gold redistribution gate remains open in issue #131.

## Reference environment

- GitHub Actions runner: Ubuntu 24.04
- Kernel: `6.17.0-1022-azure`
- Architecture: `x86_64`
- Python: `3.12.14`
- CPU: `AMD EPYC 9V74 80-Core Processor` (4 logical CPUs exposed to the run)
- Memory observed: `16373452 kB`
- GPU: not instrumented
- Portability claim: **none**; results apply only to the recorded route/version/environment and fixture subset.

## Measured control routes

### `pdftotext-bbox-layout`

- Poppler version: `24.02.0`
- executable: `/usr/bin/pdftotext`
- executable SHA-256: `0fb98ea179e19154a90202608c164f2a319b79f16576fa6534b2d601033565e7`
- route options: `-bbox-layout`
- native coordinates: top-left points
- mapped coordinates: bottom-left PDF points using page height

### `pdftohtml-xml`

- Poppler version: `24.02.0`
- executable: `/usr/bin/pdftohtml`
- executable SHA-256: `70bd5fbb655a14d0b02cb32cb53a601d3b0842a63553a24d1a6a612cf9f0624e`
- `pdfinfo`: `24.02.0`, SHA-256 `3293dda06d80e1e38dab859aa47368c2876aedc41cbc2e24e8fb9a4e66392078`
- route options: `-xml -hidden -q`
- **no `-nodrm` or access-control override is used**
- native coordinates: top-left scaled canvas
- mapped coordinates: bottom-left PDF points using per-axis scale derived from `pdfinfo` physical page dimensions

## B01-PDF-001 — single-column control

Both controls preserve all current measurable dimensions:

| Dimension | pdftotext bbox-layout | pdftohtml XML |
| --- | ---: | ---: |
| Exact reference text | 3/3 | 3/3 |
| Coordinate boxes contained in gold regions | 3/3 | 3/3 |
| Reading-order edges | 2/2 | 2/2 |
| Hierarchy | not measured | not measured |

Hierarchy is deliberately not inferred from font size or visual cues in these control routes.

## B01-PDF-002 — two-column reading order

Both controls recover all reference text and all current coordinate regions, but their observed text sequence differs:

### `pdftotext-bbox-layout`

Observed reference sequence:

```text
title → left1 → right1 → left2 → right2
```

Results:

- exact reference text: `5/5`;
- coordinate containment: `5/5`;
- reading-order edges: `3/4`;
- failed edge: `left2 → right1`;
- hierarchy: `not-measured`.

### `pdftohtml-xml`

Observed reference sequence:

```text
title → left1 → left2 → right1 → right2
```

Results:

- exact reference text: `5/5`;
- coordinate containment: `5/5`;
- reading-order edges: `4/4`;
- hierarchy: `not-measured`.

This is useful control evidence: even two tools from the same Poppler ecosystem can expose meaningfully different reading-order behavior, so routing and normalization cannot rely on a Provider brand name alone.

## Coordinate measurement boundary

The current E-03 gold uses broad source regions in bottom-left PDF points. E-04c compares:

1. exact page index; and
2. strict containment of the observed tight text bbox inside the broad gold region.

No universal IoU threshold is introduced. Content fidelity and coordinate fidelity remain separate.

For future multi-page PDFs, the `pdftohtml` mapper refuses to reuse a single generic `pdfinfo Page size` across all pages when per-page sizes are unavailable; it fails closed rather than assuming equal dimensions.

## Structured Provider setup status

This child does **not** turn control-route availability into a Provider decision.

- Apache Tika: E-02 surveyed `3.3.2`; `not-measured` in this run. E-02 release/hash evidence is merely carried forward and was not reverified by this benchmark execution. No Tika artifact was installed/materialized for this run, therefore no quality conclusion exists.
- Docling: E-02 surveyed `2.117.0`; Python module not available in this reference runner; `not-measured`, no quality conclusion.

A later E-04 child must materialize structured generalist routes reproducibly before they can be compared with these controls.

## Rights and decision boundary

- fixture/gold redistribution: `not-established` pending #131;
- `public_rights_safe=false`;
- external remote Provider: denied;
- `provider_selected=false`;
- `first_slice_promoted=false`;
- `G-02=false`, `G-04=false`, `G-05=false`.

## Coverage gaps

The current B-01 evidence does **not** cover the full accepted class. Remaining gaps include:

- headings/lists/links;
- figures/captions;
- tables;
- formula/code;
- defective native-text subprofile;
- malformed/access-controlled negative fixtures;
- structured generalist Provider measurements such as Docling/Tika.

Timing values present in the source artifact are single-run observations and are intentionally not promoted here as performance claims.
