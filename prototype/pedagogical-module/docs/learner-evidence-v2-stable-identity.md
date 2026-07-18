# Learner-evidence v2 stable identity contract

Status: design contract for issue #36. This document defines a separately versioned evidence format and does not modify learner-evidence v1.

## Version boundary

Learner-evidence v2 is a new document version. It must never be emitted under version `1`, accepted by the v1 validator, or silently substituted for a requested v1 export.

- v1 remains frozen and supported under module ID, ordered indexes, and authored step titles;
- v2 carries canonical module revision and stable pedagogical step IDs;
- validators fail closed on unsupported versions;
- coexistence is explicit: callers choose the export version they request.

## Module identity

A v2 document identifies its canonical source with:

- exact module `id`;
- exact opaque module `revision`;
- explanatory title, language, and allowlisted source metadata.

Revision values are identities, not counters. Consumers must not derive chronology, precedence, compatibility, or migration direction from numeric comparison.

## Step identity and order

Each progress entry carries:

- stable pedagogical `stepId`;
- authored `title` as an explanatory snapshot, not an identity key;
- explicit exported `index` to preserve the source revision's authored order;
- the existing observable progress fields.

Stable IDs must be unique in the document. Indexes must be canonical, contiguous, and match array positions. `currentStepId` is authoritative for current conceptual position; `currentStepIndex` is retained as a consistency check and source-order snapshot.

## Privacy boundary

V2 remains local-first and observable-only. It excludes names, email addresses, account identifiers, free-form learner notes, inferred mastery, diagnoses, disability profiles, timestamps, analytics identifiers, and cloud destinations.

Authored module IDs, step IDs, titles, labels, and source metadata must remain course-level and non-personal. Structural validation cannot detect sensitive meaning embedded by an author, so generated or imported metadata requires a separate best-effort semantic review.

## Initial increment boundary

The first v2 increment is schema, validator, examples, and documentation only.

It does not:

- change browser export controls;
- import or restore v2 evidence;
- classify compatibility across revisions;
- apply migration manifests;
- map split, merge, retirement, or replacement cases;
- mutate browser storage;
- transmit evidence to a server or LMS.

## Fail-closed validation

The v2 validator must reject:

- unsupported format or version;
- missing, boolean, fractional, zero, or negative revisions;
- malformed or duplicate stable step IDs;
- missing, duplicate, non-canonical, or non-contiguous indexes;
- inconsistent step counts;
- unknown current step IDs;
- mismatch between current step ID and current step index;
- additional non-allowlisted fields at every closed object boundary.

## Coexistence and downgrade

V2 does not define an automatic downgrade to v1. A future explicit converter may create a separate v1 document only when the current module revision and ordered titles are available and the loss of stable identity is disclosed. The original v2 document must remain unchanged.

## Deferred work

Compatibility classification, authored migration manifests, side-effect-free migration preview, and explicitly confirmed migration remain separate child issues under #19.
