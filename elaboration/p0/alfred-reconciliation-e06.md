# E-06 — Alfred filesystem Observation reconciliation evidence

> Maturity: **Elaboration evidence — candidate for acceptance**  
> Parent: [#106](https://github.com/kinderp/raiatea/issues/106)  
> Evidence issue: [#176](https://github.com/kinderp/raiatea/issues/176)  
> Raiatea baseline: `main` after Plugin API v1e merge `7ec5c9340120f9e4aab11c5428c62b5a65ea3205`  
> Alfred repository: [`kinderp/alfred`](https://github.com/kinderp/alfred)  
> Alfred evidence snapshot: `9e0e59e4232b8b173f1ae44a409c7d06f72f6c02`  
> Observation date: **25 August 2026**

## 1. Decision summary

E-06 finds **no justification for a second filesystem watcher inside Raiatea**.
The current Alfred evidence is sufficient for the bounded Linux/inotify
Observation role required by the candidate first slice, provided Raiatea keeps a
strict semantic boundary:

```text
Alfred owns filesystem observation and observation-health facts.
Raiatea owns logical identity, Location history, reconciliation,
rights, processing decisions, catalog state and downstream actions.
```

The recommended v0 integration is:

```text
Alfred semantic/diagnostic Event Model v0
        |
        | opt-in structured JSONL
        v
Raiatea AlfredObservationAdapter
        |
        v
Raiatea Observation evidence
        |
        +--> Location/reconciliation state
        +--> freshness / reconcile-required state
        +--> later processing trigger decision
```

This is an **integration boundary decision**, not authorization to implement the
candidate first slice. Promotion still requires E-07 plus the separate roadmap
decision required by #106.

### 1.1 Why JSONL first

Alfred's public direction is record-first: backend/core facts become
`alfred_record_t`, while text/JSONL/future socket or binary writers are
consumers. The current runtime already exposes opt-in structured JSONL; a future
socket writer is explicitly a compatible downstream direction.

For Raiatea this gives the narrowest useful boundary:

- no C ABI coupling;
- no import/link dependency on Alfred internals;
- replayable evidence fixtures for Raiatea tests;
- explicit Alfred `schema_version` handling;
- process failure remains outside Raiatea's domain model;
- a future `unix_socket` transport can replace file/tail delivery without
  changing the Raiatea Observation vocabulary.

Direct C/library coupling is rejected for the first slice because it would make
Alfred's memory ownership, enums and implementation lifecycle part of Raiatea's
runtime compatibility surface without providing a domain benefit.

## 2. Evidence inspected

The Alfred snapshot is the same revision already pinned by Raiatea's accepted
System Context and is still current `main` at the time of this audit.

Evidence used:

| Evidence | What it establishes |
| --- | --- |
| `docs/it/29-event-model-v0.md` | layers/categories/types; semantic vs diagnostic separation; common record contract |
| `core/include/alfred_record.h` | executable Event Model v0 vocabulary, filesystem semantic events, overflow and recovery diagnostics, optional filesystem identity evidence |
| `docs/it/26-stato-funzionalita.md` | currently supported inotify/raw/core/recovery behavior and test coverage |
| `docs/it/30-backend-api-v0.md` | backend/core ownership boundary and current Linux/inotify implementation limits |
| `docs/it/32-writer-api-v0.md` | record-first writer boundary, current opt-in JSONL and future socket direction |
| commit `9e0e59e` / PR #289 | corrected JSONL semantic path applicability: single-path vs path-pair events are no longer ambiguous aliases |
| current Alfred issues #279/#290/#278 | current product work is first-user validation/Linux userspace expansion, not a hidden cross-platform backend claim |

No Alfred source change is required by the evidence found in E-06.

## 3. Ownership boundary

### 3.1 Alfred owns

Within the platform/backend scope it actually supports, Alfred owns:

- recursive filesystem observation;
- backend normalization;
- semantic create/delete/modify/ready facts;
- rename/move/relocate correlation;
- observation overflow signalling;
- watch lifecycle and stale state;
- local resync and delayed lost-scope recovery diagnostics;
- optional backend-derived filesystem identity evidence;
- structured serialization of those records.

### 3.2 Raiatea owns

Raiatea must not outsource these meanings to Alfred:

- `LogicalIdentity` / future catalog identity;
- one-or-many current and historical `Location`s;
- exact duplicate vs same logical item vs related representation;
- known-present vs unavailable/unknown vs confirmed-missing state;
- whether an observation should trigger reindex/extraction;
- rights and policy decisions;
- processing state and provenance;
- organization/mutation authority;
- user-visible catalog durability and recovery.

An Alfred semantic event is therefore **evidence about a filesystem location**,
not a catalog command.

## 4. Minimal Raiatea Observation vocabulary

E-06 intentionally does not freeze a public product schema. It identifies the
minimum semantic categories the first implementation must be able to represent.
A candidate internal envelope is:

```text
Observation
  observation_id
  observed_at
  observer:
    system = "alfred"
    alfred_revision
    record_schema_version
    backend
  scope_ref
  kind
  location | old_location + new_location
  filesystem_identity?   # evidence only
  source_record_ref?
  freshness_effect
  confidence = observed | uncertain
```

`filesystem_identity` may carry device/inode-like evidence when Alfred provides
it, but the field is explicitly **not** Raiatea logical identity.

### 4.1 Semantic record mapping

| Alfred semantic record | Raiatea Observation kind | Required Raiatea reaction |
| --- | --- | --- |
| `FILE_CREATED` / `DIR_CREATED` | `location-appeared` | discover/reconcile candidate at path; do not invent logical identity from path alone |
| `FILE_READY` | `content-ready` | candidate signal for bounded reindex/extraction after rights/policy checks |
| `FILE_MODIFIED` | `location-content-changed` | mark representation/version evidence changed; schedule content verification as policy permits |
| `FILE_DELETED` / `DIR_DELETED` | `location-disappeared-observed` | mark this location missing candidate; **never auto-delete logical source solely from event** |
| `FILE_RENAMED` / `DIR_RENAMED` | `location-transition` | preserve identity candidate and location history; reconcile old -> new |
| `FILE_MOVED` / `DIR_MOVED` | `location-transition` | same; parent changed, path identity must not split source |
| `FILE_RELOCATED` / `DIR_RELOCATED` | `location-transition` | same; parent and basename changed |
| `OVERFLOW` | `observation-incomplete` | mark scope freshness unknown/stale and require bounded reconciliation |

The adapter consumes the **semantic** layer for ordinary filesystem meaning. Raw
or backend-observed events are not an alternate truth path for Raiatea's catalog.
They remain diagnostic/reproduction evidence unless a future separately reviewed
use case requires them.

### 4.2 Observation-health diagnostic mapping

| Alfred diagnostic | Raiatea effect |
| --- | --- |
| `WATCH_STALE` | mark affected observation coverage `uncertain`; do not apply later stale-path evidence as authoritative |
| `WATCH_STALE_EVENT_DROPPED` | retain an explicit observation gap; reconciliation required |
| `WATCH_RESYNC_BEGIN` | coverage recovery in progress; freshness remains stale |
| `WATCH_RESYNC_SCAN_FAILED` / `WATCH_RESYNC_FAILED` | reconciliation required; no synthetic deletes |
| `WATCH_RESYNC_END` | Alfred coverage restored; **catalog equality is not implied** |
| `WATCH_LOST_QUEUED` | scope identity/location temporarily unresolved; preserve catalog entities |
| `WATCH_LOST_FOUND` | candidate new location for the same filesystem object; pass through Raiatea reconciliation |
| `WATCH_LOST_NOT_FOUND` | scope/location unavailable or unresolved; **not logical deletion** |
| `WATCH_LOST_RETRY_SCHEDULED` | keep state unknown/unavailable |
| `WATCH_LOST_RECOVERY_GAVE_UP` | persistent observation gap; require user-visible stale state and bounded scan/reconcile before freshness claim |
| `WATCH_LOST_RECOVERY_END` | observer recovered; catalog still needs any reconciliation demanded by the gap window |

Fine-grained scan/reinstall diagnostics may be retained as provenance/operations
evidence without each becoming a first-class catalog state.

## 5. Conservative identity and reconciliation

### 5.1 Path is Location

The accepted System Context already requires pathname to be mutable Location,
not identity. E-06 confirms Alfred provides sufficient path-transition evidence
to preserve that rule on its supported backend.

The adapter must not implement logic equivalent to:

```text
new path -> new logical source
missing path -> delete logical source
same inode -> permanent universal identity
```

### 5.2 Filesystem identity is evidence, not ontology

Alfred exposes device/inode-style identity because it is useful for watch and
lost-scope recovery on a filesystem. Raiatea may retain it as one reconciliation
signal when present.

It is insufficient as universal logical identity because:

- copies have new filesystem identity;
- cross-filesystem moves can become copy+delete;
- removable/offline mounts can change availability and mount context;
- content can be replaced at a path;
- physical/digital/edition relationships are outside inode semantics;
- future non-filesystem sources have no inode at all.

Therefore the first slice may use exact content fingerprints plus observation
history and filesystem evidence conservatively, but ambiguous cases must remain
explicitly unresolved/reviewable.

### 5.3 Delete semantics

`FILE_DELETED` and `DIR_DELETED` mean Alfred observed disappearance from a path
inside a currently observed scope. Raiatea translates that to a location-level
fact.

A stronger state such as `confirmed-logical-deletion` requires separate Raiatea
evidence/policy. The candidate first slice has no destructive catalog purge
triggered by Alfred delete events.

### 5.4 Offline / lost scope

The required minimum state distinction for P0 is:

```text
known-present
unavailable-or-unknown
confirmed-missing-at-location
```

The first slice must be able to represent the middle state. If Alfred loses a
scope, cannot find a saved identity, schedules retry or gives up, Raiatea keeps
its known catalog/location history and marks observation freshness unavailable.
It does not fan out deletion across descendants.

## 6. Overflow, stale state and truth recovery

Continuous events are an optimization for freshness; they are not the only
source of catalog truth.

### 6.1 Fail-closed rule

```text
complete observation stream -> incremental reconciliation allowed
observation gap / stale path -> incremental certainty suspended
bounded inventory scan + reconciliation -> freshness may be restored
```

On `OVERFLOW`, `WATCH_STALE`, stale-event drop or failed lost-scope recovery,
Raiatea must record a freshness gap before applying downstream claims that depend
on complete observation.

### 6.2 Recovery is not equality

Alfred's successful resync/lost-scope recovery means the **observer** restored a
usable watch/coverage state. Events may have been missed during the gap.
Therefore Raiatea must not interpret `WATCH_RESYNC_END` or
`WATCH_LOST_RECOVERY_END` as “catalog equals filesystem”.

The integration needs a bounded inventory/reconciliation operation for the
affected scope. For the first slice this can be deliberately simple and
synchronous: enumerate the authorized root, collect stable enough file evidence,
compare with catalog Locations, and emit explicit reconciliation outcomes.

This bounded scan is not a second watcher and does not define a competing event
model.

## 7. Security and authority boundary

Observation authority and mutation authority remain different capabilities.

### 7.1 Scope

Every Alfred integration stream must be associated with an explicit Raiatea
`scope_ref` created from user/configuration authority. A web/API caller cannot
expand that root merely by putting an arbitrary path into an Observation.

The adapter validates that an incoming path belongs to its bound scope before
it can affect catalog state. Out-of-scope events fail closed and remain
diagnostics.

### 7.2 Symlinks and roots

Current Alfred inotify root handling rejects non-directory roots and symlink
roots at its target boundary. Raiatea must still treat path containment as its
own authorization concern rather than assuming a backend check grants future
mutation authority.

A future managed/reorganization feature requires a separate authority contract;
E-06 grants none.

### 7.3 Data minimization

Ordinary Observation records need metadata/path evidence, not document bytes,
credentials or extractor secrets. Content acquisition and extraction continue
through Raiatea's Source/Plugin/rights boundaries.

### 7.4 Provenance

For reconstructibility the adapter should preserve at least:

- `observer_system = alfred`;
- Alfred source revision/build identity when available;
- Alfred Event Model `schema_version`;
- source backend when present;
- original Alfred event/record identifier or stream sequence when present;
- Raiatea scope reference;
- adapter version;
- observation timestamp;
- whether the input was semantic or diagnostic.

## 8. Platform evidence and first-slice containment

Alfred's implemented/reference backend is Linux `inotify`. Its CI currently
provides multiple Linux **userspace** lanes, but those containers share the
runner kernel; this must not be marketed as independent kernel/filesystem
coverage. macOS and Windows backends remain future directions.

E-06 therefore recommends a bounded first-slice platform statement:

> The first filesystem-observation proof is Linux/inotify only, on an explicitly
> recorded environment, with bounded inventory/reconciliation available as the
> correctness recovery path.

This is enough to reduce R-04 for the experiment without forcing a second watcher
into Raiatea. Broader platform coverage remains an Alfred capability roadmap or
a future replaceable platform adapter question.

## 9. Integration alternatives

| Option | Decision | Reason |
| --- | --- | --- |
| opt-in Alfred JSONL -> Raiatea adapter | **Use for first slice** | implemented, structured, replayable, process-decoupled, schema-versioned |
| future Alfred Unix-socket writer -> same adapter semantics | **Preferred evolution** | lower-latency local integration without domain coupling; not required now |
| direct C/library linkage to `alfred_record_t` | **Do not use in first slice** | couples ABI/lifecycle/memory ownership and reduces replaceability |
| parse Alfred text logs | **Reject** | text is human/compatibility output, not a stable integration contract |
| read inotify directly in Raiatea | **Reject** | duplicates Alfred and violates accepted system boundary |
| generic shared Alfred/Raiatea plugin runtime | **Defer** | no repeated evidence justifies cross-project extraction yet |

## 10. Candidate adapter behavior

The first implementation should be intentionally boring and deterministic:

```text
read one Alfred JSONL record
    -> validate supported schema/layer/category/type
    -> validate bound scope/path containment
    -> map to Raiatea internal Observation
    -> append Observation/provenance
    -> update observation freshness state
    -> enqueue/recommend reconciliation or processing intent
```

Unknown Alfred schema versions, unsupported record tuples and malformed required
fields fail closed. They do not silently degrade into guessed filesystem actions.

The adapter is a **consumer**, not an Alfred controller. Process supervision,
startup configuration and future live transport can evolve separately from the
mapping contract.

## 11. Evidence contribution to P0 risks and gates

| Risk / gate | E-06 evidence | Remaining before promotion |
| --- | --- | --- |
| R-01 false identity / G-03 | path transitions are not logical identity; filesystem identity is evidence only; no auto-merge | E-07 must show concrete identity fixtures and conservative outcomes |
| R-02 offline != delete / G-03 | explicit unavailable/unknown state; lost-scope and delete separated | E-07 must synthesize fixture evidence and acceptance rule |
| R-04 observation gap | Alfred reuse verified for bounded Linux/inotify; overflow/stale -> reconcile-required | platform claim remains intentionally narrow; reconciliation proof belongs to first slice/exit evidence |
| R-07 provenance / G-05 | observer revision/schema/backend/adapter provenance requirements identified | E-07 integrates with extraction/transformation provenance evidence |
| R-22 local security / G-07 | observation scope cannot grant mutation; adapter path containment and data minimization required | E-07 must combine with catalog backup/export/local UI authority evidence |
| G-01 scope containment | no second watcher, no macOS/Windows implementation, no organization mutation | promotion decision must preserve these exclusions |

## 12. Findings

| ID | Severity | Status | Finding | Resolution / consequence |
| --- | --- | --- | --- | --- |
| E06-F1 | high if ignored | resolved by boundary | Alfred delete/lost-scope events could be misused as logical deletion if Raiatea copied event semantics directly into catalog state. | Map deletion to Location evidence; lost/unavailable scope is distinct; no logical purge from Observation alone. |
| E06-F2 | high if ignored | resolved by recovery rule | Successful Alfred watch recovery does not prove that no events were missed while coverage was stale. | Recovery restores observer health; Raiatea still requires bounded inventory reconciliation before claiming freshness after a gap. |
| E06-F3 | medium | contained | Alfred's current real backend evidence is Linux/inotify; cross-platform product aspirations exceed current observer implementation. | Narrow first observation proof to Linux/inotify and keep other platforms outside promotion scope rather than duplicate Alfred. |
| E06-F4 | medium | resolved by integration choice | Direct C coupling would leak Alfred implementation/ownership semantics into Raiatea. | Use structured JSONL/replay boundary first; preserve migration path to local socket. |
| E06-F5 | medium | resolved by provenance requirement | Consuming serialized events without source revision/schema/backend provenance would make later interpretation ambiguous. | Require observer/schema/revision/backend/adapter provenance on Raiatea Observation evidence. |

No E-06 finding requires a change to Alfred itself.

## 13. E-07 handoff

E-07 may consume these E-06 conclusions as evidence, not assumptions:

1. **G-03:** pathname is Location; rename/move/relocate preserve a reconciliation
   candidate; missing/offline is distinct from deletion; no auto-merge.
2. **G-04/R-04 interaction:** event delivery is freshness evidence, bounded scan
   is truth recovery after gaps.
3. **G-05:** filesystem Observation provenance includes Alfred/schema/backend and
   adapter identity.
4. **G-07:** observation scope carries no mutation authority and the adapter must
   enforce its bound root.
5. **Scope:** first proof remains Linux/inotify; macOS/Windows and generic runtime
   extraction remain excluded.
6. **Implementation seed:** an internal `AlfredObservationAdapter` consuming
   structured JSONL is the smallest evidence-backed first step if/when promotion
   authorizes the vertical slice.

## 14. Acceptance checklist

- [x] current Alfred baseline pinned and auditable;
- [x] semantic and observation-health records mapped to Raiatea Observation evidence;
- [x] path/Location vs logical identity ownership explicit;
- [x] missing/offline/lost-scope cannot collapse into logical deletion;
- [x] overflow/stale/recovery reaction is fail-closed with a truth-recovery route;
- [x] integration surface selected with alternatives and trade-offs;
- [x] platform evidence bounded to current Linux/inotify support;
- [x] security/authority boundary contributes to G-07 without mutation authority;
- [x] G-03/R-01/R-02 and R-04 contribution explicit;
- [x] no second watcher or generic runtime introduced;
- [ ] two consecutive clean review rounds on frozen PR head.
