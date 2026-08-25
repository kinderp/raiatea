# E-06 appendix — Alfred Observation delivery semantics

> Parent evidence: [`alfred-reconciliation-e06.md`](alfred-reconciliation-e06.md)  
> Issue: [#176](https://github.com/kinderp/raiatea/issues/176)

## Decision

The first Raiatea integration may consume Alfred's structured JSONL as an
**observation-evidence stream**, but it must not assume an exactly-once delivery
protocol.

The integration contract is therefore:

```text
Alfred JSONL record
    -> validate
    -> derive deterministic Raiatea Observation identity/dedupe key
    -> append/idempotently accept evidence
    -> checkpoint consumer progress when possible
    -> reconcile after any ambiguous restart/gap/truncation
```

## Why this matters

Alfred Event Model v0 provides structured record identity/sequence information
for structured consumers, but the current file writer boundary does not by
itself establish all of the delivery guarantees of a durable message broker.
A process restart, consumer restart, replayed file, partial tail, truncation or
unobserved writer gap must not cause Raiatea to:

- apply the same Location transition twice as two different logical events;
- delete a catalog entity because an intermediate record was missed;
- claim fresh observation coverage merely because the consumer reached EOF;
- treat consumer offset state as catalog truth.

## Required first-slice behavior

1. Preserve Alfred record identity/sequence when present in Observation
   provenance.
2. Make adapter acceptance idempotent for a replay of the same source record.
3. Keep the consumer checkpoint separate from catalog/source identity.
4. If the consumer cannot prove continuity — unsupported schema, malformed
   record, truncation, restart without a trustworthy checkpoint, Alfred
   `OVERFLOW`, stale-event drop, or explicit recovery failure — mark the affected
   scope `reconcile-required`/freshness unknown.
5. Restore freshness only through the bounded inventory/reconciliation rule
   defined by the main E-06 evidence, not by reaching the end of the JSONL file.
6. A future Unix-socket transport may improve latency/delivery mechanics but
   must preserve these domain invariants unless a later reviewed contract
   deliberately strengthens delivery semantics.

## Finding

| ID | Severity | Status | Finding | Resolution |
| --- | --- | --- | --- | --- |
| E06-F6 | high if ignored | resolved by adapter rule | Structured JSONL is a schema boundary, not proof of exactly-once delivery. Duplicate/replayed/missed records could otherwise create catalog drift. | Treat records as idempotent evidence, preserve source record identity/sequence, checkpoint separately, and force bounded reconciliation when continuity is uncertain. |

This finding does not require an Alfred code change for the bounded first slice.
