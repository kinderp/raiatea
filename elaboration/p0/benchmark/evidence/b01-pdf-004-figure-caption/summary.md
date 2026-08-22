# B01-PDF-004 figure, caption and asset evidence

**Status:** E-04 benchmark evidence  
**Scope:** `B01-PDF-004` only  
**Source commit:** [`614816a`](https://github.com/kinderp/raiatea/commit/614816a66d039aaeaf9bbf1f361b2c81d8c6a044)  
**Source workflow run:** [32596219962](https://github.com/kinderp/raiatea/actions/runs/32596219962)  
**Parent:** #129  
**Child:** #145  
**Rights gate:** #131 remains open and fail-closed

This snapshot records the first measured B-01 figure/caption/asset fixture across
the already-pinned Poppler, Apache Tika and Docling routes. It is benchmark-only
evidence. It does not define the E-05 public extraction contract, select a
Provider, or promote the candidate first slice.

## Fixture

`B01-PDF-004` is a deterministic 1,133-byte born-digital PDF containing:

- ordinary text before and after the figure;
- one explicit PDF `/Image` XObject;
- one authored visible caption;
- deterministic 4 × 3 RGB pixels;
- authored figure geometry `[72, 500, 252, 620]` PDF points;
- an authored figure-caption relation in the gold data.

Fingerprints:

```text
PDF SHA-256
8d4c9d3f70bc22cfe0ee7e9eabd76bc6f39d1baa98032112e44557379a34c3da

Authored RGB pixel payload SHA-256
2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee
```

Existing canonical `B01-PDF-001`, `B01-PDF-002` and `B01-PDF-003` byte
identities remain unchanged.

The project-created fixture remains rights-pending: redistribution is
`not-established`, `public_rights_safe=false`, and external remote Provider use
is denied until #131 records a different decision.

## Measurement rules

The figure benchmark deliberately refuses to collapse distinct evidence into one
quality score.

It measures separately:

1. caption text preservation;
2. explicit figure presence;
3. explicit figure geometry;
4. comparable asset/pixel identity;
5. explicit figure-caption association.

Important invariants:

- missing Provider evidence is `not-measured`, not zero and not success;
- a text box near an image is never treated as a caption relation;
- association requires a Provider-originated relation record;
- pixel identity uses the decoded pixel payload when inspectable, not equality of
  Provider-specific encoded files;
- geometry preserves raw bbox evidence and raw per-edge errors in PDF points;
- no tolerance was introduced after looking at Provider output.

## Measured results

| Route | Caption text | Figure | Geometry | Pixel identity | Figure ↔ caption |
| --- | --- | --- | --- | --- | --- |
| Poppler `pdftotext-bbox-layout` | `1/1` exact | not measured | not measured | not measured | not measured |
| Poppler `pdftohtml-xml` | `1/1` exact | `1/1` explicit | exact page + bbox; max edge error `0.0 pt` | `1/1` exact decoded pixels | not measured |
| Tika `3.3.2` XHTML | `1/1` exact | not measured | not measured | not measured | not measured |
| Docling `2.118.0` | `1/1` exact, explicit `caption` label | `1/1` explicit picture | page exact; bbox non-exact; max edge error `1.0947799682617188 pt` | not measured | `1/1` explicit relation |

### Poppler

`pdftotext-bbox-layout` preserves the authored caption text but exposes no
explicit figure collection, so figure-specific dimensions remain
`not-measured`.

`pdftohtml-xml` emits an explicit `<image>` element and a generated PNG. On the
reference run:

```text
Provider bbox -> PDF points
[72.0, 500.0, 252.0, 620.0]

Max edge error
0.0 pt

Generated PNG bytes
113

Generated PNG SHA-256
21b8823b706be67a8ae38bf3d348e068f6ae4c2d9d70c9b8d0ab161a4c3c7815

Decoded pixel SHA-256
2e9756a2943938c833aa0b9d72189577b64146bfdc7ce30957624a762cf5abee
```

The decoded pixels exactly match the authored fixture payload. Poppler does not,
however, expose an explicit figure-caption relation in this route, so that
relationship remains `not-measured` even though the caption is visibly nearby.

During this measurement, an initial mapper rejected Poppler's absolute generated
image path even though it was under the controlled temporary work root. Finding
F1 corrected the boundary: absolute and relative generated refs are accepted
only after canonical resolution proves containment under the work root;
traversal and external absolute paths still fail closed.

### Apache Tika 3.3.2

The pinned no-OCR XHTML route preserves the exact caption text but does not
expose an explicit figure collection or recognized source bbox for this fixture.
The benchmark therefore records figure presence, geometry, pixel identity and
association as `not-measured` rather than inferring them from the source PDF.

### Docling 2.118.0

The pinned lossless Docling JSON exposes:

```text
picture ref
#/pictures/0

caption ref
#/texts/2

explicit relation source
docling-picture.captions-explicit-ref
```

The picture contains explicit page/bbox provenance and an explicit `captions`
reference to a text item labeled `caption`. This is enough to measure figure
presence, caption text and figure-caption association without layout inference.

Observed picture bbox:

```text
[70.90522003173828,
 500.0570068359375,
 252.6000518798828,
 621.0237884521484]
```

Signed edge errors against the authored figure region:

```text
[-1.0947799682617188,
  0.0570068359375,
  0.6000518798828125,
  1.0237884521484375]
```

The benchmark records this measured non-exact geometry directly; it does not
invent a tolerance to turn it into a pass/fail result.

The current pinned Docling route has `generate_picture_images=False`, so it does
not produce comparable image bytes. Pixel identity therefore remains
`not-measured` even though the picture item itself is explicit.

## Reference artifacts

The compact JSON snapshot in this directory survives the temporary Actions
artifacts. The original exact-run artifacts are still useful while retained:

| Provider | Artifact | Digest |
| --- | ---: | --- |
| Poppler | `9481617551` | `sha256:a426db99771e67933751e40a6cfcf6a0b07bfdefdcd38b741db9cf5eab91c43e` |
| Tika | `9481616707` | `sha256:8bfc5c050714fb9d7d32f0780ae5981aa38d9cd3fb5a49bb3b46095f7573a7a1` |
| Docling | `9481654773` | `sha256:0686a9ac22075da56c2a805fb6a5c813fbba8628d7485d2ef130bf5a6495dc97` |

All three were produced from source commit `614816a` by workflow run
`32596219962`, which completed successfully. The normal P0 benchmark harness and
the existing semantic Docling evidence workflow were also green for that exact
commit.

## E-05 / plugin-boundary implication

This fixture provides useful architecture evidence rather than a Provider
ranking.

A future extraction contract must not assume that a Provider which can extract
PDF text can also expose all of:

```text
text
figure presence
source geometry
asset bytes
semantic figure-caption relations
```

The measured routes expose complementary evidence surfaces:

```text
Poppler pdftohtml
  -> strong explicit image bytes + exact authored geometry in this fixture
  -> no explicit caption relation

Tika XHTML
  -> caption text
  -> no explicit figure evidence in this measured route

Docling lossless JSON
  -> explicit picture + geometry + semantic caption relation
  -> no comparable picture bytes in the pinned configuration
```

Therefore E-05 should preserve capability/evidence partiality and Provider-native
provenance rather than forcing every Adapter into a false all-or-nothing
`extract()` success shape. This also informs the later Raiatea Plugin API: an
`ExtractorPlugin` should advertise and return inspectable capabilities/evidence,
while Raiatea Core owns the normalized meaning, provenance and failure semantics.

## Decision

- no Provider selected;
- no weighted/global score introduced;
- no geometry tolerance promoted;
- no first-slice promotion;
- no E-05 public payload frozen;
- no change to rights gate #131.
