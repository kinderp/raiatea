#!/usr/bin/env python3
"""Versioned local wire contract for the Raiatea GUI application bridge.

This contract reuses the *mechanics* proven by ADR-0001 (JSON-RPC 2.0 over one
bounded UTF-8 JSON object per newline) without reusing the Plugin transport
validator itself. The Plugin transport forbids generic keys such as ``content``
for its control plane, while ``LibraryItem.content`` is legitimate Raiatea
application metadata.

The bridge carries only Application Layer read models. It is not a Plugin API,
not a filesystem authority channel and not a desktop-shell decision.
"""
from __future__ import annotations

import json
from typing import Any


BRIDGE_VERSION = "raiatea.gui-application-bridge.0.1.0"
MAX_BRIDGE_FRAME_BYTES = 1024 * 1024
MAX_BRIDGE_PAGE_SIZE = 200

METHOD_GATEWAY_STATUS = "gateway.status"
METHOD_LIBRARY_PAGE = "library.page"
METHOD_SOURCE_DETAIL = "source.detail"
METHOD_SEARCH_PAGE = "search.page"
METHOD_REPRESENTATION_PAGE = "representation.page"
BRIDGE_METHODS = frozenset(
    {
        METHOD_GATEWAY_STATUS,
        METHOD_LIBRARY_PAGE,
        METHOD_SOURCE_DETAIL,
        METHOD_SEARCH_PAGE,
        METHOD_REPRESENTATION_PAGE,
    }
)

# These names represent host authority rather than ordinary document/source
# metadata. ``current_relative_location`` is intentionally allowed and remains
# validated by the Application Layer itself.
FORBIDDEN_HOST_AUTHORITY_KEYS = frozenset(
    {
        "path",
        "filepath",
        "file_path",
        "host_path",
        "filesystem_path",
        "absolute_path",
        "root",
        "scope_root",
        "catalog_store",
        "catalog_store_path",
        "source_path",
        "working_directory",
        "cwd",
    }
)


class ApplicationBridgeContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ApplicationBridgeContractError(message)


def _valid_rpc_id(value: Any) -> bool:
    return isinstance(value, (str, int)) and not isinstance(value, bool)


def _scan_public_payload(value: Any, *, trail: str = "payload") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require(isinstance(key, str), f"{trail}-key-must-be-string")
            normalized = key.strip().lower().replace("-", "_")
            _require(
                normalized not in FORBIDDEN_HOST_AUTHORITY_KEYS,
                f"bridge-host-authority-field-forbidden:{trail}.{key}",
            )
            _scan_public_payload(child, trail=f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_public_payload(child, trail=f"{trail}[{index}]")


def _json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ApplicationBridgeContractError("bridge-value-not-json-safe") from exc


def validate_request_message(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "bridge-request-must-be-object")
    _require(
        set(value) == {"jsonrpc", "id", "method", "params"},
        "bridge-request-shape-invalid",
    )
    _require(value["jsonrpc"] == "2.0", "bridge-jsonrpc-version-unsupported")
    _require(_valid_rpc_id(value["id"]), "bridge-request-id-invalid")
    _require(
        isinstance(value["method"], str) and value["method"],
        "bridge-request-method-required",
    )
    _require(isinstance(value["params"], dict), "bridge-request-params-must-be-object")
    _scan_public_payload(value["params"], trail="params")
    return value


def validate_result_envelope(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "bridge-result-envelope-must-be-object")
    _require(
        set(value) == {"bridge_version", "method", "payload"},
        "bridge-result-envelope-shape-invalid",
    )
    _require(value["bridge_version"] == BRIDGE_VERSION, "bridge-version-unsupported")
    _require(value["method"] in BRIDGE_METHODS, "bridge-result-method-invalid")
    _scan_public_payload(value["payload"])
    _json_bytes(value)
    return value


def validate_response_message(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "bridge-response-must-be-object")
    _require(value.get("jsonrpc") == "2.0", "bridge-jsonrpc-version-unsupported")
    _require("id" in value and (value["id"] is None or _valid_rpc_id(value["id"])), "bridge-response-id-invalid")
    has_result = "result" in value
    has_error = "error" in value
    _require(has_result != has_error, "bridge-response-result-error-invalid")
    _require(
        set(value) == ({"jsonrpc", "id", "result"} if has_result else {"jsonrpc", "id", "error"}),
        "bridge-response-shape-invalid",
    )
    if has_result:
        validate_result_envelope(value["result"])
    else:
        error = value["error"]
        _require(isinstance(error, dict), "bridge-error-must-be-object")
        _require(set(error) == {"code", "message"}, "bridge-error-shape-invalid")
        _require(
            isinstance(error["code"], int) and not isinstance(error["code"], bool),
            "bridge-error-code-invalid",
        )
        _require(
            isinstance(error["message"], str) and error["message"],
            "bridge-error-message-required",
        )
    return value


def encode_frame(message: dict[str, Any]) -> bytes:
    if "method" in message:
        validate_request_message(message)
    else:
        validate_response_message(message)
    payload = _json_bytes(message)
    _require(b"\n" not in payload and b"\r" not in payload, "bridge-frame-raw-newline-forbidden")
    _require(
        len(payload) + 1 <= MAX_BRIDGE_FRAME_BYTES,
        "bridge-frame-too-large",
    )
    return payload + b"\n"


def decode_frame(frame: bytes | str) -> dict[str, Any]:
    raw = frame.encode("utf-8") if isinstance(frame, str) else frame
    _require(isinstance(raw, bytes), "bridge-frame-must-be-bytes-or-text")
    _require(bool(raw), "bridge-empty-frame")
    _require(len(raw) <= MAX_BRIDGE_FRAME_BYTES, "bridge-frame-too-large")
    _require(raw.endswith(b"\n"), "bridge-frame-missing-newline")
    payload = raw[:-1]
    if payload.endswith(b"\r"):
        payload = payload[:-1]
    _require(b"\n" not in payload and b"\r" not in payload, "bridge-multiple-lines-in-frame")
    try:
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApplicationBridgeContractError("bridge-malformed-json-frame") from exc
    if isinstance(value, dict) and "method" in value:
        return validate_request_message(value)
    return validate_response_message(value)


def request_message(request_id: str | int, method: str, params: dict[str, Any]) -> dict[str, Any]:
    return validate_request_message(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
    )


def result_message(request_id: str | int, method: str, payload: Any) -> dict[str, Any]:
    envelope = validate_result_envelope(
        {"bridge_version": BRIDGE_VERSION, "method": method, "payload": payload}
    )
    response = {"jsonrpc": "2.0", "id": request_id, "result": envelope}
    validate_response_message(response)
    return response


def error_message(request_id: str | int | None, code: int, message: str) -> dict[str, Any]:
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    validate_response_message(response)
    return response
