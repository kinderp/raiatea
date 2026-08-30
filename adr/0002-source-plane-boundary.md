# ADR-0002 — Source Plane product boundary and simple local execution

Status: **Proposed**

Issue: #210  
Related P0 parent: #106  
Related PDF increment: #203  
Active implementation: #208 / PR #209

## Context

Raiatea's P0 Source Ingestion & Extraction work has produced a reusable technical foundation around heterogeneous sources and extraction engines:

- Source Families, traits and benchmark classes;
- Provider and RouteProfile separation;
- rights- and policy-aware route eligibility;
- ProviderEvidence / Raw Extraction separated from normalized representation;
- typed Source Coordinates;
- Warning / Degraded Result / partial / unknown semantics;
- provenance and transformation lineage;
- benchmark-backed route evidence rather than one global quality score;
- replaceable Source, Extractor and Transformer plugin boundaries;
- out-of-process local plugin execution.

The implementation still lives inside the Raiatea repository and its accepted conceptual contracts currently assign several extraction semantics to Raiatea Core. However, the capability is increasingly useful outside Raiatea's knowledge-product concerns and carries a very different operational profile from the rest of Raiatea: parser/OCR dependencies, model payloads, CPU/GPU requirements, provider version drift, acquisition protocols and potentially replicated workers.

At the same time, the extraction experience must remain simple. A user who adds a PDF, EPUB or later an authorized web/news source should not have to understand provider topology, containers, queues or worker scheduling in order to obtain a useful result.

The architectural question is therefore not whether extraction should become distributed immediately. It is where the durable ownership boundary should be placed while preserving a near-zero-configuration local experience.

## Decision

Adopt **Source Plane** as the provisional name for a separately owned infrastructure product / bounded context that will eventually own general Source acquisition, extraction and evidence-quality mechanics.

The physical code remains in the Raiatea repository for the current PDF1 work. This ADR records the target ownership boundary and migration direction; it does not authorize an immediate repository split.

### 1. Source Plane is infrastructure, not a second Raiatea

Source Plane is a headless infrastructure product. Its primary surfaces are contracts/API, a local runtime, worker execution, diagnostics and quality evidence. A small technical administration console may exist later.

Source Plane must **not** create competing implementations of:

- Raiatea Universal Document & Asset Library;
- catalog Views or Smart Collections;
- Raiatea Workspaces / Expeditions;
- Actor, Idea, Topic, Claim or Event knowledge models;
- knowledge graph / Observatory / Horizon / Agora;
- user-facing truth or interpretation authority.

Raiatea remains a consumer that turns acquired and extracted evidence into catalog and knowledge experiences.

### 2. Default operation must be simple and low-configuration

The default local deployment is one logical Source Plane service/runtime from the user's point of view.

The first usable experience should require approximately:

```text
install / enable Source Plane
-> start one local service or equivalent supervisor
-> submit an authorized Source
-> receive current result + evidence + warnings
```

The user must not be required to manually compose Provider workers, queues, containers or scheduler rules for ordinary local use.

The implementation may internally supervise multiple isolated worker processes and route profiles, but safe built-in defaults and capability discovery must hide unnecessary topology from the normal product path.

Advanced configuration remains possible for operators and debugging, but complexity is opt-in.

### 3. Separate a logical Control Plane from replaceable Workers

Target logical shape:

```text
Source Plane
  |
  +-- Control Plane
  |     +-- Source gateway / acquisition boundary
  |     +-- source probing + traits
  |     +-- authority / rights eligibility
  |     +-- route planner
  |     +-- quality registry
  |     +-- run supervision
  |     +-- evidence validation
  |     +-- provider-neutral document normalization
  |     +-- technical provenance
  |
  +-- Worker Plane
        +-- PDF providers
        +-- EPUB/package providers
        +-- OCR providers
        +-- web/feed acquisition providers
        +-- audiovisual/transcription providers
        +-- repository/code providers
        +-- future specialized routes
```

This is an ownership and deployment model, not a requirement for separate network services in the first version. A local installation may host the Control Plane and workers on one machine under one supervisor.

### 4. Workers remain isolated, replaceable and profile-addressed

A Provider brand is not a routing unit. RouteProfile remains the material execution identity.

Durable routing must continue to use the accepted shape:

```text
Source Family + traits
+ requested operation / evidence families
+ coordinate requirements
+ authority / rights / sensitivity / retention
+ security eligibility
+ benchmark evidence
+ resource / cost constraints
-> eligible RouteProfiles
```

Do not reduce the architecture to mappings such as `.pdf -> Docling`.

Current local out-of-process plugin evidence remains valid input to the future Source Plane runtime. The current Raiatea Plugin API is **not renamed or extracted by this ADR**; its migration/versioning requires a separate decision after current PDF work stabilizes.

### 5. Quality remains multidimensional and evidence-backed

