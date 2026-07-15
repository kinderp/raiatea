# Raiatea Pedagogical Module Prototype

This prototype turns a structured JSON document into one self-contained pedagogical HTML module.

## Goals

- separate educational content from presentation;
- avoid hand-editing each generated HTML file;
- preserve prerequisites, route, steps, quizzes, concepts, and provenance;
- work offline with no runtime dependencies;
- make Focus UI behavior reusable across modules.

## Build

```bash
python prototype/pedagogical-module/build/build_module.py \
  prototype/pedagogical-module/examples/self-attention.json \
  --output /tmp/self-attention.html
```

Open the generated HTML in a browser.

## Files

```text
prototype/pedagogical-module/
├── schema/module.schema.json
├── examples/self-attention.json
├── src/template.html
├── src/module.css
├── src/module.js
├── build/build_module.py
└── README.md
```

## Current constraints

- template replacement is intentionally dependency-free and simple;
- schema validation is not yet executed by the build script;
- mathematical rendering uses plain text unless supplied as HTML/SVG;
- visual states rely on element IDs listed in `activeNodes` and `animatedFlows`;
- learner progress is not persisted yet;
- Docker execution labs are deferred.

## Next improvements

1. Validate module JSON against the schema.
2. Add reusable visual primitives instead of embedding raw SVG in JSON.
3. Add adaptive remediation branches.
4. Add provenance cards at step level.
5. Add tests for output completeness and broken internal references.
