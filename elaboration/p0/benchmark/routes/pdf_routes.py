"""Benchmark-only Poppler B-01 PDF control routes.

These routes produce Provider-neutral benchmark observations. They are evidence
tooling, not production Adapters and not Raiatea's public P0 schema.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any, Callable
import xml.etree.ElementTree as ET


ROUTE_CONTRACT_VERSION = "0.1.0"
XHTML_NS = "http://www.w3.org/1999/xhtml"


def _contract() -> dict[str, Any]:
    return {
        "name": "raiatea-p0-benchmark-observation",
        "version": ROUTE_CONTRACT_VERSION,
        "scope": "benchmark-evidence-only",
        "public_p0_schema": False,
    }


def executable_version(executable: str) -> dict[str, Any]:
    """Capture Poppler-style executable version/path/hash without raising."""
    resolved = shutil.which(executable)
    try:
        completed = subprocess.run(
            [executable, "-v"], check=False, capture_output=True, text=True
        )
    except OSError as exc:
        return {
            "executable": executable,
            "resolved_executable": resolved,
            "version": None,
            "first_line": "",
            "returncode": None,
            "error": str(exc),
        }

    version_text = completed.stderr or completed.stdout
    first_line = version_text.splitlines()[0] if version_text else ""
    match = re.search(r"\bversion\s+([^\s]+)", first_line)
    result: dict[str, Any] = {
        "executable": executable,
        "resolved_executable": resolved,
        "version": match.group(1) if match else None,
        "first_line": first_line,
        "returncode": completed.returncode,
        "error": None,
    }
    if resolved:
        path = Path(resolved)
        if path.is_file():
            result["executable_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _controlled_run(
    source: Path,
    executable: str,
    build_args: Callable[[Path, Path], list[str]],
) -> tuple[Path | None, dict[str, Any]]:
    """Run a local CLI in a controlled temporary input/work parent.

    Files created inside ``work`` are route outputs and are recorded. Any new
    file elsewhere under the controlled parent is reported as a side effect.
    This is observability, not an OS-level sandbox claim.
    """
    started = time.perf_counter()
    temp = tempfile.TemporaryDirectory(prefix="raiatea-poppler-")
    root = Path(temp.name)
    input_dir = root / "input"
    work = root / "work"
    input_dir.mkdir()
    work.mkdir()
    local_input = input_dir / source.name
    shutil.copyfile(source, local_input)

    baseline = {
        str(candidate.relative_to(root))
        for candidate in root.rglob("*")
        if candidate.is_file()
    }
    command = [executable, *build_args(local_input, work)]
    try:
        completed = subprocess.run(
            command, cwd=work, check=False, capture_output=True, text=True
        )
    except OSError as exc:
        temp.cleanup()
        return None, {
            "status": "not-measured",
            "warnings": [{"code": "route-unavailable", "details": str(exc)}],
            "duration_seconds": round(time.perf_counter() - started, 9),
            "command_options": command[1:],
            "generated_files": [],
            "side_effect_files": [],
            "controlled_parent": True,
            "os_level_sandbox": False,
            "network_instrumentation": "not-measured",
        }

    current = {
        str(candidate.relative_to(root))
        for candidate in root.rglob("*")
        if candidate.is_file()
    }
    generated = sorted(
        str(candidate.relative_to(work))
        for candidate in work.rglob("*")
        if candidate.is_file()
    )
    expected_under_work = {f"work/{name}" for name in generated}
    side_effects = sorted(current - baseline - expected_under_work)
    metadata = {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_seconds": round(time.perf_counter() - started, 9),
        "command_options": command[1:],
        "generated_files": generated,
        "side_effect_files": side_effects,
        "controlled_parent": True,
        "os_level_sandbox": False,
        "network_instrumentation": "not-measured",
        "_temporary_directory": temp,
    }
    return work, metadata


def _cleanup(metadata: dict[str, Any]) -> None:
    temp = metadata.pop("_temporary_directory", None)
    if temp is not None:
        temp.cleanup()


def _xhtml(tag: str) -> str:
    return f"{{{XHTML_NS}}}{tag}"


def _convert_top_left_bbox(
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    page_height_points: float,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> list[float]:
    """Map a top-left box to PDF-style bottom-left page points."""
    return [
        x_min * scale_x,
        page_height_points - y_max * scale_y,
        x_max * scale_x,
        page_height_points - y_min * scale_y,
    ]


def _raw_metadata(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_output_bytes": len(raw),
    }


def run_pdftotext_bbox_layout(
    source: Path, executable: str = "pdftotext"
) -> dict[str, Any]:
    """Run ``pdftotext -bbox-layout`` and map its XHTML blocks."""

    def args(local_input: Path, work: Path) -> list[str]:
        return ["-bbox-layout", str(local_input), str(work / "bbox.html")]

    work, metadata = _controlled_run(source, executable, args)
    observation: dict[str, Any] = {
        "contract": _contract(),
        "route": "pdftotext-bbox-layout",
        "status": "unknown",
        "warnings": [],
        "pages": [],
        "blocks": [],
        "native_coordinate_system": "top-left-points",
        "mapped_coordinate_system": "bottom-left-points",
    }
    if work is None:
        observation.update(metadata)
        return observation

    try:
        observation.update({key: value for key, value in metadata.items() if not key.startswith("_")})
        output = work / "bbox.html"
        if metadata["returncode"] != 0 or not output.is_file():
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "pdftotext-failure", "details": metadata["stderr"].strip()}
            )
            return observation

        observation.update(_raw_metadata(output))
        try:
            root = ET.parse(output).getroot()
        except ET.ParseError as exc:
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "invalid-bbox-xhtml", "details": str(exc)}
            )
            return observation

        for page_index, page in enumerate(root.iter(_xhtml("page"))):
            width = float(page.attrib["width"])
            height = float(page.attrib["height"])
            observation["pages"].append(
                {
                    "page_index": page_index,
                    "width_points": width,
                    "height_points": height,
                    "native_origin": "top-left",
                    "native_units": "points",
                }
            )
            for block in page.iter(_xhtml("block")):
                words = [
                    "".join(word.itertext()).strip()
                    for word in block.iter(_xhtml("word"))
                ]
                text = " ".join(word for word in words if word)
                if not text:
                    continue
                native = [
                    float(block.attrib[key])
                    for key in ("xMin", "yMin", "xMax", "yMax")
                ]
                observation["blocks"].append(
                    {
                        "type": "text-block",
                        "text": text,
                        "page_index": page_index,
                        "native_bbox": native,
                        "bbox_points_bottom_left": _convert_top_left_bbox(
                            *native, height
                        ),
                    }
                )
        observation["status"] = "success"
        return observation
    finally:
        _cleanup(metadata)


def _pdfinfo_page_sizes(source: Path, executable: str = "pdfinfo") -> dict[int, tuple[float, float]]:
    """Read physical page sizes in points using Poppler pdfinfo.

    The function requests all pages in one call. Current E-04c fixtures are
    one-page documents, but parsing supports both ``Page size`` and per-page
    ``Page N size`` forms.
    """
    try:
        completed = subprocess.run(
            [executable, "-box", str(source)], check=False, capture_output=True, text=True
        )
    except OSError as exc:
        raise ValueError(f"pdfinfo unavailable: {exc}") from exc
    if completed.returncode != 0:
        raise ValueError(f"pdfinfo failed: {completed.stderr.strip()}")

    page_count_match = re.search(r"^Pages:\s+(\d+)", completed.stdout, re.MULTILINE)
    if not page_count_match:
        raise ValueError("pdfinfo output has no page count")
    page_count = int(page_count_match.group(1))

    generic = re.search(
        r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        completed.stdout,
        re.MULTILINE,
    )
    if generic:
        size = (float(generic.group(1)), float(generic.group(2)))
        return {index: size for index in range(page_count)}

    sizes: dict[int, tuple[float, float]] = {}
    for match in re.finditer(
        r"^Page\s+(\d+)\s+size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        completed.stdout,
        re.MULTILINE,
    ):
        sizes[int(match.group(1)) - 1] = (float(match.group(2)), float(match.group(3)))
    if len(sizes) != page_count:
        raise ValueError("pdfinfo page-size evidence is incomplete")
    return sizes


def run_pdftohtml_xml(
    source: Path,
    executable: str = "pdftohtml",
    pdfinfo_executable: str = "pdfinfo",
) -> dict[str, Any]:
    """Run ``pdftohtml -xml -hidden`` and map text boxes to PDF points."""

    def args(local_input: Path, work: Path) -> list[str]:
        return ["-xml", "-hidden", "-nodrm", "-q", str(local_input), str(work / "out")]

    work, metadata = _controlled_run(source, executable, args)
    observation: dict[str, Any] = {
        "contract": _contract(),
        "route": "pdftohtml-xml",
        "status": "unknown",
        "warnings": [],
        "pages": [],
        "blocks": [],
        "native_coordinate_system": "top-left-scaled-canvas",
        "mapped_coordinate_system": "bottom-left-points",
    }
    if work is None:
        observation.update(metadata)
        return observation

    try:
        observation.update({key: value for key, value in metadata.items() if not key.startswith("_")})
        output = work / "out.xml"
        if metadata["returncode"] != 0 or not output.is_file():
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "pdftohtml-failure", "details": metadata["stderr"].strip()}
            )
            return observation

        observation.update(_raw_metadata(output))
        try:
            root = ET.parse(output).getroot()
        except ET.ParseError as exc:
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "invalid-pdf2xml", "details": str(exc)}
            )
            return observation

        # Query the copied input inside the controlled parent, not the caller's
        # path. pdftohtml native canvas dimensions are scaled relative to the
        # physical PDF page size; pdfinfo supplies the conversion target.
        local_input = Path(metadata["command_options"][-2])
        try:
            physical_sizes = _pdfinfo_page_sizes(local_input, pdfinfo_executable)
        except ValueError as exc:
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "pdfinfo-page-size-failure", "details": str(exc)}
            )
            return observation

        for page_index, page in enumerate(root.findall("page")):
            native_width = float(page.attrib["width"])
            native_height = float(page.attrib["height"])
            if page_index not in physical_sizes:
                observation["status"] = "failed"
                observation["warnings"].append(
                    {"code": "missing-physical-page-size", "details": page_index}
                )
                return observation
            width_points, height_points = physical_sizes[page_index]
            scale_x = width_points / native_width
            scale_y = height_points / native_height
            observation["pages"].append(
                {
                    "page_index": page_index,
                    "native_width": native_width,
                    "native_height": native_height,
                    "native_origin": "top-left",
                    "mapped_width_points": width_points,
                    "mapped_height_points": height_points,
                    "scale_to_points_x": scale_x,
                    "scale_to_points_y": scale_y,
                }
            )
            for text_node in page.findall("text"):
                text = " ".join("".join(text_node.itertext()).split())
                if not text:
                    continue
                left = float(text_node.attrib["left"])
                top = float(text_node.attrib["top"])
                width = float(text_node.attrib["width"])
                height = float(text_node.attrib["height"])
                native = [left, top, left + width, top + height]
                observation["blocks"].append(
                    {
                        "type": "text-block",
                        "text": text,
                        "page_index": page_index,
                        "native_bbox": native,
                        "bbox_points_bottom_left": _convert_top_left_bbox(
                            *native,
                            height_points,
                            scale_x,
                            scale_y,
                        ),
                    }
                )
        observation["status"] = "success"
        return observation
    finally:
        _cleanup(metadata)
