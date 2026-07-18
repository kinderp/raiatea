# Pilot end-to-end acceptance finding log

Issue: #68  
Pull request: #67

## Reviewed implementation

The final increment adds no new learner behavior. It proves the complete generated pilot journey through one manual evaluator checklist and one Playwright acceptance path.

## Findings

### F1 — resolved — acceptance could have tested helpers instead of the generated product

The browser acceptance uses the same generated pilot directory served by Playwright and traverses launcher, both generated modules, dashboard, summary, remediation, and download through visible controls.

### F2 — resolved — remediation was not part of the previous route-level smoke tests

The journey deliberately answers the first diagnostic incorrectly, completes the recovery micro-activity, retries, and verifies a correct-after-remediation summary.

### F3 — resolved — cross-module state continuity needed one complete proof

The test moves from the first module to the second, records evidence in both, returns to the launcher, and verifies both derived dashboard states plus the advisory recommendation.

### F4 — resolved — export acceptance needed integration with the full journey

The second module export is triggered explicitly after a real correct interaction. Filename, v1 identity, module scope, and evidence values are asserted while local progress remains byte-for-byte unchanged.

### F5 — resolved — external-service independence needed a journey-wide assertion

Every browser request is collected across the full path and must remain on the loopback pilot server. No account, cloud, analytics, telemetry, or remote service is introduced.

### F6 — resolved — manual acceptance needed non-developer language

`PILOT-ACCEPTANCE.md` provides exact commands, numbered clicks, visible expected outcomes, troubleshooting, privacy checks, and a printable pass/fail record without requiring architecture knowledge.

### F7 — resolved — build acceptance and overwrite policy needed explicit evaluator coverage

The checklist requires a successful fresh build and a second-build refusal against the same destination, preserving the no-overwrite contract already covered by unit tests.

### F8 — resolved — closeout traceability needed to be normative

The acceptance contract and documentation index state the final merge, child closure, parent #58 closure, and complete milestone traceability requirements.

## Open findings

None.

## Final verification pending

- GitHub Actions green on the unchanged final head;
- two consecutive clean reviews on that head;
- protected squash merge;
- child #68 and parent #58 closure.
