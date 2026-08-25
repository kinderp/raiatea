# E-07 follow-up — G-02 rights-safe data boundary closure

> Parent gate synthesis: [`e07-first-slice-gates.md`](e07-first-slice-gates.md)  
> Maintainer decision: [#131](https://github.com/kinderp/raiatea/issues/131)  
> Decision date: **25 August 2026**  
> Target status after acceptance of the licensing follow-up: **satisfied-with-bounded-scope**

## 1. What changed

E-07 originally left G-02 blocked because the repository had no explicit maintainer decision for redistribution of the project-created benchmark fixture/gold material.

The maintainer has now selected:

```text
fixture content / generated fixtures / gold-reference data -> CC BY 4.0
defined fixture-generator code                            -> Apache-2.0
rest of Raiatea                                           -> no license decision here
remote Provider processing                                -> still not authorized
```

Canonical evidence:

- `benchmark/LICENSING.md` — human-readable scope, attribution and exclusions;
- `benchmark/NOTICE.md` — redistribution/attribution notice;
- `benchmark/manifests/redistribution-rights.json` — machine-readable current rights overlay;
- `benchmark-rights-decision-2026-08-25.md` — relationship to the accepted E-03/E-04 rights model;
- `benchmark/tests/test_benchmark_licensing.py` — regression evidence.

## 2. Why historical manifests are not rewritten

The old inline `not-established` fields remain valid evidence of the rights state at the commits where E-04 measurements were executed. Rewriting those pinned inputs would damage provenance without improving the current legal decision.

The current rights overlay therefore carries present redistribution policy while explicitly preserving historical evidence:

```text
measurement-era rights field -> historical fact
current rights overlay       -> current redistribution authority evidence
```

The regression suite requires both facts to remain visible.

## 3. G-02 requirements

### Processing Rights remain explicit

The E-01 separation is unchanged. A public redistribution license does not itself create permission to process every future private/protected source.

### Local/remote data flow remains separate

CC BY 4.0 makes the eligible benchmark fixtures redistributable, but it does not authorize externally hosted Provider use. The rights overlay keeps `remote_provider = denied` and the future route still requires Provider data-policy evidence.

### Redistribution Rights are now explicit

For the bounded current project-created fixture set, the overlay provides:

- explicit license identifier `CC-BY-4.0`;
- attribution requirement;
- project-created/generated origin evidence;
- `public_rights_safe = true` for redistribution;
- an explicit third-party/private-material exclusion.

The exact bounded generator code receives `Apache-2.0` through the scoped benchmark licensing record without turning the rest of the repository Apache-licensed.

## 4. Gate disposition

Subject to green licensing regressions and final review of the follow-up PR:

**G-02 = satisfied-with-bounded-scope.**

The bounded scope is important:

- current eligible project-created P0 benchmark fixtures/gold only;
- no remote Provider authorization;
- no blanket rights inheritance for future third-party fixtures;
- no repository-wide license decision;
- no trademark grant;
- no licensing conclusion for private exploratory corpus material.

## 5. First-slice consequence

Once this follow-up is accepted and #131 is closed as completed, **all G-01..G-07 first-slice planning gates have sufficient evidence within their documented scope**.

That still does not start implementation automatically. The next required repository action remains a **separate first-slice promotion decision** that selects the exact measured route/profile, implementation boundary and exit criteria.
