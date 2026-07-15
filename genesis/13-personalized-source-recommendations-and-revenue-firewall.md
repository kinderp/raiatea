# Personalized Source Recommendations and Revenue Firewall

**Status:** Draft  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Define how Raiatea recommends books, papers, courses, videos, repositories, subscriptions, and other sources for a specific learning or research path, and how those recommendations may generate revenue without corrupting their objectivity.

---

## 1. Core idea

Raiatea should not recommend a source because it is generally popular or commercially promoted.

It should recommend it because, for a specific person and a specific expedition, the source is expected to solve a clearly identified knowledge need.

A recommendation should answer:

- Why is this source useful now?
- Which part of the route does it cover?
- Which prerequisites does it assume?
- What does it explain better than the alternatives?
- What does it not cover?
- Is it too advanced, too introductory, outdated, redundant, or poorly matched to the user?
- Is there a free or open alternative?
- How much time and money will it require?

> Raiatea should recommend sources as instruments for a route, not as products to be sold.

---

## 2. Personalized source review

Each recommendation should be a personalized review rather than a generic star rating.

Example:

```text
Recommended source: Book A

Why it is useful for your route
- explains attention mechanisms more clearly than your current sources;
- fills the prerequisite gap on matrix operations;
- contains practical PyTorch examples;
- prepares chapters needed before reading Paper B.

Why it may not be ideal
- weak coverage of inference optimisation;
- examples use an older library version;
- requires basic calculus;
- overlaps with Book C in chapters 1–3.

Recommended use
- read chapters 2, 4, and 6;
- skip chapter 1 because your profile already covers it;
- complete exercise 6.3 before continuing the expedition.

Alternatives
- open lecture series D;
- Paper E for a more mathematical treatment;
- Book F if a slower introduction is preferred.
```

The review must be generated from the source's actual content, the route, the user's current understanding, and the quality of available alternatives.

---

## 3. Recommendation dimensions

Possible dimensions include:

- topic coverage;
- depth;
- clarity;
- mathematical level;
- practical orientation;
- historical importance;
- recency;
- accuracy;
- source quality;
- prerequisite fit;
- redundancy with owned material;
- expected learning gain;
- time cost;
- monetary cost;
- language;
- accessibility;
- licence and availability;
- relevance to the user's immediate goal;
- value for future routes.

The recommendation should not collapse these dimensions into one opaque score.

---

## 4. Recommendation types

Raiatea may recommend:

- books;
- individual chapters;
- papers;
- standards;
- datasets;
- repositories;
- courses;
- lectures;
- videos;
- podcasts;
- newsletters;
- journals;
- conferences;
- researchers and public profiles to follow;
- communities;
- tools and software;
- legal purchase, subscription, borrowing, or access options.

Recommendations should include free and public sources whenever they can satisfy the same need.

---

## 5. Revenue opportunity

Raiatea may earn revenue when a user voluntarily purchases or subscribes to a recommended source through an affiliate, publisher, library, course, or marketplace link.

This may support:

- the Foundation;
- infrastructure;
- preservation;
- community compute;
- open-source development;
- grants for public knowledge work.

However, commercial compensation creates a direct conflict of interest and must be constrained by design.

---

## 6. Revenue firewall

The recommendation engine must be computed independently of commercial availability and commission.

The process should be:

```text
1. Determine the user's knowledge need.
2. Rank all eligible sources using epistemic and educational criteria.
3. Record the reasons and alternatives.
4. Only after ranking, attach lawful access and purchase options.
5. Disclose any financial relationship.
```

Commercial information must not enter the epistemic ranking function except where price or access is an explicit user constraint.

Raiatea must not:

- rank a weaker source higher because it pays more;
- hide a free alternative;
- recommend unnecessary purchases;
- invent urgency or scarcity;
- allow publishers to buy positive reviews;
- suppress criticism in exchange for partnership;
- recommend a whole book when only one chapter is useful;
- use hidden sponsored placement inside a learning route.

---

## 7. Required disclosure

Every monetized recommendation should state clearly:

