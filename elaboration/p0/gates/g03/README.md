# G-03 conservative identity/reconciliation proof

> Evidence child: [#179](https://github.com/kinderp/raiatea/issues/179)  
> E-07 parent: [#178](https://github.com/kinderp/raiatea/issues/178)  
> P0 parent: [#106](https://github.com/kinderp/raiatea/issues/106)

This directory contains a **dependency-light risk-reduction proof** for the
G-03 first-slice planning gate. It is not a production catalog model, public
schema, database design or automatic deduplication engine.

## Invariants under proof

```text
path / pathname          != Logical Identity
filesystem identity      != universal Logical Identity
exact duplicate bytes    != same Stored Instance
Observation              != mutation/purge authority
offline / lost scope     != deletion
Location disappearance   != logical entity deletion
ambiguous evidence       != permission to guess
```

The proof deliberately emits conservative outcomes with inspectable evidence
basis and `destructive=false`.

## Relationship to E-06 / Alfred

E-06 established that Alfred owns filesystem observation facts while Raiatea
owns logical identity, Location history and reconciliation. The fixtures here
exercise the Raiatea side of that boundary without requiring an Alfred process:

- rename/move-like path pairs are conservative Location transitions;
- delete is Location-level evidence;
- lost/offline scope becomes `unavailable-or-unknown`;
- cross-filesystem/copy+delete ambiguity remains unresolved unless stronger
  evidence exists;
- device/inode-like values may support a bounded transition but never become a
  universal catalog identity.

## Cases

`test_reconciliation_proof.py` covers:

1. exact duplicate bytes at different paths and distinct Stored Instance ids;
2. rename with retained Location history;
3. move across directories;
4. same path with changed bytes;
5. copy with exact bytes but distinct Stored Instance candidate;
6. multiple exact-byte candidates after delete;
7. one exact-byte candidate without filesystem continuity;
8. offline/lost observation scope;
9. explicit Location delete;
10. changed-byte and conflicting-filesystem-identity transition negatives.

No path similarity, list order, fuzzy content score, LLM or bibliographic
heuristic is used to resolve ambiguity.

## Run

From this directory:

```bash
python -m unittest test_reconciliation_proof.py -v
```

The dedicated GitHub Actions workflow runs the same proof on Linux and Windows
with Python 3.10 and 3.12.

## Promotion boundary

Passing this proof contributes executable evidence to G-03. It does not by
itself authorize the first slice, select a production catalog representation,
permit destructive merge, or enable filesystem organization.
