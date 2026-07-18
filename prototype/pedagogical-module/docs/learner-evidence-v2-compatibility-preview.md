# Learner-evidence v2 compatibility classification and preview contract

Status: initial design contract for issue #46.

This increment classifies one learner-evidence v2 document against one exact caller-supplied target canonical module revision and generates a deterministic read-only preview. A caller may also supply one direct migration manifest and its exact canonical source module revision. The increment never writes browser storage, edits an input, confirms a migration, or replaces the original evidence document.

## 1. Inputs

The classifier receives:

1. `evidence`: one learner-evidence v2 document;
2. `targetModule`: one canonical target module revision;
3. optionally, as one inseparable migration context:
   - `sourceModule`: the exact canonical revision named by the evidence;
   - `manifest`: one direct migration manifest from `sourceModule` to `targetModule`.

A caller must provide either neither optional input or both. The classifier does not search a registry, choose among manifests, infer a path, or chain transitions.

Every supplied document is structurally validated by its existing validator before classification. A supplied manifest is also contextually validated against the supplied source and target modules before its operations are interpreted.

## 2. Result model

The API returns one closed result object with these conceptual fields:

- `classification`: `exact`, `declared-lossless`, `declared-partial`, `incompatible`, or `unsupported`;
- exact evidence source identity: module ID and opaque revision;
- exact requested target identity: module ID and opaque revision;
- `manifestStatus`: `not-needed`, `applicable`, `missing`, `invalid`, `mismatched`, or `unsupported`;
- ordered step preview entries;
- current-position preview;
- deterministic human-readable summary and issues;
- `candidateAvailable`: whether a later layer could construct a complete non-persisted target evidence candidate without an additional policy decision.

The result is data, not authorization. `declared-lossless`, `declared-partial`, and `candidateAvailable` never imply user confirmation or state mutation.

## 3. Classification precedence

Classification uses this fixed precedence and stops at the first applicable branch.

### 3.1 Unsupported — Class E

Return `unsupported` when a recognized input family cannot be interpreted by the current implementation, including:

- unsupported evidence format or version;
- unsupported manifest format or version;
- an operation or result-model feature outside the closed implemented vocabulary.

Unsupported data is not coerced into another version and is not treated as merely incompatible.

Malformed JSON, closed-schema violations, duplicate identities, and other invalid documents remain explicit validation failures. They do not produce a compatibility claim.

### 3.2 Exact — Class A

Return `exact` when the existing Class A checker proves that the evidence exactly matches `targetModule` by:

- module ID;
- opaque revision;
- step count;
- ordered stable-step identity sequence;
- current step ID and index.

A manifest is neither required nor consulted for an exact result. No migration preview is needed; every source step is shown as preserved in place and `candidateAvailable` is false because the original document already matches the target.

### 3.3 Incompatible — Class D before manifest interpretation

Return `incompatible` when:

- evidence and target module IDs differ;
- evidence and supplied source module identity do not match exactly;
- a non-exact transition has no complete optional migration context;
- the supplied manifest is structurally valid but does not contextually bind to the exact supplied source and target revisions;
- the evidence contains a stable step ID absent from the exact source inventory;
- the manifest cannot account deterministically for the evidence current step.

The result must state the missing or mismatched precondition. It must not guess a nearby revision or choose an arbitrary manifest.

### 3.4 Declared lossless — Class B

Return `declared-lossless` only when all of the following hold:

- the evidence exactly matches the supplied source module identity and ordered stable-step inventory;
- the manifest exactly and contextually binds that source revision to the supplied target revision;
- every source step is covered by `preserve`;
- every target step is covered by `preserve`;
- there are no `retire` or `introduce` operations;
- every allowlisted evidence field can be copied to the same stable step ID without omission, reset, aggregation, duplication, or semantic reinterpretation;
- the evidence `currentStepId` is preserved and its target index is uniquely determined from target authored order.

