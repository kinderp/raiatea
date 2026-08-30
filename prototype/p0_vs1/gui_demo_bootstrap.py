#!/usr/bin/env python3
"""Build a disposable real Raiatea workspace for the live desktop GUI demo.

The demo uses the accepted VS1 catalog/source/extraction/search product path.
It never mutates a user Library. An existing non-empty workspace is replaced
only when it carries this module's explicit demo marker.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
from typing import Any

from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.core_access import AssetBroker
from prototype.p0_vs1.extraction_service import LocalEpubExtractionService
from prototype.p0_vs1.reconciliation import (
    Vs1ObservationScopeRegistry,
    Vs1bReconciliationEngine,
)
from prototype.p0_vs1.search_service import SearchViewService
from prototype.p0_vs1.source_service import LocalSourceDiscoveryService


DEMO_CONTRACT = "raiatea.gui-live-demo.0.1.0"
DEMO_SCOPE_ID = "scope:demo-library"
MARKER_NAME = ".raiatea-gui-demo.json"
MANIFEST_NAME = "manifest.json"

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"
_GENERATOR_SPEC = importlib.util.spec_from_file_location(
    "raiatea_gui_demo_fixture_generator", GENERATOR_PATH
)
GENERATOR = importlib.util.module_from_spec(_GENERATOR_SPEC)
assert _GENERATOR_SPEC.loader is not None
_GENERATOR_SPEC.loader.exec_module(GENERATOR)


class GuiDemoBootstrapError(ValueError):
    pass


def _canonical_write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _safe_prepare_workspace(workspace: Path) -> None:
    if workspace.exists() and workspace.is_symlink():
        raise GuiDemoBootstrapError("gui-demo-workspace-symlink-forbidden")

    marker = workspace / MARKER_NAME
    if workspace.exists() and any(workspace.iterdir()):
        if not marker.is_file():
            raise GuiDemoBootstrapError("gui-demo-refusing-to-replace-unmarked-workspace")
        try:
            current = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GuiDemoBootstrapError("gui-demo-marker-invalid") from exc
        if current != {"contract": DEMO_CONTRACT}:
            raise GuiDemoBootstrapError("gui-demo-marker-contract-mismatch")
        shutil.rmtree(workspace)

    workspace.mkdir(parents=True, exist_ok=True)
    _canonical_write(marker, {"contract": DEMO_CONTRACT})


def bootstrap_demo(workspace: Path) -> dict[str, Any]:
    workspace = workspace.expanduser().resolve()
    _safe_prepare_workspace(workspace)

    library_root = workspace / "library"
    outputs_root = workspace / "outputs"
    catalog_path = workspace / "catalog.json"
    library_root.mkdir()
    outputs_root.mkdir()

    GENERATOR.generate_epub_spine(library_root / "scientific-revolutions-demo.epub")
    GENERATOR.generate_epub_navigation(library_root / "navigation-demo.epub")

    store = CatalogStateStore(catalog_path)
    scopes = Vs1ObservationScopeRegistry()
    broker: AssetBroker | None = None
    try:
        scopes.register_scope(DEMO_SCOPE_ID, library_root)
        broker = AssetBroker(scopes, outputs_root)

        reconciliation = Vs1bReconciliationEngine(
            store,
            scopes,
            broker,
            DEMO_SCOPE_ID,
        )
        reconciliation.reconcile_inventory()

        discovery = LocalSourceDiscoveryService(store, scopes, DEMO_SCOPE_ID)
        discovered = discovery.discover(rights_evidence_state="known-permitted")

        extraction = LocalEpubExtractionService(
            store,
            scopes,
            broker,
            DEMO_SCOPE_ID,
        )
        for source_ref in discovered["source_refs"]:
            extraction.extract(
                source_ref,
                rights_evidence_state="known-permitted",
            )

        search = SearchViewService(store, DEMO_SCOPE_ID)
        search.rebuild_index()

        # Re-read through the public Application-layer dependencies used by the
        # GUI bridge rather than trusting setup-side counters.
        from prototype.p0_vs1.application_facade import RaiateaApplicationFacade

        facade = RaiateaApplicationFacade(store, DEMO_SCOPE_ID)
        library = facade.library_page(page_size=50)
        probe = facade.search_page(
            {
                "criteria": [
                    {
                        "field": "extracted_text",
                        "operator": "contains",
                        "value": "Introduction",
                    }
                ],
                "sort_field": "source_ref_id",
                "descending": False,
            },
            page_size=50,
        )
    finally:
        if broker is not None:
            broker.close()
        scopes.close()

    manifest = {
        "contract": DEMO_CONTRACT,
        "scope_id": DEMO_SCOPE_ID,
        "catalog_store": os.fspath(catalog_path),
        "workspace": os.fspath(workspace),
        "known_sources": library["total_known_items"],
        "search_probe_matches": probe["total_known_matches"],
    }
    _canonical_write(workspace / MANIFEST_NAME, manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the Raiatea live GUI demo")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(".raiatea-demo"),
        help="Disposable demo workspace (default: .raiatea-demo)",
    )
    args = parser.parse_args(argv)
    manifest = bootstrap_demo(args.workspace)
    print(json.dumps(manifest, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
