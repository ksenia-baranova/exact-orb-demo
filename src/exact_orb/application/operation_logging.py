"""Compact lifecycle records for ApplicationOrchestrator (R3.2 section 11.5).

The caller owns timing, attempt history and event ordering. These functions
only emit supplied facts through the existing Python logging configuration.
"""

from __future__ import annotations

import logging
from typing import Literal
from uuid import UUID


LOGGER = logging.getLogger(__name__)


def log_operation_started(*, run_id: UUID, command_type: str) -> None:
    """Record the start of an operation with its existing correlation ID."""
    LOGGER.info(
        "application_operation_started run_id=%s command_type=%s",
        str(run_id),
        command_type,
    )


def log_stage_finished(
    *,
    run_id: UUID,
    stage: str,
    outcome: str,
    duration_ms: float,
    state_version: int | None = None,
) -> None:
    """Record a completed load or handler stage, including a known version."""
    level = (
        logging.WARNING
        if outcome in ("invalid_outcome", "unexpected_failure")
        else logging.DEBUG
    )
    message = (
        "application_stage_finished run_id=%s stage=%s outcome=%s duration_ms=%s"
    )
    arguments: tuple[object, ...] = (str(run_id), stage, outcome, duration_ms)
    if state_version is not None:
        message += " state_version=%s"
        arguments += (state_version,)
    LOGGER.log(level, message, *arguments)


def log_commit_attempt_finished(
    *,
    run_id: UUID,
    attempt: Literal[1, 2],
    outcome: str,
    detail_code: str | None,
    duration_ms: float,
    state_version: int | None = None,
) -> None:
    """Record one supplied commit attempt; every second attempt is a warning."""
    level = (
        logging.WARNING
        if attempt == 2 or outcome in ("state_commit_failed", "unexpected_failure")
        else logging.DEBUG
    )
    message = (
        "application_commit_attempt_finished run_id=%s attempt=%s outcome=%s "
        "detail_code=%s duration_ms=%s"
    )
    arguments: tuple[object, ...] = (
        str(run_id), attempt, outcome, detail_code, duration_ms,
    )
    if state_version is not None:
        message += " state_version=%s"
        arguments += (state_version,)
    LOGGER.log(level, message, *arguments)


def log_operation_finished(
    *,
    run_id: UUID,
    orch_status: str,
    handler_status: str,
    context_status: str,
    code: str,
    detail_code: str | None,
    state_version: int | None,
    load_duration_ms: float | None,
    handler_duration_ms: float | None,
    commit_duration_ms: float | None,
    commit_attempts: Literal[0, 1, 2],
    commit_error_codes: tuple[str, ...],
    delivery_cancelled: bool,
) -> None:
    """Record the supplied result, even when its delivery was cancelled."""
    level = logging.WARNING if orch_status == "FAILURE" else logging.INFO
    LOGGER.log(
        level,
        "application_operation_finished terminal_kind=result run_id=%s "
        "orch_status=%s handler_status=%s context_status=%s code=%s "
        "detail_code=%s state_version=%s load_duration_ms=%s "
        "handler_duration_ms=%s commit_duration_ms=%s commit_attempts=%s "
        "commit_error_codes=%r delivery_cancelled=%s",
        str(run_id),
        orch_status,
        handler_status,
        context_status,
        code,
        detail_code,
        state_version,
        load_duration_ms,
        handler_duration_ms,
        commit_duration_ms,
        commit_attempts,
        commit_error_codes,
        delivery_cancelled,
    )


def log_operation_cancelled(
    *,
    run_id: UUID,
    cancelled_stage: str,
    load_duration_ms: float | None,
    handler_duration_ms: float | None,
) -> None:
    """Record cancellation before commit without inventing result fields."""
    LOGGER.info(
        "application_operation_finished terminal_kind=cancelled run_id=%s "
        "cancelled_stage=%s load_duration_ms=%s handler_duration_ms=%s "
        "commit_attempts=0",
        str(run_id),
        cancelled_stage,
        load_duration_ms,
        handler_duration_ms,
    )
