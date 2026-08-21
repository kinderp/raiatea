# P0 Threat Boundary

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#123](https://github.com/kinderp/raiatea/issues/123)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Elaboration gate: [`08-inception-review.md`](../../genesis/inception/08-inception-review.md)
>
> Canonical vocabulary: [`07-glossary.md`](../../genesis/inception/07-glossary.md)
>
> Source taxonomy: [`source-taxonomy.md`](source-taxonomy.md)
>
> Rights/data boundary: [`rights-data-boundary.md`](rights-data-boundary.md)

## 1. Purpose and security posture

This document identifies P0 trust boundaries, threat classes and fail-closed
requirements before the project selects extraction Providers or implements the
candidate first slice.

It is not a full implementation security architecture and does not claim that
listed threats are mitigated. It provides the threat-oriented input needed for
later Provider survey, benchmark design, P0 contracts and local workspace
security decisions.

The foundational posture is:

> **Source content, Source metadata, Provider output and filesystem observations
> are data to evaluate; none of them grants authority.**

In particular, text extracted from a document must never acquire control-plane
meaning merely because an LLM, OCR engine or parser produced it.

## 2. Protected assets and properties

> Assertion status: `accepted-decision` for protection goals; implementation is
> future work

P0 must protect at least:

### User-controlled source material

- Original Artifacts;
- private/restricted source content;
- source code and notebooks;
- embedded images/files;
- physical/digital Location information.

### Catalog and identity state

- Logical Identity relationships;
- Stored Instance/Location state;
- duplicate/related-representation decisions;
- missing/offline/deleted state;
- user corrections.

### Provenance and processing state

- Source Coordinates;
- Raw Extraction;
- Normalized Representation;
- Transformations;
- Provider/model/version/parameter references;
- Warnings/Degraded Result state;
- Lineage;
- success/failure/unknown/partial processing state.

### Operational authority

- which Locations may be observed/read;
- which Sources may be processed;
- which Providers may receive content;
- where outputs may be written;
- which files, if any, may later be moved/renamed/deleted.

### Secrets and private metadata

- credentials/API keys;
- tokens/configuration secrets;
- account identifiers;
- private paths and filenames;
- Provider credentials;
- logs containing Source content.

## 3. Trust zones

> Assertion status: `provisional-decision`

### TZ-0 — Untrusted Source content

Every heterogeneous Source is potentially untrusted input, even when the user
owns it.

Reasons include:

- malformed file/container;
- active content or macros;
- hostile embedded objects;
- prompt/instruction text aimed at AI components;
- decompression/resource-exhaustion payloads;
- manipulated metadata/path values;
- secrets or sensitive material the user did not notice.

### TZ-1 — User-approved storage boundary

Filesystem/storage Locations explicitly made observable/processable by the user.

Important invariant:

> The existence of a file inside an observed Location does not grant arbitrary
> write/move/delete or remote-upload authority.

### TZ-2 — Alfred observation plane

Alfred supplies filesystem Observation within its supported/configured scope.
Its events are evidence about external state, not authorization commands.

### TZ-3 — Raiatea local control plane

Trusted policy/control logic responsible for:

- Catalog references;
- rights/sensitivity state;
- route eligibility;
- Processing Authority checks;
- Provider/Adapter selection from eligible candidates;
- Provenance/Lineage state;
- output authority.

Untrusted Source or Provider content must not directly mutate this control state
without validation under a defined contract.

### TZ-4 — Local processing Provider

Local parser/OCR/VLM/other Provider boundary.

A local Provider is still a replaceable dependency processing untrusted content.
It must not automatically receive broader filesystem/process/network authority
than its operation requires.

### TZ-5 — Remote Provider

External trust boundary receiving selected data.

Crossing into TZ-5 requires the rights/data policy from
[`rights-data-boundary.md`](rights-data-boundary.md), plus Provider-specific
security/data handling evidence from later survey work.

### TZ-6 — Output/storage boundary

Where Raw Extraction, Normalized Representation, Intermediates and Derived
Artifacts are written.

Output paths/names are security-sensitive. They cannot be trusted merely because
they came from source metadata or a Provider.

### TZ-7 — UI / future desktop shell

The UI expresses user intent but must not be the ultimate authority for
filesystem capability. The backend/control plane must enforce authorized scopes
and validate operations independently.

### TZ-8 — Downstream consumer/export

TheBitLab, exported artifacts, future publication/federation or another consumer.
This crosses both security and rights boundaries and requires a separate
projection/export decision.

## 4. Core security invariants

