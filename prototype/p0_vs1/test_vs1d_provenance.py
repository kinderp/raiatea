from __future__ import annotations

from datetime import datetime, timezone
import json
import unittest

from prototype.p0_vs1.test_vs1d import Vs1dFixture


class Vs1dProductProvenanceTests(Vs1dFixture):
    def test_persisted_extraction_has_real_product_provenance(self) -> None:
        before = datetime.now(timezone.utc)
        self.extraction.extract(
            self.source_ref_id,
            rights_evidence_state="known-permitted",
        )
        after = datetime.now(timezone.utc)

        row = self.store.load().payload["vs1d"]["extractions"][0]
        serialized = json.dumps(row, sort_keys=True)
        self.assertNotIn("benchmark-normalized-view", serialized)
        self.assertNotIn("benchmark-observation", serialized)
        self.assertNotIn("benchmark mapper", serialized.lower())
        self.assertIn("official-local-extractor", serialized)
        self.assertIn("plugin-observation:direct-epub-stdlib", serialized)

        processing_runs = [
            row["records"][ref["ref_id"]]
            for ref in row["record_refs"]
            if ref["record_kind"] == "ProcessingRunRecord"
        ]
        self.assertEqual(len(processing_runs), 1)
        provenance = processing_runs[0]["provenance"]
        started = datetime.fromisoformat(provenance["started_at"].replace("Z", "+00:00"))
        ended = datetime.fromisoformat(provenance["ended_at"].replace("Z", "+00:00"))
        self.assertLessEqual(before, started)
        self.assertLessEqual(started, ended)
        self.assertLessEqual(ended, after)
        self.assertEqual(
            provenance["provider_native_status_basis"],
            "Official local direct EPUB parser observation status",
        )


if __name__ == "__main__":
    unittest.main()
