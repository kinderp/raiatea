# First runnable Raiatea pilot contract

Status: normative implementation contract for issue #60 under parent #58.

## Goal

Package the existing pedagogical-module engine as one locally runnable two-module learner journey with a single entry page, deterministic build output, and simple evaluator instructions.

## Canonical pilot route

The initial route derives identity, revision, and title from two existing canonical modules:

1. `self-attention-orientation`, revision `1` — **Il ruolo della self-attention nel modello GPT**;
2. `query-key-value`, revision `1` — **Query, Key e Value nella self-attention**.

This order follows the authored module context: the learner first locates self-attention in the model and then distinguishes the internal query, key, and value responsibilities. The builder must not duplicate canonical IDs, revisions, or titles in a second route registry.

The launcher and module navigation use relative links only and do not depend on repository checkout paths.

## Output layout

A deterministic build creates one disposable output directory:

```text
pilot-dist/
├── index.html
├── self-attention.html
├── query-key-value.html
└── pilot-manifest.json
```

`index.html` is a lightweight launcher, not a second learning engine. It links to the built modules and explains the route in learner-facing language. Each module is generated through the existing canonical validator and renderer.

`pilot-manifest.json` is a closed, build-time route description containing only canonical module ID, opaque revision, canonical title, route order, relative output filename, and previous/next links. It contains no learner evidence, identity, timestamp, analytics field, telemetry field, or machine-specific path.

## Commands

From the repository root:

```bash
python prototype/pedagogical-module/build/build_pilot.py \
  --output /tmp/raiatea-pilot

python -m http.server 8000 --directory /tmp/raiatea-pilot
```

Open `http://127.0.0.1:8000/index.html`. Stop the local server with `Ctrl+C` in the terminal.

The first command fails closed without replacing an existing output path or leaving a hidden staging directory. The second command uses only the Python standard library.

## Navigation rules

- launcher starts with the self-attention orientation module;
- launcher also lists both modules for direct evaluator access;
- self-attention has no previous module and links next to query/key/value;
- query/key/value links back to self-attention and has no next module;
- both modules link back to the pilot index;
- generated navigation remains compatible with standalone module rendering;
- route labels are explanatory and do not change module or evidence identity.

## Build and installation behavior

The pilot builder:

1. resolves repository-relative canonical example paths from its own location;
2. loads and validates each canonical module, then derives route identity metadata from the validated object;
3. renders each module through the existing `build_module.py` implementation rather than duplicating rendering logic;
4. generates launcher and manifest from the same loaded route;
5. validates generated HTML, every declared output, and every relative route link in a same-parent staging directory;
6. atomically reserves the final directory with a no-replace directory creation;
7. installs validated regular files using no-overwrite hard links, so a concurrent destination file is never silently replaced;
8. revalidates the installed output and cleans only files created by this build if installation fails;
9. removes the staging directory on every success and failure path;
10. avoids network access and external runtime dependencies.

A destination that already exists initially or appears during the build is preserved and the build fails. If the platform or filesystem cannot support the no-overwrite hard-link installation used by this prototype, the build fails closed rather than falling back to replacement.

## Verification responsibilities

Tests cover:

- canonical IDs, revisions, titles, output filenames, and pedagogical route order;
- both modules built through the canonical validator and renderer;
- launcher links and previous/next links resolving inside the output directory;
- byte-deterministic output across independent builds;
- no absolute filesystem paths in generated launcher or manifest;
- no learner evidence, personal data, timestamps, analytics, or telemetry in the manifest;
- existing and concurrently created destinations preserved without changes;
- invalid module input leaving no completed output or staging directory;
- CLI success and deterministic refusal of an existing destination;
- browser launcher smoke coverage through both modules and back to the index;
- all existing standalone module builds, evidence contracts, migration contracts, and browser interactions unchanged.

## Deferred work

- learner-facing route dashboard with progress aggregation;
- cross-module completion rules;
- pilot-specific evidence walkthrough;
- evaluator acceptance checklist and release archive;
- accounts, cloud sync, LMS integration, analytics, or AI-generated content.
