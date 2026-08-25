# VS1f — Deterministic catalog backup/restore and end-to-end acceptance

> Parent vertical slice: #187  
> Micro-step: #199  
> Status: implementation in progress

## Functional increment

VS1a–VS1e let Raiatea build and use a coherent local EPUB knowledge catalog.
VS1f adds durability:

> **Raiatea can export the authoritative knowledge state deterministically,
> verify its integrity, restore it into an empty catalog bound to an explicit
> Core scope, re-check the real local files, rebuild derived search state and
> reproduce the same bounded user-visible results.**

## Backup authority

The backup preserves:

- VS1b identity/Stored Instance/Location/history/reconciliation evidence;
- VS1c SourceReference + meaningful SourcePlugin provenance/rights evidence;
- VS1d E-05 content/provenance/rights evidence;
- VS1e View definitions;
- VS1e Smart Collection rules.

It deliberately does not treat as backup authority:

- VS1e search index;
- Smart Collection evaluated member cache;
- document/source bytes;
- plugin workspace files;
- opaque temporary handles/leases;
- secrets.

Derived state is rebuilt after restore.

## Restore safety

A backup is not a document backup. Restore is first-slice `empty-store-only` and
must bind to an already registered Core scope; the backup cannot provide or
widen the root.

Restored VS1b state is forced to `reconcile-required`/unverified before it can be
used. Raiatea performs a real bounded inventory against the local collection.
Only if the restored current identity/source/extraction lineage still aligns with
the physical collection does Core rebuild search, restore Views and re-evaluate
Smart Collection rules.

Failure leaves the target catalog empty.

## End-to-end exit criterion

The complete first slice must prove:

```text
scope
 -> inventory/reconciliation
 -> SourcePlugin/SourceReference
 -> RightsDecision
 -> ExtractorPlugin/provider observation
 -> Core E-05 normalization
 -> search/View/Smart Collection
 -> stale/rename/reconciliation behavior
 -> deterministic authority backup
 -> empty-store restore
 -> physical reconciliation
 -> derived-state rebuild
 -> same query/View/Smart results and preserved provenance
```

No remote Provider, filesystem mutation or source-byte backup is introduced by
this step.
