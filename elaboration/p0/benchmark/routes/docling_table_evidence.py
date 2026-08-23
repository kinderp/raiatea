"""Explicit Docling table evidence for B01-PDF-005.

This benchmark-only mapper consumes the lossless Docling JSON shape and preserves
only Provider-originated table, cell, topology, role, coordinate and explicitly
referenced descendant-text evidence. It never reconstructs rows/columns from
spatial proximity. Missing or malformed collections remain degraded/unknown
rather than becoming a false zero.
"""

from __future__ import annotations

from typing import Any

from docling_routes import _bbox_bottom_left, _page_sizes


def _explicit_cell_role(cell: dict[str, Any]) -> str | None:
    """Return a role only when Docling exposes an explicit boolean signal."""
    if cell.get("column_header") is True:
        return "header"
    if cell.get("row_header") is True:
        return "row-header"
    if cell.get("row_section") is True:
        return "section"
    explicit_flags = (
        cell.get("column_header"),
        cell.get("row_header"),
        cell.get("row_section"),
    )
    if all(isinstance(value, bool) for value in explicit_flags):
        return "body"
    return None


def _cell_coordinate(cell: dict[str, Any]) -> tuple[int, int, int, int] | None:
    start_row = cell.get("start_row_offset_idx")
    end_row = cell.get("end_row_offset_idx")
    start_col = cell.get("start_col_offset_idx")
    end_col = cell.get("end_col_offset_idx")
    values = (start_row, end_row, start_col, end_col)
    if not all(isinstance(value, int) for value in values):
        return None
    if start_row < 0 or start_col < 0 or end_row <= start_row or end_col <= start_col:
        return None
    return start_row, start_col, end_row - start_row, end_col - start_col


