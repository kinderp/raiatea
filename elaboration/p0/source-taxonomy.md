# P0 Source Taxonomy

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#123](https://github.com/kinderp/raiatea/issues/123)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Elaboration gate: [`08-inception-review.md`](../../genesis/inception/08-inception-review.md)
>
> Canonical vocabulary: [`07-glossary.md`](../../genesis/inception/07-glossary.md)

## 1. Purpose

This document defines a **routing-, rights- and benchmark-oriented taxonomy**
for P0 Source Ingestion & Extraction.

It exists so Raiatea does not make three unsafe assumptions:

1. file extension is enough to describe a Source;
2. one extraction route or one quality score can represent every source class;
3. a product-facing category such as “book” or “paper” is automatically the
   correct parser/OCR/benchmark category.

The taxonomy does **not** select Providers, define a storage schema or declare
which source classes are implemented. It supplies vocabulary and classification
axes that later survey, benchmark and routing work can test.

## 2. Taxonomy model

> Assertion status: `provisional-decision`

P0 should reason about a Source through three complementary layers:

```text
Source
  -> Source Family
  -> Source Traits / Profiles
  -> Benchmark Class when evidence is required
```

### Source Family

A broad class based on the material and acquisition/extraction boundary.
Examples: paginated digital document, reflowable ebook, image capture, web
resource, code repository, audiovisual source.

### Source Trait / Profile

A non-exclusive characteristic that changes routing, risk or quality measures.
Examples: born-digital, image-only, scholarly, multilingual, active content,
complex tables, mathematical notation, sensitive/private.

One Source may have many traits.

### Benchmark Class

A deliberately bounded combination of family + traits for which P0 can define:

- representative fixtures;
- expected structures and Source Coordinates;
- quality measures;
- known failure modes;
- Provider/route comparisons;
- latency/cost/manual-repair observations;
- support or rejection criteria.

Benchmark classes are evidence units. They are not universal domain entities and
must not be inferred directly from file extensions.

## 3. Primary Source Families

> Assertion status: `provisional-decision`; family boundaries must be refined by
> survey and benchmark evidence

### SF-01 — Paginated digital document

Typical material:

- born-digital PDF;
- fixed-layout digital reports;
- exported slides or office documents represented as paginated PDF.

Important characteristics:

- explicit page geometry;
- possible native text layer;
- reading order may differ from geometric order;
- embedded fonts, images, annotations and vector graphics may exist;
- tables, equations, columns and figures may require structure-aware extraction.

Candidate Source Coordinates:

- page number/index;
- bounding box or polygon;
- object/structure identifier where available;
- logical section/paragraph anchor derived by P0.

Core quality dimensions:

- text fidelity;
- reading order;
- hierarchy;
- page-coordinate fidelity;
- tables/figures/formulas/code where present;
- embedded asset association;
- Warning/Degraded Result quality.

### SF-02 — Rasterized or scanned paginated document

Typical material:

- image-only PDF;
- scanned book/document pages bundled into a PDF;
- historical/archive scans.

Important characteristics:

- no reliable native text layer;
- OCR or multimodal extraction may be required;
- page rotation, skew, bleed-through, noise and curved pages can dominate
  quality;
- layout reconstruction and text recognition are separate failure dimensions.

Candidate Source Coordinates:

- page/index;
- image-space region/bounding box;
- OCR token/line/block region;
- derived logical anchor when stable enough.

Core quality dimensions add:

- recognition accuracy;
- page orientation/segmentation;
- region detection;
- reading order after OCR;
- uncertainty/confidence provenance where provided;
- manual correction burden.

### SF-03 — Reflowable ebook/package

Typical material:

- EPUB;
- future reflowable publication packages with explicit internal structure.

Important characteristics:

- content is distributed across package resources;
- reading order may be explicit in package metadata;
- HTML/XHTML, CSS, images, fonts and navigation documents may coexist;
- visual pagination is device-dependent and should not be treated as canonical.

