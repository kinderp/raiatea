from __future__ import annotations

from copy import deepcopy
import unittest

from prototype.p0_vs1.backup_service import BackupServiceError, build_backup_authority
from prototype.p0_vs1.catalog_store import CatalogSnapshot
from prototype.p0_vs1.test_vs1f import Vs1fFixture


class BackupDefinitionVersionTests(Vs1fFixture):
    def test_unknown_vs1e_state_version_is_not_treated_as_derived_cache(self) -> None:
        snapshot = self.store.load()
        payload = deepcopy(snapshot.payload)
        payload["vs1e"]["state_version"] = "raiatea.vs1e.search-state.future"
        with self.assertRaisesRegex(BackupServiceError, "vs1e-version-unsupported"):
            build_backup_authority(
                CatalogSnapshot(revision=snapshot.revision, payload=payload),
                "scope:library",
            )

    def test_unknown_smart_collection_version_is_not_treated_as_member_cache(self) -> None:
        snapshot = self.store.load()
        payload = deepcopy(snapshot.payload)
        payload["vs1e"]["smart_collections"][0]["collection_version"] = (
            "raiatea.vs1e.smart-collection.future"
        )
        with self.assertRaisesRegex(
            BackupServiceError,
            "smart-collection-version-unsupported",
        ):
            build_backup_authority(
                CatalogSnapshot(revision=snapshot.revision, payload=payload),
                "scope:library",
            )


if __name__ == "__main__":
    unittest.main()
