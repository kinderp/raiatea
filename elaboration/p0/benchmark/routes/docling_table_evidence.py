"""Explicit Docling table evidence for B01-PDF-005.

This benchmark-only mapper consumes the lossless Docling JSON shape and preserves
only Provider-originated table, cell, topology, role and coordinate evidence.
It never reconstructs rows/columns from spatial proximity. Missing or malformed
collections remain degraded/unknown rather than becoming a false zero.
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
        "topology_policy": "explicit Docling row/column offsets only; no spatial reconstruction",
        "identity_policy": "table identity is not inferred from list position",
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
                {
                    "code": "docling-table-data-unavailable",
                    "details": {"ref": provider_ref},
                }
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
                {
                    "code": "docling-table-cells-unavailable",
                    "details": {"ref": provider_ref},
                }
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
                        "details": {
                            "table_ref": provider_ref,
                            "index": cell_index,
                            "type": type(cell).__name__,
                        },
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
                            "details": {
                                "table_ref": provider_ref,
                                "index": cell_index,
                                "reason": warning,
                            },
                        }
                    )
            mapped_cells.append(mapped_cell)

        if malformed_cell:
            # Partial cells can still be inspected as raw evidence, but cannot
            # establish a complete grid/topology claim.
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

    if invalid_table_item:
        # A partially malformed Provider collection cannot support a trustworthy
        # table count or identity claim.
        result["tables"] = None
    else:
        result["tables"] = mapped_tables
    return result
