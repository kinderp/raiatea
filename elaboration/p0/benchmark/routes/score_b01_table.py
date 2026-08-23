"""Provider-neutral B01-PDF-005 table benchmark scoring.

This module is benchmark-only. It keeps visible authored cell text, explicit
Provider table presence, topology, roles and geometry as distinct dimensions.
It never reconstructs table structure from spatial proximity and never binds a
Provider table to gold by list position when identity is ambiguous.
"""

from __future__ import annotations

import re
from typing import Any


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _gold_table(gold_fixture: dict[str, Any]) -> dict[str, Any] | None:
    tables = gold_fixture.get("tables")
    if isinstance(tables, list) and len(tables) == 1 and isinstance(tables[0], dict):
        return tables[0]
    return None


def _page_text(observation: dict[str, Any]) -> str | None:
    blocks = observation.get("blocks")
    if not isinstance(blocks, list):
        return None
    parts = [
        _normalize_text(str(block.get("text", "")))
        for block in blocks
        if isinstance(block, dict) and str(block.get("text", "")).strip()
    ]
    return " ".join(parts)


def _token_occurrences(haystack: str, needle: str) -> int:
    """Count whitespace-delimited authored text without claiming cell binding."""
    normalized_haystack = _normalize_text(haystack)
    normalized_needle = _normalize_text(needle)
    pattern = rf"(?<!\S){re.escape(normalized_needle)}(?!\S)"
    return len(re.findall(pattern, normalized_haystack))


