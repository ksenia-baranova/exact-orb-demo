"""Structured DEBUG messages at component request/response boundaries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Literal, TypeVar


MessageDirection = Literal["in", "out"]
MessageStatus = Literal["ok", "error"]
PayloadMode = Literal["full", "summary", "error"]
R = TypeVar("R")


async def log_async_component_call(
    logger: logging.Logger,
    *,
    operation: str,
    request_type: str,
    run_id: object | None,
    request: object,
    call: Callable[[], Awaitable[R]],
    result_projector: Callable[[R], object] | None = None,
    result_message_type: str | None = None,
    result_payload_mode: Literal["full", "summary"] = "full",
    result_calculation_key: Callable[[R], object | None] | None = None,
) -> R:
    """Run an async boundary with an explicit full or summary result payload."""

    log_component_message(
        logger,
        direction="in",
        operation=operation,
        run_id=run_id,
        message=request,
        message_type=request_type,
    )
    try:
        result = await call()
    except BaseException as exc:
        log_component_message(
            logger,
            direction="out",
            operation=operation,
            run_id=run_id,
            message=exc,
            status="error",
            payload_mode="error",
        )
        raise

    logged_result = result
    calculation_key = None
    if logger.isEnabledFor(logging.DEBUG):
        if result_projector is not None:
            logged_result = result_projector(result)
        if result_calculation_key is not None:
            calculation_key = result_calculation_key(result)
    log_component_message(
        logger,
        direction="out",
        operation=operation,
        run_id=run_id,
        calculation_key=calculation_key,
        message=logged_result,
        message_type=result_message_type,
        payload_mode=result_payload_mode,
    )
    return result


def log_sync_component_call(
    logger: logging.Logger,
    *,
    operation: str,
    request_type: str,
    run_id: object | None,
    request: object,
    call: Callable[[], R],
    result_projector: Callable[[R], object] | None = None,
    result_message_type: str | None = None,
    result_payload_mode: Literal["full", "summary"] = "full",
    result_calculation_key: Callable[[R], object | None] | None = None,
) -> R:
    """Run a sync boundary with an explicit full or summary result payload."""

    log_component_message(
        logger,
        direction="in",
        operation=operation,
        run_id=run_id,
        message=request,
        message_type=request_type,
    )
    try:
        result = call()
    except BaseException as exc:
        log_component_message(
            logger,
            direction="out",
            operation=operation,
            run_id=run_id,
            message=exc,
            status="error",
            payload_mode="error",
        )
        raise

    logged_result = result
    calculation_key = None
    if logger.isEnabledFor(logging.DEBUG):
        if result_projector is not None:
            logged_result = result_projector(result)
        if result_calculation_key is not None:
            calculation_key = result_calculation_key(result)
    log_component_message(
        logger,
        direction="out",
        operation=operation,
        run_id=run_id,
        calculation_key=calculation_key,
        message=logged_result,
        message_type=result_message_type,
        payload_mode=result_payload_mode,
    )
    return result


def log_component_message(
    logger: logging.Logger,
    *,
    direction: MessageDirection,
    operation: str,
    run_id: object | None,
    calculation_key: object | None = None,
    message: object,
    message_type: str | None = None,
    status: MessageStatus = "ok",
    payload_mode: PayloadMode = "full",
) -> None:
    """Log one full, summary, or error boundary payload as single-line JSON."""

    if not logger.isEnabledFor(logging.DEBUG):
        return

    logger.debug(
        "component_message direction=%s operation=%s run_id=%s "
        "calculation_key=%s status=%s payload_mode=%s message_type=%s message=%s",
        direction,
        operation,
        "-" if run_id is None else str(run_id),
        "-" if calculation_key is None else str(calculation_key),
        status,
        payload_mode,
        message_type or type(message).__name__,
        serialize_component_message(message),
    )


def serialize_component_message(message: object) -> str:
    """Return a deterministic, one-line JSON representation of a message."""

    return json.dumps(
        message,
        default=_json_value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_value(value: object) -> object:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return model_dump(mode="json", warnings=False)
        except TypeError:
            return model_dump(mode="json")
    if isinstance(value, BaseException):
        details: dict[str, object] = {
            "exception_type": type(value).__name__,
            "message": str(value),
        }
        for field in ("code", "run_id"):
            field_value = getattr(value, field, None)
            if field_value is not None:
                details[field] = field_value
        return details
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="backslashreplace")
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    return repr(value)


__all__ = [
    "log_async_component_call",
    "log_component_message",
    "log_sync_component_call",
    "PayloadMode",
    "serialize_component_message",
]
