from __future__ import annotations

from dataclasses import fields
import json
import unittest

from durability_authority_proof import (
    AuthorizationDecision,
    BoundedCatalogState,
    CoreAuthorityConfig,
    ExternalRequest,
    G07ProofError,
    LocationRecord,
    LogicalItem,
    PROOF_SCHEMA_VERSION,
    ProvenanceRecord,
    ScopeGrant,
    SmartCollectionRuleRecord,
    ViewRecord,
    assert_authority_shapes_minimal,
    authorize_request,
    build_core_authority,
    create_core_scope,
    export_catalog,
    restore_catalog,
)


def state(*, reverse: bool = False) -> BoundedCatalogState:
    items = [
        LogicalItem("logical:2", "Signals"),
        LogicalItem("logical:1", "Raiatea"),
    ]
    locations = [
        LocationRecord("location:2", "logical:2", "/library/signals.epub", "known-present"),
        LocationRecord("location:1", "logical:1", "/library/raiatea.pdf", "known-present"),
    ]
    provenance = [
        ProvenanceRecord("provenance:2", "logical:2", "alfred", "event:22"),
        ProvenanceRecord("provenance:1", "logical:1", "source-plugin", "source:11"),
    ]
    views = [
        ViewRecord(
            "view:2",
            (("tag", "has", "ai"),),
            ("item_id", "title"),
        ),
        ViewRecord(
            "view:1",
            (("media_type", "eq", "application/pdf"),),
            ("item_id", "title"),
        ),
    ]
    rules = [
        SmartCollectionRuleRecord("smart:2", (("year", "eq", "2026"),)),
        SmartCollectionRuleRecord("smart:1", (("tag", "has", "docs"),)),
    ]
    if reverse:
        items.reverse()
        locations.reverse()
        provenance.reverse()
        views.reverse()
        rules.reverse()
    return BoundedCatalogState(
        catalog_revision=7,
        logical_items=tuple(items),
        locations=tuple(locations),
        provenance=tuple(provenance),
        views=tuple(views),
        smart_collection_rules=tuple(rules),
    )


def authority() -> CoreAuthorityConfig:
    scope = create_core_scope(
        "scope:library",
        "/library",
        ("read-for-processing", "observe"),
    )
    return build_core_authority((scope,))