Candidate Source Coordinates:

- package resource path/identifier;
- DOM/XPath-like or stable logical anchor where appropriate;
- heading/section/paragraph identifier;
- character/text offsets only when their stability is defined.

Core quality dimensions:

- reading-order preservation;
- hierarchy/navigation preservation;
- text fidelity;
- links/footnotes/citations;
- media/assets and captions;
- CSS/layout semantics only to the extent required by the declared use case.

### SF-04 — Editable office/open document

Typical material:

- DOCX;
- ODT;
- presentations;
- spreadsheets when treated as document sources rather than analytical data.

Important characteristics:

- package/container may expose semantic structure not visible in rendered pages;
- tracked changes, comments, hidden content, macros or embedded objects may
  exist;
- rendered appearance and logical document structure may disagree.

Candidate Source Coordinates:

- section/paragraph/table/cell/slide identifiers;
- package resource coordinates;
- rendered-page coordinates only when a rendering step is explicitly recorded.

Core quality dimensions:

- logical hierarchy;
- tables/lists/styles;
- comments/revisions policy;
- embedded-object handling;
- explicit handling of active content.

### SF-05 — Standalone image or photographed page

Typical material:

- JPG/PNG/TIFF/HEIC or equivalent captures;
- photographed book pages;
- photographed receipts, labels, flyers and signs.

Important characteristics:

- perspective distortion, glare, shadows and curved pages may be present;
- one image can contain more than one page/object;
- OCR/layout/VLM routes may produce different kinds of evidence.

Candidate Source Coordinates:

- image identifier;
- pixel-space region/bounding box/polygon;
- derived page/object region when segmentation is recorded.

Core quality dimensions:

- dewarp/perspective handling;
- text recognition;
- object/region segmentation;
- region-to-text/asset linkage;
- provenance of preprocessing transformations.

### SF-06 — Web or network document/resource

Typical material:

- HTML pages;
- official documentation;
- articles;
- feeds or API-provided textual resources.

Important characteristics:

- the remote resource can change after acquisition;
- retention and redistribution rights may differ from access rights;
- dynamic/active content and third-party resources may exist;
- capture time/version is part of provenance.

Candidate Source Coordinates:

- canonical/reference URL plus capture/version identity;
- DOM/semantic anchor;
- fragment identifier;
- resource-specific coordinate.

Core quality dimensions:

- main-content versus chrome extraction;
- heading/link/list/table preservation;
- capture/version reproducibility;
- dynamic-content warning;
- rights/retention boundary.

### SF-07 — Source code, repository or notebook

Typical material:

- source files;
- Git repositories;
- notebooks;
- configuration and documentation co-located with code.

Important characteristics:

- version/commit identity can be more important than current filesystem path;
- syntax and executable/active content must not be treated as ordinary prose;
- secrets or credentials may be embedded;
- repository structure and file/line coordinates matter.

Candidate Source Coordinates:

- repository identity + commit/ref;
- file path at that version;
- line/range or syntax-node coordinate;
- notebook cell identifier/index.

Core quality dimensions:

- exact text/code preservation;
- file/line coordinate stability;
- language/syntax classification;
- notebook cell/order/output distinction;
- secret/sensitive-data handling.

### SF-08 — Audiovisual source

Typical material:

- audio;
- video;
- podcast/interview;
- existing caption/transcript track.

Important characteristics:

- extraction may begin from existing captions or authorized transcription;
- time is the primary coordinate system;
- speaker attribution may be uncertain;
- audio/video bytes and transcript are different representations/layers.

Candidate Source Coordinates:

- media identity/version;
- timestamp or time interval;
- track/caption segment;
- speaker segment when supported and qualified.

Core quality dimensions:

- transcript fidelity;
- timestamp alignment;
- speaker attribution quality;
- existing-caption versus generated-transcript provenance;
- language detection and code-switching.

### SF-09 — Metadata-only or reference-only source

Typical material:

