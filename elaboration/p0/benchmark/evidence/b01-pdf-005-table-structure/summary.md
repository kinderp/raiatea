# B01-PDF-005 table-structure evidence

> Evidence-only extension for E-04. No Provider is selected and no first slice is promoted.
>
> Fixture SHA-256: `f841920e1e9b2566124c2d174bc6627ecaf5ebc96482898f163a4f3e1aa04456` (`1518` bytes).
>
> Fixture redistribution remains `not-established` pending #131.

## Authored fixture intent

`B01-PDF-005` contains one deterministic 4×3 table with one explicit authored header row:

| Item | Qty | Price |
| --- | ---: | ---: |
| Alpha | 2 | 3.50 |
| Beta | 1 | 7.00 |
| Total | 3 | 14.00 |

The gold defines 12 cell texts, row/column coordinates, header/body roles, table geometry and cell geometry. Ordinary text before and after the table remains a separate reading-order dimension.

The PDF itself is not semantically tagged as a table. Provider credit therefore comes only from evidence actually exposed by each measured route. Visible alignment is never converted into Provider-native row/column structure.

## Measured comparison

| Dimension | pdftotext bbox | pdftohtml XML | Tika 3.3.2 | Docling 2.118.0 pinned profile |
| --- | ---: | ---: | ---: | ---: |
| Surrounding text | 3/3 | 3/3 | 3/3 | 3/3 |
| Surrounding reading-order edges | 2/2 | 2/2 | 2/2 | 2/2 |
| Authored cell text preserved | 12/12 | 12/12 | 12/12 | 12/12 |
| Explicit table count | not measured | not measured | not measured | 1/1 |
| Explicit topology | not measured | not measured | not measured | 1×1 observed vs 4×3 gold |
| Explicit cell-bound text | not measured | not measured | not measured | not measured |
| Header/body roles | not measured | not measured | not measured | not measured |
| Table geometry | not measured | not measured | not measured | measured; max edge error ≈ 1.055 pt |
| Cell geometry | not measured | not measured | not measured | not measured |

These rows are independent evidence surfaces, not a weighted total score.

## Route-specific findings

### Poppler controls

Both Poppler controls preserve every authored cell string. `pdftotext-bbox-layout` exposes the 12 cell values as separate text blocks; `pdftohtml-xml` likewise preserves the visible text and coordinates.

Neither route exposes a trustworthy explicit table/cell collection in the current benchmark observation. The benchmark therefore does **not** reconstruct rows or columns from text positions. Presence, topology, roles and table/cell geometry remain `not-measured`.

### Apache Tika 3.3.2

Tika preserves all 12 authored cell strings, but the measured XHTML groups each visible table row into paragraph text such as `Item Qty Price` and `Alpha 2 3.50`.

That is useful content evidence, not explicit table topology. The measured XHTML exposes no trustworthy table collection, so structural dimensions remain `not-measured`.

### Docling 2.118.0 — current pinned profile

The current pinned Docling route uses `do_table_structure=false`.

Its lossless JSON exposes:

- one explicit `table` item;
- a table-level bbox close to the authored region;
- explicit table data reporting `1` row × `1` column with one empty structural cell;
- an explicit table child/group chain containing all 12 authored table strings.

The table-specific mapper therefore preserves the 12 strings as `explicit-table-descendant-unbound-to-cell` content evidence. They prove content preservation but **do not** repair the Provider's 1×1 topology and are not rebound to authored row/column coordinates.

The table bbox is `[70.94498, 439.61374, 540.68811, 601.05231]` points versus gold `[72, 440, 540, 600]`, with maximum absolute edge error about `1.055` pt. No acceptance tolerance is invented after seeing this result; the raw edge errors are retained.

This is an important E-05 input: richer table extraction, if required, should be evaluated as a **distinct Docling route/profile** rather than silently changing the already-pinned baseline.

## Provenance

All measured table evidence is frozen from exact source commit `7834742856f4cfc01e065503396df8444e7e4ce7`.

GitHub Actions table-evidence run `32624545149` completed successfully and produced:

- Poppler artifact `9489318140`, digest `sha256:72d27541d97deb3f67478eb4179e809cf56211f9529fd62a38e7e2c4921475b8`;
- Tika artifact `9489320069`, digest `sha256:5b481ca46e946d0205b5a6d6db869bfd748d4dff80c9ba834208852b96a1c8a2`;
- Docling artifact `9489357436`, digest `sha256:91c9859c1478991d6babd475e3b694e58478d18d239de6cd8233670041ee5a92`.

The same source commit also passed the dependency-light benchmark harness on Linux/Windows with Python 3.10/3.12 in run `32624545024`. Figure and semantic regression workflows were green on the same head.

The pinned Docling execution used:

- Docling `2.118.0`;
- wheel SHA-256 `fd4962c9a54229bae1eb9b49f7fadb7e7b8affabf7e4fba1aac8cb335f558c8f`;
- environment freeze SHA-256 `54625595793321bdcb4f7b5763122b2c403ce1f4ecbd6d7837ab619a96c39456`;
- stable model payload SHA-256 `c9afe973808a41c359c1f270f063097972985c096468089b206031395f8a885e`;
- raw lossless JSON SHA-256 `e1340ee6b3a4b96acf06743c40648d96cc0bba7d61f3f5c35f19396f52122c6f`.

## E-05 / Plugin API implications

This fixture strengthens several requirements for the future Provider-neutral extraction contract and `ExtractorPlugin` boundary:

- `text preserved` and `explicit table topology preserved` cannot be one boolean capability;
- an explicit table may coexist with degraded/incorrect row-column structure;
- text can have lineage to a table while cell identity remains unknown;
- Provider-native coordinates should remain inspectable rather than being reduced immediately to a pass/fail geometry score;
- route/profile capabilities matter: one Provider brand may need separate extraction profiles for native text, tables, OCR or enrichment.

## Remaining gates

B-01 remains incomplete for:

- `B01-PDF-006` formula fidelity beyond current code/preformatted coverage;
- `B01-PDF-007` defective native text and later OCR/fallback routing;
- malformed/access-controlled negative PDF cases.

Therefore:

- `provider_selected=false`;
- `first_slice_promoted=false`;
- `G-02=false` pending #131;
- `G-04=false`;
- `G-05=false`.
