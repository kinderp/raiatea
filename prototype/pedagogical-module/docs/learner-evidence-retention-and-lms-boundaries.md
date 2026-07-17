# Learner evidence retention and future LMS boundaries

Status: prototype architecture and privacy boundary  
Parent issue: [#8](https://github.com/kinderp/raiatea/issues/8)  
Implementation issue: [#16](https://github.com/kinderp/raiatea/issues/16)

## Purpose

Raiatea currently keeps observable learner evidence in the browser and lets the learner explicitly export or restore one versioned JSON document for one module. This document defines the lifecycle and engineering boundary around that evidence before any cloud or LMS integration exists.

It has four goals:

1. make the current retention and deletion behavior explicit;
2. distinguish portable evidence from identity, preferences, authored content, and inferred data;
3. define the minimum guarantees a future LMS adapter must preserve;
4. prevent a future integration from quietly turning a local learning aid into analytics or surveillance infrastructure.

This is an engineering policy for the prototype. It is not a claim of legal, regulatory, accessibility, records-management, or institutional-policy compliance. An adopting institution remains responsible for defining its lawful purpose, retention period, authorization model, learner notices, deletion process, backup policy, and incident response.

## Current trust boundary

The current module has no server-side learner account and no background network transfer.

```text
module-authored JSON
        ↓ build
self-contained HTML module
        ↓ learner interaction
browser-local progress key
        ↕ explicit learner action
versioned one-module JSON file
```

The browser module may read and write only its documented local keys. A downloaded JSON file is created only after an explicit export action. A restore is applied only after file selection, validation, compatibility checks, a conflict preview, and explicit confirmation.

## Terms

- **Observable evidence**: direct outcomes already recorded by the module, such as attempts, eventual correctness, remediation use, recovery-activity completion, and current step.
- **Authored metadata**: module ID, title, language, ordered step titles, and allowlisted source context used to interpret or validate evidence.
- **Reading preferences**: theme, font size, density, reading width, alignment, and motion settings.
- **Identity data**: names, email addresses, account IDs, institutional IDs, device IDs, or identifiers that can be linked to a person.
- **Free-form learner content**: learner-authored prose, code, notes, messages, uploads, or other unconstrained input.
- **Inferred data**: mastery scores, diagnoses, disability inferences, risk labels, predictions, behavioral profiles, or automated judgments not directly observed in the module record.
- **Adapter**: a future, explicitly invoked component that translates between the Raiatea evidence contract and an external system without changing the meaning or privacy boundary of the source document.

## Data classification

| Data class | Current location | In learner-evidence v1 export | Default future LMS transfer | Reason |
| --- | --- | --- | --- | --- |
| Observable evidence | `raiatea-progress:<module-id>` | Allowed | Allowed only after explicit authorization | It is the purpose of the interchange contract. |
| Module ID and authored titles | Built module and export context | Allowed | Allowed as interpretation/compatibility context | They identify the authored module revision, not the learner. |
| Allowlisted source context | Built module and export context | Allowed | Optional and minimized | It explains provenance but is not needed for every destination. |
| Reading preferences | `raiatea-reading-settings` | Prohibited | Prohibited by default | They are presentation preferences, not learning evidence. |
| Unrelated browser storage | Other keys | Prohibited | Prohibited | The module has no purpose or authority to transfer it. |
| Identity data | Not collected by this prototype | Prohibited | Must remain outside the evidence document | Authentication and roster mapping belong to the destination boundary. |
| Free-form learner content | Not collected by this prototype | Prohibited | Requires a separate contract and threat model | It can contain sensitive or executable content and has different review needs. |
| Inferred mastery or personal traits | Not computed | Prohibited | Prohibited unless introduced by a separately reviewed feature | Observable events must not be relabeled as authoritative judgments. |
| Timestamps and analytics IDs | Not recorded in v1 | Prohibited | Prohibited by default | They enable tracking and retention expansion without supporting current restore semantics. |

A future adapter must not solve identity mapping by inserting personal identifiers into the v1 evidence document. Authentication, authorization, roster association, and destination-specific identifiers must be carried in a separate adapter context with separate retention and access rules.

## Current lifecycle

### 1. Creation

A module creates its progress record when it renders or when the learner interacts. The record is scoped to one module ID:

```text
raiatea-progress:<module-id>
```

The module does not create a global learner profile. Reading preferences use a separate key and are not evidence.

### 2. Update

Navigation and diagnostic interactions update only the documented progress fields. The prototype does not append an event history, timestamp interactions, infer mastery, or send telemetry.

A pending restore preview is invalidated if local progress changes. This prevents confirmation based on a stale comparison.

### 3. Browser-local retention

`localStorage` persists according to browser behavior until one of the following occurs:

- the learner uses **Azzera avanzamento** for the current module;
- the learner clears site data in the browser;
- the browser, operating system, privacy mode, storage quota, or profile policy removes the data;
- the HTML module is opened in another origin or browser profile, where the previous key is not available.

The prototype does not impose an automatic expiry period. This is a limitation, not a promise of indefinite retention. It also does not guarantee backup, cross-device availability, durability, or recovery after browser data loss.

### 4. Explicit export

Export creates a new JSON file through a user action. The browser-local record remains unchanged. Raiatea does not track where the file is saved, how many copies exist, whether it is attached to a message, or when it is deleted.

The downloaded file is therefore under the control of the learner, device owner, or institution managing the device. Deleting browser progress does not delete downloaded copies, backups, email attachments, shared-drive copies, or files imported into another system.

### 5. Explicit restore

Restore follows this sequence:

```text
select local file
→ reject oversized input before parsing
→ validate v1 structure
→ check exact module compatibility
→ show current-versus-file preview
→ require explicit confirmation
→ replace one module progress key with allowlisted fields
```

Selection alone is side-effect free. Restore is replacement, not history merging. It does not import identity, reading preferences, source metadata, unknown properties, or free-form content into browser progress.

### 6. Deletion

Current deletion has distinct scopes:

| Action | Deleted | Not deleted |
| --- | --- | --- |
| **Azzera avanzamento** | Current module progress key | Reading preferences, other modules, downloaded JSON files, unrelated storage |
| Browser “clear site data” | Keys controlled by that browser origin | Downloaded files and external copies |
| Delete downloaded JSON file | That file in the chosen filesystem location | Browser progress, backups, copies, external imports |
| Remove browser profile/device | Data held only in that profile/device | Copies already exported or synchronized by device software |

The UI must not imply that one deletion action erases all copies. A future external transfer must return enough destination information for the learner or institution to understand where a separate deletion request belongs.

## Retention defaults and institutional responsibility

The prototype default is deliberately narrow:

- no server copy;
- no background transfer;
- no automatic analytics retention;
- browser-local progress persists until the browser or learner removes it;
- exported files persist wherever the user or device places them;
- no hidden duplicate is maintained by Raiatea.

Before institutional deployment or LMS integration, the adopting organization must document at least:

1. the purpose for collecting or receiving evidence;
2. who can authorize a transfer;
3. which learners and modules are in scope;
4. the retention period in the destination and in backups;
5. how deletion, correction, export, and access requests are handled;
6. whether records are educational records, temporary learning artifacts, or both under local policy;
7. what happens when a learner leaves a course or an account is deactivated;
8. how incidents, accidental disclosure, and destination misconfiguration are reported.

Raiatea should not encode a universal institutional retention duration into the interchange schema. Different deployments have different obligations. The adapter must instead require an explicit destination policy and must not silently invent one.

## Future LMS adapter boundary

A future LMS integration must remain outside the core module renderer and must be optional.

```text
Raiatea module
   │
   │ creates/validates learner-evidence v1
   ▼
Explicit transfer UI
   │  destination + scope + preview + authorization
   ▼
Provider-neutral adapter port
   │  authentication context kept separate
   ▼
LMS-specific adapter
   │
   ▼
Disclosed destination record + receipt
```

The reverse direction uses the same boundary:

```text
LMS-specific adapter
→ fetch candidate document
→ normalize to a supported Raiatea evidence version
→ local structural and compatibility validation
→ conflict preview
→ explicit restore confirmation
```

### Core responsibilities

The Raiatea core may:

- create and validate the versioned evidence document;
- calculate compatibility with the current module;
- present a human-readable transfer or restore preview;
- require an explicit action;
- expose a provider-neutral port;
- receive a non-sensitive transfer receipt.

The Raiatea core must not:

- store LMS credentials in the evidence document;
- infer a learner identity from browser or device data;
- choose a destination without disclosure;
- transfer in the background;
- broaden the payload because a provider accepts more fields;
- convert attempts into a grade or mastery score;
- silently retry a transfer to another provider;
- treat successful upload as permission for indefinite retention.

### Adapter responsibilities

Every LMS-specific adapter must:

1. **Disclose the destination**: name the organization, course/context, provider, and record type before confirmation.
2. **Separate identity context**: keep authentication and roster mapping outside the evidence payload.
3. **Minimize data**: send only fields required for the declared destination purpose.
4. **Validate versions**: reject unsupported versions rather than guessing or coercing.
5. **Preserve semantics**: do not reinterpret remediation use, attempts, or correctness as a grade unless a separate, reviewed mapping is explicitly configured and shown.
6. **Require authorization**: verify that the current user or institutional workflow is permitted to transfer the evidence.
7. **Return a receipt**: report destination, accepted evidence version, operation result, and an external reference that does not expose credentials.
8. **Handle retries safely**: use idempotency or explicit duplicate warnings so repeated confirmation does not create ambiguous records.
9. **Expose deletion ownership**: identify whether deletion must occur in Raiatea, the LMS, an institutional archive, or all of them.
10. **Fail closed**: leave the source record unchanged and report a useful error when authorization, validation, compatibility, or destination checks fail.

### Provider-neutral conceptual interface

This is an architectural boundary, not a frozen API:

```text
prepareTransfer(evidence, destinationContext)
  -> preview | validationError | authorizationError

confirmTransfer(previewToken)
  -> receipt | transferError

fetchRestoreCandidate(externalReference)
  -> evidenceDocument | retrievalError
```

`destinationContext` may carry authorization and roster information, but those values must not be serialized into learner-evidence v1. A `previewToken` must expire and must bind the exact payload, destination, and authorization context that the learner reviewed.

## Required transfer preview

Before an outbound transfer, the UI must show at least:

- destination organization/provider and course or context;
- module ID/title and evidence version;
- fields and number of step records to be sent;
- whether source context is included;
- whether the operation creates, replaces, or appends a destination record;
- destination retention/deletion policy or a link supplied by the adopting institution;
- any identity used by the destination, shown separately from the evidence payload;
- the action required to confirm.

A vague button such as “Sync” is insufficient because it hides direction, destination, payload, and overwrite semantics.

## Threat and failure cases

| Case | Risk | Required boundary or mitigation |
| --- | --- | --- |
| Silent background synchronization | Learner evidence becomes telemetry without a deliberate action | No scheduled/background transfer; explicit preview and confirmation for each policy-defined operation. |
| Wrong destination or course | Evidence is disclosed to an unintended context | Destination disclosure, authorization check, and payload-bound preview token. |
| Cross-learner mix-up | Evidence is associated with another person | Separate authenticated identity context, visible destination identity, and adapter-side authorization checks. |
| Payload expansion | Provider-specific adapter sends preferences, identity, or unrelated storage | Core allowlist plus adapter minimization tests; reject unknown fields. |
| Stale preview | The local record or destination changes after review | Invalidate preview tokens when source, destination, or authorization context changes. |
| Duplicate submission | Retry creates multiple ambiguous LMS records | Idempotency key or explicit duplicate-detection workflow. |
| Unsupported schema version | Adapter guesses field meaning and corrupts semantics | Fail closed; require an explicit reviewed migration. |
| Incompatible module revision | Evidence is restored into changed ordered steps | Exact compatibility checks and visible conflict handling. |
| Excessive retention | Temporary evidence becomes a permanent institutional profile | Destination policy disclosure, documented retention owner, and deletion process. |
| Backup persistence | UI deletion is mistaken for erasure of backups or exports | Explain deletion scope and institutional backup timelines. |
| Provider lock-in | Evidence can be sent but not recovered in an open form | Keep the Raiatea versioned document as the provider-neutral interchange form and require export/receipt references. |
| Credential leakage | Tokens are copied into downloadable evidence | Keep credentials and roster mappings outside the evidence document and logs. |
| Inferred scoring | Observable events are transformed into unsupported judgments | Separate reviewed mapping, explicit terminology, and prohibition by default. |
| Partial transfer | Destination accepts only part of a document | Return field-level result or reject atomically; never report full success for partial acceptance. |
| Network interruption | User cannot tell whether a write occurred | Idempotent retry and destination receipt lookup before repeating the operation. |

## Logging and diagnostics

The current offline prototype performs no transfer logging. A future adapter may need operational diagnostics, but logs must be minimized.

Allowed by default:

- adapter name and version;
- operation result category;
- evidence schema version;
- module ID when institutional policy permits it;
- non-sensitive correlation or idempotency reference;
- error code that does not embed payload content or credentials.

Prohibited by default:

- complete evidence documents;
- names, emails, account tokens, session cookies, or roster IDs;
- free-form learner content;
- reading preferences;
- inferred mastery or diagnostic labels;
- source documents or copyrighted content copied from the module.

Operational logs must have a separately documented retention period. Debug mode must not weaken payload minimization silently.

## Backups and copies

Raiatea cannot guarantee deletion of copies it does not control. A future adapter and institutional deployment must distinguish:

- active LMS records;
- LMS audit records;
- institutional backups;
- browser-local source records;
- downloaded JSON files;
- files shared through email, messaging, cloud drives, or removable media;
- test and staging environments.

A deletion confirmation should state which layers were affected and which remain subject to a separate retention schedule. “Deleted” must not be used when the operation only hides or detaches a record.

## Versioning and migration

Learner-evidence v1 has explicit replacement semantics and exact module compatibility checks. Future changes must follow these rules:

- do not add fields to v1 and assume old validators will ignore them;
- publish a new version when meaning or required structure changes;
- keep migrations explicit, testable, and reviewable;
- show the learner when a migration changes or drops information;
- preserve the original file unless the learner explicitly chooses to create a migrated copy;
- do not use an LMS adapter as an undocumented migration layer.

Stable step identifiers may eventually reduce dependence on ordered authored titles, but they require a separate design decision and migration policy.

## Adoption checklist

Before enabling any external adapter, confirm that:

- [ ] the destination and purpose are documented;
- [ ] the evidence allowlist is unchanged or a new reviewed schema exists;
- [ ] identity/authentication context is separate from the evidence document;
- [ ] outbound and inbound previews are explicit;
- [ ] overwrite/append/create semantics are visible;
- [ ] authorization and roster mapping are tested;
- [ ] unsupported versions and incompatible modules fail closed;
- [ ] duplicate and partial-transfer behavior is defined;
- [ ] retention, backups, deletion ownership, and learner notices are defined;
- [ ] logs exclude payloads, credentials, and inferred data;
- [ ] offline export and restore continue to work without the adapter;
- [ ] provider removal does not make existing JSON files unreadable;
- [ ] threat-model and privacy review findings are tracked to commits and tests.

## Deliberate non-goals

This document does not authorize or design:

- background synchronization;
- learner cloud accounts;
- teacher dashboards;
- grade passback;
- mastery scoring;
- behavioral analytics;
- identity federation;
- multi-module evidence bundles;
- cryptographic signing or encryption;
- a specific LMS standard or vendor protocol.

Each may be considered later as a separate parent/child issue chain with its own data model, threat model, tests, and review.

## Traceability

| Capability | Issue | PR | Result |
| --- | --- | --- | --- |
| Privacy-safe one-module export | #9 | #10 | Versioned allowlisted JSON export and validator. |
| Import structure and compatibility | #11 | #12 | Side-effect-free exact compatibility checks. |
| Explicit restore and conflict preview | #13 | #14 | Offline confirmation, replacement, and stale/race protections. |
| Retention and future LMS boundary | #16 | pending | This policy and architecture boundary. |

## Open design questions

The following questions remain intentionally unresolved:

- whether future module revisions need stable step identifiers;
- whether transfer receipts need a portable schema;
- whether evidence files require signing or encryption for particular deployments;
- how institutional deletion receipts represent backup expiry;
- whether an external adapter should support only whole-document atomic writes;
- which LMS standard, if any, fits after the provider-neutral port is validated.

They must not be answered implicitly by the first provider integration.
