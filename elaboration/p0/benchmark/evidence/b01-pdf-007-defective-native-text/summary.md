# B01-PDF-007 defective-native-text / OCR-fallback evidence

> Evidence-only E-04 subprofile. No Provider is selected, no fallback route is promoted, and no E-05 production contract is frozen.
>
> Exact measurement/scoring source: `2a4d6fb17eaedb75ee8c0fdaca3029d358f075d2`.
>
> Fixture SHA-256: `4ed576898177b66cc7e187fbf791f32d4721a30c890ee429fad54949f53a59f0`.
>
> Rights remain fail-closed under #131.

## Authored fixture intent

`B01-PDF-007` is a mixed/defective-native-text B-01 subprofile, not a fully scanned B-03 document. It contains:

- three authored native-text units;
- one raster-only visible target: `OCR TARGET 2026`;
- no native PDF text object containing the raster target;
- authored page/region geometry for native and raster-visible content.

The benchmark asks whether nominally successful native extraction can still be materially incomplete, and whether a separately measured OCR profile recovers the raster-only content without erasing native/OCR provenance boundaries.

## Exact-source comparison

| Dimension | pdftotext bbox | pdftohtml XML | Tika 3.3.2 | Docling native/no-OCR | Docling + RapidOCR locked |
| --- | ---: | ---: | ---: | ---: | ---: |
| Native authored text | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| Raster target exact text | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| Raster-region partial OCR candidate | none | none | none | none | `TARGET OCR 2026` |
| Expected token multiset | n/a | n/a | n/a | n/a | exact |
| Expected token order | n/a | n/a | n/a | n/a | mismatch |
| Exact visible-page coverage | 3/4 | 3/4 | 3/4 | 3/4 | 3/4 |
| Native text coordinates | 3/3 | 3/3 | not measured | 3/3 | 3/3 |
| Exact raster-text coordinates | not measured | not measured | not measured | not measured | not measured |
| Provider route status | success | success | success | success | success |
| Provider warning exposes visible gap | no | no | no | no | no |
| Gold-informed fallback required | yes | yes | yes | yes | yes |
| Native/OCR reconciliation | not measured | not measured | not measured | not measured | not measured |

These rows are independent evidence dimensions. They are not inputs to a weighted total score.

## Stage A — unchanged native/no-OCR profiles

Exact-source native workflow run `32633581661` completed successfully on `2a4d6fb`.

- Poppler artifact `9491704095`, digest `sha256:aa3415891b5f875dccde24deaf06086f379497e7ceeb86e97e682e5c645c56bd`;
- Tika artifact `9491704392`, digest `sha256:b17335da03ad1c8167b964e65f5e87a6784b2ab23641316d9aad24714b4df115`;
- Docling native artifact `9491742290`, digest `sha256:0768e4b8e37d3bf9f72de7a5d7e01a7090b8bf018fc57e8903f221577191df93`.

All native profiles recover every authored native string but none recovers the raster-only text. All report route `success`. Poppler and Docling preserve attributable native geometry; Tika does not expose source bbox geometry in the measured XHTML. No route reports an explicit completeness state or a warning that identifies the missing raster-visible content.

This demonstrates the central routing fact for E-05: **Provider success is not equivalent to visible-page completeness**.

## Stage B — locked Docling + RapidOCR profile

RapidOCR is measured as a separate route/profile, never as a mutation of the native Docling baseline:

`docling-2.118.0-rapidocr-3.9.2-torch-en-default`

The Docling-managed `torch:en` RapidOCR bundle is locked by Raiatea before measurement:

- 4 files;
- 32,238,329 bytes;
- manifest SHA-256 `131b40647a9d3d67f7573adc717faa7e9b07048baaef318f1c94dc3bb150b3dc`;
- per-file sizes and SHA-256 values committed in `locks/docling-2.118.0-rapidocr-3.9.2-torch-en.json`.

