# P0 Gold Data Contract

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#127](https://github.com/kinderp/raiatea/issues/127)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Fixture plan: [`benchmark-fixture-plan.md`](benchmark-fixture-plan.md)
>
> Rights manifest: [`benchmark-rights-manifest.md`](benchmark-rights-manifest.md)

## 1. Purpose

E-03 needs a definition of **reference truth for benchmark comparison** that is
independent from any extraction Provider's native representation.

Gold data answers:

> What observable properties of this Source should a benchmark route preserve,
> recover or explicitly fail to recover?

It does not define Raiatea's future P0 public schema, and it is not a serialized
copy of `DoclingDocument`, Marker JSON, MinerU middle JSON, Unstructured Elements,
Pandoc AST, TEI or another Provider output.

## 2. Gold is dimension-specific

> Assertion status: `accepted-decision` inherited from the Risk List/E-01

There is no single universal “correct document JSON”. Gold is separated into
applicable dimensions:

1. content/text fidelity;
2. hierarchy/structure;
3. reading order;
4. Source Coordinates;
5. links/references;
6. figures/images/assets and associations;
7. tables;
8. formulas;
9. code/preformatted content;
10. expected Warning/Degraded Result/failure/rejection state.

E-04 may add measured resource/cost/reproducibility dimensions, but those are run
observations rather than source gold.

## 3. Gold assertion modes

> Assertion status: `provisional-decision`

Each gold assertion must declare how it should be interpreted.

### `exact`

One deterministic value or relation is expected.

Examples:

- an authored link target;
- the exact spine order in an EPUB manifest;
- literal code text where exact whitespace is part of the fixture intent.

### `normalized-exact`

Comparison is exact after an explicitly declared normalization rule.

Examples may include Unicode normalization or line-ending normalization. The
normalization rule must be fixture/benchmark-owned and visible; it must not be
whatever a Provider happens to emit.

### `tolerance-based`

The source contains a geometric/numeric reference, but small implementation or
rendering differences are valid.

Example: PDF block region overlap with a reference bbox/polygon.

E-03 records the reference geometry and tolerance type; E-04 defines or validates
numerical thresholds from representative evidence rather than inventing them in
advance.

### `relation-or-set`

Correctness is primarily a relation or membership condition rather than one
serialized tree.

Examples:

- figure ↔ caption association;
- footnote reference ↔ footnote body;
- table cell adjacency/span relations;
- acceptable link/asset resource associations.

### `ordered-relation`

Reference expresses precedence/reading order without requiring one Provider's
block identifiers.

### `human-review-required`

A domain reviewer must judge whether the output preserves the intended property.
Use sparingly and record the review rubric.

### `ambiguous-or-unresolved`

No single exact gold is defensible. E-04 must not score one arbitrary annotation
as the only truth.

## 4. Reference unit model

> Assertion status: `provisional-decision`

Gold refers to Provider-neutral **reference units**. A reference unit is an
editorial benchmark concept, not a P0 entity or API resource.

A unit can describe:

- a text span/block;
- heading;
- list/list item;
- figure/image;
- caption;
- table/table cell;
- formula;
- code block;
- link/reference;
- EPUB resource/section;
- another fixture-specific observable structure.

Each reference unit may have:

- local gold ID;
- semantic role/type for benchmark purposes;
- expected text/content when applicable;
- source coordinate reference;
- parent/child or association relations;
- order relations;
- applicable gold assertion mode;
- annotation note/uncertainty.

These fields are conceptual and must not be copied directly into the future P0
public contract without separate E-05 design.

## 5. Text/content gold

> Assertion status: `provisional-decision`

Text gold should preserve the distinctions relevant to the fixture without
forcing presentation-specific whitespace when it is not meaningful.

A fixture must state which policy applies, for example:

- exact literal text;
- normalized Unicode + normalized line endings;
- whitespace-insensitive paragraph content;
- token/word sequence where layout line breaks are non-semantic;
- code/preformatted mode where whitespace is significant.

Do not silently lowercase, strip punctuation or remove accents simply to make a
Provider look better.

Hyphenation/dehyphenation and ligature normalization require explicit policies by
fixture/profile.

## 6. Hierarchy gold

> Assertion status: `provisional-decision`

Hierarchy should be represented as source-observable relations such as:

