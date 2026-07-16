from __future__ import annotations

import html
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def tone_class(item: dict[str, Any], default: str = "neutral") -> str:
    return f"primitive-{esc(item.get('tone', default))}"


def render_box(item: dict[str, Any]) -> str:
    x, y = item["x"], item["y"]
    width, height = item.get("width", 180), item.get("height", 72)
    title = esc(item.get("title", ""))
    subtitle = esc(item.get("subtitle", ""))
    node_id = esc(item["id"])
    subtitle_markup = (
        f'<text x="{x + width / 2}" y="{y + 48}" text-anchor="middle" class="primitive-subtitle">{subtitle}</text>'
        if subtitle
        else ""
    )
    return (
        f'<g id="{node_id}" data-node class="primitive-node {tone_class(item)}">'
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
        f'<g id="{node_id}" data-node class="primitive-node primitive-vector {tone_class(item)}">'
        f'<text x="{x}" y="{y - 10}" class="primitive-label">{label}</text>'
        f'{"".join(cells)}</g>'
    )


def render_token_row(item: dict[str, Any]) -> str:
    x, y = item["x"], item["y"]
    tokens = item.get("tokens", [])
    label = esc(item.get("label", ""))
    active_index = item.get("activeIndex")
    cell_width = item.get("cellWidth", 92)
    cells = []
    for index, token in enumerate(tokens):
        cell_x = x + index * cell_width
        active = " primitive-token-active" if index == active_index else ""
        cells.append(
            f'<g class="primitive-token{active}">'
            f'<rect x="{cell_x}" y="{y}" width="{cell_width - 6}" height="42" rx="8" />'
            f'<text x="{cell_x + (cell_width - 6) / 2}" y="{y + 26}" text-anchor="middle">{esc(token)}</text>'
            f'</g>'
        )
    return (
        f'<g id="{esc(item["id"])}" data-node class="primitive-node primitive-token-row">'
        f'<text x="{x}" y="{y - 12}" class="primitive-label">{label}</text>{"".join(cells)}</g>'
    )


def render_matrix(item: dict[str, Any]) -> str:
    x, y = item["x"], item["y"]
    values = item.get("values", [])
    row_labels = item.get("rowLabels", [])
    column_labels = item.get("columnLabels", [])
    highlight_row = item.get("highlightRow")
    highlight_column = item.get("highlightColumn")
    cell_width = item.get("cellWidth", 58)
    cell_height = item.get("cellHeight", 34)
    label = esc(item.get("label", ""))
    label_width = 54 if row_labels else 0
    parts = [f'<text x="{x}" y="{y - 14}" class="primitive-label">{label}</text>']

    for column, column_label in enumerate(column_labels):
        cx = x + label_width + column * cell_width + cell_width / 2
        parts.append(
            f'<text x="{cx}" y="{y + 18}" text-anchor="middle" class="primitive-matrix-axis">{esc(column_label)}</text>'
        )
    header_height = cell_height if column_labels else 0

    for row, row_values in enumerate(values):
        row_y = y + header_height + row * cell_height
        if row < len(row_labels):
            parts.append(
                f'<text x="{x + label_width - 8}" y="{row_y + 22}" text-anchor="end" class="primitive-matrix-axis">{esc(row_labels[row])}</text>'
            )
        for column, value in enumerate(row_values):
            cell_x = x + label_width + column * cell_width
            classes = ["primitive-matrix-cell"]
            if row == highlight_row:
                classes.append("primitive-matrix-row-highlight")
            if column == highlight_column:
                classes.append("primitive-matrix-column-highlight")
            if row == highlight_row and column == highlight_column:
                classes.append("primitive-matrix-focus")
            parts.append(
                f'<g class="{" ".join(classes)}">'
                f'<rect x="{cell_x}" y="{row_y}" width="{cell_width - 3}" height="{cell_height - 3}" rx="4" />'
                f'<text x="{cell_x + (cell_width - 3) / 2}" y="{row_y + cell_height * .66}" text-anchor="middle">{esc(value)}</text>'
                f'</g>'
            )
    return (
        f'<g id="{esc(item["id"])}" data-node class="primitive-node primitive-matrix {tone_class(item)}">'
        f'{"".join(parts)}</g>'
    )


def render_weighted_sum(item: dict[str, Any]) -> str:
    x, y = item["x"], item["y"]
    terms = item.get("terms", [])
    result = item.get("result", [])
    label = esc(item.get("label", "Somma pesata"))
    term_markup = []
    cursor_x = x
    for index, term in enumerate(terms):
        if index:
            term_markup.append(
                f'<text x="{cursor_x}" y="{y + 29}" class="primitive-operator">+</text>'
            )
            cursor_x += 24
        text = f'{term.get("weight")} × {term.get("label")}'
        width = max(82, 12 * len(str(text)))
        term_markup.append(
            f'<g class="primitive-weighted-term"><rect x="{cursor_x}" y="{y}" width="{width}" height="42" rx="7" />'
            f'<text x="{cursor_x + width / 2}" y="{y + 27}" text-anchor="middle">{esc(text)}</text></g>'
        )
        cursor_x += width + 10
    term_markup.append(
        f'<text x="{cursor_x}" y="{y + 29}" class="primitive-operator">=</text>'
    )
    cursor_x += 26
    result_text = "[" + ", ".join(esc(value) for value in result) + "]"
    result_width = max(150, 12 * len(result_text))
    term_markup.append(
        f'<g class="primitive-weighted-result"><rect x="{cursor_x}" y="{y}" width="{result_width}" height="42" rx="7" />'
        f'<text x="{cursor_x + result_width / 2}" y="{y + 27}" text-anchor="middle">{result_text}</text></g>'
    )
    return (
        f'<g id="{esc(item["id"])}" data-node class="primitive-node primitive-weighted-sum {tone_class(item, "output")}">'
        f'<text x="{x}" y="{y - 13}" class="primitive-label">{label}</text>{"".join(term_markup)}</g>'
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


RENDERERS = {
    "box": render_box,
    "vector": render_vector,
    "token-row": render_token_row,
    "matrix": render_matrix,
    "weighted-sum": render_weighted_sum,
    "text": render_text,
    "edge": render_edge,
}


def render_primitives(visual: dict[str, Any]) -> str:
    width = int(visual.get("width", 920))
    height = int(visual.get("height", 520))
    title = esc(visual.get("title", "Raiatea visual"))
    description = esc(visual.get("description", ""))
    body: list[str] = []
    for item in visual.get("items", []):
        kind = item.get("kind")
        renderer = RENDERERS.get(kind)
        if renderer is None:
            raise ValueError(f"Unsupported visual primitive kind: {kind}")
        body.append(renderer(item))
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
