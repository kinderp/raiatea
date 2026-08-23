#!/usr/bin/env python3
"""Generate deterministic, rights-pending P0 benchmark fixtures.

This is benchmark-only evidence tooling. It is not a production document engine
and does not define Raiatea's public P0 schema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "manifests" / "fixtures.json"
GENERATOR_VERSION = "0.5.0"
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _text_cmd(text: str, x: int, y: int, size: int = 12) -> str:
    return f"BT /F1 {size} Tf 1 0 0 1 {x} {y} Tm ({_pdf_escape(text)}) Tj ET\n"


def _build_pdf(lines: list[tuple[str, int, int, int]]) -> bytes:
    """Build the original minimal PDF shape used by B01-PDF-001/002.

    Keep this serializer stable so adding later fixtures does not change the
    byte identity of already-measured canonical fixtures.
    """
    stream = "".join(_text_cmd(text, x, y, size) for text, x, y, size in lines).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_offset = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(out)


def _semantic_text_cmd(text: str, x: int, y: int, size: int, font: str = "F1") -> str:
    if font not in {"F1", "F2"}:
        raise ValueError(f"Unsupported semantic fixture font: {font}")
    return f"BT /{font} {size} Tf 1 0 0 1 {x} {y} Tm ({_pdf_escape(text)}) Tj ET\n"


def _serialize_pdf_objects(objects: list[bytes]) -> bytes:
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_offset = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(out)


def _build_semantic_structure_pdf() -> bytes:
    """Build B01-PDF-003 without adding a fixture-generation dependency."""
    lines = [
        ("Raiatea B01 PDF 003", 72, 730, 20, "F1"),
        ("Semantic Structure", 72, 685, 16, "F1"),
        ("This paragraph belongs to the main section.", 72, 655, 12, "F1"),
        ("Nested Topic", 72, 615, 14, "F1"),
        ("1. First list item.", 90, 580, 12, "F1"),
        ("2. Second list item.", 90, 555, 12, "F1"),
        ('print("raiatea-structure")', 90, 510, 11, "F2"),
        ("Raiatea benchmark link", 72, 445, 12, "F1"),
    ]
    stream = "".join(
        _semantic_text_cmd(text, x, y, size, font) for text, x, y, size, font in lines
    ).encode("ascii")

    uri = "https://example.invalid/raiatea-benchmark"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> "
            b"/Contents 6 0 R /Annots [7 0 R] >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
        (
            b"<< /Type /Annot /Subtype /Link /Rect [72 438 260 458] "
            b"/Border [0 0 0] /A << /S /URI /URI ("
            + _pdf_escape(uri).encode("ascii")
            + b") >> >>"
        ),
    ]
    return _serialize_pdf_objects(objects)


def _figure_pixel_payload() -> bytes:
    """Return the authored 4x3 RGB pixel payload used by B01-PDF-004."""
    return bytes(
        [
            255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 0,
            0, 255, 255, 255, 0, 255, 64, 64, 64, 192, 192, 192,
            255, 128, 0, 128, 0, 255, 0, 128, 255, 128, 255, 0,
        ]
    )


def _build_figure_caption_pdf() -> bytes:
    """Build B01-PDF-004 with one explicit raster XObject and authored caption."""
    pixels = _figure_pixel_payload()
    stream = (
        _text_cmd("Raiatea B01 PDF 004", 72, 730, 20)
        + _text_cmd("Body text before the benchmark figure.", 72, 665, 12)
        + "q 180 0 0 120 72 500 cm /Im1 Do Q\n"
        + _text_cmd("Figure 1. Deterministic Raiatea color grid.", 72, 470, 12)
        + _text_cmd("Body text after the benchmark figure.", 72, 425, 12)
    ).encode("ascii")

    image = (
        b"<< /Type /XObject /Subtype /Image /Width 4 /Height 3 "
        b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Length "
        + str(len(pixels)).encode("ascii")
        + b" >>\nstream\n"
        + pixels
        + b"\nendstream"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> /XObject << /Im1 5 0 R >> >> "
            b"/Contents 6 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        image,
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
    ]
    return _serialize_pdf_objects(objects)


def _build_table_structure_pdf() -> bytes:
    """Build B01-PDF-005 with authored grid geometry and unambiguous cell text."""
    x_bounds = [72, 300, 390, 540]
    y_bounds = [600, 560, 520, 480, 440]
    stream_parts = [
        _text_cmd("Raiatea B01 PDF 005", 72, 730, 20),
        _text_cmd("Body text before the benchmark table.", 72, 665, 12),
        "0.75 w\n",
    ]
    for x in x_bounds:
        stream_parts.append(f"{x} {y_bounds[-1]} m {x} {y_bounds[0]} l S\n")
    for y in y_bounds:
        stream_parts.append(f"{x_bounds[0]} {y} m {x_bounds[-1]} {y} l S\n")

    rows = [
        ["Item", "Qty", "Price"],
        ["Alpha", "2", "3.50"],
        ["Beta", "1", "7.00"],
        ["Total", "3", "14.00"],
    ]
    text_x = [82, 310, 400]
    text_y = [575, 535, 495, 455]
    for row_index, row in enumerate(rows):
        for column_index, text in enumerate(row):
            stream_parts.append(
                _text_cmd(text, text_x[column_index], text_y[row_index], 12)
            )
    stream_parts.append(
        _text_cmd("Body text after the benchmark table.", 72, 390, 12)
    )
    stream = "".join(stream_parts).encode("ascii")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
    ]
    return _serialize_pdf_objects(objects)


def _build_formula_fidelity_pdf() -> bytes:
    """Build B01-PDF-006 with separately positioned math glyphs and fraction bar.

    The PDF intentionally embeds no semantic math tags. Superscript and fraction
    relations live only in authored gold; Providers are credited for structure
    only when they expose explicit evidence rather than visual inference.
    """
    stream_parts = [
        _text_cmd("Raiatea B01 PDF 006", 72, 730, 20),
        _text_cmd("Body text before the benchmark formulas.", 72, 665, 12),
        # E = mc^2: the exponent is a distinct, smaller, raised glyph.
        _text_cmd("E", 108, 610, 16),
        _text_cmd("=", 126, 610, 16),
        _text_cmd("m", 144, 610, 16),
        _text_cmd("c", 156, 610, 16),
        _text_cmd("2", 166, 622, 9),
        # x^2 + y^2 = z^2: three distinct raised exponent glyphs.
        _text_cmd("x", 108, 555, 16),
        _text_cmd("2", 118, 567, 9),
        _text_cmd("+", 132, 555, 16),
        _text_cmd("y", 150, 555, 16),
        _text_cmd("2", 160, 567, 9),
        _text_cmd("=", 174, 555, 16),
        _text_cmd("z", 192, 555, 16),
        _text_cmd("2", 202, 567, 9),
        # (a + b) / c: numerator glyphs, authored fraction bar, denominator.
        _text_cmd("(", 108, 495, 14),
        _text_cmd("a", 116, 495, 14),
        _text_cmd("+", 128, 495, 14),
        _text_cmd("b", 142, 495, 14),
        _text_cmd(")", 152, 495, 14),
        "0.8 w\n108 486 m 164 486 l S\n",
        _text_cmd("c", 132, 462, 14),
        _text_cmd("Body text after the benchmark formulas.", 72, 405, 12),
    ]
    stream = "".join(stream_parts).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
    ]
    return _serialize_pdf_objects(objects)


def generate_pdf_single_column(path: Path) -> None:
    path.write_bytes(
        _build_pdf(
            [
                ("Raiatea B01 PDF 001", 72, 720, 18),
                ("Alpha paragraph preserves exact benchmark text.", 72, 665, 12),
                ("Beta paragraph follows alpha in reading order.", 72, 625, 12),
            ]
        )
    )


def generate_pdf_two_column(path: Path) -> None:
    path.write_bytes(
        _build_pdf(
            [
                ("Raiatea B01 PDF 002", 72, 720, 18),
                ("Left one.", 72, 665, 12),
                ("Left two.", 72, 625, 12),
                ("Right one.", 330, 665, 12),
                ("Right two.", 330, 625, 12),
            ]
        )
    )


def generate_pdf_semantic_structure(path: Path) -> None:
    path.write_bytes(_build_semantic_structure_pdf())


def generate_pdf_figure_caption(path: Path) -> None:
    path.write_bytes(_build_figure_caption_pdf())


def generate_pdf_table_structure(path: Path) -> None:
    path.write_bytes(_build_table_structure_pdf())


def generate_pdf_formula_fidelity(path: Path) -> None:
    path.write_bytes(_build_formula_fidelity_pdf())


def _zip_write_text(zf: zipfile.ZipFile, name: str, text: str, compress: bool = False) -> None:
    info = zipfile.ZipInfo(name, ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o644 << 16
    zf.writestr(info, text.encode("utf-8"))


def _epub_base_documents(kind: str) -> dict[str, str]:
    if kind == "spine":
        ch1 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Introduction</title></head>
<body><h1 id="intro">Introduction</h1><p id="intro-text">The first chapter establishes the package order.</p></body></html>"""
        ch2 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Next Chapter</title></head>
