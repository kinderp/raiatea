# Pilot route dashboard finding log

Issue: #63  
Pull request: #64

## Reviewed implementation

The increment adds a read-only route dashboard to the generated pilot launcher. It reuses the canonical pilot manifest and the existing module-local progress records without changing module runtime storage or evidence contracts.

## Findings

### F1 — major — resolved — route metadata could have been duplicated in dashboard code

A second hand-maintained module list would drift from the canonical pilot route.

Resolution: the builder embeds the generated public manifest in `window.RAIATEA_PILOT`; the dashboard derives IDs, titles, files, revisions, step counts, and order exclusively from that object.

### F2 — major — resolved — permissive parsing could classify malformed storage as progress

The module runtime historically falls back to an empty state for malformed records. A dashboard that accepted partial or extra-field objects could display misleading completion.

Resolution: dashboard parsing requires an exact top-level `{currentStep, steps}` object, exact step observation fields, valid non-negative attempts, booleans, a current step in range, and an exact canonical step count. Every malformed or unsupported value fails closed to `not-started` without exposing raw content.

### F3 — major — resolved — route aggregation could enumerate or mutate unrelated storage

Enumerating all `localStorage` entries or normalizing records would exceed the privacy and mutation boundary.

Resolution: the dashboard constructs only exact route keys `raiatea-progress:<module-id>`, performs `getItem` reads for those keys, never enumerates storage, and contains no write, reset, repair, migration, or deletion operation.

### F4 — minor — resolved — completion needed a narrow observable definition

A route dashboard must not infer mastery, grading, or pedagogical success.

Resolution: `locally-completed` means every canonical step has either `correct: true` or `activityCompleted: true`. Remediation remains explanatory history and does not block local completion. The UI labels the result explicitly as local completion.

### F5 — minor — resolved — recommendation could become an access gate

A next-step recommendation might accidentally disable earlier or later modules.

Resolution: static module links always remain present and enabled. Recommendation is text-only and selects the first route module not locally completed.

### F6 — minor — resolved — browser back/forward could show stale status

Returning from a module through browser navigation may restore the launcher from the back-forward cache.

Resolution: state is recomputed on initial execution, `pageshow`, visible `visibilitychange`, and relevant same-origin `storage` events. No polling or network request is introduced.

### F7 — test — resolved — builder regressions assumed the earlier manifest shape

The dashboard needs canonical `stepCount`, and the pilot now includes a dashboard script asset.

Resolution: unit tests pin the new closed manifest field set, generated file set, static fallback hooks, deterministic bytes, privacy exclusions, no-replace installation, cleanup, and CLI behavior.

## Open findings

None. GitHub Actions and two consecutive clean reviews must target one unchanged final head before merge.
