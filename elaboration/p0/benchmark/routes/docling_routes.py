"""Benchmark-only Docling B-01 route and pure JSON mapper.

The pure mapper has no Docling dependency and is exercised by the normal
cross-platform test matrix. Runtime imports are lazy so only the dedicated
reference environment needs Docling and its model artifacts.

This module is evidence tooling. It is not a production Adapter and does not
define Raiatea's public P0 schema.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import tempfile
import time
from typing import Any, Iterator


DOCLING_VERSION = "2.118.0"
DOCLING_WHEEL_SHA256 = "fd4962c9a54229bae1eb9b49f7fadb7e7b8affabf7e4fba1aac8cb335f558c8f"
DOCLING_SOURCE_COMMIT = "9b454c9e88454d95fd04d538c552a3c07bc3c04d"
ROUTE_CONTRACT_VERSION = "0.1.0"

_LABEL_MAP = {
    "title": ("heading", 1),
    "section_header": ("heading", None),
    "text": ("paragraph", None),
    "paragraph": ("paragraph", None),
    "list_item": ("list-item", None),
    "code": ("code", None),
}


def _contract() -> dict[str, Any]:
    return {
        "name": "raiatea-p0-benchmark-observation",
        "version": ROUTE_CONTRACT_VERSION,
        "scope": "benchmark-evidence-only",
        "public_p0_schema": False,
    }


def digest_file(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_manifest(root: Path) -> dict[str, Any]:
    """Return a deterministic manifest of all files under a model/cache root."""
    resolved = root.resolve()
    files: list[dict[str, Any]] = []
    if not resolved.is_dir():
        return {
            "root": str(resolved),
            "exists": False,
            "file_count": 0,
            "bytes": 0,
            "files": [],
            "manifest_sha256": None,
        }

    for path in sorted(p for p in resolved.rglob("*") if p.is_file()):
        relative = path.relative_to(resolved).as_posix()
        files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": digest_file(path),
            }
        )
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "root": str(resolved),
        "exists": True,
        "file_count": len(files),
        "bytes": sum(item["bytes"] for item in files),
        "files": files,
        "manifest_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def installed_environment() -> dict[str, Any]:
    """Capture package/runtime evidence without importing the Docling pipeline."""
    try:
        version = importlib.metadata.version("docling")
    except importlib.metadata.PackageNotFoundError:
        return {
            "docling_version": None,
            "python_version": platform.python_version(),
            "installed": False,
        }
    distributions = []
    for dist in sorted(
        importlib.metadata.distributions(),
        key=lambda d: (d.metadata.get("Name") or "").lower(),
    ):
        name = dist.metadata.get("Name")
        if name:
            distributions.append(f"{name}=={dist.version}")
    freeze = "\n".join(distributions) + "\n"
    return {
        "docling_version": version,
        "python_version": platform.python_version(),
        "installed": True,
        "freeze": distributions,
        "freeze_sha256": hashlib.sha256(freeze.encode("utf-8")).hexdigest(),
    }


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
        size = page.get("size") or {}
        if isinstance(page_no, int) and page_no >= 1:
            try:
                sizes[page_no] = (float(size["width"]), float(size["height"]))
            except (KeyError, TypeError, ValueError):
                continue
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
) -> tuple[list[tuple[str, dict[str, Any]]], list[dict[str, Any]]]:
    """Resolve body/group refs while preserving authored Docling body order."""
    ordered: list[tuple[str, dict[str, Any]]] = []
    warnings: list[dict[str, Any]] = []
    active: set[str] = set()

    def visit_ref(ref: str) -> None:
        if ref in active:
            warnings.append({"code": "docling-ref-cycle", "details": ref})
            return
        item = registry.get(ref)
        if item is None:
            warnings.append({"code": "docling-unresolved-ref", "details": ref})
            return
        children = item.get("children")
        if isinstance(children, list):
            active.add(ref)
            for child in children:
                if isinstance(child, dict) and isinstance(child.get("$ref"), str):
                    visit_ref(child["$ref"])
            active.remove(ref)
            return
        ordered.append((ref, item))

    body = document.get("body")
    body_children = body.get("children") if isinstance(body, dict) else None
    if isinstance(body_children, list):
        for child in body_children:
            if isinstance(child, dict) and isinstance(child.get("$ref"), str):
                visit_ref(child["$ref"])
    else:
        warnings.append(
            {
                "code": "docling-body-order-unavailable",
                "details": (
                    "Document JSON has no body.children reference sequence; "
                    "texts array order is used only as a fallback observation."
                ),
            }
        )
        values = document.get("texts", [])
        for index, item in enumerate(values if isinstance(values, list) else []):
            if isinstance(item, dict):
                ordered.append((f"#/texts/{index}", item))
    return ordered, warnings


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


def _semantic(label: Any) -> tuple[str | None, int | None]:
    normalized = str(label).lower() if label is not None else ""
    return _LABEL_MAP.get(normalized, (None, None))


def map_docling_document(document: dict[str, Any]) -> dict[str, Any]:
    """Map lossless Docling JSON into conservative Provider-neutral observations."""
    page_sizes = _page_sizes(document)
    registry = _ref_registry(document)
    ordered, warnings = _body_order(document, registry)
    blocks: list[dict[str, Any]] = []

    for ref, item in ordered:
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        label = item.get("label")
        semantic_type, semantic_level = _semantic(label)
        provenance = item.get("prov") if isinstance(item.get("prov"), list) else []
        page_index: int | None = None
        bbox_points: list[float] | None = None
        coordinate_origin: str | None = None
        provenance_warning: str | None = None
        if provenance:
            first = provenance[0]
            if isinstance(first, dict):
                page_no = first.get("page_no")
                if isinstance(page_no, int) and page_no >= 1:
                    page_index = page_no - 1
                    bbox = first.get("bbox")
                    if isinstance(bbox, dict):
                        coordinate_origin = str(
                            bbox.get("coord_origin", "TOPLEFT")
                        ).upper()
                        bbox_points, provenance_warning = _bbox_bottom_left(
                            bbox, page_no, page_sizes
                        )
                else:
                    provenance_warning = "invalid-page-number"
        if provenance_warning:
            warnings.append(
                {
                    "code": "docling-provenance-degraded",
                    "details": {"ref": ref, "reason": provenance_warning},
                }
            )

        blocks.append(
            {
                "type": "text-block",
                "semantic_type": semantic_type,
                "semantic_level": semantic_level,
                "provider_label": label,
                "text": " ".join(text.split()),
                "page_index": page_index,
                "bbox_points_bottom_left": bbox_points,
                "provider_bbox_origin": coordinate_origin,
                "docling_ref": ref,
                "provenance_count": len(provenance),
            }
        )

    unknown_labels = sorted(
        {
            str(block["provider_label"])
            for block in blocks
            if block.get("provider_label") is not None
            and block.get("semantic_type") is None
        }
    )
    if unknown_labels:
        warnings.append(
            {
                "code": "docling-unmapped-labels",
                "details": unknown_labels,
            }
        )

    fallback = any(
        warning.get("code") == "docling-body-order-unavailable"
        for warning in warnings
    )
    return {
        "contract": _contract(),
        "route": "docling-2.118.0-standard-pdf-native-no-ocr",
        "status": "success",
        "warnings": warnings,
        "blocks": blocks,
        "pages_observed": sorted(page_sizes),
        "page_structure_observed": bool(page_sizes),
        "bbox_structure_observed": any(
            block.get("bbox_points_bottom_left") is not None for block in blocks
        ),
        "body_order_source": "texts-fallback" if fallback else "body.children",
    }


@contextmanager
def _offline_environment(
    artifacts_path: Path,
    cache_root: Path,
) -> Iterator[None]:
    """Apply fail-closed cache/offline environment for measured conversion."""
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


def run_docling_pdf_json(
    source: Path,
    artifacts_path: Path,
    cache_root: Path,
) -> dict[str, Any]:
    """Run Docling lazily with local artifacts and no OCR/remote/plugin features."""
    started = time.perf_counter()
    observation: dict[str, Any] = {
        "contract": _contract(),
        "route": "docling-2.118.0-standard-pdf-native-no-ocr",
        "status": "unknown",
        "warnings": [],
        "blocks": [],
        "network_policy": "offline-env-plus-docling-remote-services-disabled",
        "os_level_network_isolation": False,
        "ocr_policy": "disabled",
        "external_plugins": False,
        "remote_services": False,
    }

    environment = installed_environment()
    observation["environment"] = environment
    if not environment.get("installed"):
        observation["status"] = "not-measured"
        observation["warnings"].append(
            {"code": "docling-not-installed", "details": None}
        )
        observation["duration_seconds"] = round(time.perf_counter() - started, 9)
        return observation
    if environment.get("docling_version") != DOCLING_VERSION:
        observation["status"] = "blocked"
        observation["warnings"].append(
            {
                "code": "docling-version-mismatch",
                "details": {
                    "expected": DOCLING_VERSION,
                    "observed": environment.get("docling_version"),
                },
            }
        )
        observation["duration_seconds"] = round(time.perf_counter() - started, 9)
        return observation

    artifacts = artifact_manifest(artifacts_path)
    observation["model_artifacts"] = artifacts
    if not artifacts["exists"] or artifacts["file_count"] == 0:
        observation["status"] = "blocked"
        observation["warnings"].append(
            {"code": "docling-model-artifacts-missing", "details": str(artifacts_path)}
        )
        observation["duration_seconds"] = round(time.perf_counter() - started, 9)
        return observation

    cache_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="raiatea-docling-") as tmp:
        controlled = Path(tmp)
        input_dir = controlled / "input"
        input_dir.mkdir()
        local_input = input_dir / source.name
        local_input.write_bytes(source.read_bytes())

        baseline_cache = artifact_manifest(cache_root)
        try:
            with _offline_environment(artifacts_path, cache_root):
                from docling.datamodel.accelerator_options import (  # type: ignore[import-not-found]
                    AcceleratorDevice,
                    AcceleratorOptions,
                )
                from docling.datamodel.base_models import InputFormat  # type: ignore[import-not-found]
                from docling.datamodel.pipeline_options import (  # type: ignore[import-not-found]
                    PdfPipelineOptions,
                )
                from docling.document_converter import (  # type: ignore[import-not-found]
                    DocumentConverter,
                    PdfFormatOption,
                )

                pipeline_options = PdfPipelineOptions()
                pipeline_options.artifacts_path = artifacts_path.resolve()
                pipeline_options.enable_remote_services = False
                pipeline_options.allow_external_plugins = False
                pipeline_options.do_ocr = False
                pipeline_options.do_table_structure = False
                pipeline_options.do_code_enrichment = False
                pipeline_options.do_formula_enrichment = False
                pipeline_options.do_picture_classification = False
                pipeline_options.do_picture_description = False
                pipeline_options.do_chart_extraction = False
                pipeline_options.generate_page_images = False
                pipeline_options.generate_picture_images = False
                pipeline_options.generate_table_images = False
                pipeline_options.generate_parsed_pages = False
                pipeline_options.force_backend_text = False
                pipeline_options.accelerator_options = AcceleratorOptions(
                    num_threads=4,
                    device=AcceleratorDevice.CPU,
                )

                converter = DocumentConverter(
                    allowed_formats=[InputFormat.PDF],
                    format_options={
                        InputFormat.PDF: PdfFormatOption(
                            pipeline_options=pipeline_options,
                        )
                    },
                )
                result = converter.convert(local_input)
                provider_status = str(result.status)
                exported = result.document.export_to_dict()
        except Exception as exc:  # runtime/provider failures are benchmark evidence
            observation["status"] = "failed"
            observation["warnings"].append(
                {
                    "code": "docling-conversion-failed",
                    "details": f"{type(exc).__name__}: {exc}",
                }
            )
            observation["cache_after"] = artifact_manifest(cache_root)
            observation["duration_seconds"] = round(time.perf_counter() - started, 9)
            return observation

    raw = json.dumps(
        exported,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    mapped = map_docling_document(exported)
    observation.update(mapped)
    observation["provider_conversion_status"] = provider_status
    if "success" not in provider_status.lower():
        observation["status"] = "degraded"
        observation["warnings"].append(
            {
                "code": "docling-provider-status-not-success",
                "details": provider_status,
            }
        )
    observation["raw_document"] = exported
    observation["raw_output_sha256"] = hashlib.sha256(raw).hexdigest()
    observation["raw_output_bytes"] = len(raw)
    observation["model_artifacts"] = artifacts
    observation["cache_before"] = baseline_cache
    observation["cache_after"] = artifact_manifest(cache_root)
    observation["route_options"] = {
        "artifacts_path": "<controlled-preloaded-model-root>",
        "do_ocr": False,
        "do_table_structure": False,
        "do_code_enrichment": False,
        "do_formula_enrichment": False,
        "do_picture_classification": False,
        "do_picture_description": False,
        "do_chart_extraction": False,
        "enable_remote_services": False,
        "allow_external_plugins": False,
        "force_backend_text": False,
        "accelerator_device": "cpu",
        "accelerator_threads": 4,
        "hf_hub_offline": True,
        "transformers_offline": True,
        "controlled_cache_root": True,
    }
    observation["duration_seconds"] = round(time.perf_counter() - started, 9)
    return observation