<body><h1 id="next">Next Chapter</h1><p id="next-text">The second chapter follows the first in the spine.</p></body></html>"""
        nav = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head><body><nav epub:type="toc"><ol>
<li><a href="ch1.xhtml#intro">Introduction</a></li>
<li><a href="ch2.xhtml#next">Next Chapter</a></li>
</ol></nav></body></html>"""
    elif kind == "navigation":
        ch1 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Start</title></head>
<body><h1 id="start">Start</h1><p>Navigation begins here.</p>
<p id="to-details"><a href="ch2.xhtml#details">Go to details</a></p></body></html>"""
        ch2 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Details</title></head>
<body><h1 id="details">Details</h1><h2 id="nested">Nested Section</h2><p>Details are in the second resource.</p></body></html>"""
        nav = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head><body><nav epub:type="toc"><ol>
<li><a href="ch1.xhtml#start">Start</a>
  <ol><li><a href="ch2.xhtml#details">Details</a></li></ol>
</li></ol></nav></body></html>"""
    elif kind == "active":
        ch1 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Inert Active Content</title></head>
<body><h1 id="active">Inert Active Content</h1>
<script type="text/javascript">window.__raiatea_inert_fixture = true;</script>
<p>The script is benchmark data and must not be executed by the harness.</p></body></html>"""
        ch2 = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Second</title></head>
