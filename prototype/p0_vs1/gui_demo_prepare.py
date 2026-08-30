#!/usr/bin/env python3
"""Prepare all disposable state/dependencies for the Raiatea Tauri live demo."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Sequence

from prototype.p0_vs1.gui_demo_bootstrap import bootstrap_demo


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = REPO_ROOT / "frontend"
TAURI_ROOT = FRONTEND_ROOT / "src-tauri"
LOCK_EVIDENCE = TAURI_ROOT / "lock-evidence.json"
DEFAULT_WORKSPACE = REPO_ROOT / ".raiatea-demo"
TAURI_CLI_VERSION = "2.11.4"
MIN_NODE = (22, 12, 0)
MIN_RUST = (1, 90, 0)


class GuiDemoPrepareError(RuntimeError):
    pass


def _version_tuple(text: str, label: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if match is None:
        raise GuiDemoPrepareError(f"gui-demo-{label}-version-unrecognized:{text.strip()}")
    return tuple(int(part) for part in match.groups())


def _require_command(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise GuiDemoPrepareError(f"gui-demo-required-command-missing:{name}")
    return resolved


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    capture: bool = False,
) -> str:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            check=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
        )
    except subprocess.CalledProcessError as exc:
        raise GuiDemoPrepareError(
            f"gui-demo-command-failed:{' '.join(command)}"
        ) from exc
    return completed.stdout or ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_demo(workspace: Path = DEFAULT_WORKSPACE) -> dict[str, object]:
    _require_command("node")
    _require_command("npm")
    _require_command("cargo")
    _require_command("rustc")

    node_version = _version_tuple(
        _run(["node", "--version"], cwd=REPO_ROOT, capture=True),
        "node",
    )
    if node_version < MIN_NODE:
        raise GuiDemoPrepareError("gui-demo-node-too-old-require-22.12")

    rust_version = _version_tuple(
        _run(["rustc", "--version"], cwd=REPO_ROOT, capture=True),
        "rust",
    )
    if rust_version < MIN_RUST:
        raise GuiDemoPrepareError("gui-demo-rust-too-old-require-1.90")

    tauri_version_output = _run(
        ["cargo", "tauri", "--version"],
        cwd=FRONTEND_ROOT,
        capture=True,
    )
    tauri_version = _version_tuple(tauri_version_output, "tauri-cli")
    if tauri_version != _version_tuple(TAURI_CLI_VERSION, "expected-tauri-cli"):
        raise GuiDemoPrepareError(
            f"gui-demo-tauri-cli-version-mismatch:expected-{TAURI_CLI_VERSION}"
        )

    manifest = bootstrap_demo(workspace)

    # The normal React/Vite lockfile remains committed and unchanged by the
    # desktop proof, so renderer dependencies install strictly with npm ci.
    _run(["npm", "ci"], cwd=FRONTEND_ROOT)

    evidence = json.loads(LOCK_EVIDENCE.read_text(encoding="utf-8"))
    expected_lock = evidence.get("cargo_lock_sha256")
    if not isinstance(expected_lock, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_lock):
        raise GuiDemoPrepareError("gui-demo-lock-evidence-invalid")

    cargo_lock = TAURI_ROOT / "Cargo.lock"
    if cargo_lock.exists():
        cargo_lock.unlink()
    _run(["cargo", "generate-lockfile"], cwd=TAURI_ROOT)
    actual_lock = _sha256(cargo_lock)
    if actual_lock != expected_lock:
        raise GuiDemoPrepareError(
            f"gui-demo-cargo-lock-drift:expected-{expected_lock}:actual-{actual_lock}"
        )

    result: dict[str, object] = {
        "demo_manifest": manifest,
        "node_version": ".".join(str(part) for part in node_version),
        "rust_version": ".".join(str(part) for part in rust_version),
        "tauri_cli_version": TAURI_CLI_VERSION,
        "cargo_lock_sha256": actual_lock,
        "next": "cd frontend && npm run tauri:dev",
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare the Raiatea live Tauri demo")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help="Disposable demo workspace (default: repo/.raiatea-demo)",
    )
    args = parser.parse_args(argv)
    result = prepare_demo(args.workspace.expanduser().resolve())
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GuiDemoPrepareError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