- ISBN/DOI/reference metadata;
- catalog record;
- remote Source Reference whose content is not retained;
- physical-resource metadata.

Important characteristics:

- Raiatea may know that material exists without possessing processable full
  content;
- metadata provenance matters independently from content extraction;
- discovery/access rights do not imply acquisition rights.

Candidate Source Coordinates:

- metadata field/provider record;
- bibliographic/external identifier;
- remote reference coordinate.

Core quality dimensions:

- identifier resolution;
- metadata field provenance;
- conflicting metadata handling;
- freshness/availability.

### SF-10 — Physical holding observation

Typical material:

- a printed book on a shelf;
- physical archive item;
- another catalogued physical object for which only observation/metadata exists.

Important characteristics:

- a Physical Holding is not digital full text;
- physical Location may change without changing Logical Identity;
- later scan/digital artifact relationships must be explicit and reversible.

Candidate Source Coordinates:

- holding/catalog observation;
- shelf/bookcase/container Location;
- page coordinates only after a separate digitization Source exists.

Core quality dimensions:

- identification confidence;
- Location correctness/freshness;
- metadata provenance;
- ambiguity between edition/copy/related digital representations.

## 4. Source Traits and Profiles

> Assertion status: `provisional-decision`

Traits are non-exclusive. They inform routing, quality metrics, rights handling
and fixture selection.

### Representation traits

- `born-digital` — text/structure originated digitally rather than through an
  image-recognition step;
- `image-only` — usable text layer is absent or intentionally ignored;
- `mixed-text-image` — native text and rasterized regions coexist;
- `paginated` — fixed page coordinate system is meaningful;
- `reflowable` — presentation pagination is not canonical;
- `multi-resource-package` — content spans a package/container;
- `streamed/time-based` — primary coordinate system is temporal.

### Structural complexity traits

- `multi-column`;
- `table-heavy`;
- `figure-heavy`;
- `formula-heavy`;
- `code-heavy`;
- `footnote-endnote-heavy`;
- `citation-heavy`;
- `deep-hierarchy`;
- `forms-fields`;
- `annotations-comments-revisions`;
- `embedded-objects`.

### Acquisition quality traits

- `skewed`;
- `rotated`;
- `curved-page`;
- `low-resolution`;
- `compression-artifacts`;
- `bleed-through`;
- `glare-shadow`;
- `cropped-incomplete`;
- `damaged-source`;
- `uncertain-reading-order`.

### Language traits

- `single-language`;
- `multilingual`;
- `code-switching`;
- `right-to-left`;
- `non-latin-script`;
- `specialized-terminology`.

The actual language set is metadata/evidence, not encoded into one fixed trait
list.

### Content-domain traits

These are descriptive profiles, not parser families:

- `scholarly`;
- `technical`;
- `legal-policy`;
- `educational`;
- `financial-administrative`;
- `bibliographic`;
- `everyday-visual-document`.

A scholarly paper, for example, may be an SF-01 born-digital paginated document
with `scholarly`, `citation-heavy`, `formula-heavy` and `multi-column` traits.

### Security/active-content traits

- `active-content-capable`;
- `macro-capable`;
- `script-capable`;
- `archive-container`;
- `external-resource-loading`;
- `executable-or-code`;
- `untrusted-embedded-file`.

These traits affect safe handling before extraction. They do not imply that
active content should be executed.

### Data-sensitivity traits

> Assertion status: `working-hypothesis`; concrete policy categories belong in
> the rights/data-boundary work

Candidate policy-relevant observations include:

- public/open material;
- private corpus material;
- restricted/licensed material;
- personal/sensitive content detected or declared;
- source code/configuration potentially containing secrets;
- unknown rights/sensitivity.

The taxonomy must not infer legal permission from a descriptive label.

## 5. Candidate Benchmark Classes

> Assertion status: `working-hypothesis`

Benchmark classes are deliberately smaller than the destination taxonomy.

### B-01 — Born-digital PDF baseline

