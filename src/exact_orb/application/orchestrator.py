"""Application entry, routing and session load (implementation step 4.2).

Unknown commands and load refusals have results and lifecycle logs. A loaded
snapshot stops before handler execution and commit in later steps. This partial
coordinator is not transport-ready.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from datetime import datetime

from exact_orb.application.application_results import (
    ApplicationInternalFailure,
    ApplicationResult,
    ApplicationSessionAbsent,
    ApplicationStateReadFailure,
)
from exact_orb.application.commands import Command
from exact_orb.application.failure_policy import describe_failure
from exact_orb.application.operation_logging import (
    log_operation_finished,
    log_operation_started,
    log_stage_finished,
)
from exact_orb.application.ports import Handler
from exact_orb.run_context import RunContext
from exact_orb.session.context import ContextService
from exact_orb.session.outcomes import SessionAbsent, StateReadFailed
from exact_orb.session.persistence import SessionSnapshot


_logger = logging.getLogger(__name__)


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
        """Route first, then finish load refusals before the unfinished handler."""
        log_operation_started(
            run_id=run.run_id,
            command_type=type(command).__name__,
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
        try:
            loaded = await self._context.load(session_id)
        except Exception:
            load_duration_ms = (time.perf_counter() - load_started) * 1000
            _logger.exception("Session load failed run_id=%s", run.run_id)
            outcome = "unexpected_failure"
        else:
            load_duration_ms = (time.perf_counter() - load_started) * 1000
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
            # The snapshot and original version remain local for steps 5–6.
            raise NotImplementedError(
                "Handler execution and commit will be implemented in steps 5–6"
            )
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
