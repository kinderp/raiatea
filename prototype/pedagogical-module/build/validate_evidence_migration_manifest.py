#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

FORMAT = "raiatea-learner-evidence-migration"
VERSION = 1
ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
TOP_LEVEL_FIELDS = {"format", "version", "source", "target", "operations"}
ENDPOINT_FIELDS = {"moduleId", "revision", "stepIds"}
OPERATION_FIELDS = {"preserve", "retire", "introduce"}
PRESERVE_FIELDS = {"sourceStepId", "targetStepId"}


class MigrationManifestValidationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def _exact_fields(
    value: dict[str, Any],
    required: set[str],
    allowed: set[str],
    path: str,
    issues: list[str],
) -> None:
    for field in sorted(required - set(value)):
        issues.append(f"{path}.{field}: required field is missing")
    for field in sorted(set(value) - allowed):
        issues.append(f"{path}.{field}: field is not supported")


def _stable_id(value: Any, path: str, issues: list[str]) -> bool:
    if not isinstance(value, str) or not value:
        issues.append(f"{path}: must be a non-empty string")
        return False
    if not ID_PATTERN.fullmatch(value):
        issues.append(
            f"{path}: must contain only lowercase letters, digits, and hyphens"
        )
        return False
    return True


def _positive_integer(value: Any, path: str, issues: list[str]) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        issues.append(f"{path}: must be a positive integer")
        return False
    return True


def _validate_endpoint(
    value: Any, path: str, issues: list[str]
) -> tuple[str | None, int | None, list[str]]:
    if not isinstance(value, dict):
        issues.append(f"{path}: must be an object")
        return None, None, []

    _exact_fields(value, ENDPOINT_FIELDS, ENDPOINT_FIELDS, path, issues)

    module_id = value.get("moduleId")
    valid_module_id = module_id if _stable_id(module_id, f"{path}.moduleId", issues) else None

    revision = value.get("revision")
    valid_revision = revision if _positive_integer(revision, f"{path}.revision", issues) else None

    raw_step_ids = value.get("stepIds")
    if not isinstance(raw_step_ids, list) or not raw_step_ids:
        issues.append(f"{path}.stepIds: must contain at least one step ID")
        return valid_module_id, valid_revision, []

    step_ids: list[str] = []
    seen: set[str] = set()
    for index, step_id in enumerate(raw_step_ids):
        step_path = f"{path}.stepIds[{index}]"
        if not _stable_id(step_id, step_path, issues):
            continue
        step_ids.append(step_id)
        if step_id in seen:
            issues.append(f"{step_path}: duplicate step ID '{step_id}'")
        else:
            seen.add(step_id)

    return valid_module_id, valid_revision, step_ids


def _validate_id_array(
    value: Any, path: str, issues: list[str]
) -> list[tuple[int, str]]:
    if not isinstance(value, list):
        issues.append(f"{path}: must be an array")
        return []

    result: list[tuple[int, str]] = []
    seen: set[str] = set()
    for index, step_id in enumerate(value):
        item_path = f"{path}[{index}]"
        if not _stable_id(step_id, item_path, issues):
            continue
        result.append((index, step_id))
        if step_id in seen:
            issues.append(f"{item_path}: duplicate step ID '{step_id}'")
        else:
            seen.add(step_id)
    return result


def _canonical_order(
    values: list[str], inventory: list[str]
) -> list[str]:
    selected = set(values)
    return [step_id for step_id in inventory if step_id in selected]


