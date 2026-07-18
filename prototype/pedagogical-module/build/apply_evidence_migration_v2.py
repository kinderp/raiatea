#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import check_evidence_compatibility_v2 as exact_checker
import preview_evidence_migration_v2 as preview_engine
import validate_evidence_export_v2 as evidence_validator
import validate_module_v2 as module_validator

CONTRACT_VERSION = 1
CONFIRMATION_PREFIX = "raiatea-confirm-v1:"
APPLICABLE_CLASSIFICATIONS = {"declared-lossless", "declared-partial"}


class EvidenceMigrationApplicationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


@dataclass(frozen=True)
class _PreparedMigration:
    public: dict[str, Any]
    candidate: dict[str, Any]
    candidate_bytes: bytes
    source_bytes: bytes
    target_module: dict[str, Any]


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_compact_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_evidence_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _read_bytes(path: Path, namespace: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.{namespace}: cannot read input: {exc}"]
        ) from exc


def _input_snapshot(
    evidence_path: Path,
    target_module_path: Path,
    source_module_path: Path,
    manifest_path: Path,
) -> dict[str, bytes]:
    return {
        "sourceEvidence": _read_bytes(evidence_path, "evidence"),
        "targetModule": _read_bytes(target_module_path, "targetModule"),
        "sourceModule": _read_bytes(source_module_path, "sourceModule"),
        "manifest": _read_bytes(manifest_path, "manifest"),
    }


def _confirmation_payload(
    *,
    classification: str,
    source: dict[str, Any],
    target: dict[str, Any],
    source_evidence_digest: str,
    source_module_digest: str,
    target_module_digest: str,
    manifest_digest: str,
    candidate_digest: str,
    candidate_byte_length: int,
) -> dict[str, Any]:
    return {
        "contractVersion": CONTRACT_VERSION,
        "classification": classification,
        "source": {
            "moduleId": source["moduleId"],
            "revision": source["revision"],
        },
        "target": {
            "moduleId": target["moduleId"],
            "revision": target["revision"],
        },
        "sourceEvidenceDigest": source_evidence_digest,
        "sourceModuleDigest": source_module_digest,
        "targetModuleDigest": target_module_digest,
        "manifestDigest": manifest_digest,
        "candidateDigest": candidate_digest,
        "candidateByteLength": candidate_byte_length,
    }


