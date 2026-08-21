# P0 Provider Comparison Matrix

> Document maturity: `Draft`
>
> Assertion status: `mixed`
>
> Version: 0.1.0
>
> Last reviewed: 21 August 2026
>
> Observation date: **21 August 2026**
>
> Parent issue: [#125](https://github.com/kinderp/raiatea/issues/125)
>
> Narrative survey: [`technology-survey.md`](technology-survey.md)

## 1. Reading rules

This matrix compares **documented** Provider capabilities. It is not a benchmark
scorecard.

Legend for Provider-capability cells:

- **D** — documented by a primary source at the observed version;
- **P** — plausible/partial but needs direct fixture verification;
- **N** — not the Provider's intended capability or insufficient for the stated
  P0 requirement by itself;
- **Later** — relevant to a later Benchmark Class, not a B-01/B-02 requirement;
- **Separate** — available only through a distinct model/service/optional route
  whose license/security/runtime must be evaluated independently.

No `D` value means “Raiatea has tested it.” E-04 owns measured evidence.

Two kinds of information deliberately coexist in this document and must not be
confused:

1. **Provider evidence** — documented formats, outputs, deployment shapes and
   licenses, using the status legend above;
2. **Raiatea assessment** — architecture/threat interpretation derived from E-01,
   explicitly labelled as such and never presented as a Provider claim.

An externally hosted or third-party remote service can be noted as existing
without becoming an eligible P0 route. **Every externally hosted route is blocked
from E-04 by default in E-02 unless a separate, current Provider data-policy
snapshot and E-01 rights/sensitivity decision explicitly make that route
eligible.** Self-hosted HTTP/service deployment inside the user's controlled
environment is not the same trust boundary as sending Source content to an
external Provider.

## 2. Version and license snapshot

| Provider/tool | Snapshot | Code license / material constraint | Local route | Remote/hosted status in E-02 | Survey note |
| --- | --- | --- | --- | --- | --- |
| Docling | 2.117.0 | MIT; model licenses separate | D | Self-hosted service documented; externally hosted Provider route **not evaluated / blocked** | broad generalist |
| Marker | 2.0.0 | current code files Apache-2.0; model weights use modified AI Pubs Open Rail-M terms | D | Hosted/on-prem/API offerings may exist; external hosted route **blocked pending data-policy evidence** | PDF-focused; model/runtime license is material |
| MinerU | 3.4.4 | MinerU Open Source License = Apache-2.0 + extra commercial/attribution terms | D | Self-hosted client/server route documented; external hosted Provider route **not evaluated** | multiple pipeline/VLM/hybrid backends |
| Unstructured | 0.25.0 | OSS community components Apache-2.0; hosted platform separate | D | Hosted platform existence noted; **blocked pending current data-policy evidence** | element/ETL oriented |
| Apache Tika | 3.3.2 | Apache-2.0 | D | Self-hosted `tika-server`; no external Provider route evaluated | broad type/metadata/text extraction |
| GROBID | 0.9.0 | Apache-2.0; bundled/external components have their own licenses | D | Self-hosted service/container; optional external consolidation calls are **separate and blocked unless policy-qualified** | scholarly specialist |
| OCRmyPDF | 17.10.0 | MPL-2.0; dependencies have own licenses | D | No external hosted route evaluated | searchable PDF/PDF-A OCR orchestration |
| Tesseract | 5.5.3 | Apache-2.0 | D | No external hosted route evaluated | OCR engine, not document parser |
| PaddleOCR | 3.7.0 | Apache-2.0 code; exact model/runtime licenses must be pinned | D | Service/API ecosystem existence may be noted; external Provider route **blocked pending data-policy evidence** | OCR + layout/VLM ecosystem |
| Pandoc | 3.10.2 | GPL, version 2 or greater; distribution implications require normal dependency review | D | No external hosted route evaluated | semantic converter/AST |
| EbookLib | 0.20 | AGPL-3.0 | D | No external hosted route evaluated | EPUB read/write; not preselected |

The remote/hosted column records **survey scope and eligibility**, not an
endorsement. E-02's B-01/B-02 route candidates are local/self-hosted routes only.
A later remote-route survey must pin current retention, training/improvement,
logging, region/data-residency, subprocessors and deletion behavior as applicable
before a remote route can enter E-04.

## 3. Source Family matrix

| Provider/tool | SF-01 paginated digital | SF-02 scanned PDF | SF-03 EPUB | SF-04 Office/ODF | SF-05 image/photo | SF-06 web | SF-07 code/repo | SF-08 AV | SF-09 metadata | SF-10 physical observation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Docling | D | D | D | D | D | D | P | D | P | N |
| Marker | D | D | P via full extras/conversion | P | P | P | N | N | P | N |
| MinerU | D | D | N in current native list | D DOCX/PPTX/XLSX | D | N | N | N | P | N |
| Unstructured | D | D | D/partition support to verify semantics | D | D | D | P | P | D | N |
| Apache Tika | D | P/text/OCR integration dependent | D | D | P | D | P | P | D | N |
| GROBID | Later / scholarly PDF | Later if scholarly scan route is separately enabled | N | N | N | N | N | N | scholarly metadata D | N |
| OCRmyPDF | N for native extraction | D | N | N | P image-to-PDF workflow | N | N | N | N | N |
| Tesseract | N | D at image OCR layer | N | N | D | N | N | N | N | N |
| PaddleOCR | P | D | N | D via document conversion/parsing ecosystem | D | N | N | N | P | N |
| Pandoc | P semantic only | N OCR | D | D | N | D | P | N | D | N |
| Direct EPUB parser | N | N | D candidate capability | N | N | N | N | N | package metadata D | N |

The matrix intentionally avoids treating physical holdings as an extraction
Provider problem. SF-10 belongs to Catalog/metadata workflows until a separate
digitization Source exists.

## 4. Structure and Source Coordinate matrix

| Provider/tool | Hierarchy / reading order | Page/bbox coordinates | Reflowable/package anchors | Tables | Figures/images | Formulas | Citations/references | Raw/intermediate inspectability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Docling | D | D | P for B-02 requirements | D | D | D | P/general, not scholarly-specialized | D lossless DoclingDocument/JSON |
| Marker | D | D JSON polygon/bbox | P/needs proof | D | D | D | P | D JSON/meta; internal blocks available |
| MinerU | D | D/intermediate layout outputs | N for EPUB | D | D | D | P | D middle/model/content-list outputs |
| Unstructured | D element/parent model | D for PDF/image elements | P | D in hi_res | D | P | P | D Elements + detection origin/metadata |
| Apache Tika | P semantic text hierarchy by parser | N as general B-01 bbox contract | P semantic/package only | P | P | N/general | P metadata/text | D text/metadata, not rich layout IR |
| GROBID | D scholarly TEI | D selectively/where requested | N | D | D | D | D strongest specialization | D TEI/service output |
| OCRmyPDF | N document hierarchy | OCR text positioning inside output PDF; not Raiatea normalized bbox contract | N | N | preserves page image | N | N | P generated PDF + OCR side artifacts depending config |
| Tesseract | N document hierarchy | D OCR region formats/coordinates at OCR layer | N | N | N | N | N | D OCR outputs |
| PaddleOCR | D in structure/VL routes | D for detection/layout outputs | N | D | D | D | P | D pipeline result structures; exact selected model must be pinned |
| Pandoc | D semantic AST/reading order | N visual bbox | D semantic EPUB/HTML anchors only through reader model; stability must be tested | D semantic | D references/assets | D semantic | P | D Pandoc AST/native JSON |
| Direct EPUB parser | D spine/nav/DOM if implemented correctly | N/not applicable | D target capability | HTML semantic | D resources | HTML/MathML dependent | links/footnotes P | D package/XHTML raw data |

## 5. OCR and fallback matrix

| Provider/tool | Native-text path | OCR path | Selective/fallback OCR | Multi-engine option | Notes |
| --- | --- | --- | --- | --- | --- |
| Docling | D | D | D/configurable | D RapidOCR/EasyOCR/Tesseract/macOS/etc. | engine/model license and runtime remain separate |
| Marker | D pdftext | D Surya VLM | D page/block selective modes | P architecture can compose, built around Surya/current models | no-OCR fast route is distinct benchmark route |
| MinerU | D pipeline | D | D auto/hybrid | D multiple backend classes | compare pipeline, VLM and hybrid separately |
| Unstructured | D PDFMiner fast | D Tesseract and layout routes | D auto strategy | P OCR agent abstractions | `fast`, `ocr_only`, `hi_res` must be separate routes |
| Apache Tika | D | P via parser integrations/external OCR configs | P | P | primarily broad parser/probe baseline |
| GROBID | D scholarly PDF via pdfalto pipeline | N as generic OCR baseline | N | N | not B-03 baseline |
| OCRmyPDF | preserves/inspects existing text | D Tesseract | D default/force/skip/redo modes | N default | ideal OCR/PDF orchestration baseline |
| Tesseract | N | D | N orchestration | N | lower-level OCR engine |
| PaddleOCR | P/native document routes | D | D in structure/document pipelines | D ecosystem/model choices | exact pipeline must be version/model pinned |

## 6. Deployment and threat-boundary matrix

The Provider/deployment columns below remain documentary evidence. The
**Raiatea E-01 isolation-review priority** column is explicitly a project threat
assessment, not a Provider claim and not a measured security score.

| Provider/tool | In-process library | CLI | Local service | Remote/service existence — not eligibility | Raiatea E-01 isolation-review priority | Network needed for local core route after models installed |
| --- | --- | --- | --- | --- | --- | --- |
| Docling | D | D | D `docling-serve` | Self-hosted service documented; external hosted route not evaluated | High — complex parsers/models and untrusted documents | P/No for local route |
| Marker | D | D | D inference/server patterns | Hosted/on-prem/API existence noted; external hosted route blocked | High — VLM server + document parser | No for configured local route after assets available |
| MinerU | D | D | D FastAPI/Gradio/client-server | Self-hosted client/server documented; external hosted route not evaluated | High — multiple VLM/pipeline backends | No for local engine after models available |
| Unstructured | D | P | D/local API | Hosted platform exists; external hosted route blocked | High — `hi_res`/model/container parsing | No for configured local route after models |
| Apache Tika | Java API | D app | D `tika-server` | Self-hosted service only in E-02 scope | High — broad parser/dependency surface | No for local parser set |
| GROBID | Java/core | D/Gradle tooling | D web service/Docker | Self-hosted; optional external Crossref/glutton enrichment separately policy-gated | Medium/high — PDF parser + service/dependency surface | No for core extraction if consolidation disabled |
| OCRmyPDF | Python API | D | containerizable | No external hosted route evaluated | High — PDF/Ghostscript/qpdf/Tesseract toolchain | No |
| Tesseract | library | D | wrapper needed | No external hosted route evaluated | Medium — native image parser/OCR engine | No |
| PaddleOCR | D | D | D/deployment ecosystem | Service ecosystem exists; external hosted route blocked | High — VLM/OCR model/runtime surface | No for local models |
| Pandoc | library ecosystem | D | wrapper needed | No external hosted route evaluated | Medium/high — broad readers/resources; active content remains data | Usually no for local files, except explicitly fetched resources |
| EbookLib/direct EPUB | D | N primary | wrapper needed | No external hosted route evaluated | High — untrusted ZIP/path/resource traversal requires hardening | No |

“Network needed” does not mean “network should be allowed.” The threat boundary
may require network-disabled benchmark execution for local Providers. Likewise,
a High isolation-review priority does not mean a Provider is known vulnerable;
it means Raiatea's E-01 threat model requires stronger isolation evidence before
processing valuable/untrusted Sources with that route.

## 7. Licensing/adoption matrix

| Provider/tool | Survey status | Adoption concern | E-02 interpretation |
| --- | --- | --- | --- |
| Docling | permissive code | selected model licenses vary | low code-license friction; model manifest required |
| Marker | code permissive in current files; weights restricted/custom | commercial threshold/weight terms; backend dependencies | do not package blindly; benchmark with explicit model-license record |
| MinerU | custom Apache-derived license | MAU/revenue threshold + online-service attribution | usable candidate but not license-neutral |
| Unstructured | Apache-2.0 community components | hosted platform terms separate; model deps separate | generally reusable; pin inference dependencies |
| Tika | Apache-2.0 | huge parser/dependency surface | good reusable infrastructure candidate |
| GROBID | Apache-2.0 | pdfalto/external component licensing differs | acceptable composition if dependency boundary documented |
| OCRmyPDF | MPL-2.0 | source modifications to OCRmyPDF subject to MPL; external deps separate | good process/API composition candidate |
| Tesseract | Apache-2.0 | language traineddata/model provenance separately relevant | low core-license friction |
| PaddleOCR | Apache-2.0 code | specific models/runtime packages must be checked | component-level manifest required |
| Pandoc | GPL, version 2 or greater | distribution/linkage/deployment design needs normal compliance review | prefer process boundary if avoiding license coupling concerns |
| EbookLib | AGPL-3.0 | strong copyleft + open 2026 path-traversal issue | do not preselect for a reusable neutral core |

The matrix is architectural evidence, not legal advice.

## 8. B-01 born-digital PDF candidate matrix

| Route | Text fidelity hypothesis | Structure/read order hypothesis | Bbox/Source Coordinate hypothesis | Complex structures | Local/private route | Main reason to benchmark |
| --- | --- | --- | --- | --- | --- | --- |
| Docling PDF | strong | strong | strong documented provenance/bbox | tables/formulas/code/images | yes | closest documented fit to P0 normalized requirements |
| Marker 2 fast | strong for native text + layout | strong candidate | JSON polygon/bbox | tables/formulas; selective VLM | yes | speed/quality tradeoff and CPU/MPS relevance |
| Marker 2 balanced | strong candidate | strong candidate | JSON polygon/bbox | VLM-heavy complex structures | yes | quality ceiling versus resource/model cost |
| MinerU pipeline | strong candidate | strong candidate | intermediate/layout evidence | strong complex-doc focus | yes | non-VLM/pipeline baseline |
| MinerU hybrid/VLM | strong candidate | strong candidate | intermediate/layout evidence | strong complex-doc focus | yes | alternate complex-layout architecture |
| Unstructured fast | strong native-text baseline | medium | coordinates from PDFMiner elements | limited versus hi_res | yes | simple deterministic element baseline |
| Unstructured hi_res | strong candidate | strong element model | coordinates | tables/images | yes | ETL element route vs document-IR routes |
| Tika 3.3.2 | broad text/metadata baseline | parser dependent | weak for bbox requirement | parser dependent | yes | cheap/broad native extraction control |
| PaddleOCR document parse | candidate | candidate | detection/layout coordinates | tables/formulas/layout | yes | independent OCR/VL architecture |

All B-01 entries above refer to local/self-hosted evaluation routes. No external
hosted service is admitted to E-04 by this matrix.

No route is selected by this matrix.

## 9. B-02 EPUB candidate matrix

| Route | Native package/spine awareness | Stable package/logical anchors | XHTML semantics | Assets/nav | Visual-layout dependency | Main concern |
| --- | --- | --- | --- | --- | --- | --- |
| Docling EPUB | D format support | P — benchmark required | D/P | D/P | low | verify provenance/anchors rather than assume PDF-style model |
| Thin direct EPUB parser | target D | target D | target D | target D | none | select safe/permissive library and ZIP traversal policy |
| Pandoc EPUB reader | D | P | D semantic | D | none | AST may normalize away source-specific anchors needed by P0 |
| Marker `[full]` | P conversion support | P/unknown | P | P | may use conversion pipeline | format support may not preserve source package coordinates |
| Unstructured EPUB | D/P partition support | P | D/P | P | low | element output may lose original anchor granularity |
| Tika EPUB | D parser support | P | D/P | P | low | useful metadata/text baseline, coordinate fidelity uncertain |

All B-02 entries above refer to local/self-hosted evaluation routes. Remote
service existence is outside E-04 eligibility until the separate policy evidence
required by E-01 is available.

B-02 must not reward page/bbox features that are meaningless for canonical
reflowable content.

## 10. Capability gaps no Provider should silently own

The matrix reveals several P0 capabilities that remain Raiatea responsibilities
or explicit thin-layer gaps regardless of Provider choice:

1. Provider-neutral `Source`/input identity and version pinning.
2. Rights/sensitivity/remote-route policy before Provider invocation.
3. `Raw Extraction` preservation or diagnostic references under Retention Policy.
4. Mapping Provider output to Raiatea `Normalized Representation` concepts.
5. Source Coordinate normalization without fabricating unsupported stability.
6. Uniform `Warning`/`Degraded Result`/failure/unknown semantics.
7. Transformation/Provider/model/version/parameter Provenance.
8. Adapter validation: Provider output is untrusted data.
9. Safe output-root/path handling independent of source metadata.
10. Benchmark-class routing based on measured evidence.
11. Version drift detection and re-benchmark triggers.
12. No hard dependency of the public P0 contract on DoclingDocument, Marker JSON,
    MinerU middle JSON, Unstructured Elements, TEI or another Provider-native
    schema.

## 11. Evidence still required

The following cells cannot be promoted from `P` to measured support until E-04:

- cross-Provider reading-order fidelity;
- coordinate accuracy/stability;
- EPUB source-anchor preservation;
- manual repair burden;
- complex table/formula/figure quality;
- warning/degradation completeness;
- runtime/memory/disk/GPU behavior on target machines;
- deterministic output/version drift;
- malformed/adversarial input behavior under isolation;
- Adapter complexity based on real outputs;
- quality/cost tradeoffs between fast/pipeline/VLM modes.

Remote-hosted route eligibility additionally requires a separate current
Provider data-policy evidence package and E-01 rights/sensitivity approval before
it can even become an E-04 candidate.

## 12. Out of scope

This matrix does not:

- define weighted rankings;
- assign one universal quality score;
- select a Provider;
- authorize remote processing;
- approve transitive model licenses;
- define a public schema/API;
- promote the candidate first slice;
- replace E-03 fixture design or E-04 measurements.
