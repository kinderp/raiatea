# Raiatea Pedagogical Module Prototype

This prototype turns a structured JSON document into one self-contained pedagogical HTML module.

## Goals

- separate educational content from presentation;
- avoid hand-editing each generated HTML file;
- preserve prerequisites, route, steps, quizzes, concepts, and provenance;
- work offline with no runtime dependencies;
- make Focus UI behavior reusable across modules;
- reject structurally incomplete or internally inconsistent modules before publication;
- turn incorrect answers into targeted recovery paths rather than dead-end feedback;
- preserve observable learner evidence locally without pretending it is a mastery score.

## Build

```bash
python prototype/pedagogical-module/build/build_module.py \
  prototype/pedagogical-module/examples/self-attention.json \
  --output /tmp/self-attention.html
```

Build the query/key/value module with the same template:

```bash
python prototype/pedagogical-module/build/build_module.py \
  prototype/pedagogical-module/examples/query-key-value.json \
  --output /tmp/query-key-value.html
```

The build resolves declarative visual layouts before canonical validation, then validates both the resolved module and the generated HTML. It exits with status 1 and prints all detected problems when validation fails.

## Declarative visual layouts

A module can keep visual structure separate from pedagogical content by referencing a module-local layout file:

```json
{
  "visual": {
    "type": "layout",
    "source": "query-key-value.layout.json"
  }
}
```

The canonical loader resolves the path relative to the module JSON, rejects references that escape that directory, compiles the layout into the existing semantic primitive vocabulary, and only then runs normal validation and rendering.

The current layout compiler supports `pipeline`, `parallel`, and `branch-merge`. It intentionally does not attempt arbitrary graph layout or browser editing. Modules may still provide `svg`, `html`, or explicit `primitives` visuals directly.

## Adaptive remediation

A quiz can optionally define a deterministic recovery micro-activity:

```json
{
  "remediation": {
    "title": "Torna alla rappresentazione numerica",
    "explanation": "Il token è simbolico; l'embedding è il vettore numerico usato dalla rete.",
    "conceptRef": "embedding",
    "retryLabel": "Torna alla domanda originale",
    "activity": {
      "type": "choice",
      "prompt": "Quale oggetto può entrare nei calcoli della rete?",
      "answers": ["journey", "[0.55, 0.87, 0.66]"],
      "correctIndex": 1,
      "correctFeedback": "Esatto: è un vettore numerico.",
      "incorrectFeedback": "Cerca la rappresentazione numerica."
    }
  }
}
```

The learner flow is:

```text
incorrect answer
→ targeted explanation
→ optional concept card
→ recovery micro-activity
→ original question retry
```

## Learner evidence

Each module stores a separate progress record in `localStorage` using `raiatea-progress:<module-id>`.

The record contains only observable evidence:

- current step;
- attempts per diagnostic question;
- whether the answer was eventually correct;
- whether remediation was used;
- whether the recovery activity was completed.

The summary panel distinguishes correct without remediation, correct after remediation, attempted but not consolidated, and not yet verified. This is deliberately not called a mastery score.

### Privacy-safe JSON export: v1 browser contract

The learner can explicitly download the current module evidence with **Esporta evidenze JSON**. The operation is local and user-initiated: the browser creates a file and does not send evidence to a server.

The browser currently exports learner-evidence v1:

```json
{
  "format": "raiatea-learner-evidence",
  "version": 1
}
```

The complete contract lives in `schema/learner-evidence-export-v1.schema.json`; a representative document is stored in `evidence-examples/learner-evidence-export-v1.json`. Evidence interchange samples are deliberately separate from `examples/`, which contains only buildable pedagogical modules. The export contains only:

- module ID, title, language, step count, and allowlisted source context;
- current step;
- step index and module-authored title;
- attempts and the three observable boolean outcomes already stored locally.

The export intentionally excludes:

- learner names, email addresses, accounts, and device identifiers;
- theme, text size, density, width, alignment, and motion preferences;
- unrelated `localStorage` entries;
- free-form learner content;
- inferred mastery, diagnosis, disability, or personal profiles;
- timestamps, analytics identifiers, cloud destinations, and background telemetry.

