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

## SourceReference boundary

The internal SourceReference contract now accepts the bounded local media set:

- `application/epub+zip`;
- `application/pdf`.

The record shape is unchanged and remains path-free. A PDF SourceReference carries
opaque catalog/stored/logical refs, media type, byte length and fingerprint. It
carries no source path/root, source bytes or rights grant.

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

Therefore after PDF1a the product can truthfully say:

> "I know this PDF exists as a current Source and can track it safely."

It cannot yet say:

> "I know what this PDF contains."

That functional increment belongs to PDF1b/PDF1c.