```text
heading H1 contains section S1
S1 precedes S2
list L contains items I1..In
caption C belongs to figure F
```

Gold must avoid requiring one artificial universal document tree when the Source
itself does not uniquely imply one.

For PDF, visual headings may have hierarchy inferred from the project-created
source/template. For EPUB, authored XHTML/nav semantics can provide stronger
structural evidence.

## 7. Reading-order gold

> Assertion status: `provisional-decision`

Reading order is an ordered relation over reference units.

For a simple fixture:

```text
A < B < C < D
```

For layouts with independent regions or valid alternatives, gold may express a
partial order rather than one total sequence.

E-04 should penalize material order inversions without requiring Providers to
emit identical segmentation boundaries.

## 8. B-01 Source Coordinate gold

> Assertion status: `provisional-decision`

For born-digital PDF, applicable units may have:

- page index/label;
- reference bbox or polygon;
- coordinate origin/unit convention;
- whether the region describes glyph/text extent, logical block extent or asset
  extent;
- tolerance mode.

The gold contract explicitly separates:

```text
correct content
!=
correct source region
```

A route that returns accurate text with a wrong page/bbox has a coordinate
failure even if content fidelity is high.

E-03 does not choose a numeric overlap threshold. E-04 may evaluate IoU,
containment, centroid distance or another justified measure per fixture class.

## 9. B-02 Source Coordinate gold

> Assertion status: `provisional-decision`; the accepted invariant is only that
> reflowable EPUB must not be assigned canonical rendered page numbers

Candidate EPUB reference coordinates use package/logical semantics such as:

- package/fixture version;
- resource identifier/href;
- authored fragment ID where present;
- reference-unit anchor within the resource;
- optionally a stable structural path defined by the fixture.

Canonical rendered page numbers are forbidden as B-02 gold. The exact package/
anchor representation remains subject to E-03/E-04 evidence and must not be
promoted to a public contract by this benchmark design.

If a Provider normalizes or merges resources, its benchmark mapper/Adapter must
still demonstrate a traceable mapping back to the accepted reference semantics
or expose coordinate degradation.

## 10. Link/reference gold

Gold for authored links can include:

- source reference unit;
- href/target as authored or normalized under an explicit URI policy;
- target resource/fragment when internal;
- internal/external classification;
- backlink relation for footnotes/endnotes where applicable.

Broken/missing targets in negative fixtures are expected source facts, not
necessarily Provider failures. The expected behavior should be Warning/degraded
handling rather than inventing a valid target.

## 11. Figure/image/asset gold

Applicable reference data can describe:

- source asset identity/path;
- placement coordinate or resource location;
- caption association;
- alt text when authored;
- occurrence order;
- relation to surrounding section.

E-04 should distinguish “asset bytes extracted” from “asset correctly associated
with caption/section”.

## 12. Table gold

> Assertion status: `provisional-decision`

Tables should be defined semantically rather than by Provider HTML.

Gold may express:

- row/column count where unambiguous;
- cell textual content;
- row/column indices;
- row/column spans;
- header/data role;
- merged-cell relations;
- table caption association;
- source region/resource anchor.

For visually ambiguous tables, gold may use relation/set assertions or human
review rather than fabricate one exact grid.

## 13. Formula gold

Formula fixtures should state the intended comparison level:

- exact source text/MathML for authored EPUB math;
- normalized symbolic representation when the fixture generator provides it;
- image/region association only when semantic formula recognition is out of
  scope for that fixture;
- human-review-required for visually equivalent but serially different math
  expressions if needed.

No Provider-specific LaTeX dialect becomes canonical by default.

## 14. Code/preformatted gold

For code fixtures, gold should preserve:

- exact characters;
- line order;
- significant whitespace/indentation when intended;
- language tag only when authored/known;
- source coordinate/resource anchor.

Prose-style whitespace normalization must not be applied to code blocks.

## 15. Expected outcome gold for negative fixtures

> Assertion status: `accepted-decision` for visibility

Negative/security fixtures are evaluated against expected **state behavior**, not
normal content fidelity.

Gold can state an expected outcome class such as:

- `rejected`;
- `unsupported`;
- `requires-review`;
- `degraded-with-warning`;
- `partial-with-explicit-missing-dimension`;
- `safe-reference-only`.

