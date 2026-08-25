# G-07 catalog durability and local authority proof

> Evidence child: [#183](https://github.com/kinderp/raiatea/issues/183)  
> E-07 parent: [#178](https://github.com/kinderp/raiatea/issues/178)  
> P0 parent: [#106](https://github.com/kinderp/raiatea/issues/106)

This directory contains a **dependency-light proof only** for the G-07
first-slice planning gate. It demonstrates two bounded properties before product
implementation:

1. catalog state can be exported and restored deterministically with integrity
   and version checks;
2. external/UI/API-shaped requests cannot mint a broader filesystem scope or
   turn observation/read authority into mutation authority.

It is not a production database, backup format, authentication/ACL framework or
OS sandbox.

## Durability invariants

```text
corrupt backup          != partial best-effort restore
unsupported version     != guessed compatibility
missing critical state  != acceptable backup
input record order      != backup byte order
Smart Collection rule   != derived member cache
```

`BoundedCatalogState` preserves proof-level:

- logical item identity;
- Locations and availability;
- provenance source references;
- View definitions;
- Smart Collection **rules**.

Smart Collection current members and search indexes are intentionally not
backup authority in this proof: G-06 established they are derived from rules +
a fresh catalog revision and can be recomputed. Document bytes are also outside
this catalog-state backup proof.

`export_catalog()` canonicalizes record ordering and JSON encoding, then stores
a SHA-256 of the canonical payload beside an explicit proof schema version.
`restore_catalog()` rejects unsupported versions, closed-shape violations,
integrity mismatch, referential invalidity and noncanonical payload state before
returning a restored catalog.

## Authority invariants

```text
Core configuration      -> ScopeGrant(root, minimal capabilities)
external request         -> existing scope_id + path + capability
external request         -X-> root override / secret / document bytes
observe/read             -X-> write / move / delete / organize
```

The proof uses POSIX lexical paths deliberately so the same authority semantics
run on Linux and Windows CI. Containment compares path components, not string
prefixes, so `/library2` does not fall inside `/library`; `..` traversal is
rejected before containment.

The proof has no filesystem mutation function. Authorization returns a pure
allow/deny decision only.

### Important residual boundary: symlinks and real OS access

Lexical containment is **not** proof that following a real filesystem symlink is
safe. A product implementation must bind authorized roots/handles using an
OS-aware broker strategy that prevents symlink/reparse-point escape (for
example, appropriately resolved Core-issued handles or equivalent safe-open
semantics) before reading content. E-06 already keeps filesystem observation
scope separate from mutation authority.

Therefore G-07 evidence is bounded: it proves Core-vs-request authority
semantics and fail-closed lexical scope handling; it does not claim a production
OS sandbox.

## Run

From this directory:

```bash
python -m unittest test_durability_authority_proof.py -v
```

The dedicated Actions workflow runs compile + tests on Linux and Windows with
Python 3.10 and 3.12.

## Explicitly absent

- production storage engine;
- backup encryption, retention, rotation or remote replication;
- authentication/SSO;
- OS ACL/sandbox implementation;
- secrets delivery;
- write/move/delete operations;
- automatic organization;
- vertical-slice promotion.

Passing this proof contributes bounded evidence to G-07. E-07 must still record
its residual security/durability risks before any separate promotion decision.
