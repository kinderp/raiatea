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

The build validates both the source JSON and the generated HTML. It exits with status 1 and prints all detected problems when validation fails.

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

## Step-level provenance

A step can declare whether it is original, translated, adapted, derived, or inferred. It can also record source pages, the source figure, transformations, derived values, and an author note. The generated module exposes this in a collapsible provenance card for each step.

## Generality test: query, key, value

`examples/query-key-value.json` is the first module that is not merely another view of the orientation figure. It tests whether the same engine can represent:

- one input branching into three learned projections;
- separate query, key, and value roles;
- convergence of query and key into a compatibility score;
- a distinct value path carrying content;
- adaptive remediation and provenance without template changes.

The module uses only the existing semantic primitive vocabulary. No special-purpose QKV renderer or template branch was introduced.

## Validate without building

```bash
python prototype/pedagogical-module/build/validate_module_v2.py \
  prototype/pedagogical-module/examples/query-key-value.json
```

## Visual primitives

The semantic visual vocabulary currently includes `box`, `vector`, `text`, `edge`, `token-row`, `matrix`, and `weighted-sum`.

The builder converts these objects into accessible inline SVG while preserving node and flow identifiers used by the pedagogical steps.

## Tests

```bash
python -m unittest discover \
  -s prototype/pedagogical-module/tests \
  -p 'test_*.py' \
  -v
```

The suite covers all example modules, adaptive remediation, micro-activities, learner evidence, step provenance, semantic visual references, generated output, and common invalid cases.

## Files

```text
prototype/pedagogical-module/
├── schema/module.schema.json
├── examples/self-attention.json
├── examples/self-attention-procedure.json
├── examples/query-key-value.json
├── src/template.html
├── src/module.css
├── src/module.js
├── build/build_module.py
├── build/render_visual.py
├── build/validate_module.py
├── build/validate_module_v2.py
├── tests/test_validation.py
└── README.md
```

## Current constraints

- template replacement is intentionally dependency-free and simple;
- the Python validator is layered;
- mathematical rendering uses plain text unless represented by visual primitives;
- learner evidence is browser-local and is not synchronized across devices;
- recommendation rules are deterministic and intentionally simple;
- most visual coordinates are still authored manually;
- Docker execution labs are deferred.

## Next improvements

1. Add declarative layout primitives that reduce manual coordinates.
2. Add browser-level accessibility and interaction tests.
3. Export learner evidence without exposing personal data by default.
4. Link multiple modules into a prerequisite route.
5. Replace the temporary layered validator with one consolidated implementation.