Minimum profile:

- SF-01;
- native text available;
- representative single- and multi-column fixtures;
- headings, paragraphs, lists, links and embedded images;
- page coordinates required.

Additional subprofiles should cover tables/code/formulas only where fixture
coverage is explicit.

### B-02 — EPUB baseline

Minimum profile:

- SF-03;
- valid package + reading order;
- multiple XHTML resources;
- headings, paragraphs, lists, links, images and navigation;
- logical/package coordinates required rather than rendered page numbers.

### B-03 — Scanned PDF/OCR

Future candidate, not part of the first proof unless separately promoted:

- SF-02;
- image-only pages;
- clean and degraded scan subprofiles;
- OCR/layout uncertainty retained.

### B-04 — Scholarly-layout PDF

Future candidate:

- SF-01 or SF-02;
- `scholarly` plus combinations of multi-column, table-heavy, figure-heavy,
  formula-heavy and citation-heavy traits.

This must not be hidden inside the B-01 average because its failure modes are
materially different.

### B-05 — Photographed/curved book page

Future candidate:

- SF-05;
- perspective/curve/light degradation;
- OCR/region/preprocessing provenance required.

The candidate first slice remains B-01 + B-02 only as a **working hypothesis**.
This taxonomy does not promote that hypothesis to `planned` implementation.

## 6. Quality Profile Contract by Family

> Assertion status: `provisional-decision`

Every supported benchmark class should declare which dimensions are applicable
rather than inherit one universal score.

Minimum dimension families:

1. **content fidelity** — text/code/transcript or other primary content;
2. **structural fidelity** — hierarchy, reading order, lists, tables, sections;
3. **coordinate fidelity** — ability to route a result back to the Source;
4. **asset fidelity** — figures/images/media/embedded assets and associations;
5. **special-structure fidelity** — tables/formulas/code/citations when relevant;
6. **degradation visibility** — Warning/Degraded Result completeness;
7. **manual repair burden**;
8. **latency**;
9. **compute/storage/API cost**;
10. **privacy/rights suitability**;
11. **portability/Provider replaceability**.

A class may declare a dimension `not-applicable`, but must not silently score a
missing required dimension as success.

## 7. Source Coordinate Expectations

> Assertion status: `provisional-decision`

P0 needs a source-class-specific coordinate contract.

| Family | Coordinate examples | Important caveat |
| --- | --- | --- |
| SF-01/SF-02 | page + bbox/polygon + logical anchor | reading order and geometry are separate |
| SF-03 | package resource + logical/DOM anchor | rendered page number is not canonical |
| SF-04 | section/paragraph/table/cell/slide | rendered pages require an explicit rendering transformation |
| SF-05 | image + region/polygon | dewarp/preprocess transformations must remain traceable |
| SF-06 | capture/version + DOM/fragment anchor | remote page may change after acquisition |
| SF-07 | repository/commit + file + line/range/cell | current path outside that version is insufficient |
| SF-08 | media version + time interval/track | transcript segment is a derived representation |
| SF-09 | provider/record + field/reference | full-content coordinate may not exist |
| SF-10 | physical holding/location observation | page coordinate requires separate digitization source |

A Provider-specific coordinate may be stored as Raw Extraction evidence, but a
Normalized Representation should not pretend it is stable across Providers
unless benchmark evidence supports that claim.

## 8. Routing Implications

> Assertion status: `working-hypothesis`

Later routing may consider:

```text
family
+ traits
+ rights/data policy
+ requested output
+ required coordinate fidelity
+ benchmark evidence
+ cost/latency constraints
-> candidate route(s)
```

Routing must not be defined as:

```text
file extension -> one hard-coded Provider
```

Examples of decisions the later survey/benchmark should enable:

- native parse versus OCR fallback;
- document parser versus specialized scholarly route;
- local versus remote Provider;
- one route versus comparison/fallback route;
- full extraction versus metadata/reference-only treatment.

