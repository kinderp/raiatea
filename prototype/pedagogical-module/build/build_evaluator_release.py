#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import build_pilot

FORMAT = "raiatea-evaluator-release"
CONTRACT_VERSION = 1
VERSION_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?\Z")
MANIFEST_FIELDS = {"format", "contractVersion", "releaseVersion", "entrypoint", "pilotManifest", "files"}
FILE_FIELDS = {"path", "size"}


def _path_lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def validate_release_version(value: object) -> str:
    if not isinstance(value, str) or not VERSION_PATTERN.fullmatch(value):
        raise ValueError(
            "release version must be 1-64 lowercase ASCII letters, digits, dots, or "
            "hyphens and begin/end with a letter or digit"
        )
    return value


def _canonical_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("release file path must be a non-empty string")
    if "\\" in value or value.startswith("/"):
        raise ValueError(f"release file path is not canonical: {value!r}")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"release file path is unsafe: {value!r}")
    canonical = path.as_posix()
    if canonical != value or not canonical.startswith("pilot/"):
        raise ValueError(f"release file path must be canonical under pilot/: {value!r}")
    return canonical


def _inventory(pilot: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(pilot.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError(f"release payload contains a symbolic link: {path.name}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"release payload contains a non-regular file: {path.name}")
        relative = _canonical_relative_path(
            "pilot/" + path.relative_to(pilot).as_posix()
        )
        if relative in seen:
            raise ValueError(f"duplicate release file path: {relative}")
        seen.add(relative)
        entries.append({"path": relative, "size": path.stat().st_size})
    if not entries:
        raise ValueError("release payload is empty")
    return entries


def _manifest(version: str, files: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "format": FORMAT,
        "contractVersion": CONTRACT_VERSION,
        "releaseVersion": version,
        "entrypoint": "pilot/index.html",
        "pilotManifest": "pilot/pilot-manifest.json",
        "files": files,
    }


def validate_release_manifest(value: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, dict):
        return ["$: must be an object"]
    unknown = sorted(set(value) - MANIFEST_FIELDS)
    missing = sorted(MANIFEST_FIELDS - set(value))
    issues.extend(f"$.{field}: unsupported field" for field in unknown)
    issues.extend(f"$.{field}: required field missing" for field in missing)
    if missing:
        return issues
    if value.get("format") != FORMAT:
        issues.append("$.format: unsupported release format")
    if value.get("contractVersion") != CONTRACT_VERSION:
        issues.append("$.contractVersion: unsupported contract version")
    try:
        validate_release_version(value.get("releaseVersion"))
    except ValueError as exc:
        issues.append(f"$.releaseVersion: {exc}")
    if value.get("entrypoint") != "pilot/index.html":
        issues.append("$.entrypoint: must equal pilot/index.html")
    if value.get("pilotManifest") != "pilot/pilot-manifest.json":
        issues.append("$.pilotManifest: must equal pilot/pilot-manifest.json")
    files = value.get("files")
    if not isinstance(files, list) or not files:
        issues.append("$.files: must be a non-empty array")
        return issues
    paths: list[str] = []
    for index, entry in enumerate(files):
        prefix = f"$.files[{index}]"
        if not isinstance(entry, dict):
            issues.append(f"{prefix}: must be an object")
            continue
        for field in sorted(set(entry) - FILE_FIELDS):
            issues.append(f"{prefix}.{field}: unsupported field")
        for field in sorted(FILE_FIELDS - set(entry)):
            issues.append(f"{prefix}.{field}: required field missing")
        if "path" in entry:
            try:
                paths.append(_canonical_relative_path(entry["path"]))
            except ValueError as exc:
                issues.append(f"{prefix}.path: {exc}")
        size = entry.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            issues.append(f"{prefix}.size: must be a non-negative integer")
    if len(paths) != len(set(paths)):
        issues.append("$.files: duplicate paths are forbidden")
    if paths != sorted(paths):
        issues.append("$.files: paths must be sorted lexicographically")
    return issues


def _verify_release(directory: Path, expected_version: str) -> dict[str, Any]:
    manifest_path = directory / "release-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("release manifest is missing or not a regular file")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"release manifest is unreadable: {exc}") from exc
    issues = validate_release_manifest(manifest)
    if issues:
        raise ValueError("invalid release manifest:\n- " + "\n- ".join(issues))
    if manifest["releaseVersion"] != expected_version:
        raise ValueError("release manifest version does not match requested version")
    pilot = directory / "pilot"
    actual = _inventory(pilot)
    if actual != manifest["files"]:
        raise ValueError("release manifest file inventory does not match payload")
    for fixed in (manifest["entrypoint"], manifest["pilotManifest"]):
        target = directory / PurePosixPath(fixed)
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"release target is missing: {fixed}")
    return manifest


def _install_tree_no_replace(staged: Path, output: Path, version: str) -> None:
    try:
        os.mkdir(output, 0o755)
    except FileExistsError as exc:
        raise ValueError("release output path already exists") from exc
    created_dirs: list[Path] = []
    installed_files: list[Path] = []
    try:
        for source in sorted(staged.rglob("*"), key=lambda item: item.as_posix()):
            relative = source.relative_to(staged)
            destination = output / relative
            if source.is_symlink():
                raise ValueError(f"release staging contains a symbolic link: {relative}")
            if source.is_dir():
                destination.mkdir()
                created_dirs.append(destination)
                continue
            if not source.is_file():
                raise ValueError(f"release staging contains a non-regular file: {relative}")
            try:
                os.link(source, destination, follow_symlinks=False)
            except FileExistsError as exc:
                raise ValueError("release output changed during installation") from exc
            installed_files.append(destination)
        _verify_release(output, version)
    except BaseException:
        for path in reversed(installed_files):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        for path in reversed(created_dirs):
            try:
                path.rmdir()
            except OSError:
                pass
        try:
            output.rmdir()
        except OSError:
            pass
        raise


def build_evaluator_release(output_parent: Path, release_version: str) -> Path:
    version = validate_release_version(release_version)
    parent = output_parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    output = parent / f"raiatea-evaluator-{version}"
    if _path_lexists(output):
        raise ValueError("release output path already exists")
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=parent))
    try:
        pilot = temporary / "pilot"
        build_pilot.build_pilot(pilot)
        files = _inventory(pilot)
        manifest = _manifest(version, files)
        issues = validate_release_manifest(manifest)
        if issues:
            raise ValueError("generated release manifest is invalid:\n- " + "\n- ".join(issues))
        (temporary / "release-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _verify_release(temporary, version)
        _install_tree_no_replace(temporary, output, version)
        return output
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a versioned Raiatea evaluator release directory"
    )
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--release-version", required=True)
    args = parser.parse_args()
    try:
        result = build_evaluator_release(args.output_parent, args.release_version)
    except (OSError, ValueError) as exc:
        print("Evaluator release build failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print(result)


if __name__ == "__main__":
    main()
