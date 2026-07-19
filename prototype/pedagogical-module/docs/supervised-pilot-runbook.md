# Supervised pilot runbook

Issue: #94  
Parent: #93

## Goal

Define one closed operational checklist for a supervised Raiatea classroom pilot using the verified local synthesis kit.

## Ordered session phases

1. verify release identity and checksums;
2. confirm supported local runtime and loopback-only launch;
3. prepare the room without collecting learner identity;
4. start the pilot and record only checklist outcomes;
5. stop immediately on explicit safety, privacy or runtime criteria;
6. stop the local server and verify owned-state cleanup;
7. export only already-defined evaluator records when explicitly required;
8. delete temporary local copies and complete the closeout checklist.

## Closed checklist boundary

The machine-readable checklist will contain only canonical boolean phase results, one release version, one supported platform and launcher pairing, and a closed completion status. It will not contain names, learner answers, timestamps, class identifiers, free-form observations, device details, accounts or network destinations.

## Scope

This increment defines and validates the runbook and checklist only. Incident records, release-candidate gating and final pilot decisions remain #95–#97.

## Verification

Tests must cover field closure, canonical phase order, platform/launcher pairing, fail-closed completion rules, privacy exclusions and deterministic serialization. Merge requires green Linux and Windows Actions, a finding log and two clean final-head reviews.