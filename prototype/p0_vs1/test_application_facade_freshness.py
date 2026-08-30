from __future__ import annotations

from copy import deepcopy
import unittest

from prototype.p0_vs1.application_facade import RaiateaApplicationFacade
from prototype.p0_vs1 import test_vs1e as vs1e_tests


class ApplicationFacadeFreshnessTests(vs1e_tests.Vs1eFixture):
    def setUp(self) -> None:
        super().setUp()
        self.facade = RaiateaApplicationFacade(self.store, "scope:library")

    def test_stale_catalog_keeps_last_known_location_but_withholds_original_capability(self) -> None:
        fresh = self.facade.library_page(page_size=1)
        self.assertEqual(fresh["catalog_freshness"], "fresh")
        self.assertIn("view-original", fresh["items"][0]["capabilities"])
        self.assertIsNotNone(
            fresh["items"][0]["location"]["current_relative_location"]
        )

        current = self.store.load()
        payload = deepcopy(current.payload)
        payload["vs1b"]["freshness"] = {
            "status": "reconcile-required",
            "reason": "application-original-capability-fence-test",
        }
        self.store.save(payload, expected_revision=current.revision)

        stale = self.facade.library_page(page_size=1)
        self.assertEqual(stale["catalog_freshness"], "reconcile-required")
        item = stale["items"][0]
        self.assertIsNotNone(item["location"]["current_relative_location"])
        self.assertNotIn("view-original", item["capabilities"])
        self.assertIsNone(item["source_ref_id"])
        self.assertEqual(item["freshness"]["content"], "not-established")

        detail = self.facade.source_detail(item["item_ref"])
        self.assertNotIn("original", detail["available_panels"])
        self.assertEqual(detail["catalog_freshness"], "reconcile-required")
        self.assertIsNone(detail["source_ref_id"])
        self.assertEqual(detail["current_extractions"], [])


if __name__ == "__main__":
    unittest.main()
