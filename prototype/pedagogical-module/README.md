# Raiatea Pedagogical Module Prototype

This prototype turns a structured JSON document into one self-contained pedagogical HTML module.

## Goals

- separate educational content from presentation;
- avoid hand-editing each generated HTML file;
- preserve prerequisites, route, steps, quizzes, concepts, and provenance;
- work offline with no runtime dependencies;
- make Focus UI behavior reusable across modules;
- reject structurally incomplete or internally inconsistent modules before publication.

## Build

```bash
python prototype/pedagogical-module/build/build_module.py \
  prototype/pedagogical-module/examples/self-attention.json \
  --output /tmp/self-attention.html
```

Build the procedural example:

```bash
python prototype/pedagogical-module/build/build_module.py \
  prototype/pedagogical-module/examples/self-attention-procedure.json \
  --output /tmp/self-attention-procedure.html
```

The build validates both the source JSON and the generated HTML. It exits with status 1 and prints all detected problems when validation fails.

## Validate without building

```bash
python prototype/pedagogical-module/build/validate_module.py \
  prototype/pedagogical-module/examples/self-attention-procedure.json
```

Validation checks:

- required fields and basic data types;
- module, concept, and primitive identifier syntax;
- duplicate concept and primitive identifiers;
- quiz answer counts and `correctIndex` bounds;
- prerequisite references to existing concepts;
- `activeNodes` references to existing visual primitives;
- `animatedFlows` references to edge primitives only;
- matrix row consistency, label counts, and highlighted indices;
- token-row active-index bounds;
- weighted-sum terms and result values;
- authored links to concept cards;
- unresolved template placeholders;
- duplicate HTML IDs;
- broken internal HTML links;
- accidental external runtime resources;
- presence of embedded module data and the HTML doctype.

The validator is dependency-free. `module.schema.json` remains the declarative format contract; the Python validator applies cross-reference checks and semantic rules that JSON Schema alone does not express conveniently.

## Visual primitives

The current primitive vocabulary is:

- `box` — a labelled process or concept block;
- `vector` — a one-dimensional numeric representation;
- `token-row` — an ordered token sequence with an optional active token;
- `matrix` — a rectangular value grid with labels and highlighted rows or columns;
- `weighted-sum` — a pedagogical expression showing coefficients, terms, and result;
- `text` — an annotation;
- `edge` — an animated or static connection.

Example matrix:

```json
{
  "kind": "matrix",
  "id": "weights",
  "x": 350,
  "y": 300,
  "label": "Pesi α₂ⱼ",
  "values": [[0.1385, 0.2379, 0.2333]],
  "columnLabels": ["Your", "journey", "starts"],
  "highlightColumn": 1,
  "tone": "attention"
}
```

Example weighted sum:

```json
{
  "kind": "weighted-sum",
  "id": "context-sum",
  "x": 45,
  "y": 465,
  "terms": [
    {"weight": 0.1385, "label": "x¹"},
    {"weight": 0.2379, "label": "x²"}
  ],
  "result": [0.4419, 0.6515, 0.5683]
}
```

## Tests

```bash
python -m unittest discover \
  -s prototype/pedagogical-module/tests \
  -p 'test_*.py' \
  -v
```

The tests cover both examples and negative cases for malformed matrices, invalid token selections, empty weighted sums, broken quizzes, duplicate concepts and primitives, missing visual nodes, unknown prerequisite references, unresolved placeholders, external resources, and broken links.

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
├── tests/test_validation.py
└── README.md
```

## Current constraints

- template replacement is intentionally dependency-free and simple;
- the Python validator does not implement every JSON Schema keyword;
- mathematical rendering uses plain text unless represented through visual primitives;
- visual positioning is explicit rather than automatically laid out;
- learner progress is not persisted yet;
- Docker execution labs are deferred.

## Next improvements

1. Add adaptive remediation branches to quizzes.
2. Add reusable automatic layout helpers for matrices and process flows.
3. Add provenance cards at step level.
4. Add browser-level accessibility and interaction tests.
5. Generate a validation report suitable for authoring tools and CI annotations.
