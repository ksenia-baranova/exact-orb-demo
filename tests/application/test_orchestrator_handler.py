"""Handler input, typed outcomes, failures and cancellation: plan group 5.

The registered path reaches Handler; success reaches commit after group 6.
Empty InputRequired remains K3.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
from collections.abc import Iterator
from contextlib import suppress

import pytest

from exact_orb.application.application_results import (
    ApplicationCalculationFailure,
    ApplicationInputRequired,
    ApplicationInternalFailure,
    ApplicationResolutionFailure,
    ApplicationResult,
)
from exact_orb.application.commands import Command
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.results import BuildNatalOutcome
from exact_orb.outcomes import CalculationFailed, InputRequired, Issue, ResolutionUnavailable
from exact_orb.run_context import RunContext
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.outcomes import StateCommitFailed
from exact_orb.session.state import SessionState, new_session
from tests.application.orchestrator_fakes import Call, RecordingContext, RecordingHandler
from tests.fixtures.telemetry import FORBIDDEN_PAYLOAD, RUN_ID_B, STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit
SESSION_ID = "handler-session"
START = "application_operation_started"
STAGE = "application_stage_finished"
FINISH = "application_operation_finished"
ATTEMPT = "application_commit_attempt_finished"
EVENTS = {START, STAGE, FINISH, ATTEMPT}


class HandlerCommand(Command):
    """A registered command with payload that must stay out of compact events."""

    private_note: str


@pytest.fixture
def journal() -> list[Call]:
    return []


@pytest.fixture
def command() -> HandlerCommand:
    return HandlerCommand(private_note=FORBIDDEN_PAYLOAD)


@pytest.fixture
def run() -> RunContext:
    return RunContext(run_id=RUN_ID_B, started_at=STARTED_AT)


@pytest.fixture(autouse=True)
def application_records(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture real application records and restore the logger after each case."""
    logger = logging.getLogger("exact_orb.application")
    handlers = logger.handlers[:]
    propagate, level, disabled = logger.propagate, logger.level, logger.disabled
    try:
        caplog.set_level(logging.DEBUG, logger=logger.name)
        logger.handlers = [caplog.handler]
        logger.propagate = False
        logger.disabled = False
        yield caplog
    finally:
        logger.handlers = handlers
        logger.propagate = propagate
        logger.setLevel(level)
        logger.disabled = disabled


def _snapshot(version: int) -> SessionSnapshot:
    state = SessionState.model_validate({
        **new_session(SESSION_ID, now=STARTED_AT).model_dump(),
        "state_version": version,
    })
    return SessionSnapshot(state=state, dialog=())


def _setup(
    journal: list[Call], command: HandlerCommand, outcome: BuildNatalOutcome,
    *, version: int,
) -> tuple[ApplicationOrchestrator, RecordingContext, RecordingHandler, SessionSnapshot]:
    snapshot = _snapshot(version)
    context = RecordingContext(journal, load_result=snapshot)
    handler = RecordingHandler(journal, result=outcome)
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={HandlerCommand: handler}, clock=lambda: STARTED_AT,
    )
    return orchestrator, context, handler, snapshot


def _fields(record: logging.LogRecord) -> dict[str, object]:
    message = record.getMessage()
    assert len(message.splitlines()) == 1
    fields = json.loads(message.partition(" ")[2])
    assert isinstance(fields, dict)
    return fields


def _assert_stage(
    record: logging.LogRecord, run: RunContext, *, stage: str,
    outcome: str, version: int,
) -> float:
    fields = _fields(record)
    duration = fields["duration_ms"]
    assert type(duration) in (int, float)
    assert math.isfinite(duration) and duration >= 0
    expected = {
        "run_id": str(run.run_id), "stage": stage,
        "outcome": outcome, "duration_ms": duration,
    }
    if stage == "load" or "state_version" in fields:
        expected["state_version"] = version
    assert fields == expected
    assert record.levelno == logging.DEBUG
    return duration


