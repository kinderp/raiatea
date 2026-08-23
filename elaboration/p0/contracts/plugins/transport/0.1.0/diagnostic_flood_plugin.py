#!/usr/bin/env python3
"""Synthetic process that exceeds the candidate notification budget before a response."""
from __future__ import annotations

import json
import sys

import synthetic_plugin as S
from transport import MAX_FRAME_BYTES, TransportError, decode_frame, error_message, notification_message, result_message


def write(message: dict) -> None:
    S._write(message)


def main() -> int:
    manifest = json.loads(S.MANIFEST_PATH.read_text(encoding="utf-8"))
    handshaken = False
    while True:
        raw = sys.stdin.buffer.readline(MAX_FRAME_BYTES + 1)
        if raw == b"":
            return 0
        try:
            message = decode_frame(raw)
        except TransportError:
            write(error_message(None, -32700, "Parse error"))
            continue
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        if method == "raiatea.handshake":
            write(result_message(request_id, S._handshake(manifest)))
            handshaken = True
            continue
        if not handshaken:
            write(error_message(request_id, -32001, "Handshake required"))
            continue
        if method == "raiatea.invoke" and isinstance(params, dict):
            for index in range(65):
                diagnostic = S._diagnostic(params)
                diagnostic["diagnostic_id"] = f"diag:flood:{index}"
                write(notification_message("raiatea.diagnostic", diagnostic))
            write(result_message(request_id, S._invocation_result(manifest, params)))
            continue
        write(error_message(request_id, -32601, "Method not found"))


if __name__ == "__main__":
    raise SystemExit(main())
