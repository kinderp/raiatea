# P0 vertical slice 1 prototype

> Parent promotion: [#187](https://github.com/kinderp/raiatea/issues/187)  
> Accepted VS1a: [#188](https://github.com/kinderp/raiatea/issues/188) / PR [#189](https://github.com/kinderp/raiatea/pull/189) / `0bd70df`  
> Current micro-step: [#190](https://github.com/kinderp/raiatea/issues/190) — VS1b / PR [#191](https://github.com/kinderp/raiatea/pull/191)  
> Status: **VS1b implementation frozen for review**

This directory contains the executable product-prototype path for the first
promoted Raiatea vertical slice.

The first source route selected by #187 is local B-02 EPUB through the accepted
`direct-epub-stdlib` route. VS1a established Core-owned authority and durable
state. VS1b adds filesystem Observation and conservative inventory/reconciliation.
Extraction itself remains VS1d.

## Functional progression

The vertical slice is intentionally built as a sequence of user-observable
capabilities rather than as one large hidden implementation:

```text
VS1a  authorize + read/store safely
  ↓
VS1b  know what EPUB files exist and whether the catalog is trustworthy
  ↓
VS1c  expose the selected local source through the accepted SourcePlugin path
  ↓
VS1d  extract EPUB structure/content and persist E-05 processing/provenance
  ↓
VS1e  search and build deterministic Views / Smart Collections
  ↓
VS1f  export, restore and verify the whole end-to-end slice
```

## Implemented VS1a boundary

### Core-owned scope registry

`ScopeRegistry` is the only VS1a surface that binds a filesystem root. A scope:

- has a Core-chosen `scope_id`;
- requires an absolute existing directory;
- rejects a symlink/reparse root or a symlink/reparse component in the configured
  root path;
- is limited to `observe` and `read-for-processing` capabilities;
- exposes only `scope_id` + capabilities in its public record — never the host
  root path.

External asset operations receive an existing `scope_id` and a strict relative
POSIX-style asset name. Absolute paths, `..`, backslashes, Windows drive/ADS
colon syntax, empty components and `.` components fail closed.

### Safe source reads

Read handles reuse the accepted Plugin Runtime v1b shape:

```text
handle_id
lease_id
access = read
media_type
byte_length
fingerprint = sha256:...
expires_at
```

The public record is closed: missing or extra fields are rejected and no host
path/root field is allowed.

On **POSIX/Linux**, the scope root is opened once as a directory descriptor.
Every intermediate component is opened relative to the previous descriptor with
`O_DIRECTORY | O_NOFOLLOW`; the final file is opened with `O_NOFOLLOW` and must
be regular.

On **Windows**, VS1a opens the requested file through Win32 `CreateFileW`, rejects
a final reparse point/directory, obtains the normalized final path from the
**opened handle** through `GetFinalPathNameByHandleW`, and compares that path
component-wise against the canonical Core root captured at registration.

Issuing a handle fingerprints the bytes. Reading through the handle later opens
the file again through the same safe boundary and requires the current byte
length + SHA-256 to match the issued identity; replacement after issuance fails
closed as `asset-content-changed`.

### Core-owned write-once outputs

Output paths are never caller supplied. Core generates an opaque handle and an
internal filename under a Core-owned output root. Lease, media type, byte budget
and no-overwrite semantics are enforced. Completed output is later reopened
through the safe boundary and revalidated by length + SHA-256.

### Minimal internal catalog state store

`CatalogStateStore` persists one opaque JSON-object payload inside an internal
envelope with:

- internal store version;
- monotonically increasing revision;
- canonical JSON serialization;
- SHA-256 of the canonical payload;
- atomic temporary-file + replace write;
- post-write verification;
- symlink/reparse rejection for the Core-owned state path;
- expected-revision stale-write guard.

VS1a has **one Core process / one store owner**. It does not claim an atomic
cross-process or distributed state protocol.

## VS1b — Observation, inventory and reconciliation

### What VS1b adds functionally

Before VS1b Raiatea could read an explicitly selected file safely, but it did not
yet maintain a trustworthy picture of a collection while files were created,
changed, renamed, moved or removed.

VS1b adds that catalog-awareness layer:

```text
Alfred Event Model v0 JSONL
        ↓
AlfredObservationAdapter
        ↓
Raiatea Observation evidence
        ↓
stream continuity / freshness state
        ↓
bounded EPUB inventory
        ↓
conservative Stored Instance + Logical Identity candidates
        ↓
Location history + availability state
```

### Alfred is the observer, Raiatea owns catalog meaning

VS1b is pinned to Alfred evidence snapshot
`9e0e59e4232b8b173f1ae44a409c7d06f72f6c02` and consumes the actual structured
JSONL v0 shape emitted by that snapshot.

Raiatea does **not** add another watcher. Alfred owns filesystem Observation;
Raiatea decides what those observations mean for catalog state.

Current semantic mappings include:

| Alfred record | Raiatea meaning |
| --- | --- |
| `FILE_CREATED` / `DIR_CREATED` | a Location appeared; inventory must verify it |
| `FILE_READY` | content is ready evidence; downstream processing remains policy-gated |
| `FILE_MODIFIED` | content may have changed; inventory/reprocessing required |
| `FILE_DELETED` / `DIR_DELETED` | Location disappeared; do not delete logical history |
| rename / move / relocate | preserve candidate identity + Location history, then verify |
| `OVERFLOW` | observation stream is incomplete; catalog cannot be claimed fresh |
| stale/lost-scope diagnostics | observer coverage is uncertain; retain entities and require reconciliation |
| recovery-end diagnostics | observer recovered, but catalog equality is **not** implied |

Normalized-raw records and session metadata can contribute stream/checkpoint
evidence but never become a second catalog-truth path.

### Deterministic bounded EPUB inventory

VS1b recursively inventories `.epub` files inside the authorized Core scope:

- deterministic relative-Location ordering;
- no symlink/reparse following;
- content identity read only through the VS1a AssetBroker;
- SHA-256 + byte length + media type retained as inventory evidence;
- any scan/read ambiguity fails the reconciliation run rather than publishing a
  partial catalog as fresh.

Two byte-identical EPUBs at two Locations remain two distinct Stored Instance
and Logical Identity candidates. Fingerprint equality alone never causes a
destructive merge.

### Conservative identity and Location history

VS1b stores internal, revisable candidates rather than claiming a final public
identity ontology.

Important current rules:

- same Location + same fingerprint preserves candidate ids;
- rename/move/relocate can preserve the candidate and append the previous
  Location to history, but the transition remains unverified until inventory;
- same Location + changed fingerprint creates a new unresolved candidate and
  supersedes the previous Stored Instance candidate;
- delete is Location-level missing evidence and retains prior identity/history;
- offline/lost observer scope becomes `unavailable-or-unknown`, never a mass
  logical delete;
- a successful bounded inventory can mark absent Locations
  `confirmed-missing-at-location` while retaining historical records.

### Freshness and stream continuity

VS1b makes catalog trust explicit:

```text
unknown
reconcile-required
fresh
```

A first Alfred sequence number establishes only a checkpoint baseline. A bounded
inventory is required before the catalog becomes fresh.

After that:

- exact replay is idempotent;
- contiguous records may be applied according to their semantic class;
- sequence gaps do not apply later destructive/identity-changing semantic
  evidence and force `reconcile-required`;
- old/unseen out-of-order records force reconciliation instead of being replayed
  destructively;
- records without `seq` are accepted only as continuity-unknown evidence;
- malformed or out-of-scope records do not advance the checkpoint.

### Inventory publication fence

A bounded scan is not allowed to overwrite newer Observation state.

`reconcile_inventory()` captures the catalog revision **before** scanning. The
scan may publish `fresh` only if the same persisted revision still exists at
commit time. If an Alfred record or another reconciliation changes catalog state
while the scan is in progress, the guarded save fails and the stale inventory is
not published as current truth.

This is a single-Core-process optimistic publication fence built on the VS1a
revision guard. It is not a distributed snapshot protocol. VS1b also does not
yet own a live Alfred process or concurrent delivery scheduler: the future live
integration must serialize or retry surfaced stale-write failures rather than
silently dropping them.

## Security and platform claims

What VS1a/VS1b currently claim:

- public handles cannot carry host paths or undeclared authority fields;
- source read authority cannot escape the configured Core scope;
- tested symlink/reparse escapes do not return source bytes;
- inventory content identity comes through the safe AssetBroker;
- observation paths are evidence only and never grant read/write/delete
  authority;
- stream gaps and observer-health gaps cannot silently restore freshness;
- a stale concurrent inventory cannot overwrite newer persisted Observation
  state;
- catalog persistence fails closed on version/integrity/canonical-state errors.

Current live-observer scope remains **Linux/inotify through Alfred**. Windows CI
validates Raiatea adapter/state/inventory contracts and the VS1a Windows file
boundary; it does not imply that Alfred has a Windows backend.

Residual/product-hardening work includes authentication/ACL policy, resource
budgets for large real collections, live-handle restart recovery, multi-process
catalog writers, stronger hostile-race directory enumeration guarantees on
Windows, plugin supervision and later UI/API boundaries.

## Contract boundary

This prototype does not create a second Plugin API contract and does not freeze a
public Catalog schema. Accepted contracts under `elaboration/p0/contracts/`
remain authoritative.

## Sequential next increments

- VS1c — local SourcePlugin product path;
- VS1d — direct EPUB extraction + E-05 persistence;
- VS1e — deterministic search/View/Smart Collection;
- VS1f — export/restore + complete end-to-end acceptance.

Remote Providers, filesystem organization/mutation, natural-language search,
embeddings/vector search, translation, Durex and a generic cross-project Module
Runtime remain outside VS1.
