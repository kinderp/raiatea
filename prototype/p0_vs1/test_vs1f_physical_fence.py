from __future__ import annotations

from unittest.mock import patch
import unittest

import prototype.p0_vs1.backup_service as service_module
from prototype.p0_vs1.backup_service import BackupServiceError
from prototype.p0_vs1.test_vs1f import Vs1fFixture


class PhysicalPublicationFenceTests(Vs1fFixture):
    def test_export_rejects_source_change_after_authority_snapshot(self) -> None:
        source = self.root / "renamed-spine.epub"
        original = source.read_bytes()
        real_build = service_module.build_backup_authority

        def build_then_change(snapshot, scope_ref):
            authority = real_build(snapshot, scope_ref)
            source.write_bytes(original + b"changed-during-export")
            return authority

        try:
            with patch.object(
                service_module,
                "build_backup_authority",
                new=build_then_change,
            ):
                with self.assertRaisesRegex(
                    BackupServiceError,
                    "backup-physical-source-set-mismatch",
                ):
                    self.backup.export_bytes()
        finally:
            source.write_bytes(original)

    def test_restore_rejects_source_change_after_temporary_rebuild_before_commit(self) -> None:
        raw = self.backup.export_bytes()
        target = self.new_target("physical-race.json")
        source = self.root / "renamed-spine.epub"
        original = source.read_bytes()
        real_restore = service_module._restore_vs1e

        def restore_then_change(**kwargs):
            state = real_restore(**kwargs)
            source.write_bytes(original + b"changed-before-commit")
            return state

        try:
            with patch.object(
                service_module,
                "_restore_vs1e",
                new=restore_then_change,
            ):
                with self.assertRaisesRegex(
                    BackupServiceError,
                    "restore-physical-source-changed-before-commit",
                ):
                    self.backup.restore_into_empty_store(raw, target)
            self.assertIsNone(target.load())
        finally:
            source.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