def _prepare_internal(
    evidence_path: Path,
    target_module_path: Path,
    source_module_path: Path,
    manifest_path: Path,
) -> _PreparedMigration:
    before = _input_snapshot(
        evidence_path,
        target_module_path,
        source_module_path,
        manifest_path,
    )
    try:
        preview = preview_engine.load_and_preview(
            evidence_path,
            target_module_path,
            source_module_path=source_module_path,
            manifest_path=manifest_path,
        )
    except preview_engine.EvidenceMigrationPreviewInputError as exc:
        raise EvidenceMigrationApplicationError(list(exc.issues)) from exc

    after = _input_snapshot(
        evidence_path,
        target_module_path,
        source_module_path,
        manifest_path,
    )
    changed = [name for name in before if before[name] != after[name]]
    if changed:
        raise EvidenceMigrationApplicationError(
            [
                "$.inputs: input bytes changed while preparing migration: "
                + ", ".join(changed)
            ]
        )

    classification = preview["classification"]
    if classification == "exact":
        raise EvidenceMigrationApplicationError(
            ["$.classification: exact evidence requires no migration"]
        )
    if classification not in APPLICABLE_CLASSIFICATIONS:
        issues = [
            f"$.classification: '{classification}' is not applicable for migration"
        ]
        issues.extend(preview.get("issues", []))
        raise EvidenceMigrationApplicationError(issues)
    if not preview.get("candidateAvailable") or preview.get("candidate") is None:
        current_status = None
        current_position = preview.get("currentPosition")
        if isinstance(current_position, dict):
            current_status = current_position.get("status")
        detail = (
            f"; current position is '{current_status}'"
            if current_status is not None
            else ""
        )
        raise EvidenceMigrationApplicationError(
            [f"$.candidate: validated migration candidate is unavailable{detail}"]
        )

    candidate = preview["candidate"]
    if not isinstance(candidate, dict):
        raise EvidenceMigrationApplicationError(
            ["$.candidate: preview candidate must be an object"]
        )
    candidate_bytes = canonical_evidence_bytes(candidate)
    candidate_digest = _sha256(candidate_bytes)

    source_evidence_digest = _sha256(before["sourceEvidence"])
    source_module_digest = _sha256(before["sourceModule"])
    target_module_digest = _sha256(before["targetModule"])
    manifest_digest = _sha256(before["manifest"])
    payload = _confirmation_payload(
        classification=classification,
        source=preview["source"],
        target=preview["target"],
        source_evidence_digest=source_evidence_digest,
        source_module_digest=source_module_digest,
        target_module_digest=target_module_digest,
        manifest_digest=manifest_digest,
        candidate_digest=candidate_digest,
        candidate_byte_length=len(candidate_bytes),
    )
    confirmation_token = CONFIRMATION_PREFIX + hashlib.sha256(
        _canonical_compact_bytes(payload)
    ).hexdigest()

    current_position = preview.get("currentPosition")
    current_status = (
        current_position.get("status")
        if isinstance(current_position, dict)
        else None
    )
    public = {
        "contractVersion": CONTRACT_VERSION,
        "applicable": True,
        "classification": classification,
        "source": payload["source"],
        "target": payload["target"],
        "sourceEvidenceDigest": source_evidence_digest,
        "sourceModuleDigest": source_module_digest,
        "targetModuleDigest": target_module_digest,
        "manifestDigest": manifest_digest,
        "candidateDigest": candidate_digest,
        "candidateByteLength": len(candidate_bytes),
        "confirmationToken": confirmation_token,
        "preview": {
            "summary": preview["summary"],
            "currentPositionStatus": current_status,
        },
    }

    try:
        target_module = module_validator.load_and_validate(target_module_path)
    except module_validator.ModuleValidationError as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.targetModule{str(issue)[1:]}" for issue in exc.issues]
        ) from exc

    return _PreparedMigration(
        public=public,
        candidate=candidate,
        candidate_bytes=candidate_bytes,
        source_bytes=before["sourceEvidence"],
        target_module=target_module,
    )


