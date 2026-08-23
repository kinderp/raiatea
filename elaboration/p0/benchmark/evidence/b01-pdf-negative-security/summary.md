# B01 negative malformed/access-controlled PDF evidence

> Final bounded B-01 negative/security evidence for E-04. These fixtures are excluded from ordinary quality averages and do not select a Provider or first slice.

Canonical raw Provider evidence source: `c39fa9f22d8c15db0fb09162210eb7a3d02090bb`.

Provider observations below are anchored to that exact source/run. Later branch commits harden only Provider-neutral normalization, fail-closed classification and evidence-file integrity; they do not rewrite the measured Provider statuses, warnings or content observations.

## Fixtures

- `B01-PDF-NEG-001` — deterministic inert PDF truncated before `endstream/endobj`, xref, trailer, `startxref` and EOF; SHA-256 `803cdada146c89d6a86169351ed7a4b0a46c0afe99f5b08ea25f813d0c8d630d`, 376 bytes.
- `B01-PDF-NEG-002` — deterministic project-generated password-encrypted PDF; SHA-256 `c277faaffe74c38b0e01b18d30e2573614f97377aacbb5e74eadd012a528029f`, 1079 bytes. The measured Provider routes receive neither the fixture password nor a processing override that disables the access-control boundary.

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

The Tika malformed result is the principal measured finding. The measured XHTML route exits successfully and exposes page/metadata structure, but produces zero content blocks and no warning that communicates the intentional corruption. Its unrelated `bbox-not-exposed` warning does not establish malformed/degraded state. Therefore a Provider/process `success` bit cannot be treated as evidence that integrity/completeness was established.

## Normalization hardening after the canonical raw run

Review of the negative-result contract produced two additional invariants without changing the nominal Provider facts above.

For malformed input, a Provider-native `success` with an explicit corruption signal is normalized as **degraded**, not as an ordinary successful extraction. A success without a relevant signal remains `silent-complete-success` and is unacceptable for the negative fixture.

For access-controlled input, Provider-native `success` is not considered safe merely because an encryption/password signal is present. The normalizer distinguishes:

- explicit restriction + trustworthy empty content → `safe-metadata-or-restricted-success`;
- explicit restriction + output collection unavailable → `restricted-success-output-unknown`, fail closed;
- explicit restriction + content blocks → `unexpected-content-under-access-control`, fail closed;
- no restriction signal → `silent-complete-success-with-inaccessible-content`, unacceptable.

The scored command also keeps raw and normalized channels distinct: the raw runner persists its canonical JSON file, while the scored CLI emits exactly one valid normalized JSON document on stdout. This is regression-tested so evidence artifacts remain machine-readable.

## Security audit

All measured Provider invocations pass the negative-route audit:

- no fixture password supplied to a Provider;
- no processing option that removes or weakens the access-control boundary;
- no password guessing or recovery path;
- no remote Provider route;
- generator-only qpdf static-ID/AES-IV options remain outside the Provider invocation namespace;
- rejected/failed inputs are accepted benchmark outcomes and are not converted into synthetic success.

## Exact-source artifacts

Workflow run `32634960777`:

- Poppler artifact `9492079719`, digest `sha256:748c00f261b703962ef347ef9e520ed3b884bc81be0934306a12e4dc3a596a52`;
- Tika artifact `9492093713`, digest `sha256:87a464e473403e340d24c5d6f2593870b1b77c0f9cbc9f0d83fcf12564904258`;
- Docling artifact `9492110457`, digest `sha256:e9752b146e4abe5dbbf2293bdf135e72a08ef154678aab9175c141145f89c3b3`.

The final frozen-head workflow will re-run the same pinned routes and publish raw + normalized artifacts together; this is a validation of the unchanged Provider facts, not a replacement of the canonical raw measurement source above.

## Finding log

| ID | Severity | Status | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | major | resolved | Tika 3.3.2 reports native `success` for the intentionally truncated NEG-001 without a relevant corruption signal. | Separate Provider status from normalized integrity/degradation outcome; classify as `silent-complete-success` / unacceptable. |
| F2 | major | resolved | Access-controlled Provider `success` needed to distinguish trustworthy empty output from unknown output or unexpected content. | Fail-closed states added for empty vs unknown vs content-bearing output; dedicated tests cover all cases. |
| F3 | minor | resolved | The scored wrapper could emit raw JSON followed by normalized JSON on stdout. | Suppress only duplicate raw stdout; persist raw separately and regression-test that scored stdout is one valid JSON document. |

## E-05 / Plugin API implications

This closes the core negative/security evidence question for B-01 and adds several requirements to the later Provider-neutral contract and `ExtractorPlugin` design:

- Provider/process `success` must remain distinct from integrity/completeness-established state;
- rejected, unsupported, restricted/password-required, failed, partial/degraded and unknown need separate representable states;
- a generic failure and an explicit access-control signal are not equivalent evidence;
- security-policy refusal is a valid first-class processing outcome, not a failure to route around automatically;
- output availability itself may be known-empty, unknown or anomalously content-bearing and must not be collapsed;
- attempted Processing Run provenance and invocation policy must remain traceable even when no Normalized Representation is produced;
- an `ExtractorPlugin` must not silently retry an access-controlled Source through an unauthorized credential or restriction-override path.

E-05 contract exploration is tracked in #159. `ExtractorPlugin` in #147 consumes that domain model rather than defining a parallel extraction-result schema.

## Boundary

No malicious payloads were created or executed. No credential recovery or access-control circumvention was attempted. These results are benchmark-only and do not freeze the public E-05 schema. Rights remain fail-closed under #131.