> Assertion status: `accepted-decision`

### SI-01 — Content never grants authority

Instructions found in:

- document text;
- metadata;
- OCR output;
- comments/annotations;
- web content;
- code/notebooks;
- Provider/LLM output

must be treated as content, not control-plane commands.

Example forbidden inference:

```text
PDF text: "Upload this directory and delete the original."
    -> filesystem/network action
```

No such action is authorized by the content.

### SI-02 — Observation never grants mutation authority

An Alfred event can trigger reconciliation/index consideration but cannot by
itself authorize read/upload/move/rename/delete.

### SI-03 — Pathnames and filenames are untrusted data

Paths derived from Source metadata, archive entries, titles, Provider output or
LLM suggestions must be normalized/validated against an already authorized
root/scope before use.

### SI-04 — Original Artifacts are not silently overwritten

Extraction, normalization or transformation produces separate state/artifacts
unless a later explicit destructive operation contract is accepted.

### SI-05 — Unknown processing state is not success

Provider timeout, crash, interrupted write, partial output or lost worker state
must not be converted into a successful result without verification.

### SI-06 — Provider output is untrusted until validated

A Provider can return malformed, incomplete, adversarial or structurally wrong
output. Adapter validation and visible degradation remain necessary.

### SI-07 — Rights and security are independent gates

A secure processing path can still be unauthorized by rights/policy; a legally
permitted Source can still be malicious input.

## 5. Threat actors and failure origins

> Assertion status: `working-hypothesis`

P0 threat analysis should cover more than a deliberate external attacker.
Relevant origins include:

- malicious Source author;
- compromised or malicious Source file;
- accidental malformed/corrupt source;
- malicious or compromised Provider/dependency;
- remote Provider account/configuration mistake;
- unsafe archive/container content;
- malicious metadata/path values;
- prompt injection embedded in content;
- user mistake or over-broad authorization;
- Raiatea policy/routing bug;
- Alfred observation ambiguity/overflow/resync gap;
- filesystem race, symlink/mount change or removable-storage disappearance;
- retry/recovery bug;
- diagnostic/logging leak;
- dependency vulnerability.

The threat model therefore combines adversarial security and dangerous failure
modes.

## 6. Threat scenarios

> Assertion status: `provisional-decision`

Threat IDs are editorial references, not API/schema identifiers.

### T-01 — Prompt/content injection expands authority

Scenario:

1. Source contains instructions addressed to an AI/model/tool.
2. Extraction or later LLM stage surfaces the instruction.
3. System interprets it as permission to read another path, call a tool, upload
   data, change policy or delete/move a file.

Required boundary:

- content channel and control channel remain separate;
- tool/filesystem/network actions require backend authorization derived from
  user/product policy, never Source text;
- natural-language query interpretation, when later implemented, can propose an
  inspectable query but cannot enlarge Authority Scope.

Relevant risks/gates: R-22, G-07.

### T-02 — Path traversal / unsafe output path

Scenario:

- source title/archive entry/metadata/Provider output proposes `../`, absolute
  path, reserved device name, unsafe Unicode/canonicalization or another path
  escaping the intended output root.

Required boundary:

- output destination is resolved relative to an authorized root;
- path components are validated/canonicalized according to platform contract;
- collisions and existing destinations are handled explicitly;
- no output path is trusted solely because it was generated by an LLM/Provider.

Relevant risks/gates: R-03, R-22, feature gate for organization.

### T-03 — Symlink/hardlink/mount/reparse ambiguity

Scenario:

- a path appears inside an authorized tree but resolves to content outside the
  intended scope, or changes target between validation and use.

Required boundary:

- later implementation must define filesystem-object identity and safe traversal
  semantics rather than rely on lexical path prefix alone;
- TOCTOU/race assumptions must be explicit;
- removable/mounted storage identity must be distinguished from path text.

Relevant risks/gates: R-01/R-02/R-03/R-22, G-03/G-07.

### T-04 — Archive/container escape or resource bomb

Scenario:

- document/container contains nested archives, enormous decompressed content,
  recursive references, excessive object counts or path-escaping entries.

Required boundary:

- bounded resource limits;
- archive/container traversal rules;
- no uncontrolled extraction to filesystem;
- excessive resource use becomes failure/Degraded Result, not host instability.

Relevant risks: R-05/R-06/R-22.

### T-05 — Active content execution

Scenario:

- office macro, PDF action/script, HTML/JS, notebook code, embedded executable or
  linked active resource executes during inspection/extraction.

Required boundary:

