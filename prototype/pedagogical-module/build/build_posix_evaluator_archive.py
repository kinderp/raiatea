#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

import build_evaluator_archive
import build_evaluator_release

ROOT = Path(__file__).parent
HELPERS = ("launch-posix.sh", "stop-posix.sh")
GUIDE = "POSIX-LAUNCH.md"


def _guide_text(version: str) -> str:
    build_evaluator_release.validate_release_version(version)
    return f"""# Avvio POSIX della release Raiatea {version}

Questi helper supportano macOS e Linux con Python 3.10 o successivo. Non installano servizi, non richiedono privilegi e servono esclusivamente su `127.0.0.1`.

## Avvio

Dalla directory estratta `raiatea-evaluator-{version}`:

```sh
sh ./launch-posix.sh --no-open
```

Per scegliere una porta valida:

```sh
sh ./launch-posix.sh --port 8123
```

Senza `--no-open`, lo script prova ad aprire il browser locale dopo che `pilot/index.html` risponde. L'eventuale mancata apertura del browser non arresta il server.

## Arresto

```sh
sh ./stop-posix.sh
```

Lo stop usa soltanto lo stato locale sotto `.raiatea-runtime/` e rifiuta PID mancanti, obsoleti o appartenenti a processi estranei. La directory di stato non contiene dati del discente.
"""


def _install_helpers(release: Path, version: str) -> None:
    for name in HELPERS:
        source = ROOT / name
        target = release / name
        if target.exists() or target.is_symlink():
            raise ValueError(f"helper output already exists: {name}")
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"helper source is unsafe: {name}")
        shutil.copyfile(source, target)
    (release / GUIDE).write_text(_guide_text(version), encoding="utf-8", newline="\n")


def build_posix_evaluator_archive(output_parent: Path, release_version: str) -> Path:
    version = build_evaluator_release.validate_release_version(release_version)
    parent = output_parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    output = parent / f"raiatea-evaluator-{version}.tar"
    if os.path.lexists(os.fspath(output)):
        raise ValueError("archive output path already exists")
    workspace = Path(tempfile.mkdtemp(prefix=".raiatea-posix-archive.", dir=parent))
    try:
        base_parent = workspace / "base"
        base_archive = build_evaluator_archive.build_evaluator_archive(base_parent, version)
        extracted = build_evaluator_archive.verify_evaluator_archive(base_archive, workspace / "extracted")
        checksum = extracted / build_evaluator_archive.CHECKSUMS
        checksum.unlink()
        _install_helpers(extracted, version)
        build_evaluator_archive._write_checksums(extracted)
        staged = workspace / output.name
        build_evaluator_archive._write_archive(extracted, staged)
        build_evaluator_archive.verify_evaluator_archive(staged, workspace / "verified")
        try:
            os.link(staged, output, follow_symlinks=False)
        except FileExistsError as exc:
            raise ValueError("archive output changed during installation") from exc
        return output
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Raiatea evaluator archive with POSIX launch helpers")
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--release-version", required=True)
    args = parser.parse_args()
    try:
        result = build_posix_evaluator_archive(args.output_parent, args.release_version)
    except (OSError, ValueError) as exc:
        print("POSIX evaluator archive build failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc
    print(result)


if __name__ == "__main__":
    main()
