# Evidence compatibility preview finding log

Issue: #46  
Pull request: #47

## Reviewed implementation

Implementation reviewed through head `5687037e50d9c6396f81cd05a6c89eee9f135ec9`. Final clean-review rounds must use the unchanged final head after this finding-log update and any remaining documentation-only changes.

## Findings

### F1 — major — resolved — non-object JSON could escape namespaced validation

The initial loader asserted that parsed evidence and target JSON were objects. Arrays, strings, numbers, and `null` are valid JSON values and could therefore raise `AssertionError` instead of a deterministic input error.

Resolution: raw values are inspected without assertions; supported-version objects proceed to the existing structural validators, and non-object values fail under the exact `evidence` or `targetModule` namespace. Boundary regressions cover array and null inputs.

### F2 — major — resolved — module loading bypassed canonical layout resolution

The initial preview loader validated raw module dictionaries directly. That skipped the canonical loader's declarative-layout resolution and could reject an otherwise valid canonical module using `visual.type = layout`.

Resolution: source and target paths now use `validate_module_v2.load_and_validate`. A regression classifies the buildable declarative query/key/value module without bypassing its layout compiler.

### F3 — major — resolved — incomplete optional migration context was checked too late

An exact evidence/target pair could return Class A before noticing that only one of `sourceModule` and `manifest` had been supplied.

Resolution: invocation shape is validated before exact classification. Source module and manifest are an inseparable optional pair for every classification, including Class A.

### F4 — minor — resolved — generated candidate lacked an implementation invariant

Candidate validity was previously demonstrated only by tests after the classifier returned it.

Resolution: candidate construction now runs the learner-evidence v2 structural validator and the existing Class A exact contextual checker against the target before the candidate can be returned. Failure is an internal invariant violation rather than an invalid public result.

### F5 — minor — resolved — human output did not state the no-mutation boundary

A successful preview and candidate could be mistaken for an applied migration.

Resolution: the human-readable CLI always prints that the result is preview-only and that no evidence file or learner state was changed. JSON output retains explicit `candidateAvailable` and never writes a file or storage record.

### F6 — minor — resolved — overlapping CLI implementations appeared on the branch

A second loader/CLI temporarily duplicated unsupported-version, structural-validation, and rendering logic, risking divergent behavior.

Resolution: `preview_evidence_migration_v2.py` is the single authoritative engine, loader, and CLI. `classify_evidence_compatibility_v2.py` is only a compatibility wrapper, and all loader/CLI tests target the authoritative implementation.

### F7 — resolved — retired current position must remain unresolved

Selecting a nearest, previous, next, or first target step would introduce hidden migration policy.

Resolution: a retired current step yields `unresolved-retired`, `candidateAvailable: false`, and no candidate document.

## Regression boundary

The test suite covers:

- exact Class A preview;
- Class B title changes and reorder by stable ID;
- Class C introduction, retirement, and replacement represented as retire plus introduce;
- preserved and retired current positions;
- missing, incomplete, mismatched, malformed, non-object, and unsupported migration contexts;
- canonical declarative-layout resolution;
- deterministic human and JSON CLI output and exit status;
- generated-candidate structural and exact contextual validity;
- privacy-safe allowlisted result data and side-effect freedom;
- unchanged learner-evidence v1, v2 structural, exact compatibility, standalone manifest, and contextual-manifest contracts.

## Open findings

None. GitHub Actions must be green and two consecutive clean review rounds must run on the same unchanged final head before merge.
