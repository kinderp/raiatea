# Stable step identity and module revision contract

Status: architecture decision for future module evolution and learner-evidence versions.

This decision defines identity and migration semantics before they are added to module schemas or evidence documents. The current module model and learner-evidence v1 remain unchanged.

## 1. Problem

Learner-evidence v1 uses a deliberately conservative compatibility key:

- exact module ID;
- step count;
- canonical step indexes;
- ordered authored step titles.

That prevents accidental reinterpretation of historical evidence, but it also makes a title correction or harmless wording change incompatible. Indexes and titles are presentation attributes, not durable conceptual identities.

A future version needs stable identities without silently weakening v1.

## 2. Identity layers

| Layer | Meaning | Stability |
| --- | --- | --- |
| Module ID | Durable pedagogical route or unit | Stable across compatible revisions |
| Module revision | Explicit authored state of that route | Changes whenever compatibility-relevant content changes |
| Step ID | Durable conceptual step within the route | Stable across rename, translation, and reorder when meaning is preserved |
| Step title | Learner-facing wording | May change without changing conceptual identity |
| Step index | Presentation order in one revision | May change and is never a durable identity |

### 2.1 Module ID

A module ID identifies the continuing pedagogical route, not one generated file or one text revision. Reusing an ID for an unrelated module is forbidden.

### 2.2 Module revision

A future module revision should be an explicit positive integer or immutable revision token authored in source. It must not be inferred from file modification time, Git commit date, browser cache state, or a title hash.

Revision changes are required when a change can affect interpretation, navigation, diagnostic evidence, compatibility, or migration. Pure build-output changes that do not alter the canonical module source do not create a pedagogical revision.

### 2.3 Step ID

A future step ID should:

- be unique within its module route;
- use a predictable restricted syntax such as lowercase letters, digits, and hyphens;
- be independent of title, index, language, CSS, and visual coordinates;
- remain immutable while the conceptual role remains the same;
- never be recycled after retirement;
- be assigned by an author or reviewed generation process, not guessed during import.

Example:

```json
{
  "id": "compare-query-key",
  "title": "Confrontare query e key"
}
```

## 3. Change rules

| Change | Preserve step ID? | New module revision? | Migration decision |
| --- | --- | --- | --- |
| Typographical correction | Yes | Yes, unless project policy classifies it as non-semantic metadata | Identity mapping is one-to-one |
| Title rewrite with same pedagogical role | Yes | Yes | One-to-one |
| Translation with same conceptual role | Yes when the route is multilingual; otherwise use a separately identified route | Yes | One-to-one, language policy explicit |
| Reorder existing steps | Yes | Yes | One-to-one with order change |
| Insert a new independent step | Existing IDs preserved; new step gets a new ID | Yes | Existing evidence maps; new step starts empty |
| Expand explanation or examples without changing diagnostic meaning | Yes | Yes | Usually one-to-one, explicitly reviewed |
| Change quiz meaning or success criterion | Usually preserve ID only if the conceptual claim remains equivalent | Yes | Reviewer must decide whether prior `correct` evidence remains valid |
| Split one step into multiple steps | Original ID is retired or retained for exactly one continuing concept; every other result gets a new ID | Yes | Explicit one-to-many policy; never inferred |
| Merge multiple steps | New merged step normally gets a new ID | Yes | Explicit many-to-one policy; aggregation semantics required |
| Replace a step with a different concept | No; retire old ID and create a new ID | Yes | Old evidence is not automatically transferred |
| Remove or retire a step | ID remains reserved and cannot be reused | Yes | Evidence may be retained in migration history but not attached to another step |

A reviewer must reject any migration that uses title similarity alone as proof of identity.

## 4. Compatibility classes

Future tooling should report one of these classes rather than a single ambiguous boolean:

1. **Exact** — same module ID, revision, step IDs, and supported evidence version.
2. **Directly compatible** — different revision, but every evidence-bearing step maps one-to-one without changing evidence meaning.
3. **Migratable with explicit policy** — split, merge, retirement, changed success criterion, or new required step needs an authored migration manifest and preview.
4. **Incompatible** — unrelated module, unsupported evidence version, missing migration path, ambiguous mapping, recycled ID, or semantic replacement.

Compatibility checking remains side-effect free. Restore or migration requires a separate explicit confirmation.

## 5. Proposed migration manifest

The following is an illustrative future shape, not a committed schema:

```json
{
  "format": "raiatea-module-migration",
  "version": 1,
  "moduleId": "self-attention-orientation",
  "fromRevision": 2,
  "toRevision": 3,
  "steps": [
    {"kind": "preserve", "from": "embedding-input", "to": "embedding-input"},
    {"kind": "rename", "from": "qk-score", "to": "qk-score"},
    {"kind": "retire", "from": "legacy-overview"},
    {"kind": "introduce", "to": "softmax-normalization", "initialEvidence": "empty"}
  ]
}
```

