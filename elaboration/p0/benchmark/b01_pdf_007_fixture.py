#!/usr/bin/env python3
"""Deterministic B01-PDF-007 mixed/defective native-text fixture.

This fixture intentionally contains useful native PDF text plus one raster-only
visible text region. The raster words do not exist in the PDF text layer. It is
benchmark evidence for native-vs-OCR routing, not a production PDF generator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FIXTURE_ID = "B01-PDF-007"
FIXTURE_VERSION = "0.1.0"
GENERATOR_VERSION = "0.1.0"
RASTER_TEXT = "OCR TARGET 2026"
RASTER_SCALE = 6
RASTER_DISPLAY_BBOX = [72.0, 540.0, 489.0, 585.0]
EXPECTED_PDF_SHA256 = "4ed576898177b66cc7e187fbf791f32d4721a30c890ee429fad54949f53a59f0"
EXPECTED_PIXEL_SHA256 = "9b86156aecfab15d577faee643ef1eaa04b9a565bf37f5db79b7f9090a9bdec3"

# Seven-by-nine authored bitmap glyphs. Only the characters needed by the
# benchmark phrase are defined; no external font or rendering library is used.
_GLYPHS = {
    "O": ["0111110", "1100011", "1100011", "1100011", "1100011", "1100011", "1100011", "1100011", "0111110"],
    "C": ["0111111", "1100000", "1100000", "1100000", "1100000", "1100000", "1100000", "1100000", "0111111"],
    "R": ["1111110", "1100011", "1100011", "1100011", "1111110", "1101100", "1100110", "1100011", "1100011"],
    "T": ["1111111", "0011100", "0011100", "0011100", "0011100", "0011100", "0011100", "0011100", "0011100"],
    "A": ["0011100", "0110110", "1100011", "1100011", "1111111", "1100011", "1100011", "1100011", "1100011"],
    "G": ["0111111", "1100000", "1100000", "1100000", "1101111", "1100011", "1100011", "1100011", "0111110"],
    "E": ["1111111", "1100000", "1100000", "1100000", "1111110", "1100000", "1100000", "1100000", "1111111"],
    "2": ["0111110", "1100011", "0000011", "0000110", "0001100", "0011000", "0110000", "1100000", "1111111"],
    "0": ["0111110", "1100011", "1100111", "1101011", "1110011", "1100011", "1100011", "1100011", "0111110"],
    "6": ["0011110", "0110000", "1100000", "1100000", "1111110", "1100011", "1100011", "1100011", "0111110"],
    " ": ["0000000"] * 9,
}


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _text_cmd(text: str, x: int, y: int, size: int = 12) -> str:
    return f"BT /F1 {size} Tf 1 0 0 1 {x} {y} Tm ({_pdf_escape(text)}) Tj ET\n"


def raster_pixels() -> tuple[int, int, bytes]:
    char_width = 7
    char_height = 9
    gap = 2
    margin = 3
    width = (
        margin * 2
        + len(RASTER_TEXT) * char_width
        + (len(RASTER_TEXT) - 1) * gap
    ) * RASTER_SCALE
    height = (margin * 2 + char_height) * RASTER_SCALE
    pixels = bytearray([255]) * (width * height)

    x_cell = margin
    for character in RASTER_TEXT:
        pattern = _GLYPHS[character]
        for row_index, row in enumerate(pattern):
            for column_index, value in enumerate(row):
                if value != "1":
                    continue
                for dy in range(RASTER_SCALE):
                    y = (margin + row_index) * RASTER_SCALE + dy
                    start = y * width + (x_cell + column_index) * RASTER_SCALE
                    pixels[start : start + RASTER_SCALE] = b"\x00" * RASTER_SCALE
        x_cell += char_width + gap

    return width, height, bytes(pixels)


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


def build_fixture() -> bytes:
    width, height, pixels = raster_pixels()
    stream = (
        _text_cmd("Raiatea B01 PDF 007", 72, 730, 20)
        + _text_cmd("Native text before the raster-only region.", 72, 665, 12)
        + "q 417 0 0 45 72 540 cm /Im1 Do Q\n"
        + _text_cmd("Native text after the raster-only region.", 72, 480, 12)
    ).encode("ascii")

    image = (
        b"<< /Type /XObject /Subtype /Image /Width "
        + str(width).encode("ascii")
        + b" /Height "
        + str(height).encode("ascii")
        + b" /ColorSpace /DeviceGray /BitsPerComponent 8 /Length "
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
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"endstream",
    ]
    return _serialize_pdf_objects(objects)


def evidence() -> dict[str, object]:
    pdf = build_fixture()
    width, height, pixels = raster_pixels()
    return {
        "fixture_id": FIXTURE_ID,
        "fixture_version": FIXTURE_VERSION,
        "generator_version": GENERATOR_VERSION,
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "pdf_bytes": len(pdf),
        "raster_text": RASTER_TEXT,
        "raster_pixel_width": width,
        "raster_pixel_height": height,
        "raster_pixel_sha256": hashlib.sha256(pixels).hexdigest(),
        "raster_display_bbox_points_bottom_left": RASTER_DISPLAY_BBOX,
        "raster_words_present_in_pdf_text_layer": RASTER_TEXT.encode("ascii") in pdf,
        "rights": {
            "redistribution": "not-established",
            "decision_issue": 131,
            "public_rights_safe": False,
            "remote_provider": "denied",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(build_fixture())
    payload = evidence()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