The predictable filename is `<module-id>-evidence-v1.json`. Export does not delete or modify the browser-local progress record. Signing, encryption, multi-module bundles, and cloud transfer remain outside this prototype.

Validate a saved or example v1 export with:

```bash
python prototype/pedagogical-module/build/validate_evidence_export.py \
  prototype/pedagogical-module/evidence-examples/learner-evidence-export-v1.json
```

### Learner-evidence v2 structural contract

Learner-evidence v2 is a separately versioned document contract. It carries exact canonical module revision identity, stable pedagogical step IDs, the source revision's explicit step order, and the current position as both `currentStepId` and `currentStepIndex`.

```json
{
  "format": "raiatea-learner-evidence",
  "version": 2
}
```

The closed schema lives in `schema/learner-evidence-export-v2.schema.json`; the representative document is `evidence-examples/learner-evidence-export-v2.json`. The side-effect-free validator checks internal consistency, including:

- a positive opaque module revision identity;
- canonical and unique exported `stepId` values;
- contiguous indexes matching array positions;
- module step-count consistency;
- a current step ID present in the exported step set;
- agreement between current step ID and current step index;
- exact allowlists at every object boundary.

Validate the representative v2 document with:

```bash
python prototype/pedagogical-module/build/validate_evidence_export_v2.py \
  prototype/pedagogical-module/evidence-examples/learner-evidence-export-v2.json
```

Structural validity does not prove compatibility with an installed or published module revision. V1 and v2 coexist explicitly: the v1 validator rejects v2 fields and version `2`, the v2 validator rejects v1 documents, v2 is never silently substituted for a requested v1 export, and no automatic downgrade is defined.

### Exact contextual compatibility for v2

The exact contextual checker receives one structurally valid v2 document and one structurally valid canonical module revision. It requires exact module ID and opaque revision equality, the same step count, the same ordered stable step-ID sequence, and a current step ID/index that names the same active canonical step.

```bash
python prototype/pedagogical-module/build/check_evidence_compatibility_v2.py \
  prototype/pedagogical-module/tests/fixtures/module-identity/valid.json \
  prototype/pedagogical-module/tests/fixtures/evidence-v2-contextual/exact.json
```

Module titles, language, source metadata, and step titles remain explanatory snapshots rather than compatibility keys. Revision mismatches are reported without inferring older/newer or higher/lower ordering. The checker validates first, reports every deterministic contextual mismatch, exits non-zero on failure, and never mutates either input or browser storage.

This is Class A exact matching only. A mismatch is not automatically classified as lossless, partial, incompatible, or unsupported; those outcomes require later publication-history and manifest-aware tooling. The current browser still does not export, import, preview, restore, or migrate v2 documents.

### Closed authored migration-manifest contract

A migration manifest is a separately versioned, directional declaration between two distinct exact revisions of the same module route. It contains complete source and target stable-step inventories and supports only the initial closed operation vocabulary:

- `preserve` retains the exact same stable step ID in both revisions;
- `retire` covers one source step that has no active target destination;
- `introduce` covers one target step that has no source evidence origin.

A renamed or reordered responsibility is represented by preserving its stable ID. A replacement with a new identity is represented as `retire` plus `introduce`; the validator rejects aliases, fan-out, fan-in, split, merge, unknown operations, duplicate coverage, incomplete coverage, malformed IDs, cross-module endpoints, and equal source/target revisions.

The closed schema is `schema/learner-evidence-migration-manifest-v1.schema.json`; the representative document is `evidence-examples/learner-evidence-migration-manifest-v1.json`; and the normative implementation boundary is documented in `docs/learner-evidence-migration-manifest.md`.

Validate the representative manifest with:

```bash
python prototype/pedagogical-module/build/validate_evidence_migration_manifest.py \
  prototype/pedagogical-module/evidence-examples/learner-evidence-migration-manifest-v1.json
```