def _assert_non_success(
    journal: list[Call], context: RecordingContext, handler: RecordingHandler,
    command: HandlerCommand, snapshot: SessionSnapshot, run: RunContext,
    result: ApplicationResult, records: pytest.LogCaptureFixture, *, outcome: str,
) -> None:
    """Observe the real call sequence and the exact four lifecycle events."""
    assert journal == [
        Call(context, "load", (SESSION_ID,)),
        Call(handler, "handle", (command, snapshot.state, run)),
    ]
    handled = journal[1]
    assert handled.args[0] is command
    assert handled.args[1] is snapshot.state
    assert handled.args[2] is run
    assert result.run_id == run.run_id
    assert result.state_version == snapshot.state.state_version

    lifecycle = [
        record for record in records.records
        if record.getMessage().partition(" ")[0] in EVENTS
    ]
    assert [record.getMessage().partition(" ")[0] for record in lifecycle] == [
        START, STAGE, STAGE, FINISH,
    ]
    assert lifecycle[0].levelno == logging.INFO
    assert _fields(lifecycle[0]) == {
        "run_id": str(run.run_id), "command_type": "HandlerCommand",
    }
    load_duration = _assert_stage(
        lifecycle[1], run, stage="load", outcome="loaded",
        version=snapshot.state.state_version,
    )
    handler_duration = _assert_stage(
        lifecycle[2], run, stage="handler", outcome=outcome,
        version=snapshot.state.state_version,
    )
    assert lifecycle[3].levelno == (
        logging.INFO if result.orch_status == "INPUT_REQUIRED" else logging.WARNING
    )
    assert _fields(lifecycle[3]) == {
        "terminal_kind": "result", "run_id": str(run.run_id),
        "orch_status": result.orch_status,
        "handler_status": result.handler_status,
        "context_status": result.context_status,
        "code": result.code,
        "detail_code": result.detail_code,
        "state_version": snapshot.state.state_version,
        "load_duration_ms": load_duration,
        "handler_duration_ms": handler_duration,
        "commit_duration_ms": None,
        "commit_attempts": 0,
        "commit_error_codes": [],
        "delivery_cancelled": False,
    }
    for record in lifecycle:
        message = record.getMessage()
        assert SESSION_ID not in message
        assert FORBIDDEN_PAYLOAD not in message
        assert _fields(record)["run_id"] == str(run.run_id)
        assert "issues" not in _fields(record)
        assert "artifact" not in _fields(record)


@pytest.mark.parametrize("version", [0, 7])
async def test_input_required_preserves_handler_identity_issues_and_events(
    version: int, journal: list[Call], command: HandlerCommand, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """FR-02/05–08/26; AC-2/5/7/8/26/29/30/33, nonempty part of K3."""
    issues = (
        Issue(field="birth.place", code="INVALID"),
        Issue(field="birth.time", code="AMBIGUOUS", candidates=(14400, 10800)),
    )
    orchestrator, context, handler, snapshot = _setup(
        journal, command, InputRequired(issues=issues), version=version,
    )

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationInputRequired)
    assert result.model_dump(exclude={"issues"}) == {
        "orch_status": "INPUT_REQUIRED", "handler_status": "INPUT_REQUIRED",
        "context_status": "LOADED", "code": "INPUT_REQUIRED", "detail_code": None,
        "user_message": "Проверьте введённые данные и исправьте отмеченные поля.",
        "retryable": False, "run_id": run.run_id, "state_version": version,
    }
    assert result.issues == issues
    assert [issue.field for issue in result.issues] == ["birth.place", "birth.time"]
    _assert_non_success(
        journal, context, handler, command, snapshot, run, result,
        application_records, outcome="input_required",
    )


@pytest.mark.parametrize(("retryable", "error_code", "message"), [
    (True, "RESOLVER_TIMEOUT", "Не удалось определить данные места и времени. Попробуйте ещё раз."),
    (False, "RESOLVER_UNSUPPORTED", "Не удалось определить данные места и времени для указанного ввода."),
], ids=["retryable", "non_retryable"])
async def test_resolution_failure_keeps_handler_retryability_without_save(
    retryable: bool, error_code: str, message: str, journal: list[Call],
    command: HandlerCommand, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """FR-10/25–26; AC-8/21/26/27/29/30/33, both retry decisions."""
    orchestrator, context, handler, snapshot = _setup(
        journal, command,
        ResolutionUnavailable(error_code=error_code, retryable=retryable),
        version=7,
    )

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationResolutionFailure)
    assert result.model_dump() == {
        "orch_status": "FAILURE", "handler_status": "RESOLUTION_UNAVAILABLE",
        "context_status": "LOADED", "code": "RESOLUTION_UNAVAILABLE",
        "detail_code": error_code, "user_message": message,
        "retryable": retryable, "run_id": run.run_id, "state_version": 7,
    }
    _assert_non_success(
        journal, context, handler, command, snapshot, run, result,
        application_records, outcome="resolution_unavailable",
    )


