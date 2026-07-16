from __future__ import annotations

import html
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_box(item: dict[str, Any]) -> str:
    x, y = item["x"], item["y"]
    width, height = item.get("width", 180), item.get("height", 72)
    title = esc(item.get("title", ""))
    subtitle = esc(item.get("subtitle", ""))
    tone = esc(item.get("tone", "neutral"))
    node_id = esc(item["id"])
    subtitle_markup = (
        f'<text x="{x + width / 2}" y="{y + 48}" text-anchor="middle" class="primitive-subtitle">{subtitle}</text>'
        if subtitle
        else ""
    )
    return (
        f'<g id="{node_id}" data-node class="primitive-node primitive-{tone}">'
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" />'
        f'<text x="{x + width / 2}" y="{y + 28}" text-anchor="middle" class="primitive-title">{title}</text>'
        f'{subtitle_markup}</g>'
    )


def render_vector(item: dict[str, Any]) -> str:
    x, y = item["x"], item["y"]
    values = item.get("values", [])
    label = esc(item.get("label", ""))
    node_id = esc(item["id"])
    cell_width = item.get("cellWidth", 58)
    cells = []
    for index, value in enumerate(values):
        cell_x = x + index * cell_width
        cells.append(
            f'<rect x="{cell_x}" y="{y}" width="{cell_width - 4}" height="36" rx="6" />'
            f'<text x="{cell_x + (cell_width - 4) / 2}" y="{y + 23}" text-anchor="middle">{esc(value)}</text>'
        )
    return (
        f'<g id="{node_id}" data-node class="primitive-node primitive-vector">'
        f'<text x="{x}" y="{y - 10}" class="primitive-label">{label}</text>'
        f'{"".join(cells)}</g>'
    )


def render_text(item: dict[str, Any]) -> str:
    return (
        f'<text id="{esc(item["id"])}" data-node x="{item["x"]}" y="{item["y"]}" '
        f'class="primitive-text">{esc(item.get("text", ""))}</text>'
    )


def render_edge(item: dict[str, Any]) -> str:
    edge_id = esc(item["id"])
    path = esc(item["path"])
    label = item.get("label")
    label_markup = ""
    if label:
        label_markup = (
            f'<text x="{item.get("labelX", 0)}" y="{item.get("labelY", 0)}" '
            f'class="primitive-edge-label">{esc(label)}</text>'
        )
    return (
        f'<g id="{edge_id}" data-flow class="primitive-edge">'
        f'<path d="{path}" marker-end="url(#primitive-arrow)" />{label_markup}</g>'
    )


def render_primitives(visual: dict[str, Any]) -> str:
    width = int(visual.get("width", 920))
    height = int(visual.get("height", 520))
    title = esc(visual.get("title", "Raiatea visual"))
    description = esc(visual.get("description", ""))
    body: list[str] = []
    for item in visual.get("items", []):
        kind = item.get("kind")
        if kind == "box":
            body.append(render_box(item))
        elif kind == "vector":
            body.append(render_vector(item))
        elif kind == "text":
            body.append(render_text(item))
        elif kind == "edge":
            body.append(render_edge(item))
        else:
            raise ValueError(f"Unsupported visual primitive kind: {kind}")
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="visual-title visual-desc">'
        f'<title id="visual-title">{title}</title><desc id="visual-desc">{description}</desc>'
        '<defs><marker id="primitive-arrow" markerWidth="11" markerHeight="11" refX="9" refY="5.5" orient="auto">'
        '<path d="M0,0 L11,5.5 L0,11 z" /></marker></defs>'
        f'{"".join(body)}</svg>'
    )


def render_visual(visual: dict[str, Any]) -> str:
    if visual.get("type") == "primitives":
        return render_primitives(visual)
    return visual.get("markup", "")