class CatalogDurabilityProofTests(unittest.TestCase):
    def test_export_is_byte_deterministic_under_shuffled_record_input(self):
        first = export_catalog(state(reverse=False))
        second = export_catalog(state(reverse=True))
        self.assertEqual(first, second)
        envelope = json.loads(first.decode("utf-8"))
        self.assertEqual(envelope["schema_version"], PROOF_SCHEMA_VERSION)
        self.assertRegex(envelope["payload_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_round_trip_reconstructs_bounded_catalog_state_canonically(self):
        exported = export_catalog(state(reverse=True))
        restored = restore_catalog(exported)
        self.assertEqual(export_catalog(restored), exported)
        self.assertEqual(restored.catalog_revision, 7)
        self.assertEqual(tuple(row.logical_id for row in restored.logical_items), ("logical:1", "logical:2"))
        self.assertEqual(tuple(row.location_id for row in restored.locations), ("location:1", "location:2"))
        self.assertEqual(tuple(row.provenance_id for row in restored.provenance), ("provenance:1", "provenance:2"))
        self.assertEqual(tuple(row.view_id for row in restored.views), ("view:1", "view:2"))
        self.assertEqual(tuple(row.collection_id for row in restored.smart_collection_rules), ("smart:1", "smart:2"))

    def test_payload_corruption_fails_integrity_before_restore_acceptance(self):
        envelope = json.loads(export_catalog(state()).decode("utf-8"))
        envelope["payload"]["logical_items"][0]["title"] = "tampered"
        tampered = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(G07ProofError, "backup-integrity-mismatch"):
            restore_catalog(tampered)

    def test_unsupported_backup_schema_fails_closed(self):
        envelope = json.loads(export_catalog(state()).decode("utf-8"))
        envelope["schema_version"] = "g07-proof-catalog-9.9.9"
        altered = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(G07ProofError, "backup-schema-version-unsupported"):
            restore_catalog(altered)

    def test_missing_critical_catalog_section_fails_closed(self):
        envelope = json.loads(export_catalog(state()).decode("utf-8"))
        del envelope["payload"]["provenance"]
        altered = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(G07ProofError, "catalog-payload-missing-field:provenance"):
            restore_catalog(altered)

    def test_unknown_critical_catalog_field_fails_closed(self):
        envelope = json.loads(export_catalog(state()).decode("utf-8"))
        envelope["payload"]["opaque_future_state"] = []
        # Integrity is deliberately recomputed to prove closed-shape rejection,
        # rather than merely exercising the digest mismatch path.
        payload_bytes = json.dumps(
            envelope["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        import hashlib
        envelope["payload_sha256"] = "sha256:" + hashlib.sha256(payload_bytes).hexdigest()
        altered = json.dumps(
            envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        with self.assertRaisesRegex(G07ProofError, "catalog-payload-unknown-field:opaque_future_state"):
            restore_catalog(altered)

    def test_noncanonical_record_order_with_valid_digest_is_rejected(self):
        envelope = json.loads(export_catalog(state()).decode("utf-8"))
        envelope["payload"]["logical_items"].reverse()
        payload_bytes = json.dumps(
            envelope["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        import hashlib
        envelope["payload_sha256"] = "sha256:" + hashlib.sha256(payload_bytes).hexdigest()
        altered = json.dumps(
            envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        with self.assertRaisesRegex(G07ProofError, "backup-payload-not-canonical"):
            restore_catalog(altered)

    def test_referentially_invalid_location_is_rejected(self):
        invalid = state()
        invalid = BoundedCatalogState(
            catalog_revision=invalid.catalog_revision,
            logical_items=invalid.logical_items,
            locations=(
                LocationRecord("location:x", "logical:missing", "/library/x.pdf", "known-present"),
            ),
            provenance=invalid.provenance,
            views=invalid.views,
            smart_collection_rules=invalid.smart_collection_rules,
        )
        with self.assertRaisesRegex(G07ProofError, "location-logical-id-unknown"):
            export_catalog(invalid)


class LocalAuthorityProofTests(unittest.TestCase):
    def test_core_scope_is_canonical_and_minimal(self):
        grant = create_core_scope(
            "scope:library",
            "/library/./books",
            ("read-for-processing", "observe", "observe"),
        )
        self.assertEqual(grant.root, "/library/books")
        self.assertEqual(grant.capabilities, ("observe", "read-for-processing"))
        assert_authority_shapes_minimal()

    def test_external_request_has_no_root_or_secret_authority_field(self):
        names = {field.name for field in fields(ExternalRequest)}
        self.assertEqual(names, {"scope_id", "path", "capability"})
        self.assertTrue(names.isdisjoint({"root", "requested_root", "token", "secret", "document_bytes"}))
        with self.assertRaises(TypeError):
            ExternalRequest(  # type: ignore[call-arg]
                scope_id="scope:library",
                path="/library/a.pdf",
                capability="observe",
                root="/etc",
            )

    def test_in_scope_observation_is_authorized_by_existing_core_scope(self):
        decision = authorize_request(
            authority(),
            ExternalRequest("scope:library", "/library/inbox/a.pdf", "observe"),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.normalized_path, "/library/inbox/a.pdf")
        self.assertEqual(decision.reason, "authorized-by-existing-core-scope")

    def test_in_scope_read_for_processing_is_authorized(self):
        decision = authorize_request(
            authority(),
            ExternalRequest("scope:library", "/library/a.pdf", "read-for-processing"),
        )
        self.assertTrue(decision.allowed)

    def test_sibling_prefix_escape_is_rejected(self):
        decision = authorize_request(
            authority(),
            ExternalRequest("scope:library", "/library2/a.pdf", "observe"),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "path-outside-scope")

    def test_parent_traversal_is_rejected_before_containment(self):
        decision = authorize_request(
            authority(),
            ExternalRequest("scope:library", "/library/../etc/passwd", "observe"),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "request-path-traversal-forbidden")
        self.assertIsNone(decision.normalized_path)

    def test_absolute_outside_root_is_rejected(self):
        decision = authorize_request(
            authority(),
            ExternalRequest("scope:library", "/etc/passwd", "observe"),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "path-outside-scope")

    def test_unknown_scope_id_cannot_mint_a_new_root(self):
        decision = authorize_request(
            authority(),
            ExternalRequest("scope:attacker", "/library/a.pdf", "observe"),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "unknown-scope-id")

    def test_observe_and_read_do_not_imply_mutation_capabilities(self):
        for capability in ("write", "move", "delete", "organize"):
            with self.subTest(capability=capability):
                decision = authorize_request(
                    authority(),
                    ExternalRequest("scope:library", "/library/a.pdf", capability),
                )
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.reason, "mutation-capability-not-granted-by-proof")

    def test_core_scope_creation_itself_rejects_mutation_capability(self):
        with self.assertRaisesRegex(G07ProofError, "scope-capability-forbidden:write"):
            create_core_scope("scope:bad", "/library", ("observe", "write"))

    def test_preconstructed_scope_cannot_bypass_core_validation(self):
        forged = ScopeGrant("scope:forged", "/library", ("delete",))
        with self.assertRaisesRegex(G07ProofError, "scope-capability-forbidden:delete"):
            build_core_authority((forged,))

    def test_authorization_is_pure_decision_with_no_mutation_result_fields(self):
        names = {field.name for field in fields(AuthorizationDecision)}
        self.assertEqual(names, {"allowed", "scope_id", "capability", "normalized_path", "reason"})
        self.assertTrue(names.isdisjoint({"write_path", "move_to", "delete_path", "content_bytes"}))


if __name__ == "__main__":
    unittest.main()
