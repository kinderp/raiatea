"""Explicit Poppler image evidence for B01-PDF-004.

The existing pdftohtml text route records generated image filenames but cleans
its temporary workspace after mapping. This bounded helper re-runs the same
pinned pdftohtml route so the explicit ``<image>`` element and generated PNG can
be inspected before cleanup. It is benchmark evidence, not a production API.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from typing import Any
import xml.etree.ElementTree as ET
import zlib

from pdf_routes import _convert_top_left_bbox, _pdfinfo_page_sizes


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def decode_png_rgb8(data: bytes) -> tuple[int, int, bytes]:
    """Decode non-interlaced 8-bit RGB PNG pixels using only the stdlib."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not-png")
    pos = len(PNG_SIGNATURE)
    width = height = None
    bit_depth = color_type = interlace = None
    idat = bytearray()
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        payload_start = pos + 8
        payload_end = payload_start + length
        if payload_end + 4 > len(data):
            raise ValueError("truncated-png-chunk")
        payload = data[payload_start:payload_end]
        pos = payload_end + 4
        if chunk_type == b"IHDR":
            if len(payload) != 13:
                raise ValueError("invalid-ihdr")
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if compression != 0 or filter_method != 0:
                raise ValueError("unsupported-png-method")
        elif chunk_type == b"IDAT":
            idat.extend(payload)
        elif chunk_type == b"IEND":
            break

    if not width or not height:
        raise ValueError("missing-ihdr")
    if bit_depth != 8 or color_type != 2 or interlace != 0:
        raise ValueError(
            f"unsupported-png-layout:bit-depth={bit_depth},color-type={color_type},interlace={interlace}"
        )

    raw = zlib.decompress(bytes(idat))
    stride = width * 3
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise ValueError(f"unexpected-inflated-size:{len(raw)}!={expected}")

    rows: list[bytes] = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        row = bytearray(raw[offset + 1 : offset + 1 + stride])
        offset += stride + 1
        for index in range(stride):
            left = row[index - 3] if index >= 3 else 0
            up = previous[index]
            up_left = previous[index - 3] if index >= 3 else 0
            if filter_type == 0:
                pass
            elif filter_type == 1:
                row[index] = (row[index] + left) & 0xFF
            elif filter_type == 2:
                row[index] = (row[index] + up) & 0xFF
            elif filter_type == 3:
                row[index] = (row[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                predictor = left + up - up_left
                pa = abs(predictor - left)
                pb = abs(predictor - up)
                pc = abs(predictor - up_left)
                best = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                row[index] = (row[index] + best) & 0xFF
            else:
                raise ValueError(f"unsupported-png-filter:{filter_type}")
        rows.append(bytes(row))
        previous = row
    return width, height, b"".join(rows)


def controlled_asset_path(work: Path, src: str) -> Path:
    """Resolve a pdftohtml asset ref only when it stays inside the work root.

    Poppler may emit either an absolute path under the supplied output prefix or
    a relative basename. Both are acceptable only after canonical containment is
    proven; traversal and external absolute paths fail closed.
    """
    work_root = work.resolve()
    candidate = Path(src)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        if candidate.name != src:
            raise ValueError("non-basename-relative-reference")
        resolved = (work_root / candidate).resolve()
    try:
        resolved.relative_to(work_root)
    except ValueError as exc:
        raise ValueError("asset-reference-outside-work-root") from exc
    return resolved


def run_pdftohtml_figure_evidence(
    source: Path,
    executable: str = "pdftohtml",
    pdfinfo_executable: str = "pdfinfo",
) -> dict[str, Any]:
    """Return explicit pdftohtml image records with decoded pixel evidence."""
    with tempfile.TemporaryDirectory(prefix="raiatea-poppler-figure-") as tmp:
        root = Path(tmp)
        input_dir = root / "input"
        work = root / "work"
        input_dir.mkdir()
        work.mkdir()
        local_input = input_dir / source.name
        shutil.copyfile(source, local_input)
        command = [
            executable,
            "-xml",
            "-hidden",
            "-q",
            str(local_input),
            str(work / "out"),
        ]
        completed = subprocess.run(
            command, cwd=work, check=False, capture_output=True, text=True
        )
        result: dict[str, Any] = {
            "route": "pdftohtml-xml-explicit-image-evidence",
            "status": "unknown",
            "warnings": [],
            "figures": [],
            "figure_caption_relations": None,
            "command_options": ["-xml", "-hidden", "-q", "<local-fixture.pdf>", "<controlled-output-prefix>"],
            "association_policy": "no relation inferred from spatial proximity",
        }
        output = work / "out.xml"
        if completed.returncode != 0 or not output.is_file():
            result["status"] = "failed"
            result["warnings"].append(
                {"code": "pdftohtml-failure", "details": completed.stderr.strip()}
            )
            return result

        try:
            physical_sizes = _pdfinfo_page_sizes(local_input, pdfinfo_executable)
            xml_root = ET.parse(output).getroot()
        except (ValueError, ET.ParseError) as exc:
            result["status"] = "failed"
            result["warnings"].append(
                {"code": "poppler-figure-map-failure", "details": str(exc)}
            )
            return result

        for page_index, page in enumerate(xml_root.findall("page")):
            native_width = float(page.attrib["width"])
            native_height = float(page.attrib["height"])
            if page_index not in physical_sizes:
                result["status"] = "failed"
                result["warnings"].append(
                    {"code": "missing-physical-page-size", "details": page_index}
                )
                return result
            width_points, height_points = physical_sizes[page_index]
            scale_x = width_points / native_width
            scale_y = height_points / native_height
            for image_index, image in enumerate(page.findall("image")):
                src = image.attrib.get("src")
                if not src:
                    result["warnings"].append(
                        {"code": "missing-image-reference", "details": None}
                    )
                    continue
                try:
                    asset_path = controlled_asset_path(work, src)
                except ValueError as exc:
                    result["warnings"].append(
                        {
                            "code": "unsafe-image-reference",
                            "details": {"src": src, "reason": str(exc)},
                        }
                    )
                    continue
                if not asset_path.is_file():
                    result["warnings"].append(
                        {"code": "missing-generated-image", "details": src}
                    )
                    continue
                left = float(image.attrib["left"])
                top = float(image.attrib["top"])
                width = float(image.attrib["width"])
                height = float(image.attrib["height"])
                native_bbox = [left, top, left + width, top + height]
                asset = asset_path.read_bytes()
                figure: dict[str, Any] = {
                    "provider_ref": f"page-{page_index}-image-{image_index}",
                    "provider_source": "pdftohtml-explicit-image-element",
                    "page_index": page_index,
                    "native_bbox": native_bbox,
                    "bbox_points_bottom_left": _convert_top_left_bbox(
                        *native_bbox, height_points, scale_x, scale_y
                    ),
                    "asset_name": asset_path.name,
                    "asset_sha256": hashlib.sha256(asset).hexdigest(),
                    "asset_bytes": len(asset),
                }
                try:
                    pixel_width, pixel_height, pixels = decode_png_rgb8(asset)
                except ValueError as exc:
                    figure["decoded_pixel_sha256"] = None
                    figure["decode_warning"] = str(exc)
                else:
                    figure["pixel_width"] = pixel_width
                    figure["pixel_height"] = pixel_height
                    figure["decoded_pixel_sha256"] = hashlib.sha256(pixels).hexdigest()
                result["figures"].append(figure)

        result["raw_xml_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
        result["status"] = "success"
        return result
