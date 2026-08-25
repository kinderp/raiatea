from __future__ import annotations

from unittest.mock import patch

from prototype.p0_vs1.extraction_service import EpubExtractionError
from prototype.p0_vs1.local_process_client import LocalPluginProcessClient
from prototype.p0_vs1.test_vs1d import Vs1dFixture


class Vs1dSourceFenceTests(Vs1dFixture):
    def test_source_change_after_plugin_output_blocks_publication_without_catalog_event(self) -> None:
        real_invoke = LocalPluginProcessClient.invoke

        def invoke_then_change_file(client: LocalPluginProcessClient, request: dict) -> dict:
            result = real_invoke(client, request)
            # Simulate a filesystem change racing ahead of Alfred/catalog delivery.
            self.epub.write_bytes(self.epub.read_bytes() + b"changed-during-extraction")
            return result

        before = self.store.load().revision
        with patch.object(LocalPluginProcessClient, "invoke", new=invoke_then_change_file):
            with self.assertRaisesRegex(
                EpubExtractionError,
                "source-changed-during-plugin-run",
            ):
                self.extraction.extract(
                    self.source_ref_id,
                    rights_evidence_state="known-permitted",
                )
        self.assertEqual(self.store.load().revision, before)
        self.assertNotIn("vs1d", self.store.load().payload)


if __name__ == "__main__":
    import unittest

    unittest.main()
