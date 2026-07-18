#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import validate_module_v2 as module_validator
from validate_module_identity import validate_module_identity

ModuleValidationError = module_validator.ModuleValidationError
ValidationIssue = module_validator.ValidationIssue
raise_for_issues = module_validator.raise_for_issues
validate_rendered_html = module_validator.validate_rendered_html


def validate_identity(data: Any) -> None:
    issues = [
        ValidationIssue(path, message)
        for item in validate_module_identity(data)
        for path, message in [item.split(": ", 1)]
    ]
    raise_for_issues(issues)


def load_and_validate(path: Path) -> dict[str, Any]:
    """Load a canonical module and enforce both layered and identity contracts."""
    data = module_validator.load_and_validate(path)
    validate_identity(data)
    return data
