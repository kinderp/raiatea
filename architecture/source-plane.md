# Source Plane — Target architecture note

Status: **Working architecture note / proposed boundary**  
ADR: [`ADR-0002`](../adr/0002-source-plane-boundary.md)  
Tracking issue: #210  
Current implementation remains in Raiatea while PDF1 is completed.

## 1. Purpose

Source Plane is the provisional infrastructure product that will eventually own general-purpose Source acquisition, extraction and evidence-quality mechanics currently developed as Raiatea P0.

Its user-facing promise is intentionally simple:

> Give Source Plane an authorized source and a processing intent; receive a truthful current result, inspectable evidence, provenance and warnings without manually configuring parser topology.

It is not a document-management product and it is not a knowledge system. Raiatea remains responsible for turning Source Plane outputs into Library and knowledge experiences.

## 2. Simplicity principle

The default installation must optimize for **time-to-first-use**, not operator flexibility.

A normal local user should not need to know:

- which Provider is running;
- which worker image/process is selected;
- whether the result required one or more internal stages;
- how queues are configured;
- how worker replicas are scheduled;
- where temporary artifacts are stored.

The normal path should be approximately:

```text
install / enable
-> one local bootstrap
-> add or submit authorized source
-> choose intent (or accept safe default)
-> result
```

The system should ship with conservative built-in route profiles for supported source classes and should fail visibly when a capability is unavailable rather than requiring ad-hoc local configuration.

Advanced operators may override routing, inspect profiles, pin versions and add workers, but these controls must not leak into the basic extraction workflow.

## 3. Logical architecture

```text
Consumers
  |
  +-- Raiatea
  +-- TheBitLab / other ecosystem consumers
  +-- future CLI/API clients
  |
  v
Source Plane application boundary
  |
  +-- Control Plane
  |     |
  |     +-- Source Gateway
  |     +-- Acquisition boundary
  |     +-- Probe / Source Family + Traits
  |     +-- Authority / Rights eligibility
  |     +-- Route Planner
  |     +-- Quality Registry
  |     +-- Run Supervisor
  |     +-- Evidence Validator
  |     +-- Document Normalizer
  |     +-- Technical Provenance
  |
  +-- Worker Plane
        |
        +-- document-native workers
        +-- OCR workers
        +-- web/feed workers
        +-- audiovisual/STT workers
        +-- repository/code workers
        +-- specialist workers
```

`Control Plane` and `Worker Plane` are logical ownership boundaries. They do not imply multiple hosts or Kubernetes in the first deployment.

## 4. Local-first runtime

### 4.1 First deployment target

The preferred first deployment is one local logical service on the same trusted host as the consumer, capable of supervising isolated Provider workers.

A possible implementation shape is:

```text
Source Plane supervisor
  +-- control-plane process
  +-- Poppler worker process
  +-- Docling worker process/environment
  +-- later OCR worker
  +-- later web worker
```

This note deliberately does not freeze process layout or the public transport.

### 4.2 Isolation without configuration burden

Worker isolation should be an implementation property, not a setup task imposed on the user.

The system should own:

- worker startup/shutdown;
- capability/profile discovery;
- health checks;
- safe temporary workspaces;
- bounded input/output authority;
- timeout/cancellation where supported;
- environment/model verification;
- provider diagnostics;
- retry policy only when semantically safe and explicit.

The existing local out-of-process Raiatea plugin proofs are useful migration evidence for this model.

## 5. Source and acquisition boundary

Source Plane should support technical acquisition across source families, but it should not decide why an external source matters to a knowledge product.

Examples:

### Local document

```text
Raiatea Library intent
  -> authorized local Source reference
Source Plane
  -> probe / process / evidence
Raiatea
  -> catalog/search/knowledge projection
```

### Future news/web monitoring

```text
Raiatea News/Topic Sensor
  -> selected resource should be checked
Source Plane
  -> authorized acquisition
  -> version/snapshot/change evidence
  -> extraction
Raiatea
  -> assess significance and update Topic/Actor/Expedition model
```

This allows Source Plane to be reusable without importing Raiatea's Observatory semantics.

## 6. Provider and RouteProfile model

Providers are implementation families. RouteProfiles are the reproducible routing units.

Examples:

```text
Provider: Docling 2.118.0
RouteProfile: native PDF / no OCR / exact model payload / CPU profile

Provider: Poppler 24.02.0
RouteProfile: pdftohtml XML geometry/asset profile
```

Routing decisions should be based on:

```text
Source Family / traits
+ requested operation
+ requested evidence families
+ Source Coordinate requirements
+ rights / sensitivity / retention
+ security eligibility
+ benchmark evidence
+ available resources
-> eligible RouteProfiles
```

No durable architecture should encode `.pdf -> Provider X` as the only decision rule.

## 7. Quality model

### 7.1 Quality is not one score

Quality must remain multidimensional because different source classes and intents require different evidence.

Candidate dimensions include:

- text fidelity;
- reading-order fidelity;
- hierarchy/semantic structure;
- coordinate fidelity;
- figures/assets;
- explicit relations such as figure-caption;
- table topology;
- formula semantics;
- transcription fidelity;
- timestamp/speaker alignment;
- capture/version reproducibility;
- visible degradation/failure behavior;
- manual repair burden;
- latency and resource observations.

Not every dimension applies to every source class.

### 7.2 Route quality vs runtime quality

Keep two separate forms of evidence.

**Route quality evidence** answers:

> How has this exact RouteProfile performed on this bounded Benchmark Class / trait profile?

**Runtime document evidence** answers:

> What is actually established for this Source in this run?

A strong benchmark route can still produce partial or unavailable evidence on an individual source.