The taxonomy does not decide those choices.

## 9. Failure and Ambiguity Handling

> Assertion status: `accepted-decision` for visibility; exact representation is
> future contract work

Classification may be uncertain or multi-valued. P0 must allow:

- `unknown` family/profile;
- conflicting MIME/extension/content evidence;
- malformed container;
- incomplete source;
- uncertain native-text usability;
- mixed native/OCR regions;
- rights/sensitivity unknown;
- Provider unsupported class;
- degraded result rather than false complete success.

A Source is not rejected merely because every trait is not known. Missing facts
should remain visible so routing can choose a conservative path or request
review.

## 10. Relationship to the Document & Asset Library

> Assertion status: `accepted-decision`

P0 taxonomy is an **ingestion/benchmark classification**, not the complete
Catalog classification model.

The Library may classify material by:

- topic;
- author;
- course/project;
- language;
- user-defined categories;
- reading/translation state;
- other product metadata.

P0 taxonomy answers a different question:

> What extraction, rights, safety, coordinate and quality behavior does this
> Source require?

Changing a P0 source profile must not automatically reorganize filesystem
folders or redefine the user's logical Views.

## 11. Rights and Threat Hand-off

> Assertion status: `provisional-decision`

Source family/traits feed the rights and threat boundary but do not themselves
make legal or security decisions.

Examples:

- SF-07 + `executable-or-code` increases active-content/secrets risk;
- SF-04 + `macro-capable` requires non-executing safe inspection policy;
- SF-06 may require capture/retention/redistribution policy per remote source;
- SF-02/SF-05 may create large image intermediates with retention implications;
- SF-09 may intentionally remain reference-only;
- private/sensitive traits may force local-only processing under policy.

The authoritative architectural distinction remains:

```text
Source classification
  != Processing Authority
  != Processing Rights
  != Redistribution Rights
```

## 12. Evidence Produced by This Taxonomy

> Assertion status: `working-hypothesis`

This document advances:

- G-02 by identifying where source class and sensitivity affect rights/data
  policy;
- G-04 by defining source-class-specific benchmark units and quality dimensions;
- G-05 by defining coordinate/provenance expectations by family;
- R-05/R-06 by preventing unlike extraction classes from being averaged into a
  misleading universal score;
- R-19 by keeping routing Provider-neutral.

It does **not** satisfy those gates by itself. Later artifacts and experiments
must provide evidence.

## 13. Open Questions for Survey and Benchmark Work

- Should born-digital PDF be split into semantic-tagged versus untagged classes?
- Which PDF traits justify a specialized scholarly route rather than B-01?
- How should mixed native-text + scanned-region documents be benchmarked?
- Which Source Coordinates can be normalized across Providers without losing
  fidelity?
- Which office formats are relevant enough for early P0 support?
- Which active-content containers require pre-parser sandboxing or rejection?
- Which language/script profiles require separate quality benchmarks?
- How should handwritten content be classified and deferred?
- When is metadata-only handling preferable to full acquisition?
- Which source-class traits should be machine-detected versus user-declared?

These questions belong in evidence-driven Elaboration; they are not gaps to fill
with guesses.

## 14. Out of Scope

This taxonomy does not:

- select or rank Providers;
- define parser/OCR routing implementation;
- define a database or JSON schema;
- adopt a bibliographic Work/Manifestation model;
- define user-facing topic taxonomy;
- define legal rights conclusions;
- authorize remote processing;
- promote the PDF/EPUB first slice;
- define P1-P7 source models.

## 15. Exit Criteria for This Artifact

Before acceptance, review must verify that:

- family and trait layers are distinct;
- scholarly/technical/legal categories do not become mistaken parser formats;
- Source Coordinates are source-class specific;
- quality is source-class specific rather than one universal score;
- unknown/mixed/degraded states remain visible;
- rights/security labels do not imply permission;
- no Provider or storage schema is selected;
- B-01/B-02 remain benchmark candidates rather than implemented support.
