#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import build_evaluator_archive
import build_evaluator_release
import build_field_pilot_archive
import evaluator_session_aggregate
import evaluator_session_batch_intake
import evaluator_session_batch_manifest
import evaluator_session_record

ROOT = Path(__file__).parent
TOOLS = (
    "evaluator_session_record.py",
    "evaluator_session_batch_manifest.py",
    "evaluator_session_batch_intake.py",
    "evaluator_session_aggregate.py",
)
GUIDE = "SYNTHESIS-KIT.md"
EXAMPLE = "synthesis-example"


def _record(version: str, platform: str, launcher: str, truth: bool) -> dict[str, object]:
    return {
        "format": evaluator_session_record.FORMAT,
        "version": evaluator_session_record.VERSION,
        "releaseVersion": version,
        "platform": platform,
        "launcher": launcher,
        "results": {key: truth for key in evaluator_session_record.RESULT_KEYS},
        "observations": "",
        "declaration": evaluator_session_record.DECLARATION,
    }


def _write_json(path: Path, value: object) -> bytes:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def _guide_text(version: str) -> str:
    build_evaluator_release.validate_release_version(version)
    return f"""# Kit locale di sintesi Raiatea {version}

Il kit aggrega esclusivamente record valutatore locali già validi. Non importa evidenze del discente, non usa account e non invia dati in rete.

## Esempio incluso

```text
python evaluator_session_batch_manifest.py synthesis-example/batch-manifest.json
python evaluator_session_batch_intake.py synthesis-example/batch-manifest.json --root synthesis-example
python evaluator_session_aggregate.py synthesis-example/batch-manifest.json --root synthesis-example --themes synthesis-example/themes.json --output synthesis-example/aggregate-copy.json
```

Il file `synthesis-example/aggregate.json` è il risultato canonico atteso. L'output nuovo non sostituisce file esistenti.

## Uso con record propri

Mettere i record sotto una directory locale, creare un manifest con percorsi relativi e digest SHA-256, validare l'intake e generare l'aggregato. Le label ammesse sono: {', '.join(evaluator_session_aggregate.APPROVED_THEMES)}.

## Cleanup

Eliminare esplicitamente manifest, assegnazioni di label, aggregati ed eventuali copie dei record. Il kit non crea servizi, database, cache persistenti, upload, telemetria o processi in background.
"""


def _install_tools(release: Path) -> None:
    for name in TOOLS:
        source = ROOT / name
        target = release / name
        if os.path.lexists(os.fspath(target)):
            raise ValueError(f"synthesis tool already exists: {name}")
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"synthesis tool source is unsafe: {name}")
        shutil.copyfile(source, target)


def _install_example(release: Path, version: str) -> None:
    example = release / EXAMPLE
    if os.path.lexists(os.fspath(example)):
        raise ValueError("synthesis example already exists")
    linux = _record(version, "linux", "posix", True)
    windows = _record(version, "windows", "powershell", False)
    linux_bytes = _write_json(example / "sessions/linux.json", linux)
    windows_bytes = _write_json(example / "sessions/windows.json", windows)
    entries = [
        ("sessions/linux.json", hashlib.sha256(linux_bytes).hexdigest()),
        ("sessions/windows.json", hashlib.sha256(windows_bytes).hexdigest()),
    ]
    manifest = evaluator_session_batch_manifest.build_manifest(entries)
    _write_json(example / "batch-manifest.json", manifest)
    themes = {
        entries[0][1]: ["navigation"],
        entries[1][1]: ["stability"],
    }
    _write_json(example / "themes.json", themes)
    snapshots = evaluator_session_batch_intake.validate_batch_intake(example / "batch-manifest.json", example)
    aggregate = evaluator_session_aggregate.build_aggregate(snapshots, themes)
    _write_json(example / "aggregate.json", aggregate)


def build_synthesis_kit_archive(output_parent: Path, release_version: str) -> Path:
    version = build_evaluator_release.validate_release_version(release_version)
    parent = output_parent.resolve()
    parent.mkdir(parents=True, exist_ok=True)
    output = parent / f"raiatea-evaluator-{version}.tar"
    if os.path.lexists(os.fspath(output)):
        raise ValueError("archive output path already exists")
    workspace = Path(tempfile.mkdtemp(prefix=".raiatea-synthesis-kit.", dir=parent))
    try:
        base = build_field_pilot_archive.build_field_pilot_archive(workspace / "base", version)
        release = build_evaluator_archive.verify_evaluator_archive(base, workspace / "extracted")
        (release / build_evaluator_archive.CHECKSUMS).unlink()
        _install_tools(release)
        _install_example(release, version)
        (release / GUIDE).write_text(_guide_text(version), encoding="utf-8", newline="\n")
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
    parser = argparse.ArgumentParser(description="Build the Raiatea field-pilot synthesis kit archive")
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument("--release-version", required=True)
    args = parser.parse_args()
    try:
        print(build_synthesis_kit_archive(args.output_parent, args.release_version))
    except (OSError, ValueError) as exc:
        print("Synthesis kit archive build failed:")
        print(f"- {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
