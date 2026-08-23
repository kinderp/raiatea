# B01-PDF-006 formula-fidelity evidence

> Evidence-only extension for E-04. No Provider is selected and no first slice is promoted.
>
> Exact evidence source: `6440da9b69c5ab50370db3999bccc8ceb8146cd5`.
>
> Fixture SHA-256: `f3b711f45bcff702fedb2abdf8efa013b8b074eaa9e0adf555618e9342a488ba` (1621 bytes).
>
> Rights remain fail-closed pending #131.

## Authored intent

The fixture contains three bounded visual formula cases built only from positioned ASCII glyphs and one drawn line:

1. `E = mc²`, with the `2` authored as a separately positioned raised glyph;
2. `x² + y² = z²`, again using separately positioned raised `2` glyphs;
3. `(a + b) / c`, with numerator text, an authored horizontal fraction bar and denominator text.

The PDF contains no semantic mathematics. Superscript and fraction relations exist only in Provider-neutral gold. A Provider receives mathematical-structure credit only when it exposes explicit relation evidence; font size, vertical offset, picture grouping and the fraction bar are never promoted to semantics.

## Measured comparison

| Dimension | pdftotext bbox | pdftohtml XML | Tika 3.3.2 | Docling 2.118.0 pinned profile |
| --- | ---: | ---: | ---: | ---: |
| Visible formula surfaces | 1/3 | 3/3 | 3/3 | 3/3 |
| Formula display-order edges | 0/2 (partial) | 2/2 | 2/2 | 2/2 |
| Token geometry | 6/19 | 6/19 | not measured | 6/19 |
| Max observed token edge error | 7.512 pt | 7.333 pt | not measured | 7.512 pt |
| Explicit superscript/fraction relations | not measured 0/5 | not measured 0/5 | not measured 0/5 | not measured 0/5 |
| Provider grouping diagnostic | none | none | none | 2 `picture` groups, explicitly non-semantic |

These are independent measurements. There is no weighted or universal formula score.

## Route-specific findings

### Poppler `pdftotext-bbox-layout`

The route preserves individual glyph text and useful geometry, but its text flow moves the raised exponent from the energy expression away from its base. Consequently only one of the three compact authored formula surfaces is preserved as a unique sequence and no authored formula-order edge can be established from those complete surfaces. This is a reading-flow/content-surface limitation, not evidence that the exponent semantics were understood or lost: semantic relations remain `not-measured`.

### Poppler `pdftohtml-xml`

The XML route preserves all three visible formula surfaces and both display-order edges. It provides attributable bbox evidence for 6/19 authored tokens. It still exposes no explicit superscript or fraction relation collection, so mathematical structure remains `not-measured`.

### Apache Tika 3.3.2

Tika preserves all three compact visible surfaces and their order, including flattened forms such as `E = mc 2`. The measured XHTML exposes no source bbox geometry for formula tokens and no explicit mathematical relations. Therefore surface fidelity is measured while geometry and mathematical structure remain `not-measured`.

### Docling 2.118.0, current pinned profile

The current route deliberately keeps `do_formula_enrichment=false`. Lossless JSON groups the first two visual formula regions as two `picture` objects with explicit text children, while the fraction text remains outside those picture groups. The benchmark retains these two groups as `observed-nonsemantic` diagnostics only. With the lossless descendant text restored for content measurement, all three visible formula surfaces and both display-order edges are preserved; 6/19 token bboxes are attributable. No explicit superscript/fraction relations are exposed, so the result remains 0/5 `not-measured` for math semantics.

This evidence supports evaluating a formula-enriched Docling profile later only as a **separate route/profile**, never as a silent replacement for the pinned baseline.

## Provenance

GitHub Actions formula workflow run `32627418501` on source `6440da9` succeeded for the contract and all Provider jobs:

- Poppler artifact `9490114603`, digest `sha256:d033353048e2cebcad2d7cf26c298ac0fafb4bfa523954dd1f4795b2a3ce8fcb`;
- Tika artifact `9490109129`, digest `sha256:62676c16967184957f348b4cce1c4b477e8fc846edefbe9988649071b0e18c19`;
- Docling artifact `9490153938`, digest `sha256:4d75cdd3c3b3d1d7a846c496c0dcc8963e9ded26d57da6868a627e2cf1062e7e`.

On the same source head, benchmark harness run `32627418549`, semantic regression `32627418585`, figure regression `32627418540` and table regression `32627418473` all succeeded.

## E-05 / Plugin API implications

Formula evidence reinforces the same contract direction emerging from figures and tables:

- visible content preservation must be separable from structural/semantic interpretation;
- Source Coordinates may exist for only part of a structure;
- Provider-native grouping must remain representable without coercing it into Raiatea semantic types;
- unsupported or absent semantic relations must stay explicitly unknown/`not-measured`;
- capabilities should be route/profile-specific: e.g. `native-pdf` and a future `formula-enriched-pdf` are materially different extraction profiles even when supplied by the same Provider;
- an `ExtractorPlugin` must be able to expose raw/Provider evidence plus normalized Raiatea evidence without fabricating a lowest-common-denominator success flag.

No public E-05 schema is frozen by this benchmark record.

## Remaining E-04 B-01 gaps

After this child, B-01 still needs the defective native-text/OCR-fallback subprofile and malformed/access-controlled negative PDF evidence. #131/G-02/G-04/G-05 and first-slice promotion remain open.