def _ref_registry(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for collection in ("texts", "groups"):
        values = document.get(collection)
        if not isinstance(values, list):
            continue
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                continue
            canonical = f"#/{collection}/{index}"
            ref = item.get("self_ref") if isinstance(item.get("self_ref"), str) else canonical
            registry[ref] = item
            registry.setdefault(canonical, item)
    return registry


def _descendant_text_blocks(
    table: dict[str, Any],
    table_ref: str,
    document: dict[str, Any],
    pages: dict[int, tuple[float, float]],
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preserve text reached through explicit table/group references.

    These blocks are intentionally *unbound* to authored row/column coordinates.
    A Provider may retain text below a table container even when its explicit
    table topology collapses. That text can support content preservation but
    never repairs Provider cell identity or topology.
    """
    registry = _ref_registry(document)
    roots: list[str] = []
    for child in table.get("children", []) if isinstance(table.get("children"), list) else []:
        if isinstance(child, dict) and isinstance(child.get("$ref"), str):
            roots.append(child["$ref"])

    data = table.get("data")
    if isinstance(data, dict) and isinstance(data.get("table_cells"), list):
        for cell in data["table_cells"]:
            if not isinstance(cell, dict):
                continue
            ref_value = cell.get("ref")
            if isinstance(ref_value, dict) and isinstance(ref_value.get("$ref"), str):
                roots.append(ref_value["$ref"])

    blocks: list[dict[str, Any]] = []
    emitted: set[str] = set()
    active: set[str] = set()

    def visit(ref: str) -> None:
        if ref in active:
            result["status"] = "degraded"
            result["warnings"].append(
                {"code": "docling-table-descendant-ref-cycle", "details": {"table_ref": table_ref, "ref": ref}}
            )
            return
        item = registry.get(ref)
        if item is None:
            result["status"] = "degraded"
            result["warnings"].append(
                {"code": "docling-table-descendant-ref-unresolved", "details": {"table_ref": table_ref, "ref": ref}}
            )
            return

        children = item.get("children")
        if isinstance(children, list):
            active.add(ref)
            for child in children:
                if isinstance(child, dict) and isinstance(child.get("$ref"), str):
                    visit(child["$ref"])
            active.remove(ref)

        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            return
        provider_ref = item.get("self_ref") if isinstance(item.get("self_ref"), str) else ref
        if provider_ref in emitted:
            return
        emitted.add(provider_ref)

        block: dict[str, Any] = {
            "type": "text-block",
            "text": " ".join(text.split()),
            "provider_ref": provider_ref,
            "docling_ref": provider_ref,
            "table_ref": table_ref,
            "binding": "explicit-table-descendant-unbound-to-cell",
            "page_index": None,
            "bbox_points_bottom_left": None,
        }
        provenance = item.get("prov") if isinstance(item.get("prov"), list) else []
        if provenance and isinstance(provenance[0], dict):
            first = provenance[0]
            page_no = first.get("page_no")
            bbox = first.get("bbox")
            if isinstance(page_no, int) and page_no >= 1:
                block["page_index"] = page_no - 1
                if isinstance(bbox, dict):
                    converted, warning = _bbox_bottom_left(bbox, page_no, pages)
                    block["bbox_points_bottom_left"] = converted
                    if warning:
                        result["warnings"].append(
                            {
                                "code": "docling-table-descendant-text-provenance-degraded",
                                "details": {"table_ref": table_ref, "ref": provider_ref, "reason": warning},
                            }
                        )
        blocks.append(block)

    for ref in dict.fromkeys(roots):
        visit(ref)
    return blocks


def map_docling_table_evidence(document: dict[str, Any]) -> dict[str, Any]:
    pages = _page_sizes(document)
    tables_value = document.get("tables")
    tables_available = isinstance(tables_value, list)
    tables = tables_value if tables_available else []

    result: dict[str, Any] = {
        "route": "docling-lossless-explicit-table-evidence",
        "status": "success" if tables_available else "degraded",
        "warnings": [],
        # None means the Provider collection is unavailable/incomplete. [] means
        # it was explicitly present, structurally valid and empty.
        "tables": [] if tables_available else None,
        "unbound_table_text_blocks": [],
        "topology_policy": "explicit Docling row/column offsets only; no spatial reconstruction",
        "identity_policy": "table identity is not inferred from list position",
        "text_policy": (
            "text reached through explicit table/group refs may support content preservation, "
            "but never supplies row/column identity unless Provider cell topology does"
        ),
    }
    if not tables_available:
        result["warnings"].append(
            {
                "code": "docling-table-collection-unavailable",
                "details": (
                    "Lossless Docling output did not expose `tables` as a list; "
                    "table presence is unknown and must remain not-measured."
                ),
            }
        )
        return result

    invalid_table_item = False
    mapped_tables: list[dict[str, Any]] = []
    text_blocks: list[dict[str, Any]] = []
    for table_index, table in enumerate(tables):
        if not isinstance(table, dict):
            invalid_table_item = True
            result["status"] = "degraded"
            result["warnings"].append(
                {
                    "code": "docling-table-item-invalid",
                    "details": {"index": table_index, "type": type(table).__name__},
                }
            )
            continue

        provider_ref = table.get("self_ref") or f"#/tables/{table_index}"
        text_blocks.extend(
            _descendant_text_blocks(table, provider_ref, document, pages, result)
        )
        mapped: dict[str, Any] = {
            "provider_ref": provider_ref,
            "provider_source": "docling-explicit-table-item",
            "provider_label": table.get("label"),
            "page_index": None,
            "bbox_points_bottom_left": None,
            "row_count": None,
            "column_count": None,
            "cells": None,
            "topology_complete": False,
        }

        table_page_no: int | None = None
        provenance = table.get("prov") if isinstance(table.get("prov"), list) else []
        if provenance and isinstance(provenance[0], dict):
            first = provenance[0]
            page_no = first.get("page_no")
            bbox = first.get("bbox")
            if isinstance(page_no, int) and page_no >= 1:
                table_page_no = page_no
                mapped["page_index"] = page_no - 1
                if isinstance(bbox, dict):
                    converted, warning = _bbox_bottom_left(bbox, page_no, pages)
                    mapped["bbox_points_bottom_left"] = converted
                    if warning:
                        result["warnings"].append(
                            {
                                "code": "docling-table-provenance-degraded",
                                "details": {"ref": provider_ref, "reason": warning},
                            }
                        )

        data = table.get("data")
        if not isinstance(data, dict):
            result["status"] = "degraded"
            result["warnings"].append(
                {"code": "docling-table-data-unavailable", "details": {"ref": provider_ref}}
            )
            mapped_tables.append(mapped)
            continue

        num_rows = data.get("num_rows")
        num_cols = data.get("num_cols")
        if isinstance(num_rows, int) and num_rows >= 0:
            mapped["row_count"] = num_rows
        if isinstance(num_cols, int) and num_cols >= 0:
            mapped["column_count"] = num_cols

        cells_value = data.get("table_cells")
        if not isinstance(cells_value, list):
            result["status"] = "degraded"
            result["warnings"].append(
                {"code": "docling-table-cells-unavailable", "details": {"ref": provider_ref}}
            )
            mapped_tables.append(mapped)
            continue

        mapped_cells: list[dict[str, Any]] = []
        malformed_cell = False
        for cell_index, cell in enumerate(cells_value):
            if not isinstance(cell, dict):
                malformed_cell = True
                result["status"] = "degraded"
                result["warnings"].append(
                    {
                        "code": "docling-table-cell-invalid",
                        "details": {"table_ref": provider_ref, "index": cell_index, "type": type(cell).__name__},
                    }
                )
                continue

            coordinate = _cell_coordinate(cell)
            if coordinate is None:
                malformed_cell = True
                result["status"] = "degraded"
                result["warnings"].append(
                    {
                        "code": "docling-table-cell-coordinate-unavailable",
                        "details": {"table_ref": provider_ref, "index": cell_index},
                    }
                )
                continue
            row, column, row_span, column_span = coordinate
            text = cell.get("text")
            mapped_cell: dict[str, Any] = {
                "provider_ref": f"{provider_ref}/cells/{cell_index}",
                "row": row,
                "column": column,
                "row_span": row_span,
                "column_span": column_span,
                "text": " ".join(text.split()) if isinstance(text, str) else None,
                "role": _explicit_cell_role(cell),
                "bbox_points_bottom_left": None,
            }

            bbox = cell.get("bbox")
            if isinstance(bbox, dict) and table_page_no is not None:
                converted, warning = _bbox_bottom_left(bbox, table_page_no, pages)
                mapped_cell["bbox_points_bottom_left"] = converted
                if warning:
                    result["warnings"].append(
                        {
                            "code": "docling-table-cell-provenance-degraded",
                            "details": {"table_ref": provider_ref, "index": cell_index, "reason": warning},
                        }
                    )
            mapped_cells.append(mapped_cell)

        if malformed_cell:
            mapped["cells"] = mapped_cells
            mapped["topology_complete"] = False
        else:
            mapped["cells"] = mapped_cells
            coordinate_pairs = {(cell["row"], cell["column"]) for cell in mapped_cells}
            expected_pairs = (
                {
                    (row, column)
                    for row in range(mapped["row_count"])
                    for column in range(mapped["column_count"])
                }
                if isinstance(mapped["row_count"], int)
                and isinstance(mapped["column_count"], int)
                else None
            )
            no_spans = all(
                cell["row_span"] == 1 and cell["column_span"] == 1
                for cell in mapped_cells
            )
            mapped["topology_complete"] = bool(
                expected_pairs is not None
                and coordinate_pairs == expected_pairs
                and len(mapped_cells) == len(expected_pairs)
                and no_spans
            )
        mapped_tables.append(mapped)

    # Preserve only unique Provider text refs. These blocks remain explicitly
    # unbound to cells/topology.
    by_ref: dict[str, dict[str, Any]] = {}
    for block in text_blocks:
        ref = str(block.get("provider_ref"))
        by_ref.setdefault(ref, block)
    result["unbound_table_text_blocks"] = list(by_ref.values())

    if invalid_table_item:
        result["tables"] = None
    else:
        result["tables"] = mapped_tables
    return result
