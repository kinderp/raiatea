"""Explicit Docling picture/caption evidence for B01-PDF-004.

The normal Docling text mapper intentionally treats top-level picture items as
non-text leaves. This bounded mapper reads the pinned lossless Docling JSON and
preserves only explicit picture provenance and explicit caption references.
It does not infer relations from layout and does not claim pixel identity when
picture-image generation is disabled.
"""

from __future__ import annotations

from typing import Any

from docling_routes import _bbox_bottom_left, _page_sizes


def map_docling_figure_evidence(document: dict[str, Any]) -> dict[str, Any]:
    pages = _page_sizes(document)
    texts = document.get("texts", [])
    pictures_value = document.get("pictures")
    pictures_available = isinstance(pictures_value, list)
    pictures = pictures_value if pictures_available else []
    text_registry = {
        f"#/texts/{index}": item
        for index, item in enumerate(texts if isinstance(texts, list) else [])
        if isinstance(item, dict)
    }

    result: dict[str, Any] = {
        "route": "docling-lossless-explicit-picture-evidence",
        "status": "success" if pictures_available else "degraded",
        "warnings": [],
        # None means the Provider collection was unavailable/incomplete, while
        # [] means it was explicitly present, structurally valid and empty.
        "figures": [] if pictures_available else None,
        "caption_blocks": [],
        "figure_caption_relations": [],
        "asset_identity_available": False,
        "asset_identity_reason": (
            "The pinned Docling route disables generate_picture_images; no Provider image bytes "
            "are available for pixel-identity comparison."
        ),
        "association_policy": "Docling captions refs only; no spatial proximity inference",
    }
    if not pictures_available:
        result["warnings"].append(
            {
                "code": "docling-picture-collection-unavailable",
                "details": (
                    "Lossless Docling output did not expose `pictures` as a list; "
                    "figure presence is unknown and must remain not-measured."
                ),
            }
        )

    invalid_picture_item = False
    for index, picture in enumerate(pictures):
        if not isinstance(picture, dict):
            invalid_picture_item = True
            result["status"] = "degraded"
            result["warnings"].append(
                {
                    "code": "docling-picture-item-invalid",
                    "details": {"index": index, "type": type(picture).__name__},
                }
            )
            continue
        provider_ref = picture.get("self_ref") or f"#/pictures/{index}"
        figure: dict[str, Any] = {
            "provider_ref": provider_ref,
            "provider_source": "docling-explicit-picture-item",
            "provider_label": picture.get("label"),
            "page_index": None,
            "bbox_points_bottom_left": None,
            "decoded_pixel_sha256": None,
        }
        provenance = picture.get("prov") if isinstance(picture.get("prov"), list) else []
        if provenance and isinstance(provenance[0], dict):
            first = provenance[0]
            page_no = first.get("page_no")
            bbox = first.get("bbox")
            if isinstance(page_no, int) and page_no >= 1:
                figure["page_index"] = page_no - 1
                if isinstance(bbox, dict):
                    mapped, warning = _bbox_bottom_left(bbox, page_no, pages)
                    figure["bbox_points_bottom_left"] = mapped
                    if warning:
                        result["warnings"].append(
                            {
                                "code": "docling-picture-provenance-degraded",
                                "details": {"ref": provider_ref, "reason": warning},
                            }
                        )
        assert isinstance(result["figures"], list)
        result["figures"].append(figure)

        captions = picture.get("captions") if isinstance(picture.get("captions"), list) else []
        for caption_ref in captions:
            ref = caption_ref.get("$ref") if isinstance(caption_ref, dict) else None
            caption = text_registry.get(ref) if isinstance(ref, str) else None
            if caption is None:
                result["warnings"].append(
                    {
                        "code": "docling-picture-caption-ref-unresolved",
                        "details": {"picture_ref": provider_ref, "caption_ref": ref},
                    }
                )
                continue
            text = caption.get("text")
            if not isinstance(text, str) or not text.strip():
                result["warnings"].append(
                    {
                        "code": "docling-picture-caption-text-missing",
                        "details": {"picture_ref": provider_ref, "caption_ref": ref},
                    }
                )
                continue

            caption_block: dict[str, Any] = {
                "type": "text-block",
                "semantic_type": "caption" if str(caption.get("label", "")).lower() == "caption" else None,
                "semantic_level": None,
                "provider_label": caption.get("label"),
                "text": " ".join(text.split()),
                "page_index": None,
                "bbox_points_bottom_left": None,
                "docling_ref": ref,
                "provider_relation_parent": provider_ref,
            }
            caption_prov = caption.get("prov") if isinstance(caption.get("prov"), list) else []
            if caption_prov and isinstance(caption_prov[0], dict):
                first_caption = caption_prov[0]
                page_no = first_caption.get("page_no")
                bbox = first_caption.get("bbox")
                if isinstance(page_no, int) and page_no >= 1:
                    caption_block["page_index"] = page_no - 1
                    if isinstance(bbox, dict):
                        mapped, warning = _bbox_bottom_left(bbox, page_no, pages)
                        caption_block["bbox_points_bottom_left"] = mapped
                        if warning:
                            result["warnings"].append(
                                {
                                    "code": "docling-caption-provenance-degraded",
                                    "details": {"ref": ref, "reason": warning},
                                }
                            )
            result["caption_blocks"].append(caption_block)
            result["figure_caption_relations"].append(
                {
                    "provider_figure_ref": provider_ref,
                    "provider_caption_ref": ref,
                    "caption_text": caption_block["text"],
                    "provider_relation_source": "docling-picture.captions-explicit-ref",
                }
            )

    if invalid_picture_item:
        # A partially malformed Provider collection cannot support an exact
        # figure-count observation. Preserve any caption text evidence collected
        # from valid items, but make figure presence/geometry unknown.
        result["figures"] = None

    return result
