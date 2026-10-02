"""Compact, payload-free HTTP coordination events."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import json
import logging
from typing import TypeVar

from starlette.responses import Response


_LOG = logging.getLogger("exact_orb.http_api")
_T = TypeVar("_T")


def request_started(request_id: str, method: str, route: str, *, run_id: str | None) -> None:
    _LOG.info(
        "http_request_started request_id=%s method=%s route=%s run_id=%s",
        request_id, method, route, run_id or "none",
    )


def _public_code(response: Response) -> str:
    if response.status_code < 400:
        return "none"
    try:
        payload = json.loads(response.body)
    except (AttributeError, TypeError, ValueError):
        return "none"
    code = payload.get("code") if isinstance(payload, dict) else None
    return code if isinstance(code, str) else "none"


def request_finished(
    request_id: str, *, run_id: str | None, started_at: float, now: float,
    response: Response | None = None, outcome: str | None = None,
    status_code: int | None = None, public_code: str | None = None,
) -> None:
    status = response.status_code if response is not None else status_code
    if outcome is None:
        assert status is not None
        outcome = (
            "timeout" if status == 504 else
            "success" if status < 400 else
            "rejected" if status < 500 else "failed"
        )
    code = _public_code(response) if response is not None else public_code or "none"
    duration_ms = max(0, round((now - started_at) * 1000))
    level = logging.WARNING if status is None or status >= 500 else logging.INFO
    _LOG.log(
        level,
        "http_request_finished request_id=%s run_id=%s outcome=%s status=%s "
        "code=%s duration_ms=%s",
        request_id, run_id or "none", outcome, status if status is not None else "none",
        code, duration_ms,
    )


def message(
    request_id: str, *, direction: str, peer: str, operation: str,
    message_type: str, run_id: str | None = None,
) -> None:
    _LOG.info(
        "http_message request_id=%s run_id=%s direction=%s peer=%s "
        "operation=%s message_type=%s",
        request_id, run_id or "none", direction, peer, operation, message_type,
    )


async def exchange(
    request_id: str, *, peer: str, operation: str,
    call: Callable[[], Awaitable[_T]], run_id: str | None = None,
    result_type: str | Callable[[_T], str] | None = None,
    none_result_type: str | None = None,
) -> _T:
    """Log the actual call boundary; receive exists only for a returned result."""

    message(
        request_id, direction="send", peer=peer, operation=operation,
        message_type="Call", run_id=run_id,
    )
    result = await call()
    received_type = result_type(result) if callable(result_type) else result_type
    message(
        request_id, direction="receive", peer=peer, operation=operation,
        message_type=received_type or (
            none_result_type if result is None and none_result_type is not None
            else type(result).__name__
        ), run_id=run_id,
    )
    return result


def admission_rejected(
    request_id: str, *, run_id: str | None, kind: str, scope: str,
    code: str, detail_code: str | None, retry_after: int,
) -> None:
    _LOG.info(
        "http_admission_rejected request_id=%s run_id=%s class=%s scope=%s "
        "code=%s detail_code=%s retry_after=%s",
        request_id, run_id or "none", kind, scope, code,
        detail_code or "none", retry_after,
    )


def cookie_replaced(request_id: str, reason: str) -> None:
    _LOG.info("http_cookie_replaced request_id=%s reason=%s", request_id, reason)


def chart_unavailable(request_id: str, safe_reason: str) -> None:
    _LOG.error(
        "chart_unavailable request_id=%s safe_reason=%s", request_id, safe_reason,
    )
