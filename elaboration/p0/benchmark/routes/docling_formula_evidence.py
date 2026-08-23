"""Lossless Docling diagnostic evidence for B01-PDF-006.

Docling's pinned profile has formula enrichment disabled. Picture/group structure
and descendant text are preserved as Provider evidence, but are never promoted
to formula or mathematical-relation semantics.
"""
from __future__ import annotations
from typing import Any

from docling_routes import _bbox_bottom_left, _page_sizes


def _registry(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for collection in ("texts", "pictures", "groups"):
        values = document.get(collection)
        if isinstance(values, list):
            for index, item in enumerate(values):
                if isinstance(item, dict):
                    registry[f"#/{collection}/{index}"] = item
    return registry


def _text_block(
    ref: str,
    item: dict[str, Any],
    sizes: dict[int, tuple[float, float]],
) -> dict[str, Any] | None:
    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    page_index = None
    bbox_out = None
    provenance = item.get("prov") if isinstance(item.get("prov"), list) else []
    if provenance and isinstance(provenance[0], dict):
        page_no = provenance[0].get("page_no")
        bbox = provenance[0].get("bbox")
        if isinstance(page_no, int) and page_no >= 1:
            page_index = page_no - 1
            if isinstance(bbox, dict):
                bbox_out, _ = _bbox_bottom_left(bbox, page_no, sizes)
    return {
        "type": "text-block",
        "text": " ".join(text.split()),
        "page_index": page_index,
        "bbox_points_bottom_left": bbox_out,
        "docling_ref": ref,
        "provider_label": item.get("label"),
    }


def map_docling_formula_evidence(document: dict[str, Any]) -> dict[str, Any]:
    sizes = _page_sizes(document)
    registry = _registry(document)
    warnings: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []

    texts = document.get("texts")
    if not isinstance(texts, list):
        warnings.append(
            {
                "code": "docling-formula-texts-unavailable",
                "details": type(texts).__name__,
            }
        )
        texts = []
    for index, item in enumerate(texts):
        if isinstance(item, dict):
            block = _text_block(f"#/texts/{index}", item, sizes)
            if block:
                blocks.append(block)

    pictures = document.get("pictures")
    if pictures is None:
        warnings.append(
            {"code": "docling-formula-groups-unavailable", "details": "pictures missing"}
        )
    elif not isinstance(pictures, list):
        warnings.append(
            {
                "code": "docling-formula-groups-invalid",
                "details": type(pictures).__name__,
            }
        )
    else:
        for index, picture in enumerate(pictures):
            if not isinstance(picture, dict):
                warnings.append(
                    {"code": "docling-formula-group-invalid-item", "details": index}
                )
                continue
            children = []
            raw_children = (
                picture.get("children") if isinstance(picture.get("children"), list) else []
            )
            for child in raw_children:
                ref = child.get("$ref") if isinstance(child, dict) else None
                item = registry.get(ref) if isinstance(ref, str) else None
                if isinstance(item, dict):
                    children.append(
                        {"provider_ref": ref, "text": item.get("text")}
                    )
                elif ref:
                    warnings.append(
                        {
                            "code": "docling-formula-group-unresolved-child",
                            "details": {
                                "group": f"#/pictures/{index}",
                                "ref": ref,
                            },
                        }
                    )

            page_index = None
            bbox_out = None
            provenance = (
                picture.get("prov") if isinstance(picture.get("prov"), list) else []
            )
            if provenance and isinstance(provenance[0], dict):
                page_no = provenance[0].get("page_no")
                bbox = provenance[0].get("bbox")
                if isinstance(page_no, int) and page_no >= 1:
                    page_index = page_no - 1
                    if isinstance(bbox, dict):
                        bbox_out, _ = _bbox_bottom_left(bbox, page_no, sizes)
            groups.append(
                {
                    "provider_ref": f"#/pictures/{index}",
                    "provider_label": picture.get("label"),
                    "page_index": page_index,
                    "bbox_points_bottom_left": bbox_out,
                    "children": children,
                    "mathematical_semantics": False,
                }
            )

    return {
        "route": "docling-lossless-formula-diagnostic",
        "status": "success",
        "warnings": warnings,
        "formula_text_blocks": blocks,
        "provider_formula_groups": groups,
        "formula_enrichment_enabled": False,
        "math_relations": None,
        "semantic_policy": (
            "picture/group structure is diagnostic only; no math semantics inferred "
            "from grouping, geometry or child layout"
        ),
    }
