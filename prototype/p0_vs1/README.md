# P0 vertical slice 1 prototype

> Parent promotion: [#187](https://github.com/kinderp/raiatea/issues/187)  
> Current micro-step: [#188](https://github.com/kinderp/raiatea/issues/188) — VS1a  
> Status: **Draft implementation under PR #189**

This directory contains the executable product-prototype path for the first
promoted Raiatea vertical slice.

The first source route selected by #187 is local B-02 EPUB through the accepted
`direct-epub-stdlib` route. VS1a does **not** implement extraction yet; it builds
the Core-owned authority and persistence boundary required before real content
can safely cross the Plugin API.

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
be regular. This anchors access to the Core-authorized directory even if its
pathname is later renamed.

On **Windows**, VS1a opens the requested file through Win32 `CreateFileW`, rejects
a final reparse point/directory, obtains the normalized final path from the
**opened handle** through `GetFinalPathNameByHandleW`, and compares that path
component-wise against the canonical Core root captured at registration. An
intermediate junction/symlink that resolves outside the root therefore fails
before `ReadFile` returns content.

Issuing a handle fingerprints the bytes. Reading through the handle later opens
the file again through the same safe boundary and requires the current byte
length + SHA-256 to match the issued identity; replacement after issuance fails
as `asset-content-changed`.

### Core-owned write-once outputs

Output paths are never caller supplied. Core generates an opaque handle and an
internal filename under a Core-owned output root.

The public target carries only:

```text
handle_id
lease_id
access = write-once-output
media_type
max_byte_length
expires_at
```

The broker enforces lease/access/media/budget, creates without overwrite, then
records actual byte length + SHA-256. A later Core read reopens the result through
the same OS-aware safe-read boundary and verifies the completed fingerprint and
length, so post-completion disk tampering is visible.

### Minimal internal catalog state store

`CatalogStateStore` intentionally knows nothing about LogicalItem, Location,
View or Smart Collection domain schemas yet. It persists one opaque JSON-object
payload inside an internal envelope with:

- internal store version;
- monotonically increasing revision;
- canonical JSON serialization;
- SHA-256 of the canonical payload;
- atomic temporary-file + replace write;
- post-write verification;
- symlink/reparse rejection for the Core-owned state path;
- expected-revision stale-write guard.

VS1a has **one Core process / one store owner**. Calls through one store instance
are serialized with an in-process lock. This is not advertised as an atomic
cross-process or distributed compare-and-swap protocol; multi-process writers,
Durex and distributed state remain outside this increment.

## Security claims and residuals

VS1a proves the boundary required for the promoted local EPUB slice, but it is
not an OS sandbox or a complete security product.

What VS1a **does claim**:

- public handles cannot carry host paths or undeclared extra authority fields;
- source read scope cannot be widened using an external absolute/traversal path;
- tested symlink/reparse escapes do not return source bytes;
- source bytes are bound to an issued fingerprint/length;
- output authority is Core-created, bounded and write-once;
- completed output tampering is detected;
- catalog persistence fails closed on version/integrity/canonical-state errors.

What remains for later increments/product hardening:

- authentication/user identity and OS ACL policy;
- per-source/input memory and resource budgets for large real collections;
- persistence/recovery of live handle leases across Core restart;
- crash recovery for a file written immediately before in-memory output
  completion state is recorded;
- multi-process catalog writers/locking;
- platform claims beyond Linux and Windows CI evidence;
- SourcePlugin supervision and real plugin broker wiring (VS1c).

The Windows implementation validates final opened-handle containment and
reparse-point behavior; it does not claim to be a general hostile multi-user
Windows sandbox. The selected VS1 remains a local, explicitly authorized
single-user proof.

## Contract boundary

This prototype does not create a second Plugin API contract and does not freeze a
public catalog schema. Accepted contracts under `elaboration/p0/contracts/`
remain authoritative. VS1a tests its generated read/output records inside the
accepted Runtime v1b validator and reruns the accepted manifest, transport,
runtime and real v1d Source/EPUB proof suites.

## Sequential next increments

- VS1b — Alfred Observation adapter + inventory/reconciliation;
- VS1c — local SourcePlugin product path;
- VS1d — direct EPUB extraction + E-05 persistence;
- VS1e — deterministic search/View/Smart Collection;
- VS1f — export/restore + complete end-to-end acceptance.

Remote Providers, filesystem organization/mutation, natural-language search,
embeddings/vector search, translation, Durex and a generic cross-project Module
Runtime remain outside VS1.
