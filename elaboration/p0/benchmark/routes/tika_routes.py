"""Benchmark-only Apache Tika B-01 PDF route.

This module executes a local, hash-verified Tika app jar with an explicit
born-digital/no-OCR config and maps XHTML into Provider-neutral observations.
It is evidence tooling, not a production Adapter or public P0 contract.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any
import xml.etree.ElementTree as ET


TIKA_VERSION = "3.3.2"
TIKA_APP_SHA512 = (
    "88c2032cba0d45feea361e6eebd2918bd04707614cdda5d89a1b167da5503c98"
    "e7b4cd368336f0402d559abcaf5006fcc7c825c32c749ae0417ea2f3b8423aba"
)
ROUTE_CONTRACT_VERSION = "0.1.0"


def _contract() -> dict[str, Any]:
    return {
        "name": "raiatea-p0-benchmark-observation",
        "version": ROUTE_CONTRACT_VERSION,
        "scope": "benchmark-evidence-only",
        "public_p0_schema": False,
    }


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def java_version(executable: str = "java") -> dict[str, Any]:
    resolved = shutil.which(executable)
    try:
        completed = subprocess.run(
            [executable, "-version"], check=False, capture_output=True, text=True
        )
    except OSError as exc:
        return {
            "executable": executable,
            "resolved_executable": resolved,
            "version_line": None,
            "returncode": None,
            "error": str(exc),
        }
    version_text = completed.stderr or completed.stdout
    first_line = version_text.splitlines()[0] if version_text else ""
    result: dict[str, Any] = {
        "executable": executable,
        "resolved_executable": resolved,
        "version_line": first_line,
        "returncode": completed.returncode,
        "error": None,
    }
    if resolved:
        path = Path(resolved)
        if path.is_file():
            result["executable_sha256"] = digest_file(path, "sha256")
    return result


def verify_tika_jar(path: Path, expected_sha512: str = TIKA_APP_SHA512) -> dict[str, Any]:
    if not path.is_file():
        return {
            "verified": False,
            "reason": "missing-artifact",
            "expected_sha512": expected_sha512,
            "actual_sha512": None,
            "sha256": None,
            "bytes": None,
        }
    actual = digest_file(path, "sha512")
    return {
        "verified": actual == expected_sha512,
        "reason": None if actual == expected_sha512 else "sha512-mismatch",
        "expected_sha512": expected_sha512,
        "actual_sha512": actual,
        "sha256": digest_file(path, "sha256"),
        "bytes": path.stat().st_size,
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _class_tokens(element: ET.Element) -> set[str]:
    return set(element.attrib.get("class", "").split())


def _clean_text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def map_tika_xhtml(xhtml: bytes | str) -> dict[str, Any]:
    """Map Tika XHTML conservatively into benchmark observations.

    Only explicit XHTML semantics are promoted. No bbox/page geometry is
    invented. Page identity is recorded only if Tika emits an explicit page
    container/marker that can be observed in the XHTML.
    """
    data = xhtml.encode("utf-8") if isinstance(xhtml, str) else xhtml
    root = ET.fromstring(data)
    observation: dict[str, Any] = {
        "blocks": [],
        "metadata": {},
        "pages_observed": [],
        "page_structure_observed": False,
        "bbox_structure_observed": False,
    }

    for element in root.iter():
        if _local_name(element.tag) == "meta":
            name = element.attrib.get("name") or element.attrib.get("property")
            content = element.attrib.get("content")
            if name and content is not None:
                observation["metadata"].setdefault(name, []).append(content)

    page_counter = 0

    def walk(element: ET.Element, current_page: int | None = None) -> None:
        nonlocal page_counter
        tag = _local_name(element.tag)
        classes = _class_tokens(element)
        local_page = current_page
        if tag == "div" and (
            "page" in classes
            or "page-content" in classes
            or any(token.startswith("page-") for token in classes)
        ):
            local_page = page_counter
            observation["pages_observed"].append(
                {
                    "page_index": page_counter,
                    "tag": tag,
                    "class": element.attrib.get("class", ""),
                }
            )
            observation["page_structure_observed"] = True
            page_counter += 1

        semantic_type: str | None = None
        level: int | None = None
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            semantic_type = "heading"
            level = int(tag[1])
        elif tag == "p":
            semantic_type = "paragraph"
        elif tag == "pre":
            semantic_type = "code"
        elif tag == "li":
            semantic_type = "list-item"

        if semantic_type is not None:
            text = _clean_text(element)
            if text:
                observation["blocks"].append(
                    {
                        "type": "text-block",
                        "semantic_type": semantic_type,
                        "semantic_level": level,
                        "text": text,
                        "page_index": local_page,
                        "bbox_points_bottom_left": None,
                        "xhtml_tag": tag,
                        "xhtml_class": element.attrib.get("class", ""),
                        "xhtml_id": element.attrib.get("id"),
                    }
                )

        for child in list(element):
            walk(child, local_page)

    walk(root)
    return observation


def run_tika_pdf_xhtml(
    source: Path,
    jar_path: Path,
    config_path: Path,
    java_executable: str = "java",
) -> dict[str, Any]:
    started = time.perf_counter()
    observation: dict[str, Any] = {
        "contract": _contract(),
        "route": "tika-app-3.3.2-xhtml",
        "status": "unknown",
        "warnings": [],
        "blocks": [],
        "metadata": {},
        "pages_observed": [],
        "page_structure_observed": False,
        "bbox_structure_observed": False,
        "ocr_policy": "explicit-no-ocr",
        "network_instrumentation": "not-measured",
        "os_level_sandbox": False,
    }

    jar_evidence = verify_tika_jar(jar_path)
    observation["tika_artifact"] = jar_evidence
    if not jar_evidence["verified"]:
        observation["status"] = "blocked"
        observation["warnings"].append(
            {"code": "tika-artifact-verification-failed", "details": jar_evidence}
        )
        observation["duration_seconds"] = round(time.perf_counter() - started, 9)
        return observation

    if not config_path.is_file():
        observation["status"] = "blocked"
        observation["warnings"].append(
            {"code": "tika-config-missing", "details": str(config_path)}
        )
        observation["duration_seconds"] = round(time.perf_counter() - started, 9)
        return observation

    java_info = java_version(java_executable)
    observation["java"] = java_info
    if java_info["returncode"] != 0:
        observation["status"] = "not-measured"
        observation["warnings"].append(
            {"code": "java-unavailable", "details": java_info.get("error")}
        )
        observation["duration_seconds"] = round(time.perf_counter() - started, 9)
        return observation

    with tempfile.TemporaryDirectory(prefix="raiatea-tika-") as tmp:
        root = Path(tmp)
        input_dir = root / "input"
        work = root / "work"
        java_tmp = root / "java-tmp"
        input_dir.mkdir()
        work.mkdir()
        java_tmp.mkdir()
        local_input = input_dir / source.name
        shutil.copyfile(source, local_input)

        baseline = {
            str(candidate.relative_to(root))
            for candidate in root.rglob("*")
            if candidate.is_file()
        }
        command = [
            java_executable,
            f"-Djava.io.tmpdir={java_tmp}",
            "-jar",
            str(jar_path.resolve()),
            f"--config={config_path.resolve()}",
            "-x",
            str(local_input),
        ]
        completed = subprocess.run(
            command, cwd=work, check=False, capture_output=True
        )
        current = {
            str(candidate.relative_to(root))
            for candidate in root.rglob("*")
            if candidate.is_file()
        }
        observation["side_effect_files"] = sorted(current - baseline)
        observation["command_options"] = [
            "-Djava.io.tmpdir=<controlled>",
            "-jar",
            "<verified-tika-app-3.3.2.jar>",
            "--config=<pinned-no-ocr-config>",
            "-x",
            "<local-fixture.pdf>",
        ]
        observation["returncode"] = completed.returncode
        observation["stderr"] = completed.stderr.decode("utf-8", errors="replace").strip()
        observation["raw_output_sha256"] = hashlib.sha256(completed.stdout).hexdigest()
        observation["raw_output_bytes"] = len(completed.stdout)

        if completed.returncode != 0:
            observation["status"] = "failed"
            observation["warnings"].append(
                {
                    "code": "tika-nonzero-exit",
                    "details": observation["stderr"],
                }
            )
            observation["duration_seconds"] = round(time.perf_counter() - started, 9)
            return observation

        try:
            mapped = map_tika_xhtml(completed.stdout)
        except ET.ParseError as exc:
            observation["status"] = "failed"
            observation["warnings"].append(
                {"code": "tika-invalid-xhtml", "details": str(exc)}
            )
            observation["duration_seconds"] = round(time.perf_counter() - started, 9)
            return observation

        observation.update(mapped)
        observation["status"] = "success"
        if not observation["page_structure_observed"]:
            observation["warnings"].append(
                {
                    "code": "page-identity-not-exposed",
                    "details": "Measured Tika XHTML did not expose an explicit page container recognized by the benchmark mapper.",
                }
            )
        if not observation["bbox_structure_observed"]:
            observation["warnings"].append(
                {
                    "code": "bbox-not-exposed",
                    "details": "Measured Tika XHTML did not expose source geometry recognized by the benchmark mapper.",
                }
            )

    observation["duration_seconds"] = round(time.perf_counter() - started, 9)
    return observation