def _cell_text_content(gold_fixture: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    table = _gold_table(gold_fixture)
    if table is None:
        return {"status": "not-applicable", "expected_count": 0, "exact_once_count": 0, "cells": []}
    page_text = _page_text(observation)
    cells = table.get("cells") if isinstance(table.get("cells"), list) else []
    if page_text is None:
        return {
            "status": "not-measured",
            "reason": "The route exposes no comparable text-block collection.",
            "expected_count": len(cells),
            "exact_once_count": 0,
            "cells": [],
        }
    rows = []
    for cell in cells:
        text = str(cell.get("text", ""))
        count = _token_occurrences(page_text, text)
        rows.append(
            {
                "gold_cell": cell.get("id"),
                "expected_text": text,
                "occurrences_in_provider_text": count,
                "exact_once": count == 1,
            }
        )
    return {
        "status": "measured",
        "expected_count": len(rows),
        "exact_once_count": sum(row["exact_once"] for row in rows),
        "cells": rows,
        "binding": "page-text-presence-only",
        "policy": (
            "visible text presence is independent from table/cell structural identity; "
            "this dimension never proves Provider-native table topology"
        ),
    }


def _edge_errors(observed: list[float], expected: list[float]) -> dict[str, Any]:
    signed = [float(observed[index]) - float(expected[index]) for index in range(4)]
    absolute = [abs(value) for value in signed]
    return {
        "signed_edge_error_points": signed,
        "absolute_edge_error_points": absolute,
        "max_absolute_edge_error_points": max(absolute),
        "bbox_exact": all(value == 0.0 for value in absolute),
    }


def _explicit_table_dimensions(
    gold_fixture: dict[str, Any],
    observation: dict[str, Any],
) -> dict[str, Any]:
    gold = _gold_table(gold_fixture)
    if gold is None:
        return {
            "table_presence": {"status": "not-applicable", "expected_count": 0},
            "table_topology": {"status": "not-applicable"},
            "explicit_cell_text": {"status": "not-applicable"},
            "header_roles": {"status": "not-applicable"},
            "table_geometry": {"status": "not-applicable"},
            "cell_geometry": {"status": "not-applicable"},
        }

    observed_tables = observation.get("tables")
    if not isinstance(observed_tables, list):
        reason = "The measured route exposes no trustworthy explicit table collection."
        return {
            "table_presence": {
                "status": "not-measured",
                "reason": reason,
                "expected_count": 1,
                "observed_count": None,
            },
            "table_topology": {"status": "not-measured", "reason": reason},
            "explicit_cell_text": {"status": "not-measured", "reason": reason},
            "header_roles": {"status": "not-measured", "reason": reason},
            "table_geometry": {"status": "not-measured", "reason": reason},
            "cell_geometry": {"status": "not-measured", "reason": reason},
        }

    presence = {
        "status": "measured",
        "expected_count": 1,
        "observed_count": len(observed_tables),
        "count_exact": len(observed_tables) == 1,
        "policy": "explicit Provider table records only",
    }
    if len(observed_tables) != 1 or not isinstance(observed_tables[0], dict):
        reason = (
            "Table count is observable, but the authored table identity is ambiguous; "
            "no list-position matching is allowed."
        )
        return {
            "table_presence": presence,
            "table_topology": {"status": "not-measured", "reason": reason},
            "explicit_cell_text": {"status": "not-measured", "reason": reason},
            "header_roles": {"status": "not-measured", "reason": reason},
            "table_geometry": {"status": "not-measured", "reason": reason},
            "cell_geometry": {"status": "not-measured", "reason": reason},
        }

    provider = observed_tables[0]
    provider_cells = provider.get("cells")
    provider_rows = provider.get("row_count")
    provider_columns = provider.get("column_count")
    gold_cells = gold.get("cells") if isinstance(gold.get("cells"), list) else []
    topology_complete = provider.get("topology_complete") is True

    topology: dict[str, Any]
    cell_text: dict[str, Any]
    header_roles: dict[str, Any]
    cell_geometry: dict[str, Any]

    if not topology_complete or not isinstance(provider_cells, list):
        reason = (
            "The Provider exposes an explicit table but not a complete explicit cell grid; "
            "spatial reconstruction is not substituted."
        )
        topology = {
            "status": "not-measured",
            "reason": reason,
            "expected_rows": gold.get("row_count"),
            "observed_rows": provider_rows,
            "expected_columns": gold.get("column_count"),
            "observed_columns": provider_columns,
        }
        cell_text = {"status": "not-measured", "reason": reason}
        header_roles = {"status": "not-measured", "reason": reason}
        cell_geometry = {"status": "not-measured", "reason": reason}
    else:
        provider_by_coord: dict[tuple[int, int], dict[str, Any]] = {}
        duplicate_coords = False
        for cell in provider_cells:
            if not isinstance(cell, dict):
                duplicate_coords = True
                continue
            row = cell.get("row")
            column = cell.get("column")
            if not isinstance(row, int) or not isinstance(column, int):
                duplicate_coords = True
                continue
            key = (row, column)
            if key in provider_by_coord:
                duplicate_coords = True
            provider_by_coord[key] = cell

        expected_coords = {(cell["row"], cell["column"]) for cell in gold_cells}
        observed_coords = set(provider_by_coord)
        topology_exact = (
            not duplicate_coords
            and provider_rows == gold.get("row_count")
            and provider_columns == gold.get("column_count")
            and observed_coords == expected_coords
            and len(provider_cells) == len(gold_cells)
        )
        topology = {
            "status": "measured",
            "expected_rows": gold.get("row_count"),
            "observed_rows": provider_rows,
            "expected_columns": gold.get("column_count"),
            "observed_columns": provider_columns,
            "expected_cell_count": len(gold_cells),
            "observed_cell_count": len(provider_cells),
            "coordinate_set_exact": observed_coords == expected_coords,
            "duplicate_or_invalid_coordinates": duplicate_coords,
            "topology_exact": topology_exact,
            "policy": "explicit Provider row/column coordinates only; no spatial reconstruction",
        }

        if topology_exact:
            text_rows = []
            role_rows = []
            geometry_rows = []
            for gold_cell in gold_cells:
                key = (gold_cell["row"], gold_cell["column"])
                provider_cell = provider_by_coord[key]
                observed_text = provider_cell.get("text")
                expected_text = gold_cell.get("text")
                text_exact = (
                    isinstance(observed_text, str)
                    and _normalize_text(observed_text) == _normalize_text(str(expected_text))
                )
                text_rows.append(
                    {
                        "gold_cell": gold_cell.get("id"),
                        "row": key[0],
                        "column": key[1],
                        "expected_text": expected_text,
                        "observed_text": observed_text,
                        "exact": text_exact,
                    }
                )

                expected_role = gold_cell.get("role")
                observed_role = provider_cell.get("role")
                role_rows.append(
                    {
                        "gold_cell": gold_cell.get("id"),
                        "expected_role": expected_role,
                        "observed_role": observed_role,
                        "evidence_available": observed_role is not None,
                        "exact": observed_role == expected_role if observed_role is not None else None,
                    }
                )

                expected_bbox = gold_cell.get("region")
                observed_bbox = provider_cell.get("bbox_points_bottom_left")
                available = (
                    isinstance(expected_bbox, list)
                    and len(expected_bbox) == 4
                    and isinstance(observed_bbox, list)
                    and len(observed_bbox) == 4
                )
                geometry_rows.append(
                    {
                        "gold_cell": gold_cell.get("id"),
                        "evidence_available": available,
                        "expected_bbox_points_bottom_left": expected_bbox,
                        "observed_bbox_points_bottom_left": observed_bbox,
                        **(_edge_errors(observed_bbox, expected_bbox) if available else {}),
                    }
                )

            cell_text = {
                "status": "measured",
                "expected_count": len(text_rows),
                "exact_count": sum(row["exact"] for row in text_rows),
                "cells": text_rows,
                "binding": "explicit-row-column-coordinate",
            }
            role_evidence = sum(row["evidence_available"] for row in role_rows)
            header_roles = {
                "status": (
                    "measured"
                    if role_evidence == len(role_rows)
                    else "partial"
                    if role_evidence
                    else "not-measured"
                ),
                "expected_count": len(role_rows),
                "evidence_count": role_evidence,
                "exact_count": sum(row["exact"] is True for row in role_rows),
                "cells": role_rows,
            }
            geometry_evidence = sum(row["evidence_available"] for row in geometry_rows)
            measured_errors = [
                row["max_absolute_edge_error_points"]
                for row in geometry_rows
                if row["evidence_available"]
            ]
            cell_geometry = {
                "status": (
                    "measured"
                    if geometry_evidence == len(geometry_rows)
                    else "partial"
                    if geometry_evidence
                    else "not-measured"
                ),
                "expected_count": len(geometry_rows),
                "evidence_count": geometry_evidence,
                "bbox_exact_count": sum(row.get("bbox_exact") is True for row in geometry_rows),
                "max_observed_edge_error_points": max(measured_errors) if measured_errors else None,
                "cells": geometry_rows,
                "policy": "raw per-edge errors only; no post-hoc geometry tolerance",
            }
        else:
            reason = (
                "Explicit Provider topology does not uniquely match the authored grid; "
                "cell identity is not repaired by list position or spatial proximity."
            )
            cell_text = {"status": "not-measured", "reason": reason}
            header_roles = {"status": "not-measured", "reason": reason}
            cell_geometry = {"status": "not-measured", "reason": reason}

    expected_table_bbox = gold.get("region")
    observed_table_bbox = provider.get("bbox_points_bottom_left")
    page_available = isinstance(provider.get("page_index"), int)
    bbox_available = (
        isinstance(expected_table_bbox, list)
        and len(expected_table_bbox) == 4
        and isinstance(observed_table_bbox, list)
        and len(observed_table_bbox) == 4
    )
    if page_available and bbox_available:
        table_geometry = {
            "status": "measured",
            "expected_page_index": gold.get("page_index"),
            "observed_page_index": provider.get("page_index"),
            "page_exact": provider.get("page_index") == gold.get("page_index"),
            "expected_bbox_points_bottom_left": expected_table_bbox,
            "observed_bbox_points_bottom_left": observed_table_bbox,
            **_edge_errors(observed_table_bbox, expected_table_bbox),
            "matching_basis": "single-table-cardinality",
            "policy": "raw per-edge errors only; no post-hoc geometry tolerance",
        }
    else:
        table_geometry = {
            "status": "not-measured",
            "reason": "Explicit Provider table page/bbox evidence is incomplete.",
        }

    return {
        "table_presence": presence,
        "table_topology": topology,
        "explicit_cell_text": cell_text,
        "header_roles": header_roles,
        "table_geometry": table_geometry,
        "cell_geometry": cell_geometry,
    }


def measure_b01_table_dimensions(
    observation: dict[str, Any],
    gold_fixture: dict[str, Any],
) -> dict[str, Any]:
    dimensions = {
        "cell_text_content": _cell_text_content(gold_fixture, observation),
    }
    dimensions.update(_explicit_table_dimensions(gold_fixture, observation))
    return dimensions