def validate_migration_manifest(data: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["$: must be an object"]

    _exact_fields(data, TOP_LEVEL_FIELDS, TOP_LEVEL_FIELDS, "$", issues)
    if data.get("format") != FORMAT:
        issues.append(f"$.format: must be {FORMAT}")
    version = data.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version != VERSION:
        issues.append(f"$.version: must be the integer {VERSION}")

    source_module_id, source_revision, source_ids = _validate_endpoint(
        data.get("source"), "$.source", issues
    )
    target_module_id, target_revision, target_ids = _validate_endpoint(
        data.get("target"), "$.target", issues
    )

    if (
        source_module_id is not None
        and target_module_id is not None
        and source_module_id != target_module_id
    ):
        issues.append("$.target.moduleId: must match $.source.moduleId")
    if (
        source_revision is not None
        and target_revision is not None
        and source_revision == target_revision
    ):
        issues.append("$.target.revision: must differ from $.source.revision")

    operations = data.get("operations")
    if not isinstance(operations, dict):
        issues.append("$.operations: must be an object")
        return issues

    _exact_fields(
        operations,
        OPERATION_FIELDS,
        OPERATION_FIELDS,
        "$.operations",
        issues,
    )

    raw_preserve = operations.get("preserve")
    preserve_entries: list[tuple[int, str, str]] = []
    if not isinstance(raw_preserve, list):
        issues.append("$.operations.preserve: must be an array")
    else:
        for index, entry in enumerate(raw_preserve):
            path = f"$.operations.preserve[{index}]"
            if not isinstance(entry, dict):
                issues.append(f"{path}: must be an object")
                continue
            _exact_fields(entry, PRESERVE_FIELDS, PRESERVE_FIELDS, path, issues)
            source_step_id = entry.get("sourceStepId")
            target_step_id = entry.get("targetStepId")
            source_valid = _stable_id(
                source_step_id, f"{path}.sourceStepId", issues
            )
            target_valid = _stable_id(
                target_step_id, f"{path}.targetStepId", issues
            )
            if source_valid and target_valid:
                if source_step_id != target_step_id:
                    issues.append(
                        f"{path}.targetStepId: preserve must retain the exact source step ID "
                        f"'{source_step_id}'"
                    )
                preserve_entries.append((index, source_step_id, target_step_id))

    retire_entries = _validate_id_array(
        operations.get("retire"), "$.operations.retire", issues
    )
    introduce_entries = _validate_id_array(
        operations.get("introduce"), "$.operations.introduce", issues
    )

    source_inventory = set(source_ids)
    target_inventory = set(target_ids)

    for index, source_step_id, target_step_id in preserve_entries:
        path = f"$.operations.preserve[{index}]"
        if source_step_id not in source_inventory:
            issues.append(
                f"{path}.sourceStepId: unknown source step ID '{source_step_id}'"
            )
        if target_step_id not in target_inventory:
            issues.append(
                f"{path}.targetStepId: unknown target step ID '{target_step_id}'"
            )

    for index, step_id in retire_entries:
        if step_id not in source_inventory:
            issues.append(
                f"$.operations.retire[{index}]: unknown source step ID '{step_id}'"
            )
    for index, step_id in introduce_entries:
        if step_id not in target_inventory:
            issues.append(
                f"$.operations.introduce[{index}]: unknown target step ID '{step_id}'"
            )

    preserved_sources = [source for _, source, _ in preserve_entries]
    preserved_targets = [target for _, _, target in preserve_entries]
    retired_ids = [step_id for _, step_id in retire_entries]
    introduced_ids = [step_id for _, step_id in introduce_entries]

    for step_id, count in Counter(preserved_sources).items():
        if count > 1:
            issues.append(
                "$.operations.preserve: source step ID "
                f"'{step_id}' is preserved more than once"
            )
    for step_id, count in Counter(preserved_targets).items():
        if count > 1:
            issues.append(
                "$.operations.preserve: target step ID "
                f"'{step_id}' is preserved more than once"
            )

    source_coverage = Counter(preserved_sources + retired_ids)
    target_coverage = Counter(preserved_targets + introduced_ids)
    for step_id in source_ids:
        count = source_coverage[step_id]
        if count == 0:
            issues.append(
                f"$.operations: source step ID '{step_id}' is not covered"
            )
        elif count > 1:
            issues.append(
                f"$.operations: source step ID '{step_id}' is covered more than once"
            )
    for step_id in target_ids:
        count = target_coverage[step_id]
        if count == 0:
            issues.append(
                f"$.operations: target step ID '{step_id}' is not covered"
            )
        elif count > 1:
            issues.append(
                f"$.operations: target step ID '{step_id}' is covered more than once"
            )

    if preserved_sources != _canonical_order(preserved_sources, source_ids):
        issues.append(
            "$.operations.preserve: entries must follow $.source.stepIds order"
        )
    if retired_ids != _canonical_order(retired_ids, source_ids):
        issues.append(
            "$.operations.retire: entries must follow $.source.stepIds order"
        )
    if introduced_ids != _canonical_order(introduced_ids, target_ids):
        issues.append(
            "$.operations.introduce: entries must follow $.target.stepIds order"
        )

    return issues


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MigrationManifestValidationError(
            [f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
        ) from exc

    issues = validate_migration_manifest(data)
    if issues:
        raise MigrationManifestValidationError(issues)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a Raiatea learner-evidence migration manifest v1"
    )
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        manifest = load_and_validate(args.manifest)
    except MigrationManifestValidationError as exc:
        print("Migration manifest validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    print(
        "Valid migration manifest: "
        f"{manifest['source']['moduleId']} "
        f"{manifest['source']['revision']} -> {manifest['target']['revision']}"
    )


if __name__ == "__main__":
    main()
