# Pilot export and summary walkthrough finding log

Issue: #65  
Pull request: #66

## Reviewed implementation

The increment adds static launcher guidance and browser verification around the existing module-local summary and unchanged learner-evidence v1 export. It does not modify module progress, export construction, dashboard state, or evidence schemas.

## Findings

### F1 — resolved — learner-facing concepts could be conflated

The launcher now explicitly distinguishes route dashboard status, the module-local observable summary, and the downloaded evidence file. Wording avoids mastery, grading, diagnosis, credential, or portfolio claims.

### F2 — resolved — guidance could have depended on JavaScript

The walkthrough is emitted as static semantic HTML in `index.html`. Module links and all instructions remain readable when dashboard JavaScript is unavailable.

### F3 — resolved — guidance could have duplicated export runtime behavior

No new export implementation was introduced. The existing `exportEvidence()` operation and v1 payload builder remain unchanged; the launcher only explains how to reach and use them.

### F4 — resolved — automatic or background download risk

Browser coverage proves that loading the launcher and module produces no download. Exactly one download occurs only after the explicit **Esporta evidenze JSON** click.

### F5 — resolved — export scope and privacy could be ambiguous

Tests pin the predictable `<module-id>-evidence-v1.json` filename, closed top-level v1 shape, current module identity, step observations, and exclusion of unrelated storage, preferences, timestamps, analytics, telemetry, and email data.

### F6 — resolved — export might mutate local state

Browser snapshots before and after export prove identical module progress, reading-setting sentinel, unrelated storage, and key inventory. The dashboard still derives the same locally-completed state and next-module recommendation after export.

### F7 — resolved — evaluator scenarios were incomplete

`PILOT.md` now covers empty, partial, remediation-used, locally-completed, summary interpretation, explicit download, filename verification, and non-destructive behavior.

### F8 — resolved — generated launcher contract needed build-level verification

Unit coverage requires the static walkthrough, accessibility heading, both module links, v1 filename explanation, non-mastery wording, and absence of automatic download or route-wide export fields.

## Open findings

None.

## Final verification pending

- GitHub Actions green on the unchanged final head;
- two consecutive clean review rounds on that same head;
- protected squash merge with expected head.
