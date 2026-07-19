#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import evaluator_session_batch_intake
import evaluator_session_record

FORMAT = "raiatea-evaluator-session-aggregate"
VERSION = 1
APPROVED_THEMES = (
    "accessibility",
    "instructions",
    "navigation",
    "performance",
    "remediation",
    "stability",
)
TOP_FIELDS = {
    "format",
    "version",
    "recordCount",
    "inputSha256",
    "platformCounts",
    "launcherCounts",
    "resultCounts",
    "themeCounts",
}


def _zero_counts(keys: Iterable[str]) -> dict[str, int]:
    return {key: 0 for key in keys}


def _validate_themes(
    snapshots: tuple[evaluator_session_batch_intake.RecordSnapshot, ...],
    themes: Mapping[str, Iterable[str]] | None,
) -> dict[str, tuple[str, ...]]:
    normalized: dict[str, tuple[str, ...]] = {}
    known = {snapshot.sha256 for snapshot in snapshots}
    for digest, labels in (themes or {}).items():
        if digest not in known:
            raise ValueError(f"theme assignment references an unknown digest: {digest}")
        if not isinstance(labels, (list, tuple)):
            raise ValueError(f"theme labels must be an array: {digest}")
        values = tuple(labels)
        if values != tuple(sorted(set(values))):
            raise ValueError(f"theme labels must be sorted and unique: {digest}")
        for label in values:
            if label not in APPROVED_THEMES:
                raise ValueError(f"unsupported theme label: {label}")
        normalized[digest] = values
    return normalized


def build_aggregate(
    snapshots: tuple[evaluator_session_batch_intake.RecordSnapshot, ...],
    themes: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    if not snapshots:
        raise ValueError("at least one validated record snapshot is required")
    digests = [snapshot.sha256 for snapshot in snapshots]
    if len(digests) != len(set(digests)):
        raise ValueError("duplicate snapshot digests are forbidden")
    if digests != sorted(digests):
        snapshots = tuple(sorted(snapshots, key=lambda item: item.sha256))
        digests = [snapshot.sha256 for snapshot in snapshots]
    theme_assignments = _validate_themes(snapshots, themes)

    platform_counts = _zero_counts(evaluator_session_record.PLATFORMS)
    launcher_counts = _zero_counts(evaluator_session_record.LAUNCHERS)
    result_counts = {key: {"false": 0, "true": 0} for key in evaluator_session_record.RESULT_KEYS}
    theme_counts = _zero_counts(APPROVED_THEMES)

    for snapshot in snapshots:
        value = snapshot.value
        platform_counts[value["platform"]] += 1
        launcher_counts[value["launcher"]] += 1
        for key in evaluator_session_record.RESULT_KEYS:
            result_counts[key]["true" if value["results"][key] else "false"] += 1
        for label in theme_assignments.get(snapshot.sha256, ()):
            theme_counts[label] += 1

    aggregate = {
        "format": FORMAT,
        "version": VERSION,
        "recordCount": len(snapshots),
        "inputSha256": digests,
        "platformCounts": platform_counts,
        "launcherCounts": launcher_counts,
        "resultCounts": result_counts,
        "themeCounts": theme_counts,
    }
    issues = validate_aggregate(aggregate)
    if issues:
        raise ValueError("invalid aggregate:\n- " + "\n- ".join(issues))
    return aggregate


def validate_aggregate(value: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, dict):
        return ["$: must be an object"]
    for field in sorted(set(value) - TOP_FIELDS):
        issues.append(f"$.{field}: unsupported field")
    for field in sorted(TOP_FIELDS - set(value)):
        issues.append(f"$.{field}: required field missing")
    if TOP_FIELDS - set(value):
        return issues
    if value["format"] != FORMAT:
        issues.append("$.format: unsupported format")
    if value["version"] != VERSION:
        issues.append("$.version: unsupported version")
    count = value["recordCount"]
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        issues.append("$.recordCount: must be a positive integer")
    digests = value["inputSha256"]
    if not isinstance(digests, list) or digests != sorted(set(digests)):
        issues.append("$.inputSha256: must be a sorted unique array")
    elif len(digests) != count:
        issues.append("$.inputSha256: length must equal recordCount")
    for field, keys in (
        ("platformCounts", evaluator_session_record.PLATFORMS),
        ("launcherCounts", evaluator_session_record.LAUNCHERS),
        ("themeCounts", APPROVED_THEMES),
    ):
        counts = value[field]
        if not isinstance(counts, dict) or tuple(counts) != tuple(keys):
            issues.append(f"$.{field}: keys must equal the canonical list")
        elif any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in counts.values()):
            issues.append(f"$.{field}: counts must be non-negative integers")
    results = value["resultCounts"]
    if not isinstance(results, dict) or tuple(results) != evaluator_session_record.RESULT_KEYS:
        issues.append("$.resultCounts: keys must equal the canonical result list")
    else:
        for key, counts in results.items():
            if not isinstance(counts, dict) or tuple(counts) != ("false", "true"):
                issues.append(f"$.resultCounts.{key}: must contain false and true counts")
            elif any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in counts.values()):
                issues.append(f"$.resultCounts.{key}: counts must be non-negative integers")
            elif counts["false"] + counts["true"] != count:
                issues.append(f"$.resultCounts.{key}: counts must sum to recordCount")
    return issues


def write_aggregate(path: Path, aggregate: dict[str, Any]) -> Path:
    issues = validate_aggregate(aggregate)
    if issues:
        raise ValueError("invalid aggregate:\n- " + "\n- ".join(issues))
    if os.path.lexists(os.fspath(path)):
        raise ValueError("aggregate output path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8", newline="\n")
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("aggregate output changed during creation") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _load_themes(path: Path | None) -> Mapping[str, Iterable[str]] | None:
    if path is None:
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("theme assignment must be one regular JSON file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("theme assignment must be a JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a deterministic evaluator-session aggregate")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--themes", type=Path)
    args = parser.parse_args()
    try:
        snapshots = evaluator_session_batch_intake.validate_batch_intake(args.manifest, args.root)
        aggregate = build_aggregate(snapshots, _load_themes(args.themes))
        print(write_aggregate(args.output, aggregate))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Evaluator-session aggregate generation failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
