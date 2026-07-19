#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

import build_evaluator_release

CHECKSUMS = "SHA256SUMS"


def _path_lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _distributed_files(release: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(release.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError(f"release contains a symbolic link: {path.relative_to(release)}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"release contains a non-regular file: {path.relative_to(release)}")
        if path.name != CHECKSUMS:
            files.append(path)
    return files


def _write_checksums(release: Path) -> Path:
    entries = []
    for path in _distributed_files(release):
        relative = path.relative_to(release).as_posix()
        entries.append(f"{_sha256(path)}  {relative}\n")
    target = release / CHECKSUMS
    if _path_lexists(target):
        raise ValueError("checksum file already exists")
    target.write_text("".join(entries), encoding="ascii", newline="\n")
    return target


def _parse_checksums(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for number, line in enumerate(text.splitlines(), 1):
        if len(line) < 67 or line[64:66] != "  ":
            raise ValueError(f"invalid checksum line {number}")
        digest, relative = line[:64], line[66:]
        if any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError(f"invalid checksum digest on line {number}")
        path = PurePosixPath(relative)
        if not relative or relative.startswith("/") or "\\" in relative or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError(f"unsafe checksum path on line {number}")
        canonical = path.as_posix()
        if canonical != relative or canonical == CHECKSUMS:
            raise ValueError(f"invalid checksum path on line {number}")
        if canonical in seen:
            raise ValueError("duplicate checksum path")
        seen.add(canonical)
        entries.append((digest, canonical))
    if not entries or [path for _, path in entries] != sorted(path for _, path in entries):
        raise ValueError("checksum paths must be non-empty and sorted")
    return entries


def _tar_info(name: str, directory: bool, size: int = 0) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name + ("/" if directory and not name.endswith("/") else ""))
    info.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
    info.size = 0 if directory else size
    info.mode = 0o755 if directory else 0o644
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def _write_archive(release: Path, archive: Path) -> None:
    root = release.name
    with tarfile.open(archive, "w", format=tarfile.USTAR_FORMAT) as target:
        target.addfile(_tar_info(root, True))
        for path in sorted(release.rglob("*"), key=lambda item: item.relative_to(release).as_posix()):
            if path.is_symlink():
                raise ValueError(f"release contains a symbolic link: {path.relative_to(release)}")
            relative = path.relative_to(release).as_posix()
            name = f"{root}/{relative}"
            if path.is_dir():
                target.addfile(_tar_info(name, True))
            elif path.is_file():
                data = path.read_bytes()
                target.addfile(_tar_info(name, False, len(data)), io.BytesIO(data))
            else:
                raise ValueError(f"release contains a non-regular entry: {relative}")


def verify_evaluator_archive(archive: Path, output_parent: Path) -> Path:
    parent = output_parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:") as source:
        members = source.getmembers()
        if not members:
            raise ValueError("archive is empty")
        names: list[str] = []
        root: str | None = None
        for member in members:
            name = member.name.rstrip("/")
            path = PurePosixPath(name)
            if not name or name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in path.parts):
                raise ValueError(f"unsafe archive member: {member.name}")
            if root is None:
                root = path.parts[0]
            if path.parts[0] != root or not root.startswith("raiatea-evaluator-"):
                raise ValueError("archive must contain one evaluator release root")
            if name in names:
                raise ValueError("duplicate archive member")
            names.append(name)
            if not (member.isdir() or member.isfile()):
                raise ValueError(f"unsupported archive member type: {member.name}")
            expected_mode = 0o755 if member.isdir() else 0o644
            if member.mtime != 0 or member.uid != 0 or member.gid != 0 or member.uname or member.gname or member.mode != expected_mode:
                raise ValueError(f"archive member metadata is not normalized: {member.name}")
        if names != sorted(names):
            raise ValueError("archive members are not sorted")
        assert root is not None
        destination = parent / root
        if _path_lexists(destination):
            raise ValueError("verification output path already exists")
        temporary = Path(tempfile.mkdtemp(prefix=f".{root}.", dir=parent))
        try:
            for member in members:
                relative = PurePosixPath(member.name).relative_to(root)
                target = temporary.joinpath(*relative.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    extracted = source.extractfile(member)
                    if extracted is None:
                        raise ValueError(f"cannot read archive member: {member.name}")
                    target.write_bytes(extracted.read())
            version = root.removeprefix("raiatea-evaluator-")
            build_evaluator_release._verify_release(temporary, version)
            checksum_path = temporary / CHECKSUMS
            entries = _parse_checksums(checksum_path.read_text(encoding="ascii"))
            actual = [p.relative_to(temporary).as_posix() for p in _distributed_files(temporary)]
            if actual != [path for _, path in entries]:
                raise ValueError("checksum inventory does not match extracted files")
            for digest, relative in entries:
                if _sha256(temporary / PurePosixPath(relative)) != digest:
                    raise ValueError(f"checksum mismatch: {relative}")
            os.replace(temporary, destination)
            return destination
        finally:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)


def build_evaluator_archive(output_parent: Path, release_version: str) -> Path:
    parent = output_parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    archive = parent / f"raiatea-evaluator-{release_version}.tar"
    if _path_lexists(archive):
        raise ValueError("archive output path already exists")
    workspace = Path(tempfile.mkdtemp(prefix=".raiatea-archive.", dir=parent))
    staged_archive = workspace / archive.name
    try:
        release = build_evaluator_release.build_evaluator_release(workspace, release_version)
        _write_checksums(release)
        _write_archive(release, staged_archive)
        verify_parent = workspace / "verify"
        verify_evaluator_archive(staged_archive, verify_parent)
        try:
            os.link(staged_archive, archive, follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("archive output changed during installation") from exc
        return archive
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a reproducible Raiatea evaluator archive")
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        result = verify_evaluator_archive(args.verify, args.output_parent) if args.verify else build_evaluator_archive(args.output_parent, args.release_version)
    except (OSError, ValueError, tarfile.TarError) as exc:
        print("Evaluator archive operation failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print(result)


if __name__ == "__main__":
    main()