@pytest.mark.parametrize(("error_code", "retryable", "message"), [
    ("EPHEMERIS_UNAVAILABLE", True, "Расчёт временно недоступен. Попробуйте ещё раз."),
    ("HOUSES_DEGENERATE", False, "Для выбранных данных невозможно рассчитать дома в текущей системе домов."),
    ("SPEC_INVALID", False, "Не удалось подготовить параметры расчёта карты."),
    ("GEOGRAPHY_INVALID", False, "Не удалось выполнить расчёт карты для выбранного места."),
    ("ENGINE_UNEXPECTED", False, "Не удалось рассчитать карту из-за внутренней ошибки."),
], ids=[
    "EPHEMERIS_UNAVAILABLE", "HOUSES_DEGENERATE", "SPEC_INVALID",
    "GEOGRAPHY_INVALID", "ENGINE_UNEXPECTED",
])
async def test_known_calculation_failure_uses_exact_policy_without_save(
    error_code: str, retryable: bool, message: str, journal: list[Call],
    command: HandlerCommand, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """FR-10/25–26; AC-8/21/25–27/29/30/33, known-code mapper."""
    orchestrator, context, handler, snapshot = _setup(
        journal, command, CalculationFailed(error_code=error_code), version=7,
    )

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationCalculationFailure)
    assert result.model_dump() == {
        "orch_status": "FAILURE", "handler_status": "CALCULATION_FAILED",
        "context_status": "LOADED", "code": "CALCULATION_FAILED",
        "detail_code": error_code, "user_message": message,
        "retryable": retryable, "run_id": run.run_id, "state_version": 7,
    }
    _assert_non_success(
        journal, context, handler, command, snapshot, run, result,
        application_records, outcome="calculation_failed",
    )
    assert not [
        record for record in application_records.records
        if record.levelno == logging.WARNING
        and record.getMessage().partition(" ")[0] not in EVENTS
    ]


async def test_unknown_calculation_code_uses_fallback_and_diagnostic_warn(
    journal: list[Call], command: HandlerCommand, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """FR-10/25–26; AC-8/21/25–27/29/30/33, open code and separate WARN."""
    error_code = "SYNTHETIC_UNKNOWN_CALCULATION_CODE"
    orchestrator, context, handler, snapshot = _setup(
        journal, command, CalculationFailed(error_code=error_code), version=7,
    )

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationCalculationFailure)
    assert result.model_dump() == {
        "orch_status": "FAILURE", "handler_status": "CALCULATION_FAILED",
        "context_status": "LOADED", "code": "CALCULATION_FAILED",
        "detail_code": error_code, "user_message": "Не удалось рассчитать карту.",
        "retryable": False, "run_id": run.run_id, "state_version": 7,
    }
    _assert_non_success(
        journal, context, handler, command, snapshot, run, result,
        application_records, outcome="calculation_failed",
    )
    diagnostics = [
        record for record in application_records.records
        if record.levelno == logging.WARNING
        and record.getMessage().partition(" ")[0] not in EVENTS
    ]
    assert len(diagnostics) == 1
    assert error_code in diagnostics[0].getMessage()
    assert str(run.run_id) in diagnostics[0].getMessage()
    assert FORBIDDEN_PAYLOAD not in diagnostics[0].getMessage()
    assert SESSION_ID not in diagnostics[0].getMessage()


