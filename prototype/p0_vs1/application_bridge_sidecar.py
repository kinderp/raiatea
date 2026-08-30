#!/usr/bin/env python3
"""Local read-only sidecar for the Raiatea GUI Application Layer.

The trusted parent process supplies the catalog store path and opaque scope id at
process bootstrap. Renderer requests carry neither host roots nor process-launch
authority. Stdout is reserved for the versioned JSON-RPC/NDJSON protocol; stderr
is non-authoritative operator diagnostics.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any, BinaryIO

from prototype.p0_vs1.application_bridge_contract import (
    ApplicationBridgeContractError,
    BRIDGE_METHODS,
    MAX_BRIDGE_FRAME_BYTES,
    MAX_BRIDGE_PAGE_SIZE,
    METHOD_GATEWAY_STATUS,
    METHOD_LIBRARY_PAGE,
    METHOD_REPRESENTATION_PAGE,
    METHOD_SEARCH_PAGE,
    METHOD_SOURCE_DETAIL,
    decode_frame,
    encode_frame,
    error_message,
    result_message,
)
from prototype.p0_vs1.application_facade import (
    ApplicationFacadeError,
    RaiateaApplicationFacade,
)
from prototype.p0_vs1.catalog_store import CatalogStateStore
from prototype.p0_vs1.search_service import SearchServiceError


JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603
BRIDGE_APPLICATION_ERROR = -32010
BRIDGE_RESPONSE_TOO_LARGE = -32011
BRIDGE_REQUEST_TOO_LARGE = -32012

_SAFE_APPLICATION_MESSAGE = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")


class ApplicationBridgeDispatchError(ValueError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require_params_shape(
    params: Any,
    *,
    allowed: set[str],
    required: set[str] = frozenset(),
) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise ApplicationBridgeDispatchError(
            JSONRPC_INVALID_PARAMS,
            "bridge-params-must-be-object",
        )
    actual = set(params)
    missing = sorted(required - actual)
    extra = sorted(actual - allowed)
    if missing:
        raise ApplicationBridgeDispatchError(
            JSONRPC_INVALID_PARAMS,
            f"bridge-param-required:{missing[0]}",
        )
    if extra:
        raise ApplicationBridgeDispatchError(
            JSONRPC_INVALID_PARAMS,
            f"bridge-param-unknown:{extra[0]}",
        )
    return params


def _page_params(params: dict[str, Any]) -> tuple[int, str | None]:
    page_size = params.get("page_size", 50)
    if (
        not isinstance(page_size, int)
        or isinstance(page_size, bool)
        or not 1 <= page_size <= MAX_BRIDGE_PAGE_SIZE
    ):
        raise ApplicationBridgeDispatchError(
            JSONRPC_INVALID_PARAMS,
            "bridge-page-size-invalid",
        )
    cursor = params.get("cursor")
    if cursor is not None and not isinstance(cursor, str):
        raise ApplicationBridgeDispatchError(
            JSONRPC_INVALID_PARAMS,
            "bridge-cursor-invalid",
        )
    return page_size, cursor


def _safe_application_message(exc: BaseException) -> str:
    observed = str(exc)
    if _SAFE_APPLICATION_MESSAGE.fullmatch(observed):
        return observed
    return "application-request-rejected"


class ApplicationBridgeService:
    """Dispatch bridge methods to one configured RaiateaApplicationFacade."""

    def __init__(self, facade: RaiateaApplicationFacade) -> None:
        self.facade = facade

    def dispatch(self, method: str, params: dict[str, Any]) -> Any:
        if method not in BRIDGE_METHODS:
            raise ApplicationBridgeDispatchError(
                JSONRPC_METHOD_NOT_FOUND,
                "bridge-method-not-found",
            )

        if method == METHOD_GATEWAY_STATUS:
            _require_params_shape(params, allowed=set())
            return {
                "mode": "live",
                "label": "Local Raiatea",
                "detail": "Connected to the local Raiatea Application Layer.",
            }

        if method == METHOD_LIBRARY_PAGE:
            values = _require_params_shape(
                params,
                allowed={"page_size", "cursor"},
            )
            page_size, cursor = _page_params(values)
            return self.facade.library_page(page_size=page_size, cursor=cursor)

        if method == METHOD_SOURCE_DETAIL:
            values = _require_params_shape(
                params,
                allowed={"item_ref"},
                required={"item_ref"},
            )
            item_ref = values["item_ref"]
            if not isinstance(item_ref, str) or not item_ref:
                raise ApplicationBridgeDispatchError(
                    JSONRPC_INVALID_PARAMS,
                    "bridge-item-ref-invalid",
                )
            return self.facade.source_detail(item_ref)

        if method == METHOD_SEARCH_PAGE:
            values = _require_params_shape(
                params,
                allowed={"plan", "page_size", "cursor"},
                required={"plan"},
            )
            plan = values["plan"]
            if not isinstance(plan, dict):
                raise ApplicationBridgeDispatchError(
                    JSONRPC_INVALID_PARAMS,
                    "bridge-search-plan-invalid",
                )
            page_size, cursor = _page_params(values)
            return self.facade.search_page(
                plan,
                page_size=page_size,
                cursor=cursor,
            )

        if method == METHOD_REPRESENTATION_PAGE:
            values = _require_params_shape(
                params,
                allowed={"representation_id", "page_size", "cursor"},
                required={"representation_id"},
            )
            representation_id = values["representation_id"]
            if not isinstance(representation_id, str) or not representation_id:
                raise ApplicationBridgeDispatchError(
                    JSONRPC_INVALID_PARAMS,
                    "bridge-representation-id-invalid",
                )
            page_size, cursor = _page_params(values)
            return self.facade.representation_page(
                representation_id,
                page_size=page_size,
                cursor=cursor,
            )

        raise ApplicationBridgeDispatchError(
            JSONRPC_METHOD_NOT_FOUND,
            "bridge-method-not-found",
        )


def handle_request(
    service: ApplicationBridgeService,
    request: dict[str, Any],
) -> dict[str, Any]:
    request_id = request["id"]
    method = request["method"]
    params = request["params"]
    try:
        payload = service.dispatch(method, params)
        return result_message(request_id, method, payload)
    except ApplicationBridgeDispatchError as exc:
        return error_message(request_id, exc.code, exc.message)
    except (ApplicationFacadeError, SearchServiceError) as exc:
        return error_message(
            request_id,
            BRIDGE_APPLICATION_ERROR,
            _safe_application_message(exc),
        )
    except Exception as exc:  # fail closed; raw internals stay on stderr only
        print(
            f"application-bridge-internal-error:{type(exc).__name__}",
            file=sys.stderr,
            flush=True,
        )
        return error_message(
            request_id,
            JSONRPC_INTERNAL_ERROR,
            "application-bridge-internal-error",
        )


def _write_response(output: BinaryIO, response: dict[str, Any]) -> None:
    request_id = response.get("id")
    try:
        frame = encode_frame(response)
    except ApplicationBridgeContractError as exc:
        if str(exc) != "bridge-frame-too-large":
            raise
        frame = encode_frame(
            error_message(
                request_id if isinstance(request_id, (str, int)) else None,
                BRIDGE_RESPONSE_TOO_LARGE,
                "bridge-response-too-large",
            )
        )
    output.write(frame)
    output.flush()


def serve(
    service: ApplicationBridgeService,
    *,
    input_stream: BinaryIO,
    output_stream: BinaryIO,
) -> None:
    while True:
        raw = input_stream.readline(MAX_BRIDGE_FRAME_BYTES + 1)
        if raw == b"":
            return
        if len(raw) > MAX_BRIDGE_FRAME_BYTES:
            # Drain the remainder of the oversized logical line before accepting
            # another request so one bad frame cannot desynchronize the stream.
            while raw and not raw.endswith(b"\n"):
                raw = input_stream.readline(MAX_BRIDGE_FRAME_BYTES + 1)
            _write_response(
                output_stream,
                error_message(None, BRIDGE_REQUEST_TOO_LARGE, "bridge-request-too-large"),
            )
            continue
        try:
            request = decode_frame(raw)
            if "method" not in request:
                raise ApplicationBridgeContractError("bridge-request-expected")
        except ApplicationBridgeContractError:
            _write_response(
                output_stream,
                error_message(None, JSONRPC_PARSE_ERROR, "bridge-invalid-request-frame"),
            )
            continue
        _write_response(output_stream, handle_request(service, request))


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Raiatea local GUI application bridge")
    parser.add_argument("--catalog-store", required=True)
    parser.add_argument("--scope-id", required=True)
    args = parser.parse_args(argv)
    path = Path(args.catalog_store)
    if not path.is_absolute():
        parser.error("--catalog-store must be absolute")
    if not isinstance(args.scope_id, str) or not args.scope_id:
        parser.error("--scope-id is required")
    args.catalog_store = path
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    store = CatalogStateStore(args.catalog_store)
    facade = RaiateaApplicationFacade(store, args.scope_id)
    service = ApplicationBridgeService(facade)
    serve(
        service,
        input_stream=sys.stdin.buffer,
        output_stream=sys.stdout.buffer,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
