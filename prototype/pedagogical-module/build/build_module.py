#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parent
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from render_visual import render_visual  # noqa: E402
from validate_module import (  # noqa: E402
    ModuleValidationError,
    load_and_validate,
    raise_for_issues,
    validate_rendered_html,
)


def escape(text: str) -> str:
    return html.escape(text, quote=True)


def render_list(items: list[str], tag: str = "li") -> str:
    return "".join(f"<{tag}>{escape(item)}</{tag}>" for item in items)


def render_module(data: dict, template: str, css: str, js: str) -> str:
    prerequisite_items = "".join(
        f"<li><b>{escape(item['level'].title())}:</b> {escape(item['summary'])}</li>"
        for item in data["prerequisites"]
    )
    previous_chips = "".join(
        f'<span class="chip">{escape(item)}</span>'
        for item in data["route"]["previous"]
    )
    step_buttons = "".join(
        f'<button data-step="{index}">{index + 1} · {escape(item["title"])}</button>'
        for index, item in enumerate(data["steps"])
    )
    concept_cards = "".join(
        f'<div class="concept" id="concept-{escape(item["id"])}" tabindex="-1">'
        f'<h4>{escape(item["label"])}</h4><p>{escape(item["definition"])}</p>'
        f'{f"<p><small>Serve per: {escape(item["usedFor"])}</small></p>" if item.get("usedFor") else ""}'
        f'{f"<p><small>Da non confondere con: {escape(item["confusedWith"])}</small></p>" if item.get("confusedWith") else ""}'
        f'</div>'
        for item in data["concepts"]
    )

    source = data.get("source", {})
    pages = source.get("pages", [])
    page_text = ", ".join(str(page) for page in pages)
    provenance = "".join(
        [
            f"<p><b>Fonte:</b> {escape(source.get('title', 'Non specificata'))}</p>",
            f"<p><b>Capitolo/sezione:</b> {escape(source.get('chapter', ''))} {escape(source.get('section', ''))}</p>",
            f"<p><b>Pagine:</b> {escape(page_text)}</p>" if page_text else "",
            f"<p><b>Figura:</b> {escape(source.get('figure', ''))}</p>",
        ]
    )

    replacements = {
        "{{ language }}": escape(data.get("language", "it")),
        "{{ title }}": escape(data["title"]),
        "{{ subtitle }}": escape(data.get("subtitle", "")),
        "{{ css }}": css,
        "{{ js }}": js,
        "{{ route_summary }}": escape(data["route"]["summary"]),
        "{{ previous_chips }}": previous_chips,
        "{{ prerequisite_items }}": prerequisite_items,
        "{{ estimated_minutes }}": str(data.get("difficulty", {}).get("minutes", "—")),
        "{{ visual_markup }}": render_visual(data.get("visual", {})),
        "{{ step_buttons }}": step_buttons,
        "{{ next_summary }}": escape(data["next"]["summary"]),
        "{{ next_items }}": render_list(data["next"]["items"]),
        "{{ provenance }}": provenance,
        "{{ concept_cards }}": concept_cards,
        "{{ module_json }}": json.dumps(data, ensure_ascii=False).replace("</", "<\/"),
    }

    output = template
    for needle, value in replacements.items():
        output = output.replace(needle, value)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a self-contained Raiatea pedagogical module"
    )
    parser.add_argument("module", type=Path, help="Path to module JSON")
    parser.add_argument("--output", type=Path, required=True, help="Output HTML path")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).parents[1] / "src/template.html",
    )
    parser.add_argument(
        "--css",
        type=Path,
        default=Path(__file__).parents[1] / "src/module.css",
    )
    parser.add_argument(
        "--js",
        type=Path,
        default=Path(__file__).parents[1] / "src/module.js",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip source and output validation (intended only for template debugging)",
    )
    args = parser.parse_args()

    try:
        data = (
            json.loads(args.module.read_text(encoding="utf-8"))
            if args.skip_validation
            else load_and_validate(args.module)
        )
        output = render_module(
            data,
            args.template.read_text(encoding="utf-8"),
            args.css.read_text(encoding="utf-8"),
            args.js.read_text(encoding="utf-8"),
        )
        if not args.skip_validation:
            raise_for_issues(validate_rendered_html(output))
    except (ModuleValidationError, ValueError) as exc:
        print("Build failed validation:")
        if isinstance(exc, ModuleValidationError):
            for issue in exc.issues:
                print(f"- {issue}")
        else:
            print(f"- {exc}")
        raise SystemExit(1) from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
