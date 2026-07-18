# Confirmed evidence migration application finding log

Issue: #48  
Pull request: #51

## Reviewed implementation

Initial implementation review targeted head `f34edc980100b2a6c8e511735a8fa167b6126051`. The findings below are resolved in the rewritten two-phase implementation. Final Actions and two clean review rounds must target one unchanged final head.

## Findings

### F1 — major — resolved — confirmation omitted the source module and full manifest

The initial digest accepted evidence, target, preview, and only manifest endpoint identity. A valid source-module metadata change could leave the token unchanged, and the token did not state the full current manifest content.

Resolution: the versioned canonical projection now contains complete validated evidence, source module, target module, manifest, and complete freshly recomputed preview.

### F2 — major — resolved — malformed direct inputs could escape as raw exceptions

The initial application called the classifier before structurally validating the supplied dictionaries. Missing fields or wrong types could therefore surface `KeyError` or `TypeError`.

Resolution: preparation and application deep-copy and structurally validate all current inputs in fixed evidence/target/source/manifest namespace order before classification.

### F3 — major — resolved — caller-supplied preview was trusted during confirmation creation

The initial public digest helper accepted an arbitrary preview object. This weakened the claim that confirmation was produced by the authoritative current transition.

Resolution: `prepare_migration` recomputes the authoritative preview from current validated inputs and is the only public token-creation boundary. Application repeats that preparation before comparison.

### F4 — minor — resolved — public contracts were not explicitly versioned or pinned

The initial result used a raw digest and tests did not pin a closed public shape.

Resolution: `contractVersion: 1`, `raiatea-confirm-v1:<sha256>`, `sha256:<candidate>`, and exact preparation/application key-set tests define the closed contract.

### F5 — minor — resolved — normative stale-input, malformed, privacy, and deep-copy rows were incomplete

The initial tests covered basic Class B/Class C success, cancellation, one stale digest, exact refusal, and retired current position.

Resolution: regressions now cover complete source/target binding, retired-only evidence changes that leave the candidate unchanged, malformed/incomplete context, invalid manifest changes, deterministic token format, candidate validity, privacy exclusions, nested deep-copy independence, and no mutation on failure. The complete existing test suite remains the freeze for all prior contracts.

## Open findings

None. GitHub Actions and two consecutive clean review rounds are still required on the unchanged final head before merge.
