"""One confirmed commit through the real ApplicationOrchestrator (step 6.1)."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import traceback
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest

from exact_orb.application.application_results import (
    ApplicationAlreadyApplied,
    ApplicationCommitted,
    ApplicationInternalFailure,
    ApplicationResult,
    ApplicationSessionAbsent,
    ApplicationStateCommitFailure,
    ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.failure_policy import describe_failure
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.results import BuildNatalSuccess
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.run_context import RunContext
from exact_orb.session.outcomes import (
    AlreadyApplied,
    Committed,
    SessionAbsent,
    StateCommitFailed,
    Superseded,
)
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import SessionState, StateDelta, new_session
from tests.application.orchestrator_fakes import (
    Call,
    RecordingContext,
    RecordingHandler,
    SaveOutcome,
)
from tests.fixtures.calculation import artifact, chart_spec, resolved_birth_data
from tests.fixtures.telemetry import RUN_ID_B, STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit
SESSION_ID = "controlled-commit-session"
LOGGER_NAME = "exact_orb.application"
EVENTS = (
    "application_operation_started",
    "application_stage_finished",
    "application_commit_attempt_finished",
    "application_operation_finished",
)
EXPECTED_EVENTS = (EVENTS[0], EVENTS[1], EVENTS[1], EVENTS[2], EVENTS[3])


class ControlledCommitContext(RecordingContext):
    """Expose real entry and completion of save without protecting it from cancel."""

    def __init__(
        self, journal: list[Call], timeline: list[object], *,
        snapshot: SessionSnapshot, committed: Committed,
    ) -> None:
        super().__init__(journal, load_result=snapshot, save_result=committed)
        self.timeline = timeline
        self.save_entered = asyncio.Event()
        self.allow_save_finish = asyncio.Event()
        self.save_finished = False
        self.save_cancelled = False
        self.save_task: asyncio.Task[object] | None = None

    async def save(
        self, session_id: str, expected_state_version: int, delta: StateDelta,
    ) -> Committed:
        self.journal.append(Call(self, "save", (session_id, expected_state_version, delta)))
        self.save_task = asyncio.current_task()
        self.timeline.append("save_entered")
        self.save_entered.set()
        try:
            await self.allow_save_finish.wait()
        except asyncio.CancelledError:
            self.save_cancelled = True
            raise
        assert isinstance(self.save_result, Committed)
        self.save_finished = True
        self.timeline.append("save_finished")
        return self.save_result


@dataclass
class CommitCase:
    journal: list[Call]
    timeline: list[object]
    snapshot: SessionSnapshot
    command: BuildNatalCommand
    run: RunContext
    outcome: BuildNatalSuccess
    committed: Committed
    context: ControlledCommitContext
    handler: RecordingHandler
    orchestrator: ApplicationOrchestrator


def make_case(*, loaded_version: int, committed_version: int) -> CommitCase:
    journal: list[Call] = []
    timeline: list[object] = []
    state = SessionState.model_validate({
        **new_session(SESSION_ID, now=STARTED_AT).model_dump(),
        "state_version": loaded_version,
    })
    snapshot = SessionSnapshot(state=state, dialog=())
    spec, fixture_birth = chart_spec(), resolved_birth_data()
    resolved = ResolvedBirthData.model_validate({
        **fixture_birth.model_dump(),
        "utc_datetime": fixture_birth.utc_datetime.replace(second=0, microsecond=0),
    })
    local_birth = resolved.utc_datetime + timedelta(seconds=resolved.utc_offset_seconds)
    birth_input = BirthInput(
        birth_date=local_birth.date(),
        birth_time=local_birth.time().replace(tzinfo=None),
        place_id="moscow-ru",
    )
    command = BuildNatalCommand(birth_input=birth_input)
    outcome = BuildNatalSuccess(
        artifact=artifact(spec=spec, resolved=resolved),
        delta=StateDelta(
            birth_input=birth_input, birth_resolved=resolved, base_chart_spec=spec,
        ),
    )
    committed = Committed(state_version=committed_version)
    context = ControlledCommitContext(
        journal, timeline, snapshot=snapshot, committed=committed,
    )
    handler = RecordingHandler(journal, result=outcome)
    run = RunContext(run_id=RUN_ID_B, started_at=STARTED_AT)
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={BuildNatalCommand: handler},
        clock=lambda: STARTED_AT,
    )
    return CommitCase(
        journal, timeline, snapshot, command, run, outcome, committed,
        context, handler, orchestrator,
    )


@contextmanager
def capture_lifecycle(
    caplog: pytest.LogCaptureFixture, timeline: list[object],
) -> Iterator[None]:
    """Record actual LogRecords in the same ordered stream as save/caller events."""
    logger = logging.getLogger(LOGGER_NAME)
    handlers = logger.handlers[:]
    propagate, level, disabled = logger.propagate, logger.level, logger.disabled

    class TimelineHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.getMessage().partition(" ")[0] in EVENTS:
                timeline.append(record)

    observer = TimelineHandler()
    try:
        caplog.set_level(logging.DEBUG, logger=logger.name)
        logger.handlers = [caplog.handler, observer]
        logger.propagate = False
        logger.disabled = False
        yield
    finally:
        logger.handlers = handlers
        logger.propagate = propagate
        logger.setLevel(level)
        logger.disabled = disabled
        observer.close()


def lifecycle(timeline: list[object]) -> list[logging.LogRecord]:
    return [item for item in timeline if isinstance(item, logging.LogRecord)]


def fields(record: logging.LogRecord) -> dict[str, object]:
    message = record.getMessage()
    assert len(message.splitlines()) == 1
    value = json.loads(message.partition(" ")[2])
    assert isinstance(value, dict)
    return value


def assert_calls(case: CommitCase) -> None:
    assert [call.method for call in case.journal] == ["load", "handle", "save"]
    loaded, handled, saved = case.journal
    assert loaded.target is case.context and loaded.args == (SESSION_ID,)
    assert handled.target is case.handler and len(handled.args) == 3
    assert handled.args[0] is case.command
    assert handled.args[1] is case.snapshot.state
    assert handled.args[2] is case.run
    assert saved.target is case.context and len(saved.args) == 3
    assert saved.args[:2] == (SESSION_ID, case.snapshot.state.state_version)
    assert saved.args[2] is case.outcome.delta


async def await_save_entry(case: CommitCase, caller: asyncio.Task[object]) -> None:
    """Observe entry inside save, or surface early execute failure immediately."""
    entered = asyncio.create_task(case.context.save_entered.wait())
    try:
        done, _ = await asyncio.wait(
            {caller, entered}, timeout=2, return_when=asyncio.FIRST_COMPLETED,
        )
        assert done, "execute did not enter save"
        if caller in done:
            await caller
            pytest.fail("execute returned before save was entered")
        assert entered in done and entered.result() is True
    finally:
        if not entered.done():
            entered.cancel()
            with suppress(asyncio.CancelledError):
                await entered


async def drain_case(case: CommitCase, caller: asyncio.Task[object]) -> None:
    """Release a pending fake and collect caller/inner-task outcomes on failure."""
    case.context.allow_save_finish.set()
    if caller.done():
        with suppress(asyncio.CancelledError):
            caller.exception()
    else:
        with suppress(Exception, asyncio.CancelledError):
            await asyncio.wait_for(caller, timeout=2)
    inner = case.context.save_task
    if inner is not None and inner is not caller:
        with suppress(Exception, asyncio.CancelledError):
            await asyncio.wait_for(inner, timeout=2)


def assert_lifecycle(case: CommitCase, *, delivery_cancelled: bool) -> None:
    records = lifecycle(case.timeline)
    assert tuple(record.getMessage().partition(" ")[0] for record in records) == EXPECTED_EVENTS
    assert [record.levelno for record in records] == [
        logging.INFO, logging.DEBUG, logging.DEBUG, logging.DEBUG, logging.INFO,
    ]
    started, loaded, handled, attempt, terminal = map(fields, records)
    run_id = str(case.run.run_id)
    assert started == {"run_id": run_id, "command_type": "BuildNatalCommand"}
    assert all(event["run_id"] == run_id for event in (loaded, handled, attempt, terminal))
    loaded_version = case.snapshot.state.state_version
    for stage, event, outcome in (
        ("load", loaded, "loaded"), ("handler", handled, "success"),
    ):
        duration = event["duration_ms"]
        assert type(duration) in (int, float) and math.isfinite(duration) and duration >= 0
        assert event == {
            "run_id": run_id, "stage": stage, "outcome": outcome,
            "duration_ms": duration, "state_version": loaded_version,
        }
    duration = attempt["duration_ms"]
    assert type(duration) in (int, float) and math.isfinite(duration) and duration >= 0
    assert attempt == {
        "run_id": run_id, "attempt": 1, "outcome": "committed",
        "detail_code": None, "duration_ms": duration,
        "state_version": case.committed.state_version,
    }
    assert terminal == {
        "terminal_kind": "result", "run_id": run_id,
        "orch_status": "SUCCESS", "handler_status": "SUCCESS",
        "context_status": "COMMITTED", "code": "OK", "detail_code": None,
        "state_version": case.committed.state_version,
        "load_duration_ms": loaded["duration_ms"],
        "handler_duration_ms": handled["duration_ms"],
        "commit_duration_ms": duration, "commit_attempts": 1,
        "commit_error_codes": [], "delivery_cancelled": delivery_cancelled,
    }
    for record in records:
        message = record.getMessage()
        assert SESSION_ID not in message
        assert "birth_input" not in message
        assert "birth_resolved" not in message
        assert "base_chart_spec" not in message
        assert "artifact" not in message
        assert str(case.command.birth_input.birth_date) not in message


@pytest.mark.parametrize(
    ("loaded_version", "committed_version"), [(0, 4), (7, 19)],
)
async def test_one_confirmed_save_waits_and_returns_committed(
    loaded_version: int, committed_version: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-10/11/13/17/26; AC-7/10/19/26/27/29–32: wait for one save and report its version."""
    case = make_case(
        loaded_version=loaded_version, committed_version=committed_version,
    )

    async def invoke() -> ApplicationCommitted:
        result = await case.orchestrator.execute(
            case.command, session_id=SESSION_ID, run=case.run,
        )
        case.timeline.append("caller_returned")
        return result

    with capture_lifecycle(caplog, case.timeline):
        caller = asyncio.create_task(invoke())
        try:
            await await_save_entry(case, caller)
            assert_calls(case)
            assert not caller.done() and not case.context.save_finished
            assert not case.context.save_cancelled
            assert [record.getMessage().partition(" ")[0] for record in lifecycle(case.timeline)] == [
                EVENTS[0], EVENTS[1], EVENTS[1],
            ]
            case.context.allow_save_finish.set()
            result = await asyncio.wait_for(caller, timeout=2)
            observed = tuple(case.timeline)  # before cleanup, at result delivery
            assert isinstance(result, ApplicationCommitted)
            assert result.model_dump() == {
                "orch_status": "SUCCESS", "handler_status": "SUCCESS",
                "context_status": "COMMITTED", "code": "OK", "detail_code": None,
                "user_message": None, "retryable": False, "run_id": case.run.run_id,
                "state_version": case.committed.state_version,
                "artifact": case.outcome.artifact.model_dump(),
            }
            assert case.context.save_finished and not case.context.save_cancelled
            assert case.context.save_task is not None and case.context.save_task.done()
            assert case.timeline.index("save_finished") < case.timeline.index("caller_returned")
            assert isinstance(observed[-2], logging.LogRecord)
            assert observed[-2].getMessage().startswith(EVENTS[3] + " ")
            assert observed[-1] == "caller_returned"
            assert_calls(case)
            assert_lifecycle(case, delivery_cancelled=False)
        finally:
            await drain_case(case, caller)