The standalone validator is deterministic and side-effect free. It validates only manifest-internal structure and invariants. It does not look up publication history, prove that external module files match the declared inventories, choose a migration path, classify an evidence document, generate a preview, mutate browser progress, or apply a migration.

### V1 import compatibility policy

A structurally valid v1 export is not automatically safe to restore into every module revision. The side-effect-free compatibility checker requires:

- exact supported format and version through the structural validator;
- exact module ID;
- the same current module step count;
- the same exported step-sequence length;
- the same ordered, module-authored step titles.

Step indexes are already required to match their array positions by the v1 structural validator. Source title, chapter, pages, figure, and other allowlisted source metadata remain explanatory context and do not determine compatibility.

Check the merged sample against the current module with:

```bash
python prototype/pedagogical-module/build/check_evidence_compatibility.py \
  prototype/pedagogical-module/examples/self-attention.json \
  prototype/pedagogical-module/evidence-examples/learner-evidence-export-v1.json
```

The checker reads and validates both files, reports every incompatibility, and exits non-zero on failure. It does not access browser storage or apply progress.

### Explicit v1 restore with conflict preview

The learner can select a JSON file with **Importa evidenze JSON**. Selection alone never changes progress. The browser performs the same conservative v1 structural and module-compatibility checks, then shows a preview comparing:

- completed checks in the current browser state;
- attempts in the current browser state;
- completed checks in the selected file;
- attempts in the selected file.

Only **Ripristina questo avanzamento** applies the file. Restore is an explicit replacement, not a merge. It writes only the allowlisted progress fields to `raiatea-progress:<module-id>`:

- `currentStep`;
- `attempts`;
- `correct`;
- `usedRemediation`;
- `activityCompleted`.

Module titles, step titles, indexes, source metadata, unknown properties, and any other file content are validation context only and are never copied into browser progress. Reading preferences and unrelated `localStorage` entries remain untouched.

Malformed, oversized, unsupported, cross-module, or revision-incompatible files keep the current progress unchanged and never enable confirmation. **Annulla importazione** also leaves progress unchanged. Active playback stops when import starts, obsolete asynchronous file reads cannot replace a newer selection, and a pending preview is invalidated if local progress changes before confirmation. The entire flow remains offline and imposes a 1 MB file-size limit before parsing.

The current conflict policy is intentionally narrow:

- compatible v1 evidence replaces the current module record only after confirmation;
- histories are not merged;
- versions are not migrated or coerced;
- there is no background upload, analytics, telemetry, cloud synchronization, or LMS transfer.

### Retention, deletion, and external integration boundaries

The architecture and privacy decision is documented in [`docs/learner-evidence-boundaries.md`](docs/learner-evidence-boundaries.md). It defines:

- the separate lifecycles of browser progress, reading preferences, pending imports, and downloaded files;
- exactly what **Azzera avanzamento**, reading-settings reset, browser site-data deletion, and operating-system file deletion affect;
- why resetting browser progress cannot delete exported or external copies;
- data-minimization, purpose-limitation, and learner-control rules;
- the trust boundary between the self-contained module, an optional adapter, and an external LMS or archive;
- provider-neutral future integration operations and mandatory LMS safeguards;
- versioning rules, forbidden defaults, and a review checklist for future evidence work.

The current generated module contains no provider credentials, network queue, external destination, or remote deletion mechanism. A future adapter must define its own purpose, identity, retention, deletion, security, and failure semantics without changing the meaning of local reset controls.

### Module evolution and future evidence compatibility

The architecture decision for durable module identity, explicit revisions, immutable step IDs, and authored migration responsibilities is documented in [`docs/module-evolution-and-evidence-compatibility.md`](docs/module-evolution-and-evidence-compatibility.md). The executable authoring rules are in [`docs/module-revision-authoring.md`](docs/module-revision-authoring.md), the v2 stable-identity contract is in [`docs/learner-evidence-v2-stable-identity.md`](docs/learner-evidence-v2-stable-identity.md), the exact contextual contract is in [`docs/learner-evidence-v2-exact-compatibility.md`](docs/learner-evidence-v2-exact-compatibility.md), the migration-manifest contract is in [`docs/learner-evidence-migration-manifest.md`](docs/learner-evidence-migration-manifest.md), and the documentation index is available in [`docs/README.md`](docs/README.md).