Source Plane owns a **Quality Registry / Quality Lab** concept that distinguishes:

- **route quality evidence**: benchmark evidence for a specific RouteProfile + Benchmark Class / trait profile;
- **runtime document evidence**: what is actually established, partial, unavailable, ambiguous or malformed for one processed Source.

There is no authoritative universal quality score.

A route may be preferred for semantic hierarchy while another is preferred for fine geometry or another evidence family. Multiple routes may intentionally coexist.

Provider evidence remains independent. Cross-provider alignment, reconciliation or fusion must be a separate explicit derivation stage with its own basis, provenance and validation evidence.

### 6. Source Plane owns document/extraction semantics; Raiatea owns knowledge semantics

Target ownership after migration:

**Source Plane owns or supplies:**

- Source Family / traits / technical source version or snapshot;
- acquisition method and technical acquisition provenance;
- ProviderRef / RouteProfileRef;
- technical ProcessingRun / stages;
- ProviderEvidence / Raw Extraction;
- document-level Source Coordinates;
- document-level NormalizedRepresentation;
- extraction warnings / degraded / partial / unknown states;
- provider/model/runtime provenance;
- benchmark / quality evidence.

**Raiatea owns:**

- catalog Logical Identity and user Library semantics;
- relationships between holdings/copies/representations at product level;
- Search / Views / Smart Collections product semantics;
- knowledge Observation derived from Source Plane evidence;
- Actor / Organization / Idea / Movement / Topic / Field / Technology / Event / Process;
- Claim / Evidence / CounterEvidence epistemic relationships;
- Workspaces / Expeditions;
- Reality Observatory / Horizon / Agora / shared knowledge.

Source Plane may state what a Provider observed and how the observation was normalized. It does not decide whether a public-world claim is true or how it should be interpreted.

### 7. Acquisition intent stays with the consumer when it is a knowledge concern

For future online sources, a consumer such as Raiatea may decide **what should be watched and why**. Source Plane executes the bounded authorized acquisition and records the resulting Source version/snapshot and provenance.

Example boundary:

```text
Raiatea Knowledge Sensor
  -> requests check/acquisition of selected authorized resource
Source Plane
  -> acquire / version / extract / report change evidence
Raiatea
  -> decide whether the change matters to a Topic, Actor, Expedition or present-world model
```

This keeps news/social monitoring strategy out of the extraction infrastructure while making acquisition reusable.

### 8. Container/pod workers, replicas and worker dashboard are future evolution

The architecture must not prevent workers from later running as containers or pods, with multiple replicas selected by capability and load. This is especially relevant to high-volume web/news acquisition, OCR and GPU-backed routes.

However, this ADR does **not** select:

- Docker Compose;
- Docker Swarm;
- Kubernetes;
- Nomad;
- another orchestrator;
- a queue technology;
- a service mesh;
- autoscaling policy.

A future **Worker Dashboard** is an intended operational surface for observing worker identity/profile, health, capacity, queue/run state, resource use, failures and replicas. It is not a current product acceptance requirement.

The first local deployment must not inherit distributed-system complexity merely because later deployments may use replicas.

### 9. Deployment scale must not change extraction semantics

Source Plane must be distributable both as a **near-zero-configuration local runtime** and, in the future, as a **multi-tenant or dedicated Extraction-as-a-Service deployment with a horizontally replicable Worker Plane**, without changing the semantic extraction contract exposed to consumers.

The durable invariance is:

```text
same Source / request intent
+ same RouteProfile contract
+ same evidence semantics
+ same provenance / warning / quality rules

regardless of whether execution happens on:

one local worker
-> several workers on one host
-> replicated container workers
-> a clustered commercial service
```

Deployment topology, replica count and scheduler placement are operational facts, not document semantics. They may appear in technical ProcessingRun provenance and metering, but must not redefine ProviderEvidence or NormalizedRepresentation meaning.

This permits a future commercial Source Plane service for continuous authorized extraction of documents, feeds, web/news sources, audiovisual material and other Source Families while preserving compatibility with local Raiatea installations and other clients.

Commercial scale-out may later add API gateway, tenant isolation, quotas, metering, shared or dedicated worker pools, queue-based dispatch and autoscaling. Those capabilities must remain outside the semantic contract and require separate security, privacy, rights and operational decisions.

### 10. Migration is staged after current PDF evidence is stable

Do not interrupt PDF1c/PDF1d/PDF1 exit to perform the physical split.

Migration direction:

```text
Stage 0 — current
  P0/VS1/PDF code remains in Raiatea
  architecture boundary documented

Stage 1 — after bounded PDF evidence is stable
  define Source Plane public/application boundary
  classify which existing contracts migrate, remain Raiatea-owned or are superseded

Stage 2
  extract Provider/worker, route, evidence, quality and acquisition mechanics
  retain Raiatea client/adapter and compatibility tests

Stage 3
  optional separate repository/package/product distribution
  only after independent reuse and operational value are demonstrated
```

