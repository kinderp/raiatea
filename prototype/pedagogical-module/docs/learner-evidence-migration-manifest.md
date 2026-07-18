# Learner-evidence migration manifest contract

Status: implementation contract for issue #41. This increment defines a closed, directional, declarative manifest format and validator. It does not classify evidence, preview a migration, or mutate progress.

## Purpose

A migration manifest records one authored transition between two exact canonical revisions of the same module. It names source and target identities explicitly and describes stable-step coverage without deriving direction from revision values.

## Identity boundary

- source and target module IDs must be exactly equal;
- source and target revisions must be distinct exact identities;
- revisions are opaque: numeric representation does not imply chronology, precedence, adjacency, or migration direction;
- direction exists only because the manifest labels one endpoint `source` and the other `target`.

## Initial operation vocabulary

The first contract supports only operations whose evidence semantics do not require invented aggregation or duplication policy:

- `preserve`: one source stable step ID maps one-to-one to one target stable step ID;
- `retire`: one source stable step ID has no target evidence destination;
- `introduce`: one target stable step ID has no source evidence origin.

A stable-ID-preserving title rename uses `preserve`. Reorder is represented by the target revision's authored order and is not a mapping operation.

Split, merge, fan-out, fan-in, aggregation, evidence synthesis, semantic matching, and LLM inference are unsupported and fail closed.

## Coverage invariants

The manifest declares complete source and target stable-ID inventories and complete operation coverage.

- every source ID appears exactly once in `preserve` or `retire`;
- every target ID appears exactly once in `preserve` or `introduce`;
- preserve mappings are one-to-one;
- operation arrays are deterministic and duplicate-free;
- IDs use the canonical lowercase/digit/hyphen syntax;
- all object boundaries are closed.

## Validation boundary

The standalone validator checks only manifest-internal structure and invariants. It does not prove that either revision was published, that inventories match external module files, or that the manifest is the selected path for an evidence document. Those contextual checks belong to later increments.

Validation is side-effect free. It never reads browser storage, changes evidence, selects a compatibility class, or applies a migration.

## Deferred work

- contextual validation against immutable source and target module revisions;
- compatibility classification and path selection;
- human-readable migration preview;
- explicit confirmation and atomic application preserving the original evidence;
- browser v2 export/import and restore;
- split/merge policies.
