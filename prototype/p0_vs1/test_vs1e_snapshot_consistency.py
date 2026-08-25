from __future__ import annotations

from unittest.mock import patch

from prototype.p0_vs1.test_vs1e import Vs1eFixture, plan


class SnapshotConsistencyTests(Vs1eFixture):
    def test_view_evaluation_does_not_reload_through_public_search(self) -> None:
        self.search.save_view(
            "view:headings",
            plan(("semantic_type", "has", "heading")),
            ["source_ref_id", "unit_count"],
        )
        with patch.object(
            self.search,
            "search",
            side_effect=AssertionError("evaluate_view must not reload catalog"),
        ):
            result = self.search.evaluate_view("view:headings")
        self.assertEqual(result["freshness"], "fresh")
        self.assertEqual(len(result["source_ids"]), 2)

    def test_smart_collection_create_and_reevaluate_do_not_reload_public_search(self) -> None:
        with patch.object(
            self.search,
            "search",
            side_effect=AssertionError("smart collection must use loaded snapshot"),
        ):
            created = self.search.save_smart_collection(
                "smart:headings",
                plan(("semantic_type", "has", "heading")),
            )
        self.assertEqual(len(created["members"]), 2)

        with patch.object(
            self.search,
            "search",
            side_effect=AssertionError("reevaluation must use loaded snapshot"),
        ):
            refreshed = self.search.reevaluate_smart_collection("smart:headings")
        self.assertEqual(refreshed["members"], created["members"])


if __name__ == "__main__":
    import unittest

    unittest.main()