The current implementation boundary is:

- every canonical module carries a positive integer `revision`;
- every pedagogical step carries a unique stable ID using lowercase letters, digits, and hyphens;
- learner-evidence v1 keeps its exact title/index browser export, compatibility, preview, and restore behavior;
- learner-evidence v2 has a separate closed schema, example, and structural validator carrying revision identity and stable step IDs;
- exact v2 contextual matching is available against one supplied canonical revision using exact ID, revision, stable-step sequence, and current-position checks;
- a closed authored migration-manifest schema, example, and side-effect-free validator describe complete same-module revision transitions using exact-ID `preserve`, `retire`, and `introduce` operations;
- browser v2 export/import, publication-history lookup, contextual manifest validation, compatibility classes B–E, migration preview, and migration application are not implemented;
- rename, reorder, split, merge, retirement, and replacement are not migrated automatically;
- future migration classification, preview, and application must remain deterministic, explicit, reviewable, and confirmed before any state change.

Publication registries, contextual manifest checks, compatibility classification, migration previews, and state-changing migration remain separate reviewable increments.

## Step-level provenance

A step can declare whether it is original, translated, adapted, derived, or inferred. It can also record source pages, the source figure, transformations, derived values, and an author note. The generated module exposes this in a collapsible provenance card for each step.

## Generality test: query, key, value

`examples/query-key-value.json` is the first module that is not merely another view of the orientation figure. It tests whether the same engine can represent:

- one input branching into three learned projections;
- separate query, key, and value roles;
- convergence of query and key into a compatibility score;
- a distinct value path carrying content;
- adaptive remediation and provenance without template changes.

`examples/query-key-value.json` references `examples/query-key-value.layout.json`. The canonical loader compiles that declarative branch-and-merge description into the existing semantic primitive vocabulary. No special-purpose QKV renderer or template branch was introduced.

## Validate without building

```bash
python prototype/pedagogical-module/build/validate_module_v2.py \
  prototype/pedagogical-module/examples/query-key-value.json
```

## Visual primitives

The semantic visual vocabulary currently includes `box`, `vector`, `text`, `edge`, `token-row`, `matrix`, and `weighted-sum`.

The builder converts both explicit primitives and compiled declarative layouts into accessible inline SVG while preserving node and flow identifiers used by the pedagogical steps.

## Tests

```bash
python -m unittest discover \
  -s prototype/pedagogical-module/tests \
  -p 'test_*.py' \
  -v
```

The suite covers all example modules, canonical revision and step-ID fixtures, adaptive remediation, micro-activities, v1 and v2 evidence validation, v1 browser export/import compatibility, exact v2 contextual compatibility, migration-manifest structure and invariants, step provenance, semantic visual references, generated output, and common invalid cases.

## Browser interaction tests

The browser suite uses an exact, test-only Playwright version and Chromium. The generated HTML remains self-contained and has no Playwright or Node.js runtime dependency.

From the prototype directory:

```bash
cd prototype/pedagogical-module
npm ci
npx playwright install chromium
npm run test:browser
```

`npm ci` installs exactly the dependency graph recorded in `package-lock.json`; update the lockfile intentionally whenever the test dependency changes.

The Playwright configuration builds `examples/self-attention.json` through the canonical Python builder, serves the generated artifact from a temporary local directory, and verifies:

- step buttons, direct navigation, reset, and document-level arrow shortcuts;
- active visual nodes and disabled boundary controls;
- theme, text size, spacing, column width, alignment, motion, and persistence;
- preservation of arrow-key behavior while a reading control has focus;
- reduced-motion concept navigation, centered target focus, and non-flashing highlight state;
- targeted remediation, retry behavior, local evidence, and reload persistence;
- versioned v1 evidence download, predictable filename, exported values, and privacy exclusions;
- compatible v1 evidence preview without immediate mutation;
- explicit v1 replacement and reload persistence;
- preservation of reading preferences and unrelated storage;
- cancel, malformed JSON, and incompatible-module no-op behavior;
- playback shutdown, latest-selection ordering, visible file chooser, and stale-preview invalidation;
- basic semantic hooks such as document language, accessible SVG role, and live regions.