A title change or reorder may therefore be lossless. Numeric indexes are recalculated from target order; stable IDs remain the identity keys.

### 3.5 Declared partial — Class C

Return `declared-partial` when an applicable direct manifest contains at least one `retire` or `introduce` operation and all preserved source observations remain attributable by exact stable ID.

The preview must distinguish:

- preserved steps whose allowlisted observations remain attributable;
- retired source steps retained only as historical source evidence;
- introduced target steps with explicit empty/unobserved target state;
- current position preserved and remapped to its target index, or unresolved because the active source step is retired.

An unresolved current position makes a complete candidate unavailable but does not erase the factual partial classification. The preview must state that a future confirmation/application policy must choose a target position before any target document can be completed.

The current manifest vocabulary does not support split, merge, fan-out, fan-in, aggregation, or semantic transformation. Such features are `unsupported`, not partial.

## 4. Ordered step preview

Preview entries are emitted in deterministic groups:

1. target steps in target authored order, each marked `preserved` or `introduced`;
2. retired source steps in source authored order.

Each entry contains only allowlisted factual data:

- stable `stepId`;
- source index when present;
- target index when present;
- source and target authored title snapshots when present;
- status: `preserved`, `introduced`, or `retired`;
- evidence disposition: `copied`, `empty`, or `historical-only`;
- observable source evidence snapshot when present.

Titles are explanatory snapshots and never determine mapping or classification.

## 5. Current-position preview

The current-position result is one of:

- `unchanged`: exact target identity and index already match;
- `remapped`: current stable ID is preserved and its target index is deterministic;
- `unresolved-retired`: current stable ID is retired and no target identity is selected;
- `invalid`: the current stable ID is not valid in the exact source evidence context.

The classifier never selects the next index, previous index, nearest preserved step, first introduced step, or any other fallback for `unresolved-retired`.

## 6. Candidate boundary

This increment may expose `candidateAvailable` and a deterministic candidate plan, but it must not persist or download a migrated document.

A complete non-persisted target candidate is available only for:

- Class B; or
- Class C when the current source step is preserved and therefore remaps deterministically.

For a candidate plan:

- preserved per-step evidence is copied by exact stable ID;
- introduced target steps receive zero attempts and all observable outcome booleans `false`;
- target indexes and authored title snapshots come from `targetModule`;
- retired source evidence remains only in the preview and is not silently inserted into active target evidence;
- the original evidence input remains unchanged.

If the current step is retired, `candidateAvailable` is false and no candidate document is produced.

Actual candidate serialization, confirmation, original-copy preservation, browser storage writes, and restore behavior remain separate reviewed work unless this issue explicitly accepts them after tests prove the boundary.

## 7. Error and output rules

- Structural validation errors are namespaced by input and precede classification.
- Result ordering is stable across runs.
- All issues are accumulated only where doing so cannot create false downstream claims from an invalid prerequisite.
- Revision values are compared only for equality and never interpreted as chronology, precedence, distance, or adjacency.
- The CLI exits `0` for `exact`, `declared-lossless`, and `declared-partial` previews; it exits non-zero for validation failure, `incompatible`, or `unsupported`.
- Machine-readable output and human-readable output describe the same classification and preview.

## 8. Privacy and side effects

The classifier and preview:

- operate only on caller-supplied local documents;
- make no network request or registry lookup;
- do not read browser storage;
- do not mutate input objects or files;
- do not write a candidate automatically;
- do not add learner identity, timestamps, analytics, free text, inferred mastery, diagnosis, or device data;
- preserve learner-evidence v1 unchanged.

## 9. Deferred work

- multi-hop path discovery or chaining;
- manifest registry selection;
- split or merge policy;
- semantic correction policy beyond exact stable-ID preservation;
- browser v2 export/import;
- user confirmation and conflict UI;
- atomic original-copy preservation and storage mutation;
- cloud, LMS, account, analytics, signing, or encryption behavior.
