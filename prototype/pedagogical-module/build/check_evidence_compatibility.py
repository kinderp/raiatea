#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import validate_evidence_export as evidence_validator
import validate_module as module_validator


class EvidenceCompatibilityError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def check_compatibility(module: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    """Return deterministic compatibility issues without mutating either input."""
    issues: list[str] = []
    module_context = evidence["module"]
    exported_steps = evidence["progress"]["steps"]
    current_steps = module["steps"]

    if module_context["id"] != module["id"]:
        issues.append(
            "$.module.id: exported module ID "
            f"'{module_context['id']}' does not match current module ID '{module['id']}'"
        )

    if module_context["stepCount"] != len(current_steps):
        issues.append(
            "$.module.stepCount: exported step count "
            f"{module_context['stepCount']} does not match current module step count "
            f"{len(current_steps)}"
        )

    if len(exported_steps) != len(current_steps):
        issues.append(
            "$.progress.steps: exported step sequence length "
            f"{len(exported_steps)} does not match current module step sequence length "
            f"{len(current_steps)}"
        )

    for index, (exported_step, current_step) in enumerate(
        zip(exported_steps, current_steps, strict=False)
    ):
        if exported_step["title"] != current_step["title"]:
            issues.append(
                f"$.progress.steps[{index}].title: exported title "
                f"'{exported_step['title']}' does not match current module title "
                f"'{current_step['title']}'"
            )

    return issues


def load_and_check(module_path: Path, evidence_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    module = module_validator.load_and_validate(module_path)
    evidence = evidence_validator.load_and_validate(evidence_path)
    issues = check_compatibility(module, evidence)
    if issues:
        raise EvidenceCompatibilityError(issues)
    return module, evidence


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a Raiatea learner evidence export is structurally valid "
            "and compatible with a pedagogical module"
        )
    )
    parser.add_argument("module", type=Path)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()

    try:
        module, evidence = load_and_check(args.module, args.evidence)
    except module_validator.ModuleValidationError as exc:
        print("Module validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    except evidence_validator.EvidenceExportValidationError as exc:
        print("Evidence export validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    except EvidenceCompatibilityError as exc:
        print("Evidence export is incompatible:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    print(
        "Compatible evidence export: "
        f"{evidence['module']['id']} v{evidence['version']} -> {module['id']}"
    )


if __name__ == "__main__":
    main()