class OutcomeRecordingContext(RecordingContext):
    """Mark when a typed save or unexpected exception has actually finished."""

    def __init__(
        self, journal: list[Call], timeline: list[object], *,
        snapshot: SessionSnapshot, save_result: SaveOutcome | None,
        error: Exception | None = None,
    ) -> None:
        super().__init__(journal, load_result=snapshot, save_result=save_result)
        self.timeline = timeline
        self.error = error

    async def save(
        self, session_id: str, expected_state_version: int, delta: StateDelta,
    ) -> SaveOutcome:
        try:
            if self.error is not None:
                self.journal.append(Call(self, "save", (session_id, expected_state_version, delta)))
                raise self.error
            return await super().save(session_id, expected_state_version, delta)
        finally:
            self.timeline.append("save_exited")


@dataclass
class OutcomeCase:
    prepared: CommitCase
    context: OutcomeRecordingContext
    run: RunContext
    orchestrator: ApplicationOrchestrator


def make_outcome_case(
    *, save_result: SaveOutcome | None, loaded_version: int = 7,
    deadline: datetime | None = None, error: Exception | None = None,
) -> OutcomeCase:
    prepared = make_case(loaded_version=loaded_version, committed_version=19)
    context = OutcomeRecordingContext(
        prepared.journal, prepared.timeline, snapshot=prepared.snapshot,
        save_result=save_result, error=error,
    )
    run = RunContext(
        run_id=prepared.run.run_id, started_at=prepared.run.started_at,
        deadline=deadline,
    )
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={BuildNatalCommand: prepared.handler},
        clock=lambda: STARTED_AT,
    )
    return OutcomeCase(prepared, context, run, orchestrator)


