# PDF1a — Mixed EPUB + PDF local Sources

> Parent PDF increment: #203  
> Micro-step: #204  
> Scope: source admission/catalog only; no PDF extraction yet.

## Functional increment

VS1 accepted a complete local EPUB product slice. PDF1a broadens the same local
Source catalog so a single authorized collection may contain both EPUB and PDF.

Before PDF1a:

```text
library/
  book.epub  -> inventoried Source
  paper.pdf  -> ignored by bounded inventory
```

After PDF1a:

```text
library/
  book.epub  -> application/epub+zip -> Stored Instance -> SourceReference
  paper.pdf  -> application/pdf      -> Stored Instance -> SourceReference
  notes.txt  -> ignored
```

The PDF is a first-class **Source**, but not yet extracted content. Poppler and
Docling product extraction are later PDF1 children.

## Shared identity and Location semantics

PDF does not get a second catalog or a PDF-specific identity model. EPUB and PDF
entries share the accepted VS1b rules:

- path is mutable `Location`, not identity;
- equal bytes at two Locations remain two Stored Instances;
- rename/move may preserve candidate identity when observation evidence supports
  the transition;
- delete/offline is Location-level evidence, not logical purge;
- changed bytes at a Location create a replacement candidate rather than changing
  the meaning of an existing Stored Instance silently;
- stale/gapped observation requires bounded inventory reconciliation.

A media-class transition such as `.epub -> .pdf` is not accepted merely from the
rename. The candidate remains non-fresh until bounded inventory verifies the new
Location and media admission. The physical Stored Instance candidate may remain
stable for identical bytes, but the current `SourceReference` rotates because its
media class changed.

## SourceReference boundary

The internal SourceReference contract now accepts the bounded local media set:

- `application/epub+zip`;
- `application/pdf`.

The record shape is unchanged and remains path-free. A PDF SourceReference carries
opaque catalog/stored/logical refs, media type, byte length and fingerprint. It
carries no source path/root, source bytes or rights grant.

Existing EPUB SourceReference ids retain the accepted VS1 identity basis. New
non-EPUB source classes bind `media_type` into the deterministic SourceReference
namespace so an otherwise identical opaque catalog instance cannot collide
across media classes.

The existing official LocalSourcePlugin remains a metadata-only
catalog-snapshot-to-reference process. It does not parse either EPUB or PDF.

## Admission is not PDF validation

`.pdf` is a bounded inventory admission rule, not proof that bytes are a valid
PDF. The PDF extractor profile later owns parsing/provider evidence and must fail
closed on malformed/access-controlled inputs according to the accepted B-01
negative evidence.

## Downstream truth boundary

PDF1a intentionally does not make unextracted PDFs searchable. The existing EPUB
ExtractorPlugin remains media-specific and rejects a PDF SourceReference.

The VS1f authority backup may preserve a current PDF inventory/SourceReference,
but restore must physically reconcile that PDF before publication. It does not
create a PDF extraction or searchable content. A missing PDF causes the mixed
restore to fail closed and leave the target store empty.

Therefore after PDF1a the product can truthfully say:

> "I know this PDF exists as a current Source and can track it safely."

It cannot yet say:

> "I know what this PDF contains."

That functional increment belongs to PDF1b/PDF1c.

## Finding log

| ID | Severity | Status | Finding | Resolution |
| --- | --- | --- | --- | --- |
| PDF1A-F1 | major | resolved | Generalizing the Source contract without media-aware identity could let otherwise identical opaque catalog/fingerprint inputs collide across EPUB and PDF SourceReference namespaces. | New non-EPUB SourceReference ids bind `media_type`; regression proves the same opaque instance/bytes produce different EPUB and PDF Source ids. |
| PDF1A-F2 | major | resolved | Binding `media_type` unconditionally would rename every accepted VS1 EPUB SourceReference during upgrade. | EPUB retains the exact legacy VS1 identity basis; a dedicated regression computes the old basis independently and requires the same id. |
| PDF1A-F3 | major | resolved | Accepted VS1f restore reconciles through the original EPUB-only inventory; a PDF preserved in backup authority would therefore be misclassified as physically missing. | `MixedCatalogBackupService` keeps the VS1f backup contract but performs restore reconciliation through the mixed EPUB+PDF engine; PDF survives only when the real source still matches. |
| PDF1A-R1 | moderate residual | accepted for PDF1a | The bounded `Mixed*` adapters reuse accepted private VS1 primitives but duplicate some source-discovery/restore orchestration rather than changing the already-accepted VS1 classes in place. | There is still one CatalogStateStore, one VS1b identity model, one SourceReference contract and one LocalSourcePlugin; no competing authority is created. Before PDF1 exit, multi-media admission should be absorbed into the general local product path so future source classes do not multiply wrappers. |

## Validation boundary

PDF1a requires:

- Ubuntu/Windows × Python 3.10/3.12 mixed-source tests;
- mixed inventory, duplicate, rename, delete, changed-byte and media-transition cases;
- path-free PDF SourceReference and legacy EPUB SourceReference stability;
- EPUB extractor rejection of PDF;
- unextracted PDF excluded from current search content;
- mixed backup/restore with physical PDF reconciliation;
- all VS1a–VS1f regressions green on the frozen head.

## Next functional step

PDF1b adds the first capability to know **what is inside a PDF** through the
promoted Poppler `pdftohtml-xml` local profile. PDF1c then adds the complementary
Docling native/no-OCR semantic profile. The two Provider evidence routes remain
separate; automatic cross-Provider fusion is not part of PDF1a–PDF1c.