The exact runtime state names remain E-05 work. E-03 records semantic intent.

Examples:

- hostile EPUB path → must not escape workspace; rejection/warning acceptable
  according to E-04 contract;
- active script → must not execute; extraction may continue only if safe;
- password/access-controlled source without supported authorized route → visible
  restricted/unsupported outcome, no guessing/bypass;
- malformed resource → no silent full-success state.

## 16. Gold provenance

Every gold dataset/version should record:

- fixture ID/version/fingerprint;
- gold version;
- annotator/generator role;
- annotation/generation date;
- source template/reference used;
- rule/rubric version;
- assertion modes used;
- known ambiguity;
- correction history;
- rights-manifest reference.

A corrected gold annotation creates a new gold version and must not silently
rewrite historical E-04 results.

## 17. Gold creation workflow

> Assertion status: `working-hypothesis`

Preferred workflow:

```text
fixture source/template
    -> generated concrete PDF/EPUB
    -> independent reference annotation
    -> review against source/template
    -> gold version + fingerprint
    -> E-04 consumes immutable fixture/gold pair
```

Where the project creates the fixture from a structured source, generator
metadata can seed gold but should not blindly become gold if the rendering/
packaging step can alter semantics or geometry.

## 18. Provider output mapping for E-04

E-04 must compare Providers through **benchmark observations** mapped from their
native outputs.

Conceptually:

```text
Provider native output
    -> benchmark-only mapping/observation layer
    -> compare to Provider-neutral gold dimensions
```

The mapping layer may know Provider schemas, but gold does not.

This prevents:

- Docling winning because gold is shaped like DoclingDocument;
- Marker winning because blocks are defined like Marker JSON;
- Unstructured winning because gold is an Element list;
- Pandoc winning because gold is a Pandoc AST.

Adapter complexity itself can later be an E-04 observation.

## 19. Segmentation mismatch policy

> Assertion status: `working-hypothesis`

Providers may segment the same source differently. Gold should therefore avoid
requiring a one-to-one block match when the meaningful property can be compared
as text, relation, order or region coverage.

E-04 should support alignment/matching between Provider observations and
reference units before scoring applicable dimensions.

The alignment algorithm belongs to E-04 and must be inspectable; E-03 only
requires that gold units carry enough content/coordinate/relationship evidence
to support alignment.

## 20. Ambiguity and adjudication

When reviewers disagree:

1. retain both interpretations temporarily;
2. identify whether the disagreement is about source ambiguity, annotation error
   or rubric ambiguity;
3. prefer changing the fixture when a supposedly atomic fixture is inherently
   ambiguous;
4. record `human-review-required` or `ambiguous-or-unresolved` when ambiguity is
   genuinely part of the source;
5. never resolve uncertainty solely to simplify automated scoring.

## 21. Machine-readable representation boundary

> Assertion status: `provisional-decision`

E-03 may later add a machine-readable fixture/gold manifest for benchmark tooling.
Such a file is an **internal benchmark contract**, not the P0 public extraction
schema.

Before adding it, review must confirm that:

- it represents reference dimensions rather than a universal document model;
- Provider mappings can target it without redefining Provider outputs;
- it can evolve/version independently from E-05;
- it does not force PDF page concepts onto EPUB;
- it supports ambiguous/tolerance/relation assertions.

## 22. Out of scope

This contract does not:

- define numerical scoring thresholds;
- define one overall benchmark score;
- define the future Normalized Representation schema;
- select a Provider;
- define Provider Adapter APIs;
- require exact block segmentation;
- authorize remote processing;
- define full manual-repair measurement protocol;
- promote the candidate first slice.

## 23. Exit criteria

Before acceptance, review must verify:

- gold is Provider-neutral;
- dimensions are independent;
- assertion modes distinguish exact/tolerance/relation/order/human/ambiguous;
- B-01 and B-02 coordinates use different correct semantics without freezing the
  concrete EPUB anchor representation;
- segmentation mismatch is supported;
- negative fixtures have expected state behavior rather than bogus quality gold;
- table/formula/code gold does not privilege one Provider serialization;
- ambiguity/version/correction provenance is explicit;
- E-04 can map heterogeneous Provider output to this gold without making the gold
  itself a hidden P0 schema.