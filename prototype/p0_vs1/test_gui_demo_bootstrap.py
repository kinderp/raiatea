from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from prototype.p0_vs1.application_facade import RaiateaApplicationFacade
from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.gui_demo_bootstrap import (
    DEMO_CONTRACT,
    DEMO_SCOPE_ID,
    GuiDemoBootstrapError,
    bootstrap_demo,
)


class GuiDemoBootstrapTests(unittest.TestCase):
    def test_bootstrap_builds_real_reopenable_application_state_and_is_rerunnable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve() / "demo"

            first = bootstrap_demo(workspace)
            self.assertEqual(first["contract"], DEMO_CONTRACT)
            self.assertEqual(first["scope_id"], DEMO_SCOPE_ID)
            self.assertEqual(first["known_sources"], 2)
            self.assertGreaterEqual(first["search_probe_matches"], 1)

            store = CatalogStateStore(Path(first["catalog_store"]))
            facade = RaiateaApplicationFacade(store, DEMO_SCOPE_ID)
            library = facade.library_page(page_size=50)
            self.assertEqual(library["catalog_freshness"], "fresh")
            self.assertEqual(library["total_known_items"], 2)
            self.assertTrue(all(item["source_ref_id"] for item in library["items"]))
            self.assertTrue(all(item["extraction"]["state"] == "current" for item in library["items"]))

            second = bootstrap_demo(workspace)
            self.assertEqual(second["contract"], first["contract"])
            self.assertEqual(second["scope_id"], first["scope_id"])
            self.assertEqual(second["catalog_store"], first["catalog_store"])
            self.assertEqual(second["known_sources"], first["known_sources"])
            self.assertEqual(second["search_probe_matches"], first["search_probe_matches"])

    def test_bootstrap_refuses_to_delete_unmarked_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve() / "not-a-demo"
            workspace.mkdir()
            sentinel = workspace / "keep-me.txt"
            sentinel.write_text("user data", encoding="utf-8")

            with self.assertRaisesRegex(
                GuiDemoBootstrapError,
                "refusing-to-replace-unmarked-workspace",
            ):
                bootstrap_demo(workspace)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "user data")


if __name__ == "__main__":
    unittest.main()
