# Evidence compatibility preview finding log

Issue: #46  
Pull request: #47

## Reviewed candidate

Candidate head reviewed: `0eae0d15c85861b5aedfc098f5923692e1b0b0bf`.

## Findings

### F1 — resolved — implementation already exceeded the initial Class A-only scaffold

The branch contains one authoritative preview engine with Class A exact matching, Class B declared-lossless direct migrations, Class C declared-partial direct migrations, Class D fail-closed incompatibility, and Class E unsupported-version handling. The thin classifier module delegates to that engine rather than maintaining a second decision path.

Resolution: retain `preview_evidence_migration_v2.py` as the authoritative implementation and keep `classify_evidence_compatibility_v2.py` as a compatibility wrapper only.

### F2 — resolved — candidate generation needed an executable invariant

A preview that reports `candidateAvailable` must not emit a malformed or contextually incompatible target document.

Resolution: every generated candidate is validated structurally as learner-evidence v2 and checked for exact Class A compatibility against the target revision before it is returned.

### F3 — resolved — retired current position must remain unresolved

Selecting the next, previous, nearest, or first target step would introduce hidden migration policy.

Resolution: a retired current step yields `unresolved-retired`, `candidateAvailable: false`, and no candidate document.

### F4 — resolved — preview output must not become authorization

Classification and candidate availability could otherwise be mistaken for confirmation or persistence permission.

Resolution: the contract, result model, tests, and CLI keep preview generation read-only; no browser storage, input file, or input object is modified.

## Regression boundary

The test suite covers:

- exact Class A preview;
- Class B rename/reorder by stable ID;
- Class C introduction and retirement;
- preserved and retired current positions;
- missing, partial, mismatched, malformed, and unsupported migration contexts;
- deterministic CLI and JSON output;
- generated-candidate structural and exact contextual validity;
- side-effect freedom;
- unchanged learner-evidence v1, v2 structural, exact compatibility, and migration-manifest contracts.

No unresolved finding is known. Clean final-head review rounds must run only after GitHub Actions is green on an unchanged head.
