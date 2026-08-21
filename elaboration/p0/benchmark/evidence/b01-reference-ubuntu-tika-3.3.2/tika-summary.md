# B-01 Apache Tika 3.3.2 XHTML reference baseline

> Benchmark evidence only. Tika is not selected as a production Provider.
>
> Evidence source code: `14acf44200705bfdc6deb5b2c723d319498a18c2`.
>
> GitHub Actions run: `32528505169`; artifact `9463033920`, digest `sha256:4155813b13c67fd3d0334929ebcc81d831fff119de3741dce1dbf2cba99d9d44`.
>
> The fixture/gold redistribution gate remains open in issue #131.

## Environment / route

- OS: `Linux 6.17.0-1022-azure` `x86_64`
- Python: `3.12.14`
- Tika: `3.3.2`
- Tika jar SHA-256: `71ca551380e5eab1add99101f4597a8a49a6a18c6143d6874ee9599ca10ae00e`
- Tika jar SHA-512 verified: `True`
- Java: `openjdk version "21.0.12" 2026-07-21 LTS`
- Java executable SHA-256: `11af352aa2c506c4123a4e4c19c187d59e06cd0dff317d54f5e6806e07c6715d`
- OCR policy: `explicit-no-ocr`
- Config SHA-256: `2a1fe156c5be30ae578496e472e7754c01f156624d28d35f423a4224287841c2`
- Java temp files and PDFBox font cache are confined under the benchmark temporary parent.
- Controlled runtime files observed: `['pdfbox-font-cache/.pdfbox.cache']`
- Unexpected files observed under the controlled parent: `0`.
- Local file input only; no hosted/API route.
- OS-level sandboxing/network isolation are not claimed.

## B01-PDF-001

- route status: `success`
- exact reference text units: `3/3`
- reading-order edges: `2/2`
- source coordinates: `not-measured`
- hierarchy: `measured`; exact semantic types `2/3` when measurable
- page structure observed: `True`
- bbox structure observed: `False`
- metadata keys observed: `20`
- controlled runtime files: `['pdfbox-font-cache/.pdfbox.cache']`
- unexpected side-effect files: `[]`
- raw XHTML SHA-256: `6004c7c397851f22c9d0731acd838e32b3955b9733a8fbecff4bf7cba2332a35`

## B01-PDF-002

- route status: `success`
- exact reference text units: `5/5`
- reading-order edges: `4/4`
- source coordinates: `not-measured`
- hierarchy: `measured`; exact semantic types `4/5` when measurable
- page structure observed: `True`
- bbox structure observed: `False`
- metadata keys observed: `20`
- controlled runtime files: `['pdfbox-font-cache/.pdfbox.cache']`
- unexpected side-effect files: `[]`
- raw XHTML SHA-256: `b34e3c20337e8a81b04fadeae0064dfbf2aa1e03e19662851e4e9768ea7867ba`

## Interpretation boundary

- Missing bbox evidence is reported as `not-measured`/`partial`, never as successful geometry and never as an invented zero score.
- Explicit page containers are retained as page identity; they do not imply source geometry.
- Explicit XHTML tags may provide hierarchy evidence; visual/font cues are not promoted to semantic structure.
- The current fixture title is emitted by Tika as a paragraph, so heading recovery is correctly reported as a semantic mismatch rather than inferred from typography.
- No weighted/universal score is produced.
- Comparison with Poppler controls is limited to dimensions measured by both routes.
- B-01 coverage remains incomplete and #131/G-02/G-04/G-05/first-slice promotion remain open.

## Comparison with the current Poppler controls

- `B01-PDF-001`: Tika and both Poppler controls preserve all current reference text and reading-order edges. Poppler exposes geometry; Tika exposes page identity but no bbox.
- `B01-PDF-002`: Tika preserves text `5/5` and reading order `4/4`, matching the `pdftohtml-xml` control on the current reading-order gold and outperforming `pdftotext-bbox-layout` (`3/4`) on that single dimension. This is not a total Provider ranking.
- Tika adds explicit page containers and metadata, but on these fixtures it emits the visual title as `<p>`, so heading semantics are not recovered.
- Geometry remains unavailable in the measured Tika XHTML route; Poppler controls remain the coordinate baseline for these fixtures.
