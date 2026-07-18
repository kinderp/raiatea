#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import validate_evidence_migration_manifest as manifest_validator
import validate_module_v2 as module_validator


class MigrationManifestContextError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _module_step_ids(module: dict[str, Any]) -> list[str]:
    return [step["id"] for step in module["steps"]]


def _inventory_issues(
    *,
    role: str,
    manifest_ids: list[str],
    canonical_ids: list[str],
) -> list[str]:
    """Compare one ordered manifest inventory with one canonical step sequence."""
    path = f"$.{role}.stepIds"
    issues: list[str] = []

    if len(manifest_ids) != len(canonical_ids):
        issues.append(
            f"{path}: manifest {role} inventory length {len(manifest_ids)} "
            f"does not match canonical {role} step count {len(canonical_ids)}"
        )

    canonical_set = set(canonical_ids)
    manifest_set = set(manifest_ids)
    for index, step_id in enumerate(manifest_ids):
        if step_id not in canonical_set:
            issues.append(
                f"{path}[{index}]: manifest {role} step ID '{step_id}' "
                f"is not present in the canonical {role} revision"
            )

    for step_id in canonical_ids:
        if step_id not in manifest_set:
            issues.append(
                f"{path}: canonical {role} step ID '{step_id}' "
                "is missing from the manifest inventory"
            )

    if canonical_set == manifest_set and manifest_ids != canonical_ids:
        for index, (manifest_id, canonical_id) in enumerate(
            zip(manifest_ids, canonical_ids, strict=False)
        ):
            if manifest_id != canonical_id:
                issues.append(
                    f"{path}[{index}]: manifest {role} step ID '{manifest_id}' "
                    f"does not match canonical {role} step ID '{canonical_id}' "
                    "at this route position"
                )

    return issues


def check_manifest_context(
    source_module: dict[str, Any],
    target_module: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    """Return deterministic contextual mismatch issues without mutation."""
    issues: list[str] = []
    source = manifest["source"]
    target = manifest["target"]

    if target_module["id"] != source_module["id"]:
        issues.append(
            "$.target.moduleId: supplied target module ID "
            f"'{target_module['id']}' does not match supplied source module ID "
            f"'{source_module['id']}'"
        )
    if target_module["revision"] == source_module["revision"]:
        issues.append(
            "$.target.revision: supplied target module revision must differ "
            "from supplied source module revision"
        )

    if source["moduleId"] != source_module["id"]:
        issues.append(
            "$.source.moduleId: manifest source module ID "
            f"'{source['moduleId']}' does not match supplied source module ID "
            f"'{source_module['id']}'"
        )
    if source["revision"] != source_module["revision"]:
        issues.append(
            "$.source.revision: manifest source revision "
            f"'{source['revision']}' does not match supplied source module revision "
            f"'{source_module['revision']}'"
        )
    issues.extend(
        _inventory_issues(
            role="source",
            manifest_ids=source["stepIds"],
            canonical_ids=_module_step_ids(source_module),
        )
    )

    if target["moduleId"] != target_module["id"]:
        issues.append(
            "$.target.moduleId: manifest target module ID "
            f"'{target['moduleId']}' does not match supplied target module ID "
            f"'{target_module['id']}'"
        )
    if target["revision"] != target_module["revision"]:
        issues.append(
            "$.target.revision: manifest target revision "
            f"'{target['revision']}' does not match supplied target module revision "
            f"'{target_module['revision']}'"
        )
    issues.extend(
        _inventory_issues(
            role="target",
            manifest_ids=target["stepIds"],
            canonical_ids=_module_step_ids(target_module),
        )
    )

    return issues


def load_and_check(
    source_module_path: Path,
    target_module_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Structurally validate all inputs, then perform contextual comparison."""
    source_module = module_validator.load_and_validate(source_module_path)
    target_module = module_validator.load_and_validate(target_module_path)
    manifest = manifest_validator.load_and_validate(manifest_path)

    issues = check_manifest_context(source_module, target_module, manifest)
    if issues:
        raise MigrationManifestContextError(issues)
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
    except module_validator.ModuleValidationError as exc:
        print("Canonical module validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    except manifest_validator.MigrationManifestValidationError as exc:
        print("Migration manifest validation failed:")
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
