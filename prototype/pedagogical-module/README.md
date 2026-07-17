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

### Privacy-safe JSON export

The learner can explicitly download the current module evidence with **Esporta evidenze JSON**. The operation is local and user-initiated: the browser creates a file and does not send evidence to a server.

The v1 document is identified by:

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

Validate a saved or example export with:

```bash
python prototype/pedagogical-module/build/validate_evidence_export.py \
  prototype/pedagogical-module/evidence-examples/learner-evidence-export-v1.json
```

### Import compatibility policy

A structurally valid export is not automatically safe to restore into every module revision. Before a future import may modify local progress, the side-effect-free compatibility checker requires:

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

The checker reads and validates both files, reports every incompatibility, and exits non-zero on failure. It does not access browser storage, apply progress, merge evidence, or choose a conflict policy. Those state-changing decisions belong to a separate explicit restore increment.

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

The suite covers all example modules, adaptive remediation, micro-activities, learner evidence, export validation, import compatibility, step provenance, semantic visual references, generated output, and common invalid cases.

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
- versioned evidence download, predictable filename, exported values, and privacy exclusions;
- basic semantic hooks such as document language, accessible SVG role, and live regions.

CI installs Chromium with its Linux system dependencies before running the same command. Cross-browser and screenshot-regression coverage remain explicitly out of scope for this increment.

## Files

```text
prototype/pedagogical-module/
├── schema/module.schema.json
├── schema/learner-evidence-export-v1.schema.json
├── examples/self-attention.json
├── examples/self-attention-procedure.json
├── examples/query-key-value.json
├── examples/query-key-value.layout.json
├── evidence-examples/learner-evidence-export-v1.json
├── src/template.html
├── src/module.css
├── src/module.js
├── build/build_module.py
├── build/layout_visual.py
├── build/render_visual.py
├── build/validate_module.py
├── build/validate_module_v2.py
├── build/validate_evidence_export.py
├── build/check_evidence_compatibility.py
├── tests/test_layout_visual.py
├── tests/test_validation.py
├── tests/test_evidence_export.py
├── tests/test_evidence_compatibility.py
├── browser-tests/module.spec.js
├── playwright.config.js
├── package.json
├── package-lock.json
└── README.md
```

## Current constraints

- template replacement is intentionally dependency-free and simple;
- the Python module validator is layered;
- mathematical rendering uses plain text unless represented by visual primitives;
- learner evidence remains browser-local unless the learner explicitly exports one module;
- exported evidence can be checked for compatibility but cannot yet be applied or merged;
- recommendation rules are deterministic and intentionally simple;
- declarative layouts currently cover linear and branch/merge structures only;
- complex primitive visuals still require authored coordinates;
- browser coverage currently targets Chromium only;
- Docker execution labs are deferred.

## Next improvements

1. Add explicit import/restore with conflict handling and no silent overwrite.
2. Document retention and future LMS integration boundaries after the restore contract exists.
3. Link multiple modules into a prerequisite route.
4. Replace the temporary layered module validator with one consolidated implementation.
