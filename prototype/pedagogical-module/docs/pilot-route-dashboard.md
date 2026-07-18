# Pilot route dashboard and cross-module progression contract

Status: initial implementation contract for issue #63 under parent #58.

## Goal

Add a learner-facing dashboard to the runnable pilot launcher. The dashboard reads only the two existing module-local progress records, derives a narrow route status, and recommends the next module without locking navigation or creating a new evidence format.

## 1. Authoritative route

The dashboard uses the generated `pilot-manifest.json` order. It does not duplicate module IDs, titles, revisions, or output paths in a second hand-maintained route table.

Each route entry exposes only:

- canonical module ID;
- canonical revision;
- authored title;
- relative module link;
- derived route status;
- advisory next action.

## 2. Storage boundary

For each module, the dashboard may read only:

```text
raiatea-progress:<module-id>
```

It must not enumerate all browser storage keys or read unrelated entries. It never writes, resets, repairs, migrates, or deletes module progress.

Storage access remains same-origin and browser-local. No value is sent to a server, placed in a URL, logged remotely, or embedded in the pilot manifest.

## 3. Closed progress states

The initial dashboard exposes exactly three learner-facing states:

- `not-started` — no valid progress object exists, or all allowlisted observable fields remain at their initial empty values;
- `in-progress` — at least one allowlisted observation shows activity, but the completion rule is not satisfied;
- `locally-completed` — every canonical step has `activityCompleted: true` or `correct: true` in the existing module-local progress representation.

This is a route-navigation aid, not a mastery judgment, grade, diagnosis, or credential.

Use of remediation does not prevent local completion. It remains explanatory observable history only.

## 4. Fail-closed parsing

A storage entry is accepted only when it is a JSON object with the exact module-local progress structure already consumed by the generated module runtime.

Malformed JSON, wrong types, missing required arrays, inconsistent lengths, unknown module IDs, or unsupported shapes are treated as `not-started` for route display and produce no copied free-form data.

The dashboard must not display raw storage content or exception text.

## 5. Recommendation policy

Recommendation is deterministic and advisory:

1. recommend the first module that is not `locally-completed`;
2. if every module is locally completed, recommend reviewing the route summary;
3. all module links remain enabled regardless of recommendation;
4. no redirect, unlock gate, modal block, or hidden prerequisite is introduced.

## 6. Refresh behavior

The dashboard refreshes derived state:

- on initial load;
- on `pageshow`, including browser back/forward cache restoration;
- on `visibilitychange` when the document becomes visible;
- on same-origin `storage` events when another tab changes one of the exact route progress keys.

No polling or background network activity is used.

## 7. Accessibility and fallback

The launcher remains useful without JavaScript: module links and route order are present in static HTML.

With JavaScript enabled, status text is exposed in normal document content and recommendation changes use a polite live region. Status is not communicated by color alone.

## 8. Privacy allowlist

Dashboard state may contain only:

- module ID, revision, title, relative file;
- one closed status token;
- completion counts derived from canonical steps;
- one advisory recommended module ID.

It excludes learner identity, timestamps, free text, source excerpts, account/device IDs, analytics, telemetry, diagnosis, mastery inference, network destinations, and unrelated local storage.

## 9. Verification matrix

Tests must cover:

- empty storage;
- valid initial empty progress;
- partial attempts;
- remediation use;
- all-step local completion;
- malformed JSON and wrong object shape;
- unrelated localStorage keys;
- pageshow/visibility/storage refresh;
- all links remaining enabled;
- no dashboard writes to localStorage;
- no network requests outside the local pilot server;
- unchanged standalone module, evidence, migration, and pilot-builder regressions.

## 10. Deferred work

- multi-module evidence export;
- teacher dashboard or cohort aggregation;
- account or LMS synchronization;
- configurable completion policy;
- server persistence;
- automatic unlocking or grading;
- AI-generated recommendations.
