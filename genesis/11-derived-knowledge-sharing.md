# Derived Knowledge Sharing

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Define how knowledge derived from privately owned books, documents, videos, and other lawful private sources can improve the shared Raiatea network without redistributing protected source content.

---

## 1. Core principle

A private source may remain private while the new knowledge produced through analysis, comparison, verification, experimentation, and original explanation should be eligible for sharing.

Raiatea should therefore separate:

- source possession;
- private processing;
- derived knowledge;
- public redistribution.

> Private sources can produce public understanding, but the shared result must not reproduce the protected source in substance or form.

---

## 2. Default expectation

When a user processes a lawfully acquired private work, Raiatea should generate two outputs:

### Private output

May include:

- original file;
- extracted full text;
- OCR;
- full translation;
- close annotations;
- page-by-page alignment;
- private notes;
- private summaries;
- locally generated embeddings and indexes.

This remains within the user's authorised private corpus.

### Shareable derived output

May include, after rights and privacy checks:

- bibliographic reference;
- concepts;
- claims expressed independently;
- timelines;
- process models;
- relationships between ideas;
- source coordinates;
- short necessary quotations;
- original explanations;
- comparisons with other sources;
- corrections;
- contradictions;
- experiments;
- verified results;
- reading prerequisites;
- topic classifications;
- uncertainty and confidence;
- reusable knowledge bundles.

The shared layer should enrich future expeditions without exposing the private copy.

---

## 3. Sharing should be expected, but not blind

Raiatea's network grows only if private expeditions can contribute back. For that reason, the product may treat contribution of eligible derived knowledge as the normal path.

However, automatic publication must stop when there is uncertainty about:

- copyright;
- contractual restrictions;
- confidentiality;
- personal data;
- trade secrets;
- security;
- sensitive research;
- attribution;
- whether the output is too close to the original expression.

A user should see a contribution preview explaining:

```text
What will remain private
What will be shared
Which source supports it
How it was transformed
Why it is considered independently expressed
Which quotations are included
Which restrictions apply
```

The user confirms publication unless a future institution-specific policy explicitly governs the corpus.

---

## 4. Knowledge extraction is not enough

Simple mechanical transformations are not automatically suitable for public sharing.

Examples that normally remain private:

- full translation of a protected book;
- chapter-by-chapter paraphrase preserving the same structure;
- reconstruction of all examples and figures;
- an output that substitutes economically for the original work;
- extensive quotations;
- summaries so detailed that they reproduce the expressive content of the source.

Examples more suitable for sharing:

- a new causal model constructed from several sources;
- a comparison between competing explanations;
- a concept definition written independently;
- a timeline combining books, papers, code, and events;
- an experiment reproducing or challenging a claim;
- a map of prerequisites;
- a correction supported by a page reference;
- a novel tutorial or explanation that does not mirror the source's structure;
- a knowledge bundle containing facts, claims, evidence links, provenance, and uncertainty.

The distinction is not merely between copied and rewritten text. It is between redistributing an author's protected expression and contributing independently constructed knowledge.

---

## 5. Provenance without publication of the source

A shared knowledge bundle should preserve enough provenance to allow verification by another authorised reader without publishing the full source.

Example:

```yaml
source:
  title: "Example Book"
  author: "Example Author"
  edition: "2nd edition"
  identifier: "ISBN or publisher ID"
  location:
    page: 147
    section: "4.2"
  access_scope: private-source

contribution:
  type: causal_model
  statement: "Independent formulation of the derived knowledge"
  transformation: synthesis_across_sources
  confidence: medium
  reviewer_status: pending
  public_quotes: []
```

Other users who lawfully possess the same work may independently verify the contribution against the cited location.

---

## 6. Convergent private verification

Raiatea can gain confidence without sharing full private text.

If several users independently process the same edition, their nodes may publish privacy-preserving attestations that:

- the cited page exists;
- a claim is supported, contradicted, or ambiguous;
- the quoted excerpt matches;
- a translation segment is accurate;
- a derived relation is plausible.

The network should publish the verification result, not the users' private copy.

Possible status:

```text
single private attestation
multiple independent attestations
community verified
expert verified
disputed
edition dependent
unable to verify
```

This must not reveal who owns a politically, medically, or personally sensitive work unless the user chooses disclosure.

---

## 7. Attribution and contribution ownership

The source author retains attribution for the underlying work.

The contributor receives attribution for the original derived contribution, such as:

- synthesis;
- model;
- explanation;
- timeline;
- experiment;
- correction;
- translation review;
- relation proposal.

Raiatea should record both lineages:

```text
Underlying sources
        ↓
Derived contribution
        ↓
Reviews and revisions
        ↓
Later models and expeditions
```

No contribution should imply that the original author endorsed the derived interpretation.

---

## 8. Contribution licences

Public derived contributions should use a clear licence compatible with the shared commons.

The contribution interface must distinguish:

- source licence;
- user's rights over private material;
- licence granted for the new derived contribution;
- restrictions on quotations and embedded media.

A knowledge bundle may contain components with different policies. The most restrictive component must not silently contaminate the whole public graph or, conversely, be stripped of its restrictions.

---

## 9. Architecture implications

Raiatea needs a transformation and publication boundary:

```text
Private Corpus
→ Analysis Workspace
→ Candidate Derived Knowledge
→ Rights / Privacy / Similarity Review
→ Contribution Preview
→ User or institutional approval
→ Public Knowledge Bundle
→ Community verification
```

Candidate derived knowledge should be checked for:

- textual similarity to the source;
- structural similarity;
- quotation volume;
- source substitution risk;
- private or confidential data;
- missing attribution;
- unsupported claims;
- incompatible licences.

Automated checks support the decision but do not replace legal and human judgment in difficult cases.

---

## 10. Product behaviour

The user should not have to manually rewrite every useful discovery for the community.

Raiatea should propose an independently expressed contribution such as:

```text
Your private expedition produced three potentially shareable contributions:

1. A prerequisite relationship between concepts A and B.
2. A timeline correction supported by page 147 and two papers.
3. An original explanation comparing methods X and Y.

The original text, full translation, annotations, and private notes will not be shared.
```

The user can:

- approve all;
- inspect and edit;
- approve selected contributions;
- keep everything private;
- postpone review.

For explicitly public or institutionally funded projects, a policy may require eligible derived contributions to be returned to the commons, provided participants know this before processing begins.

---

## 11. Constitutional interpretation

The statement "private knowledge belongs to the user" protects the private corpus and personal learning state.

It does not imply that all independently constructed knowledge must remain isolated.

The desired equilibrium is:

> The user's private library remains private; the understanding newly built from it should be easy and normally encouraged to join the commons when it can be shared lawfully and without reproducing the source.

---

## 12. Open questions

- Should contribution be opt-in, opt-out, or policy-dependent?
- How is source-substitution risk measured?
- Can similarity checks operate locally so protected text never leaves the device?
- How can nodes verify page-level claims without revealing ownership or identity?
- Which licences best fit structured knowledge bundles?
- How are incompatible interpretations from the same source represented?
- When does a detailed synthesis become too close to a protected work?
- How should revenue from commercial use of community-derived bundles be returned to the commons?
- Can publishers offer machine-readable permissions that enable richer sharing?

---

## 13. Provisional decision

Raiatea will treat lawfully shareable derived knowledge as a contribution candidate by default.

Original files, full extracted text, complete translations, close paraphrases, private annotations, and sensitive corpus metadata remain private unless separately authorised.

> The network should inherit the understanding created during a private expedition, not the private library from which that understanding emerged.
