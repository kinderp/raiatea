#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import validate_evidence_migration_manifest as manifest_validator
import validate_module as module_validator


class MigrationManifestInputValidationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


class MigrationManifestContextError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _prefixed_issue(namespace: str, issue: object) -> str:
    text = str(issue)
    if text.startswith("$"):
        return f"$.{namespace}{text[1:]}"
    return f"$.{namespace}: {text}"


def _module_step_ids(module: dict[str, Any]) -> list[str]:
    return [step["id"] for step in module["steps"]]


def _inventory_issue(
    role: str,
    manifest_ids: list[str],
    module_ids: list[str],
    *,
    endpoint_identity_matches: bool,
) -> str:
    path = f"$.manifest.{role}.stepIds"
    if not endpoint_identity_matches:
        return (
            f"{path}: manifest {role} step IDs {manifest_ids!r} do not match "
            f"{role} module step IDs {module_ids!r}"
        )

    missing = [step_id for step_id in module_ids if step_id not in manifest_ids]
    unknown = [step_id for step_id in manifest_ids if step_id not in module_ids]

    if len(manifest_ids) != len(module_ids):
        return (
            f"{path}: manifest {role} inventory length {len(manifest_ids)} does not "
            f"match {role} module inventory length {len(module_ids)}; "
            f"missing IDs {missing!r}; unknown IDs {unknown!r}"
        )

    if missing or unknown:
        return (
            f"{path}: manifest {role} inventory replaces canonical IDs; "
            f"missing IDs {missing!r}; unknown IDs {unknown!r}; "
            f"manifest order {manifest_ids!r}; canonical order {module_ids!r}"
        )

    return (
        f"{path}: manifest {role} inventory contains the exact canonical IDs but "
        f"uses a different order; manifest order {manifest_ids!r}; "
        f"canonical order {module_ids!r}"
    )


def check_manifest_context(
    source_module: dict[str, Any],
    target_module: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    """Return deterministic contextual mismatch issues without mutation."""
    issues: list[str] = []
    source = manifest["source"]
    target = manifest["target"]
    source_ids = _module_step_ids(source_module)
    target_ids = _module_step_ids(target_module)

    source_id_matches = source["moduleId"] == source_module["id"]
    source_revision_matches = source["revision"] == source_module["revision"]
    target_id_matches = target["moduleId"] == target_module["id"]
    target_revision_matches = target["revision"] == target_module["revision"]

    if not source_id_matches:
        issues.append(
            "$.manifest.source.moduleId: manifest source module ID "
            f"'{source['moduleId']}' does not match source module ID "
            f"'{source_module['id']}'"
        )
    if not source_revision_matches:
        issues.append(
            "$.manifest.source.revision: manifest source revision "
            f"'{source['revision']}' does not match source module revision "
            f"'{source_module['revision']}'"
        )
    if source["stepIds"] != source_ids:
        issues.append(
            _inventory_issue(
                "source",
                source["stepIds"],
                source_ids,
                endpoint_identity_matches=(source_id_matches and source_revision_matches),
            )
        )

    if not target_id_matches:
        issues.append(
            "$.manifest.target.moduleId: manifest target module ID "
            f"'{target['moduleId']}' does not match target module ID "
            f"'{target_module['id']}'"
        )
    if not target_revision_matches:
        issues.append(
            "$.manifest.target.revision: manifest target revision "
            f"'{target['revision']}' does not match target module revision "
            f"'{target_module['revision']}'"
        )
    if target["stepIds"] != target_ids:
        issues.append(
            _inventory_issue(
                "target",
                target["stepIds"],
                target_ids,
                endpoint_identity_matches=(target_id_matches and target_revision_matches),
            )
        )

    return issues


def load_and_check(
    source_module_path: Path,
    target_module_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate all inputs in fixed namespace order before contextual comparison."""
    input_issues: list[str] = []
    source_module: dict[str, Any] | None = None
    target_module: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None

    try:
        source_module = module_validator.load_and_validate(source_module_path)
    except module_validator.ModuleValidationError as exc:
        input_issues.extend(
            _prefixed_issue("sourceModule", issue) for issue in exc.issues
        )

    try:
        target_module = module_validator.load_and_validate(target_module_path)
    except module_validator.ModuleValidationError as exc:
        input_issues.extend(
            _prefixed_issue("targetModule", issue) for issue in exc.issues
        )

    try:
        manifest = manifest_validator.load_and_validate(manifest_path)
    except manifest_validator.MigrationManifestValidationError as exc:
        input_issues.extend(
            _prefixed_issue("manifest", issue) for issue in exc.issues
        )

    if input_issues:
        raise MigrationManifestInputValidationError(input_issues)

    assert source_module is not None
    assert target_module is not None
    assert manifest is not None
    context_issues = check_manifest_context(source_module, target_module, manifest)
    if context_issues:
        raise MigrationManifestContextError(context_issues)
    return source_module, target_module, manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one Raiatea learner-evidence migration manifest against "
            "its exact source and target canonical module revisions"
        )
    )
    parser.add_argument("source_module", type=Path)
    parser.add_argument("target_module", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        source_module, target_module, manifest = load_and_check(
            args.source_module, args.target_module, args.manifest
        )
    except MigrationManifestInputValidationError as exc:
        print("Migration manifest contextual input validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    except MigrationManifestContextError as exc:
        print("Migration manifest does not match the supplied canonical revisions:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    print(
        "Contextually valid migration manifest: "
        f"{manifest['source']['moduleId']} revision "
        f"{source_module['revision']} -> "
        f"{manifest['target']['moduleId']} revision "
        f"{target_module['revision']}"
    )


if __name__ == "__main__":
    main()
