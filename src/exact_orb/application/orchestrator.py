"""Application entry and unknown-command failure (implementation step 3.2).

Only the unknown-command branch has a complete result and lifecycle log.
Registered commands stop explicitly until load, handler execution and commit
are implemented in steps 4–6. This partial coordinator is not transport-ready.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime

from exact_orb.application.application_results import (
    ApplicationInternalFailure,
    ApplicationResult,
)
from exact_orb.application.commands import Command
from exact_orb.application.failure_policy import describe_failure
from exact_orb.application.operation_logging import (
    log_operation_finished,
    log_operation_started,
)
from exact_orb.application.ports import Handler
from exact_orb.run_context import RunContext
from exact_orb.session.context import ContextService


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
        """Reject an unregistered command before accessing session state."""
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

        # Step 4.2 continues here with load; handler and commit follow in 5–6.
        raise NotImplementedError(
            "Registered command execution will be implemented in steps 4–6"
        )
