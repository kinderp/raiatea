# VS1c — Replaceable local SourcePlugin

> Parent vertical slice: #187  
> Micro-step: #192  
> Pull request: #193  
> Status: implementation under final validation

## Functional increment

VS1a made local file access safe. VS1b made the local EPUB catalog observable and
reconcilable. VS1c adds the next product capability:

> **the local collection is no longer a special Core-only source path; it is
> represented through a replaceable SourcePlugin boundary.**

Before VS1c:

```text
Core
  -> local EPUB inventory
  -> internal catalog candidates
```

After VS1c:

```text
fresh VS1b catalog
        ↓
Core path-free DiscoverySnapshot
        ↓
Core RightsDecision
        ↓
official LocalSourcePlugin process
        ↓
path-free SourceReference records
        ↓
Core validation + persistence
```

The SourcePlugin can therefore be replaced in later increments by another source
family without moving filesystem authority, catalog identity or rights policy
into the plugin.

## What crosses the plugin boundary

The plugin receives metadata for current, inventory-verified EPUB candidates:

- opaque catalog entry reference;
- opaque Stored Instance candidate reference;
- opaque Logical Identity candidate reference;
- media type;
- byte length;
- SHA-256 fingerprint.

It does **not** receive:

- the authorized user root;
- relative or absolute source paths;
- Location history;
- EPUB bytes;
- secrets;
- a rights grant it can widen;
- network authority.

The snapshot is canonically ordered. Equivalent catalog facts produce the same
snapshot regardless of internal entry-list order.

## SourceReference semantics

The plugin converts each DiscoverySnapshot item into one deterministic
`SourceReferenceRecord`.

A SourceReference carries:

- a stable `source_ref_id` derived from opaque catalog/stored-instance identity
  plus content fingerprint;
- source class;
- opaque catalog/stored/logical candidate refs;
- media type;
- byte length;
- fingerprint;
- `location_exposed = false`.

Two byte-identical EPUB files at different Stored Instances remain two distinct
SourceReferences. Fingerprint equality alone never merges them.

SourceReference identity is not tied to the plugin version, so replacing the
implementation does not automatically rename an unchanged source.

## Core-owned RightsDecision

VS1c introduces the first executable rights/policy decision used by the product
slice for `source.discover`.

The decision explicitly keeps these concepts separate:

```text
processing authority
!= processing rights evidence
!= redistribution rights
```

For this narrow discovery route:

- the user-authorized Core scope establishes local processing authority;
- `known-restricted` fails closed;
- `requires-review` fails closed;
- `unknown` remains explicitly `unknown`;
- `known-permitted` remains explicitly `known-permitted`;
- source bytes are never shared with the SourcePlugin;
- redistribution is always false;
- the record states that no legal conclusion is established by this policy
  decision.

Allowing `unknown` in VS1c is specific to the reference-only metadata flow. It
must **not** be automatically reused for VS1d content extraction, where source
bytes cross an extractor boundary and a separate processing decision is required.

## Real process boundary

The official LocalSourcePlugin runs as a separate local process and uses the
accepted Plugin API transport/runtime primitives:

- manifest declaration;
- handshake;
- `source.discover/local-catalog-read-only` invocation;
- opaque input/output AssetHandles;
- Core-issued write-once output target;
- bounded diagnostics;
- Runtime v1 result/provenance validation;
- deterministic process cleanup.

This is a VS1-specific implementation. It does not extract a generic shared
Module Runtime.

## Private plugin I/O workspace

Core creates a temporary private workspace for one plugin session. The workspace
contains only:

- the path-free DiscoverySnapshot payload;
- a Core-owned output location for the SourceReferenceBundle;
- broker metadata mapping opaque handles to those private scratch files.

The workspace is removed after the invocation.

The plugin manifest declares no source filesystem, network or secret
permissions. In VS1c this is a declarative capability boundary and the Core also
withholds source paths/bytes. **VS1c is not yet an OS-level hostile-plugin
sandbox.** An official local process can theoretically use ambient OS access
outside the declared contract; sandboxing/untrusted third-party plugin execution
requires a later separately reviewed security boundary.

Therefore the supported VS1c claim is:

> Core does not grant or transmit source filesystem authority through the Plugin
> API, and it validates the plugin output exactly against the Core snapshot.

It is not:

> arbitrary malicious native/plugin code is cryptographically prevented from
> accessing everything the host account can access.

## Output validation

Core does not trust the plugin result merely because Runtime validation passes.
It also requires:

- canonical SourceReferenceBundle JSON;
- exact one-to-one coverage of DiscoverySnapshot items;
- no missing, duplicate or extra references;
- exact fingerprint/length/media/ref agreement;
- expected record-ref ordering;
- matching rights decision provenance;
- valid write-once output handle fingerprint and byte length.

A modified or incomplete bundle is rejected without catalog persistence.

## Stale catalog fence

The Core captures the catalog revision before invoking the plugin.

If Alfred/reconciliation/another Core action changes persisted catalog state
while the plugin is running, the final `CatalogStateStore.save()` revision guard
fails. Stale SourceReferences are not published and discovery must be repeated
against the newer fresh catalog.

This keeps VS1c source discovery downstream of VS1b catalog truth rather than
allowing the plugin to become a competing source of identity.

## Current platform evidence

The product contract is exercised on:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.12;
- Windows / Python 3.10;
- Windows / Python 3.12.

The plugin is a local process on both platforms. This does not change the VS1b
statement that live Alfred filesystem observation is currently Linux/inotify.

## What VS1c still cannot do

VS1c knows **where a source sits in Raiatea's logical source boundary**, but it
still does not know the text or structure inside the EPUB.

That is the functional purpose of VS1d:

```text
SourceReference
   ↓
Core resolves current Stored Instance
   ↓
safe source AssetHandle
   ↓
direct EPUB ExtractorPlugin
   ↓
E-05 ProcessingRun / Outcome / NormalizedRepresentation
   ↓
text + structure + source coordinates + provenance persisted in catalog
```

VS1c also does not add remote sources, UI search, Views, Smart Collections,
filesystem organization, a plugin marketplace, third-party sandboxing or a
generic cross-project runtime.
