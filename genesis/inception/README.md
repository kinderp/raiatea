# Canonical Inception index

> Document maturity: `Accepted`
>
> Assertion status: `accepted-decision`
>
> Version: 2.0.0
>
> Last reviewed: 21 August 2026
>
> Accepted through: [PR #103](https://github.com/kinderp/raiatea/pull/103), updated through [PR #118](https://github.com/kinderp/raiatea/pull/118)
>
> Parent issue: [#98](https://github.com/kinderp/raiatea/issues/98)

## 1. Purpose

This directory contains the concise, canonical artifacts used to orient
Raiatea's Inception. It does not replace the exploratory notes in `genesis/`.
Instead, it derives current guidance from them while preserving links to the
reasoning, alternatives and uncertainties that produced each conclusion.

A canonical artifact must make it possible to distinguish:

- what Raiatea currently does;
- what has been deliberately decided;
- what is still a hypothesis;
- what is planned but absent;
- what has been deferred;
- what is retained only as history;
- what has been rejected and why.

## 2. Authority and conflict resolution

The authority order remains the one defined by `AGENTS.md`:

1. the maintainer's current explicit request;
2. operational rules;
3. commit, PR and review rules;
4. stable ADRs and component contracts;
5. the current milestone roadmap;
6. canonical Inception artifacts;
7. exploratory notes and historical ideas.

An Inception artifact can orient product and architecture work, but it cannot
silently override an implemented stable contract or an accepted ADR. A conflict
must be recorded and resolved explicitly.

## 3. Document map

The audit is numbered separately because it observes the state preceding the
canonical set. The final paths of the intended artifacts preserve the names
announced by `genesis/README.md`.

| Artifact | Availability | Document maturity | Assertion status | Purpose | Primary sources |
| --- | --- | --- | --- | --- | --- |
| [`00-genesis-audit-and-traceability.md`](00-genesis-audit-and-traceability.md) | Present | `Accepted` | `Mixed` | Map founding ideas, gaps and implementation state | Conversation, `genesis/00`-`20`, repository and GitHub state |
| [`00-why-raiatea.md`](00-why-raiatea.md) | Present | `Accepted` | `mixed` | Define the problem and reason to begin | `genesis/00`, `08`, `10`, `18` |
| [`01-manifesto.md`](01-manifesto.md) | Present | `Accepted` | `mixed` | State human and philosophical commitments | `genesis/00`, `03`, `09`, `16`-`18`; maintainer approval 21 August 2026 |
| [`02-vision.md`](02-vision.md) | Present | `Accepted` | `mixed` | Define users, value, product hierarchy, scope and measurable direction | `genesis/08`, `10`, `18`-`20`; maintainer approval 21 August 2026 |
| [`03-system-context.md`](03-system-context.md) | Present | `Accepted` | `mixed` | Define actors, system boundaries, ownership and external systems | Vision, `genesis/04`, COMPASS, #111, pinned ecosystem evidence |
| [`04-product-map.md`](04-product-map.md) | Present | `Accepted` | `mixed` | Separate document foundation, research/learning products, experiences and shared capabilities | Vision, System Context, #111 |
| [`05-use-case-model.md`](05-use-case-model.md) | Present | `Accepted` | `mixed` | Capture primary actors, significant scenarios, alternatives/failures and invariants | System Context, Product Map, #113 |
| [`06-risk-list.md`](06-risk-list.md) | Present | `Accepted` | `mixed` | Prioritize failure modes and define evidence, promotion and invalidation gates | Why, Manifesto, Vision, Use Case Model, #115; complete register in [`06-risk-register.md`](06-risk-register.md) |
| [`07-glossary.md`](07-glossary.md) | Present | `Accepted` | `mixed` | Establish the initial ubiquitous language without freezing schema/API | Accepted Inception artifacts 01-06, #117 |
| [`08-inception-review.md`](08-inception-review.md) | Present | `Draft` | `mixed` | Decide whether the reviewed evidence supports leaving Genesis for bounded P0 Elaboration | All preceding artifacts, #106 and current pilot state, #121 |

Supporting terminology reconciliation for the Glossary is documented in
[`07-terminology-compatibility.md`](07-terminology-compatibility.md). It is an
Accepted supporting artifact on `main` and maps accepted pre-Glossary shorthand
to the preferred vocabulary without rewriting historical canonical documents
or implying schema migrations.

`planned` in this table qualifies the creation of each absent artifact. It does
not assign document maturity to a file that does not exist and does not approve
the future artifact's conclusions in advance.

## 4. Two separate status dimensions

Document maturity and assertion status answer different questions and must not
be collapsed into one `status` field.

### 4.1 Document maturity

Document maturity describes the editorial lifecycle of a file.

| Maturity | Meaning | Entry criterion | Exit criterion |
| --- | --- | --- | --- |
| `Draft` | Work is incomplete and can change substantially | Issue and scope exist | Author requests a complete review |
| `In review` | Scope is complete enough for finding-based review | Draft PR or equivalent review surface exists | Findings resolved and required clean rounds complete |
| `Accepted` | Document is the intended canonical version | Maintainer accepts material decisions and the proposed text completes required review and CI; merge makes it authoritative on `main` | A replacement is accepted or the document is withdrawn |
| `Superseded` | A newer canonical artifact replaces the document | Replacement links back to this file | Normally terminal; history is preserved |
| `Archived` | File remains for provenance but no longer guides work | Maintainer records why it is inactive | Normally terminal; reactivation requires a new review |

An `Accepted` document on an unmerged review branch records the intended
canonical state after its acceptance criteria have been met in that PR. Until
that PR is merged, `main` remains the authoritative repository state.
Acceptance applies to the document as an accurate record; it does not
automatically accept every hypothesis or future capability mentioned inside it.

### 4.2 Assertion status

Assertion status describes the operational weight of a statement, section or
table row.

| Status | Meaning | Evidence or authority required |
| --- | --- | --- |
| `principle` | Durable value or safety constraint that guides choices | Explicit maintainer acceptance and consistency with operational rules |
| `current-contract` | Behavior or data contract that exists now | Merged implementation or documentation, tests where applicable, and current traceability |
| `accepted-decision` | Deliberate non-transient product, editorial or architectural choice | Recorded rationale, scope, alternatives and maintainer acceptance; ADR when technical and durable |
| `provisional-decision` | Reversible choice used to make progress while evidence is incomplete | Owner, review date or invalidation condition |
| `working-hypothesis` | Testable statement whose truth or value is not established | Falsifiable criterion or planned observation |
| `planned` | Approved deliverable or behavior that does not exist yet | Linked milestone or issue and explicit out-of-scope boundary |
| `deferred-research` | Relevant idea intentionally excluded from the current roadmap | Reason for deferral and trigger for reconsideration |
| `historical-note` | Earlier reasoning retained for provenance | Link to the decision or artifact that replaced it when one exists |
| `rejected` | Evaluated option that must not be treated as current direction | Rationale, date and authority that rejected it |

`accepted-decision` is intentionally distinct from `current-contract`. A
decision can be accepted before it has a software representation, while a
contract describes behavior or structure that is already authoritative now.

## 5. Applying assertion status

A homogeneous artifact may declare one assertion status near its title. A
mixed artifact must declare the aggregate marker `mixed` and label
consequential sections or tables individually. `mixed` is not an additional
assertion status and is not a substitute for section-level labels.

Status labels are required when a reader could otherwise mistake a future idea
for current capability. They are optional for ordinary explanatory prose whose
status is unambiguous from its containing section.

Preferred form:

```markdown
> Document maturity: Draft
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: YYYY-MM-DD
>
> Sources: `genesis/04`, `genesis/10`, issue #...
```

For a consequential section:

```markdown
### Candidate continuous-ingestion capability

> Assertion status: `deferred-research`
```

Status is not confidence. Confidence describes uncertainty in evidence or an
inference; assertion status describes how the project may use a statement.

## 6. Transition rules

- `Draft` becomes `In review` only when scope, sources and open questions are
  explicit.
- `In review` becomes proposed `Accepted` text only after the maintainer has
  accepted the material decisions and required findings, review rounds and CI
  are complete; merge then makes that accepted text authoritative on `main`.
- `planned` becomes `current-contract` only for the exact behavior or
  deliverable whose Definition of Done has been verified and merged. Creating
  or accepting a planned document changes that file's maturity; it does not
  promote every assertion inside the document to `current-contract`.
- `provisional-decision` becomes `accepted-decision` only when its rationale,
  alternatives and authority are recorded.
- `working-hypothesis` never becomes a fact merely because work was completed;
  it must be supported, narrowed, rejected or retained with updated evidence.
- `deferred-research` returns to active consideration only through a roadmap
  decision, normally with a new issue.
- `rejected`, `historical-note`, `Superseded` and `Archived` content is not
  deleted merely to simplify the current narrative.

Substantive status changes require normal issue, PR and review traceability.
Purely editorial corrections do not change assertion status.

## 7. Provenance requirements

Every canonical artifact must include or link to:

- the exploratory Genesis notes from which it derives;
- relevant issues, PRs, ADRs, contracts and pilot evidence;
- the observation date for repository or external-state claims;
- unresolved questions and decisions requiring the maintainer;
- superseded or competing formulations when omission would distort history.

External factual, legal, cultural, scientific or policy-sensitive claims require
current authoritative sources before public use. A statement from the founding
conversation can establish intent, not external truth.

## 8. Current capability language

Canonical documents use the following verbs deliberately:

- **is / does / supports** only for `current-contract` behavior;
- **has decided / requires** for `accepted-decision` or `principle` statements;
- **currently uses** for a `provisional-decision` already applied;
- **plans / will attempt** for `planned` work;
- **hypothesizes / intends to test** for `working-hypothesis`;
- **may explore** for `deferred-research`.

Words such as *understands*, *learns*, *knows*, *trusts*, *predicts*,
*competence* and *mastery* require an explicit operational definition. Simple
local interactions remain observed evidence and must not be promoted to a
stronger cognitive claim.

## 9. Review checklist for canonical artifacts

Before acceptance, reviewers must verify:

- purpose and target reader are explicit;
- current, planned and deferred capability are distinguishable;
- material assertions have appropriate status;
- sources and observation dates are present;
- contradictions with contracts or ADRs are surfaced;
- terminology matches the current glossary or is marked provisional;
- open decisions have an owner or next review point;
- no placeholder text creates the appearance of progress;
- finding log, clean review rounds and required CI satisfy operational rules.

## 10. Current next step

`00-why-raiatea.md` through `07-glossary.md` are Accepted canonical artifacts on
`main`. Issue [#121](https://github.com/kinderp/raiatea/issues/121) and draft PR
[#122](https://github.com/kinderp/raiatea/pull/122) contain the final sequential
Inception step: `08-inception-review.md`. The review proposes a bounded GO to
Elaboration for P0 risk reduction while keeping the first slice a working
hypothesis, carrying G-01..G-07 forward and leaving the pedagogical pilot as an
independent evidence stream. Until #122 is accepted and merged, Project Genesis
remains the authoritative current phase.
