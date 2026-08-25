#!/usr/bin/env python3
"""Product direct EPUB parser for the promoted VS1 route.

This code carries forward the behavior proven by the B-02 benchmark route but is
product-owned: it does not emit benchmark contracts, does not extract ZIP
members to disk, and never executes active content.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import posixpath
import re
import time
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


OBSERVATION_VERSION = "raiatea.vs1d.direct-epub-observation.0.1.0"
OPF_NS = {"opf": "http://www.idpf.org/2007/opf"}
CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}


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
        raise ValueError("unsafe-backslash-epub-href")
    if href.startswith("/") or re.match(r"^[A-Za-z]:", href):
        raise ValueError("unsafe-absolute-epub-href")
    path_part = href.split("#", 1)[0]
    resolved = posixpath.normpath(posixpath.join(package_dir, path_part))
    reason = _unsafe_member_reason(resolved)
    if reason:
        raise ValueError(f"unsafe-resolved-epub-member:{reason}")
    return resolved


def _parse_link_target(package_dir: str, target: str) -> tuple[str | None, str | None]:
    resource_part, _, fragment = target.partition("#")
    if not resource_part:
        return None, fragment or None
    return _resolve_member(package_dir, resource_part), fragment or None


def _read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    if name not in zf.namelist():
        raise ValueError("missing-required-epub-resource")
    return ET.fromstring(zf.read(name))


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
                {
                    "resource": resource,
                    "fragment": element.attrib.get("id"),
                    "kind": "script",
                }
            )
            continue
        if tag not in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "pre"}:
            continue
        text = _clean_text(element)
        if not text:
            continue
        block_type = (
            "heading"
            if tag.startswith("h")
            else ("code" if tag == "pre" else "paragraph")
        )
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


def parse_direct_epub(path: Path) -> dict[str, Any]:
    """Parse one private local EPUB copy without extracting package members."""

    started = time.perf_counter()
    observation: dict[str, Any] = {
        "observation_version": OBSERVATION_VERSION,
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
                return _finalize(observation, started)

            if not names or names[0] != "mimetype":
                observation["warnings"].append(
                    {"code": "epub-mimetype-not-first", "details": names[:1]}
                )
            if "mimetype" not in names or zf.read("mimetype") != b"application/epub+zip":
                raise ValueError("invalid-or-missing-epub-mimetype")

            container = _read_xml(zf, "META-INF/container.xml")
            rootfile = container.find(".//c:rootfile", CONTAINER_NS)
            if rootfile is None:
                raise ValueError("epub-container-has-no-rootfile")
            package_path = rootfile.attrib.get("full-path", "")
            if _unsafe_member_reason(package_path):
                raise ValueError("unsafe-epub-package-path")
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
                    raise ValueError("spine-references-missing-manifest-item")
                item = manifest[item_id]
                member = _resolve_member(package_dir, item["href"])
                observation["resources"].append(
                    {
                        "id": item_id,
                        "resource": member,
                        "media_type": item["media_type"],
                    }
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
                    {
                        "code": "active-content-present",
                        "details": observation["active_content"],
                    }
                )
                observation["status"] = "degraded"
            else:
                observation["status"] = "success"
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile) as exc:
        observation["status"] = "failed"
        observation["warnings"].append(
            {"code": "direct-epub-failure", "details": str(exc)}
        )
    return _finalize(observation, started)


def _finalize(observation: dict[str, Any], started: float) -> dict[str, Any]:
    observation["duration_seconds"] = round(time.perf_counter() - started, 9)
    return observation
