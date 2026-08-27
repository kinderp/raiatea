#!/usr/bin/env python3
"""Product-local Poppler pdftohtml parser for PDF1b.

This module is intentionally independent from benchmark routes. It runs only on
a Core-private source copy and emits the closed path-free PopplerObservation
shape. Raw command lines, temporary paths and raw stderr never enter the output.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from typing import Any
import xml.etree.ElementTree as ET
import zlib

from prototype.p0_vs1.poppler_observation_contract import (
    POPPLER_OBSERVATION_VERSION,
    POPPLER_PROFILE,
    encode_poppler_observation_bundle,
    validate_poppler_observation_bundle,
)


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PopplerProductError(ValueError):
    pass


def _sha_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _executable_info(executable: str) -> dict[str, Any]:
    resolved = shutil.which(executable)
    if not resolved:
        raise PopplerProductError(f"provider-executable-unavailable:{executable}")
    path = Path(resolved)
    if not path.is_file():
        raise PopplerProductError(f"provider-executable-not-file:{executable}")
    try:
        completed = subprocess.run(
            [resolved, "-v"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PopplerProductError(f"provider-version-probe-failed:{executable}") from exc
    text = completed.stderr or completed.stdout
    first_line = text.splitlines()[0] if text else ""
    match = re.search(r"\bversion\s+([^\s]+)", first_line)
    if not match:
        raise PopplerProductError(f"provider-version-unrecognized:{executable}")
    return {
        "resolved": resolved,
        "version": match.group(1),
        "sha256": _sha_bytes(path.read_bytes()),
    }


def inspect_poppler_provider(
    pdftohtml_executable: str = "pdftohtml",
    pdfinfo_executable: str = "pdfinfo",
) -> dict[str, Any]:
    html = _executable_info(pdftohtml_executable)
    info = _executable_info(pdfinfo_executable)
    if html["version"] != info["version"]:
        raise PopplerProductError("provider-executable-version-mismatch")
    return {
        "provider_id": "poppler",
        "version": html["version"],
        "executables": {
            "pdftohtml": {"version": html["version"], "sha256": html["sha256"]},
            "pdfinfo": {"version": info["version"], "sha256": info["sha256"]},
        },
        "_pdftohtml": html["resolved"],
        "_pdfinfo": info["resolved"],
    }


def verify_reference_poppler(provider: dict[str, Any]) -> None:
    """Require the exact accepted Ubuntu reference binary set.

    This is the real-provider acceptance policy for PDF1b. It deliberately does
    not claim that another platform/build is equivalent merely because its
    version string matches.
    """
    expected = {
        "version": "24.02.0",
        "pdftohtml": "sha256:70bd5fbb655a14d0b02cb32cb53a601d3b0842a63553a24d1a6a612cf9f0624e",
        "pdfinfo": "sha256:3293dda06d80e1e38dab859aa47368c2876aedc41cbc2e24e8fb9a4e66392078",
    }
    if provider.get("version") != expected["version"]:
        raise PopplerProductError("reference-poppler-version-mismatch")
    executables = provider.get("executables", {})
    if executables.get("pdftohtml", {}).get("sha256") != expected["pdftohtml"]:
        raise PopplerProductError("reference-pdftohtml-fingerprint-mismatch")
    if executables.get("pdfinfo", {}).get("sha256") != expected["pdfinfo"]:
        raise PopplerProductError("reference-pdfinfo-fingerprint-mismatch")


def _failure_status(stderr: str) -> tuple[str, dict[str, Any]]:
    lowered = stderr.casefold()
    if "password" in lowered or "encrypted" in lowered or "permission" in lowered:
        return "restricted", {
            "code": "pdf-access-restriction-signaled",
            "details": "provider signaled password/encryption/access restriction",
        }
    return "failed", {
        "code": "pdftohtml-failed",
        "details": "provider returned a non-zero status",
    }


def _pdfinfo_page_sizes(executable: str, source: Path) -> dict[int, tuple[float, float]]:
    try:
        completed = subprocess.run(
            [executable, "-box", str(source)],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PopplerProductError("pdfinfo-execution-failed") from exc
    if completed.returncode != 0:
        status, _ = _failure_status(completed.stderr)
        if status == "restricted":
            raise PopplerProductError("pdfinfo-access-restricted")
        raise PopplerProductError("pdfinfo-returned-failure")
    page_count_match = re.search(r"^Pages:\s+(\d+)", completed.stdout, re.MULTILINE)
    if not page_count_match:
        raise PopplerProductError("pdfinfo-page-count-missing")
    page_count = int(page_count_match.group(1))
    sizes: dict[int, tuple[float, float]] = {}
    for match in re.finditer(
        r"^Page\s+(\d+)\s+size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        completed.stdout,
        re.MULTILINE,
    ):
        sizes[int(match.group(1)) - 1] = (float(match.group(2)), float(match.group(3)))
    if len(sizes) == page_count:
        return sizes
    generic = re.search(
        r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        completed.stdout,
        re.MULTILINE,
    )
    if generic and page_count == 1:
        return {0: (float(generic.group(1)), float(generic.group(2)))}
    if generic and page_count > 1:
        raise PopplerProductError("pdfinfo-multipage-size-evidence-incomplete")
    raise PopplerProductError("pdfinfo-page-size-evidence-incomplete")


def _convert_bbox(
    left: float,
    top: float,
    right: float,
    bottom: float,
    page_height_points: float,
    scale_x: float,
    scale_y: float,
) -> list[float]:
    return [
        left * scale_x,
        page_height_points - bottom * scale_y,
        right * scale_x,
        page_height_points - top * scale_y,
    ]


def _controlled_asset_path(work: Path, src: str) -> Path:
    root = work.resolve()
    candidate = Path(src)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        if candidate.name != src:
            raise PopplerProductError("image-reference-non-basename")
        resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PopplerProductError("image-reference-outside-workspace") from exc
    return resolved


def _decode_png_rgb8(data: bytes) -> tuple[int, int, bytes]:
    if not data.startswith(PNG_SIGNATURE):
        raise PopplerProductError("image-not-supported-rgb-png")
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
            raise PopplerProductError("image-png-truncated")
        payload = data[payload_start:payload_end]
        pos = payload_end + 4
        if chunk_type == b"IHDR":
            if len(payload) != 13:
                raise PopplerProductError("image-png-invalid-header")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if compression != 0 or filtering != 0:
                raise PopplerProductError("image-png-unsupported-method")
        elif chunk_type == b"IDAT":
            idat.extend(payload)
        elif chunk_type == b"IEND":
            break
    if not width or not height:
        raise PopplerProductError("image-png-missing-header")
    if bit_depth != 8 or color_type != 2 or interlace != 0:
        raise PopplerProductError("image-png-layout-not-rgb8-noninterlaced")
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise PopplerProductError("image-png-deflate-invalid") from exc
    stride = width * 3
    if len(raw) != height * (stride + 1):
        raise PopplerProductError("image-png-inflated-size-invalid")
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
                raise PopplerProductError("image-png-filter-unsupported")
        rows.append(bytes(row))
        previous = row
    return width, height, b"".join(rows)


def _public_provider(provider: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider_id": provider["provider_id"],
        "version": provider["version"],
        "executables": provider["executables"],
    }


def run_poppler_pdf(
    source_bytes: bytes,
    *,
    source_ref_id: str,
    source_fingerprint: str,
    pdftohtml_executable: str = "pdftohtml",
    pdfinfo_executable: str = "pdfinfo",
) -> dict[str, Any]:
    provider = inspect_poppler_provider(pdftohtml_executable, pdfinfo_executable)
    observation: dict[str, Any] = {
        "status": "unknown",
        "warnings": [],
        "pages": [],
        "blocks": [],
        "links": [],
        "figures": [],
        "raw_xml_sha256": None,
    }
    with tempfile.TemporaryDirectory(prefix="raiatea-pdf1b-poppler-") as temporary:
        root = Path(temporary)
        work = root / "work"
        work.mkdir()
        source = root / "source.pdf"
        source.write_bytes(source_bytes)
        output_prefix = work / "out"
        try:
            completed = subprocess.run(
                [
                    provider["_pdftohtml"],
                    "-xml",
                    "-hidden",
                    "-q",
                    str(source),
                    str(output_prefix),
                ],
                cwd=work,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "pdftohtml-timeout", "details": "provider exceeded bounded execution time"}
            )
        except OSError:
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "pdftohtml-execution-failed", "details": "provider process could not be executed"}
            )
        else:
            if completed.returncode != 0:
                status, warning = _failure_status(completed.stderr)
                observation["status"] = status
                observation["warnings"].append(warning)
                observation["warnings"].append(
                    {"code": "provider-returncode", "details": completed.returncode}
                )
            else:
                output = work / "out.xml"
                if not output.is_file():
                    observation["status"] = "failed"
                    observation["warnings"].append(
                        {"code": "pdftohtml-output-missing", "details": None}
                    )
                else:
                    try:
                        sizes = _pdfinfo_page_sizes(provider["_pdfinfo"], source)
                        xml_root = ET.parse(output).getroot()
                    except (PopplerProductError, ET.ParseError):
                        observation["status"] = "failed"
                        observation["warnings"].append(
                            {"code": "poppler-output-map-failed", "details": "page-size or XML evidence invalid"}
                        )
                    else:
                        observation["raw_xml_sha256"] = _sha_bytes(output.read_bytes())
                        block_seq = link_seq = figure_seq = 0
                        for page_index, page in enumerate(xml_root.findall("page")):
                            if page_index not in sizes:
                                observation["status"] = "failed"
                                observation["warnings"].append(
                                    {"code": "physical-page-size-missing", "details": page_index}
                                )
                                break
                            native_width = float(page.attrib["width"])
                            native_height = float(page.attrib["height"])
                            width_points, height_points = sizes[page_index]
                            scale_x = width_points / native_width
                            scale_y = height_points / native_height
                            observation["pages"].append(
                                {
                                    "page_index": page_index,
                                    "width_points": width_points,
                                    "height_points": height_points,
                                }
                            )
                            for node in page.findall("text"):
                                text = " ".join("".join(node.itertext()).split())
                                if not text:
                                    continue
                                left = float(node.attrib["left"])
                                top = float(node.attrib["top"])
                                width = float(node.attrib["width"])
                                height = float(node.attrib["height"])
                                bbox = _convert_bbox(
                                    left,
                                    top,
                                    left + width,
                                    top + height,
                                    height_points,
                                    scale_x,
                                    scale_y,
                                )
                                observation["blocks"].append(
                                    {
                                        "block_id": f"block-{block_seq:08d}",
                                        "text": text,
                                        "page_index": page_index,
                                        "bbox_points_bottom_left": bbox,
                                    }
                                )
                                block_seq += 1
                                for anchor in node.iter("a"):
                                    href = anchor.attrib.get("href")
                                    if not href:
                                        continue
                                    anchor_text = " ".join("".join(anchor.itertext()).split())
                                    observation["links"].append(
                                        {
                                            "link_id": f"link-{link_seq:08d}",
                                            "kind": "uri" if href.startswith(("http://", "https://")) else "other",
                                            "target": href,
                                            "from_text": anchor_text or text,
                                            "page_index": page_index,
                                            "provider_source": "pdftohtml-explicit-anchor",
                                        }
                                    )
                                    link_seq += 1
                            for image in page.findall("image"):
                                src = image.attrib.get("src")
                                if not src:
                                    observation["warnings"].append(
                                        {"code": "image-reference-missing", "details": page_index}
                                    )
                                    continue
                                try:
                                    asset_path = _controlled_asset_path(work, src)
                                except PopplerProductError:
                                    observation["warnings"].append(
                                        {"code": "image-reference-unsafe", "details": page_index}
                                    )
                                    continue
                                if not asset_path.is_file():
                                    observation["warnings"].append(
                                        {"code": "image-output-missing", "details": page_index}
                                    )
                                    continue
                                left = float(image.attrib["left"])
                                top = float(image.attrib["top"])
                                width = float(image.attrib["width"])
                                height = float(image.attrib["height"])
                                bbox = _convert_bbox(
                                    left,
                                    top,
                                    left + width,
                                    top + height,
                                    height_points,
                                    scale_x,
                                    scale_y,
                                )
                                asset = asset_path.read_bytes()
                                figure: dict[str, Any] = {
                                    "provider_ref": f"figure-{figure_seq:08d}",
                                    "provider_source": "pdftohtml-explicit-image-element",
                                    "page_index": page_index,
                                    "bbox_points_bottom_left": bbox,
                                    "asset_sha256": _sha_bytes(asset),
                                    "asset_bytes": len(asset),
                                    "decoded_pixel_sha256": None,
                                    "decode_warning": None,
                                }
                                try:
                                    pixel_width, pixel_height, pixels = _decode_png_rgb8(asset)
                                except PopplerProductError as exc:
                                    figure["decode_warning"] = str(exc)
                                else:
                                    figure["pixel_width"] = pixel_width
                                    figure["pixel_height"] = pixel_height
                                    figure["decoded_pixel_sha256"] = _sha_bytes(pixels)
                                observation["figures"].append(figure)
                                figure_seq += 1
                        else:
                            observation["status"] = "success"

    observation["blocks"].sort(key=lambda row: row["block_id"])
    observation["links"].sort(key=lambda row: row["link_id"])
    observation["figures"].sort(key=lambda row: row["provider_ref"])
    bundle = {
        "bundle_version": POPPLER_OBSERVATION_VERSION,
        "record_kind": "PopplerObservationBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": source_fingerprint,
        "provider": _public_provider(provider),
        "route_profile": POPPLER_PROFILE,
        "observation": observation,
    }
    validate_poppler_observation_bundle(bundle)
    encode_poppler_observation_bundle(bundle)
    return bundle
