#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import validate_evidence_export_v2 as evidence_validator
import validate_module as module_validator


class EvidenceV2CompatibilityError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = tuple(issues)
        super().__init__("\n".join(issues))


def check_exact_compatibility(
    module: dict[str, Any], evidence: dict[str, Any]
) -> list[str]:
    """Return deterministic exact-compatibility issues without mutation."""
    issues: list[str] = []
    module_context = evidence["module"]
    progress = evidence["progress"]
    exported_steps = progress["steps"]
    canonical_steps = module["steps"]
    exported_ids = [step["stepId"] for step in exported_steps]
    canonical_ids = [step["id"] for step in canonical_steps]

    if module_context["id"] != module["id"]:
        issues.append(
            "$.module.id: exported module ID "
            f"'{module_context['id']}' does not match canonical module ID "
            f"'{module['id']}'"
        )

    if module_context["revision"] != module["revision"]:
        issues.append(
            "$.module.revision: exported module revision "
            f"'{module_context['revision']}' does not match canonical module revision "
            f"'{module['revision']}'"
        )

    if module_context["stepCount"] != len(canonical_steps):
        issues.append(
            "$.module.stepCount: exported step count "
            f"{module_context['stepCount']} does not match canonical module step count "
            f"{len(canonical_steps)}"
        )

    if len(exported_steps) != len(canonical_steps):
        issues.append(
            "$.progress.steps: exported step sequence length "
            f"{len(exported_steps)} does not match canonical module step sequence length "
            f"{len(canonical_steps)}"
        )

    canonical_id_set = set(canonical_ids)
    exported_id_set = set(exported_ids)
    for index, step_id in enumerate(exported_ids):
        if step_id not in canonical_id_set:
            issues.append(
                f"$.progress.steps[{index}].stepId: exported step ID "
                f"'{step_id}' is not present in the canonical module revision"
            )

    for step_id in canonical_ids:
        if step_id not in exported_id_set:
            issues.append(
                "$.progress.steps: canonical step ID "
                f"'{step_id}' is missing from the exported step sequence"
            )

    if canonical_id_set == exported_id_set and exported_ids != canonical_ids:
        for index, (exported_id, canonical_id) in enumerate(
            zip(exported_ids, canonical_ids, strict=False)
        ):
            if exported_id != canonical_id:
                issues.append(
                    f"$.progress.steps[{index}].stepId: exported step ID "
                    f"'{exported_id}' does not match canonical step ID "
                    f"'{canonical_id}' at this route position"
                )

    current_index = progress["currentStepIndex"]
    current_step_id = progress["currentStepId"]
    if current_index >= len(canonical_steps):
        issues.append(
            "$.progress.currentStepIndex: exported current step index "
            f"{current_index} does not refer to an active canonical step"
        )
    else:
        canonical_current_id = canonical_steps[current_index]["id"]
        if current_step_id != canonical_current_id:
            issues.append(
                "$.progress.currentStepId: exported current step ID "
                f"'{current_step_id}' does not match canonical step ID "
                f"'{canonical_current_id}' at currentStepIndex {current_index}"
            )

    return issues


def load_and_check(
    module_path: Path, evidence_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    module = module_validator.load_and_validate(module_path)
    evidence = evidence_validator.load_and_validate(evidence_path)
    issues = check_exact_compatibility(module, evidence)
    if issues:
        raise EvidenceV2CompatibilityError(issues)
    return module, evidence


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check exact contextual compatibility between a Raiatea learner-evidence "
            "v2 document and one canonical module revision"
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
    except evidence_validator.EvidenceExportV2ValidationError as exc:
        print("Evidence v2 validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc
    except EvidenceV2CompatibilityError as exc:
        print("Evidence v2 is not an exact contextual match:")
        for issue in exc.issues:
            print(f"- {issue}")
        raise SystemExit(1) from exc

    print(
        "Exact compatible evidence v2: "
        f"{evidence['module']['id']} revision {evidence['module']['revision']} "
        f"-> {module['id']} revision {module['revision']}"
    )


if __name__ == "__main__":
    main()
