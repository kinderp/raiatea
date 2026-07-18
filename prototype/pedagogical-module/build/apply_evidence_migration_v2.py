#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import check_evidence_compatibility_v2 as exact_checker
import preview_evidence_migration_v2 as preview_engine
import validate_evidence_export_v2 as evidence_validator
import validate_module_v2 as module_validator

CONFIRMATION_TOKEN = "APPLY-NEW-COPY"
APPLICABLE_CLASSIFICATIONS = {"declared-lossless", "declared-partial"}


class EvidenceMigrationApplicationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path, namespace: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.{namespace}: cannot read input: {exc}"]
        ) from exc


def _verify_candidate_file(path: Path, target_module: dict[str, Any]) -> dict[str, Any]:
    try:
        candidate = evidence_validator.load_and_validate(path)
    except evidence_validator.EvidenceExportV2ValidationError as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.destination{str(issue)[1:]}" if str(issue).startswith("$") else f"$.destination: {issue}" for issue in exc.issues]
        ) from exc

    issues = exact_checker.check_exact_compatibility(target_module, candidate)
    if issues:
        raise EvidenceMigrationApplicationError(
            [f"$.destination{issue[1:]}" if issue.startswith("$") else f"$.destination: {issue}" for issue in issues]
        )
    return candidate


def _flush_directory(directory: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _serialize_candidate(candidate: dict[str, Any]) -> bytes:
    return (
        json.dumps(candidate, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")


def apply_new_copy(
    evidence_path: Path,
    target_module_path: Path,
    destination_path: Path,
    *,
    source_module_path: Path | None = None,
    manifest_path: Path | None = None,
    confirmation: str | None = None,
) -> dict[str, Any]:
    """Create one confirmed migration output without modifying the source evidence."""
    if confirmation != CONFIRMATION_TOKEN:
        raise EvidenceMigrationApplicationError(
            [f"$.confirmation: must equal {CONFIRMATION_TOKEN}"]
        )
    if (source_module_path is None) != (manifest_path is None):
        raise EvidenceMigrationApplicationError(
            ["$.migrationContext: sourceModule and manifest must be supplied together"]
        )

    source_resolved = evidence_path.resolve(strict=False)
    destination_resolved = destination_path.resolve(strict=False)
    if source_resolved == destination_resolved:
        raise EvidenceMigrationApplicationError(
            ["$.destination: must not resolve to the source evidence path"]
        )
    if os.path.lexists(destination_path):
        raise EvidenceMigrationApplicationError(
            ["$.destination: path already exists and will not be overwritten"]
        )

    destination_parent = destination_path.parent
    if not destination_parent.exists() or not destination_parent.is_dir():
        raise EvidenceMigrationApplicationError(
            ["$.destination: parent directory must already exist"]
        )

    source_before = _read_bytes(evidence_path, "evidence")
    try:
        preview = preview_engine.load_and_preview(
            evidence_path,
            target_module_path,
            source_module_path=source_module_path,
            manifest_path=manifest_path,
        )
    except preview_engine.EvidenceMigrationPreviewInputError as exc:
        raise EvidenceMigrationApplicationError(list(exc.issues)) from exc

    classification = preview["classification"]
    if classification not in APPLICABLE_CLASSIFICATIONS:
        if classification == "exact":
            issue = "$.classification: exact evidence requires no migration"
        elif preview.get("currentPosition", {}).get("status") == "unresolved-retired":
            issue = "$.currentPosition: retired current step has no approved target position"
        else:
            issue = f"$.classification: {classification} preview cannot be applied"
        raise EvidenceMigrationApplicationError([issue])
    if not preview["candidateAvailable"] or preview["candidate"] is None:
        status = (preview.get("currentPosition") or {}).get("status")
        if status == "unresolved-retired":
            issue = "$.currentPosition: retired current step has no approved target position"
        else:
            issue = "$.candidate: validated migration candidate is unavailable"
        raise EvidenceMigrationApplicationError([issue])

    target_module = module_validator.load_and_validate(target_module_path)
    candidate = preview["candidate"]
    candidate_issues = evidence_validator.validate_evidence_export_v2(candidate)
    candidate_issues.extend(exact_checker.check_exact_compatibility(target_module, candidate))
    if candidate_issues:
        raise EvidenceMigrationApplicationError(
            [
                f"$.candidate{issue[1:]}" if issue.startswith("$") else f"$.candidate: {issue}"
                for issue in candidate_issues
            ]
        )
    payload = _serialize_candidate(candidate)

    temporary_path: Path | None = None
    destination_installed = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination_parent,
            prefix=f".{destination_path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb", closefd=True) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise

        _verify_candidate_file(temporary_path, target_module)
        if _read_bytes(evidence_path, "evidence") != source_before:
            raise EvidenceMigrationApplicationError(
                ["$.evidence: source bytes changed during migration preparation"]
            )
        if os.path.lexists(destination_path):
            raise EvidenceMigrationApplicationError(
                ["$.destination: path appeared before atomic installation"]
            )

        try:
            os.link(temporary_path, destination_path)
        except FileExistsError as exc:
            raise EvidenceMigrationApplicationError(
                ["$.destination: path appeared before atomic installation"]
            ) from exc
        except OSError as exc:
            raise EvidenceMigrationApplicationError(
                [f"$.destination: atomic create-if-absent failed: {exc}"]
            ) from exc
        destination_installed = True
        temporary_path.unlink()
        temporary_path = None
        _flush_directory(destination_parent)

        installed_candidate = _verify_candidate_file(destination_path, target_module)
        destination_bytes = _read_bytes(destination_path, "destination")
        source_after = _read_bytes(evidence_path, "evidence")
        if source_after != source_before:
            raise EvidenceMigrationApplicationError(
                ["$.evidence: source bytes changed during migration application"]
            )
        if installed_candidate != candidate:
            raise EvidenceMigrationApplicationError(
                ["$.destination: installed candidate differs from prepared candidate"]
            )

        return {
            "status": "applied-new-copy",
            "classification": classification,
            "sourcePath": str(evidence_path),
            "destinationPath": str(destination_path),
            "target": {
                "moduleId": target_module["id"],
                "revision": target_module["revision"],
            },
            "sourceSha256Before": _digest(source_before),
            "sourceSha256After": _digest(source_after),
            "destinationSha256": _digest(destination_bytes),
            "sourceUnchanged": True,
            "browserStorageChanged": False,
        }
    except BaseException:
        if destination_installed and os.path.lexists(destination_path):
            try:
                destination_path.unlink()
                _flush_directory(destination_parent)
            except OSError:
                pass
        raise
    finally:
        if temporary_path is not None and os.path.lexists(temporary_path):
            try:
                temporary_path.unlink()
            except OSError:
                pass


def _print_human(result: dict[str, Any]) -> None:
    print("Migration applied to a new evidence copy.")
    print(f"Classification: {result['classification']}")
    print(
        "Target: "
        f"{result['target']['moduleId']} revision {result['target']['revision']}"
    )
    print(f"Destination: {result['destinationPath']}")
    print("Original evidence unchanged: true")
    print("Browser storage changed: false")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Apply one validated learner-evidence v2 migration to a new file "
            "without modifying the source evidence"
        )
    )
    parser.add_argument("evidence", type=Path)
    parser.add_argument("target_module", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--confirm")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        result = apply_new_copy(
            args.evidence,
            args.target_module,
            args.destination,
            source_module_path=args.source,
            manifest_path=args.manifest,
            confirmation=args.confirm,
        )
    except (EvidenceMigrationApplicationError, module_validator.ModuleValidationError) as exc:
        print("Evidence migration application failed:")
        issues = getattr(exc, "issues", [str(exc)])
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        _print_human(result)


if __name__ == "__main__":
    main()
