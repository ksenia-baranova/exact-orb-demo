"""Application entry, routing, load and one protected commit attempt.

Unknown commands, load refusals and non-success Handler outcomes have results
and lifecycle logs. A retry after a failed commit is a later step.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import get_args

from exact_orb.application.application_results import (
    ApplicationAlreadyApplied,
    ApplicationCalculationFailure,
    ApplicationCommitted,
    ApplicationInputRequired,
    ApplicationInternalFailure,
    ApplicationResult,
    ApplicationResolutionFailure,
    ApplicationSessionAbsent,
    ApplicationStateCommitFailure,
    ApplicationStateReadFailure,
    ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand, Command
from exact_orb.application.failure_policy import describe_failure
from exact_orb.application.operation_logging import (
    log_commit_attempt_finished,
    log_operation_cancelled,
    log_operation_finished,
    log_operation_started,
    log_stage_finished,
)
from exact_orb.application.ports import Handler
from exact_orb.application.results import BuildNatalSuccess
from exact_orb.component_logging import log_component_message
from exact_orb.calculation.errors import (
    CalculationUnavailableErrorCode,
    ChartCalculationErrorCode,
)
from exact_orb.outcomes import CalculationFailed, InputRequired, ResolutionUnavailable
from exact_orb.run_context import RunContext
from exact_orb.session.context import ContextService
from exact_orb.session.outcomes import (
    AlreadyApplied,
    Committed,
    SessionAbsent,
    StateCommitFailed,
    StateReadFailed,
    Superseded,
)
from exact_orb.session.persistence import SessionSnapshot


_logger = logging.getLogger(__name__)
_KNOWN_CALCULATION_CODES = frozenset(
    get_args(ChartCalculationErrorCode) + get_args(CalculationUnavailableErrorCode)
)


def _commit_internal_failure(run: RunContext) -> ApplicationInternalFailure:
    """Return the safe application result for an internal commit-stage error."""
    reaction = describe_failure(kind="internal_failure")
    return ApplicationInternalFailure(
        handler_status="SUCCESS",
        context_status="COMMIT_FAILED",
        code=reaction.code,
        detail_code=reaction.detail_code,
        user_message=reaction.user_message,
        retryable=reaction.retryable,
        run_id=run.run_id,
        state_version=None,
    )


def _require_utc_clock(value: object) -> datetime:
    """Reject an invalid injected retry clock at its only point of use."""
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != timedelta(0)
    ):
        raise ValueError("clock must return a timezone-aware UTC datetime")
    return value


def _log_message(
    *, run: RunContext, direction: str, peer: str, operation: str,
    message_type: str = "-", attempt: int | None = None,
) -> None:
    """Expose only direct Orchestrator calls and returned message types at INFO."""
    _logger.info(
        "application_message direction=%s run_id=%s peer=%s operation=%s "
        "message_type=%s attempt=%s",
        direction, run.run_id, peer, operation, message_type,
        "-" if attempt is None else attempt,
    )


class ApplicationOrchestrator:
    """Keep startup dependencies and route commands by their exact type."""

    def __init__(
        self,
        *,
        context: ContextService,
        handlers: Mapping[type[Command], Handler],
        clock: Callable[[], datetime],
    ) -> None:
        self._context = context
        self._handlers = dict(handlers)
        self._clock = clock

    async def execute(
        self,
        command: Command,
        *,
        session_id: str,
        run: RunContext,
    ) -> ApplicationResult:
        """Route, load and classify Handler and first commit outcomes."""
        log_operation_started(
            run_id=run.run_id,
            command_type=type(command).__name__,
        )
        log_component_message(
            _logger,
            direction="in",
            operation="application_execute",
            run_id=run.run_id,
            message_type="ApplicationExecuteRequest",
            message={
                "command_type": type(command).__name__,
                "command": command,
                "session_id": session_id,
                "run": run,
            },
        )
        handler = self._handlers.get(type(command))
        if handler is None:
            reaction = describe_failure(kind="handler_not_registered")
            result = ApplicationInternalFailure(
                orch_status="FAILURE",
                handler_status="NOT_STARTED",
                context_status="NOT_ACCESSED",
                code=reaction.code,
                detail_code=reaction.detail_code,
                user_message=reaction.user_message,
                retryable=reaction.retryable,
                run_id=run.run_id,
                state_version=None,
            )
            log_operation_finished(
                result=result,
                load_duration_ms=None,
                handler_duration_ms=None,
                commit_duration_ms=None,
                commit_attempts=0,
                commit_error_codes=(),
                delivery_cancelled=False,
            )
            return result

        load_started = time.perf_counter()
        _log_message(
            run=run, direction="send", peer=type(self._context).__name__,
            operation="load", message_type="ContextLoadRequest",
        )
        try:
            loaded = await self._context.load(session_id)
        except asyncio.CancelledError:
            log_operation_cancelled(
                run_id=run.run_id,
                cancelled_stage="load",
                load_duration_ms=None,
                handler_duration_ms=None,
            )
            raise
        except Exception:
            load_duration_ms = (time.perf_counter() - load_started) * 1000
            _logger.exception("Session load failed run_id=%s", run.run_id)
            outcome = "unexpected_failure"
        else:
            load_duration_ms = (time.perf_counter() - load_started) * 1000
            _log_message(
                run=run, direction="receive", peer=type(self._context).__name__,
                operation="load", message_type=type(loaded).__name__,
            )
            if isinstance(loaded, SessionSnapshot):
                snapshot = loaded
                original_expected_state_version = snapshot.state.state_version
                outcome = "loaded"
            elif isinstance(loaded, SessionAbsent):
                outcome = "session_absent"
            elif isinstance(loaded, StateReadFailed):
                outcome = "state_read_failed"
            else:
                try:
                    raise TypeError("ContextService.load returned an unsupported outcome")
                except TypeError:
                    _logger.exception(
                        "Invalid session load outcome run_id=%s", run.run_id
                    )
                outcome = "invalid_outcome"

        log_stage_finished(
            run_id=run.run_id,
            stage="load",
            outcome=outcome,
            duration_ms=load_duration_ms,
            state_version=original_expected_state_version if outcome == "loaded" else None,
        )

        if outcome == "loaded":
            handler_started = time.perf_counter()
            _log_message(
                run=run, direction="send", peer=type(handler).__name__,
                operation="handle", message_type=(
                    "BuildNatalRequest" if type(command) is BuildNatalCommand
                    else type(command).__name__
                ),
            )
            try:
                handled = await handler.handle(command, snapshot.state, run)
            except asyncio.CancelledError:
                log_operation_cancelled(
                    run_id=run.run_id,
                    cancelled_stage="handler",
                    load_duration_ms=load_duration_ms,
                    handler_duration_ms=None,
                )
                raise
            except Exception:
                handler_duration_ms = (time.perf_counter() - handler_started) * 1000
                _logger.exception("Handler failed run_id=%s", run.run_id)
                handler_outcome = "unexpected_failure"
                reaction = describe_failure(kind="internal_failure")
                result = ApplicationInternalFailure(
                    orch_status="FAILURE",
                    handler_status="UNEXPECTED_FAILURE",
                    context_status="LOADED",
                    code=reaction.code,
                    detail_code=reaction.detail_code,
                    user_message=reaction.user_message,
                    retryable=reaction.retryable,
                    run_id=run.run_id,
                    state_version=original_expected_state_version,
                )
            else:
                handler_duration_ms = (time.perf_counter() - handler_started) * 1000
                _log_message(
                    run=run, direction="receive", peer=type(handler).__name__,
                    operation="handle", message_type=type(handled).__name__,
                )
                if isinstance(handled, InputRequired):
                    handler_outcome = "input_required"
                    reaction = describe_failure(kind="input_required")
                    result = ApplicationInputRequired(
                        orch_status="INPUT_REQUIRED",
                        handler_status="INPUT_REQUIRED",
                        context_status="LOADED",
                        code=reaction.code,
                        detail_code=reaction.detail_code,
                        user_message=reaction.user_message,
                        retryable=reaction.retryable,
                        run_id=run.run_id,
                        state_version=original_expected_state_version,
                        issues=handled.issues,
                    )
                elif isinstance(handled, ResolutionUnavailable):
                    handler_outcome = "resolution_unavailable"
                    reaction = describe_failure(
                        kind="resolution_unavailable",
                        error_code=handled.error_code,
                        retryable=handled.retryable,
                    )
                    result = ApplicationResolutionFailure(
                        orch_status="FAILURE",
                        handler_status="RESOLUTION_UNAVAILABLE",
                        context_status="LOADED",
                        code=reaction.code,
                        detail_code=reaction.detail_code,
                        user_message=reaction.user_message,
                        retryable=reaction.retryable,
                        run_id=run.run_id,
                        state_version=original_expected_state_version,
                    )
                elif isinstance(handled, CalculationFailed):
                    handler_outcome = "calculation_failed"
                    reaction = describe_failure(
                        kind="calculation_failed", error_code=handled.error_code,
                    )
                    if handled.error_code not in _KNOWN_CALCULATION_CODES:
                        _logger.warning(
                            "Unknown calculation failure code=%r run_id=%s",
                            handled.error_code, run.run_id,
                        )
                    result = ApplicationCalculationFailure(
                        orch_status="FAILURE",
                        handler_status="CALCULATION_FAILED",
                        context_status="LOADED",
                        code=reaction.code,
                        detail_code=reaction.detail_code,
                        user_message=reaction.user_message,
                        retryable=reaction.retryable,
                        run_id=run.run_id,
                        state_version=original_expected_state_version,
                    )
                elif isinstance(handled, BuildNatalSuccess):
                    log_stage_finished(
                        run_id=run.run_id,
                        stage="handler",
                        outcome="success",
                        duration_ms=handler_duration_ms,
                        state_version=original_expected_state_version,
                    )
                    cancelled_error: asyncio.CancelledError | None = None
                    commit_durations: list[float] = []
                    commit_error_codes: list[str] = []
                    for attempt in (1, 2):
                        commit_started = time.perf_counter()
                        save_error: Exception | None = None
                        try:
                            commit_task = asyncio.create_task(self._context.save(
                                session_id, original_expected_state_version, handled.delta,
                            ))
                        except Exception as exc:
                            save_error = exc
                        else:
                            _log_message(
                                run=run, direction="send", peer=type(self._context).__name__,
                                operation="save", message_type="ContextSaveRequest",
                                attempt=attempt,
                            )
                            while True:
                                try:
                                    saved = await asyncio.shield(commit_task)
                                except asyncio.CancelledError as exc:
                                    if cancelled_error is None:
                                        cancelled_error = exc
                                    # Keep the task referenced and wait through cancellation;
                                    # another cancel request must not detach a running save.
                                    if commit_task.done():
                                        try:
                                            saved = commit_task.result()
                                        except Exception as inner_exc:
                                            save_error = inner_exc
                                        break
                                except Exception as exc:
                                    save_error = exc
                                    break
                                else:
                                    break
                        commit_duration_ms = (time.perf_counter() - commit_started) * 1000
                        commit_durations.append(commit_duration_ms)
                        if save_error is None:
                            _log_message(
                                run=run, direction="receive", peer=type(self._context).__name__,
                                operation="save", message_type=type(saved).__name__,
                                attempt=attempt,
                            )
                            if isinstance(saved, Committed):
                                result = ApplicationCommitted(
                                    run_id=run.run_id,
                                    state_version=saved.state_version,
                                    artifact=handled.artifact,
                                )
                                attempt_outcome = "committed"
                                attempt_version = saved.state_version
                            elif isinstance(saved, AlreadyApplied):
                                result = ApplicationAlreadyApplied(
                                    run_id=run.run_id,
                                    state_version=saved.state_version,
                                    artifact=handled.artifact,
                                )
                                attempt_outcome = "already_applied"
                                attempt_version = saved.state_version
                            elif isinstance(saved, Superseded):
                                reaction = describe_failure(kind="superseded")
                                result = ApplicationSuperseded(
                                    code=reaction.code,
                                    detail_code=reaction.detail_code,
                                    user_message=reaction.user_message,
                                    retryable=reaction.retryable,
                                    run_id=run.run_id,
                                    state_version=saved.actual.state_version,
                                )
                                attempt_outcome = "superseded"
                                attempt_version = saved.actual.state_version
                            elif isinstance(saved, SessionAbsent):
                                reaction = describe_failure(
                                    kind="session_absent", stage="commit", reason=saved.reason,
                                )
                                result = ApplicationSessionAbsent(
                                    handler_status="SUCCESS",
                                    code=reaction.code,
                                    detail_code=reaction.detail_code,
                                    user_message=reaction.user_message,
                                    retryable=reaction.retryable,
                                    run_id=run.run_id,
                                    state_version=None,
                                    reason=saved.reason,
                                )
                                attempt_outcome = "session_absent"
                                attempt_version = None
                            elif isinstance(saved, StateCommitFailed):
                                reaction = describe_failure(
                                    kind="state_commit_failed", error_code=saved.error_code,
                                )
                                result = ApplicationStateCommitFailure(
                                    code=reaction.code,
                                    detail_code=reaction.detail_code,
                                    user_message=reaction.user_message,
                                    retryable=reaction.retryable,
                                    run_id=run.run_id,
                                    state_version=None,
                                )
                                attempt_outcome = "state_commit_failed"
                                attempt_version = None
                            else:
                                try:
                                    raise TypeError(
                                        "ContextService.save returned an unsupported outcome"
                                    )
                                except TypeError as exc:
                                    save_error = exc
                        if save_error is not None:
                            _logger.error(
                                "Commit save failed run_id=%s", run.run_id,
                                exc_info=(type(save_error), save_error, save_error.__traceback__),
                            )
                            result = _commit_internal_failure(run)
                            attempt_outcome = "unexpected_failure"
                            attempt_version = None
                        detail_code = (
                            saved.error_code if save_error is None
                            and isinstance(saved, StateCommitFailed) else None
                        )
                        if detail_code is not None:
                            commit_error_codes.append(detail_code)
                        log_commit_attempt_finished(
                            run_id=run.run_id,
                            attempt=attempt,
                            outcome=attempt_outcome,
                            detail_code=detail_code,
                            duration_ms=commit_duration_ms,
                            state_version=attempt_version,
                        )
                        should_retry = (
                            attempt == 1
                            and detail_code is not None
                            and cancelled_error is None
                        )
                        if should_retry and run.deadline is not None:
                            try:
                                should_retry = run.deadline > _require_utc_clock(self._clock())
                            except Exception:
                                _logger.exception(
                                    "Commit retry decision failed run_id=%s", run.run_id
                                )
                                result = _commit_internal_failure(run)
                                should_retry = False
                        if should_retry:
                            continue
                        break
                    log_operation_finished(
                        result=result,
                        load_duration_ms=load_duration_ms,
                        handler_duration_ms=handler_duration_ms,
                        commit_duration_ms=sum(commit_durations),
                        commit_attempts=len(commit_durations),
                        commit_error_codes=tuple(commit_error_codes),
                        delivery_cancelled=cancelled_error is not None,
                    )
                    if cancelled_error is not None:
                        raise cancelled_error
                    return result
                else:
                    _logger.error("Invalid Handler outcome run_id=%s", run.run_id, stack_info=True)
                    handler_outcome = "invalid_outcome"
                    reaction = describe_failure(kind="internal_failure")
                    result = ApplicationInternalFailure(
                        orch_status="FAILURE",
                        handler_status="UNEXPECTED_FAILURE",
                        context_status="LOADED",
                        code=reaction.code,
                        detail_code=reaction.detail_code,
                        user_message=reaction.user_message,
                        retryable=reaction.retryable,
                        run_id=run.run_id,
                        state_version=original_expected_state_version,
                    )

            log_stage_finished(
                run_id=run.run_id,
                stage="handler",
                outcome=handler_outcome,
                duration_ms=handler_duration_ms,
                state_version=original_expected_state_version,
            )
            log_operation_finished(
                result=result,
                load_duration_ms=load_duration_ms,
                handler_duration_ms=handler_duration_ms,
                commit_duration_ms=None,
                commit_attempts=0,
                commit_error_codes=(),
                delivery_cancelled=False,
            )
            return result
        if outcome == "session_absent":
            reaction = describe_failure(
                kind="session_absent", stage="load", reason=loaded.reason
            )
            result = ApplicationSessionAbsent(
                orch_status="SESSION_ABSENT",
                handler_status="NOT_STARTED",
                context_status="SESSION_ABSENT",
                code=reaction.code,
                detail_code=reaction.detail_code,
                user_message=reaction.user_message,
                retryable=reaction.retryable,
                run_id=run.run_id,
                state_version=None,
                reason=loaded.reason,
            )
        elif outcome == "state_read_failed":
            reaction = describe_failure(
                kind="state_read_failed", error_code=loaded.error_code
            )
            result = ApplicationStateReadFailure(
                orch_status="FAILURE",
                handler_status="NOT_STARTED",
                context_status="READ_FAILED",
                code=reaction.code,
                detail_code=reaction.detail_code,
                user_message=reaction.user_message,
                retryable=reaction.retryable,
                run_id=run.run_id,
                state_version=None,
            )
        else:
            reaction = describe_failure(kind="internal_failure")
            result = ApplicationInternalFailure(
                orch_status="FAILURE",
                handler_status="NOT_STARTED",
                context_status="NOT_ACCESSED",
                code=reaction.code,
                detail_code=reaction.detail_code,
                user_message=reaction.user_message,
                retryable=reaction.retryable,
                run_id=run.run_id,
                state_version=None,
            )

        log_operation_finished(
            result=result,
            load_duration_ms=load_duration_ms,
            handler_duration_ms=None,
            commit_duration_ms=None,
            commit_attempts=0,
            commit_error_codes=(),
            delivery_cancelled=False,
        )
        return result
