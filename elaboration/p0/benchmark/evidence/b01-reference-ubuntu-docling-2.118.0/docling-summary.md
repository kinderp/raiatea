# B-01 Docling 2.118.0 structured reference baseline

> Benchmark evidence only. Docling is not selected as a production Provider.
>
> Evidence source code: `4fca693d512d02df7da971280ae34779cbec57fb`.
>
> GitHub Actions run: `32566131807`; artifact `9474163662`, digest `sha256:ad41fef5d2c658284d14c0ee92266c60f860697a2d5a0437b353475944f521c3`.
>
> The fixture/gold redistribution gate remains open in issue #131.

## Reproducibility

The reference verifier passed before document measurement:

- Docling `2.118.0`; top-level wheel SHA-256 `fd4962c9a54229bae1eb9b49f7fadb7e7b8affabf7e4fba1aac8cb335f558c8f`;
- CPython `3.12.14` on GitHub Actions Ubuntu 24.04 / x86_64;
- dependency environment: `121/121` exact locked distributions, freeze SHA-256 `54625595793321bdcb4f7b5763122b2c403ce1f4ecbd6d7837ab619a96c39456`;
- stable `layout` model payload: `11/11` files, `342987978` bytes, manifest SHA-256 `c9afe973808a41c359c1f270f063097972985c096468089b206031395f8a885e`;
- ephemeral Hugging Face `.cache` metadata is excluded from the stable payload lock but retained in the cache-inclusive evidence tree;
- measured route: CPU, OCR off, table/enrichment models off, remote services off, external plugins off;
- measured phase uses offline Hugging Face/transformers controls and controlled cache roots; OS-level network isolation is not claimed;
- no new files appeared in the measured cache roots for either fixture.

## B01-PDF-001 — single-column control

- content preserved: `3/3`;
- Provider segmentation exact: `3/3`;
- reading-order edges: `2/2`;
- source coordinates: `measured`, unit-attributable geometry `3/3`, contained `3/3`;
- hierarchy semantic type: `3/3`; segmentation-exact semantic units `3/3`;
- raw lossless JSON SHA-256: `ff88397d1128a9e92d462ef597e3c2c355d0042e11bc5c42c17ffd729ca4e30d`.

On this minimal single-column fixture Docling preserves the current content, order, semantic labels and per-unit source geometry.

## B01-PDF-002 — two-column reading-order control

- content preserved: `5/5`;
- Provider segmentation exact: `1/5`;
- reading-order edges: `4/4`;
- source coordinates: `partial`; only `1/5` reference units has unit-attributable geometry;
- hierarchy semantic type: `5/5`, but segmentation-exact semantic units: `1/5`;
- raw lossless JSON SHA-256: `6f1576c784f8127f4b70c62c5a957e9130ec2c586a8228d02a33fede4be01cb1`.

Docling emits the title as one heading block and merges the four column paragraphs into one larger paragraph block. The four reference texts are present in the correct order inside that block, so content/order can be measured, but the aggregate bbox is **not copied** onto the four reference paragraphs. Their per-paragraph geometry therefore remains unmeasured.

## Comparison with current B-01 evidence

- Poppler remains the strongest current control for fine per-text geometry on `B01-PDF-002`: both Poppler routes expose all five current coordinate regions; `pdftohtml-xml` also has reading order `4/4`.
- Tika has reading order `4/4` and explicit page/paragraph structure, but no bbox on these fixtures.
- Docling adds explicit heading/paragraph semantics and bbox provenance, but on the current two-column fixture its paragraph segmentation is coarser: content/order are preserved while only the title retains unit-attributable geometry.

These are per-dimension observations over two minimal fixtures, **not a total Provider ranking** and not enough to select the P0 Provider.

## Remaining gates

- full B-01 coverage is still false: headings/lists/links, figures/captions, tables, formula/code, defective native text and negative malformed/access-controlled PDFs remain open;
- issue #131 remains open, therefore `G-02=false` and the fixture corpus is not yet public-rights-safe;
- `G-04=false`, `G-05=false`;
- `provider_selected=false`;
- `first_slice_promoted=false`.