def prepare_migration(
    evidence_path: Path,
    target_module_path: Path,
    *,
    source_module_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Prepare one applicable migration without writing any file."""
    return _prepare_internal(
        Path(evidence_path),
        Path(target_module_path),
        Path(source_module_path),
        Path(manifest_path),
    ).public


def _resolved_destination(
    source_path: Path, destination_path: Path
) -> tuple[Path, Path]:
    try:
        source_real = source_path.resolve(strict=True)
    except OSError as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.evidence: cannot resolve source path: {exc}"]
        ) from exc
    if not source_real.is_file():
        raise EvidenceMigrationApplicationError(
            ["$.evidence: source path must resolve to a regular file"]
        )

    if destination_path.name in {"", ".", ".."}:
        raise EvidenceMigrationApplicationError(
            ["$.destination: destination must name a new file"]
        )
    try:
        parent_real = destination_path.parent.resolve(strict=True)
    except OSError as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.destination: cannot resolve destination directory: {exc}"]
        ) from exc
    if not parent_real.is_dir():
        raise EvidenceMigrationApplicationError(
            ["$.destination: destination parent must be a directory"]
        )

    destination_real = parent_real / destination_path.name
    if destination_real == source_real:
        raise EvidenceMigrationApplicationError(
            ["$.destination: destination must not alias the source evidence"]
        )
    if os.path.lexists(destination_real):
        raise EvidenceMigrationApplicationError(
            ["$.destination: destination already exists"]
        )
    return source_real, destination_real


def _validate_candidate_file(path: Path, target_module: dict[str, Any]) -> bytes:
    try:
        evidence = evidence_validator.load_and_validate(path)
    except evidence_validator.EvidenceExportV2ValidationError as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.destination{str(issue)[1:]}" for issue in exc.issues]
        ) from exc
    compatibility_issues = exact_checker.check_exact_compatibility(
        target_module, evidence
    )
    if compatibility_issues:
        raise EvidenceMigrationApplicationError(
            [f"$.destination{str(issue)[1:]}" for issue in compatibility_issues]
        )
    return _read_bytes(path, "destination")


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _same_published_inode(path: Path, identity: tuple[int, int]) -> bool:
    try:
        details = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (details.st_dev, details.st_ino) == identity


def apply_confirmed_migration(
    evidence_path: Path,
    target_module_path: Path,
    *,
    source_module_path: Path,
    manifest_path: Path,
    destination_path: Path,
    confirmation_token: str,
) -> dict[str, Any]:
    """Create one new validated evidence copy after exact-input confirmation."""
    evidence_path = Path(evidence_path)
    target_module_path = Path(target_module_path)
    source_module_path = Path(source_module_path)
    manifest_path = Path(manifest_path)
    destination_path = Path(destination_path)

    source_real, destination_real = _resolved_destination(
        evidence_path, destination_path
    )
    prepared = _prepare_internal(
        evidence_path,
        target_module_path,
        source_module_path,
        manifest_path,
    )

    if not isinstance(confirmation_token, str) or not confirmation_token.startswith(
        CONFIRMATION_PREFIX
    ):
        raise EvidenceMigrationApplicationError(
            ["$.confirmation: malformed confirmation token"]
        )
    if not hmac.compare_digest(
        confirmation_token, prepared.public["confirmationToken"]
    ):
        raise EvidenceMigrationApplicationError(
            ["$.confirmation: token does not match the freshly prepared migration"]
        )

    source_real_after, destination_real_after = _resolved_destination(
        evidence_path, destination_path
    )
    if source_real_after != source_real or destination_real_after != destination_real:
        raise EvidenceMigrationApplicationError(
            ["$.paths: source or destination resolution changed before publication"]
        )
    if _read_bytes(source_real, "evidence") != prepared.source_bytes:
        raise EvidenceMigrationApplicationError(
            ["$.evidence: source bytes changed before publication"]
        )

    temporary_path: Path | None = None
    published_identity: tuple[int, int] | None = None
    published = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination_real.name}.raiatea-",
            suffix=".tmp",
            dir=destination_real.parent,
        )
        temporary_path = Path(temporary_name)
        os.chmod(temporary_path, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(prepared.candidate_bytes)
            stream.flush()
            os.fsync(stream.fileno())

        temporary_details = temporary_path.stat(follow_symlinks=False)
        if not stat.S_ISREG(temporary_details.st_mode):
            raise EvidenceMigrationApplicationError(
                ["$.destination: temporary publication object is not a regular file"]
            )
        if stat.S_IMODE(temporary_details.st_mode) != 0o600:
            raise EvidenceMigrationApplicationError(
                ["$.destination: temporary file permissions are not private"]
            )

        temporary_bytes = _validate_candidate_file(
            temporary_path, prepared.target_module
        )
        if temporary_bytes != prepared.candidate_bytes:
            raise EvidenceMigrationApplicationError(
                ["$.destination: temporary candidate bytes changed after writing"]
            )
        if _read_bytes(source_real, "evidence") != prepared.source_bytes:
            raise EvidenceMigrationApplicationError(
                ["$.evidence: source bytes changed before publication"]
            )

        try:
            os.link(
                temporary_path,
                destination_real,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise EvidenceMigrationApplicationError(
                ["$.destination: destination was created concurrently"]
            ) from exc
        except OSError as exc:
            raise EvidenceMigrationApplicationError(
                [
                    "$.destination: atomic no-overwrite publication is "
                    f"unavailable: {exc}"
                ]
            ) from exc

        linked_details = destination_real.stat(follow_symlinks=False)
        published_identity = (linked_details.st_dev, linked_details.st_ino)
        published = True
        temporary_path.unlink()
        temporary_path = None
        _fsync_directory(destination_real.parent)

        published_bytes = _validate_candidate_file(
            destination_real, prepared.target_module
        )
        if published_bytes != prepared.candidate_bytes:
            raise EvidenceMigrationApplicationError(
                ["$.destination: published bytes do not match prepared candidate"]
            )
        if _sha256(published_bytes) != prepared.public["candidateDigest"]:
            raise EvidenceMigrationApplicationError(
                ["$.destination: published candidate digest mismatch"]
            )
        if _read_bytes(source_real, "evidence") != prepared.source_bytes:
            raise EvidenceMigrationApplicationError(
                ["$.evidence: original source bytes changed during application"]
            )

        return {
            "contractVersion": CONTRACT_VERSION,
            "applied": True,
            "classification": prepared.public["classification"],
            "source": prepared.public["source"],
            "target": prepared.public["target"],
            "confirmationToken": prepared.public["confirmationToken"],
            "sourceEvidenceDigest": prepared.public["sourceEvidenceDigest"],
            "candidateDigest": prepared.public["candidateDigest"],
            "destinationDigest": _sha256(published_bytes),
            "manifestDigest": prepared.public["manifestDigest"],
            "publishedByteLength": len(published_bytes),
            "originalPreserved": True,
            "browserStateChanged": False,
        }
    except EvidenceMigrationApplicationError:
        raise
    except Exception as exc:
        raise EvidenceMigrationApplicationError(
            [f"$.application: migration application failed: {exc}"]
        ) from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        if published and published_identity is not None:
            success = 'published_bytes' in locals()
            if not success and _same_published_inode(
                destination_real, published_identity
            ):
                try:
                    destination_real.unlink()
                    _fsync_directory(destination_real.parent)
                except OSError:
                    pass


def _print_preparation(result: dict[str, Any]) -> None:
    print(f"Classification: {result['classification']}")
    print(
        "Identity: "
        f"{result['source']['moduleId']} revision {result['source']['revision']} -> "
        f"{result['target']['moduleId']} revision {result['target']['revision']}"
    )
    print(f"Candidate digest: {result['candidateDigest']}")
    print(f"Confirmation token: {result['confirmationToken']}")
    print("Preparation only: no evidence file or learner state was changed.")


def _print_receipt(result: dict[str, Any]) -> None:
    print(f"Applied: {str(result['applied']).lower()}")
    print(f"Classification: {result['classification']}")
    print(f"Destination digest: {result['destinationDigest']}")
    print("Original preserved: true")
    print("Browser state changed: false")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare or explicitly apply one direct learner-evidence v2 migration "
            "to a new local copy"
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("evidence", type=Path)
        command.add_argument("target_module", type=Path)
        command.add_argument("--source-module", type=Path, required=True)
        command.add_argument("--manifest", type=Path, required=True)
        command.add_argument("--json", action="store_true", dest="json_output")

    prepare_parser = subparsers.add_parser(
        "prepare", help="prepare and print an exact confirmation token"
    )
    add_common_arguments(prepare_parser)

    apply_parser = subparsers.add_parser(
        "apply", help="apply a prepared migration to one new destination"
    )
    add_common_arguments(apply_parser)
    apply_parser.add_argument("--destination", type=Path, required=True)
    apply_parser.add_argument("--confirm", required=True)

    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_migration(
                args.evidence,
                args.target_module,
                source_module_path=args.source_module,
                manifest_path=args.manifest,
            )
        else:
            result = apply_confirmed_migration(
                args.evidence,
                args.target_module,
                source_module_path=args.source_module,
                manifest_path=args.manifest,
                destination_path=args.destination,
                confirmation_token=args.confirm,
            )
    except EvidenceMigrationApplicationError as exc:
        print("Confirmed evidence migration failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.command == "prepare":
        _print_preparation(result)
    else:
        _print_receipt(result)


if __name__ == "__main__":
    main()
