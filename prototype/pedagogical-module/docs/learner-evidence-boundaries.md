# Learner evidence: retention, deletion, privacy, and integration boundaries

Status: architecture and privacy decision for the current pedagogical-module prototype.

This document describes what Raiatea does today and the constraints that any future evidence adapter must preserve. It is a technical design boundary, not legal advice or a compliance certification.

## 1. Current data flow

The self-contained pedagogical module has no evidence server and performs no background network transfer.

```text
learner interaction
→ observable module progress
→ browser localStorage for the current origin
→ optional user-initiated JSON export
→ optional user-initiated compatible JSON restore
```

The core module does not create learner accounts, attach evidence to an identity, upload evidence, infer mastery, or maintain a remote retention system.

## 2. Data classes and storage locations

| Data class | Current location | Written by | Leaves the browser automatically? |
| --- | --- | --- | --- |
| Current module progress | `localStorage`, key `raiatea-progress:<module-id>` | module interactions and explicit compatible restore | No |
| Reading preferences | `localStorage`, key `raiatea-reading-settings` | learner reading controls | No |
| Pending import preview | JavaScript memory only | explicit file selection | No |
| Exported v1 evidence file | learner-selected download location | explicit export action | No automatic transfer |
| Imported file contents | browser memory while validating/restoring | explicit file selection | No |

The v1 progress fields are limited to:

- `currentStep`;
- per-step `attempts`;
- per-step `correct`;
- per-step `usedRemediation`;
- per-step `activityCompleted`.

The exported document also contains allowlisted module and source context needed to interpret and validate those observations. That context is not copied into browser progress during restore.

## 3. Retention model

### 3.1 Browser-local progress

Raiatea does not impose a time-based retention period on browser-local progress. The browser retains `localStorage` according to its own storage policy until one of the following occurs:

- the learner selects **Azzera avanzamento** for the current module;
- the learner or device administrator clears site data;
- the browser removes site data because of browser-specific storage, privacy, or device-management policy;
- the origin changes, so the module no longer addresses the same storage namespace.

No server copy exists in the current architecture, so Raiatea has no remote progress record to expire or delete.

### 3.2 Reading preferences

Reading preferences are stored separately from learner evidence. **Azzera avanzamento** does not delete `raiatea-reading-settings`. The reading toolbar's own reset action removes those preferences. Clearing browser site data may remove both progress and reading preferences according to browser behavior.

### 3.3 Pending imports

A selected compatible document remains only as an in-memory pending snapshot. It is invalidated by:

- cancellation;
- reset;
- a newer file selection;
- any local progress change after the preview;
- page reload or page close.

A pending snapshot is never persisted before explicit confirmation.

### 3.4 Exported files

An exported JSON file is a separate, user-controlled copy. After download:

- its location and lifetime are controlled by the learner, operating system, browser, backup software, removable media, or any tool to which the learner provides it;
- **Azzera avanzamento** does not delete it;
- clearing browser storage does not delete it;
- Raiatea cannot revoke or remotely erase it because the current module does not know where the file was stored or copied.

Documentation and future interfaces must never imply that deleting browser progress also deletes exported copies.

## 4. Deletion semantics

| User action | Current module progress | Reading preferences | Pending import | Exported files |
| --- | --- | --- | --- | --- |
| **Azzera avanzamento** | Deletes/reinitializes only `raiatea-progress:<current-module-id>` | Preserved | Invalidated | Unchanged |
| Reading settings **Ripristina** | Preserved | Deletes/reinitializes `raiatea-reading-settings` | Preserved unless progress changes | Unchanged |
| Cancel import | Preserved | Preserved | Invalidated | Source file unchanged |
| Clear browser site data | Browser-dependent deletion, normally removed for the origin | Browser-dependent deletion, normally removed for the origin | Lost with page context | Unchanged |
| Delete exported file in the operating system | Preserved | Preserved | Preserved | Deletes only the selected filesystem copy, subject to OS/backup behavior |

A future external adapter must define its own deletion behavior explicitly. Core deletion controls must not claim to delete evidence held by an LMS, cloud service, backup, email attachment, or another device.

## 5. Privacy and purpose boundaries

### 5.1 Data minimization

The core evidence contract records observable interactions needed to resume and describe the module path. It must not add by default:

- learner name, email address, username, account ID, or device ID;
- IP address, location, contacts, cookies, advertising identifiers, or browser fingerprint;
- theme, font size, density, alignment, motion, or other reading preferences;
- free-form learner text;
- inferred mastery, intelligence, motivation, diagnosis, disability, or personal profile;
- timestamps, session replay, clickstream, or background telemetry;
- teacher comments, grades, disciplinary information, or institutional identifiers.

A future use case that needs additional data requires a separate contract and cannot silently widen v1.

### 5.2 Purpose limitation

The current purpose is narrow:

- resume one compatible module;
- show observable progress to the learner;
- let the learner move that progress explicitly between compatible local artifacts or tools.

The evidence must not be repurposed automatically for advertising, behavioral profiling, high-stakes grading, surveillance, eligibility decisions, or automated diagnosis.

### 5.3 Learner control