def _lifecycle(records: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [
        record for record in records.records
        if record.getMessage().partition(" ")[0] in EVENTS
    ]


def _assert_internal_handler_flow(
    journal: list[Call], context: RecordingContext, handler: RecordingHandler,
    command: HandlerCommand, snapshot: SessionSnapshot, run: RunContext,
    result: ApplicationResult, records: pytest.LogCaptureFixture,
    *, outcome: str,
) -> list[logging.LogRecord]:
    """UC-12: a completed but defective Handler never reaches persistence."""
    assert journal == [
        Call(context, "load", (SESSION_ID,)),
        Call(handler, "handle", (command, snapshot.state, run)),
    ]
    assert journal[1].args[0] is command
    assert journal[1].args[1] is snapshot.state
    assert journal[1].args[2] is run
    assert isinstance(result, ApplicationInternalFailure)
    assert result.model_dump() == {
        "orch_status": "FAILURE", "handler_status": "UNEXPECTED_FAILURE",
        "context_status": "LOADED", "code": "INTERNAL_FAILURE",
        "detail_code": None, "user_message": "Произошла внутренняя ошибка.",
        "retryable": False, "run_id": run.run_id,
        "state_version": snapshot.state.state_version,
    }

    lifecycle = _lifecycle(records)
    assert [record.getMessage().partition(" ")[0] for record in lifecycle] == [
        START, STAGE, STAGE, FINISH,
    ]
    assert lifecycle[0].levelno == logging.INFO
    assert _fields(lifecycle[0]) == {
        "run_id": str(run.run_id), "command_type": "HandlerCommand",
    }
    load_duration = _assert_stage(
        lifecycle[1], run, stage="load", outcome="loaded",
        version=snapshot.state.state_version,
    )
    handler_record = lifecycle[2]
    assert handler_record.levelno == logging.WARNING
    handler_fields = _fields(handler_record)
    handler_duration = handler_fields["duration_ms"]
    assert type(handler_duration) in (int, float)
    assert math.isfinite(handler_duration) and handler_duration >= 0
    expected_handler_fields = {
        "run_id": str(run.run_id), "stage": "handler", "outcome": outcome,
        "duration_ms": handler_duration,
    }
    if "state_version" in handler_fields:
        expected_handler_fields["state_version"] = snapshot.state.state_version
    assert handler_fields == expected_handler_fields
    assert lifecycle[3].levelno == logging.WARNING
    assert _fields(lifecycle[3]) == {
        "terminal_kind": "result", "run_id": str(run.run_id),
        "orch_status": result.orch_status,
        "handler_status": result.handler_status,
        "context_status": result.context_status,
        "code": result.code, "detail_code": result.detail_code,
        "state_version": result.state_version,
        "load_duration_ms": load_duration,
        "handler_duration_ms": handler_duration,
        "commit_duration_ms": None, "commit_attempts": 0,
        "commit_error_codes": [], "delivery_cancelled": False,
    }
    for record in lifecycle:
        message = record.getMessage()
        assert SESSION_ID not in message
        assert FORBIDDEN_PAYLOAD not in message
    diagnostics = [
        record for record in records.records
        if record.name.startswith("exact_orb.application")
        and record.levelno >= logging.WARNING and record not in lifecycle
    ]
    assert len(diagnostics) == 1
    assert str(run.run_id) in diagnostics[0].getMessage()
    return diagnostics


@pytest.mark.parametrize("invalid,version", [
    pytest.param(None, 0, id="none-version-zero"),
    pytest.param(StateCommitFailed(error_code="FOREIGN_OUTCOME"), 7, id="foreign-type"),
])
async def test_invalid_handler_outcome_is_internal_failure_without_save(
    invalid: object, version: int, journal: list[Call], command: HandlerCommand,
    run: RunContext, application_records: pytest.LogCaptureFixture,
) -> None:
    """UC-12; FR-25/26; AC-9/21/26/29/30/32/33, invalid return types."""
    class InvalidHandler(RecordingHandler):
        async def handle(self, command: Command, state: SessionState, run: RunContext) -> object:
            await super().handle(command, state, run)
            return invalid

    snapshot = _snapshot(version)
    context = RecordingContext(journal, load_result=snapshot)
    handler = InvalidHandler(journal, result=InputRequired(issues=(Issue(field="date", code="MISSING"),)))
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={HandlerCommand: handler}, clock=lambda: STARTED_AT,
    )

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    _assert_internal_handler_flow(
        journal, context, handler, command, snapshot, run, result,
        application_records, outcome="invalid_outcome",
    )


async def test_handler_exception_has_real_traceback_and_safe_result(
    journal: list[Call], command: HandlerCommand, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """UC-12; FR-25/26; AC-21/26/29/30/32/33, exception boundary."""
    error = RuntimeError(f"synthetic Handler failure {FORBIDDEN_PAYLOAD} /private/chart.db")

    class RaisingHandler(RecordingHandler):
        async def handle(self, command: Command, state: SessionState, run: RunContext) -> BuildNatalOutcome:
            await super().handle(command, state, run)
            raise error

    snapshot = _snapshot(7)
    context = RecordingContext(journal, load_result=snapshot)
    handler = RaisingHandler(journal, result=InputRequired(issues=(Issue(field="date", code="MISSING"),)))
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={HandlerCommand: handler}, clock=lambda: STARTED_AT,
    )

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    diagnostics = _assert_internal_handler_flow(
        journal, context, handler, command, snapshot, run, result,
        application_records, outcome="unexpected_failure",
    )
    assert error.args[0] not in result.user_message
    assert diagnostics[0].exc_info is not None
    assert diagnostics[0].exc_info[1] is error
    assert diagnostics[0].exc_info[2] is not None


