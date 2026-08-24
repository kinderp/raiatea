# v1d transport change log

Transport baseline: v1c merge `88e33198b338b097373a21c53d6be7ca9e2aef34`.

## Final real-proof result

Status: **no transport changes required**.

The v1d proof code imports and uses the accepted v1c `transport.py` and `process_harness.py` unchanged. All new path/handle resolution remains confined to `proof_broker.py` under the proof directory and is explicitly non-production/out-of-band.

Real proof coverage:

- rights-safe `LocalReadOnlySourcePlugin` over a deterministic project-created local library;
- benchmark-backed direct EPUB stdlib `ExtractorPlugin` producing/referencing accepted E-05 records;
- real subprocess startup/handshake/invocation/diagnostic/shutdown paths;
- Source scope escape and subprocess crash;
- extractor media/profile/AssetHandle negative paths;
- canonical E-05 result validation after the process boundary;
- accepted v1a/v1b/v1c regression suites rerun within the cross-platform proof jobs.

Evidence on pre-ADR evidence head `99eeffdadd8213f70500de45968a03f2d247b5f2`:

- v1d workflow `32713762585` — success;
- Linux Python 3.10 and 3.12 — success;
- Windows Python 3.10 and 3.12 — success;
- manifest/E-05 schema reference validation — success;
- E-05 conformance workflow `32713762546` — success after #172 hardening.

## Findings relevant to transport

No real proof required a v1c wire/framing change.

The most material integration finding was #172: E-05 semantic validation needed to bind known source classes to compatible populated SourceCoordinate families. That fix belongs to E-05 and required no change to JSON-RPC/NDJSON, the runtime contract, or proof process framing.

This separation is part of the acceptance evidence for ADR-0001: transport validity, runtime validity and domain validity remain distinct layers.

## Decision

ADR-0001 is promoted to **Accepted** in this v1d branch, subject to final unchanged-head CI and review gates for PR #171.