CI installs Chromium with its Linux system dependencies before running the same command. Cross-browser and screenshot-regression coverage remain explicitly out of scope for this increment.

## Files

```text
prototype/pedagogical-module/
├── schema/module.schema.json
├── schema/learner-evidence-export-v1.schema.json
├── schema/learner-evidence-export-v2.schema.json
├── schema/learner-evidence-migration-manifest-v1.schema.json
├── examples/self-attention.json
├── examples/self-attention-procedure.json
├── examples/query-key-value.json
├── examples/query-key-value.layout.json
├── evidence-examples/learner-evidence-export-v1.json
├── evidence-examples/learner-evidence-export-v2.json
├── evidence-examples/learner-evidence-migration-manifest-v1.json
├── docs/README.md
├── docs/learner-evidence-boundaries.md
├── docs/module-evolution-and-evidence-compatibility.md
├── docs/module-revision-authoring.md
├── docs/learner-evidence-v2-stable-identity.md
├── docs/learner-evidence-v2-exact-compatibility.md
├── docs/learner-evidence-migration-manifest.md
├── src/template.html
├── src/module.css
├── src/module.js
├── build/build_module.py
├── build/layout_visual.py
├── build/render_visual.py
├── build/validate_module.py
├── build/validate_module_v2.py
├── build/validate_module_identity.py
├── build/validate_evidence_export.py
├── build/validate_evidence_export_v2.py
├── build/validate_evidence_migration_manifest.py
├── build/check_evidence_compatibility.py
├── build/check_evidence_compatibility_v2.py
├── tests/fixtures/module-identity/
├── tests/fixtures/evidence-v2/
├── tests/fixtures/evidence-v2-contextual/
├── tests/fixtures/evidence-migration-manifest/
├── tests/test_layout_visual.py
├── tests/test_validation.py
├── tests/test_module_identity.py
├── tests/test_evidence_export.py
├── tests/test_evidence_export_v2.py
├── tests/test_evidence_compatibility.py
├── tests/test_evidence_compatibility_v2.py
├── tests/test_evidence_migration_manifest.py
├── tests/test_evidence_migration_manifest_inventory_duplicates.py
├── browser-tests/module.spec.js
├── browser-tests/evidence-import-race.spec.js
├── browser-tests/evidence-import-conflict.spec.js
├── playwright.config.js
├── package.json
├── package-lock.json
└── README.md
```

## Current constraints

- template replacement is intentionally dependency-free and simple;
- the Python module validator is layered;
- mathematical rendering uses plain text unless represented by visual primitives;
- the browser currently exports and restores only one-module v1 JSON documents;
- v2 structural validation and exact contextual matching are local CLI/API capabilities only;
- exact matching knows only the supplied target module, not publication history or migration paths;
- migration-manifest validation is structural and internal only; it does not validate external revisions, classify evidence, preview, or apply a transition;
- no v2 browser export/import, compatibility classes B–E, or migration application exists;
- restore supports explicit replacement of one compatible v1 module record, not history merging;
- no version migration, multi-module bundle, signing, encryption, cloud sync, or LMS transfer exists;
- recommendation rules are deterministic and intentionally simple;
- declarative layouts currently cover linear and branch/merge structures only;
- complex primitive visuals still require authored coordinates;
- browser coverage currently targets Chromium only;
- Docker execution labs are deferred.

## Next improvements

1. Validate manifests contextually against immutable source and target module revisions.
2. Add compatibility classification and human-readable migration preview without state changes.
3. Add explicitly confirmed migration while preserving the original evidence copy.
4. Add explicit browser v2 export/import only after contextual compatibility and migration policy are complete.
5. Define a provider-neutral adapter interface only when a concrete integration use case exists.
6. Link multiple modules into a prerequisite route.
7. Replace the temporary layered module validator with one consolidated implementation.
