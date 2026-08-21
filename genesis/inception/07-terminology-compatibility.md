# Raiatea Pre-Glossary Terminology Compatibility Map

> Supporting artifact for [`07-glossary.md`](07-glossary.md)
>
> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Parent issue: [#117](https://github.com/kinderp/raiatea/issues/117)

## Purpose

Raiatea's accepted Why, Vision, System Context, Product Map and Use Case Model
were written before the canonical Glossary existed. Some of those artifacts
therefore use deliberately provisional labels such as `Asset / Source Registry`,
`Manifestation` or `Work`.

This compatibility map preserves those documents as historical/canonical
records while explaining how their terminology should be interpreted after the
Glossary is accepted. It does **not** silently rewrite their original wording and
does not create new schema entities.

## Reading rule

When an older accepted artifact uses a term listed here:

1. preserve the original wording when quoting or explaining the historical
   decision;
2. use the preferred Glossary term in new documentation when the concept is the
   same;
3. do not infer a database/API migration solely from the terminology mapping;
4. if the old term carried more than one concept, split the meaning rather than
   forcing a one-to-one rename.

## Compatibility table

| Pre-Glossary wording | Where it appears / why | Canonical interpretation after Glossary | Migration rule for new prose |
| --- | --- | --- | --- |
| `Asset / Source Registry` | System Context/Product Map shorthand for the general logical inventory + source/provenance boundary | Read as the **Catalog** boundary plus the ability for catalogued material to assume the **Source** role in workflows; it does not imply one `Source` entity type | Prefer `Catalog` for inventory; use `Source` only for source role; name provenance/processing boundary separately when needed |
| `Asset Registry` | Earlier conversation/issues and architecture shorthand | General logical catalog/inventory responsibility | Prefer `Catalog`; `Asset` remains broad product vocabulary |
| `Source Registry` | Earlier exploratory ingestion language | Registry/inventory of source references and acquisition/provenance state, not a claim that every catalog object is a Source | Prefer concrete phrases such as `Catalog`, `Source Reference`, `Source role` or `provenance state` depending on meaning |
| `Asset` as a domain entity | Earlier broad shorthand | Too broad to be the preferred precise entity term | Use `Digital Artifact`, `Stored Instance`, `Physical Holding`, `Catalog Entry` or `Source` according to intended meaning |
| `Source` meaning file/document record | Common pre-Glossary shorthand | A **role** in a workflow/evidentiary context, not a synonym for file/path/work | Use `Digital Artifact`/`Stored Instance` for digital material, `Catalog Entry` for generic catalog reference, `Source` only when the role is intended |
| `Manifestation` / `manifestation` | Vision/#111 discussion of multiple copies/formats | Historical/provisional way to describe alternate embodiments/formats; the bibliographic Manifestation entity is not adopted | Prefer `Digital Artifact`, `Stored Instance`, `Related Representation` or `Physical Holding`; retain `Manifestation` only in historical discussion or later bibliographic research |
| `Work` | #111 and exploratory bibliographic grouping examples | Possible future bibliographic abstraction, not current core identity root | Avoid as a required entity in first-slice contracts; use explicit related-representation relationships until later evidence justifies a Work model |
| `Document` as broad item type | Earlier document-centric descriptions | Useful source/category word but not universal ontology root | Keep when the material is actually a document; use broader catalog/source/artifact vocabulary for heterogeneous future media |
| `Derivative` | Earlier provenance/transformation prose | Shorthand for `Derived Artifact` | Prefer `Derived Artifact` in formal definitions; `Derivative` remains acceptable prose shorthand |
| `Locator` | Earlier source/provenance discussions | Ambiguous between storage location and coordinate inside a source | Prefer `Location` for where material is found and `Source Coordinate` for an address inside a Source |
| `Job` / `Run` | Durex and workflow discussions | Execution concepts remain separate from `Processing Recipe`; Durex ownership remains unresolved | Prefer `Processing Run` for product/runtime-neutral use; use Durex-specific names only when referring to Durex contracts |
| `Library Catalog` | Early product idea focused on books | Superseded in scope by Universal Document & Asset Library and its `Catalog` capability | Use `Catalog` for the logical inventory and full product name for the user-facing surface |
| `Knowledge Core`, `Knowledge OS`, `Memory Graph` | Genesis exploratory language | Not an accepted current bounded context | Use concrete accepted capabilities or mark the historical term explicitly; revisit only through a future architecture decision |

## Important non-renames

The following are **not** simple renames:

### `Asset / Source Registry` → not one new entity

The old compound label compressed several responsibilities:

```text
logical catalog/inventory
+ source role/reference
+ processing/provenance state
```

The Glossary intentionally separates those meanings. A future schema may still
choose a practical aggregate internally, but documentation must not use the old
compound label to imply one universal record type.

### `Manifestation` → not automatically `Digital Artifact`

The historical word was used loosely for alternate copies/formats. Formal
bibliographic `Manifestation` has a richer established meaning that Raiatea has
not adopted. Depending on context the correct current term may instead be:

- `Digital Artifact` — concrete versioned digital material;
- `Stored Instance` — one stored copy;
- `Physical Holding` — one physical copy;
- `Related Representation` — relationship between alternate embodiments.

### `Source` → not automatically `Digital Artifact`

A Digital Artifact becomes a Source only when a workflow uses it as origin or
evidence. Conversely a Source may be a remote Source Reference or other
material that Raiatea does not retain as a Digital Artifact.

## Canonical-document interpretation

After acceptance of the Glossary:

- the decisions in `03-system-context.md` and `04-product-map.md` remain valid;
- their ownership boundary historically labelled `Asset / Source Registry`
  should be understood through `Catalog` + role-based `Source` terminology;
- `05-use-case-model.md` use-case goals remain unchanged;
- `06-risk-list.md` R-17 is contained by this explicit mapping plus the Glossary,
  but remains open for implementation/domain-model evidence;
- future P0 #106 contracts must use the Glossary or document an intentional
  divergence rather than copying pre-Glossary shorthand blindly.

## Out of scope

This compatibility map does not:

- rewrite already-accepted documents solely for terminology style;
- define schema migrations;
- adopt a bibliographic ontology;
- decide identifier formats;
- mark R-17 permanently mitigated;
- make a historical exploratory term current merely by listing it here.