- extraction is non-executing by default;
- active content is data unless an explicit isolated execution use case exists;
- future execution capability belongs behind a separate runtime/security gate.

Relevant risks: R-09/R-22; future execution-lab concerns.

### T-06 — Secrets/PII/private content leaked to remote Provider

Scenario:

- Source contains credentials, private notes, hidden revisions or sensitive
  content;
- remote route sends more content than intended.

Required boundary:

- remote transmission is an explicit policy event;
- route evaluates sensitivity/rights/Provider policy;
- later design decides whether preview/redaction/detection is required;
- Provenance records what class of data was transmitted.

Relevant risks/gates: R-09/R-22, G-02/G-07.

### T-07 — Provider retention/training/logging mismatch

Scenario:

- remote Provider retains or uses data in a way inconsistent with Raiatea policy
  or user expectation.

Required boundary:

- current Provider data-handling terms are survey inputs;
- unknown behavior remains uncertainty;
- Provider may be disqualified for a sensitive route;
- provider switching must remain possible.

Relevant risks/gates: R-09/R-19, G-02/G-04.

### T-08 — Provider output corrupts control/catalog state

Scenario:

- parser/OCR/VLM returns malformed JSON/paths/IDs/coordinates or deliberately
  crafted values;
- Adapter writes them directly into trusted control state.

Required boundary:

- Adapter validates Provider output against Raiatea semantics;
- external identifiers remain namespaced/provenanced;
- Provider cannot mint trusted Logical Identity or Authority Scope merely by
  returning a value;
- invalid output yields Warning/failure, not silent normalization to trusted
  state.

Relevant risks/gates: R-01/R-05/R-07, G-03/G-04/G-05.

### T-09 — Wrong Source Coordinates create false provenance

Scenario:

- extracted text is roughly correct but page/bbox/anchor points to the wrong
  source region;
- later user sees a plausible citation that cannot support the derived text.

Required boundary:

- coordinate fidelity is benchmarked separately from text fidelity;
- unsupported/unstable coordinate mappings are degraded/qualified;
- transformations preserve coordinate lineage where available.

Relevant risks/gates: R-05/R-07, G-04/G-05.

### T-10 — Retry/recovery duplicates or forks successful output

Scenario:

- worker/Provider completes but acknowledgement is lost;
- retry produces a second conflicting Derived Artifact or duplicate external
  side effect.

Required boundary:

- Processing Run identity/idempotency semantics before reliable long-running
  execution;
- known successful output not silently duplicated;
- unknown/partial state remains explicit;
- Durex reuse cannot be assumed until its generic contract is audited.

Relevant risks/gates: R-08/R-13, G-05.

### T-11 — Missing/offline storage treated as deletion

Scenario:

- NAS/removable disk/mount is unavailable;
- reconciliation marks Sources deleted and erases relationships/history.

Required boundary:

- Present/Unavailable/Missing/Deleted remain distinct evidence states;
- storage identity/freshness is recorded;
- disappearance does not automatically authorize destructive cleanup.

Relevant risks/gates: R-01/R-02/R-04/R-18, G-03/G-07.

### T-12 — Own move/rename event misclassified as a new Source

Scenario:

- future Organization Policy moves a Stored Instance;
- Alfred observes the change;
- Raiatea creates a duplicate Logical Identity or loses Location history.

Required boundary:

- expected operations/reconciliation contract;
- content/object identity evidence;
- move correlation from Alfred where available;
- no automatic merge based only on weak similarity.

Relevant risks/gates: R-01/R-02/R-03, G-03; organization remains feature-blocked.

### T-13 — Logs/diagnostics leak source content

Scenario:

- exception, request payload or debug log stores full document text, secret,
  path or remote Provider payload.

Required boundary:

- log schema should default to minimal metadata;
- source excerpts only when explicitly necessary/authorized;
- retention and export of diagnostic artifacts are policy-governed;
- redaction/secure debug mechanisms considered during implementation.

Relevant risks: R-09/R-18/R-22.

### T-14 — Malicious or compromised dependency

Scenario:

- parser/OCR library/CLI/provider dependency has malicious behavior or a
  vulnerability reachable through crafted input.

Required boundary:

- replaceable Adapter boundary;
- dependency/version provenance;
- minimized privileges/network/filesystem scope;
- later sandbox/isolation decision based on source/provider risk;
- survey records maintenance/security posture where evidence exists.

Relevant risks: R-09/R-19/R-22.

### T-15 — Denial of service by expensive input

Scenario:

- huge PDF, pathological layout, OCR-heavy images, recursive resources or model
  route consumes excessive CPU/GPU/memory/API cost/time.

