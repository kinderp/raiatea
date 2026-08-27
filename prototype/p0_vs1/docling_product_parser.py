#!/usr/bin/env python3
"""PDF1c product mapping helpers for the pinned native/no-OCR Docling profile.

This module maps Docling lossless document evidence into the closed Raiatea
DoclingObservation contract. It does not own the real Provider execution loop;
that fail-closed lifecycle lives in ``docling_provider_runtime.py``.
Benchmark modules are deliberately not imported.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator

from prototype.p0_vs1.docling_observation_contract import (
    DOCLING_OBSERVATION_VERSION,
    DOCLING_PROFILE,
    encode_docling_observation_bundle,
    validate_docling_observation_bundle,
)
from prototype.p0_vs1.docling_reference import validate_reference_provider_record


# Provider labels are normalized by Raiatea Core policy. Numeric heading levels
# are never inferred from the label itself; they are retained only when Docling
# exposes an explicit positive integer ``level`` on the lossless item.
_LABEL_MAP: dict[str, str] = {
    "title": "heading",
    "section_header": "heading",
    "text": "paragraph",
    "paragraph": "paragraph",
    "list_item": "list_item",
    "code": "code",
    "caption": "caption",
}


class DoclingProductError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DoclingProductError(message)


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DoclingProductError("docling-export-not-json-safe") from exc


def _source_sha(source_bytes: bytes) -> str:
    return "sha256:" + hashlib.sha256(source_bytes).hexdigest()


def _page_sizes(document: dict[str, Any]) -> dict[int, tuple[float, float]]:
    sizes: dict[int, tuple[float, float]] = {}
    pages = document.get("pages", {})
    iterable = (
        pages.values()
        if isinstance(pages, dict)
        else pages
        if isinstance(pages, list)
        else []
    )
    for page in iterable:
        if not isinstance(page, dict):
            continue
        page_no = page.get("page_no")
        size = page.get("size")
        if not isinstance(size, dict) or not isinstance(page_no, int) or page_no < 1:
            continue
        try:
            width = float(size["width"])
            height = float(size["height"])
        except (KeyError, TypeError, ValueError):
            continue
        if width > 0 and height > 0:
            sizes[page_no] = (width, height)
    return sizes


def _ref_registry(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for collection in (
        "texts",
        "groups",
        "tables",
        "pictures",
        "key_value_items",
        "form_items",
    ):
        values = document.get(collection, [])
        if not isinstance(values, list):
            continue
        for index, item in enumerate(values):
            if isinstance(item, dict):
                registry[f"#/{collection}/{index}"] = item
    return registry


def _body_order(
    document: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> tuple[list[tuple[str, dict[str, Any]]], str, list[dict[str, Any]]]:
    ordered: list[tuple[str, dict[str, Any]]] = []
    warnings: list[dict[str, Any]] = []
    active: set[str] = set()

    def visit(ref: str) -> None:
        if ref in active:
            warnings.append({"code": "docling-ref-cycle", "details": ref})
            return
        item = registry.get(ref)
        if item is None:
            warnings.append({"code": "docling-unresolved-ref", "details": ref})
            return
        children = item.get("children")
        if ref.startswith("#/groups/") and isinstance(children, list):
            active.add(ref)
            for child in children:
                child_ref = child.get("$ref") if isinstance(child, dict) else None
                if isinstance(child_ref, str):
                    visit(child_ref)
            active.remove(ref)
            return
        ordered.append((ref, item))

    body = document.get("body")
    children = body.get("children") if isinstance(body, dict) else None
    if isinstance(children, list):
        for child in children:
            ref = child.get("$ref") if isinstance(child, dict) else None
            if isinstance(ref, str):
                visit(ref)
        return ordered, "body.children", warnings

    warnings.append(
        {
            "code": "docling-body-order-unavailable",
            "details": "texts array order used as explicit fallback observation",
        }
    )
    texts = document.get("texts", [])
    for index, item in enumerate(texts if isinstance(texts, list) else []):
        if isinstance(item, dict):
            ordered.append((f"#/texts/{index}", item))
    return ordered, "texts-fallback", warnings


def _bbox_bottom_left(
    bbox: dict[str, Any],
    page_no: int,
    page_sizes: dict[int, tuple[float, float]],
) -> tuple[list[float] | None, str | None]:
    try:
        left = float(bbox["l"])
        top = float(bbox["t"])
        right = float(bbox["r"])
        bottom = float(bbox["b"])
    except (KeyError, TypeError, ValueError):
        return None, "invalid-bbox"
    origin = str(bbox.get("coord_origin", "TOPLEFT")).upper()
    if origin == "BOTTOMLEFT":
        return [left, bottom, right, top], None
    if origin == "TOPLEFT":
        size = page_sizes.get(page_no)
        if size is None:
            return None, "missing-page-size-for-top-left-bbox"
        page_height = size[1]
        return [left, page_height - bottom, right, page_height - top], None
    return None, f"unsupported-coordinate-origin:{origin}"


def _coordinate(
    item: dict[str, Any],
    page_sizes: dict[int, tuple[float, float]],
    *,
    provider_ref: str,
    warning_prefix: str,
) -> tuple[dict[str, Any] | None, int, list[dict[str, Any]]]:
    provenance = item.get("prov") if isinstance(item.get("prov"), list) else []
    warnings: list[dict[str, Any]] = []
    if len(provenance) > 1:
        warnings.append(
            {
                "code": f"{warning_prefix}-multiple-provenance",
                "details": {"provider_ref": provider_ref, "count": len(provenance)},
            }
        )
    if not provenance or not isinstance(provenance[0], dict):
        return None, len(provenance), warnings
    first = provenance[0]
    page_no = first.get("page_no")
    bbox = first.get("bbox")
    if not isinstance(page_no, int) or page_no < 1:
        warnings.append(
            {
                "code": f"{warning_prefix}-provenance-degraded",
                "details": {"provider_ref": provider_ref, "reason": "invalid-page-number"},
            }
        )
        return None, len(provenance), warnings
    if not isinstance(bbox, dict):
        return None, len(provenance), warnings
    mapped, reason = _bbox_bottom_left(bbox, page_no, page_sizes)
    if reason is not None:
        warnings.append(
            {
                "code": f"{warning_prefix}-provenance-degraded",
                "details": {"provider_ref": provider_ref, "reason": reason},
            }
        )
        return None, len(provenance), warnings
    return {
        "page_index": page_no - 1,
        "bbox_points_bottom_left": mapped,
    }, len(provenance), warnings


def _provider_label(item: dict[str, Any]) -> str | None:
    value = item.get("label")
    return value if isinstance(value, str) and value else None


def _semantic(item: dict[str, Any]) -> tuple[str | None, int | None]:
    label = (_provider_label(item) or "").lower()
    semantic_type = _LABEL_MAP.get(label)
    level: int | None = None
    provider_level = item.get("level")
    if (
        semantic_type == "heading"
        and isinstance(provider_level, int)
        and not isinstance(provider_level, bool)
        and provider_level >= 1
    ):
        level = provider_level
    return semantic_type, level


def _text_surface(item: dict[str, Any]) -> str | None:
    value = item.get("text")
    if not isinstance(value, str) or not value.strip():
        return None
    # ProviderObservation retains Docling's explicit text string. Whitespace
    # normalization belongs downstream in a Core normalization/search layer, not
    # in provider-native evidence.
    return value


def _caption_record(
    item: dict[str, Any],
    provider_ref: str,
    page_sizes: dict[int, tuple[float, float]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    text = _text_surface(item)
    if text is None:
        return None, [
            {
                "code": "docling-picture-caption-text-missing",
                "details": {"caption_ref": provider_ref},
            }
        ]
    coordinate, provenance_count, warnings = _coordinate(
        item,
        page_sizes,
        provider_ref=provider_ref,
        warning_prefix="docling-caption",
    )
    label = _provider_label(item)
    return {
        "provider_ref": provider_ref,
        "text": text,
        "provider_label": label,
        "semantic_type": "caption" if (label or "").lower() == "caption" else None,
        "coordinate": coordinate,
        "provenance_count": provenance_count,
        "provenance_source": (
            "docling-text-provenance"
            if coordinate is not None
            else "docling-lossless-caption"
        ),
    }, warnings


def _picture_evidence(
    document: dict[str, Any],
    page_sizes: dict[int, tuple[float, float]],
) -> tuple[
    str,
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    warnings: list[dict[str, Any]] = []
    value = document.get("pictures")
    if not isinstance(value, list):
        return (
            "unavailable",
            [],
            [],
            [],
            [
                {
                    "code": "docling-picture-collection-unavailable",
                    "details": "lossless Docling output did not expose pictures as a list",
                }
            ],
        )

    texts = document.get("texts", [])
    text_registry = {
        f"#/texts/{index}": item
        for index, item in enumerate(texts if isinstance(texts, list) else [])
        if isinstance(item, dict)
    }
    state = "present"
    pictures: list[dict[str, Any]] = []
    captions_by_ref: dict[str, dict[str, Any]] = {}
    relations: list[dict[str, Any]] = []

    for picture_index, picture in enumerate(value):
        if not isinstance(picture, dict):
            state = "degraded"
            warnings.append(
                {
                    "code": "docling-picture-item-invalid",
                    "details": {
                        "index": picture_index,
                        "type": type(picture).__name__,
                    },
                }
            )
            continue
        self_ref = picture.get("self_ref")
        provider_ref = (
            self_ref
            if isinstance(self_ref, str) and self_ref
            else f"#/pictures/{picture_index}"
        )
        coordinate, provenance_count, coordinate_warnings = _coordinate(
            picture,
            page_sizes,
            provider_ref=provider_ref,
            warning_prefix="docling-picture",
        )
        warnings.extend(coordinate_warnings)
        pictures.append(
            {
                "provider_ref": provider_ref,
                "provider_label": _provider_label(picture),
                "coordinate": coordinate,
                "provenance_count": provenance_count,
                "provenance_source": "docling-picture-item",
            }
        )

        captions_value = picture.get("captions", [])
        if not isinstance(captions_value, list):
            state = "degraded"
            warnings.append(
                {
                    "code": "docling-picture-captions-invalid",
                    "details": {"picture_ref": provider_ref},
                }
            )
            continue
        for caption_index, caption_ref_value in enumerate(captions_value):
            caption_ref = (
                caption_ref_value.get("$ref")
                if isinstance(caption_ref_value, dict)
                else None
            )
            caption_item = (
                text_registry.get(caption_ref)
                if isinstance(caption_ref, str)
                else None
            )
            if caption_item is None:
                state = "degraded"
                warnings.append(
                    {
                        "code": "docling-picture-caption-ref-unresolved",
                        "details": {
                            "picture_ref": provider_ref,
                            "caption_ref": caption_ref,
                        },
                    }
                )
                continue
            caption_record, caption_warnings = _caption_record(
                caption_item,
                caption_ref,
                page_sizes,
            )
            warnings.extend(caption_warnings)
            if caption_record is None:
                state = "degraded"
                continue
            prior = captions_by_ref.get(caption_ref)
            if prior is not None and prior != caption_record:
                state = "degraded"
                warnings.append(
                    {
                        "code": "docling-caption-evidence-conflict",
                        "details": {"caption_ref": caption_ref},
                    }
                )
                continue
            captions_by_ref[caption_ref] = caption_record
            relations.append(
                {
                    "relation_id": (
                        f"relation:picture-caption:{picture_index:04d}:{caption_index:04d}"
                    ),
                    "picture_ref": provider_ref,
                    "caption_ref": caption_ref,
                    "relation_source": "docling-picture.captions-explicit-ref",
                }
            )

    pictures.sort(key=lambda row: row["provider_ref"])
    captions = sorted(
        captions_by_ref.values(), key=lambda row: row["provider_ref"]
    )
    relations.sort(key=lambda row: row["relation_id"])
    return state, pictures, captions, relations, warnings


def _provider_status(value: str | None) -> str:
    if not isinstance(value, str) or not value:
        return "unknown"
    token = value.rsplit(".", 1)[-1].replace("-", "_").casefold()
    if token == "success":
        return "success"
    if "partial" in token:
        return "degraded"
    if token in {"failure", "failed", "error"}:
        return "failed"
    return "unknown"


def map_docling_document(
    document: dict[str, Any],
    *,
    source_ref_id: str,
    source_fingerprint: str,
    provider: dict[str, Any],
    provider_conversion_status: str,
) -> dict[str, Any]:
    validate_reference_provider_record(provider)
    _require(isinstance(document, dict), "docling-export-must-be-object")
    page_sizes = _page_sizes(document)
    registry = _ref_registry(document)
    ordered, body_order_source, warnings = _body_order(document, registry)
    blocks: list[dict[str, Any]] = []
    for provider_ref, item in ordered:
        text = _text_surface(item)
        if text is None:
            continue
        coordinate, provenance_count, coordinate_warnings = _coordinate(
            item,
            page_sizes,
            provider_ref=provider_ref,
            warning_prefix="docling-text",
        )
        warnings.extend(coordinate_warnings)
        semantic_type, semantic_level = _semantic(item)
        blocks.append(
            {
                "provider_ref": provider_ref,
                "body_order_index": len(blocks),
                "text": text,
                "provider_label": _provider_label(item),
                "semantic_type": semantic_type,
                "semantic_level": semantic_level,
                "coordinate": coordinate,
                "provenance_count": provenance_count,
                "provenance_source": (
                    "docling-text-provenance"
                    if coordinate is not None
                    else "docling-lossless-item"
                ),
            }
        )

    picture_state, pictures, captions, relations, picture_warnings = _picture_evidence(
        document,
        page_sizes,
    )
    warnings.extend(picture_warnings)
    unknown_labels = sorted(
        {
            str(row["provider_label"])
            for row in blocks
            if row["provider_label"] is not None and row["semantic_type"] is None
        }
    )
    if unknown_labels:
        warnings.append({"code": "docling-unmapped-labels", "details": unknown_labels})

    raw = _canonical_bytes(document)
    bundle = {
        "bundle_version": DOCLING_OBSERVATION_VERSION,
        "record_kind": "DoclingObservationBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": source_fingerprint,
        "provider": dict(provider),
        "route_profile": DOCLING_PROFILE,
        "observation": {
            "status": _provider_status(provider_conversion_status),
            "provider_conversion_status": provider_conversion_status,
            "warnings": warnings,
            "body_order_source": body_order_source,
            "blocks": blocks,
            "picture_collection_state": picture_state,
            "pictures": pictures,
            "caption_blocks": captions,
            "picture_caption_relations": relations,
            "raw_document_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        },
    }
    validate_docling_observation_bundle(bundle)
    return bundle


def failed_docling_observation(
    *,
    source_ref_id: str,
    source_fingerprint: str,
    provider: dict[str, Any],
    restricted: bool,
    error_type: str,
) -> dict[str, Any]:
    validate_reference_provider_record(provider)
    bundle = {
        "bundle_version": DOCLING_OBSERVATION_VERSION,
        "record_kind": "DoclingObservationBundle",
        "source_ref_id": source_ref_id,
        "source_fingerprint": source_fingerprint,
        "provider": dict(provider),
        "route_profile": DOCLING_PROFILE,
        "observation": {
            "status": "restricted" if restricted else "failed",
            "provider_conversion_status": None,
            "warnings": [
                {
                    "code": (
                        "docling-access-restriction-signaled"
                        if restricted
                        else "docling-conversion-failed"
                    ),
                    "details": {"error_type": error_type},
                }
            ],
            "body_order_source": "unavailable",
            "blocks": [],
            "picture_collection_state": "unavailable",
            "pictures": [],
            "caption_blocks": [],
            "picture_caption_relations": [],
            "raw_document_sha256": None,
        },
    }
    validate_docling_observation_bundle(bundle)
    return bundle


@contextmanager
def _offline_environment(artifacts_path: Path, cache_root: Path) -> Iterator[None]:
    cache_root = cache_root.resolve()
    values = {
        "DOCLING_ARTIFACTS_PATH": str(artifacts_path.resolve()),
        "HF_HOME": str(cache_root / "huggingface"),
        "HUGGINGFACE_HUB_CACHE": str(cache_root / "huggingface" / "hub"),
        "TRANSFORMERS_CACHE": str(cache_root / "transformers"),
        "XDG_CACHE_HOME": str(cache_root / "xdg"),
        "TORCH_HOME": str(cache_root / "torch"),
        "MPLCONFIGDIR": str(cache_root / "matplotlib"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "DOCLING_DEVICE": "cpu",
        "DOCLING_NUM_THREADS": "4",
    }
    previous = {key: os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        yield
    finally:
        for key, old in previous.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


def run_docling_pdf(
    source_bytes: bytes,
    *,
    source_ref_id: str,
    source_fingerprint: str,
    provider: dict[str, Any],
    artifacts_path: Path,
    cache_root: Path,
) -> dict[str, Any]:
    """Compatibility facade over the single fail-closed product runtime."""
    from prototype.p0_vs1.docling_provider_runtime import run_docling_pdf_product

    return run_docling_pdf_product(
        source_bytes,
        source_ref_id=source_ref_id,
        source_fingerprint=source_fingerprint,
        provider=provider,
        artifacts_path=artifacts_path,
        cache_root=cache_root,
    )


__all__ = [
    "DoclingProductError",
    "encode_docling_observation_bundle",
    "failed_docling_observation",
    "map_docling_document",
    "run_docling_pdf",
]
