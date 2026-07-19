#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

import build_evaluator_archive
import build_evaluator_release
import build_posix_evaluator_archive

ROOT = Path(__file__).parent
WINDOWS_HELPERS = ("Launch-Raiatea.ps1", "Stop-Raiatea.ps1")
WINDOWS_GUIDE = "WINDOWS-LAUNCH.md"


def _guide_text(version: str) -> str:
    build_evaluator_release.validate_release_version(version)
    return f"""# Avvio Windows della release Raiatea {version}

Richiede Windows PowerShell 5.1 o PowerShell 7 e Python 3.10 o successivo. Gli helper non modificano execution policy, registro, firewall, servizi o impostazioni di sistema.

## Avvio

Dalla directory estratta `raiatea-evaluator-{version}`:

```powershell
powershell -NoProfile -File .\Launch-Raiatea.ps1 -NoOpen
```

Per scegliere una porta:

```powershell
powershell -NoProfile -File .\Launch-Raiatea.ps1 -Port 8123
```

## Arresto

```powershell
powershell -NoProfile -File .\Stop-Raiatea.ps1
```

Il server ascolta soltanto su `127.0.0.1`. Lo stato locale sotto `.raiatea-runtime` non contiene dati del discente.
"""


def build_desktop_evaluator_archive(output_parent: Path, release_version: str) -> Path:
    version = build_evaluator_release.validate_release_version(release_version)
    parent = output_parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    output = parent / f"raiatea-evaluator-{version}.tar"
    if os.path.lexists(os.fspath(output)):
        raise ValueError("archive output path already exists")
    workspace = Path(tempfile.mkdtemp(prefix=".raiatea-desktop-archive.", dir=parent))
    try:
        posix_archive = build_posix_evaluator_archive.build_posix_evaluator_archive(workspace / "posix", version)
        release = build_evaluator_archive.verify_evaluator_archive(posix_archive, workspace / "extracted")
        (release / build_evaluator_archive.CHECKSUMS).unlink()
        for name in WINDOWS_HELPERS:
            source = ROOT / name
            target = release / name
            if source.is_symlink() or not source.is_file() or target.exists() or target.is_symlink():
                raise ValueError(f"unsafe Windows helper: {name}")
            shutil.copyfile(source, target)
        (release / WINDOWS_GUIDE).write_text(_guide_text(version), encoding="utf-8", newline="\n")
        build_evaluator_archive._write_checksums(release)
        staged = workspace / output.name
        build_evaluator_archive._write_archive(release, staged)
        build_evaluator_archive.verify_evaluator_archive(staged, workspace / "verified")
        try:
            os.link(staged, output, follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("archive output changed during installation") from exc
        return output
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Raiatea desktop evaluator archive")
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--release-version", required=True)
    args = parser.parse_args()
    try:
        result = build_desktop_evaluator_archive(args.output_parent, args.release_version)
    except (OSError, ValueError) as exc:
        print("Desktop evaluator archive build failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print(result)


if __name__ == "__main__":
    main()
