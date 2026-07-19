#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

import build_desktop_evaluator_archive
import build_evaluator_archive
import build_evaluator_release

ROOT = Path(__file__).parent
MODULE_ROOT = ROOT.parent
FILES = {
    "evaluator-session-record.py": ROOT / "evaluator_session_record.py",
    "evaluator-session-record-v1.json": MODULE_ROOT / "contracts" / "evaluator-session-record-v1.json",
    "desktop-acceptance-matrix-v1.json": MODULE_ROOT / "contracts" / "desktop-acceptance-matrix-v1.json",
}
GUIDE = "EVALUATOR-SESSION.md"


def _guide_text(version: str) -> str:
    build_evaluator_release.validate_release_version(version)
    return f"""# Record locale della sessione valutatore — Raiatea {version}

Il record è facoltativo, locale e separato dalle evidenze del discente. Non contiene timestamp, nomi, account, risposte, browser storage, indirizzi IP, hostname, username, percorsi assoluti, analytics o dati macchina raccolti automaticamente.

## Creazione esplicita

```text
python evaluator-session-record.py create evaluator-session.json --release-version {version} --platform linux --launcher posix
```

Su macOS usare `--platform macos --launcher posix`; su Windows usare `--platform windows --launcher powershell`.

## Validazione ed export locale

```text
python evaluator-session-record.py validate evaluator-session.json
python evaluator-session-record.py export evaluator-session.json evaluator-session-copy.json
```

L'export crea una nuova copia e non sostituisce file esistenti.

## Eliminazione esplicita

```text
python evaluator-session-record.py delete evaluator-session.json
```

Non esistono upload, sincronizzazione, account, telemetria, analytics o invio remoto. La matrice `desktop-acceptance-matrix-v1.json` distingue le verifiche CI Linux/Windows dalla parità manuale macOS.
"""


def _install_field_files(release: Path, version: str) -> None:
    for name, source in FILES.items():
        target = release / name
        if os.path.lexists(os.fspath(target)):
            raise ValueError(f"field-pilot file already exists: {name}")
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"field-pilot source is unsafe: {name}")
        shutil.copyfile(source, target)
    (release / GUIDE).write_text(_guide_text(version), encoding="utf-8", newline="\n")


def build_field_pilot_archive(output_parent: Path, release_version: str) -> Path:
    version = build_evaluator_release.validate_release_version(release_version)
    parent = output_parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    output = parent / f"raiatea-evaluator-{version}.tar"
    if os.path.lexists(os.fspath(output)):
        raise ValueError("archive output path already exists")
    workspace = Path(tempfile.mkdtemp(prefix=".raiatea-field-pilot.", dir=parent))
    try:
        base = build_desktop_evaluator_archive.build_desktop_evaluator_archive(workspace / "base", version)
        release = build_evaluator_archive.verify_evaluator_archive(base, workspace / "extracted")
        (release / build_evaluator_archive.CHECKSUMS).unlink()
        _install_field_files(release, version)
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
    parser = argparse.ArgumentParser(description="Build the cross-platform Raiatea field-pilot archive")
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--release-version", required=True)
    args = parser.parse_args()
    try:
        print(build_field_pilot_archive(args.output_parent, args.release_version))
    except (OSError, ValueError) as exc:
        print("Field-pilot archive build failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
