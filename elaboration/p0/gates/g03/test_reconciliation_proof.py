from __future__ import annotations

import unittest

from reconciliation_proof import (
    StoredInstanceEvidence,
    ambiguous_copy_delete,
    copy_candidate,
    exact_duplicate_evidence,
    location_transition,
    mark_scope_unavailable,
    observe_location_delete,
    same_path_changed_bytes,
    sha256_bytes,
)


BYTES_A = b"Raiatea fixture A\n"
BYTES_B = b"Raiatea fixture B\n"
FP_A = sha256_bytes(BYTES_A)
FP_B = sha256_bytes(BYTES_B)


def instance(
    *,
    logical_id: str = "logical:book-a",
    instance_id: str = "instance:a",
    location: str = "/library/a.epub",
    fingerprint: str = FP_A,
    fsid: str | None = "dev1:inode100",
) -> StoredInstanceEvidence:
    return StoredInstanceEvidence(
        logical_id=logical_id,
        instance_id=instance_id,
        current_location=location,
        fingerprint=fingerprint,
        filesystem_identity=fsid,
    )


class ConservativeReconciliationProofTests(unittest.TestCase):
    def assert_safe(self, outcome) -> None:
        self.assertFalse(outcome.destructive)
        self.assertTrue(outcome.evidence_basis)

    def test_exact_duplicate_different_paths_keeps_distinct_instances(self):
        left = instance()
        right = instance(
            logical_id="logical:copy-candidate",
            instance_id="instance:b",
            location="/library/copies/a.epub",
            fsid="dev1:inode200",
        )
        outcome = exact_duplicate_evidence(left, right)
        self.assertEqual(outcome.kind, "exact-duplicate-distinct-instances")
        self.assertEqual(outcome.instance_ids, ("instance:a", "instance:b"))
        self.assertIsNone(outcome.logical_id)
        self.assert_safe(outcome)

    def test_rename_preserves_candidate_identity_and_location_history(self):
        original = instance()
        updated, outcome = location_transition(
            original,
            old_location="/library/a.epub",
            new_location="/library/renamed.epub",
            observed_fingerprint=FP_A,
            observed_filesystem_identity="dev1:inode100",
        )
        self.assertEqual(updated.logical_id, original.logical_id)
        self.assertEqual(updated.instance_id, original.instance_id)
        self.assertEqual(updated.current_location, "/library/renamed.epub")
        self.assertEqual(updated.location_history, ("/library/a.epub",))
        self.assertEqual(outcome.kind, "preserve-logical-identity-candidate")
        self.assert_safe(outcome)

    def test_move_across_directories_preserves_candidate_identity(self):
        original = instance(location="/library/inbox/a.epub")
        updated, outcome = location_transition(
            original,
            old_location="/library/inbox/a.epub",
            new_location="/library/books/a.epub",
            observed_fingerprint=FP_A,
            observed_filesystem_identity="dev1:inode100",
        )
        self.assertEqual(updated.logical_id, "logical:book-a")
        self.assertEqual(updated.location_history, ("/library/inbox/a.epub",))
        self.assertIn("filesystem-identity-equal", outcome.evidence_basis)
        self.assert_safe(outcome)

    def test_same_path_changed_bytes_requires_version_reconciliation(self):
        original = instance()
        outcome = same_path_changed_bytes(original, observed_fingerprint=FP_B)
        self.assertEqual(outcome.kind, "content-version-reconciliation-required")
        self.assertTrue(outcome.requires_review)
        self.assertIn("path-is-not-content-identity", outcome.evidence_basis)
        self.assert_safe(outcome)

    def test_copy_keeps_distinct_stored_instance_candidate(self):
        original = instance()
        copied, outcome = copy_candidate(
            original,
            copied_instance_id="instance:copy",
            copied_location="/library/copy/a.epub",
            copied_fingerprint=FP_A,
            copied_filesystem_identity="dev1:inode300",
        )
        self.assertNotEqual(copied.instance_id, original.instance_id)
        self.assertNotEqual(copied.current_location, original.current_location)
        self.assertEqual(copied.fingerprint, original.fingerprint)
        self.assertEqual(outcome.kind, "exact-duplicate-copy-candidate")
        self.assertIn("copy-does-not-authorize-destructive-merge", outcome.evidence_basis)
        self.assert_safe(outcome)

    def test_ambiguous_copy_delete_with_multiple_byte_matches_stays_unresolved(self):
        original = instance()
        candidate_one = instance(
            logical_id="logical:c1",
            instance_id="instance:c1",
            location="/other/a.epub",
            fsid="dev2:inode1",
        )
        candidate_two = instance(
            logical_id="logical:c2",
            instance_id="instance:c2",
            location="/other/b.epub",
            fsid="dev2:inode2",
        )
        outcome = ambiguous_copy_delete(original, (candidate_one, candidate_two))
        self.assertEqual(outcome.kind, "ambiguous-unresolved")
        self.assertTrue(outcome.requires_review)
        self.assertIn("list-order-and-path-similarity-forbidden-as-tie-breakers", outcome.evidence_basis)
        self.assert_safe(outcome)

    def test_single_byte_match_without_filesystem_continuity_stays_unresolved(self):
        original = instance()
        candidate = instance(
            logical_id="logical:c1",
            instance_id="instance:c1",
            location="/other/a.epub",
            fsid="dev2:inode1",
        )
        outcome = ambiguous_copy_delete(original, (candidate,))
        self.assertEqual(outcome.kind, "ambiguous-unresolved")
        self.assertTrue(outcome.requires_review)
        self.assertIn("copy-vs-cross-filesystem-move-unresolved", outcome.evidence_basis)
        self.assert_safe(outcome)

    def test_offline_scope_marks_unknown_without_deleting_identity(self):
        original = instance()
        unavailable = mark_scope_unavailable((original,))[0]
        self.assertEqual(unavailable.availability, "unavailable-or-unknown")
        self.assertEqual(unavailable.logical_id, original.logical_id)
        self.assertEqual(unavailable.instance_id, original.instance_id)
        self.assertEqual(unavailable.current_location, original.current_location)

    def test_delete_is_location_level_and_retains_logical_history(self):
        original = instance()
        updated, outcome = observe_location_delete(original, location="/library/a.epub")
        self.assertEqual(updated.availability, "confirmed-missing-at-location")
        self.assertEqual(updated.logical_id, original.logical_id)
        self.assertEqual(updated.instance_id, original.instance_id)
        self.assertEqual(outcome.kind, "location-disappeared-observed")
        self.assertIn("logical-history-retained", outcome.evidence_basis)
        self.assert_safe(outcome)

    def test_path_transition_rejects_changed_bytes(self):
        original = instance()
        with self.assertRaisesRegex(ValueError, "transition-fingerprint-mismatch"):
            location_transition(
                original,
                old_location="/library/a.epub",
                new_location="/library/b.epub",
                observed_fingerprint=FP_B,
                observed_filesystem_identity="dev1:inode100",
            )

    def test_path_transition_rejects_conflicting_filesystem_identity(self):
        original = instance()
        with self.assertRaisesRegex(ValueError, "transition-filesystem-identity-mismatch"):
            location_transition(
                original,
                old_location="/library/a.epub",
                new_location="/library/b.epub",
                observed_fingerprint=FP_A,
                observed_filesystem_identity="dev1:inode999",
            )


if __name__ == "__main__":
    unittest.main()
