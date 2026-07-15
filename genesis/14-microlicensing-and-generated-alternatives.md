# Microlicensing and Generated Learning Alternatives

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Define how Raiatea may offer licensed access to only the portions of a source needed for an expedition, and how it may produce an independently authored alternative when licensed access is unavailable.

---

## 1. Core opportunity

Users often do not need an entire book, course, journal issue, video series, or subscription.

They may need:

- one chapter;
- one section;
- a small set of pages;
- a specific exercise set;
- a ten-minute video segment;
- one lecture;
- one article;
- one dataset;
- a temporary access window;
- a bundle assembled from several sources.

Raiatea can create value by identifying the smallest lawful source unit that satisfies a specific knowledge need.

> The unit of purchase should follow the learning need, not necessarily the commercial packaging of the source.

---

## 2. Two distinct offers

Raiatea may present two clearly separated options.

### Option A — Official licensed source fragment

The user purchases or accesses the original material through an agreement with the publisher, author, platform, library, or rights-management organisation.

Possible products:

- chapter licence;
- paragraph or section licence;
- time-limited reading access;
- selected video segment;
- article-level access;
- learning bundle assembled from several official sources;
- institutional or library loan;
- credit toward the full work if later purchased.

The original author and publisher are compensated, and Raiatea may receive a disclosed service or affiliate fee.

### Option B — Independent Raiatea learning artefact

Raiatea creates a new learning resource designed around the user's identified need.

It may include:

- an independently structured explanation;
- diagrams created for the new explanation;
- examples and exercises created specifically for the learner;
- comparisons across multiple lawful sources;
- public-domain and open-access references;
- simulations and code;
- prerequisite remediation;
- a personalised sequence;
- citations to private sources without reproducing them;
- links to official sources for deeper reading.

This is not a substitute copy, translation, abridgement, or chapter-by-chapter paraphrase of a protected work. It is a new educational artefact built from facts, ideas, methods, multiple sources, and original authorship.

---

## 3. The user choice

A recommendation may be presented as:

```text
You need to understand GPU memory hierarchy before continuing.

Official source option
- Chapter 5 of Book A
- estimated time: 70 minutes
- price: €X
- strengths: authoritative diagrams and exercises
- limitations: broader than your immediate need

Raiatea learning artefact
- personalised module created from open sources, shared knowledge, and new examples
- estimated time: 35 minutes
- price: €Y or included in subscription
- strengths: tailored to your current route and prior knowledge
- limitations: not the original author's complete treatment

Open alternative
- public lecture B and paper C
- price: free
- estimated time: 110 minutes
```

The user should be able to compare authority, depth, cost, time, completeness, and fit.

---

## 4. Why publishers may participate

Publishers may initially resist fragment-level sales because they fear cannibalisation, technical complexity, and loss of control.

Raiatea can offer them benefits:

- qualified demand at the exact moment a learner needs the content;
- discovery of older or specialised titles;
- conversion from fragments to full-book purchases;
- analytics about learning needs without exposing private user data;
- royalties from material that might otherwise not be purchased;
- links from generated modules to authoritative treatments;
- bundled access for universities and organisations;
- machine-readable content maps;
- errata and update channels;
- verified attribution and provenance.

A useful commercial model could credit the cost of purchased fragments toward the full book.

---

## 5. Microlicensing architecture

Raiatea would require a rights and commerce layer capable of representing:

```yaml
work_id: publisher or global identifier
licensable_unit:
  type: chapter | section | page_range | video_segment | article | dataset
  locator: stable structural reference
access_mode: stream | download | read_only | time_limited
territory: allowed jurisdictions
user_scope: individual | classroom | institution
price: amount and currency
royalty_split: publisher / author / platform / Raiatea
full_purchase_credit: optional
quotation_rights: explicit limits
ai_processing_rights: allowed | restricted | prohibited
sharing_rights: private_only | group | public_derivatives
expiry: optional
```

The system must preserve the official fragment separately from any annotations, translation, or generated learning artefact.

---

## 6. Generated alternatives must be genuinely independent

A generated alternative becomes high-risk when it mirrors the protected source too closely.

Raiatea should not publish, without permission:

- a full translation;
- an abridged replacement of a chapter;
- the same sequence of sections, arguments, examples, and exercises with different wording;
- recreated protected figures;
- extensive quotations;
- a substitute that allows the user to avoid the original while consuming substantially the same expressive work.