No current record/schema should be renamed merely to anticipate Stage 2.

## Alternatives considered

| Alternative | Advantages | Risks / costs | Decision |
| --- | --- | --- | --- |
| Keep all Source/Extraction permanently inside Raiatea | lowest short-term boundary cost; one Core owns everything | parser/OCR/model operational concerns pollute knowledge product; weak ecosystem reuse; harder independent scaling and upgrades | Rejected as durable target |
| Extract only a shared in-process library/SDK | simple calls and low runtime overhead | dependency/runtime coupling; provider crashes and native/model conflicts affect clients; harder worker reuse and heterogeneous runtime support | Useful implementation technique for pure contracts, rejected as sole product boundary |
| Build Source Plane as separate infrastructure product with simple local runtime and replaceable workers | clean ownership; reusable; isolated dependencies; future scale-out; preserves local-first UX | requires explicit client/API and lifecycle boundaries; migration/versioning work | **Chosen** |
| Build a fully independent document-management application with its own catalog/search/UI | standalone marketable application | duplicates Raiatea Library and product semantics; creates two authorities and unnecessary UX scope | Rejected |
| Start immediately with Kubernetes/microservices/replicated worker pools | scale and operational isolation from day one | large configuration/operations burden; violates simplicity-first; premature without measured workload | Rejected for first deployment; future-compatible only |

## Consequences

### Positive

- Raiatea's knowledge architecture is decoupled from parser/OCR/provider operational complexity.
- The extraction foundation can eventually serve Raiatea, TheBitLab and other authorized consumers.
- Provider/model upgrades can be qualified independently through the Quality Lab.
- CPU/GPU/heavy dependencies can remain isolated from client runtimes.
- A single local deployment remains possible and is the default target.
- The same consumer-facing semantic contract can survive local, replicated and future commercial deployments.
- Future replicated worker deployments do not require changing Raiatea's product semantics.
- Continuous authorized extraction can become an independently operable and monetizable service without turning deployment topology into knowledge truth.
- Current multi-provider truth boundaries, especially the PDF Poppler/Docling non-fusion rule, become a general infrastructure invariant rather than a PDF-specific exception.

### Costs / constraints

- A stable application/client boundary must eventually be versioned.
- Artifact transfer and identity across the boundary must avoid leaking host paths or creating a second catalog authority.
- Rights/authority ownership must be re-audited carefully when the physical split occurs; separation must not create a route around current fail-closed policy.
- Multi-tenant operation will require explicit tenant isolation, quota, metering, privacy, retention and abuse-resistance decisions before any commercial deployment.
- Existing E-05 documents currently describe some semantics as Raiatea Core-owned and will need a deliberate migration/superseding update rather than silent rewriting.
- Plugin API naming/ownership requires a later compatibility decision.
- Source Plane needs its own operational lifecycle, diagnostics and upgrade story once physically separated.

## Evidence supporting the direction

Repository evidence already establishes the important technical properties:

- `elaboration/p0/source-taxonomy.md` — accepted source-family/traits/benchmark-oriented taxonomy;
- `elaboration/p0/build-buy-reuse.md` — accepted thin-layer, benchmark-first, provider-neutral route strategy;
- `elaboration/p0/provider-neutral-extraction-contract.md` — accepted evidence-state, RouteProfile, Source Coordinate, provenance and no-universal-quality-score semantics;
- `adr/0001-plugin-local-process-transport-candidate.md` — accepted out-of-process local plugin transport and isolation evidence;
- #203 — promoted PDF increment retaining complementary Poppler and Docling profiles without automatic fusion;
- #208 / PR #209 — active Docling route proving exact environment/model/profile isolation.

These artifacts show that the differentiating capability is not one parser. It is the replaceable, inspectable and evidence-backed control layer around heterogeneous routes.

## Not decided here

- final product/repository name;
- exact public API protocol or serialization;
- whether the initial service runs as a daemon, supervised subprocess tree or another packaging shape;
- artifact store implementation;
- production queue implementation;
- Durex reuse for general Job/Run execution;
- container image layout;
- Docker Swarm, Kubernetes or another orchestrator;
- worker autoscaling policy;
- remote/cloud commercial deployment mechanics;
- multi-tenant identity, billing and metering design;
- worker dashboard UX and metrics backend;
- cross-provider alignment algorithm;
- final ownership/versioning of the current Raiatea Plugin API;
- exact E-05 migration/version compatibility plan.

Each requires separate evidence and, when architecturally significant, a separate ADR.

## Superseding decisions

None.

If the product boundary, local runtime shape or ownership model changes after evidence from PDF1 exit or independent consumers, preserve this ADR and create a superseding ADR rather than rewriting the history.