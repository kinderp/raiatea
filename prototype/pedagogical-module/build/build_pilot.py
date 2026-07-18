#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from build_module import render_module
from validate_module_v2 import load_and_validate, raise_for_issues, validate_rendered_html

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "examples"
TEMPLATE = ROOT / "src" / "template.html"
CSS = ROOT / "src" / "module.css"
JS = ROOT / "src" / "module.js"

ROUTE = (
    {
        "id": "query-key-value",
        "title": "Query, key e value",
        "source": EXAMPLES / "query-key-value.json",
        "output": "query-key-value.html",
    },
    {
        "id": "self-attention",
        "title": "Self-attention",
        "source": EXAMPLES / "self-attention.json",
        "output": "self-attention.html",
    },
)


def _navigation(previous: dict[str, Any] | None, next_item: dict[str, Any] | None) -> str:
    links: list[str] = ['<a href="index.html">Indice del pilot</a>']
    if previous is not None:
        links.append(
            f'<a href="{html.escape(previous["output"], quote=True)}">'
            f'← {html.escape(previous["title"])}</a>'
        )
    if next_item is not None:
        links.append(
            f'<a href="{html.escape(next_item["output"], quote=True)}">'
            f'{html.escape(next_item["title"])} →</a>'
        )
    return (
        '<nav class="pilot-route" aria-label="Percorso pilot">'
        + " · ".join(links)
        + "</nav>"
    )


def _inject_navigation(document: str, navigation: str) -> str:
    marker = "</body>"
    if marker not in document:
        raise ValueError("generated module is missing </body>")
    return document.replace(marker, navigation + marker, 1)


def _launcher(route: tuple[dict[str, Any], ...]) -> str:
    cards = "".join(
        "<li>"
        f'<a href="{html.escape(item["output"], quote=True)}">'
        f'{index + 1}. {html.escape(item["title"])}</a>'
        "</li>"
        for index, item in enumerate(route)
    )
    first = html.escape(route[0]["output"], quote=True)
    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Raiatea pilot</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 52rem; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; }}
    main {{ border: 1px solid #bbb; border-radius: 1rem; padding: 1.5rem; }}
    .start {{ display: inline-block; padding: .7rem 1rem; border: 1px solid currentColor; border-radius: .6rem; }}
  </style>
</head>
<body>
  <main>
    <h1>Raiatea: primo percorso pilot</h1>
    <p>Un percorso locale in due moduli per passare da query, key e value alla self-attention.</p>
    <ol>{cards}</ol>
    <p><a class="start" href="{first}">Inizia il percorso</a></p>
    <p><small>Il pilot funziona offline e salva i progressi soltanto nel browser locale.</small></p>
  </main>
</body>
</html>
"""


def _manifest(route: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    modules: list[dict[str, Any]] = []
    for index, item in enumerate(route):
        modules.append(
            {
                "id": item["id"],
                "title": item["title"],
                "order": index,
                "file": item["output"],
                "previous": route[index - 1]["output"] if index > 0 else None,
                "next": route[index + 1]["output"] if index + 1 < len(route) else None,
            }
        )
    return {"format": "raiatea-pilot", "version": 1, "modules": modules}


def _verify_output(directory: Path, manifest: dict[str, Any]) -> None:
    required = {"index.html", "pilot-manifest.json"}
    required.update(module["file"] for module in manifest["modules"])
    missing = sorted(name for name in required if not (directory / name).is_file())
    if missing:
        raise ValueError(f"pilot output is missing files: {missing}")

    for module in manifest["modules"]:
        document = (directory / module["file"]).read_text(encoding="utf-8")
        for link in ("index.html", module["previous"], module["next"]):
            if link is not None and f'href="{link}"' not in document:
                raise ValueError(f"{module['file']} is missing route link {link}")

    serialized = json.dumps(manifest, ensure_ascii=False)
    if str(directory.resolve()) in serialized:
        raise ValueError("pilot manifest contains an absolute output path")


def build_pilot(output: Path) -> Path:
    if output.exists():
        raise ValueError("pilot output path already exists")
    output_parent = output.parent.resolve()
    output_parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output_parent))
    try:
        template = TEMPLATE.read_text(encoding="utf-8")
        css = CSS.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        for index, item in enumerate(ROUTE):
            data = load_and_validate(item["source"])
            document = render_module(data, template, css, js)
            raise_for_issues(validate_rendered_html(document))
            previous = ROUTE[index - 1] if index > 0 else None
            next_item = ROUTE[index + 1] if index + 1 < len(ROUTE) else None
            document = _inject_navigation(document, _navigation(previous, next_item))
            (temporary / item["output"]).write_text(document, encoding="utf-8")

        manifest = _manifest(ROUTE)
        (temporary / "index.html").write_text(_launcher(ROUTE), encoding="utf-8")
        (temporary / "pilot-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _verify_output(temporary, manifest)
        os.replace(temporary, output)
        return output
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the first runnable Raiatea pilot")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_pilot(args.output)
    except (OSError, ValueError) as exc:
        print("Pilot build failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print(result)


if __name__ == "__main__":
    main()
