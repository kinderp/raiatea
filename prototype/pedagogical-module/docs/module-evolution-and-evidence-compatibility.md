# Module evolution and learner-evidence compatibility

Status: architecture decision for future module evolution. This document defines identity, revision, and migration responsibilities; it does not change the current module schema, learner-evidence v1, validators, or restore behavior.

Related work: parent issue #19, decision issue #20, and the current privacy boundary in [`learner-evidence-boundaries.md`](learner-evidence-boundaries.md).

## 1. Decision context

Learner-evidence v1 identifies a module by its authored module `id` and treats ordered step titles and indexes as a conservative compatibility boundary. This protects the current restore flow from silently applying observations to a changed pedagogical route, but it also means that harmless wording or ordering changes make an export incompatible.

Raiatea needs a durable model for module evolution before adding stable step identifiers, another evidence version, or executable migration support. The model must preserve historical meaning rather than guessing that two similar-looking steps are equivalent.

## 2. Scope and non-goals

This decision defines:

- durable module identity;
- explicit module revision semantics;
- immutable step identity within a pedagogical route;
- rules for rename, reorder, insertion, correction, split, merge, retirement, and replacement;
- compatibility classes;
- responsibilities of authored migration manifests;
- privacy, security, and failure constraints for future migration tooling.

This decision does not:

- modify existing module JSON files or schemas;
- add step IDs to the current canonical module model;
- create learner-evidence v2;
- migrate or restore any document;
- infer identity through titles, indexes, semantic similarity, embeddings, or an LLM;
- add cloud synchronization, learner accounts, or background transfer.

## 3. Terms

### Pedagogical route

The durable learning path represented by a module: its topic, intended outcomes, conceptual boundaries, and progression responsibility. The route can evolve across authored revisions without becoming a different module every time wording or presentation changes.

### Module ID

The durable identifier of the pedagogical route. It does not identify one file, build artifact, translation, or particular revision.

### Module revision

An explicit, author-assigned identifier for one published state of a module route. A revision changes only through a deliberate author decision; it is never derived automatically from timestamps, hashes, titles, step count, or file names.

### Step ID

A future immutable identifier for one pedagogical step concept within a module route. It is independent of title, position, display language, and visual representation.

### Evidence document

A versioned record of observable learner interactions. Evidence records what happened against a particular published module context; it does not prove mastery and must not be silently reinterpreted after the module changes.

### Migration manifest

A future, authored, directional, reviewable mapping from one module revision to another. A manifest describes intended identity continuity and incompatibilities. It does not apply changes by itself.

## 4. Identity model

### 4.1 Module identity

The module `id` identifies the durable pedagogical route.

The following normally preserve the same module ID:

- correcting wording or typographical errors;
- changing presentation or visual layout;
- renaming a step while preserving its pedagogical responsibility;
- reordering existing steps;
- inserting a new step into the route;
- retiring or replacing a step through an explicit revision decision;
- translating the route while preserving the same conceptual responsibilities, when the project chooses a shared multilingual route.

The following require a new module ID unless an explicit architecture decision says otherwise:

- changing the primary learning outcome into a materially different route;
- repurposing the module for a different conceptual subject;
- reusing an old ID for an unrelated module;
- replacing most of the route while claiming historical evidence remains directly equivalent.

A module ID must never be recycled after retirement.

### 4.2 Module revisions

Each published state of a route may carry an explicit revision identifier in a future schema. The author increments or replaces that identifier whenever a change can affect interpretation, compatibility, migration, or reproducibility.

A new revision is required for:

- any authored step rename or reorder;
- insertion, removal, retirement, split, merge, or replacement;
- a content correction that changes the meaning of a diagnostic answer, explanation, activity, or recorded evidence;
- a contract change that affects rendering, validation, provenance, or evidence interpretation;
- a source or transformation correction that changes the pedagogical claim represented by the route.

A rebuild that produces equivalent output from unchanged authored content does not create a new module revision.

Revision identifiers are opaque authored values. Raiatea may validate syntax and uniqueness, but it must not infer semantic ordering from the string unless a future contract explicitly defines such ordering.

### 4.3 Step identity

A future `step.id` identifies one stable pedagogical responsibility inside a module route.

A step ID:

- is immutable after publication;
- is independent of title, array position, language, and visual node identifiers;
- is scoped by the module ID;
- is never reused for a different pedagogical responsibility;
- may remain present in migration history after the step is retired;
- cannot be assigned automatically by title matching or content similarity.

The pair `(moduleId, stepId)` is the stable conceptual identity. A module revision identifies which published definition of that route and step set was used.

## 5. Change rules