def assert_outcome_calls(case: OutcomeCase) -> None:
    calls = case.prepared.journal
    assert [call.method for call in calls] == ["load", "handle", "save"]
    loaded, handled, saved = calls
    assert loaded.target is case.context and loaded.args == (SESSION_ID,)
    assert handled.target is case.prepared.handler
    assert len(handled.args) == 3
    assert handled.args[0] is case.prepared.command
    assert handled.args[1] is case.prepared.snapshot.state
    assert handled.args[2] is case.run
    assert saved.target is case.context
    assert len(saved.args) == 3
    assert saved.args[:2] == (SESSION_ID, case.prepared.snapshot.state.state_version)
    assert saved.args[2] is case.prepared.outcome.delta


async def execute_outcome_case(case: OutcomeCase) -> ApplicationResult:
    try:
        result = await case.orchestrator.execute(
            case.prepared.command, session_id=SESSION_ID, run=case.run,
        )
    except Exception:
        # Keep an unfinished mapper visibly red, but prove it reached one real save.
        assert_outcome_calls(case)
        raise
    case.prepared.timeline.append("caller_returned")
    assert_outcome_calls(case)
    return result


def assert_outcome_lifecycle(
    case: OutcomeCase, result: ApplicationResult, *, outcome: str,
    state_version: int | None, detail_code: str | None,
    attempt_level: int, terminal_level: int,
    commit_error_codes: list[str], forbidden_text: str | None = None,
) -> None:
    timeline = case.prepared.timeline
    records = lifecycle(timeline)
    assert tuple(record.getMessage().partition(" ")[0] for record in records) == EXPECTED_EVENTS
    assert [record.levelno for record in records] == [
        logging.INFO, logging.DEBUG, logging.DEBUG, attempt_level, terminal_level,
    ]
    assert timeline[-1] == "caller_returned"
    assert timeline.index("save_exited") < timeline.index(records[3])
    assert timeline.index(records[4]) < timeline.index("caller_returned")

    started, loaded, handled, attempt, terminal = map(fields, records)
    run_id = str(case.run.run_id)
    assert started == {"run_id": run_id, "command_type": "BuildNatalCommand"}
    assert all(event["run_id"] == run_id for event in (loaded, handled, attempt, terminal))
    for stage, event, stage_outcome in (
        ("load", loaded, "loaded"), ("handler", handled, "success"),
    ):
        duration = event["duration_ms"]
        assert type(duration) in (int, float) and math.isfinite(duration) and duration >= 0
        assert event == {
            "run_id": run_id, "stage": stage, "outcome": stage_outcome,
            "duration_ms": duration,
            "state_version": case.prepared.snapshot.state.state_version,
        }
    duration = attempt["duration_ms"]
    assert type(duration) in (int, float) and math.isfinite(duration) and duration >= 0
    expected_attempt = {
        "run_id": run_id, "attempt": 1, "outcome": outcome,
        "detail_code": detail_code, "duration_ms": duration,
    }
    if state_version is not None:
        expected_attempt["state_version"] = state_version
    assert attempt == expected_attempt
    assert terminal == {
        "terminal_kind": "result", "run_id": run_id,
        "orch_status": result.orch_status,
        "handler_status": result.handler_status,
        "context_status": result.context_status,
        "code": result.code, "detail_code": result.detail_code,
        "state_version": result.state_version,
        "load_duration_ms": loaded["duration_ms"],
        "handler_duration_ms": handled["duration_ms"],
        "commit_duration_ms": duration, "commit_attempts": 1,
        "commit_error_codes": commit_error_codes, "delivery_cancelled": False,
    }
    for record in records:
        message = record.getMessage()
        assert SESSION_ID not in message
        assert "birth_input" not in message
        assert "birth_resolved" not in message
        assert "base_chart_spec" not in message
        assert "artifact" not in message
        assert str(case.prepared.command.birth_input.birth_date) not in message
        if forbidden_text is not None:
            assert forbidden_text not in message


