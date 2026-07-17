#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class LayoutError(ValueError):
    pass


def _node(node: dict[str, Any], x: float, y: float, width: float, height: float) -> dict[str, Any]:
    if not isinstance(node, dict) or not node.get("id") or not node.get("title"):
        raise LayoutError("each node requires non-empty id and title")
    return {
        "kind": "box",
        "id": node["id"],
        "x": x,
        "y": y,
        "width": node.get("width", width),
        "height": node.get("height", height),
        "title": node["title"],
        **({"subtitle": node["subtitle"]} if node.get("subtitle") else {}),
        **({"tone": node["tone"]} if node.get("tone") else {}),
    }


def _edge(edge_id: str, x1: float, y1: float, x2: float, y2: float, label: str | None = None) -> dict[str, Any]:
    edge: dict[str, Any] = {"kind": "edge", "id": edge_id, "path": f"M{x1:g} {y1:g} H{x2:g}" if y1 == y2 else f"M{x1:g} {y1:g} L{x2:g} {y2:g}"}
    if label:
        edge.update({"label": label, "labelX": (x1 + x2) / 2, "labelY": (y1 + y2) / 2 - 8})
    return edge


def compile_pipeline(layout: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = layout.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise LayoutError("pipeline requires at least one node")
    x = float(layout.get("x", 40)); y = float(layout.get("y", 80))
    width = float(layout.get("nodeWidth", 180)); height = float(layout.get("nodeHeight", 76)); gap = float(layout.get("gap", 80))
    items: list[dict[str, Any]] = []
    positions: list[tuple[float, float]] = []
    for index, node in enumerate(nodes):
        nx = x + index * (width + gap)
        items.append(_node(node, nx, y, width, height)); positions.append((nx, y))
    for index in range(len(nodes) - 1):
        x1 = positions[index][0] + width; x2 = positions[index + 1][0]
        label = nodes[index].get("edgeLabel")
        items.append(_edge(f"{nodes[index]['id']}-to-{nodes[index + 1]['id']}", x1, y + height / 2, x2, y + height / 2, label))
    return items


def compile_parallel(layout: dict[str, Any]) -> list[dict[str, Any]]:
    source = layout.get("source"); branches = layout.get("branches"); target = layout.get("target")
    if not isinstance(source, dict) or not isinstance(target, dict) or not isinstance(branches, list) or len(branches) < 2:
        raise LayoutError("parallel requires source, target, and at least two branches")
    x = float(layout.get("x", 40)); y = float(layout.get("y", 50)); width = float(layout.get("nodeWidth", 170)); height = float(layout.get("nodeHeight", 72)); column_gap = float(layout.get("columnGap", 120)); row_gap = float(layout.get("rowGap", 38))
    branch_x = x + width + column_gap; target_x = branch_x + width + column_gap
    total = len(branches) * height + (len(branches) - 1) * row_gap
    center_y = y + total / 2 - height / 2
    items = [_node(source, x, center_y, width, height), _node(target, target_x, center_y, width, height)]
    source_center = (x + width, center_y + height / 2); target_center = (target_x, center_y + height / 2)
    for index, branch in enumerate(branches):
        by = y + index * (height + row_gap)
        items.append(_node(branch, branch_x, by, width, height))
        items.append(_edge(f"{source['id']}-to-{branch['id']}", source_center[0], source_center[1], branch_x, by + height / 2, branch.get("inLabel")))
        items.append(_edge(f"{branch['id']}-to-{target['id']}", branch_x + width, by + height / 2, target_center[0], target_center[1], branch.get("outLabel")))
    return items


def compile_layout(layout: dict[str, Any]) -> dict[str, Any]:
    layout_type = layout.get("type")
    if layout_type == "pipeline": items = compile_pipeline(layout)
    elif layout_type in {"parallel", "branch-merge"}: items = compile_parallel(layout)
    else: raise LayoutError("layout type must be pipeline, parallel, or branch-merge")
    return {
        "type": "primitives",
        "width": int(layout.get("width", 960)),
        "height": int(layout.get("height", 460)),
        "title": layout.get("title", "Raiatea visual"),
        "description": layout.get("description", ""),
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a declarative Raiatea layout into semantic visual primitives")
    parser.add_argument("layout", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.layout.read_text(encoding="utf-8"))
    output = compile_layout(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
