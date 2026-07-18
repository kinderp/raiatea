#!/usr/bin/env python3
"""Temporary compatibility wrapper during canonical validator consolidation.

All behavior now lives in ``validate_module``. Repository consumers are migrated
within issue #34, after which this file is deleted.
"""
from __future__ import annotations

from validate_module import (  # noqa: F401
    ModuleValidationError,
    ValidationIssue,
    load_and_validate,
    main,
    raise_for_issues,
    resolve_module_layout,
    validate_module,
    validate_rendered_html,
)


if __name__ == "__main__":
    main()