Required boundary:

- preflight/bounds where possible;
- per-run resource/cost limits;
- cancellation/timeout;
- visible Degraded Result/failure;
- benchmark includes cost and manual repair, not quality alone.

Relevant risks/gates: R-06, G-04.

### T-16 — Benchmark/gold-data leakage or rights violation

Scenario:

- private/proprietary source or derived gold data is committed/published;
- benchmark artifacts expose material whose Redistribution Rights were never
  established.

Required boundary:

- fixture rights record;
- public benchmark packaging separated from private evaluation corpus;
- publication requires Redistribution Rights;
- CI/artifact uploads considered an external data flow.

Relevant risks/gates: R-09, G-02.

### T-17 — UI/backend authority mismatch

Scenario:

- browser or future desktop shell manipulates request parameters and asks backend
  to read/write outside configured scope.

Required boundary:

- backend enforces Authority Scope independently;
- client-visible IDs/paths are not capabilities by themselves;
- privileged filesystem/provider actions are revalidated server-side;
- local deployment is not equated with trusted input.

Relevant risks/gates: R-22, G-07.

### T-18 — Metadata confusion / identity poisoning

Scenario:

- Source metadata claims a misleading ISBN/DOI/title/author/path or malicious
  identifier;
- system merges it with an unrelated Catalog entry.

Required boundary:

- metadata is evidence with provenance;
- weak metadata match cannot cause irreversible identity merge;
- Exact Duplicate remains byte identity;
- Related Representation/identity suggestions can remain reviewable.

Relevant risks/gates: R-01, G-03.

## 7. Safe-processing requirements for Provider survey

> Assertion status: `working-hypothesis`

The later technology survey should collect evidence for Provider attributes such
as:

- can it process untrusted files without executing active content?
- process isolation model / deployment shape;
- filesystem access required;
- network access required;
- supported resource limits/timeouts;
- behavior on malformed input;
- archive/embedded-object behavior;
- output validation/schema guarantees;
- source-coordinate support;
- dependency/update/security maintenance posture;
- local versus remote execution;
- remote retention/training/logging terms where applicable;
- license and redistribution implications;
- deterministic/reproducible modes where relevant.

These attributes are evaluation criteria, not a claim that one Provider must
satisfy every property.

## 8. Control-plane versus content-plane model

> Assertion status: `accepted-decision`

The most important P0 security separation is:

```text
CONTENT PLANE
Source bytes
metadata
Raw Extraction
Normalized Representation
Provider/LLM output
      |
      | validated data only
      v
CONTROL PLANE
Authority Scope
rights/sensitivity policy
route eligibility
output-location policy
Processing Run state
Provenance policy
```

There must be no generic path where arbitrary content becomes a privileged
control instruction.

Future LLM usage must follow the same boundary. An LLM may classify, interpret
or propose; privileged actions require separately authorized, structured tool
contracts enforced by Raiatea.

## 9. Filesystem boundary requirements

> Assertion status: `provisional-decision`

Before any valuable corpus or managed organization feature, later design must
resolve:

- lexical path versus resolved filesystem-object semantics;
- symlink/hardlink/reparse-point policy;
- mount/storage identity;
- removable/offline state;
- race/TOCTOU behavior between validation and open/write;
- safe temporary/output file creation;
- atomicity where needed;
- collision handling;
- output root confinement;
- recovery/journaling for destructive operations;
- Alfred overflow/resync/freshness reconciliation.

The candidate first slice intentionally avoids automatic organization, but read
and output confinement still matter for P0 processing.

## 10. Provider isolation questions

> Assertion status: `working-hypothesis`

The project has not yet chosen whether extraction Providers require:

- separate OS process;
- sandbox/container;
- restricted user/account;
- seccomp/macOS sandbox/Windows isolation equivalent;
- network-disabled execution;
- read-only input mount;
- bounded scratch/output directory;
- CPU/memory/file-size/time quotas.

The survey/threat evidence should determine isolation proportional to Provider
and Source risk. This document does not prescribe one universal sandbox.

## 11. Remote Provider security boundary

> Assertion status: `provisional-decision`

Before a remote Provider route can be enabled for a Source class, later evidence
must cover:

- authentication/credential storage;
- TLS/transport assumptions via Provider-supported interface;
- data sent and minimization;
- rights/sensitivity eligibility;
- Provider data retention/training/logging behavior;
- error payloads/logging;
- result authenticity/integrity assumptions;
- rate/cost limits;
- retry/idempotency behavior;
- Provider outage/fallback;
- provenance of Provider/model/version where meaningful.

