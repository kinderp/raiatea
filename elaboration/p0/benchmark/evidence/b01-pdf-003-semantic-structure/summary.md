# B01-PDF-003 semantic-structure evidence

> Evidence-only extension for E-04f. No Provider is selected and no first slice is promoted.
>
> Evidence source commit: `804bd104b5ba9eed4d7be41cc6364d66885c3e70`.
>
> Fixture SHA-256: `91c16c6d06b213123256ae4b0ad15f8aa398c2dd5e9af34fc0f27e7cb494061b`.
>
> Fixture redistribution remains `not-established` pending #131.

## Authored fixture intent

`B01-PDF-003` adds one bounded semantic-text fixture with:

- document title, authored heading level 1;
- section heading, authored level 2;
- nested heading, authored level 3;
- normal paragraph;
- two ordered-list items;
- Courier code-like line;
- a real PDF URI annotation associated with the visible label `Raiatea benchmark link` and target `https://example.invalid/raiatea-benchmark`.

The gold was committed before Provider measurement. Font size, Courier and visual position are **not** accepted as semantic proof by the scorer.

## Measured comparison

| Dimension | pdftotext bbox | pdftohtml XML | Tika 3.3.2 | Docling 2.118.0 |
| --- | ---: | ---: | ---: | ---: |
| Content preserved | 8/8 | 8/8 | 8/8 | 8/8 |
| Segmentation exact | 8/8 | 8/8 | 8/8 | 8/8 |
| Reading-order edges | 7/7 | 7/7 | 7/7 | 7/7 |
| Unit-attributable coordinate regions | 8/8 | 8/8 | not measured | 8/8 |
| Semantic types exact | 0/8 | 0/8 | 2/8 | 6/8 |
| Heading levels exact | not measured | not measured | not measured | 1/3 |
| URI target exact | not measured | 1/1 | not measured | 1/1 |
| URI source association exact | not measured | 1/1 | not measured | 1/1 |

These rows are independent measurements, not inputs to a weighted total score.

## Route-specific findings

### Poppler controls

Both Poppler controls preserve all current text, order and geometry. They still expose no Provider-neutral heading/list/code semantics, so semantic types and heading levels remain unmeasured rather than inferred from font/layout.

`pdftohtml-xml` adds one useful explicit capability over `pdftotext-bbox-layout`: its generated XML contains an actual `<a href="https://example.invalid/raiatea-benchmark">Raiatea benchmark link</a>`. The benchmark therefore measures URI target `1/1` and source association `1/1` for that route. `pdftotext-bbox-layout` has no explicit link collection and remains `not-measured` for links.

### Apache Tika 3.3.2

Tika preserves all eight text units and all reading-order edges. It exposes page structure but no source bbox geometry in the measured XHTML.

For this fixture, all eight current text units are emitted as paragraph elements. As a result only the authored normal paragraph and authored link-label paragraph match semantic type (`2/8`). Heading levels remain `not-measured`. The URI target does not appear in the measured Tika XHTML/metadata, so link extraction also remains `not-measured`.

### Docling 2.118.0

Docling preserves all eight text units, exact block segmentation, order and current geometry. It explicitly recognizes:

- all three authored headings as headings;
- both list items as `list_item`;
- the normal paragraph as paragraph.

Two semantic mismatches remain visible:

- the authored code line is emitted as normal text/paragraph;
- the visible link label is emitted as `section_header`/heading.

All three heading-like units expose Docling level `1`, so only the authored level-1 title matches (`1/3`). This is measured evidence, not a typography inference.

Docling's normalized `text` strips the `1.` / `2.` list markers, while the same lossless item exposes the authored surface in `orig`. The E-04f semantic supplement uses `orig` **only for explicit `list_item` surface evidence**, preserving the normalized text as metadata. The lossless `hyperlink` field likewise supplies the URI target and visible-label association directly. No visual inference is used.

## Provenance

General reference workflow run `32569054875` on the exact source commit produced:

- Poppler artifact `9474843038`, digest `sha256:0dae2cccbfa3eb82d4e4f32c7e09e8d4ef2d72943bcc17147391eab92d0a1d4e`;
- Tika artifact `9474841518`, digest `sha256:91ade410c4e5f91b052fa2d81e174c418fd8f613aa8b17053602c03da9f15396`;
- canonical Docling artifact `9474875972`, digest `sha256:4f2ae90650ad1fae7efc3d2189f2f69df2ca6a95dc46460de42ab63810cfe066`.

The separate Docling semantic-supplement workflow run `32569054888` passed the same dependency/model locks and produced artifact `9474872892`, digest `sha256:1080ae6b809b0398e10e7a23ee6a9aac506bfaffbb3b0c68c95402035e06d3a9`.

## Remaining gates

The fixture closes only the bounded semantic-text gap. B-01 is still incomplete for:

- figures/captions/assets;
- tables;
- formula fidelity beyond code/preformatted text;
- defective native text and later OCR/fallback routing;
- malformed/access-controlled negatives.

Therefore:

- `provider_selected=false`;
- `first_slice_promoted=false`;
- `G-02=false` pending #131;
- `G-04=false`;
- `G-05=false`.
