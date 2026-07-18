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
DASHBOARD_JS = ROOT / "src" / "pilot-dashboard.js"

ROUTE_SPECS = (
    {"source": EXAMPLES / "self-attention.json", "output": "self-attention.html"},
    {"source": EXAMPLES / "query-key-value.json", "output": "query-key-value.html"},
)


def _path_lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _load_route() -> tuple[dict[str, Any], ...]:
    route: list[dict[str, Any]] = []
    outputs: set[str] = set()
    identities: set[tuple[str, object]] = set()
    for spec in ROUTE_SPECS:
        source = Path(spec["source"])
        output = str(spec["output"])
        if Path(output).name != output or output in {"", ".", ".."}:
            raise ValueError(f"invalid pilot output filename: {output!r}")
        if output in outputs:
            raise ValueError(f"duplicate pilot output filename: {output}")
        data = load_and_validate(source)
        identity = (data["id"], data["revision"])
        if identity in identities:
            raise ValueError(
                "duplicate canonical module identity in pilot route: "
                f"{data['id']} revision {data['revision']}"
            )
        outputs.add(output)
        identities.add(identity)
        route.append(
            {
                "id": data["id"],
                "revision": data["revision"],
                "title": data["title"],
                "stepCount": len(data["steps"]),
                "source": source,
                "output": output,
                "module": data,
            }
        )
    if not route:
        raise ValueError("pilot route must contain at least one module")
    return tuple(route)


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
    return '<nav class="pilot-route" aria-label="Percorso pilot">' + " · ".join(links) + "</nav>"


def _inject_navigation(document: str, navigation: str) -> str:
    if "</body>" not in document:
        raise ValueError("generated module is missing </body>")
    return document.replace("</body>", navigation + "</body>", 1)


def _public_manifest(route: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    modules: list[dict[str, Any]] = []
    for index, item in enumerate(route):
        modules.append(
            {
                "id": item["id"],
                "revision": item["revision"],
                "title": item["title"],
                "stepCount": item["stepCount"],
                "order": index,
                "file": item["output"],
                "previous": route[index - 1]["output"] if index > 0 else None,
                "next": route[index + 1]["output"] if index + 1 < len(route) else None,
            }
        )
    return {"format": "raiatea-pilot", "version": 1, "modules": modules}


def _launcher(route: tuple[dict[str, Any], ...], manifest: dict[str, Any]) -> str:
    cards = "".join(
        f'<li data-pilot-module="{html.escape(item["id"], quote=True)}">'
        f'<a href="{html.escape(item["output"], quote=True)}">'
        f'{index + 1}. {html.escape(item["title"])}</a>'
        '<p><strong data-pilot-status>Non iniziato</strong> · '
        f'<span data-pilot-count>0/{item["stepCount"]} attività verificate</span></p>'
        "</li>"
        for index, item in enumerate(route)
    )
    first = html.escape(route[0]["output"], quote=True)
    manifest_json = json.dumps(manifest, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
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
    li {{ margin-block: 1rem; }}
  </style>
</head>
<body>
  <main>
    <h1>Raiatea: primo percorso pilot</h1>
    <p>Un percorso locale in due moduli: prima collochi la self-attention nel modello, poi distingui i ruoli di query, key e value.</p>
    <p data-pilot-recommendation aria-live="polite">Prossimo passo consigliato: {html.escape(route[0]["title"])}.</p>
    <ol>{cards}</ol>
    <p><a class="start" href="{first}">Inizia il percorso</a></p>
    <p><small>Il pilot funziona offline e legge i progressi soltanto dal browser locale.</small></p>
  </main>
  <script>window.RAIATEA_PILOT={manifest_json};</script>
  <script src="pilot-dashboard.js" defer></script>
</body>
</html>
"""


def _verify_output(directory: Path, manifest: dict[str, Any]) -> None:
    required = {"index.html", "pilot-manifest.json", "pilot-dashboard.js"}
    required.update(module["file"] for module in manifest["modules"])
    missing = sorted(name for name in required if not (directory / name).is_file())
    if missing:
        raise ValueError(f"pilot output is missing files: {missing}")
    launcher = (directory / "index.html").read_text(encoding="utf-8")
    if 'src="pilot-dashboard.js"' not in launcher:
        raise ValueError("launcher is missing dashboard script")
    for module in manifest["modules"]:
        if f'href="{module["file"]}"' not in launcher:
            raise ValueError(f"launcher is missing module link {module['file']}")
        document = (directory / module["file"]).read_text(encoding="utf-8")
        for link in ("index.html", module["previous"], module["next"]):
            if link is not None and f'href="{link}"' not in document:
                raise ValueError(f"{module['file']} is missing route link {link}")
    generated = launcher + json.dumps(manifest, ensure_ascii=False)
    if str(directory.resolve()) in generated:
        raise ValueError("pilot output contains an absolute output path")


def _install_directory_no_replace(staged: Path, output: Path, manifest: dict[str, Any]) -> None:
    try:
        os.mkdir(output, 0o755)
    except FileExistsError as exc:
        raise ValueError("pilot output path already exists") from exc
    installed: list[Path] = []
    try:
        for source in sorted(staged.iterdir(), key=lambda path: path.name):
            if not source.is_file() or source.is_symlink():
                raise ValueError(f"pilot staging contains a non-regular file: {source.name}")
            destination = output / source.name
            try:
                os.link(source, destination, follow_symlinks=False)
            except FileExistsError as exc:
                raise ValueError("pilot output changed during installation") from exc
            installed.append(destination)
        _verify_output(output, manifest)
    except BaseException:
        for destination in reversed(installed):
            try:
                destination.unlink()
            except FileNotFoundError:
                pass
        try:
            output.rmdir()
        except OSError:
            pass
        raise


def build_pilot(output: Path) -> Path:
    if _path_lexists(output):
        raise ValueError("pilot output path already exists")
    output_parent = output.parent.resolve()
    output_parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output_parent))
    try:
        route = _load_route()
        template = TEMPLATE.read_text(encoding="utf-8")
        css = CSS.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        dashboard_js = DASHBOARD_JS.read_text(encoding="utf-8")
        for index, item in enumerate(route):
            document = render_module(item["module"], template, css, js)
            raise_for_issues(validate_rendered_html(document))
            previous = route[index - 1] if index > 0 else None
            next_item = route[index + 1] if index + 1 < len(route) else None
            document = _inject_navigation(document, _navigation(previous, next_item))
            raise_for_issues(validate_rendered_html(document))
            (temporary / item["output"]).write_text(document, encoding="utf-8")
        manifest = _public_manifest(route)
        (temporary / "index.html").write_text(_launcher(route, manifest), encoding="utf-8")
        (temporary / "pilot-dashboard.js").write_text(dashboard_js, encoding="utf-8")
        (temporary / "pilot-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _verify_output(temporary, manifest)
        _install_directory_no_replace(temporary, output, manifest)
        return output
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


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
