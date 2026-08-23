#!/usr/bin/env python3
"""Dependency-light JSON-RPC 2.0 / NDJSON transport candidate.

This module owns wire framing only. It deliberately knows nothing about E-05
or Plugin Runtime domain meaning.
"""
from __future__ import annotations

import json
from typing import Any


MAX_FRAME_BYTES = 256 * 1024
FORBIDDEN_INLINE_KEYS = {"base64", "blob", "bytes", "content"}


class TransportError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TransportError(message)


def _valid_id(value: Any) -> bool:
    return (isinstance(value, (str, int)) and not isinstance(value, bool)) or value is None


def _scan_no_inline_payload(value: Any, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require(isinstance(key, str), f"{path}-key-must-be-string")
            normalized = key.strip().lower().replace("-", "_")
            _require(normalized not in FORBIDDEN_INLINE_KEYS, f"inline-large-payload-field-forbidden:{key}")
            _scan_no_inline_payload(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_no_inline_payload(child, f"{path}[{index}]")


def validate_message(message: Any) -> dict[str, Any]:
    _require(isinstance(message, dict), "jsonrpc-message-must-be-object")
    _require(message.get("jsonrpc") == "2.0", "unsupported-jsonrpc-version")

    has_method = "method" in message
    has_result = "result" in message
    has_error = "error" in message

    if has_method:
        _require(not has_result and not has_error, "jsonrpc-request-cannot-be-response")
        _require(isinstance(message.get("method"), str) and bool(message["method"]), "jsonrpc-method-required")
        _require(set(message) <= {"jsonrpc", "id", "method", "params"}, "unknown-jsonrpc-request-field")
        if "id" in message:
            _require(_valid_id(message["id"]), "invalid-jsonrpc-id")
        params = message.get("params", {})
        _require(isinstance(params, dict), "jsonrpc-params-must-be-object")
        _scan_no_inline_payload(params, "params")
        return message

    _require("id" in message and _valid_id(message.get("id")), "jsonrpc-response-id-required")
    _require(has_result != has_error, "jsonrpc-response-needs-exactly-one-result-or-error")
    _require(set(message) <= {"jsonrpc", "id", "result", "error"}, "unknown-jsonrpc-response-field")

    if has_error:
        error = message.get("error")
        _require(isinstance(error, dict), "jsonrpc-error-must-be-object")
        _require(set(error) == {"code", "message"}, "jsonrpc-error-is-protocol-only")
        _require(isinstance(error.get("code"), int) and not isinstance(error.get("code"), bool), "jsonrpc-error-code-required")
        _require(isinstance(error.get("message"), str) and bool(error["message"]), "jsonrpc-error-message-required")
    else:
        _scan_no_inline_payload(message.get("result"), "result")
    return message


def encode_frame(message: dict[str, Any]) -> bytes:
    validate_message(message)
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    _require(b"\n" not in payload and b"\r" not in payload, "jsonrpc-frame-contains-raw-newline")
    _require(len(payload) + 1 <= MAX_FRAME_BYTES, "jsonrpc-frame-too-large")
    return payload + b"\n"


def decode_frame(frame: bytes | str) -> dict[str, Any]:
    if isinstance(frame, str):
        raw = frame.encode("utf-8")
    else:
        _require(isinstance(frame, bytes), "jsonrpc-frame-must-be-bytes-or-text")
        raw = frame
    _require(bool(raw), "jsonrpc-empty-frame")
    _require(len(raw) <= MAX_FRAME_BYTES, "jsonrpc-frame-too-large")
    _require(raw.endswith(b"\n"), "jsonrpc-frame-missing-newline")
    payload = raw[:-1]
    if payload.endswith(b"\r"):
        payload = payload[:-1]
    _require(b"\n" not in payload and b"\r" not in payload, "jsonrpc-multiple-lines-in-frame")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise TransportError("jsonrpc-frame-not-utf8") from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TransportError("malformed-json-frame") from exc
    return validate_message(value)


def request_message(request_id: str | int, method: str, params: dict[str, Any]) -> dict[str, Any]:
    return validate_message({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})


def notification_message(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return validate_message({"jsonrpc": "2.0", "method": method, "params": params})


def result_message(request_id: str | int | None, result: Any) -> dict[str, Any]:
    return validate_message({"jsonrpc": "2.0", "id": request_id, "result": result})


def error_message(request_id: str | int | None, code: int, message: str) -> dict[str, Any]:
    return validate_message({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})
