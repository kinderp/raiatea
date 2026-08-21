# P0 Benchmark Rights Manifest

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#127](https://github.com/kinderp/raiatea/issues/127)
>
> P0 roadmap: [#106](https://github.com/kinderp/raiatea/issues/106)
>
> Fixture plan: [`benchmark-fixture-plan.md`](benchmark-fixture-plan.md)
>
> Rights boundary: [`rights-data-boundary.md`](rights-data-boundary.md)

## 1. Purpose

This manifest defines the evidence that must accompany benchmark fixtures and
gold data before they can be processed, retained, shared or used in CI.

It is an architectural evidence contract, not legal advice and not a declaration
that possession/access automatically creates Processing Rights or Redistribution
Rights.

The primary rule is:

> **A fixture's benchmark usefulness never overrides its rights/data boundary.**

## 2. Rights dimensions remain separate

> Assertion status: `accepted-decision`, inherited from E-01

For every fixture, keep these questions independent:

```text
Can Raiatea access/process it?          Processing Authority
Is the requested processing allowed?   Processing Rights
Can the fixture/gold be published?      Redistribution Rights
Can it be sent to a remote Provider?    Route/data-policy eligibility
How long/where may layers be retained?  Retention Policy
```

A `yes` to one does not imply `yes` to the others.

## 3. Manifest record requirements

> Assertion status: `provisional-decision`

Every concrete fixture version should have a record with at least:

- fixture ID and version;
- origin category;
- creator/source provenance;
- creation/acquisition date when relevant;
- source/generator reference;
- license or other rights basis actually relied on;
- Processing Authority state;
- Processing Rights evidence/state;
- Redistribution Rights evidence/state;
- allowed public-repository exposure;
- allowed CI/artifact exposure;
- local processing eligibility;
- external remote Provider eligibility;
- Retention Policy class for Original Artifact;
- Retention Policy class for Raw Extraction / Normalized Representation / gold;
- attribution/NOTICE requirements;
- third-party fonts/images/code/assets and their separate rights basis;
- withdrawal/deletion/replacement notes;
- reviewer/evidence reference when human or specialist review is required.

This list is conceptual and does not freeze a public schema.

## 4. Origin categories

> Assertion status: `provisional-decision`

Suggested evidence categories:

### `project-created`

Source and embedded material are created specifically for Raiatea by contributors
whose contribution terms allow the intended benchmark distribution.

Preferred default for E-03.

### `generated-from-project-assets`

Fixture is deterministically generated from project-created/distributable source
templates and assets. The manifest must include generator/version provenance.

### `public-domain`

Source is supported by evidence that the relevant material is public domain in
the context relied on. Do not infer this merely from age or public availability.

### `open-license`

Source is under a verified license compatible with intended processing,
retention and redistribution. Required attribution/notice must be recorded.

### `private-non-distributable`

User/project can process the source privately under the applicable policy but the
fixture bytes and/or gold derived from them are not approved for public
redistribution. This category cannot be a dependency of the public baseline.

### `restricted`

Known restrictions prevent one or more requested benchmark operations. The
record must say which operation is restricted rather than treating the fixture
as globally unusable.

### `unknown` / `requires-review`

Insufficient evidence. Public distribution and external remote processing fail
closed until resolved.

## 5. Admission rules for the public benchmark baseline

> Assertion status: `provisional-decision`

A fixture may enter the repository/public E-03 baseline only when:

1. origin/provenance is recorded;
2. Processing Rights are sufficiently established for the benchmark operations;
3. Redistribution Rights cover the exact material that will be published;
4. third-party embedded assets have compatible evidence;
5. attribution/notice obligations can be fulfilled;
6. no secrets/personal/confidential data are intentionally embedded;
7. retention is compatible with repository/CI use;
8. security fixture contents are inert/minimal and safe to distribute;
9. a future Provider benchmark can use it locally without inventing new rights.

If any required field is `unknown`, the fixture remains outside the public
baseline.

## 6. Remote Provider eligibility

> Assertion status: `accepted-decision` for conservative boundary

E-03 does not authorize externally hosted Provider routes.

Even for a fully redistributable fixture:

```text
public fixture
    != automatically eligible for every remote Provider
```

External remote eligibility also requires the Provider-policy evidence and E-01
route decision that E-02 explicitly deferred.

E-03 may mark a public fixture as **potentially remote-evaluable** only to state
that fixture rights/sensitivity would not themselves block such a future route.
It does not override missing Provider data-policy evidence.

## 7. Private exploratory extension

> Assertion status: `accepted-decision` for boundary

Private/licensed material may be useful for validating whether the public
fixtures represent real-world difficulty, but it must remain separate:

- never required to reproduce the public benchmark;
- never committed to the repository by default;
- never uploaded to CI/public artifact storage by default;
- never sent to external Providers without explicit route eligibility;
- results must avoid publishing recoverable protected source content;
- observations may motivate a new project-created/public fixture that reproduces
  the relevant phenomenon safely.

The manifest may record a private fixture reference without retaining its bytes
if policy allows and that is enough for provenance.

## 8. Gold-data rights

> Assertion status: `provisional-decision`

Gold/reference data has its own rights surface. Hand annotation does not
necessarily remove restrictions from the source it reproduces.

Gold records should distinguish:

- abstract structural labels/relations that do not reproduce source expression;
- short source-linked expected values needed for exact comparison;
- larger textual reproductions;
- images/crops/regions from source material;
- derived tables/formulas/code excerpts;
- synthetic/project-authored reference values.

For public fixtures, design gold so it is independently distributable under the
recorded fixture/annotation terms.

For private fixtures, do not publish gold that reconstructs substantial protected
content merely because the original bytes are omitted.

## 9. Generated fixtures and transitive assets

> Assertion status: `provisional-decision`

A project-created template can still become non-distributable if the generator
embeds restricted third-party material.

Check separately:

- fonts;
- icons/images;
- code snippets;
- equations/data examples from third parties;
- styles/templates;
- test documents copied from Provider repos;
- generated model output if its terms affect redistribution.

Prefer project-created simple vector/raster assets and system/open fonts whose
redistribution basis is known.

## 10. CI and artifact boundary

> Assertion status: `accepted-decision` for safety intent; implementation future

Public CI should consume only fixtures explicitly marked CI-safe.

CI/logging rules should prevent:

- dumping full private Source text on failure;
- attaching proprietary documents to workflow artifacts;
- exposing absolute private paths unnecessarily;
- embedding API tokens/secrets in synthetic fixtures;
- publishing Provider request/response payloads from private runs.

A fixture may be locally processable while not CI-eligible.

## 11. Planned public fixture-family rights basis

> Assertion status: `working-hypothesis`

No concrete fixture is granted a license by this table. It records the intended
creation strategy to be verified when files/generators exist.

| Fixture family | Intended origin basis | Intended public redistribution | External remote status in E-03 |
| --- | --- | --- | --- |
| B-01 atomic PDFs | project-created/generated | yes, after actual license/NOTICE record | not authorized by E-03 |
| B-01 composite PDF | project-created/generated | yes, after actual license/NOTICE record | not authorized by E-03 |
| B-01 negative PDFs | project-created minimal/inert | yes if safe and rights-complete | not authorized by E-03 |
| B-02 atomic EPUBs | project-created/generated | yes, after actual license/NOTICE record | not authorized by E-03 |
| B-02 composite EPUB | project-created/generated | yes, after actual license/NOTICE record | not authorized by E-03 |
| B-02 active/path negative EPUBs | project-created minimal/inert | yes if safe and rights-complete | not authorized by E-03 |
| private exploratory extension | user/project licensed/private | no by default | denied unless separately authorized |

## 12. Rights evidence quality

> Assertion status: `provisional-decision`

A manifest entry should distinguish:

- explicit license/contract/project-creation evidence;
- contributor declaration;
- external authoritative metadata;
- inferred or incomplete evidence;
- specialist-review conclusion.

Do not convert weak inference into `known-permitted` merely because doing so
would make a benchmark easier.

## 13. Change and withdrawal handling

> Assertion status: `working-hypothesis`

If fixture rights evidence changes or an asset must be withdrawn:

1. mark the affected fixture version unavailable/restricted;
2. preserve non-sensitive provenance that explains why prior benchmark runs used
   it when policy permits;
3. stop public/CI distribution where required;
4. create a replacement fixture version/ID when content materially changes;
5. do not silently compare new results against old gold as if the fixture were
   unchanged.

E-04 result manifests should therefore reference immutable fixture versions, not
only human-readable names.

## 14. Manifest review checklist

Before a concrete fixture enters the distributable baseline, verify:

- creator/origin evidence;
- exact license/rights basis;
- third-party asset inventory;
- Processing Rights;
- Redistribution Rights;
- Retention Policy;
- public repository permission;
- CI permission;
- external remote eligibility explicitly separate;
- attribution/notice;
- no secrets/PII/private identifiers;
- fixture/gold fingerprints and versions.

## 15. Out of scope

This artifact does not:

- give legal advice;
- authorize copyrighted/licensed private books for public distribution;
- authorize any remote Provider;
- choose a benchmark Provider;
- define production user rights UX;
- define a universal license ontology;
- freeze the future P0 public schema;
- mark G-02 satisfied solely because this manifest format exists.

## 16. Exit criteria

Before acceptance, review must verify:

- Processing Authority/Rights/Redistribution/retention/remote eligibility remain
  separate;
- unknown evidence fails closed for public/remote use;
- gold-data redistribution is considered independently;
- generated fixtures account for transitive assets;
- private extensions cannot become public benchmark dependencies;
- CI/public exposure is explicit;
- planned fixture families have a rights-safe creation path without pretending
  that not-yet-created files are already licensed.