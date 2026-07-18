# First runnable Raiatea pilot contract

Status: initial implementation contract for issue #60 under parent #58.

## Goal

Package the existing pedagogical-module engine as one locally runnable two-module learner journey with a single entry page, deterministic build output, and simple evaluator instructions.

## Pilot route

The initial route uses two existing canonical modules:

1. `query-key-value` — introduces query, key, and value responsibilities;
2. `self-attention` — continues into the complete self-attention flow.

The route order is authored explicitly. The launcher and module navigation must use relative links only and must not depend on repository checkout paths.

## Output layout

A deterministic build creates one disposable output directory:

```text
pilot-dist/
├── index.html
├── query-key-value.html
├── self-attention.html
└── pilot-manifest.json
```

`index.html` is a lightweight launcher, not a second learning engine. It links to the built modules and explains the route in learner-facing language. Each module remains generated through the existing canonical build path.

`pilot-manifest.json` is a closed, build-time route description containing only module IDs, titles, order, relative output filenames, and previous/next links. It contains no learner evidence, identity, timestamps, analytics, or machine-specific paths.

## Commands

The target interface is:

```bash
python prototype/pedagogical-module/build/build_pilot.py \
  --output /tmp/raiatea-pilot

python -m http.server 8000 --directory /tmp/raiatea-pilot
```

The first command must fail closed without leaving a partially valid output directory. The second command uses only the Python standard library.

## Navigation rules

- launcher links to the first module;
- launcher also lists both modules for direct evaluator access;
- the first module has no previous module and links next to self-attention;
- the second module links back to query/key/value and has no next module;
- generated navigation remains compatible with standalone module rendering;
- route labels are explanatory and do not change module or evidence identity.

## Build behavior

The pilot builder must:

1. resolve repository-relative canonical example paths from its own location;
2. build each module through the existing `build_module.py` implementation rather than duplicating rendering;
3. generate launcher and manifest from one in-memory route definition;
4. validate that every declared output exists and every relative route link resolves;
5. install the completed directory only after all temporary outputs pass validation;
6. avoid network access and external runtime dependencies.

## Verification

Tests must cover:

- deterministic output filenames and route order;
- both modules built through the canonical validator and renderer;
- launcher links and previous/next links resolve inside the output directory;
- no absolute filesystem paths appear in generated launcher or manifest;
- no learner evidence, personal data, timestamps, or telemetry appears in the manifest;
- an invalid module build leaves no completed pilot output;
- existing standalone builds and browser tests remain unchanged;
- a browser smoke test opens the launcher and reaches both modules.

## Deferred work

- learner-facing route dashboard with progress aggregation;
- cross-module completion rules;
- pilot-specific evidence walkthrough;
- evaluator checklist and release archive;
- accounts, cloud sync, LMS integration, analytics, or AI-generated content.