async def _await_stage_entry(task: asyncio.Task[ApplicationResult], entered: asyncio.Event) -> None:
    """Use an Event handshake; a premature execute failure keeps its cause."""
    entered_waiter = asyncio.create_task(entered.wait())
    try:
        done, _ = await asyncio.wait(
            {task, entered_waiter}, timeout=2, return_when=asyncio.FIRST_COMPLETED,
        )
        assert done, "execute did not enter the controlled stage"
        if task.done():
            await task
            pytest.fail("execute completed before entering the controlled stage")
        assert entered_waiter in done and entered_waiter.result() is True
    finally:
        if not entered_waiter.done():
            entered_waiter.cancel()
            with suppress(asyncio.CancelledError):
                await entered_waiter


def _assert_cancelled_flow(
    records: pytest.LogCaptureFixture, run: RunContext, *, stage: str,
    version: int | None,
) -> None:
    """UC-14: the terminal precedes observed cancellation; no false stage end."""
    lifecycle = _lifecycle(records)
    names = [record.getMessage().partition(" ")[0] for record in lifecycle]
    assert names == ([START, FINISH] if stage == "load" else [START, STAGE, FINISH])
    assert lifecycle[0].levelno == logging.INFO
    assert _fields(lifecycle[0]) == {
        "run_id": str(run.run_id), "command_type": "HandlerCommand",
    }
    load_duration: float | None = None
    if stage == "handler":
        assert version is not None
        load_duration = _assert_stage(
            lifecycle[1], run, stage="load", outcome="loaded", version=version,
        )
    terminal_record = lifecycle[-1]
    assert terminal_record.levelno == logging.INFO
    fields = _fields(terminal_record)
    assert fields.keys() == {
        "terminal_kind", "run_id", "cancelled_stage", "load_duration_ms",
        "handler_duration_ms", "commit_attempts",
    }
    assert fields["terminal_kind"] == "cancelled"
    assert fields["run_id"] == str(run.run_id)
    assert fields["cancelled_stage"] == stage
    assert fields["commit_attempts"] == 0
    if load_duration is not None:
        assert fields["load_duration_ms"] == load_duration
    for name in ("load_duration_ms", "handler_duration_ms"):
        duration = fields[name]
        if duration is not None:
            assert type(duration) in (int, float)
            assert math.isfinite(duration) and duration >= 0
    for record in lifecycle:
        message = record.getMessage()
        assert SESSION_ID not in message
        assert FORBIDDEN_PAYLOAD not in message


async def test_cancel_during_load_writes_one_cancelled_terminal(
    journal: list[Call], command: HandlerCommand, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """UC-14; FR-26; AC-17/26/29/30/32/33, interrupted load."""
    entered, release = asyncio.Event(), asyncio.Event()

    class BlockingContext(RecordingContext):
        async def load(self, session_id: str) -> SessionSnapshot:
            snapshot = await super().load(session_id)
            entered.set()
            await release.wait()
            return snapshot

    context = BlockingContext(journal, load_result=_snapshot(7))
    handler = RecordingHandler(
        journal, result=InputRequired(issues=(Issue(field="date", code="MISSING"),)),
    )
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={HandlerCommand: handler}, clock=lambda: STARTED_AT,
    )
    task = asyncio.create_task(orchestrator.execute(command, session_id=SESSION_ID, run=run))
    try:
        await _await_stage_entry(task, entered)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
    finally:
        release.set()
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    assert journal == [Call(context, "load", (SESSION_ID,))]
    _assert_cancelled_flow(application_records, run, stage="load", version=None)


async def test_cancel_during_handler_writes_one_cancelled_terminal(
    journal: list[Call], command: HandlerCommand, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """UC-14; FR-26; AC-17/26/29/30/32/33, interrupted Handler."""
    entered, release = asyncio.Event(), asyncio.Event()

    class BlockingHandler(RecordingHandler):
        async def handle(self, command: Command, state: SessionState, run: RunContext) -> BuildNatalOutcome:
            outcome = await super().handle(command, state, run)
            entered.set()
            await release.wait()
            return outcome

    snapshot = _snapshot(7)
    context = RecordingContext(journal, load_result=snapshot)
    handler = BlockingHandler(
        journal, result=InputRequired(issues=(Issue(field="date", code="MISSING"),)),
    )
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={HandlerCommand: handler}, clock=lambda: STARTED_AT,
    )
    task = asyncio.create_task(orchestrator.execute(command, session_id=SESSION_ID, run=run))
    try:
        await _await_stage_entry(task, entered)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
    finally:
        release.set()
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    assert journal == [
        Call(context, "load", (SESSION_ID,)),
        Call(handler, "handle", (command, snapshot.state, run)),
    ]
    assert journal[1].args[0] is command
    assert journal[1].args[1] is snapshot.state
    assert journal[1].args[2] is run
    _assert_cancelled_flow(application_records, run, stage="handler", version=7)
