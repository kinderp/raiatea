from __future__ import annotations

import unittest

from prototype.p0_vs1.source_contract import (
    EPUB_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    build_source_reference,
)


class Pdf1aSourceIdentityTests(unittest.TestCase):
    def test_same_catalog_instance_and_bytes_use_distinct_source_ids_across_media_classes(self) -> None:
        base = {
            "catalog_entry_ref": "entry:1",
            "stored_instance_ref": "stored:1",
            "logical_candidate_ref": "logical:1",
            "byte_length": 123,
            "fingerprint": "sha256:" + "a" * 64,
        }
        epub = build_source_reference(
            "scope:library",
            {**base, "media_type": EPUB_MEDIA_TYPE},
        )
        pdf = build_source_reference(
            "scope:library",
            {**base, "media_type": PDF_MEDIA_TYPE},
        )
        self.assertNotEqual(epub["source_ref_id"], pdf["source_ref_id"])
        self.assertEqual(epub["stored_instance_ref"], pdf["stored_instance_ref"])
        self.assertEqual(epub["fingerprint"], pdf["fingerprint"])


if __name__ == "__main__":
    unittest.main()
