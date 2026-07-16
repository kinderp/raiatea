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

The build validates both the source JSON and the generated HTML. It exits with status 1 and prints all detected problems when validation fails.

Open the generated HTML in a browser.

## Validate without building

```bash
python prototype/pedagogical-module/build/validate_module.py \
  prototype/pedagogical-module/examples/self-attention.json
```

Validation currently checks:

- required fields and basic data types;
- module and concept identifier syntax;
- duplicate concept identifiers;
- quiz answer counts and `correctIndex` bounds;
- prerequisite references to existing concepts;
- `activeNodes` and `animatedFlows` references to IDs present in the visual markup;
- authored links to concept cards;
- unresolved template placeholders;
- duplicate HTML IDs;
- broken internal HTML links;
- accidental external runtime resources;
- presence of embedded module data and the HTML doctype.

The validator is dependency-free. `module.schema.json` remains the declarative format contract; the Python validator applies the schema's important rules and the cross-reference checks that JSON Schema alone does not express conveniently.

## Tests

```bash
python -m unittest discover \
  -s prototype/pedagogical-module/tests \
  -p 'test_*.py' \
  -v
```

The tests include positive generation from the self-attention example and negative cases for broken quizzes, duplicate concepts, missing visual nodes, unknown prerequisite references, unresolved placeholders, external resources, and broken links.

## Files

```text
prototype/pedagogical-module/
├── schema/module.schema.json
├── examples/self-attention.json
├── src/template.html
├── src/module.css
├── src/module.js
├── build/build_module.py
├── build/validate_module.py
├── tests/test_validation.py
└── README.md
```

## Current constraints

- template replacement is intentionally dependency-free and simple;
- the Python validator does not yet implement every JSON Schema keyword;
- mathematical rendering uses plain text unless supplied as HTML/SVG;
- visual states rely on element IDs listed in `activeNodes` and `animatedFlows`;
- learner progress is not persisted yet;
- Docker execution labs are deferred.

## Next improvements

1. Add reusable visual primitives instead of embedding raw SVG in JSON.
2. Add adaptive remediation branches.
3. Add provenance cards at step level.
4. Add browser-level accessibility and interaction tests.
5. Generate a validation report suitable for authoring tools and CI annotations.
