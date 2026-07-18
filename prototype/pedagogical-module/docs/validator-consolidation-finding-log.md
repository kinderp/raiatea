# Pedagogical module validator consolidation finding log

Parent issue: #33  
Child issue: #34

## Objective

Replace the temporary layered `validate_module.py` plus `validate_module_v2.py` architecture with one canonical `validate_module.py` implementation while preserving every current module, layout, remediation, provenance, procedure, rendered-HTML, learner-evidence, and browser regression.

## Initial review checklist

- preserve exact `ValidationIssue` and `ModuleValidationError` behavior;
- merge revision and stable-step identity validation into the canonical module validator;
- merge remediation, recovery activity, and provenance validation;
- preserve declarative layout resolution and module-local path safety;
- migrate every runtime, test, documentation, and CI consumer;
- remove `validate_module_v2.py` only after the repository contains no reference to it;
- replace broad `${...}` broken-link suppression with script-aware internal-link extraction;
- prove advanced primitives, procedure modules, generated HTML, v1 evidence, v2 evidence, manifests, preview, and confirmed application remain unchanged;
- record every red Actions run and its repository correction;
- complete two consecutive clean review rounds on one unchanged final head.

## Findings

No finding recorded yet. The first implementation review begins after the canonical validator and consumer migration are present on the branch.
