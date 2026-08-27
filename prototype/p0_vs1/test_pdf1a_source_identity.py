from __future__ import annotations

import hashlib
import unittest

from prototype.p0_vs1.source_contract import (
    EPUB_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    SOURCE_REFERENCE_VERSION,
    build_source_reference,
    canonical_json_bytes,
)


class Pdf1aSourceIdentityTests(unittest.TestCase):
    def test_existing_epub_source_id_keeps_the_accepted_vs1_identity_basis(self) -> None:
        item = {
            "catalog_entry_ref": "entry:legacy",
            "stored_instance_ref": "stored:legacy",
            "logical_candidate_ref": "logical:legacy",
            "media_type": EPUB_MEDIA_TYPE,
            "byte_length": 123,
            "fingerprint": "sha256:" + "a" * 64,
        }
        reference = build_source_reference("scope:library", item)
        legacy_basis = {
            "version": SOURCE_REFERENCE_VERSION,
            "scope_ref": "scope:library",
            "catalog_entry_ref": item["catalog_entry_ref"],
            "stored_instance_ref": item["stored_instance_ref"],
            "fingerprint": item["fingerprint"],
        }
        expected = "source-ref:" + hashlib.sha256(
            canonical_json_bytes(legacy_basis)
        ).hexdigest()
        self.assertEqual(reference["source_ref_id"], expected)

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