@pytest.mark.parametrize("applied_version", [0, 13])
async def test_already_applied_returns_success_without_another_save(
    applied_version: int, caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-14/15/26; AC-19/26/27/31/32: preserve typed applied version and artifact."""
    case = make_outcome_case(
        save_result=AlreadyApplied(state_version=applied_version),
        loaded_version=0,
    )
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await execute_outcome_case(case)
        assert isinstance(result, ApplicationAlreadyApplied)
        assert result.model_dump() == {
            "orch_status": "SUCCESS", "handler_status": "SUCCESS",
            "context_status": "ALREADY_APPLIED", "code": "OK",
            "detail_code": None, "user_message": None, "retryable": False,
            "run_id": case.run.run_id, "state_version": applied_version,
            "artifact": case.prepared.outcome.artifact.model_dump(),
        }
        assert_outcome_lifecycle(
            case, result, outcome="already_applied", state_version=applied_version,
            detail_code=None, attempt_level=logging.DEBUG,
            terminal_level=logging.INFO, commit_error_codes=[],
        )


@pytest.mark.parametrize("actual_version", [0, 21])
async def test_superseded_returns_actual_version_without_artifact_or_retry(
    actual_version: int, caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-14/16/26; AC-19/26/27/31/32: report actual state and stop after one save."""
    actual = SessionState.model_validate({
        **new_session(SESSION_ID, now=STARTED_AT).model_dump(),
        "state_version": actual_version,
    })
    case = make_outcome_case(save_result=Superseded(actual=actual))
    reaction = describe_failure(kind="superseded")
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await execute_outcome_case(case)
        assert isinstance(result, ApplicationSuperseded)
        assert result.model_dump() == {
            "orch_status": "SUPERSEDED", "handler_status": "SUCCESS",
            "context_status": "SUPERSEDED", "code": "RESULT_SUPERSEDED",
            "detail_code": None, "user_message": reaction.user_message,
            "retryable": False, "run_id": case.run.run_id,
            "state_version": actual_version,
        }
        assert not hasattr(result, "artifact")
        assert_outcome_lifecycle(
            case, result, outcome="superseded", state_version=actual_version,
            detail_code=None, attempt_level=logging.DEBUG,
            terminal_level=logging.INFO, commit_error_codes=[],
        )


@pytest.mark.parametrize("reason", ["expired", "not_found"])
async def test_absent_during_save_uses_commit_stage_code(
    reason: str, caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-14/26; AC-19/20/26/27/31/32: preserve absence reason at commit stage."""
    case = make_outcome_case(save_result=SessionAbsent(reason=reason))
    reaction = describe_failure(kind="session_absent", reason=reason, stage="commit")
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await execute_outcome_case(case)
        assert isinstance(result, ApplicationSessionAbsent)
        assert result.model_dump() == {
            "orch_status": "SESSION_ABSENT", "handler_status": "SUCCESS",
            "context_status": "SESSION_ABSENT", "code": "SESSION_LOST_DURING_OPERATION",
            "detail_code": None, "user_message": reaction.user_message,
            "retryable": False, "run_id": case.run.run_id,
            "state_version": None, "reason": reason,
        }
        assert not hasattr(result, "artifact")
        assert_outcome_lifecycle(
            case, result, outcome="session_absent", state_version=None,
            detail_code=None, attempt_level=logging.DEBUG,
            terminal_level=logging.INFO, commit_error_codes=[],
        )


async def test_commit_failure_after_expired_deadline_has_one_attempt(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-14/18/26; AC-19/26/27/31/32: expired deadline forbids retry, not first save."""
    error_code = "WRITE_UNCONFIRMED"
    case = make_outcome_case(
        save_result=StateCommitFailed(error_code=error_code),
        deadline=STARTED_AT - timedelta(seconds=1),
    )
    reaction = describe_failure(kind="state_commit_failed", error_code=error_code)
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await execute_outcome_case(case)
        assert isinstance(result, ApplicationStateCommitFailure)
        assert result.model_dump() == {
            "orch_status": "FAILURE", "handler_status": "SUCCESS",
            "context_status": "COMMIT_FAILED", "code": "STATE_COMMIT_FAILED",
            "detail_code": error_code, "user_message": reaction.user_message,
            "retryable": True, "run_id": case.run.run_id,
            "state_version": None,
        }
        assert not hasattr(result, "artifact")
        assert error_code not in result.user_message
        assert_outcome_lifecycle(
            case, result, outcome="state_commit_failed", state_version=None,
            detail_code=error_code, attempt_level=logging.WARNING,
            terminal_level=logging.WARNING, commit_error_codes=[error_code],
        )


async def test_unexpected_save_exception_is_logged_and_returns_internal_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-25/26; AC-19/21/26/27/31/32: safe failure plus separate traceback."""
    sentinel = "unique-save-exception-private-sentinel"
    case = make_outcome_case(save_result=None, error=RuntimeError(sentinel))
    reaction = describe_failure(kind="internal_failure")
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await execute_outcome_case(case)
        assert isinstance(result, ApplicationInternalFailure)
        assert result.model_dump() == {
            "orch_status": "FAILURE", "handler_status": "SUCCESS",
            "context_status": "COMMIT_FAILED", "code": "INTERNAL_FAILURE",
            "detail_code": None, "user_message": reaction.user_message,
            "retryable": False, "run_id": case.run.run_id,
            "state_version": None,
        }
        assert not hasattr(result, "artifact")
        assert sentinel not in result.user_message
        assert_outcome_lifecycle(
            case, result, outcome="unexpected_failure", state_version=None,
            detail_code=None, attempt_level=logging.WARNING,
            terminal_level=logging.WARNING, commit_error_codes=[],
            forbidden_text=sentinel,
        )
        exception_records = [
            record for record in caplog.records
            if record.exc_info is not None and record.name.startswith(LOGGER_NAME)
        ]
        assert len(exception_records) == 1
        exception_record = exception_records[0]
        assert str(case.run.run_id) in exception_record.getMessage()
        assert sentinel in "".join(traceback.format_exception(*exception_record.exc_info))