| Change | Identity decision | Revision required | Automatic evidence reinterpretation |
| --- | --- | --- | --- |
| Typographical correction with no semantic effect | Preserve module and step identity | Yes, for published reproducibility | No for v1; future versions require declared compatibility |
| Step title rename | Preserve step ID when responsibility is unchanged | Yes | Never inferred from the title |
| Step reorder | Preserve step IDs | Yes | Never inferred from indexes |
| Insert new step | Create a new step ID | Yes | Existing steps may remain identifiable; missing evidence stays missing |
| Correct explanation without changing expected evidence | Preserve step ID | Yes | Requires authored compatibility decision |
| Change accepted answer or evidence meaning | Preserve or replace step ID only through explicit author decision | Yes | Default incompatible without an explicit mapping and rationale |
| Split one step into multiple steps | Retire or transform the old step; create new step IDs | Yes | No automatic distribution of historical evidence |
| Merge multiple steps into one | Retire source steps; create or designate one target step ID explicitly | Yes | No automatic aggregation of historical evidence |
| Retire a step | Preserve historical step ID as retired | Yes | Historical evidence remains historical; it is not reassigned |
| Replace a step with a different responsibility | Retire old ID and create a new ID | Yes | Incompatible by default |
| Replace the route with a different learning outcome | New module ID | Yes | Incompatible |

## 6. Required examples

### 6.1 Rename

Revision `r1` contains step `attention-score` titled “Calcola lo score”. Revision `r2` titles the same step “Confronta query e key”. If the pedagogical responsibility is unchanged, the step ID remains `attention-score`, but the module revision changes. Learner-evidence v1 remains incompatible because its current contract compares authored titles.

### 6.2 Reorder

Revision `r1` orders `embedding`, `query-key`, `weighted-sum`. Revision `r2` introduces a different presentation order while keeping the same step IDs. A future evidence format can identify observations by step ID, but ordering-dependent progress such as `currentStep` still needs an authored migration decision. Indexes must never be used as durable identity.

### 6.3 Insertion

Revision `r2` inserts `softmax-normalization` between existing steps. The new step receives a new ID. Historical observations for existing step IDs may remain attributable, but the new step has no historical completion evidence. A migration preview must state that absence rather than marking the new step complete.

### 6.4 Content correction

A spelling fix preserves the step ID. A correction that changes which answer is correct or what the activity measures requires explicit compatibility classification. The author must state whether previous observations still mean the same thing. Tooling must default to incompatible when that decision is absent.

### 6.5 Split

Revision `r1` has `self-attention` as one step. Revision `r2` replaces it with `score-computation` and `value-aggregation`. Historical completion of `self-attention` cannot be copied automatically to both new steps. The manifest may preserve the old observation as historical context, but current completion for the new steps remains unset unless a separate, explicitly justified policy exists.

### 6.6 Merge

Revision `r1` has `query-key-score` and `softmax`. Revision `r2` combines them into `attention-weights`. Attempts and completion from two source steps cannot be summed, averaged, or collapsed automatically. The manifest must declare the merge and the preview must show that current evidence cannot be reconstructed without loss.

### 6.7 Retirement

A retired step retains its historical ID and evidence context. It disappears from the active route but is not erased from migration history. A future export or archive may preserve it as retired historical evidence; the current route must not silently attach it to another step.

### 6.8 Incompatible replacement

Revision `r2` replaces a factual recall step with a programming exercise. Even if the title is similar and occupies the same position, the old step ID is retired and a new ID is created. Historical evidence is incompatible with the new responsibility.

## 7. Compatibility classes

Future compatibility checks and manifests should use explicit classes rather than one ambiguous boolean.

### Class A: exact

The evidence format, module ID, module revision, and required step identities match exactly. No migration is needed.

### Class B: declared lossless migration

An authored manifest maps the source revision to the target revision without changing the meaning of retained observations. Examples may include a pure rename or reorder where step identities and evidence semantics are preserved.

“Lossless” applies only to the allowlisted evidence fields covered by the manifest. It does not imply pedagogical equivalence beyond those fields.

### Class C: declared partial migration

Some observations remain attributable, while other fields or steps must be omitted, retired, or reset. Insertion, retirement, and some corrections may fall here. The preview must identify every preserved, omitted, reset, or historical-only value.

### Class D: incompatible

No safe authored mapping exists, required manifest links are missing, or the route/evidence semantics changed materially. Restore or migration must stop without mutating current progress.

### Class E: unsupported

The evidence version, manifest version, module revision, operation, or feature is unknown to the current tool. Unsupported data is rejected, not guessed or coerced.

## 8. Learner-evidence v1 remains frozen

This decision does not widen learner-evidence v1.

The existing v1 contract continues to use:

- exact module ID;
- step count and sequence length;
- ordered indexes;
- ordered authored step titles;
- the current structural and privacy allowlists.

Therefore:

- a rename or reorder remains incompatible with v1;
- a future module revision field is not retrofitted into v1;
- a future step ID is not added to v1;
- v1 files are not silently upgraded during validation, preview, or restore;
- current v1 restore remains explicit replacement after conservative compatibility checks.

A future evidence version may carry module revision and step IDs only through a separate schema, validator, sample, browser behavior, documentation, and migration decision.

## 9. Proposed future migration-manifest shape

The following is a design sketch, not a committed schema or executable contract:

