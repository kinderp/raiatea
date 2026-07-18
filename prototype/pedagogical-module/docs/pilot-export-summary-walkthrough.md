# Pilot evidence export and summary walkthrough contract

Status: initial implementation contract for issue #65 under parent #58.

## Goal

Make the existing module-local summary and explicit learner-evidence v1 export directly understandable and testable from the generated pilot, without changing progress semantics or creating a route-wide evidence format.

## 1. Three distinct learner-facing views

The pilot must keep these concepts separate:

1. **Route dashboard status** — a navigation aid derived from current browser-local module progress;
2. **Module summary** — the existing observable per-step recap inside one module;
3. **Exported evidence** — one explicit, user-initiated JSON file for the current module only.

None of these is a mastery score, grade, diagnosis, credential, or learner profile.

## 2. Walkthrough placement

The launcher provides static, accessible guidance explaining:

- how to open a module;
- how to reach the existing summary panel;
- how to interpret attempts, correctness, remediation use, and completed recovery activities;
- how to select **Esporta evidenze JSON**;
- that the resulting file describes only the current module;
- that route-wide export remains unavailable.

Guidance must remain useful without JavaScript and must not duplicate the module runtime implementation.

## 3. Export boundary

Export remains exactly the existing learner-evidence v1 browser operation:

- initiated only by an explicit learner click;
- local browser download only;
- predictable filename `<module-id>-evidence-v1.json`;
- existing closed v1 document shape;
- current module ID, title, language, step count, allowlisted source context, current step, and observable step evidence only;
- no network request, automatic upload, background backup, account, timestamp, analytics, telemetry, or unrelated storage.

The walkthrough does not add or alter export fields.

## 4. Non-destructive behavior

Export must not change:

- module progress;
- dashboard status or recommendation;
- reading preferences;
- pending unrelated storage;
- evidence import state;
- route manifest or generated module content.

Opening guidance without clicking export produces no download and no mutation.

## 5. Evaluator scenarios

The evaluator documentation and browser tests cover:

- empty module progress;
- one attempted step;
- remediation used;
- locally completed module;
- explicit export click;
- predictable filename;
- downloaded JSON structural shape and module identity;
- observable values matching the browser-local module record;
- route dashboard and unrelated localStorage unchanged after export;
- absence of external requests.

## 6. Accessibility

Walkthrough headings, ordered steps, explanatory notes, and links use normal document structure. Export remains an existing labeled button in the module. Guidance must not rely on color, modal interruption, or hidden hover text.

## 7. Privacy and wording

Allowed wording describes only observed interaction state. It must not claim that the learner has mastered, failed, understood, or been diagnosed. The downloaded file is described as evidence for one module, not a complete portfolio.

## 8. Verification

Tests must prove:

- guidance is present in generated `index.html`;
- both module links remain usable;
- download occurs only after the explicit export click;
- filename and JSON match learner-evidence v1;
- export is module-scoped and privacy-safe;
- no progress or unrelated state changes;
- all prior pilot, dashboard, evidence, migration, and standalone module tests remain green.

## 9. Deferred work

- multi-module evidence bundles;
- route-wide portfolio export;
- learner-evidence v2 browser export/import;
- signing, encryption, cloud/LMS transfer, accounts, identity, analytics, or automatic backups.
