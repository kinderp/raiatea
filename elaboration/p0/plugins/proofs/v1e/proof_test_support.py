#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from elaboration.p0.plugins.proofs.v1d import proof_broker as BROKER

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
MANIFEST_PATH = HERE / "manifest.json"
MODULE = "elaboration.p0.plugins.proofs.v1e.newline_transformer_plugin"
MEDIA_TYPE = "text/plain; charset=utf-8"
INPUT_HANDLE_ID = "handle:v1e:text:input"
INPUT_LEASE_ID = "lease:v1e:text:input"
DATA_HANDLE_ID = "handle:v1e:text:output"
DATA_LEASE_ID = "lease:v1e:text:output"
BUNDLE_HANDLE_ID = "handle:v1e:records:output"
BUNDLE_LEASE_ID = "lease:v1e:records:output"
INPUT_ARTIFACT_ID = "artifact:v1e:source-text"
OUTPUT_ARTIFACT_ID = "artifact:v1e:normalized-text"


def _utc_after(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def transformer_command() -> list[str]:
    return [sys.executable, "-m", MODULE]


def reset_runtime(payload: bytes | None = None) -> dict[str, Any]:
    if BROKER.RUNTIME_ROOT.exists():
        shutil.rmtree(BROKER.RUNTIME_ROOT)
    fixture_root = BROKER.FIXTURE_ROOT / "v1e"
    fixture_root.mkdir(parents=True)
    BROKER.OUTPUT_ROOT.mkdir(parents=True)
    input_path = fixture_root / "mixed-newlines.txt"
    input_bytes = payload if payload is not None else b"alpha\r\nbeta\rgamma\n"
    input_path.write_bytes(input_bytes)
    broker = {
        "proof_only": True,
        "workspace_scopes": {},
        "read_handles": {
            INPUT_HANDLE_ID: {
                "relative_path": "v1e/mixed-newlines.txt",
                "lease_id": INPUT_LEASE_ID
            }
        },
        "output_handles": {
            DATA_HANDLE_ID: {
                "relative_path": "v1e-normalized.txt",
                "lease_id": DATA_LEASE_ID
            },
            BUNDLE_HANDLE_ID: {
                "relative_path": "v1e-transformation-records.json",
                "lease_id": BUNDLE_LEASE_ID
            }
        }
    }
    BROKER.BROKER_PATH.write_text(json.dumps(broker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"input_path": input_path, "input_bytes": input_bytes, "broker": broker}


def request(runtime_instance_id: str, *, invocation_id: str = "invoke:v1e:transform:1") -> dict[str, Any]:
    input_bytes = (BROKER.FIXTURE_ROOT / "v1e" / "mixed-newlines.txt").read_bytes()
    expiry = _utc_after(10)
    return {
        "record_type": "invocation-request",
        "invocation_id": invocation_id,
        "idempotency_key": f"idem:{invocation_id}",
        "runtime_instance_id": runtime_instance_id,
        "capability": {"capability_id": "transform.run", "profile_id": "normalize-newlines-v1"},
        "inputs": [
            {
                "kind": "asset-handle",
                "handle": {
                    "handle_id": INPUT_HANDLE_ID,
                    "lease_id": INPUT_LEASE_ID,
                    "access": "read",
                    "media_type": MEDIA_TYPE,
                    "byte_length": len(input_bytes),
                    "fingerprint": sha256_bytes(input_bytes),
                    "expires_at": expiry
                }
            }
        ],
        "output_targets": [
            {
                "handle_id": DATA_HANDLE_ID,
                "lease_id": DATA_LEASE_ID,
                "access": "write-once-output",
                "media_type": MEDIA_TYPE,
                "max_byte_length": 65536,
                "expires_at": expiry
            },
            {
                "handle_id": BUNDLE_HANDLE_ID,
                "lease_id": BUNDLE_LEASE_ID,
                "access": "write-once-output",
                "media_type": "application/vnd.raiatea.transformation-proof+json",
                "max_byte_length": 131072,
                "expires_at": expiry
            }
        ],
        "runtime_context": {
            "workspace_scope_id": "workspace:v1e:transformer",
            "rights_decision_ref": "rights-proof:project-created-local-only",
            "secret_leases": []
        },
        "deadline_at": _utc_after(5),
        "parameters": {
            "input_artifact_id": INPUT_ARTIFACT_ID,
            "output_artifact_id": OUTPUT_ARTIFACT_ID
        }
    }


def read_output_bytes() -> bytes:
    return BROKER.read_core_output(DATA_HANDLE_ID, DATA_LEASE_ID)


def read_bundle() -> dict[str, Any]:
    return json.loads(BROKER.read_core_output(BUNDLE_HANDLE_ID, BUNDLE_LEASE_ID).decode("utf-8"))