```json
{
  "format": "raiatea-module-migration",
  "version": 1,
  "moduleId": "self-attention",
  "fromRevision": "r1",
  "toRevision": "r2",
  "classification": "partial",
  "steps": [
    {
      "operation": "preserve",
      "from": ["embedding"],
      "to": ["embedding"]
    },
    {
      "operation": "split",
      "from": ["self-attention"],
      "to": ["score-computation", "value-aggregation"],
      "evidencePolicy": "historical-only"
    },
    {
      "operation": "insert",
      "from": [],
      "to": ["softmax-normalization"],
      "evidencePolicy": "reset"
    }
  ],
  "notes": "Authored rationale and review context"
}
```

A committed manifest contract must later define closed enums, identifier syntax, uniqueness, operation-specific cardinality, required rationale, optional provenance, and exact evidence-field behavior.

## 10. Manifest rules

A future migration manifest must be:

- authored, never inferred from similarity;
- directional from one explicit revision to one explicit revision;
- versioned independently from module and evidence formats;
- structurally validated before compatibility evaluation;
- side-effect free during validation and preview;
- reviewable in source control;
- explicit about preserved, reset, omitted, retired, and historical-only evidence;
- rejected if it contains unknown operations, duplicate targets, ambiguous mappings, cycles, or mismatched module IDs;
- chained only through an explicit validated path, never by selecting an arbitrary “closest” revision;
- applied only after an explicit preview and confirmation.

The source evidence document must remain unchanged. Migration creates a new candidate document or snapshot; it never edits the original file in place.

## 11. Responsibilities

| Component or actor | Responsibility |
| --- | --- |
| Module author | Assign module revisions and future step IDs; decide identity continuity; author migration rationale |
| Module schema and validator | Enforce syntax, uniqueness, required fields, and internal references without inferring semantics |
| Evidence validator | Validate one evidence version without silently upgrading it |
| Compatibility checker | Classify exact, declared migration, incompatible, or unsupported cases without mutation |
| Migration validator | Validate a manifest and its source/target module contexts |
| Migration preview | Show preserved, reset, omitted, retired, and historical-only values before confirmation |
| Restore/apply layer | Mutate only after explicit confirmation and only with an already validated candidate snapshot |
| Reviewer | Verify semantic identity claims, privacy boundaries, failure handling, fixtures, and documentation |
| Learner or authorized user | Decide whether to apply the previewed replacement or migration |

No validator can prove that two pedagogical responsibilities are semantically equivalent. That remains an accountable authored and reviewed decision.

## 12. Privacy and security constraints

Future stable IDs and migration manifests must preserve the local-first boundary:

- module, revision, and step identifiers must not embed learner names, email addresses, roster IDs, confidential notes, credentials, secrets, or private URLs;
- migration manifests describe authored module structure, not learner identity;
- validation and preview must not transmit evidence;
- unknown fields and versions are rejected according to their schemas;
- file-size and resource limits must be defined before parsing untrusted manifests or evidence;
- external adapters remain separate from the generated module and must not receive data during local migration preview;
- logs and error messages must avoid reproducing unnecessary evidence payloads;
- local reset, exported-file deletion, and external deletion remain separate operations.

Structural validation cannot determine whether an author placed personal information inside an otherwise valid string. Content review and data minimization remain mandatory.

## 13. Failure behavior

A future migration operation must fail closed when:

- source or target module ID/revision does not match the manifest;
- required step IDs are missing, duplicated, retired unexpectedly, or reused;
- an operation has invalid cardinality;
- more than one operation claims the same active target without an explicit allowed rule;
- a required manifest in a revision chain is missing;
- the evidence version is unsupported;
- the migration would require an unspecified merge, split, aggregation, or inference policy;
- local progress changes after preview;
- a newer explicit file or manifest selection supersedes an older asynchronous read.

Failure leaves current browser progress, reading preferences, source files, and external systems unchanged.

## 14. Implementation sequence

The safe sequence after this decision is:

1. add explicit module revisions and immutable step IDs to the canonical module model and examples, without changing evidence v1;
2. validate uniqueness, immutability expectations, and references in fixtures and documentation;
3. design a new evidence version carrying module revision and step IDs;
4. define and publish a closed migration-manifest schema;
5. implement side-effect-free manifest and compatibility validation;
6. implement migration preview with comprehensive rename, reorder, insertion, split, merge, retirement, replacement, stale-preview, and race fixtures;
7. add explicit confirmation before any state-changing restore.

Each item is a separate reviewable increment. No step authorizes silent migration or background synchronization.

## 15. Decision summary

Raiatea treats a module ID as the durable identity of a pedagogical route, an explicit module revision as one published state of that route, and a future step ID as the immutable identity of one pedagogical responsibility. Titles and indexes remain presentation and ordering data, not durable identity.

Module changes always produce an explicit revision decision. Rename and reorder may preserve step identity; insertion creates new identity; split, merge, retirement, and replacement require authored mappings and cannot be inferred. Learner-evidence v1 remains frozen under its current conservative title/index rules. Future migrations must be versioned, authored, directional, side-effect free until confirmation, privacy-preserving, and fail closed whenever meaning is ambiguous.