Remote processing is therefore a separate route class, not a transparent swap
for local execution.

## 12. Threat-to-gate map

> Assertion status: `working-hypothesis`

| Threat group | Main gate/risk input |
| --- | --- |
| T-01 content/prompt injection | G-07 / R-22 |
| T-02/T-03 path/link/mount escape | G-03, G-07 / R-01,R-03,R-22 |
| T-04/T-05 container/active content | G-04,G-07 / R-05,R-06,R-22 |
| T-06/T-07 remote leakage/provider policy | G-02,G-04,G-07 / R-09,R-19,R-22 |
| T-08/T-09 Provider output/provenance corruption | G-03,G-04,G-05 / R-01,R-05,R-07 |
| T-10 retry/partial state | G-05 / R-08,R-13 |
| T-11/T-12 reconciliation failures | G-03,G-07 / R-01,R-02,R-04,R-18 |
| T-13 logs leakage | G-02,G-07 / R-09,R-22 |
| T-14 dependency compromise | G-04,G-07 / R-19,R-22 |
| T-15 resource exhaustion | G-04 / R-06 |
| T-16 benchmark rights leak | G-02 / R-09 |
| T-17 UI/backend mismatch | G-07 / R-22 |
| T-18 metadata/identity poisoning | G-03 / R-01 |

The map does not mark any threat mitigated.

## 13. Security evidence required before first-slice promotion

> Assertion status: `provisional-decision`

At minimum, G-02/G-03/G-05/G-07 evidence should demonstrate for the bounded
first-slice environment:

- corpus/Provider data-flow eligibility;
- backend-enforced read/output scope;
- safe path/output confinement;
- untrusted input cannot grant filesystem/network authority;
- Exact Duplicate/rename/move reconciliation is conservative;
- missing/offline state is not destructive;
- Provider output is validated and provenance-linked;
- success/failure/unknown/partial state is explicit;
- minimum catalog/provenance backup/export exists;
- logs/diagnostics do not require unrestricted Source-content capture.

The exact tests belong to later experiment/implementation planning.

## 14. Security non-goals for #123

This threat boundary does not:

- implement a sandbox;
- select a security framework;
- claim formal verification;
- perform penetration testing;
- choose authentication technology;
- decide remote Provider credentials design;
- define production multi-user isolation;
- solve all web security;
- authorize active code execution;
- authorize automatic organization;
- claim that listed threats are mitigated.

## 15. Open questions

- Which Providers require process/sandbox isolation even for the first
  benchmark?
- Should benchmark parsers run with network disabled by default?
- Which file/container formats need preflight before Provider invocation?
- How should archive recursion/object-count limits be chosen empirically?
- Which Source classes need secret/PII scanning before remote processing?
- Which local web authentication/CSRF/origin controls are required for the first
  bounded environment?
- How should filesystem identity be represented across Linux/macOS/Windows?
- Which Alfred event/freshness guarantees are sufficient for P0 versus later
  managed organization?
- What minimum log/redaction contract is necessary for reproducible failures?
- How should Provider-supplied external links/resources be treated during
  extraction?

## 16. Evidence produced by this artifact

> Assertion status: `working-hypothesis`

This document advances:

- G-07 by defining control/data trust boundaries and local filesystem/UI threat
  requirements;
- G-02 by identifying remote data exfiltration/provider-policy threats;
- G-03 by identifying path/storage/identity/reconciliation threat cases;
- G-04 by defining security/robustness attributes for Provider survey/benchmark;
- G-05 by identifying provenance/partial/retry integrity requirements;
- R-22 as the primary local-authority risk;
- R-09/R-19 for remote Provider privacy/data policy;
- R-01/R-02/R-04 for filesystem identity/reconciliation;
- R-05/R-06 for malicious/pathological input;
- R-07/R-13 for provenance/processing integrity.

It does not satisfy these gates without later evidence.

## 17. Exit criteria for this artifact

Before acceptance, review must verify that:

- untrusted content cannot grant authority;
- Alfred Observation cannot grant authority;
- Source and Provider outputs are both treated as untrusted data;
- path traversal, symlink/mount ambiguity and unsafe outputs are visible risks;
- active content is non-executing by default;
- local/remote Provider boundaries align with rights/data policy;
- logs/intermediates are included in leakage/retention analysis;
- partial/retry/provenance integrity is covered;
- UI does not become the security authority;
- no sandbox/provider/framework is selected prematurely;
- no threat is falsely marked mitigated.
