# Raiatea Pedagogical Module Prototype

This prototype turns a structured JSON document into one self-contained pedagogical HTML module.

## Goals

- separate educational content from presentation;
- avoid hand-editing each generated HTML file;
- preserve prerequisites, route, steps, quizzes, concepts, and provenance;
- work offline with no runtime dependencies;
- make Focus UI behavior reusable across modules;
- reject structurally incomplete or internally inconsistent modules before publication;
- turn incorrect answers into targeted recovery paths rather than dead-end feedback.

## Build

```bash
python prototype/pedagogical-module/build/build_module.py \
  prototype/pedagogical-module/examples/self-attention.json \
  --output /tmp/self-attention.html
```

The build validates both the source JSON and the generated HTML. It exits with status 1 and prints all detected problems when validation fails.

## Adaptive remediation

A quiz can optionally define a recovery path:

```json
{
  "question": "Che cosa riceve la self-attention?",
  "answers": ["Stringhe grezze", "Vettori numerici"],
  "correctIndex": 1,
  "correctFeedback": "Corretto.",
  "incorrectFeedback": "La rete non elabora direttamente le parole visualizzate.",
  "remediation": {
    "title": "Torna alla rappresentazione numerica",
    "explanation": "Il token è simbolico; l'embedding è il vettore numerico usato dalla rete.",
    "conceptRef": "embedding",
    "actionLabel": "Rivedi embedding",
    "retryLabel": "Riprova la domanda"
  }
}
```

After an incorrect answer the learner receives:

- the immediate error feedback;
- a short targeted explanation;
- an optional link to the relevant concept card;
- a retry action;
- a visible attempt count for the current question.

The validator rejects missing remediation fields, unknown concept references, unsupported remediation properties, and empty labels.

## Validate without building

```bash
python prototype/pedagogical-module/build/validate_module_v2.py \
  prototype/pedagogical-module/examples/self-attention.json
```

## Visual primitives

The semantic visual vocabulary currently includes:

- `box`;
- `vector`;
- `text`;
- `edge`;
- `token-row`;
- `matrix`;
- `weighted-sum`.

The builder converts these objects into accessible inline SVG while preserving node and flow identifiers used by the pedagogical steps.

## Tests

```bash
python -m unittest discover \
  -s prototype/pedagogical-module/tests \
  -p 'test_*.py' \
  -v
```

The suite includes positive generation and negative cases for broken quizzes, invalid remediation paths, duplicate concepts and primitives, missing visual nodes, unknown prerequisite references, unresolved placeholders, external resources, and broken links.

## Files

```text
prototype/pedagogical-module/
├── schema/module.schema.json
├── examples/self-attention.json
├── examples/self-attention-procedure.json
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
- the Python validator is layered: the base validator checks modules and visuals, while `validate_module_v2.py` adds adaptive remediation rules;
- mathematical rendering uses plain text unless represented by visual primitives;
- learner attempts exist only for the current browser session and are not yet persisted as mastery evidence;
- remediation currently points to local concept cards, not separate generated micro-lessons;
- Docker execution labs are deferred.

## Next improvements

1. Record learner evidence and mastery state separately from interface preferences.
2. Allow remediation to open a short embedded recovery activity, not only a concept card.
3. Re-test the original question after the recovery activity and record whether understanding improved.
4. Add step-level provenance cards.
5. Add browser-level accessibility and interaction tests.