### 7.3 Quality Registry / Quality Lab

The future Quality Lab should preserve:

- rights-safe fixtures;
- benchmark classes;
- authored/gold evidence where lawful;
- exact Provider and RouteProfile versions;
- model/dependency locks;
- quality vectors;
- resource observations;
- known failure cases;
- regressions between releases;
- promotion/limitation decisions for profiles.

Provider upgrades should be candidates until benchmark/regression evidence supports promotion.

## 8. Evidence and normalization

The durable layering remains:

```text
Original / acquired source version
   -> Provider-native observation / Raw Extraction
   -> validated ProviderEvidence
   -> document-level normalization
   -> optional explicit derivation/alignment
```

Rules:

- Provider success is not universal completeness;
- missing evidence never becomes zero or success;
- explicit empty and unavailable remain different;
- coordinates are typed by source semantics;
- Provider-native and Source-Plane-derived facts retain separate origins;
- cross-provider alignment requires an explicit derivation basis;
- original evidence remains inspectable under retention policy.

## 9. Current PDF example

PDF1 demonstrates why Source Plane must retain complementary routes.

```text
PDF Source
  |
  +-- Poppler profile
  |     -> fine text geometry / links / image evidence where exposed
  |
  +-- Docling profile
        -> richer semantic labels / picture-caption evidence where exposed
```

The current non-fusion rule is preserved:

```text
Poppler ProviderEvidence != Docling ProviderEvidence
```

If a future alignment stage combines evidence, the alignment itself must be versioned, inspectable and provenance-bearing.

## 10. Ownership boundary with Raiatea

### Source Plane

Owns the technical truth of acquisition and extraction:

- source technical class/traits;
- acquired version/snapshot identity;
- acquisition method;
- provider/route identity;
- processing stages;
- provider evidence;
- document/media coordinates;
- document-level normalized units;
- extraction diagnostics/warnings;
- technical lineage;
- quality/benchmark evidence.

### Raiatea

Owns product and epistemic meaning:

- Logical Identity and Library/catalog semantics;
- Views / Smart Collections;
- Workspaces / Expeditions;
- Observations as knowledge inputs;
- Actor / Organization / Idea / Movement / Topic / Field / Technology / Event / Process;
- claims and evidence/counter-evidence relationships;
- public-reality models;
- Observatory / Horizon / Agora;
- shared/federated knowledge semantics.

This boundary prevents Source Plane from becoming an authority over truth merely because it parsed a source successfully.

## 11. Future worker deployment

### 11.1 Containers/pods

Workers should be designed so that later implementations may package them as containers or pods when isolation, dependency conflicts, GPU placement or horizontal replication justify it.

Potential future examples:

```text
web-acquisition worker x N
PDF semantic worker x N
PDF geometry worker x N
OCR GPU worker x N
STT worker x N
```

This is a compatibility target, not the first deployment requirement.

### 11.2 Replicas

Replication may eventually be useful for:

- bursty web/news acquisition;
- parallel batch extraction;
- expensive OCR/STT queues;
- GPU-backed model routes;
- fault tolerance;
- heterogeneous hardware pools.

Replica count must be driven by measured workload and operational evidence rather than anticipated scale.

### 11.3 Worker Dashboard

A future technical dashboard should expose at least:

- worker identity/version;
- declared capabilities and RouteProfiles;
- execution environment/model payload;
- health/readiness;
- active/queued/recent runs;
- failure and restart history;
- CPU/RAM/GPU/resource observations;
- replica count and placement when distributed;
- version drift / unsupported profiles;
- quality-regression or quarantine state when applicable.

The dashboard is operational visibility. It must not become a second Raiatea Library or knowledge UI.

## 12. Deployment evolution

```text
Phase A — simple local
  one logical Source Plane runtime
  local isolated workers

Phase B — home/server
  one control plane
  workers possibly isolated in containers
  multiple local clients

Phase C — replicated workers
  capability pools / queues
  worker dashboard
  measured horizontal scaling

Phase D — distributed/federated deployment if justified
  explicit security, identity, authority and transport design
```

Each phase requires its own evidence and may stop if the additional complexity does not produce user value.

## 13. Migration from current Raiatea P0

The current implementation is valuable evidence and should not be rewritten during active PDF1 work.

Migration should inventory at least:

- Source taxonomy;
- E-05 conceptual/machine-readable extraction contracts;
- benchmark harness and Quality Lab evidence;
- Source/Extractor plugin contracts;
- local process transport;
- Provider implementations/proofs;
- rights-policy interfaces;
- asset/handle boundary;
- provenance records;
- PDF/EPUB product services.

For each artifact decide explicitly:

```text
move to Source Plane
remain Raiatea-owned
split into consumer/provider halves
supersede with versioned compatibility bridge
```

Do not mass-rename existing contracts before this inventory.

## 14. Explicit non-goals for the first Source Plane release

- Kubernetes requirement;
- user-managed worker topology;
- arbitrary remote execution;
- automatic cloud upload;
- marketplace/PKI;
- universal source support;
- universal quality score;
- automatic cross-provider fusion;
- duplicate Raiatea Library/search/knowledge features;
- full operational dashboard before workers require it.

## 15. Open decisions

Separate future decisions are required for:

- final product name;
- API protocol and versioning;
- packaging/bootstrap mechanism;
- artifact transport/store;
- job/run engine and possible Durex reuse;
- worker container contract;
- scheduler/orchestrator when replicas are justified;
- worker dashboard implementation;
- remote authentication/authorization;
- E-05 ownership migration and compatibility;
- Plugin API ownership/migration;
- cross-provider alignment algorithms.

