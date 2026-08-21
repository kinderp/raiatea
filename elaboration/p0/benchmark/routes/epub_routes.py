"""Benchmark-only B-02 EPUB routes.

These routes produce Provider-neutral benchmark observations. They are evidence
tooling, not production Adapters and not Raiatea's public P0 schema.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


ROUTE_CONTRACT_VERSION = "0.1.0"
OPF_NS = {"opf": "http://www.idpf.org/2007/opf"}
CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}


def _contract() -> dict[str, Any]:
    return {
        "name": "raiatea-p0-benchmark-observation",
        "version": ROUTE_CONTRACT_VERSION,
        "scope": "benchmark-evidence-only",
        "public_p0_schema": False,
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean_text(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _unsafe_member_reason(name: str) -> str | None:
    if not name:
        return "empty-name"
    if "\x00" in name:
        return "nul-byte"
    if "\\" in name:
        return "backslash-path"
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return "absolute-path"
    if ".." in PurePosixPath(name).parts:
        return "parent-traversal"
    return None


def _resolve_member(package_dir: str, href: str) -> str:
    if "\\" in href:
        raise ValueError(f"Unsafe backslash path in EPUB href: {href!r}")
    if href.startswith("/") or re.match(r"^[A-Za-z]:", href):
        raise ValueError(f"Unsafe absolute EPUB href: {href!r}")
    path_part = href.split("#", 1)[0]
    resolved = posixpath.normpath(posixpath.join(package_dir, path_part))
    reason = _unsafe_member_reason(resolved)
    if reason:
        raise ValueError(f"Unsafe resolved EPUB member {resolved!r}: {reason}")
    return resolved


def _parse_link_target(package_dir: str, target: str) -> tuple[str | None, str | None]:
    resource_part, _, fragment = target.partition("#")
    if not resource_part:
        return None, fragment or None
    return _resolve_member(package_dir, resource_part), fragment or None


def _read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    if name not in zf.namelist():
        raise ValueError(f"Missing required EPUB resource: {name}")
    return ET.fromstring(zf.read(name))


def parse_direct_epub(path: Path) -> dict[str, Any]:
    """Parse an EPUB without extracting members or executing active content."""
    started = time.perf_counter()
    observation: dict[str, Any] = {
        "contract": _contract(),
        "route": "direct-epub-stdlib",
        "status": "unknown",
        "warnings": [],
        "spine": [],
        "resources": [],
        "blocks": [],
        "navigation": [],
        "links": [],
        "active_content": [],
    }

    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            unsafe = [
                {"member": name, "reason": reason}
                for name in names
                if (reason := _unsafe_member_reason(name))
            ]
            if unsafe:
                observation["status"] = "rejected"
                observation["warnings"].append(
                    {"code": "unsafe-package-member", "details": unsafe}
                )
                return _finalize_observation(observation, started)

            if not names or names[0] != "mimetype":
                observation["warnings"].append(
                    {"code": "epub-mimetype-not-first", "details": names[:1]}
                )
            if "mimetype" not in names or zf.read("mimetype") != b"application/epub+zip":
                raise ValueError("Invalid or missing EPUB mimetype")

            container = _read_xml(zf, "META-INF/container.xml")
            rootfile = container.find(".//c:rootfile", CONTAINER_NS)
            if rootfile is None:
                raise ValueError("EPUB container has no rootfile")
            package_path = rootfile.attrib.get("full-path", "")
            if _unsafe_member_reason(package_path):
                raise ValueError(f"Unsafe package path: {package_path!r}")
            package_dir = posixpath.dirname(package_path)

            package = _read_xml(zf, package_path)
            manifest: dict[str, dict[str, str]] = {}
            for item in package.findall(".//opf:manifest/opf:item", OPF_NS):
                item_id = item.attrib.get("id", "")
                href = item.attrib.get("href", "")
                if not item_id or not href:
                    continue
                manifest[item_id] = {
                    "href": href,
                    "properties": item.attrib.get("properties", ""),
                    "media_type": item.attrib.get("media-type", ""),
                }

            spine_ids = [
                item.attrib.get("idref", "")
                for item in package.findall(".//opf:spine/opf:itemref", OPF_NS)
                if item.attrib.get("idref")
            ]
            observation["spine"] = spine_ids

            for item_id in spine_ids:
                if item_id not in manifest:
                    raise ValueError(f"Spine references missing manifest item: {item_id}")
                item = manifest[item_id]
                member = _resolve_member(package_dir, item["href"])
                observation["resources"].append(
                    {"id": item_id, "resource": member, "media_type": item["media_type"]}
                )
                root = _read_xml(zf, member)
                _collect_xhtml_observations(root, member, observation)

            nav_items = [
                item
                for item in manifest.values()
                if "nav" in item["properties"].split()
            ]
            for item in nav_items:
                member = _resolve_member(package_dir, item["href"])
                nav_root = _read_xml(zf, member)
                for anchor in nav_root.iter():
                    if _local_name(anchor.tag) != "a":
                        continue
                    href = anchor.attrib.get("href")
                    if not href:
                        continue
                    resource, fragment = _parse_link_target(package_dir, href)
                    observation["navigation"].append(
                        {
                            "label": _clean_text(anchor),
                            "resource": resource,
                            "fragment": fragment,
                            "raw_target": href,
                        }
                    )

            if observation["active_content"]:
                observation["warnings"].append(
                    {"code": "active-content-present", "details": observation["active_content"]}
                )
                observation["status"] = "degraded"
            else:
                observation["status"] = "success"

    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile) as exc:
        observation["status"] = "failed"
        observation["warnings"].append(
            {"code": "direct-epub-failure", "details": str(exc)}
        )

    return _finalize_observation(observation, started)


def _collect_xhtml_observations(
    root: ET.Element,
    resource: str,
    observation: dict[str, Any],
) -> None:
    package_dir = posixpath.dirname(resource)
    for element in root.iter():
        tag = _local_name(element.tag)
        if tag == "script":
            observation["active_content"].append(
                {"resource": resource, "fragment": element.attrib.get("id"), "kind": "script"}
            )
            continue
        if tag not in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "pre"}:
            continue
        text = _clean_text(element)
        if not text:
            continue
        block_type = "heading" if tag.startswith("h") else ("code" if tag == "pre" else "paragraph")
        observation["blocks"].append(
            {
                "type": block_type,
                "level": int(tag[1]) if tag.startswith("h") else None,
                "text": text,
                "resource": resource,
                "fragment": element.attrib.get("id"),
            }
        )
        for anchor in element.iter():
            if _local_name(anchor.tag) != "a":
                continue
            href = anchor.attrib.get("href")
            if not href:
                continue
            target_resource, target_fragment = _parse_link_target(package_dir, href)
            observation["links"].append(
                {
                    "from_resource": resource,
                    "from_fragment": element.attrib.get("id"),
                    "text": _clean_text(anchor),
                    "raw_target": href,
                    "target_resource": target_resource,
                    "target_fragment": target_fragment,
                }
            )


def _finalize_observation(observation: dict[str, Any], started: float) -> dict[str, Any]:
    observation["duration_seconds"] = round(time.perf_counter() - started, 9)
    return observation


def _inline_text(inlines: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for inline in inlines:
        kind = inline.get("t")
        content = inline.get("c")
        if kind == "Str":
            chunks.append(str(content))
        elif kind in {"Space", "SoftBreak", "LineBreak"}:
            chunks.append(" ")
        elif kind in {"Code", "Math"}:
            chunks.append(str(content[1]))
        elif kind in {
            "Emph", "Strong", "Underline", "Strikeout", "Superscript",
            "Subscript", "SmallCaps",
        }:
            chunks.append(_inline_text(content))
        elif kind in {"Span", "Link", "Image"}:
            chunks.append(_inline_text(content[1]))
    return " ".join("".join(chunks).split())


def _pandoc_links(inlines: list[dict[str, Any]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for inline in inlines:
        kind = inline.get("t")
        content = inline.get("c")
        if kind == "Link":
            links.append({"text": _inline_text(content[1]), "raw_target": str(content[2][0])})
            links.extend(_pandoc_links(content[1]))
        elif kind in {
            "Emph", "Strong", "Underline", "Strikeout", "Superscript",
            "Subscript", "SmallCaps",
        }:
            links.extend(_pandoc_links(content))
        elif kind in {"Span", "Image"}:
            links.extend(_pandoc_links(content[1]))
    return links


def _split_pandoc_anchor(identifier: str) -> tuple[str | None, str | None]:
    if ".xhtml#" in identifier:
        resource, fragment = identifier.split("#", 1)
        return resource, fragment or None
    if identifier.endswith(".xhtml"):
        return identifier, None
    return None, identifier or None


def _is_pandoc_resource_marker(content: Any) -> bool:
    if not isinstance(content, list) or len(content) != 1:
        return False
    inline = content[0]
    if inline.get("t") != "Span":
        return False
    attr, inlines = inline.get("c")
    identifier = attr[0]
    return bool(identifier.endswith(".xhtml") and not inlines)


def map_pandoc_json(document: dict[str, Any]) -> dict[str, Any]:
    """Map Pandoc native JSON into Provider-neutral benchmark observations."""
    observation: dict[str, Any] = {
        "contract": _contract(),
        "route": "pandoc-epub",
        "status": "success",
        "warnings": [],
        "spine": [],
        "resources": [],
        "blocks": [],
        "navigation": [],
        "links": [],
        "pandoc_api_version": document.get("pandoc-api-version"),
    }
    current_resource: str | None = None
    resource_sequence: list[str] = []
    for block in document.get("blocks", []):
        kind = block.get("t")
        content = block.get("c")
        if kind == "Para" and _is_pandoc_resource_marker(content):
            attr = content[0]["c"][0]
            current_resource = attr[0] or None
            if current_resource and current_resource not in resource_sequence:
                resource_sequence.append(current_resource)
            continue
        if kind == "Header":
            level, attr, inlines = content
            identifier = attr[0]
            anchor_resource, fragment = _split_pandoc_anchor(identifier)
            if anchor_resource:
                current_resource = anchor_resource
                if current_resource not in resource_sequence:
                    resource_sequence.append(current_resource)
            observation["blocks"].append(
                {
                    "type": "heading",
                    "level": level,
                    "text": _inline_text(inlines),
                    "resource": current_resource,
                    "fragment": fragment,
                    "raw_identifier": identifier,
                }
            )
            continue
        if kind in {"Para", "Plain"}:
            inlines = content
            text = _inline_text(inlines)
            if text:
                observation["blocks"].append(
                    {
                        "type": "paragraph",
                        "level": None,
                        "text": text,
                        "resource": current_resource,
                        "fragment": None,
                    }
                )
            for link in _pandoc_links(inlines):
                observation["links"].append(
                    {"from_resource": current_resource, "from_fragment": None, **link}
                )
    observation["resources"] = [{"resource": resource} for resource in resource_sequence]
    observation["spine"] = [Path(resource).stem for resource in resource_sequence]
    observation["warnings"].append(
        {
            "code": "navigation-not-exposed-in-pandoc-ast",
            "details": "Pandoc JSON mapping has no separate EPUB nav tree.",
        }
    )
    return observation


def pandoc_version(executable: str = "pandoc") -> dict[str, Any]:
    resolved = shutil.which(executable)
    try:
        completed = subprocess.run(
            [executable, "--version"], check=False, capture_output=True, text=True
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
    first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
    version = first_line.removeprefix("pandoc ").strip() if first_line else None
    result: dict[str, Any] = {
        "executable": executable,
        "resolved_executable": resolved,
        "version": version,
        "first_line": first_line,
        "returncode": completed.returncode,
        "error": None,
    }
    if resolved:
        resolved_path = Path(resolved)
        if resolved_path.is_file():
            result["executable_sha256"] = hashlib.sha256(resolved_path.read_bytes()).hexdigest()
    return result


def run_pandoc_epub(path: Path, executable: str = "pandoc") -> dict[str, Any]:
    """Run local Pandoc in its sandbox and map its JSON.

    The input is copied into a controlled temporary parent so file side effects
    relative to the input or CWD are observable. This is benchmark evidence, not
    a claim of OS-level filesystem or network isolation.
    """
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="raiatea-pandoc-") as tmp:
        root = Path(tmp)
        input_dir = root / "input"
        work = root / "work"
        input_dir.mkdir()
        work.mkdir()
        local_input = input_dir / path.name
        shutil.copyfile(path, local_input)
        baseline_files = {
            str(candidate.relative_to(root))
            for candidate in root.rglob("*")
            if candidate.is_file()
        }
        command = [
            executable, "--sandbox", "--from=epub", "--to=json", str(local_input)
        ]
        try:
            completed = subprocess.run(
                command, cwd=work, check=False, capture_output=True, text=True
            )
        except OSError as exc:
            return {
                "contract": _contract(),
                "route": "pandoc-epub",
                "status": "not-measured",
                "warnings": [{"code": "pandoc-unavailable", "details": str(exc)}],
                "duration_seconds": round(time.perf_counter() - started, 9),
                "command_options": ["--sandbox", "--from=epub", "--to=json"],
                "sandbox_enabled": True,
                "network_instrumentation": "not-measured",
                "side_effect_files": [],
            }
        side_effects = sorted(
            {
                str(candidate.relative_to(root))
                for candidate in root.rglob("*")
                if candidate.is_file()
            }
            - baseline_files
        )

    raw = completed.stdout.encode("utf-8")
    base = {
        "duration_seconds": round(time.perf_counter() - started, 9),
        "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_output_bytes": len(raw),
        "side_effect_files": side_effects,
        "command_options": ["--sandbox", "--from=epub", "--to=json"],
        "sandbox_enabled": True,
        "network_instrumentation": "not-measured",
    }
    if completed.returncode != 0:
        return {
            "contract": _contract(),
            "route": "pandoc-epub",
            "status": "failed",
            "warnings": [{"code": "pandoc-nonzero-exit", "details": completed.stderr.strip()}],
            **base,
        }
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {
            "contract": _contract(),
            "route": "pandoc-epub",
            "status": "failed",
            "warnings": [{"code": "pandoc-invalid-json", "details": str(exc)}],
            **base,
        }
    observation = map_pandoc_json(document)
    observation["stderr"] = completed.stderr.strip()
    observation.update(base)
    return observation
