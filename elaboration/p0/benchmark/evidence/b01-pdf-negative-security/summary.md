# B01 negative malformed/access-controlled PDF evidence

> Final bounded B-01 negative/security evidence for E-04. These fixtures are excluded from ordinary quality averages and do not select a Provider or first slice.

Canonical raw Provider evidence source: `c39fa9f22d8c15db0fb09162210eb7a3d02090bb`.

## Fixtures

- `B01-PDF-NEG-001` — deterministic inert PDF truncated before `endstream/endobj`, xref, trailer, `startxref` and EOF; SHA-256 `803cdada146c89d6a86169351ed7a4b0a46c0afe99f5b08ea25f813d0c8d630d`, 376 bytes.
- `B01-PDF-NEG-002` — deterministic project-generated password-encrypted PDF; SHA-256 `c277faaffe74c38b0e01b18d30e2573614f97377aacbb5e74eadd012a528029f`, 1079 bytes. The measured Provider routes receive neither the fixture password nor a bypass/decryption option.

qpdf is fixture-generation/setup evidence only: version 11.9.0, Ubuntu package `11.9.0-1.1ubuntu0.1`, executable SHA-256 `10fc302c4ca9860f24b8d2cb7f8a4cc454ba59d4a91e7a8e40f6b2c229486df7`.

## Measured negative outcomes

| Fixture / route | Provider status | Explicit negative/restriction signal | Normalized outcome | Acceptable negative outcome |
| --- | --- | --- | --- | --- |
| NEG-001 / Poppler `pdftotext-bbox-layout` | failed | malformed/xref/trailer | failed-with-malformed-signal | yes |
| NEG-001 / Poppler `pdftohtml-xml` | failed | not explicit | safe-failure-generic | yes |
| NEG-001 / Tika 3.3.2 | **success** | **no** | **silent-complete-success** | **no** |
| NEG-001 / Docling 2.118.0 | failed | PDFium data-format error | failed-with-malformed-signal | yes |
| NEG-002 / Poppler `pdftotext-bbox-layout` | failed | incorrect password | restricted-or-password-required | yes |
| NEG-002 / Poppler `pdftohtml-xml` | failed | not explicit | safe-failure-generic | yes |
| NEG-002 / Tika 3.3.2 | failed | encrypted / invalid password | restricted-or-password-required | yes |
| NEG-002 / Docling 2.118.0 | failed | PDFium incorrect-password error | restricted-or-password-required | yes |

The Tika malformed result is the main finding. The measured XHTML route exits successfully and exposes page/metadata structure, but produces zero content blocks and no warning that communicates the intentional corruption. Its unrelated `bbox-not-exposed` warning does not establish malformed/degraded state. Therefore a Provider/process `success` bit cannot be treated as evidence that integrity/completeness was established.

## Security audit

All measured Provider invocations pass the negative-route audit:

- no fixture password supplied to a Provider;
- no `-nodrm`, decrypt/remove-restrictions option, password file, password guessing or recovery path;
- no remote Provider route;
- generator-only qpdf static-ID/AES-IV options remain outside the Provider invocation namespace;
- rejected/failed inputs are accepted benchmark outcomes and are not converted into synthetic success.

## Exact-source artifacts

Workflow run `32634960777`:

- Poppler artifact `9492079719`, digest `sha256:748c00f261b703962ef347ef9e520ed3b884bc81be0934306a12e4dc3a596a52`;
- Tika artifact `9492093713`, digest `sha256:87a464e473403e340d24c5d6f2593870b1b77c0f9cbc9f0d83fcf12564904258`;
- Docling artifact `9492110457`, digest `sha256:e9752b146e4abe5dbbf2293bdf135e72a08ef154678aab9175c141145f89c3b3`.

## E-05 / Plugin API implications

This closes the core negative/security evidence question for B-01 and adds several requirements to the later Provider-neutral contract and `ExtractorPlugin` design:

- Provider/process `success` must remain distinct from integrity/completeness-established state;
- rejected, unsupported, restricted/password-required, failed, partial/degraded and unknown need separate representable states;
- a generic failure and an explicit access-control signal are not equivalent evidence;
- security-policy refusal is a valid first-class processing outcome, not a failure to be bypassed;
- attempted Processing Run provenance and invocation policy must remain traceable even when no Normalized Representation is produced;
- an `ExtractorPlugin` must not silently retry an access-controlled Source through circumvention/password-guess/restriction-removal behavior.

## Boundary

No malicious payloads were created or executed. No access-control bypass or credential recovery was attempted. These results are benchmark-only and do not freeze the public E-05 schema. Rights remain fail-closed under #131.