Export, selection, preview, and restore are explicit learner actions. Future adapters must preserve the distinction between:

- **preview or validate**, which must not mutate or transmit evidence; and
- **send, restore, or replace**, which requires an explicit action with a clear destination and consequence.

Silence, page load, a quiz answer, or enabling an adapter must not be treated as consent to upload historical evidence.

## 6. Trust boundaries

```text
┌──────────────────────────────────────────────────────────────┐
│ Self-contained module                                       │
│ - module data                                                │
│ - local progress                                             │
│ - validation, preview, explicit restore                      │
│ - no credentials or network queue                            │
└──────────────────────────┬───────────────────────────────────┘
                           │ explicit user action + allowlisted document
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Optional adapter boundary                                    │
│ - version and compatibility validation                       │
│ - destination-specific mapping                               │
│ - consent/purpose/retention display                          │
│ - authentication and transport, if required                  │
└──────────────────────────┬───────────────────────────────────┘
                           │ provider-specific protocol
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ External system                                              │
│ - LMS, portfolio, local archive, or another tool             │
│ - separate controller/retention/deletion responsibilities    │
└──────────────────────────────────────────────────────────────┘
```

The adapter boundary is a separate component. Provider credentials, network calls, retry queues, offline upload caches, and destination identifiers must not be embedded in the generated pedagogical HTML artifact.

## 7. Provider-neutral future integration points

A future adapter may consume the v1 document only after the core export has been produced or after equivalent allowlisted evidence has been validated. The adapter interface should separate these operations:

1. `inspectCapabilities()` — describe supported evidence versions and destination features without accessing learner evidence.
2. `validate(document, moduleContext)` — perform structural and compatibility checks without mutation or transmission.
3. `previewMapping(document)` — show exactly which fields would be mapped, omitted, or transformed.
4. `send(document, destination, authorization)` — transmit only after an explicit learner or authorized educator action.
5. `reportReceipt()` — return a destination receipt without changing the local evidence contract.
6. `requestDeletion(reference)` — optional adapter operation whose effect and limitations are destination-specific and must never be represented as core browser deletion.

These names are conceptual, not a committed API.

## 8. Mandatory safeguards for an LMS adapter

Before an LMS integration can be considered, its issue and PR must define and test:

- supported Raiatea evidence versions;
- structural validation and module compatibility behavior;
- the exact field mapping and every dropped or derived field;
- the legal/organizational purpose and authorized actor outside this technical document;
- destination identity and account-linking behavior;
- retention duration or retention decision owner at the destination;
- deletion request path and what copies may remain in backups or institutional records;
- authentication, authorization, transport security, and credential storage;
- explicit send confirmation and a clear destination label;
- retry, duplicate-send, idempotency, and partial-failure behavior;
- offline queue behavior, including how queued evidence is displayed and deleted;
- audit events that avoid storing the evidence payload unnecessarily;
- tests proving that reading settings, unrelated storage, unknown fields, and inferred learner traits are not transmitted.

The adapter must not change the meaning of browser **Azzera avanzamento**. Local deletion and external deletion remain separate actions with separate feedback.

## 9. Versioning and compatibility

The current interchange identifier is:

```json
{
  "format": "raiatea-learner-evidence",
  "version": 1
}
```

Future changes follow these rules:

- unknown versions are rejected, not guessed;
- additive or breaking changes require an explicit version decision;
- migration is a separate, testable operation and must preserve the original document until the learner confirms replacement;
- stable module/step identifiers should be evaluated before supporting module-title or step-title changes across revisions;
- external adapters must declare supported versions rather than accepting arbitrary objects.

## 10. Forbidden defaults

The following remain forbidden unless a future issue explicitly changes the architecture with privacy, security, migration, and failure-mode review:

- background evidence upload;
- automatic account creation or identity attachment;
- silent synchronization on page load or quiz completion;
- transmitting the complete `localStorage` namespace;
- using reading preferences as learner evidence;
- adding inferred mastery or personal profiles to v1;
- silently merging histories;
- silently overwriting incompatible progress;
- embedding provider credentials in generated modules;
- claiming that local reset deletes remote or exported copies;
- making network access a requirement for reading or completing a module.

## 11. Review checklist for future evidence work

Every future evidence PR should answer:

- What exact data is read, written, exported, imported, or transmitted?
- Which storage key, file, queue, or destination owns each copy?
- What user action creates each copy?
- How can each copy be deleted, and what cannot be deleted by Raiatea?
- Is validation side-effect free?
- Can an obsolete asynchronous action win over a newer explicit action?
- Can a preview become stale before confirmation?
- Are unknown versions and fields rejected?
- Are identity and inferred traits still excluded by default?
- Does the generated module remain fully usable offline?

## 12. Decision summary

Raiatea learner evidence is local-first, observable, minimal, versioned, and portable only through explicit actions. Browser progress, reading preferences, pending imports, exported files, and future external copies are separate data stores with separate lifecycles. The core module owns only its browser-local record. Any LMS or cloud integration must live behind an explicit adapter boundary and define its own purpose, identity, retention, deletion, security, and failure semantics before implementation.
