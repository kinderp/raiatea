# P0 Benchmark Fixture Plan

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 1.0.0
>
> Last reviewed: 21 August 2026
>
> Accepted through: [PR #128](https://github.com/kinderp/raiatea/pull/128)
>
> Parent issue: [#127](https://github.com/kinderp/raiatea/issues/127)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Previous evidence: [E-02 technology survey](technology-survey.md)
>
> Rights companion: [`benchmark-rights-manifest.md`](benchmark-rights-manifest.md)
>
> Gold companion: [`gold-data-contract.md`](gold-data-contract.md)

## 1. Purpose

E-03 defines the rights-safe fixtures that E-04 will use to measure extraction
routes. The plan exists to make the benchmark **Provider-neutral, discriminating,
reproducible and source-class specific** before any numerical comparison begins.

It does not select Docling, Marker, MinerU, Unstructured, Tika, PaddleOCR,
Pandoc or another Provider. It also does not promote the PDF/EPUB candidate first
slice from `working-hypothesis` to `planned` implementation.

## 2. Fixture design principles

> Assertion status: `accepted-decision` where inherited from E-01/E-02;
> concrete fixture set is `working-hypothesis`

1. **Measure source classes, not file extensions.** A fixture belongs to B-01 or
   B-02 because of its source semantics and declared traits.
2. **Use minimal discriminating fixtures.** Prefer several focused fixtures over
   one giant document whose failure cannot be localized.
3. **Keep integrated fixtures too.** After atomic traits are covered, one or more
   composite fixtures may test interactions such as multi-column + figures +
   links.
4. **Separate baseline quality from failure/security behavior.** Malformed,
   encrypted, active-content and hostile-path fixtures are not averaged into
   ordinary content-quality results.
5. **Gold data is Provider-neutral.** No expected result is defined in terms of
   `DoclingDocument`, Marker JSON, MinerU middle JSON, Unstructured Elements,
   Pandoc AST or another Provider-native schema.
6. **Coordinates are source-class specific.** B-01 may use page geometry; B-02
   must use package/resource/logical anchors and must not invent canonical page
   numbers.
7. **Rights are part of the fixture.** A fixture without sufficient provenance,
   Processing Rights and Redistribution Rights evidence cannot enter the public
   benchmark package.
8. **Reproducibility is explicit.** Fixture content, generator inputs and gold
   references are versioned and fingerprinted where applicable.
9. **Ambiguity remains visible.** Gold data may state that several outcomes are
   valid or that human judgment is required rather than manufacture false
   precision.

## 3. Fixture identity convention

> Assertion status: `provisional-decision`

E-03 uses editorial fixture identifiers to make discussion and E-04 manifests
stable. They are not public API identifiers.

Suggested form:

```text
B01-PDF-<NNN>
B01-PDF-NEG-<NNN>
B02-EPUB-<NNN>
B02-EPUB-NEG-<NNN>
```

Each concrete fixture version must later have:

- fixture ID;
- fixture version;
- content fingerprint;
- Source Family and Source Traits;
- creation/origin provenance;
- rights-manifest entry;
- gold-data version;
- intended dimensions;
- explicitly excluded dimensions;
- expected normal/degraded/rejected outcome class.

## 4. B-01 — born-digital PDF fixture matrix

> Assertion status: `working-hypothesis`

B-01 represents born-digital paginated PDF. Image-only/scanned PDF is B-03 and
scholarly-heavy PDF is B-04 unless a specific B-01 fixture deliberately isolates
a shared structure such as a table.

| Fixture | Primary discriminating purpose | Key traits | Main gold dimensions | Excluded from baseline? |
| --- | --- | --- | --- | --- |
| `B01-PDF-001` | clean native-text control | born-digital, paginated, single-column | text, hierarchy, page coordinates | no |
| `B01-PDF-002` | multi-column reading order | born-digital, multi-column | reading order, text, coordinates | no |
| `B01-PDF-003` | headings/lists/links | deep-hierarchy, links, lists | hierarchy, ordered blocks, link targets | no |
| `B01-PDF-004` | figure/caption association | figure-heavy | asset identity, caption relation, coordinates | no |
| `B01-PDF-005` | table structure | table-heavy | rows/cells/spans, reading order, region | no |
| `B01-PDF-006` | formula + code/preformatted | formula-heavy, code-heavy | formula/code content, block type, order | no, but score dimensions separately |
| `B01-PDF-007` | mixed/defective native text | mixed-text-image or bad text layer | route warning, native/OCR decision evidence, text | separate subprofile |
| `B01-PDF-008` | integrated realistic page | multi-column + figure + links/list | cross-feature ordering/associations | no; report separately from atomic fixtures |
| `B01-PDF-NEG-001` | malformed/corrupt document | malformed | visible failure/degraded state | yes |
| `B01-PDF-NEG-002` | access-controlled input without supported authorized route | password/access-controlled | restricted/unsupported state; no bypass | yes |

### 4.1 B-01 coordinate expectations

Gold coordinates should describe source evidence rather than Provider output.
For applicable blocks:

```text
page index / page label where meaningful
+ reference region (bbox or polygon)
+ coordinate system definition
+ tolerance semantics defined by E-04
```

E-03 records reference geometry. E-04 will decide measured tolerances after
baseline inspection; E-03 must not invent one universal numeric IoU threshold.

Text fidelity and coordinate fidelity are independent. A Provider can extract
correct words while pointing them to the wrong region.

### 4.2 B-01 reading order

Reading-order gold is an ordered relation over reference units, not a dump of one
Provider's block IDs. Atomic fixtures should minimize genuinely ambiguous orders.
Where multiple orders are defensible, gold data must encode alternatives or mark
human review required.

## 5. B-02 — EPUB fixture matrix

> Assertion status: `working-hypothesis`

B-02 represents reflowable EPUB/package semantics. Visual pagination is not
canonical and must not be rewarded as though the EPUB were a PDF.

| Fixture | Primary discriminating purpose | Key traits | Main gold dimensions | Excluded from baseline? |
| --- | --- | --- | --- | --- |
| `B02-EPUB-001` | package/spine control | multi-resource-package, reflowable | manifest/spine order, text, resource anchors | no |
| `B02-EPUB-002` | nested navigation | deep-hierarchy, navigation | hierarchy/nav tree, target anchors | no |
| `B02-EPUB-003` | cross-resource/internal/external links | links | link target identity and source anchor | no |
| `B02-EPUB-004` | images/captions/alt | figure-heavy | asset relationship, caption/alt, resource path | no |
| `B02-EPUB-005` | footnotes/endnotes | footnote-endnote-heavy | backlink/target relations and order | no |
| `B02-EPUB-006` | tables/code/MathML semantic content | table/formula/code traits | semantic structure/content | no; dimensions separately |
| `B02-EPUB-007` | integrated multi-chapter book-like package | multi-resource + nav + assets + links | spine/nav/anchors/relations | no; report separately |
| `B02-EPUB-NEG-001` | scripted/active content | script-capable | non-executing inspection + warning/policy state | yes |
| `B02-EPUB-NEG-002` | unsafe package path entry | archive-container, hostile path | fail-closed path validation | yes |
| `B02-EPUB-NEG-003` | malformed/missing referenced resource | malformed/incomplete | visible degraded/failure state | yes |

### 5.1 B-02 Source Coordinates

Reference coordinates must be package/logical coordinates such as:

```text
EPUB package identity/version
+ resource href/identifier
+ stable fragment / element anchor where authored
+ optional structural path within the resource
```

A rendered page number is explicitly **not** canonical B-02 gold. Character
indices may be recorded only where their normalization/stability is defined.

### 5.2 Active-content fixture

The active-content fixture must be inert/minimal and designed to prove that the
benchmark harness and Provider route do not execute scripts/resources as a side
effect of extraction. It must not contain harmful payloads or network-dependent
behavior.

### 5.3 Unsafe-package fixture

The path-safety fixture should contain only the minimum package metadata needed
to express an unsafe member/path reference. The expected outcome is confinement,
rejection or explicit Warning according to the later E-04 contract — never a
write outside the benchmark workspace.

## 6. Cross-class negative and policy fixtures

> Assertion status: `working-hypothesis`

Negative fixtures test visible behavior rather than extraction quality averages.
Candidate classes:

- malformed source/container;
- encrypted/password/access-controlled source without a supported authorized
  route;
- missing or dangling referenced resource;
- active-content-capable source;
- unsafe path/archive member;
- unsupported Source Trait;
- deliberately ambiguous structure where exact gold would be dishonest.

Expected outcomes may include:

- rejected/unsupported;
- requires-review;
- degraded result with explicit Warning;
- partial result with missing dimension;
- safe metadata/reference-only handling.

`unknown` or `partial` must never be silently scored as full success.

## 7. Fixture composition strategy

> Assertion status: `provisional-decision`

E-03 should maintain three levels:

### Level A — atomic fixtures

Smallest practical source isolating one dimension. Used to diagnose route
behavior and Adapter mappings.

### Level B — interaction fixtures

Combine two or three traits that commonly interact, for example multi-column +
figure/caption.

### Level C — realistic composite fixtures

Longer multi-page/multi-resource sources that approximate real documents while
remaining entirely rights-safe and reproducible.

E-04 must retain per-fixture/per-dimension results so Level C does not hide why a
route failed.

## 8. Fixture creation strategy

> Assertion status: `provisional-decision`

Preferred order:

1. project-created source templates and assets;
2. deterministic generated/synthetic fixtures whose inputs are distributable;
3. verified public-domain/open-license sources when they cover a phenomenon that
   would be artificial to recreate;
4. narrowly-scoped third-party material only when the rights manifest explicitly
   supports processing and intended redistribution.

Private/licensed books available to a maintainer can be useful for private
exploratory comparison, but are not part of the distributable E-03 baseline and
must not enter CI/public artifacts by accident.

Generated fixture sources should live separately from the generated PDF/EPUB so
regeneration is auditable.

## 9. Generator reproducibility

> Assertion status: `provisional-decision`

A generated fixture should record:

- source template version;
- generator/tool identity and version;
- fonts/assets and their rights basis;
- relevant rendering options;
- deterministic seed when randomness exists;
- output fingerprint;
- platform-dependent variation if any.

E-03 does not select the final fixture-generator stack. A simple deterministic
HTML/Markdown/LaTeX/EPUB construction route is preferable to a complex toolchain
when it can express the test condition faithfully.

## 10. Dimension coverage matrix

Each fixture must declare one of:

- **target** — designed to measure this dimension;
- **observed** — may be recorded but is not a primary discriminator;
- **not-applicable** — dimension is not meaningful for this source;
- **excluded** — intentionally not scored because the fixture is a failure,
  security or later-class case.

Dimensions available to E-03/E-04 include:

1. content fidelity;
2. hierarchy;
3. reading order;
4. Source Coordinate fidelity;
5. links/references;
6. figures/assets and associations;
7. tables;
8. formulas;
9. code/preformatted content;
10. warning/degradation/failure visibility;
11. manual repair observations;
12. latency/resources/cost — measured only in E-04;
13. reproducibility/version behavior — measured only in E-04.

No fixture or benchmark produces one authoritative total score.

## 11. Public versus private benchmark layers

> Assertion status: `accepted-decision` for boundary; concrete packaging future

The benchmark design must support at least:

```text
PUBLIC/REDISTRIBUTABLE BASELINE
  project-created + verified distributable sources/gold
  safe for repository/CI publication

PRIVATE EXPLORATORY EXTENSION
  optional user-owned/licensed Sources when policy permits
  never required to reproduce the public benchmark
  never uploaded/published by default
```

Private extension results may reveal missing fixture traits. The response is to
create a rights-safe public fixture reproducing the phenomenon where practical,
not to publish the private Source.

## 12. Hand-off to E-04

E-04 should receive from E-03:

- accepted fixture list/version;
- source/gold fingerprints;
- Source Family + traits;
- rights eligibility;
- expected coordinate semantics;
- per-fixture target/excluded dimensions;
- gold-data reference and certainty type;
- expected failure/degradation outcome for negative fixtures;
- route-independent comparison inputs.

E-04 remains responsible for:

- executing routes;
- measurement methods/thresholds;
- resource/cost capture;
- manual-repair protocol;
- Provider/version execution manifests;
- per-dimension results and route decisions.

## 13. Out of scope

This plan does not:

- create numerical benchmark results;
- select a Provider;
- define a public P0 extraction schema;
- define E-04 thresholds;
- include B-03/B-04/B-05 as baseline classes;
- authorize remote Provider processing;
- include proprietary/private sources in the distributable corpus;
- implement production routing/Adapters;
- promote the candidate first slice.

## 14. Exit criteria

Before acceptance, review must verify:

- B-01 and B-02 cover the accepted discriminating traits;
- later classes are not hidden inside baseline averages;
- Source Coordinates are PDF-appropriate for B-01 and package/logical for B-02;
- failure/security fixtures remain outside normal quality averages;
- fixture design is Provider-neutral;
- realistic composite fixtures do not replace atomic diagnostics;
- public/private benchmark layers are explicitly separated;
- fixture provenance, rights and reproducibility requirements are actionable;
- E-04 receives sufficient information to design measurements without reopening
  the basic fixture taxonomy.
