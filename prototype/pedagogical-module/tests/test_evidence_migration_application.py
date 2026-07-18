from __future__ import annotations

import copy
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]
BUILD_DIR = ROOT / "build"
CONTEXT_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-context"
PREVIEW_DIR = ROOT / "tests" / "fixtures" / "evidence-migration-preview"
sys.path.insert(0, str(BUILD_DIR))

import apply_evidence_migration_v2 as application  # noqa: E402
import check_evidence_compatibility as v1_checker  # noqa: E402
import check_evidence_compatibility_v2 as exact_checker  # noqa: E402
import validate_evidence_export_v2 as evidence_validator  # noqa: E402
import validate_module_v2 as module_validator  # noqa: E402


class EvidenceMigrationApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_fixture = CONTEXT_DIR / "exact-source.json"
        cls.partial_target = CONTEXT_DIR / "exact-target.json"
        cls.partial_manifest = CONTEXT_DIR / "exact-manifest.json"
        cls.preserved_evidence = PREVIEW_DIR / "source-current-preserved.json"
        cls.retired_evidence = PREVIEW_DIR / "source-current-retired.json"
        cls.lossless_target = PREVIEW_DIR / "lossless-target.json"
        cls.lossless_manifest = PREVIEW_DIR / "lossless-manifest.json"
        cls.exact_target = (
            ROOT / "tests" / "fixtures" / "module-identity" / "valid.json"
        )
        cls.exact_evidence = (
            ROOT / "tests" / "fixtures" / "evidence-v2-contextual" / "exact.json"
        )

    def _copied_source(self, directory: Path, fixture: Path | None = None) -> Path:
        source = directory / "source-evidence.json"
        source.write_bytes((fixture or self.preserved_evidence).read_bytes())
        return source

    def _prepare_partial(self, source: Path) -> dict[str, object]:
        return application.prepare_migration(
            source,
            self.partial_target,
            source_module_path=self.source_fixture,
            manifest_path=self.partial_manifest,
        )

    def _apply_partial(
        self, source: Path, destination: Path, token: str
    ) -> dict[str, object]:
        return application.apply_confirmed_migration(
            source,
            self.partial_target,
            source_module_path=self.source_fixture,
            manifest_path=self.partial_manifest,
            destination_path=destination,
            confirmation_token=token,
        )

    def test_prepare_is_deterministic_closed_and_side_effect_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            original = source.read_bytes()
            before = set(directory.iterdir())
            first = self._prepare_partial(source)
            second = self._prepare_partial(source)
            after = set(directory.iterdir())

        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(original, source.read_bytes())
        self.assertEqual(
            {
                "contractVersion",
                "applicable",
                "classification",
                "source",
                "target",
                "sourceEvidenceDigest",
                "sourceModuleDigest",
                "targetModuleDigest",
                "manifestDigest",
                "candidateDigest",
                "candidateByteLength",
                "confirmationToken",
                "preview",
            },
            set(first),
        )
        self.assertEqual("declared-partial", first["classification"])
        self.assertTrue(first["applicable"])
        self.assertTrue(
            str(first["confirmationToken"]).startswith("raiatea-confirm-v1:")
        )
        serialized = json.dumps(first).lower()
        for forbidden in (
            "timestamp",
            "email",
            "learnername",
            "deviceid",
            "analytics",
            str(directory).lower(),
        ):
            self.assertNotIn(forbidden, serialized)

    def test_apply_partial_creates_private_exact_copy_and_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            destination = directory / "migrated.json"
            original = source.read_bytes()
            preparation = self._prepare_partial(source)
            receipt = self._apply_partial(
                source, destination, str(preparation["confirmationToken"])
            )

            self.assertEqual(original, source.read_bytes())
            self.assertTrue(destination.is_file())
            self.assertEqual(0o600, stat.S_IMODE(destination.stat().st_mode))
            migrated = evidence_validator.load_and_validate(destination)
            target = module_validator.load_and_validate(self.partial_target)
            self.assertEqual(
                [], exact_checker.check_exact_compatibility(target, migrated)
            )
            self.assertEqual(
                application.canonical_evidence_bytes(migrated),
                destination.read_bytes(),
            )
            self.assertEqual(
                ["orient-concept", "apply-concept", "new-enrichment"],
                [step["stepId"] for step in migrated["progress"]["steps"]],
            )
            self.assertEqual(0, migrated["progress"]["steps"][1]["attempts"])
            self.assertNotIn(
                "legacy-practice",
                [step["stepId"] for step in migrated["progress"]["steps"]],
            )
            self.assertEqual(
                [],
                [path.name for path in directory.iterdir() if ".raiatea-" in path.name],
            )

        self.assertEqual(
            {
                "contractVersion",
                "applied",
                "classification",
                "source",
                "target",
                "confirmationToken",
                "sourceEvidenceDigest",
                "candidateDigest",
                "destinationDigest",
                "manifestDigest",
                "publishedByteLength",
                "originalPreserved",
                "browserStateChanged",
            },
            set(receipt),
        )
        self.assertTrue(receipt["applied"])
        self.assertTrue(receipt["originalPreserved"])
        self.assertFalse(receipt["browserStateChanged"])
        self.assertEqual(receipt["candidateDigest"], receipt["destinationDigest"])

    def test_apply_lossless_reorders_by_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            destination = directory / "lossless.json"
            preparation = application.prepare_migration(
                source,
                self.lossless_target,
                source_module_path=self.source_fixture,
                manifest_path=self.lossless_manifest,
            )
            receipt = application.apply_confirmed_migration(
                source,
                self.lossless_target,
                source_module_path=self.source_fixture,
                manifest_path=self.lossless_manifest,
                destination_path=destination,
                confirmation_token=str(preparation["confirmationToken"]),
            )
            migrated = evidence_validator.load_and_validate(destination)

        self.assertEqual("declared-lossless", receipt["classification"])
        self.assertEqual(
            ["legacy-practice", "orient-concept"],
            [step["stepId"] for step in migrated["progress"]["steps"]],
        )
        self.assertEqual(1, migrated["progress"]["currentStepIndex"])
        self.assertEqual(2, migrated["progress"]["steps"][1]["attempts"])

    def test_exact_and_retired_current_are_non_applicable(self) -> None:
        with self.assertRaises(
            application.EvidenceMigrationApplicationError
        ) as exact:
            application.prepare_migration(
                self.exact_evidence,
                self.exact_target,
                source_module_path=self.source_fixture,
                manifest_path=self.partial_manifest,
            )
        self.assertEqual(
            ["$.classification: exact evidence requires no migration"],
            list(exact.exception.issues),
        )

        with self.assertRaises(
            application.EvidenceMigrationApplicationError
        ) as retired:
            application.prepare_migration(
                self.retired_evidence,
                self.partial_target,
                source_module_path=self.source_fixture,
                manifest_path=self.partial_manifest,
            )
        self.assertIn("unresolved-retired", retired.exception.issues[0])

    def test_wrong_and_stale_confirmation_never_create_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            original = source.read_bytes()
            destination = directory / "migrated.json"
            preparation = self._prepare_partial(source)

            with self.assertRaises(
                application.EvidenceMigrationApplicationError
            ) as wrong:
                self._apply_partial(
                    source,
                    destination,
                    "raiatea-confirm-v1:" + "0" * 64,
                )
            self.assertIn("does not match", wrong.exception.issues[0])
            self.assertFalse(destination.exists())
            self.assertEqual(original, source.read_bytes())

            changed = json.loads(source.read_text(encoding="utf-8"))
            changed["progress"]["steps"][0]["attempts"] += 1
            source.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(
                application.EvidenceMigrationApplicationError
            ) as stale:
                self._apply_partial(
                    source,
                    destination,
                    str(preparation["confirmationToken"]),
                )
            self.assertIn("does not match", stale.exception.issues[0])
            self.assertFalse(destination.exists())

    def test_alias_and_existing_destination_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            preparation = self._prepare_partial(source)
            token = str(preparation["confirmationToken"])

            with self.assertRaises(
                application.EvidenceMigrationApplicationError
            ) as alias:
                self._apply_partial(source, source, token)
            self.assertIn("must not alias", alias.exception.issues[0])

            destination = directory / "existing.json"
            destination.write_text("keep", encoding="utf-8")
            with self.assertRaises(
                application.EvidenceMigrationApplicationError
            ) as existing:
                self._apply_partial(source, destination, token)
            self.assertIn("already exists", existing.exception.issues[0])
            self.assertEqual("keep", destination.read_text(encoding="utf-8"))

            symbolic = directory / "symbolic.json"
            symbolic.symlink_to(source)
            with self.assertRaises(
                application.EvidenceMigrationApplicationError
            ) as symlink:
                self._apply_partial(source, symbolic, token)
            self.assertIn("already exists", symlink.exception.issues[0])
            self.assertTrue(symbolic.is_symlink())

    def test_concurrent_destination_and_fsync_failure_leave_no_partial_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            original = source.read_bytes()
            preparation = self._prepare_partial(source)
            token = str(preparation["confirmationToken"])
            destination = directory / "race.json"

            with mock.patch.object(
                application.os, "link", side_effect=FileExistsError("race")
            ):
                with self.assertRaises(
                    application.EvidenceMigrationApplicationError
                ) as race:
                    self._apply_partial(source, destination, token)
            self.assertIn("created concurrently", race.exception.issues[0])
            self.assertFalse(destination.exists())
            self.assertEqual(original, source.read_bytes())
            self.assertEqual(
                [],
                [path.name for path in directory.iterdir() if ".raiatea-" in path.name],
            )

            with mock.patch.object(
                application.os, "fsync", side_effect=OSError("fsync failed")
            ):
                with self.assertRaises(
                    application.EvidenceMigrationApplicationError
                ) as failed:
                    self._apply_partial(source, destination, token)
            self.assertIn("migration application failed", failed.exception.issues[0])
            self.assertFalse(destination.exists())
            self.assertEqual(original, source.read_bytes())
            self.assertEqual(
                [],
                [path.name for path in directory.iterdir() if ".raiatea-" in path.name],
            )

    def test_post_publication_verification_failure_removes_only_new_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            original = source.read_bytes()
            destination = directory / "verify.json"
            preparation = self._prepare_partial(source)
            token = str(preparation["confirmationToken"])
            real_validate = application._validate_candidate_file
            calls = 0

            def fail_second(path: Path, target: dict[str, object]) -> bytes:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise application.EvidenceMigrationApplicationError(
                        ["$.destination: injected verification failure"]
                    )
                return real_validate(path, target)

            with mock.patch.object(
                application, "_validate_candidate_file", side_effect=fail_second
            ):
                with self.assertRaises(
                    application.EvidenceMigrationApplicationError
                ) as failed:
                    self._apply_partial(source, destination, token)

            self.assertIn("injected verification failure", failed.exception.issues[0])
            self.assertFalse(destination.exists())
            self.assertEqual(original, source.read_bytes())

    def test_input_change_during_publication_removes_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            manifest = directory / "manifest.json"
            manifest.write_bytes(self.partial_manifest.read_bytes())
            destination = directory / "changed-input.json"
            preparation = application.prepare_migration(
                source,
                self.partial_target,
                source_module_path=self.source_fixture,
                manifest_path=manifest,
            )
            real_link = os.link

            def change_then_link(
                source_path: os.PathLike[str],
                destination_path: os.PathLike[str],
                *,
                follow_symlinks: bool = True,
            ) -> None:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
                payload["operations"]["retire"] = ["legacy-practice"]
                manifest.write_text(
                    json.dumps(payload, indent=2) + "\n", encoding="utf-8"
                )
                real_link(
                    source_path,
                    destination_path,
                    follow_symlinks=follow_symlinks,
                )

            with mock.patch.object(application.os, "link", side_effect=change_then_link):
                with self.assertRaises(
                    application.EvidenceMigrationApplicationError
                ) as changed:
                    application.apply_confirmed_migration(
                        source,
                        self.partial_target,
                        source_module_path=self.source_fixture,
                        manifest_path=manifest,
                        destination_path=destination,
                        confirmation_token=str(preparation["confirmationToken"]),
                    )
            self.assertIn("input bytes changed", changed.exception.issues[0])
            self.assertFalse(destination.exists())

    def test_cli_prepare_and_apply_use_same_closed_results(self) -> None:
        cli = BUILD_DIR / "apply_evidence_migration_v2.py"
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = self._copied_source(directory)
            destination = directory / "cli-migrated.json"
            prepare_result = subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "prepare",
                    str(source),
                    str(self.partial_target),
                    "--source-module",
                    str(self.source_fixture),
                    "--manifest",
                    str(self.partial_manifest),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, prepare_result.returncode, prepare_result.stderr)
            preparation = json.loads(prepare_result.stdout)

            apply_result = subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "apply",
                    str(source),
                    str(self.partial_target),
                    "--source-module",
                    str(self.source_fixture),
                    "--manifest",
                    str(self.partial_manifest),
                    "--destination",
                    str(destination),
                    "--confirm",
                    preparation["confirmationToken"],
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, apply_result.returncode, apply_result.stderr)
            receipt = json.loads(apply_result.stdout)
            self.assertTrue(receipt["applied"])
            self.assertTrue(destination.exists())

    def test_existing_v1_contract_remains_unchanged(self) -> None:
        module = module_validator.load_and_validate(
            ROOT / "examples" / "self-attention.json"
        )
        evidence = v1_checker.evidence_validator.load_and_validate(
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        self.assertEqual([], v1_checker.check_compatibility(module, evidence))


if __name__ == "__main__":
    unittest.main()