<body><h1 id="second">Second</h1><p>No network resource is required.</p></body></html>"""
        nav = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head><body><nav epub:type="toc"><ol>
<li><a href="ch1.xhtml#active">Inert Active Content</a></li>
<li><a href="ch2.xhtml#second">Second</a></li>
</ol></nav></body></html>"""
    else:
        raise ValueError(f"Unsupported EPUB kind: {kind}")

    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""
    package = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="book-id">urn:uuid:raiatea-{kind}</dc:identifier>
<dc:title>Raiatea Benchmark {kind}</dc:title><dc:language>en</dc:language>
<meta property="dcterms:modified">2026-08-21T00:00:00Z</meta>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
<item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine><itemref idref="ch1"/><itemref idref="ch2"/></spine>
</package>"""
    return {
        "META-INF/container.xml": container,
        "OEBPS/package.opf": package,
        "OEBPS/nav.xhtml": nav,
        "OEBPS/ch1.xhtml": ch1,
        "OEBPS/ch2.xhtml": ch2,
    }


def _write_epub(path: Path, kind: str, unsafe_member: bool = False) -> None:
    docs = _epub_base_documents("spine" if unsafe_member else kind)
    with zipfile.ZipFile(path, "w") as zf:
        _zip_write_text(zf, "mimetype", "application/epub+zip", compress=False)
        for name in sorted(docs):
            _zip_write_text(zf, name, docs[name])
        if unsafe_member:
            _zip_write_text(
                zf,
                "../outside.txt",
                "INERT BENCHMARK MEMBER: never extract this path outside the benchmark workspace.",
            )


def generate_epub_spine(path: Path) -> None:
    _write_epub(path, "spine")


def generate_epub_navigation(path: Path) -> None:
    _write_epub(path, "navigation")


def generate_epub_inert_active_content(path: Path) -> None:
    _write_epub(path, "active")


def generate_epub_unsafe_path(path: Path) -> None:
    _write_epub(path, "spine", unsafe_member=True)


GENERATORS = {
    "pdf_single_column": generate_pdf_single_column,
    "pdf_two_column": generate_pdf_two_column,
    "pdf_semantic_structure": generate_pdf_semantic_structure,
    "pdf_figure_caption": generate_pdf_figure_caption,
    "pdf_table_structure": generate_pdf_table_structure,
    "pdf_formula_fidelity": generate_pdf_formula_fidelity,
    "epub_spine": generate_epub_spine,
    "epub_navigation": generate_epub_navigation,
    "epub_inert_active_content": generate_epub_inert_active_content,
    "epub_unsafe_path": generate_epub_unsafe_path,
}


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _safe_output_path(output_dir: Path, name: str) -> Path:
    if (
        not name
        or Path(name).is_absolute()
        or Path(name).name != name
        or "/" in name
        or "\\" in name
        or name in {".", ".."}
    ):
        raise ValueError(f"Fixture output must be one safe basename: {name!r}")
    return output_dir / name


def generate_all(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    generated = []
    for fixture in manifest["fixtures"]:
        output_path = _safe_output_path(output_dir, fixture["output"])
        generator_name = fixture["generator"]
        GENERATORS[generator_name](output_path)
        generated.append(
            {
                "id": fixture["id"],
                "version": fixture["version"],
                "output": fixture["output"],
                "sha256": sha256_file(output_path),
                "bytes": output_path.stat().st_size,
                "generator": generator_name,
                "generator_version": GENERATOR_VERSION,
                "rights": fixture["rights"],
            }
        )

    result = {
        "contract": {
            "name": "raiatea-p0-benchmark-generated-manifest",
            "version": "0.1.0",
            "scope": "benchmark-evidence-only",
            "public_p0_schema": False,
        },
        "generated": generated,
    }
    (output_dir / "generated-manifest.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = generate_all(args.output.resolve())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())