A safer and more valuable alternative should:

- start from the learner's knowledge gap;
- use multiple independent sources;
- adopt a new structure;
- create original examples and diagrams;
- distinguish shared facts and ideas from source-specific expression;
- cite all important influences;
- include open alternatives;
- explain limitations;
- pass textual and structural similarity checks;
- undergo human or legal review for high-risk cases.

Text and data mining permissions do not automatically grant the right to distribute translations or derivative substitutes. The publication boundary must therefore be stricter than the private analysis boundary.

---

## 7. Shared-by-default generated knowledge

A personalised Raiatea module may begin from one user's need, but its reusable core should normally return to the shared commons.

The module can be separated into:

### Private personalisation layer

- user's prior knowledge;
- private examples;
- study schedule;
- mistakes;
- private source ownership;
- confidential context.

### Shareable learning core

- independent explanation;
- original diagrams;
- generic exercises;
- concept map;
- prerequisite relations;
- bibliography;
- open-source links;
- source roles;
- version and review history.

Later users receive the shared core, which Raiatea adapts locally to their own profiles.

> Personalisation may be private; the reusable educational contribution should normally become common knowledge.

---

## 8. Compensation for generated artefacts

Possible models include:

- included in a Raiatea subscription;
- one-time purchase for intensive custom generation;
- community compute credits;
- institutional sponsorship;
- creator marketplace with quality review;
- revenue sharing with human authors and reviewers;
- free shared core with paid private adaptation and tutoring;
- paid certification, assessment, and professional support.

The user should not pay repeatedly for the same already-shared core. Payment should primarily cover:

- new computation;
- private adaptation;
- expert review;
- guaranteed quality;
- fast delivery;
- private storage;
- specialised assessment;
- licensed source access.

---

## 9. Avoiding perverse incentives

Raiatea must not make generated alternatives appear superior merely because Raiatea earns a larger margin on them.

The comparison engine should rank options before commercial margins are attached.

Required safeguards:

1. Show official, generated, and free options when they are credible.
2. Explain differences in authority, completeness, originality, time, and price.
3. Disclose every commercial relationship.
4. Let users disable paid and affiliate options.
5. Preserve the same epistemic recommendation with monetisation disabled.
6. Audit whether generated alternatives systematically displace stronger official sources.
7. Compensate publishers or authors only through explicit licences, not informal extraction.
8. Never label generated material as official or author-endorsed.

---

## 10. A possible marketplace

In the longer term, Raiatea could become a marketplace for knowledge units rather than only whole publications.

Participants may include:

- publishers;
- authors;
- teachers;
- universities;
- libraries;
- course creators;
- research communities;
- expert reviewers;
- open educational resource projects.

The marketplace could offer:

- licensed fragments;
- complete works;
- independently authored modules;
- alternative explanations;
- exercise packs;
- verified translations;
- expert reviews;
- learning paths;
- update subscriptions.

Ranking must remain governed by fit and quality rather than commercial bidding.

---

## 11. Immediate value

This feature can create strong perceived value because Raiatea may say:

- buy only this chapter;
- watch only these twelve minutes;
- borrow this book instead of purchasing it;
- do not buy anything yet;
- use the free source first;
- pay for the official treatment if you need its depth;
- use a shorter personalised module for your immediate gap;
- upgrade later if the topic becomes central to your route.

This converts source acquisition from uncertain shopping into a justified learning decision.

---

## 12. Open questions

- Will publishers licence chapters, sections, or video segments at viable prices?
- How are royalties divided among publishers, authors, platforms, and Raiatea?
- Can fragment purchases be credited toward full works?
- What technical standard identifies stable paragraphs and video segments across editions?
- How is source-substitution risk measured across languages and modalities?
- How much human authorship and review is required for a generated module?
- Which parts of a generated artefact are copyrightable and who owns them?
- Should all reusable generated cores use a commons licence?
- How are errors corrected after a module has been widely shared?
- How can small publishers and independent authors participate without expensive integrations?

---

## 13. Provisional decision

Raiatea should pursue two parallel routes:

1. negotiate lawful micro-access to official source fragments;
2. create genuinely independent, multi-source, personalised learning artefacts whose reusable core returns to the shared commons.

The options must be presented neutrally, with free alternatives and full disclosure of commercial interests.

> Raiatea should help users purchase only the authority they need, generate only the explanation they lack, and share the new understanding without copying the work that inspired it.