```text
Raiatea recommends this source for the reasons above.
The ranking was produced independently of commercial compensation.
Raiatea may receive a commission if you use this purchase link.
A free or non-affiliate access option is shown when available.
```

The user should be able to disable affiliate links globally while retaining the same recommendations.

A recommendation must remain identical in epistemic content whether or not the user enables monetized links.

---

## 8. Independent auditability

To preserve trust, Raiatea should maintain an auditable recommendation record containing:

- route state at recommendation time;
- detected knowledge gap;
- candidate sources considered;
- ranking criteria;
- excluded sources and reasons;
- user constraints;
- commercial relationships attached after ranking;
- later user feedback;
- whether the recommendation improved the route.

Aggregate reports should show:

- revenue by publisher or provider;
- concentration of recommended vendors;
- percentage of recommendations with free alternatives;
- conversion rates;
- recommendation quality independent of conversion;
- complaints and corrections;
- cases where a non-monetized source outranked a monetized source.

---

## 9. Publisher and creator participation

Publishers, authors, teachers, and creators may provide:

- machine-readable tables of contents;
- sample chapters;
- learning objectives;
- prerequisites;
- licences;
- update feeds;
- errata;
- access options;
- educator resources;
- structured metadata.

They may not directly set recommendation rank.

Raiatea may allow verified creators to respond to reviews, correct metadata, or explain intended audiences, but those responses must remain distinguishable from independent analysis.

---

## 10. Community feedback

Users may report:

- whether a source was worth the time;
- whether it matched the stated level;
- which chapters were useful;
- errors or obsolete sections;
- missing alternatives;
- accessibility issues;
- whether the recommendation advanced the expedition.

Community feedback should update the evidence behind recommendations, not become a popularity contest.

A source useful to experts may be unsuitable for beginners even if highly rated overall.

---

## 11. Recommendations over time

Recommendations should evolve with the user and the field.

A source may move through statuses such as:

```text
recommended now
recommended later
optional
reference only
historically important
partially obsolete
superseded
not suitable for this route
already covered by owned sources
```

Raiatea should notify the user when:

- a better edition appears;
- a book becomes outdated;
- an open alternative becomes available;
- a previously recommended source is corrected or withdrawn;
- a new source materially improves the route.

---

## 12. Immediate value

This capability creates immediate value because users frequently waste money and time on sources that are:

- too advanced;
- too superficial;
- redundant;
- outdated;
- poorly matched to their goal;
- recommended through generic popularity rather than need.

A useful Raiatea recommendation can save more value by advising against a purchase than by generating an affiliate commission.

> Trust grows when the system is willing to say: do not buy this yet, read this free source first, or use only these three chapters.

---

## 13. Business-model implications

Affiliate revenue can be one minor and diversified component of Raiatea's sustainability model.

It must not become the dominant revenue source, because dependence would create pressure to increase purchases and favour commercial material.

Possible policy limits:

- maximum percentage of total revenue from affiliate commissions;
- no exclusive publisher agreements affecting ranking;
- public disclosure of partner revenue concentration;
- recommendation audits by the Foundation;
- mandatory free-alternative search;
- separation between recommendation engineers and commercial partnership targets;
- independent complaints and appeal process.

---

## 14. Domain concepts introduced

- `KnowledgeGap`;
- `SourceCandidate`;
- `SourceFitAssessment`;
- `PersonalizedSourceReview`;
- `RecommendationReason`;
- `AlternativeSource`;
- `AccessOption`;
- `CommercialRelationship`;
- `AffiliateDisclosure`;
- `RecommendationAudit`;
- `LearningOutcomeFeedback`;
- `SourceLifecycleStatus`.

---

## 15. Provisional decision

Raiatea may monetize access links associated with source recommendations, but recommendations must be generated before and independently of commercial compensation.

Every recommendation must explain its value for the user's route, expose limits and alternatives, disclose financial relationships, and remain usable with monetization disabled.

> Raiatea earns trust by helping the user acquire the right source at the right moment—and sometimes by advising them not to buy anything at all.
