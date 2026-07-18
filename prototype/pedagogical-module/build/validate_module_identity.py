#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

ID_PATTERN = re.compile(r"^[a-z0-9-]+$")


def validate_module_identity(data: Any) -> list[str]:
    """Validate canonical module revision and durable pedagogical step IDs.

    This helper is deliberately independent from learner-evidence v1. It only
    inspects canonical module authoring fields and never mutates its input.
    """
    issues: list[str] = []
    if not isinstance(data, dict):
        return ["$: expected object"]

    revision = data.get("revision")
    if "revision" not in data:
        issues.append("$.revision: required field is missing")
    elif not isinstance(revision, int) or isinstance(revision, bool):
        issues.append("$.revision: must be a positive integer")
    elif revision < 1:
        issues.append("$.revision: must be a positive integer")

    steps = data.get("steps")
    if not isinstance(steps, list):
        return issues

    seen: set[str] = set()
    for index, step in enumerate(steps):
        path = f"$.steps[{index}]"
        if not isinstance(step, dict):
            continue
        if "id" not in step:
            issues.append(f"{path}.id: required field is missing")
            continue
        step_id = step.get("id")
        if not isinstance(step_id, str) or not ID_PATTERN.fullmatch(step_id):
            issues.append(
                f"{path}.id: must contain only lowercase letters, digits, and hyphens"
            )
            continue
        if step_id in seen:
            issues.append(f"{path}.id: duplicate step id '{step_id}'")
        else:
            seen.add(step_id)

    return issues
