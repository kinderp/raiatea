from __future__ import annotations

import json
import os
import shutil
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


class ConfirmedEvidenceMigrationApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.source_path = self.directory / "source-evidence.json"
        shutil.copyfile(
            PREVIEW_DIR / "source-current-preserved.json", self.source_path
        )
        self.source_module_path = CONTEXT_DIR / "exact-source.json"
        self.target_module_path = CONTEXT_DIR / "exact-target.json"
        self.manifest_path = CONTEXT_DIR / "exact-manifest.json"
        self.destination_path = self.directory / "migrated-evidence.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def apply(self, **overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "evidence_path": self.source_path,
            "target_module_path": self.target_module_path,
            "destination_path": self.destination_path,
            "source_module_path": self.source_module_path,
            "manifest_path": self.manifest_path,
            "confirmation": application.CONFIRMATION_TOKEN,
        }
        values.update(overrides)
        return application.apply_new_copy(**values)  # type: ignore[arg-type]

    def test_partial_migration_creates_exact_new_copy_and_preserves_source(self) -> None:
        source_before = self.source_path.read_bytes()
        result = self.apply()

        self.assertEqual("applied-new-copy", result["status"])
        self.assertEqual("declared-partial", result["classification"])
        self.assertTrue(result["sourceUnchanged"])
        self.assertFalse(result["browserStorageChanged"])
        self.assertEqual(source_before, self.source_path.read_bytes())
        self.assertTrue(self.destination_path.is_file())
        self.assertEqual(0o600, self.destination_path.stat().st_mode & 0o777)

        target = module_validator.load_and_validate(self.target_module_path)
        migrated = evidence_validator.load_and_validate(self.destination_path)
        self.assertEqual([], exact_checker.check_exact_compatibility(target, migrated))
        self.assertEqual(2, migrated["progress"]["steps"][0]["attempts"])
        self.assertEqual(0, migrated["progress"]["steps"][1]["attempts"])
        self.assertNotEqual(
            result["sourceSha256Before"], result["destinationSha256"]
        )
        self.assertEqual(
            result["sourceSha256Before"], result["sourceSha256After"]
        )

    def test_declared_lossless_migration_remaps_current_position(self) -> None:
        result = self.apply(
            target_module_path=PREVIEW_DIR / "lossless-target.json",
            manifest_path=PREVIEW_DIR / "lossless-manifest.json",
        )
        self.assertEqual("declared-lossless", result["classification"])
        migrated = evidence_validator.load_and_validate(self.destination_path)
        self.assertEqual("orient-concept", migrated["progress"]["currentStepId"])
        self.assertEqual(1, migrated["progress"]["currentStepIndex"])

    def test_retired_current_step_is_not_applicable(self) -> None:
        shutil.copyfile(
            PREVIEW_DIR / "source-current-retired.json", self.source_path
        )
        source_before = self.source_path.read_bytes()
        with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
            self.apply()
        self.assertEqual(
            ["$.currentPosition: retired current step has no approved target position"],
            list(raised.exception.issues),
        )
        self.assertFalse(self.destination_path.exists())
        self.assertEqual(source_before, self.source_path.read_bytes())

    def test_exact_evidence_is_rejected_as_no_migration_required(self) -> None:
        exact_evidence = (
            ROOT / "tests" / "fixtures" / "evidence-v2-contextual" / "exact.json"
        )
        exact_target = ROOT / "tests" / "fixtures" / "module-identity" / "valid.json"
        with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
            application.apply_new_copy(
                exact_evidence,
                exact_target,
                self.destination_path,
                confirmation=application.CONFIRMATION_TOKEN,
            )
        self.assertEqual(
            ["$.classification: exact evidence requires no migration"],
            list(raised.exception.issues),
        )
        self.assertFalse(self.destination_path.exists())

    def test_confirmation_source_alias_and_existing_destination_fail_closed(self) -> None:
        with self.assertRaises(application.EvidenceMigrationApplicationError) as missing:
            self.apply(confirmation=None)
        self.assertTrue(missing.exception.issues[0].startswith("$.confirmation:"))

        with self.assertRaises(application.EvidenceMigrationApplicationError) as alias:
            self.apply(destination_path=self.source_path)
        self.assertEqual(
            ["$.destination: must not resolve to the source evidence path"],
            list(alias.exception.issues),
        )

        self.destination_path.write_text("existing", encoding="utf-8")
        with self.assertRaises(application.EvidenceMigrationApplicationError) as existing:
            self.apply()
        self.assertEqual(
            ["$.destination: path already exists and will not be overwritten"],
            list(existing.exception.issues),
        )
        self.assertEqual("existing", self.destination_path.read_text(encoding="utf-8"))

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links unavailable")
    def test_broken_symlink_destination_is_existing_and_never_replaced(self) -> None:
        os.symlink("missing-target", self.destination_path)
        with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
            self.apply()
        self.assertEqual(
            ["$.destination: path already exists and will not be overwritten"],
            list(raised.exception.issues),
        )
        self.assertTrue(self.destination_path.is_symlink())
        self.assertEqual("missing-target", os.readlink(self.destination_path))

    def test_atomic_install_failure_removes_temporary_file(self) -> None:
        source_before = self.source_path.read_bytes()
        with mock.patch.object(os, "link", side_effect=OSError("link unavailable")):
            with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
                self.apply()
        self.assertIn("atomic create-if-absent failed", raised.exception.issues[0])
        self.assertFalse(self.destination_path.exists())
        self.assertEqual(source_before, self.source_path.read_bytes())
        self.assertEqual([], list(self.directory.glob(".*.tmp")))

    def test_source_drift_aborts_before_install_and_preserves_changed_source(self) -> None:
        original_verify = application._verify_candidate_file
        changed_source = self.source_path.read_bytes() + b"\n"
        calls = 0

        def mutate_after_prepare(
            path: Path, target: dict[str, object]
        ) -> dict[str, object]:
            nonlocal calls
            result = original_verify(path, target)  # type: ignore[arg-type,assignment]
            calls += 1
            if calls == 1:
                self.source_path.write_bytes(changed_source)
            return result  # type: ignore[return-value]

        with mock.patch.object(
            application, "_verify_candidate_file", side_effect=mutate_after_prepare
        ):
            with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
                self.apply()
        self.assertTrue(
            any("source bytes changed" in issue for issue in raised.exception.issues)
        )
        self.assertEqual(changed_source, self.source_path.read_bytes())
        self.assertFalse(self.destination_path.exists())
        self.assertEqual([], list(self.directory.glob(".*.tmp")))

    def test_post_install_verification_failure_rolls_back_new_destination_only(self) -> None:
        source_before = self.source_path.read_bytes()
        original_verify = application._verify_candidate_file
        calls = 0

        def fail_second(path: Path, target: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise application.EvidenceMigrationApplicationError(
                    ["$.destination: simulated verification failure"]
                )
            return original_verify(path, target)  # type: ignore[arg-type,return-value]

        with mock.patch.object(
            application, "_verify_candidate_file", side_effect=fail_second
        ):
            with self.assertRaises(application.EvidenceMigrationApplicationError):
                self.apply()
        self.assertFalse(self.destination_path.exists())
        self.assertEqual(source_before, self.source_path.read_bytes())
        self.assertEqual([], list(self.directory.glob(".*.tmp")))

    def test_rollback_does_not_delete_replaced_foreign_destination(self) -> None:
        original_verify = application._verify_candidate_file
        calls = 0

        def replace_before_failure(
            path: Path, target: dict[str, object]
        ) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 2:
                path.unlink()
                path.write_text("foreign", encoding="utf-8")
                raise application.EvidenceMigrationApplicationError(
                    ["$.destination: simulated verification failure"]
                )
            return original_verify(path, target)  # type: ignore[arg-type,return-value]

        with mock.patch.object(
            application, "_verify_candidate_file", side_effect=replace_before_failure
        ):
            with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
                self.apply()
        self.assertTrue(
            any("identity changed" in issue for issue in raised.exception.issues)
        )
        self.assertEqual("foreign", self.destination_path.read_text(encoding="utf-8"))

    def test_cleanup_failure_is_reported(self) -> None:
        original_remove = application._remove_owned_path

        def fail_temporary_cleanup(
            path: Path,
            identity: tuple[int, int],
            namespace: str,
        ) -> list[str]:
            if namespace == "temporaryFile":
                return ["$.temporaryFile: simulated cleanup failure"]
            return original_remove(path, identity, namespace)

        with mock.patch.object(
            application, "_remove_owned_path", side_effect=fail_temporary_cleanup
        ):
            with self.assertRaises(application.EvidenceMigrationApplicationError) as raised:
                self.apply()
        self.assertTrue(
            any("cleanup failure" in issue for issue in raised.exception.issues)
        )
        self.assertFalse(self.destination_path.exists())

    def test_cli_requires_confirmation_and_reports_success_as_json(self) -> None:
        command = [
            sys.executable,
            str(BUILD_DIR / "apply_evidence_migration_v2.py"),
            str(self.source_path),
            str(self.target_module_path),
            str(self.destination_path),
            "--source",
            str(self.source_module_path),
            "--manifest",
            str(self.manifest_path),
            "--confirm",
            application.CONFIRMATION_TOKEN,
            "--json",
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("applied-new-copy", payload["status"])
        self.assertTrue(payload["sourceUnchanged"])
        self.assertFalse(payload["browserStorageChanged"])

        second_destination = self.directory / "without-confirmation.json"
        failure = subprocess.run(
            [
                sys.executable,
                str(BUILD_DIR / "apply_evidence_migration_v2.py"),
                str(self.source_path),
                str(self.target_module_path),
                str(second_destination),
                "--source",
                str(self.source_module_path),
                "--manifest",
                str(self.manifest_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, failure.returncode)
        self.assertIn("$.confirmation:", failure.stdout)
        self.assertFalse(second_destination.exists())

    def test_learner_evidence_v1_contract_remains_unchanged(self) -> None:
        module = module_validator.load_and_validate(
            ROOT / "examples" / "self-attention.json"
        )
        evidence = v1_checker.evidence_validator.load_and_validate(
            ROOT / "evidence-examples" / "learner-evidence-export-v1.json"
        )
        self.assertEqual([], v1_checker.check_compatibility(module, evidence))


if __name__ == "__main__":
    unittest.main()
