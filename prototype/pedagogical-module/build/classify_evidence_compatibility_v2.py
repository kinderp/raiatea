#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from preview_evidence_migration_v2 import classify_preview


def classify(
    evidence: dict[str, Any],
    target_module: dict[str, Any],
    *,
    source_module: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper around the authoritative read-only preview engine."""
    return classify_preview(
        evidence,
        target_module,
        source_module=source_module,
        manifest=manifest,
    )
