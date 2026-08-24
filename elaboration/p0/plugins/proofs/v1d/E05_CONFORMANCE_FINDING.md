# v1d finding — E-05 SourceCoordinate source-class conformance

Issue: #172  
Discovered by: #170 / PR #171  
Status: **resolved in the active v1d branch; acceptance pending frozen-head CI/review**

## Finding

The accepted E-05 conceptual model already requires source-class-specific coordinates: PDF geometric coordinates and EPUB logical/package coordinates must remain distinct.

The machine-readable E-05 `0.1.0` schema correctly modeled `pdf-geometric` and `epub-logical` as distinct `SourceCoordinate` variants, but the dependency-light `validate_representation()` conformance layer originally validated only the shape of the selected variant. It did not bind a populated coordinate kind to `source_ref.source_class`.

Consequently, a mutated EPUB `NormalizedRepresentationRecord` carrying a structurally valid `pdf-geometric` coordinate could pass semantic validation.

## Resolution

The canonical E-05 semantic validator now enforces the coordinate family for source classes already established by accepted evidence:

```text
B-01 / pdf  -> populated coordinate kind must be pdf-geometric
B-02 / epub -> populated coordinate kind must be epub-logical
```

The rule applies only when coordinate evidence is populated. Empty/unavailable coordinate evidence remains valid without inventing a coordinate kind. Unknown/future source classes remain conservative: the validator does not guess a family mapping that E-05 has not defined.

Direct E-05 tests cover:

- B-02 EPUB + epub-logical -> pass;
- B-02 EPUB + pdf-geometric -> fail;
- B-01 PDF + pdf-geometric -> pass;
- B-01 PDF + epub-logical -> fail;
- empty coordinate evidence -> pass;
- unknown future source class -> no invented mapping.

The v1d Extractor proof also mutates its real out-of-process B-02 EPUB result to a PDF coordinate and requires the canonical E-05 validator to reject it.

## Versioning decision

Treat this as an internal E-05 `0.1.0` **conformance bugfix**, not a serialization change:

- no JSON field was added/removed;
- no record shape changed;
- no contract id/version reference changed;
- no accepted enum/value vocabulary changed;
- the enforced invariant was already part of Accepted E-05a.

A patch-version artifact is therefore not introduced solely for this semantic-validator correction.

## Plugin/transport consequence

No Plugin API v1c transport change was required. The finding demonstrates the intended layering: a transport-valid and runtime-valid result can still fail the E-05 domain/conformance layer, and the fix belongs to E-05 rather than to the ExtractorPlugin or wire protocol.
