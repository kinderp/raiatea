# P0 Rights and Data Boundary

> Document maturity: `Accepted`
>
> Assertion status: `mixed`
>
> Version: 1.0.0
>
> Last reviewed: 21 August 2026
>
> Accepted through: [PR #124](https://github.com/kinderp/raiatea/pull/124)
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

## 1. Purpose and limits

This document defines the **architectural rights, authority, retention and data-
flow boundary** for P0.

It is not legal advice and does not decide whether a particular copyrighted,
licensed, personal, confidential or regulated source may lawfully be processed
in a particular jurisdiction. Where a legal conclusion is necessary, P0 must
record the unresolved dependency and obtain appropriate specialist review.

The architectural objective is narrower:

> Raiatea must know **what the user authorized, what rights evidence is known,
> what data a Provider would receive, what may be retained, and what may be
> redistributed** before a processing route crosses a trust boundary.

## 2. Canonical distinctions

> Assertion status: `accepted-decision`, inherited from the Glossary/Manifesto

P0 must not collapse these concepts:

```text
Processing Authority
    != Processing Rights
    != Redistribution Rights
    != Provider permission/terms
    != Retention Policy
```

### Processing Authority

The operational authority granted by the user/product to perform an action in a
bounded scope.

Examples:

- read/index a selected folder;
- process one selected Source;
- create a Derived Artifact in a permitted output location.

It does not prove legal permission.

### Processing Rights

The rights/permissions under which the requested processing is allowed in the
applicable source/license/context.

The project may record evidence about these rights, but must not infer them from
mere possession or accessibility.

### Redistribution Rights

The rights/permissions to publish/share source or derived material with others.

Private processing never automatically implies redistribution permission.

### Provider permission/terms

A Provider may impose its own data-handling, retention, training/logging or
service constraints. A route can be technically possible and user-authorized
while still being inappropriate under Provider terms or the Source's rights.

### Retention Policy

The policy governing which layers may be retained, for how long, where, and
under what deletion/expiry behavior.

## 3. Rights evidence state

> Assertion status: `provisional-decision`

For route selection, P0 needs an explicit state rather than a binary implicit
assumption.

Candidate conceptual states:

- `known-permitted` — sufficient evidence exists for the requested operation in
  the declared context;
- `known-restricted` — the requested operation is known to be prohibited or
  outside the current permission boundary;
- `unknown` — the project lacks enough information to decide;
- `requires-review` — the operation may be possible but needs a human or
  specialist decision before execution.

These are product/architecture states, not legal conclusions themselves.

A route must not silently convert `unknown` into `known-permitted`.

## 4. Rights evidence sources

> Assertion status: `working-hypothesis`

Evidence can come from different origins and should retain provenance:

- user declaration of ownership/access/authorization;
- explicit license metadata;
- repository/package license;
- publisher/provider terms attached to the Source;
- API/feed/provider usage policy;
- institutional or project policy;
- public-domain/open-license metadata;
- specialist legal decision where required;
- explicit benchmark-fixture creation terms.

Conflicting evidence must remain visible. A permissive user declaration must not
silently override a known restrictive license/Provider condition.

## 5. Data sensitivity boundary

> Assertion status: `provisional-decision`

Rights and sensitivity are different axes.

P0 should be able to distinguish at least:

- `public-or-open` — material intended for public access under known terms;
- `private-corpus` — user/project-private material;
- `licensed-restricted` — material lawfully accessible but with non-public or
  redistribution restrictions;
- `sensitive-or-personal` — material declared/detected as containing personal,
  confidential or otherwise sensitive information;
- `secrets-risk` — source code/configuration/notebooks or documents that may
  contain credentials, tokens or secrets;
- `unknown` — sensitivity has not been established.

These labels are policy inputs. They do not prove legal status and they must not
be treated as a complete privacy classification system.

## 6. Conservative default policy

> Assertion status: `provisional-decision`

Until benchmark/provider evidence supports a more specific policy, the safest
P0 default should be:

1. **local reference/inventory is preferred** when full-content processing is
   unnecessary;
2. **local processing is preferred** for private/restricted/sensitive Sources
   when a viable local route exists;
3. **remote full-content processing is denied by default** unless:
   - Processing Authority explicitly includes it;
   - Processing Rights evidence permits the requested operation;
   - Provider data handling is known enough for the policy;
   - the Source sensitivity policy permits that Provider/data flow;
4. unknown rights or sensitivity trigger review/restricted routing rather than
   silent remote transmission;
5. Redistribution Rights are evaluated separately from processing;
6. Derived Artifacts inherit a conservative rights/sensitivity relationship to
   their Source until a more specific policy is recorded.

This is an architectural safety default, not a claim that every local operation
is lawful or every remote operation is unlawful.

## 7. Data-flow zones

> Assertion status: `provisional-decision`

### Zone Z0 — User-controlled source locations

Examples:

- local filesystem;
- mounted/removable storage;
- NAS or selected storage visible to Raiatea;
- physical holding metadata.

Raiatea may observe only within configured authority. Alfred Observation does
not enlarge the authority boundary.

### Zone Z1 — Raiatea local control plane

Conceptual responsibilities:

- Catalog/Logical Identity references;
- route decision inputs;
- rights/sensitivity state;
- Processing Recipe/Run intent;
- Provenance/Lineage metadata;
- policy decisions.

This zone should not need to copy full source bytes merely to know they exist.

### Zone Z2 — Raiatea local processing workspace

Temporary or persistent local processing area for:

- Original Artifact copy when policy requires/permits it;
- Raw Extraction;
- Normalized Representation;
- Intermediate;
- Derived Artifact;
- Provider working files.

Retention must be explicit by layer.

### Zone Z3 — Local Provider

A replaceable Provider running in the local trust environment.

Even a local Provider must receive only the data required for its declared
operation and must not silently execute active content.

### Zone Z4 — Remote Provider

A Provider receiving data outside the local environment.

Crossing Z2/Z1 -> Z4 is a material policy event. It requires explicit route
eligibility and provenance of what was sent, to which Provider/version, and for
which operation.

### Zone Z5 — External consumer / publication boundary

Examples:

- TheBitLab projection;
- exported/shared artifact;
- public publication;
- future federation.

This boundary requires separate Redistribution Rights and consumer policy. P0
processing permission is insufficient.

## 8. Layer-specific retention model

> Assertion status: `provisional-decision`

Retention must be considered separately for each layer.

| Layer | Why it may need retention | Conservative question before retention |
| --- | --- | --- |
| Source Reference | reproduce provenance without retaining bytes | Is the reference stable enough and lawful to retain? |
| Original Artifact | reproducibility/reprocessing | May Raiatea retain a copy, and is duplication necessary? |
| Raw Extraction | audit Provider output and transformations | Does it contain essentially the full protected/private content? |
| Normalized Representation | downstream search/processing | Does normalization preserve content whose retention is restricted? |
| Intermediate | reuse/caching | Is caching necessary, and what invalidates/deletes it? |
| Derived Artifact | user-requested result | What Source restrictions/sensitivity propagate to the derivative? |
| Provenance/Lineage | audit/reconstruction | Can provenance be kept if source bytes must be removed? |
| Logs/diagnostics | reliability/security | Do logs leak source text, secrets, paths or identifiers unnecessarily? |

No layer should inherit “retain forever” simply because storage is cheap.

## 9. Proposed Retention Policy classes

> Assertion status: `working-hypothesis`

The implementation may later use different names/representation. Conceptually it
needs policies equivalent to:

### Reference-only

- retain metadata/Source Reference/Provenance;
- do not retain full original content;
- temporary processing bytes deleted according to bounded lifecycle.

### Process-and-discard

- full content available only for a bounded Processing Run;
- Raw Extraction/Intermediate removed after outcome/recovery window;
- retain minimal Provenance/Warnings/metrics allowed by policy.

### Private retained corpus

- retain authorized Source/content layers locally;
- no remote Provider unless separately permitted;
- no redistribution by default.

### Reproducible benchmark fixture

- retention and sharing explicitly defined by fixture rights;
- gold/reference data separated from restricted source material where needed;
- provenance sufficient to reproduce the benchmark.

### Published/shareable derivative

- only after explicit Redistribution Rights/policy decision;
- publication never inferred from private processing.

## 10. Operation rights matrix

> Assertion status: `working-hypothesis`

The future policy model should be able to answer operations independently.

| Operation | Authority required | Rights/data questions |
| --- | --- | --- |
| discover/reference | observe/reference scope | Can metadata/reference be retained? |
| read/hash locally | read Processing Authority | Is local content processing permitted? |
| preserve original copy | copy/retention authority | May an additional retained copy exist? |
| parse/OCR locally | processing authority | Is transformation/extraction allowed? |
| send to remote Provider | explicit remote-processing authority | Do rights + sensitivity + Provider policy permit transmission? |
| retain Raw Extraction | retention authority | Does raw output reproduce protected/private content? |
| normalize/index | processing/index authority | May searchable content be retained? |
| create derivative | transformation authority | What source restrictions propagate? |
| share/export externally | export/publish authority | Are Redistribution Rights established? |
| delete/expire retained layer | deletion authority/policy | What Provenance/history must remain? |

No row is automatically enabled by another.

## 11. Local versus remote Provider decision

> Assertion status: `provisional-decision`

A Provider route should be eligible only after evaluating:

```text
requested operation
+ Source family/traits
+ Processing Authority
+ Processing Rights evidence
+ sensitivity policy
+ Retention Policy
+ Provider data handling/terms
+ required fidelity/coordinates
+ benchmark evidence
-> eligible routes
```

A remote route should record at least conceptually:

- Provider identity/version/model where relevant;
- operation;
- data classes sent;
- whether full source, excerpts, images, metadata or normalized content were
  transmitted;
- policy/rights decision reference;
- timestamp;
- returned result and Warnings;
- known Provider retention/logging/training setting or unresolved uncertainty.

The exact technical record belongs to later P0 contract work.

## 12. Provider data-handling unknowns

> Assertion status: `accepted-decision` for visibility

If Raiatea cannot determine relevant Provider behavior, that uncertainty must be
visible rather than converted into a safe assumption.

Examples:

- whether input is retained;
- retention duration;
- whether input/output can be used for training/improvement;
- region/data residency;
- subprocessors;
- logging/debug capture;
- deletion controls;
- account/project isolation.

The later technology survey must capture these attributes from current
authoritative Provider documentation when a Provider is actually evaluated.

## 13. Rights-safe benchmark corpus requirements

> Assertion status: `provisional-decision`

A benchmark corpus should contain only fixtures for which the project can
record a defensible processing and retention basis.

Minimum record for each fixture family should include:

- origin/provenance;
- source class/traits;
- Processing Rights evidence or project-created fixture status;
- Redistribution Rights if fixture/source bytes or gold data will be published;
- allowed retention;
- allowed transformation;
- whether remote Provider evaluation is permitted;
- whether excerpts/derived gold/reference data may be published;
- required attribution/license notice where applicable;
- deletion/withdrawal behavior where relevant.

### Preferred fixture strategy

Where practical, prefer:

- project-created synthetic or original fixtures;
- openly licensed/public-domain fixtures with verified terms;
- minimal rights-safe extracts whose use is explicitly permitted;
- separately generated gold/reference data.

Do not make the benchmark dependent on distributing a private or proprietary
corpus merely because the maintainer can access it privately.

## 14. Private Corpus boundary

> Assertion status: `accepted-decision` for privacy principle;
> concrete enforcement remains future work

Private Corpus material:

- remains private by default;
- is not uploaded remotely merely because a remote Provider performs better;
- is not exposed in benchmark artifacts/logs by default;
- is not projected into TheBitLab or future shared spaces without separate
  rights and user intent;
- may retain private translations/derivatives when authorized without making
  them public artifacts;
- should be exportable/deletable under future retention/data-management
  contracts.

## 15. Secrets and sensitive-content handling

> Assertion status: `provisional-decision`

P0 must assume that heterogeneous Sources can contain material the user did not
intend to send externally, including:

- credentials/API keys;
- private repository configuration;
- personal identifiers;
- confidential business/school documents;
- hidden comments/revisions/metadata;
- embedded files;
- document properties not visible in the rendered view.

Before remote processing becomes a supported route, Elaboration should decide
whether the system needs:

- user declaration only;
- automated sensitive-data detection/redaction;
- Provider-specific allow/deny policy;
- class-specific local-only defaults;
- explicit preview of transmitted material.

This issue does not select the mechanism.

## 16. Deletion and provenance

> Assertion status: `accepted-decision` for preservation principle;
> exact data lifecycle future work

Deletion/expiry of source bytes must not automatically erase all historical
Provenance/Lineage.

The system needs to distinguish:

- content no longer retained;
- Location currently unavailable;
- Source known deleted;
- metadata/reference retained;
- derivative retained or removed;
- legal/policy requirement to propagate deletion further.

If policy requires removal of even provenance metadata, that exception must be
explicit rather than silently conflated with ordinary file deletion.

## 17. Relationship to Alfred

> Assertion status: `accepted-decision`

Alfred reports filesystem Observation within its configured scope. It does not
provide Processing Authority or Processing Rights.

Therefore:

```text
Alfred: "a file appeared / moved / changed"
       !=
Raiatea: "I may read/process/upload/move/publish this file"
```

The rights/authority decision remains in Raiatea policy.

## 18. Relationship to Organization Policy

> Assertion status: `accepted-decision`

This document does not authorize automatic move/rename.

Managed organization is a separate feature gate. Even if a Source is fully
processable, Raiatea must not infer permission to reorganize its Stored Instance
unless the relevant Authority Scope explicitly permits it and the organization
safety gate has been satisfied.

## 19. Evidence and gates advanced

> Assertion status: `working-hypothesis`

This boundary primarily advances:

- **G-02** by defining required rights/data-flow evidence;
- **G-07** by separating UI/user authority from backend/filesystem/provider
  authority;
- inputs to **G-04** by defining what remote/local route attributes need
  comparison;
- inputs to **G-05** by defining data-flow and retention provenance needs;
- **R-09** rights/privacy;
- **R-22** local-web/filesystem authority;
- **R-19** Provider lock-in/data-policy visibility.

It does not satisfy those gates without implementation/benchmark evidence.

## 20. Open questions requiring later evidence or specialist review

- Which processing operations require explicit per-Source confirmation versus a
  reusable policy?
- Which rights metadata standards are useful without creating false certainty?
- How should license/terms changes affect previously acquired Sources?
- Which Provider attributes must be machine-readable versus documented in the
  survey?
- Which Source classes should be local-only by default?
- What minimum metadata can remain after a retention/deletion request?
- How should remote Provider deletion guarantees be represented?
- Which personal/sensitive-data categories require specialist privacy review?
- What is the minimum rights record for a reproducible public benchmark?
- How should private translated derivatives inherit source restrictions?

## 21. Out of scope

This document does not:

- give legal advice;
- declare copyrighted/licensed material universally processable or forbidden;
- select Providers;
- define authentication/encryption implementation;
- define a full privacy compliance program;
- define final data-retention durations;
- authorize remote processing by default;
- authorize redistribution;
- authorize automatic file organization;
- promote the candidate first slice.

## 22. Exit criteria for this artifact

Before acceptance, review must verify that:

- Authority, Processing Rights, Redistribution Rights, Provider policy and
  Retention are distinct;
- local versus remote Provider flow is explicit;
- unknown rights/sensitivity cannot silently become permitted;
- retention is layer-specific;
- Private Corpus is private by default;
- benchmark corpus requirements do not require publishing restricted sources;
- Alfred Observation does not grant processing/mutation authority;
- no legal conclusion or Provider choice is fabricated;
- the model supplies actionable inputs to G-02/G-07 without pretending those
  gates are already passed.
