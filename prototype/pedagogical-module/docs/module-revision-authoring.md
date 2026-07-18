# Canonical module revision and step identity authoring rules

Status: implementation contract for issue #29. This document applies to the canonical pedagogical-module model and does not change learner-evidence v1.

## Module revision

Every canonical module must declare a top-level `revision` field.

- `revision` is a positive JSON integer.
- `true`, `false`, zero, negative values, fractions, strings, and missing values are invalid.
- Revision identifiers are publication identities, not mutable counters: once a `(module id, revision)` pair is published, it must not be reused for different authored content.
- The integer representation does not define numeric, chronological, semantic, or precedence ordering; consumers compare revision identity only through exact equality or an authored contract.
- The initial revision for the existing examples is `1`.

## Stable pedagogical step identity

Every item in `steps` must declare an `id`.

- The syntax is lowercase ASCII letters, digits, and hyphens: `^[a-z0-9-]+$`.
- IDs must be unique within one module.
- An ID names the durable pedagogical responsibility of the step, not its title, position, visual node, quiz wording, or implementation detail.
- Renaming or reordering a step keeps its ID when the pedagogical responsibility remains the same.
- A newly inserted responsibility receives a new unique ID.
- Split, merge, retirement, and migration behavior remain outside this increment and must fail closed until a later explicit contract is implemented.

Step IDs are independent from concept IDs and visual primitive IDs. Reusing the same text across those namespaces is not prohibited by this increment, but authors should avoid accidental semantic ambiguity.

## Learner-evidence v1 boundary

This model change must not alter the exact learner-evidence v1 document shape or behavior.

- v1 exports do not add `revision` or `stepId`.
- v1 compatibility continues to compare module ID, step counts, ordered indexes, and ordered authored titles.
- v1 restore continues to preview and explicitly replace compatible browser-local progress without migration.
- Generated HTML may contain the canonical module fields because it embeds module JSON, but the evidence exporter must continue to select only the existing v1 allowlist.

Tests for issue #29 must prove this boundary explicitly rather than relying only on schema validation.

## Validation expectations

Validation errors should identify exact paths where practical. The implementation must reject:

- missing, boolean, non-integer, zero, or negative `revision`;
- missing or malformed `steps[i].id`;
- duplicate step IDs within one module.

All canonical examples must validate and build with revision `1` and reviewed durable step IDs before the pull request can leave draft state.
