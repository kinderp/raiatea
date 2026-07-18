#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import preview_evidence_migration_v2 as preview_engine
import validate_evidence_export_v2 as evidence_validator
import validate_evidence_migration_manifest as manifest_validator
import validate_module_v2 as module_validator


class EvidenceCompatibilityPreviewInputError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _prefixed_issue(namespace: str, issue: object) -> str:
    text = str(issue)
    if text.startswith("$"):
        return f"$.{namespace}{text[1:]}"
    return f"$.{namespace}: {text}"


def _read_json(path: Path, namespace: str) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [
            f"$.{namespace}: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ]
    except OSError as exc:
        return None, [f"$.{namespace}: cannot read input: {exc}"]


def _load_module(path: Path, namespace: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return module_validator.load_and_validate(path), []
    except module_validator.ModuleValidationError as exc:
        return None, [_prefixed_issue(namespace, issue) for issue in exc.issues]
    except OSError as exc:
        return None, [f"$.{namespace}: cannot read input: {exc}"]


def _unsupported_result(
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    *,
    manifest_status: str,
    issue: str,
) -> dict[str, Any]:
    evidence_module = evidence.get("module")
    if not isinstance(evidence_module, dict):
        evidence_module = {}
    return {
        "classification": "unsupported",
        "source": {
            "moduleId": evidence_module.get("id"),
            "revision": evidence_module.get("revision"),
        },
        "target": {
            "moduleId": target_module["id"],
            "revision": target_module["revision"],
        },
        "manifestStatus": manifest_status,
        "summary": "The requested evidence or manifest feature is unsupported.",
        "issues": [issue],
        "steps": [],
        "currentPosition": None,
        "candidateAvailable": False,
        "candidate": None,
    }


def load_and_classify(
    evidence_path: Path,
    target_module_path: Path,
    *,
    source_module_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Load validated local inputs and return one deterministic read-only result."""
    if (source_module_path is None) != (manifest_path is None):
        raise EvidenceCompatibilityPreviewInputError(
            ["$.migrationContext: --source and --manifest must be supplied together"]
        )

    evidence, evidence_read_issues = _read_json(evidence_path, "evidence")
    target_module, target_issues = _load_module(target_module_path, "targetModule")

    source_module: dict[str, Any] | None = None
    source_issues: list[str] = []
    manifest: Any | None = None
    manifest_read_issues: list[str] = []
    if source_module_path is not None and manifest_path is not None:
        source_module, source_issues = _load_module(
            source_module_path, "sourceModule"
        )
        manifest, manifest_read_issues = _read_json(manifest_path, "manifest")

    read_and_module_issues = (
        evidence_read_issues
        + target_issues
        + source_issues
        + manifest_read_issues
    )
    if read_and_module_issues:
        raise EvidenceCompatibilityPreviewInputError(read_and_module_issues)

    assert target_module is not None

    if not isinstance(evidence, dict):
        evidence_issues = evidence_validator.validate_evidence_export_v2(evidence)
        raise EvidenceCompatibilityPreviewInputError(
            [_prefixed_issue("evidence", issue) for issue in evidence_issues]
        )

    if (
        evidence.get("format") != evidence_validator.FORMAT
        or evidence.get("version") != evidence_validator.VERSION
    ):
        return _unsupported_result(
            evidence,
            target_module,
            manifest_status="not-needed" if manifest is None else "unsupported",
            issue="$.evidence: unsupported learner-evidence format or version",
        )

    input_issues = [
        _prefixed_issue("evidence", issue)
        for issue in evidence_validator.validate_evidence_export_v2(evidence)
    ]

    validated_manifest: dict[str, Any] | None = None
    if manifest is not None:
        if not isinstance(manifest, dict):
            input_issues.extend(
                _prefixed_issue("manifest", issue)
                for issue in manifest_validator.validate_migration_manifest(manifest)
            )
        else:
            operations = manifest.get("operations")
            operation_keys = set(operations) if isinstance(operations, dict) else set()
            if (
                manifest.get("format") != manifest_validator.FORMAT
                or manifest.get("version") != manifest_validator.VERSION
                or not operation_keys.issubset(manifest_validator.OPERATION_FIELDS)
            ):
                if input_issues:
                    raise EvidenceCompatibilityPreviewInputError(input_issues)
                return _unsupported_result(
                    evidence,
                    target_module,
                    manifest_status="unsupported",
                    issue="$.manifest: unsupported manifest format, version, or operation",
                )

            manifest_issues = manifest_validator.validate_migration_manifest(manifest)
            input_issues.extend(
                _prefixed_issue("manifest", issue) for issue in manifest_issues
            )
            if not manifest_issues:
                validated_manifest = manifest

    if input_issues:
        raise EvidenceCompatibilityPreviewInputError(input_issues)

    return preview_engine.classify_preview(
        evidence,
        target_module,
        source_module=source_module,
        manifest=validated_manifest,
    )


def print_human(result: dict[str, Any]) -> None:
    print(f"Classification: {result['classification']}")
    print(
        "Identity: "
        f"{result['source']['moduleId']} revision {result['source']['revision']} -> "
        f"{result['target']['moduleId']} revision {result['target']['revision']}"
    )
    print(f"Manifest: {result['manifestStatus']}")
    print(result["summary"])
    for issue in result["issues"]:
        print(f"- {issue}")
    for step in result["steps"]:
        print(
            f"- {step['status']}: {step['stepId']} "
            f"({step['evidenceDisposition']})"
        )
    if result["currentPosition"] is not None:
        print(f"Current position: {result['currentPosition']['status']}")
    print(f"Candidate available: {str(result['candidateAvailable']).lower()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Classify one learner-evidence v2 document against an exact target "
            "revision and generate a read-only direct-migration preview"
        )
    )
    parser.add_argument("evidence", type=Path)
    parser.add_argument("target_module", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        result = load_and_classify(
            args.evidence,
            args.target_module,
            source_module_path=args.source,
            manifest_path=args.manifest,
        )
    except EvidenceCompatibilityPreviewInputError as exc:
        print("Evidence compatibility preview input validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_human(result)

    if result["classification"] not in preview_engine.SUCCESS_CLASSIFICATIONS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
