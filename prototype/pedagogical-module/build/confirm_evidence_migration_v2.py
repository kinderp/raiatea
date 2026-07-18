#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import apply_confirmed_evidence_migration_v2 as application
import preview_evidence_migration_v2 as preview_engine
import validate_evidence_export_v2 as evidence_validator
import validate_evidence_migration_manifest as manifest_validator
import validate_module_v2 as module_validator


def _load_inputs(
    evidence_path: Path,
    target_path: Path,
    source_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    evidence = evidence_validator.load_and_validate(evidence_path)
    target = module_validator.load_and_validate(target_path)
    source = module_validator.load_and_validate(source_path)
    manifest = manifest_validator.load_and_validate(manifest_path)
    return evidence, target, source, manifest


def _prepare(
    evidence: dict[str, Any],
    target: dict[str, Any],
    source: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    preview = preview_engine.classify_preview(
        evidence,
        target,
        source_module=source,
        manifest=manifest,
    )
    if preview["classification"] not in application.ELIGIBLE_CLASSIFICATIONS:
        raise application.EvidenceMigrationApplicationError(
            ["$.preview.classification: preview is not eligible for application"]
        )
    if not preview["candidateAvailable"]:
        raise application.EvidenceMigrationApplicationError(
            ["$.preview.candidateAvailable: complete candidate is required"]
        )
    digest = application.confirmation_digest(
        evidence,
        target,
        preview,
        manifest=manifest,
    )
    return {
        "classification": preview["classification"],
        "source": preview["source"],
        "target": preview["target"],
        "currentPosition": preview["currentPosition"],
        "candidateAvailable": True,
        "confirmationDigest": digest,
        "applied": False,
        "summary": "Preparation only; no evidence document or learner state changed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare or apply one confirmed Raiatea learner-evidence v2 migration in memory"
    )
    parser.add_argument("mode", choices=("prepare", "apply"))
    parser.add_argument("evidence", type=Path)
    parser.add_argument("target_module", type=Path)
    parser.add_argument("source_module", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--confirm-digest")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        evidence, target, source, manifest = _load_inputs(
            args.evidence,
            args.target_module,
            args.source_module,
            args.manifest,
        )
        if args.mode == "prepare":
            result = _prepare(evidence, target, source, manifest)
        else:
            result = application.apply_confirmed_migration(
                evidence,
                target,
                source_module=source,
                manifest=manifest,
                confirmed=True,
                confirmed_digest=args.confirm_digest,
            )
    except (
        application.EvidenceMigrationApplicationError,
        evidence_validator.EvidenceExportV2ValidationError,
        module_validator.ModuleValidationError,
        manifest_validator.MigrationManifestValidationError,
    ) as exc:
        print("Confirmed evidence migration failed:")
        for issue in getattr(exc, "issues", (str(exc),)):
            print(f"- {issue}")
        raise SystemExit(1) from exc

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Mode: {args.mode}")
        print(f"Classification: {result['classification']}")
        print(f"Applied: {str(result['applied']).lower()}")
        if args.mode == "prepare":
            print(f"Confirmation digest: {result['confirmationDigest']}")
        print(result["summary"])


if __name__ == "__main__":
    main()