A real schema must be closed, versioned, directional, and validate:

- exact module ID and source/target revisions;
- uniqueness and existence of every referenced step ID;
- no accidental reuse or duplicate destinations;
- explicit semantics for split, merge, attempts, correctness, remediation, and current-step movement;
- deterministic output;
- a human-readable preview;
- preservation of the original evidence document until confirmation.

## 6. Split and merge safeguards

### 6.1 Split

Prior `correct: true` for one broad step must not automatically mark every new child step correct. An authored policy may choose among:

- retain evidence on one designated continuing step and initialize others empty;
- archive old evidence as historical context without assigning correctness;
- require new diagnostics for all split steps.

### 6.2 Merge

Combining attempts or correctness from multiple old steps requires an explicit rule. Examples such as “any correct”, “all correct”, maximum attempts, or summed attempts have different pedagogical meanings. There is no safe universal default.

### 6.3 Changed diagnostic meaning

A stable step ID does not guarantee that old evidence remains valid. If the success criterion changes materially, the migration must reset or archive the affected evidence even when the conceptual label is similar.

## 7. Current-step migration

The learner's current position is navigation state, not mastery evidence. A migration must define what happens when the current step:

- still exists under the same ID;
- moved to a different index;
- was split;
- was merged;
- was retired;
- became optional or inaccessible because prerequisites changed.

The safe default for an ambiguous position is a reviewed fallback step or the first incomplete compatible step, shown in the preview before confirmation.

## 8. Evidence versioning

Learner-evidence v1 is frozen. It continues to use module ID, count, indexes, and ordered titles exactly as documented. Stable step IDs must not be added silently to v1 or interpreted from titles.

A future evidence version may include:

- module revision;
- stable step ID for each evidence item;
- optional original display title for human interpretation;
- migration provenance showing source revision, target revision, manifest identifier, and user confirmation.

Introducing that version requires a separate schema, validator, examples, browser behavior, compatibility policy, and migration plan. Unknown versions remain rejected.

## 9. Privacy and security boundaries

Stable IDs and migration metadata must not introduce:

- learner identity, account IDs, device IDs, or institutional identifiers into the core evidence document;
- inferred mastery or personal profiles;
- background network synchronization;
- provider credentials or external destination identifiers in generated modules;
- silent migration on page load;
- executable migration code supplied by an untrusted evidence file.

Migration manifests are declarative data validated by trusted local tooling. An imported file must not define JavaScript, templates, URLs to execute, or arbitrary expressions.

## 10. Failure modes to test

Every later implementation must include fixtures for:

- title rename with stable ID;
- reorder with stable IDs;
- insertion of a new step;
- retired step;
- one-to-many split;
- many-to-one merge;
- changed quiz meaning requiring reset;
- duplicate or recycled step IDs;
- unknown source or target revision;
- manifest for another module;
- incomplete or ambiguous mapping;
- obsolete asynchronous migration preview;
- local progress changing after preview;
- cancellation and unchanged original evidence;
- unsupported evidence or migration version.

## 11. Authoring and review responsibilities

Module authors own identity decisions. Tooling may detect suspicious changes and propose mappings, but it must not finalize conceptual identity automatically.

A PR that changes revision or step identity should show:

- old and new module revisions;
- added, preserved, retired, split, merged, and replaced IDs;
- whether old diagnostic evidence remains meaningful;
- migration or explicit incompatibility decision;
- fixtures and expected previews;
- confirmation that v1 behavior is unchanged unless a separate versioned feature is in scope.

## 12. Implementation sequence

1. Add module revision and stable step IDs to the canonical module schema and examples, while preserving v1 export behavior.
2. Validate uniqueness, syntax, non-reuse policy documentation, and step references.
3. Design a new evidence version carrying revision and stable step IDs.
4. Define a closed migration-manifest schema and side-effect-free validator.
5. Add compatibility classes and human-readable migration preview.
6. Add explicit confirmed migration while preserving the original evidence copy.

Each item is a separate issue and PR.

## 13. Decision summary

Module IDs identify durable routes, revisions identify explicit authored states, and step IDs identify durable conceptual steps. Titles and indexes remain presentation attributes. Identity never implies evidence validity after a semantic change; split, merge, retirement, and changed diagnostics require explicit migration policy. Learner-evidence v1 remains frozen, and future stable-ID evidence or migration behavior must be introduced through new versioned contracts with preview and confirmation.
