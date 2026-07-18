# Pilot end-to-end acceptance contract

Status: initial implementation contract for the final child increment under parent issue #58.

## Goal

Prove that the first Raiatea pilot can be built, served, navigated, exercised, summarized, and exported end to end by a non-developer evaluator using the documented local workflow.

## Acceptance journey

1. build the pilot into a new destination;
2. serve the generated directory on loopback;
3. open the launcher and verify the canonical two-module route;
4. enter the first module and complete one correct and one remediation-assisted interaction;
5. return to the dashboard and verify derived route status;
6. navigate to the second module without an access gate;
7. inspect the module-local summary;
8. explicitly export one learner-evidence v1 JSON file;
9. verify filename, module scope, privacy allowlist, and unchanged browser-local state;
10. return to the launcher and verify recommendation and links remain coherent.

## Manual acceptance artifact

The repository must contain one concise evaluator checklist with:

- prerequisites;
- exact build, serve, open, and stop commands;
- numbered clicks and expected visible outcomes;
- failure troubleshooting that does not ask the evaluator to inspect internal architecture;
- a final pass/fail record template;
- explicit local/offline/privacy boundaries.

## Automated acceptance

One browser test must exercise the complete journey through generated pilot files rather than isolated helpers. It must assert:

- launcher, both modules, dashboard, summary, remediation, and download are reachable;
- relative navigation remains coherent;
- no external network request occurs;
- no account, learner identity, analytics, or telemetry is introduced;
- progress and dashboard state survive page transitions;
- the explicit export remains module-scoped and non-destructive;
- existing unit and browser regressions remain unchanged.

## Build acceptance

The generated pilot directory must be complete, deterministic, self-contained for runtime use, and refuse overwrite of an existing destination. CI must build and verify the same artifact used by browser acceptance.

## Boundaries

This increment does not add new learner behavior, module content, evidence versions, dashboard semantics, migration behavior, remote integrations, or a deployment service. It closes the first pilot by proving the already delivered journey.

## Definition of Done

- manual evaluator checklist complete;
- automated full-journey acceptance green;
- finding log has no open findings;
- GitHub Actions green on the final head;
- two consecutive clean reviews on the unchanged final head;
- protected squash merge complete;
- child issue and parent #58 closed with final traceability.