The reference workflow downloads model material during setup, verifies it byte-for-byte against the lock, then executes the document phase with offline Hugging Face/Transformers controls and remote Docling services/plugins disabled.

Exact-source RapidOCR workflow run `32633581646` completed successfully on `2a4d6fb`; artifact `9491742718`, digest `sha256:73acd2a3afa4c46368f30dc8d02ae67d0fb8c34408fb52c7781bce8daa51fd12`.

### What RapidOCR actually recovered

RapidOCR produced one text block overlapping 99.26% of the authored raster target region:

`TARGET OCR 2026`

Compared with authored `OCR TARGET 2026`:

- all 3 expected tokens are present;
- token multiset is exact;
- token order is wrong;
- normalized exact text is therefore false;
- exact raster recovery remains `0/1`;
- exact visible-page coverage remains `3/4`;
- fallback remains required for this benchmark objective.

This is deliberately recorded as **partial OCR surface evidence**, not as either “OCR saw nothing” or “OCR succeeded”.

## Native/OCR overlap and reconciliation

The measured Docling normalized blocks do not attribute each emitted text block to a `native` versus `ocr` extraction stage. Consequently Raiatea cannot prove whether native text was duplicated/reconciled internally by this profile.

The benchmark therefore records native/OCR reconciliation as `not-measured`. It does **not** infer “no overlap” from the absence of duplicate strings, and it performs no destructive merge.

This is an E-05 / `ExtractorPlugin` requirement: per-evidence lineage must survive normalization when a route contains multiple extraction stages.

## Findings

### F1 — nominal success hides visible incompleteness

All Stage A native profiles return success while exact visible-page coverage is only `3/4`. Provider status and warnings are insufficient to establish completeness.

### F2 — OCR payload must be immutable before canonical measurement

The first RapidOCR run was exploratory because Docling-managed model binaries were not yet pinned. Raiatea now locks file set, sizes, SHA-256 values and canonical manifest digest and fails closed on drift before OCR begins.

### F3 — exact-only scoring hid partial OCR recovery

The first scorer treated `TARGET OCR 2026` as simply missing because it did not exactly equal `OCR TARGET 2026`. The corrected scorer keeps exact recovery at `0/1` while separately recording the raster-region candidate, exact token multiset and token-order mismatch.

### F4 — normalized Docling blocks lose native/OCR stage attribution

The current route does not expose enough per-block provenance to measure native/OCR overlap safely. Reconciliation therefore stays `not-measured`; absence of explicit attribution never becomes an implicit no-overlap claim.

## Route decision

The measured RapidOCR profile is **not promoted as Raiatea's fallback route** from this fixture:

- it is reproducible;
- it demonstrates real partial OCR recovery;
- it fails exact authored word order on the bounded target;
- it exposes no explicit completeness state;
- normalized output does not retain native/OCR stage attribution needed for inspectable reconciliation.

E-04 does not require finding a universally successful OCR engine. This bounded subprofile has produced enough evidence to shape E-05. OCRmyPDF/Tesseract or another profile may be measured later if a later routing decision specifically requires it; it is not needed merely to force a winner here.

## E-05 / Plugin API implications

The future Provider-neutral contract and `ExtractorPlugin` design must preserve:

- Provider **and** route/profile identity;
- native vs OCR/fallback processing-stage lineage;
- success separate from completeness/coverage uncertainty;
- exact content fidelity separate from partial OCR surface evidence;
- Source Coordinates attached only to the evidence they actually support;
- warnings, partial, not-measured and mismatch states;
- conservative overlap/reconciliation state;
- routing/fallback reason as explicit evidence/policy output rather than Provider-brand inference.

## Remaining B-01 gap

This child closes the bounded mixed/defective-native-text routing evidence. B-01 still requires a separate malformed/access-controlled negative child before E-04 can be synthesized toward E-05.

No Provider is selected; no first slice is promoted; G-02/G-04/G-05 remain open; #131 remains fail-closed.
