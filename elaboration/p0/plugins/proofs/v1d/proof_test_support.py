#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from . import proof_broker as BROKER

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[5]
GENERATOR_PATH = REPO_ROOT / "elaboration" / "p0" / "benchmark" / "generate_fixtures.py"
SOURCE_MANIFEST_PATH = HERE / "manifests" / "local-read-only-source-proof.json"
EXTRACTOR_MANIFEST_PATH = HERE / "manifests" / "direct-epub-extractor-proof.json"
SOURCE_MODULE = "elaboration.p0.plugins.proofs.v1d.local_source_plugin"
EXTRACTOR_MODULE = "elaboration.p0.plugins.proofs.v1d.epub_extractor_plugin"

_GENERATOR_SPEC = importlib.util.spec_from_file_location("v1d_fixture_generator", GENERATOR_PATH)
GENERATOR = importlib.util.module_from_spec(_GENERATOR_SPEC)
assert _GENERATOR_SPEC.loader is not None
_GENERATOR_SPEC.loader.exec_module(GENERATOR)


def _utc_after(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def reset_runtime() -> dict[str, Any]:
    if BROKER.RUNTIME_ROOT.exists():
        shutil.rmtree(BROKER.RUNTIME_ROOT)
    source_root = BROKER.FIXTURE_ROOT / "source-library"
    epub_root = BROKER.FIXTURE_ROOT / "epubs"
    source_root.mkdir(parents=True)
    (source_root / "nested").mkdir()
    epub_root.mkdir(parents=True)
    BROKER.OUTPUT_ROOT.mkdir(parents=True)

    (source_root / "alpha.txt").write_text("Raiatea v1d source proof alpha.\n", encoding="utf-8")
    (source_root / "nested" / "beta.md").write_text("# Raiatea v1d source proof beta\n", encoding="utf-8")

    epub_path = epub_root / "B02-EPUB-001.epub"
    GENERATOR.generate_epub_spine(epub_path)

    broker = {
        "proof_only": True,
        "workspace_scopes": {
            "workspace:v1d:source": "source-library"
        },
        "read_handles": {
            "handle:v1d:epub:input": {
                "relative_path": "epubs/B02-EPUB-001.epub",
                "lease_id": "lease:v1d:epub:input"
            }
        },
        "output_handles": {
            "handle:v1d:source:bundle": {
                "relative_path": "source-reference-bundle.json",
                "lease_id": "lease:v1d:source:bundle"
            },
            "handle:v1d:epub:bundle": {
                "relative_path": "e05-epub-bundle.json",
                "lease_id": "lease:v1d:epub:bundle"
            }
        }
    }
    BROKER.BROKER_PATH.write_text(json.dumps(broker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "source_root": source_root,
        "epub_path": epub_path,
        "epub_fingerprint": _sha256(epub_path),
        "broker": broker,
    }


def source_command() -> list[str]:
    return [sys.executable, "-m", SOURCE_MODULE]


def extractor_command() -> list[str]:
    return [sys.executable, "-m", EXTRACTOR_MODULE]


def source_request(runtime_instance_id: str) -> dict[str, Any]:
    expiry = _utc_after(10)
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:v1d:source:1",
        "idempotency_key": "idem:v1d:source:1",
        "runtime_instance_id": runtime_instance_id,
        "capability": {"capability_id": "source.discover", "profile_id": "local-read-only"},
        "inputs": [],
        "output_targets": [
            {
                "handle_id": "handle:v1d:source:bundle",
                "lease_id": "lease:v1d:source:bundle",
                "access": "write-once-output",
                "media_type": "application/vnd.raiatea.v1d-source-proof+json",
                "max_byte_length": 65536,
                "expires_at": expiry
            }
        ],
        "runtime_context": {
            "workspace_scope_id": "workspace:v1d:source",
            "rights_decision_ref": "rights-proof:project-created-local-only",
            "secret_leases": []
        },
        "deadline_at": _utc_after(5),
        "parameters": {}
    }


def extractor_request(runtime_instance_id: str, epub_path: Path) -> dict[str, Any]:
    expiry = _utc_after(10)
    return {
        "record_type": "invocation-request",
        "invocation_id": "invoke:v1d:epub:1",
        "idempotency_key": "idem:v1d:epub:1",
        "runtime_instance_id": runtime_instance_id,
        "capability": {"capability_id": "extract.run", "profile_id": "epub-direct-stdlib"},
        "inputs": [
            {
                "kind": "asset-handle",
                "handle": {
                    "handle_id": "handle:v1d:epub:input",
                    "lease_id": "lease:v1d:epub:input",
                    "access": "read",
                    "media_type": "application/epub+zip",
                    "byte_length": epub_path.stat().st_size,
                    "fingerprint": _sha256(epub_path),
                    "expires_at": expiry
                }
            }
        ],
        "output_targets": [
            {
                "handle_id": "handle:v1d:epub:bundle",
                "lease_id": "lease:v1d:epub:bundle",
                "access": "write-once-output",
                "media_type": "application/vnd.raiatea.e05-proof-bundle+json",
                "max_byte_length": 524288,
                "expires_at": expiry
            }
        ],
        "runtime_context": {
            "workspace_scope_id": "workspace:v1d:extractor",
            "rights_decision_ref": "rights-proof:project-created-local-only",
            "secret_leases": []
        },
        "deadline_at": _utc_after(5),
        "parameters": {}
    }


def load_output_bundle(handle_id: str, lease_id: str) -> dict[str, Any]:
    return json.loads(BROKER.read_core_output(handle_id, lease_id).decode("utf-8"))
