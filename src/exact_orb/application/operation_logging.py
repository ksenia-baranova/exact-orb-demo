"""Compact JSON lifecycle records for ApplicationOrchestrator (R3.2 §11.5).

The caller owns timing, attempt history and ordering. Invalid event arguments
are rejected before emitting a record; a logging contract error is not a
persistence outcome and must never reclassify a confirmed commit.
"""

from __future__ import annotations

import json
import logging
import math
from typing import Literal
from uuid import UUID

from exact_orb.application.application_results import ApplicationResult


LOGGER = logging.getLogger(__name__)


class LifecycleEventError(ValueError):
    """Supplied metadata cannot form a valid lifecycle record."""


def _duration(value: float | None, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if type(value) not in (int, float):
        raise LifecycleEventError("duration must be a finite nonnegative number")
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise LifecycleEventError("duration must be a finite nonnegative number")


def _version(value: int | None, *, minimum: int = 0, required: bool = False) -> None:
    if value is None and not required:
        return
    if type(value) is not int or value < minimum:
        raise LifecycleEventError("state_version must be an integer within the outcome bound")


def _emit(level: int, event: str, fields: dict[str, object]) -> None:
    # Explicit field projection only: never dump a result or its domain payload.
    message = json.dumps(fields, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    LOGGER.log(level, "%s %s", event, message)


def log_operation_started(*, run_id: UUID, command_type: str) -> None:
    """Record the start of an operation with its existing correlation ID."""
    _emit(logging.INFO, "application_operation_started", {
        "run_id": str(run_id), "command_type": command_type,
    })


def log_stage_finished(
    *,
    run_id: UUID,
    stage: str,
    outcome: str,
    duration_ms: float,
    state_version: int | None = None,
) -> None:
    """Record a completed load or handler stage, including a known version."""
    _duration(duration_ms)
    _version(state_version)
    level = logging.WARNING if outcome in ("invalid_outcome", "unexpected_failure") else logging.DEBUG
    fields: dict[str, object] = {
        "run_id": str(run_id), "stage": stage, "outcome": outcome, "duration_ms": duration_ms,
    }
    if state_version is not None:
        fields["state_version"] = state_version
    _emit(level, "application_stage_finished", fields)


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
    _duration(duration_ms)
    if type(attempt) is not int or attempt not in (1, 2):
        raise LifecycleEventError("attempt must be 1 or 2")
    if outcome in ("committed", "already_applied", "superseded"):
        _version(state_version, minimum=1 if outcome == "committed" else 0, required=True)
    elif state_version is not None:
        raise LifecycleEventError("this commit outcome has no confirmed state_version")
    level = logging.WARNING if attempt == 2 or outcome in (
        "state_commit_failed", "unexpected_failure",
    ) else logging.DEBUG
    fields: dict[str, object] = {
        "run_id": str(run_id), "attempt": attempt, "outcome": outcome,
        "detail_code": detail_code, "duration_ms": duration_ms,
    }
    if state_version is not None:
        fields["state_version"] = state_version
    _emit(level, "application_commit_attempt_finished", fields)


def log_operation_finished(
    *,
    result: ApplicationResult,
    load_duration_ms: float | None,
    handler_duration_ms: float | None,
    commit_duration_ms: float | None,
    commit_attempts: Literal[0, 1, 2],
    commit_error_codes: tuple[str, ...],
    delivery_cancelled: bool,
) -> None:
    """Project the actual result into its terminal record, without its payload."""
    if not isinstance(result, ApplicationResult):
        raise LifecycleEventError("result must be an ApplicationResult")
    for duration in (load_duration_ms, handler_duration_ms, commit_duration_ms):
        _duration(duration, optional=True)
    if type(commit_attempts) is not int or commit_attempts not in (0, 1, 2):
        raise LifecycleEventError("commit_attempts must be 0, 1 or 2")
    if not isinstance(commit_error_codes, tuple) or any(
        not isinstance(code, str) for code in commit_error_codes
    ):
        raise LifecycleEventError("commit_error_codes must be a tuple of strings")
    if type(delivery_cancelled) is not bool:
        raise LifecycleEventError("delivery_cancelled must be boolean")
    level = logging.WARNING if result.orch_status == "FAILURE" else logging.INFO
    _emit(level, "application_operation_finished", {
        "terminal_kind": "result", "run_id": str(result.run_id),
        "orch_status": result.orch_status, "handler_status": result.handler_status,
        "context_status": result.context_status, "code": result.code,
        "detail_code": result.detail_code, "state_version": result.state_version,
        "load_duration_ms": load_duration_ms, "handler_duration_ms": handler_duration_ms,
        "commit_duration_ms": commit_duration_ms, "commit_attempts": commit_attempts,
        "commit_error_codes": commit_error_codes, "delivery_cancelled": delivery_cancelled,
    })


def log_operation_cancelled(
    *,
    run_id: UUID,
    cancelled_stage: str,
    load_duration_ms: float | None,
    handler_duration_ms: float | None,
) -> None:
    """Record cancellation before commit without inventing result fields."""
    _duration(load_duration_ms, optional=True)
    _duration(handler_duration_ms, optional=True)
    _emit(logging.INFO, "application_operation_finished", {
        "terminal_kind": "cancelled", "run_id": str(run_id),
        "cancelled_stage": cancelled_stage, "load_duration_ms": load_duration_ms,
        "handler_duration_ms": handler_duration_ms, "commit_attempts": 0,
    })
