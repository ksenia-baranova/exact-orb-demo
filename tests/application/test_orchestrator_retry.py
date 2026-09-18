"""One exact commit retry through the real ApplicationOrchestrator."""

from __future__ import annotations

import asyncio
import logging
import math
import traceback
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
from tests.application.orchestrator_fakes import Call, RecordingContext, SaveOutcome
from tests.application.test_orchestrator_commit import (
    CommitCase,
    EVENTS,
    EXPECTED_EVENTS,
    LOGGER_NAME,
    SESSION_ID,
    capture_lifecycle,
    fields,
    lifecycle,
    make_case,
)
from tests.fixtures.telemetry import STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit
FIRST_ERROR = "FIRST_WRITE_UNCONFIRMED"
SECOND_ERROR = "SECOND_WRITE_UNCONFIRMED"


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.now = now
        self.calls = 0

    def __call__(self) -> datetime:
        self.calls += 1
        return self.now


class SequencedContext(RecordingContext):
    """Expose actual save calls and an optional gate within the first save."""

    def __init__(
        self, journal: list[Call], timeline: list[object], *,
        snapshot: SessionSnapshot, outcomes: tuple[SaveOutcome | Exception, ...],
        block_first: bool = False,
    ) -> None:
        super().__init__(journal, load_result=snapshot)
        self.timeline = timeline
        self.outcomes = outcomes
        self.block_first = block_first
        self.first_entered = asyncio.Event()
        self.allow_first = asyncio.Event()
        if not block_first:
            self.allow_first.set()
        self.save_cancelled = False
        self.save_tasks: list[asyncio.Task[object] | None] = []

    async def save(
        self, session_id: str, expected_state_version: int, delta: StateDelta,
    ) -> SaveOutcome:
        attempt = len(self.save_tasks) + 1
        self.journal.append(Call(self, "save", (session_id, expected_state_version, delta)))
        self.save_tasks.append(asyncio.current_task())
        self.timeline.append(f"save_{attempt}_entered")
        try:
            if attempt == 1:
                self.first_entered.set()
                await self.allow_first.wait()
            outcome = self.outcomes[attempt - 1]
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        except asyncio.CancelledError:
            self.save_cancelled = True
            raise
        finally:
            self.timeline.append(f"save_{attempt}_exited")


@dataclass
class RetryCase:
    prepared: CommitCase
    context: SequencedContext
    run: RunContext
    clock: FixedClock
    orchestrator: ApplicationOrchestrator


def make_retry_case(
    second: SaveOutcome | Exception, *, deadline: datetime | None = None,
    block_first: bool = False,
) -> RetryCase:
    prepared = make_case(loaded_version=7, committed_version=19)
    context = SequencedContext(
        prepared.journal, prepared.timeline, snapshot=prepared.snapshot,
        outcomes=(StateCommitFailed(error_code=FIRST_ERROR), second),
        block_first=block_first,
    )
    run = RunContext(
        run_id=prepared.run.run_id, started_at=prepared.run.started_at,
        deadline=deadline,
    )
    clock = FixedClock(STARTED_AT)
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={BuildNatalCommand: prepared.handler},
        clock=clock,
    )
    return RetryCase(prepared, context, run, clock, orchestrator)


async def invoke(case: RetryCase) -> ApplicationResult:
    try:
        result = await case.orchestrator.execute(
            case.prepared.command, session_id=SESSION_ID, run=case.run,
        )
    except asyncio.CancelledError:
        case.prepared.timeline.append("caller_cancelled")
        raise
    case.prepared.timeline.append("caller_returned")
    return result


def assert_calls(case: RetryCase, *, attempts: int) -> None:
    calls = case.prepared.journal
    assert [call.method for call in calls] == ["load", "handle"] + ["save"] * attempts
    loaded, handled, *saved = calls
    assert loaded.target is case.context and loaded.args == (SESSION_ID,)
    assert handled.target is case.prepared.handler
    assert handled.args == (case.prepared.command, case.prepared.snapshot.state, case.run)
    assert handled.args[0] is case.prepared.command
    assert handled.args[1] is case.prepared.snapshot.state
    assert handled.args[2] is case.run
    assert len(saved) == attempts
    for call in saved:
        assert call.target is case.context
        assert call.args[:2] == (SESSION_ID, case.prepared.snapshot.state.state_version)
        assert call.args[2] is case.prepared.outcome.delta
    assert len(case.context.save_tasks) == attempts
    assert all(task is not None and task.done() for task in case.context.save_tasks)
    assert not case.context.save_cancelled


def assert_events(
    case: RetryCase, result: ApplicationResult, *, attempts: int,
    second_outcome: str | None = None, second_detail: str | None = None,
    second_version: int | None = None, error_codes: list[str],
    delivery_cancelled: bool = False, exception_text: str | None = None,
) -> None:
    timeline = case.prepared.timeline
    records = lifecycle(timeline)
    names = [record.getMessage().partition(" ")[0] for record in records]
    assert names == list(EXPECTED_EVENTS[:3]) + [EVENTS[2]] * attempts + [EVENTS[3]]
    assert [record.levelno for record in records] == [
        logging.INFO, logging.DEBUG, logging.DEBUG,
        *([logging.WARNING] * attempts),
        logging.WARNING if result.orch_status == "FAILURE" else logging.INFO,
    ]
    started, loaded, handled = map(fields, records[:3])
    attempt_records = records[3:-1]
    terminal = fields(records[-1])
    run_id = str(case.run.run_id)
    assert started == {"run_id": run_id, "command_type": "BuildNatalCommand"}
    for event, stage, outcome in (
        (loaded, "load", "loaded"), (handled, "handler", "success"),
    ):
        assert event == {
            "run_id": run_id, "stage": stage, "outcome": outcome,
            "duration_ms": event["duration_ms"],
            "state_version": case.prepared.snapshot.state.state_version,
        }
        assert_finite_duration(event["duration_ms"])
    durations: list[float] = []
    for number, record in enumerate(attempt_records, 1):
        event = fields(record)
        assert_finite_duration(event["duration_ms"])
        durations.append(event["duration_ms"])
        expected = {
            "run_id": run_id, "attempt": number,
            "outcome": "state_commit_failed" if number == 1 else second_outcome,
            "detail_code": FIRST_ERROR if number == 1 else second_detail,
            "duration_ms": event["duration_ms"],
        }
        if number == 2 and second_version is not None:
            expected["state_version"] = second_version
        assert event == expected
        assert timeline.index(f"save_{number}_exited") < timeline.index(record)
    if attempts == 2:
        assert timeline.index(attempt_records[0]) < timeline.index("save_2_entered")
    assert terminal == {
        "terminal_kind": "result", "run_id": run_id,
        "orch_status": result.orch_status,
        "handler_status": result.handler_status,
        "context_status": result.context_status,
        "code": result.code, "detail_code": result.detail_code,
        "state_version": result.state_version,
        "load_duration_ms": loaded["duration_ms"],
        "handler_duration_ms": handled["duration_ms"],
        "commit_duration_ms": terminal["commit_duration_ms"],
        "commit_attempts": attempts,
        "commit_error_codes": error_codes,
        "delivery_cancelled": delivery_cancelled,
    }
    assert terminal["commit_duration_ms"] == pytest.approx(sum(durations))
    assert timeline.index(attempt_records[-1]) < timeline.index(records[-1])
    assert timeline[-1] == ("caller_cancelled" if delivery_cancelled else "caller_returned")
    assert timeline.index(records[-1]) < len(timeline) - 1
    for record in records:
        message = record.getMessage()
        assert SESSION_ID not in message
        assert "birth_input" not in message
        assert "birth_resolved" not in message
        assert "base_chart_spec" not in message
        assert "artifact" not in message
        assert str(case.prepared.command.birth_input.birth_date) not in message
        if exception_text is not None:
            assert exception_text not in message


def assert_finite_duration(value: object) -> None:
    assert type(value) in (int, float) and math.isfinite(value) and value >= 0


@pytest.mark.parametrize(
    ("second", "expected_type", "context_status", "version"),
    [
        (Committed(state_version=23), ApplicationCommitted, "COMMITTED", 23),
        (AlreadyApplied(state_version=0), ApplicationAlreadyApplied, "ALREADY_APPLIED", 0),
    ],
    ids=["committed", "already_applied"],
)
async def test_retry_success_uses_original_delta_and_typed_version(
    second: SaveOutcome, expected_type: type[ApplicationResult],
    context_status: str, version: int, caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-11–13/19/26; AC-11–13/19/26/27/31/32: one exact retry can confirm success."""
    case = make_retry_case(second)
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await invoke(case)
        assert_calls(case, attempts=2)
        assert isinstance(result, expected_type)
        assert result.model_dump() == {
            "orch_status": "SUCCESS", "handler_status": "SUCCESS",
            "context_status": context_status, "code": "OK", "detail_code": None,
            "user_message": None, "retryable": False,
            "run_id": case.run.run_id, "state_version": version,
            "artifact": case.prepared.outcome.artifact.model_dump(),
        }
        assert_events(
            case, result, attempts=2,
            second_outcome="committed" if context_status == "COMMITTED" else "already_applied",
            second_version=version, error_codes=[FIRST_ERROR],
        )


async def test_retry_superseded_stops_without_artifact(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-16/19/26; AC-13/19/26/27/31/32: second Superseded ends the operation."""
    actual = SessionState.model_validate({
        **new_session(SESSION_ID, now=STARTED_AT).model_dump(), "state_version": 21,
    })
    case = make_retry_case(Superseded(actual=actual))
    reaction = describe_failure(kind="superseded")
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await invoke(case)
        assert_calls(case, attempts=2)
        assert isinstance(result, ApplicationSuperseded)
        assert result.model_dump() == {
            "orch_status": "SUPERSEDED", "handler_status": "SUCCESS",
            "context_status": "SUPERSEDED", "code": "RESULT_SUPERSEDED",
            "detail_code": None, "user_message": reaction.user_message,
            "retryable": False, "run_id": case.run.run_id,
            "state_version": actual.state_version,
        }
        assert not hasattr(result, "artifact")
        assert_events(
            case, result, attempts=2, second_outcome="superseded",
            second_version=actual.state_version, error_codes=[FIRST_ERROR],
        )


@pytest.mark.parametrize("reason", ["expired", "not_found"])
async def test_retry_session_absent_preserves_reason(
    reason: str, caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-19/26; AC-13/19/20/26/27/31/32: second absence is a commit-stage result."""
    case = make_retry_case(SessionAbsent(reason=reason))
    reaction = describe_failure(kind="session_absent", stage="commit", reason=reason)
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await invoke(case)
        assert_calls(case, attempts=2)
        assert isinstance(result, ApplicationSessionAbsent)
        assert result.model_dump() == {
            "orch_status": "SESSION_ABSENT", "handler_status": "SUCCESS",
            "context_status": "SESSION_ABSENT", "code": "SESSION_LOST_DURING_OPERATION",
            "detail_code": None, "user_message": reaction.user_message,
            "retryable": False, "run_id": case.run.run_id,
            "state_version": None, "reason": reason,
        }
        assert not hasattr(result, "artifact")
        assert_events(
            case, result, attempts=2, second_outcome="session_absent",
            error_codes=[FIRST_ERROR],
        )


async def test_retry_second_commit_failure_uses_last_error_code(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-18/19/26; AC-11/13/19/26/27/31/32: two failures retain ordered codes."""
    case = make_retry_case(StateCommitFailed(error_code=SECOND_ERROR))
    reaction = describe_failure(kind="state_commit_failed", error_code=SECOND_ERROR)
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await invoke(case)
        assert_calls(case, attempts=2)
        assert isinstance(result, ApplicationStateCommitFailure)
        assert result.model_dump() == {
            "orch_status": "FAILURE", "handler_status": "SUCCESS",
            "context_status": "COMMIT_FAILED", "code": "STATE_COMMIT_FAILED",
            "detail_code": SECOND_ERROR, "user_message": reaction.user_message,
            "retryable": True, "run_id": case.run.run_id,
            "state_version": None,
        }
        assert not hasattr(result, "artifact")
        assert_events(
            case, result, attempts=2, second_outcome="state_commit_failed",
            second_detail=SECOND_ERROR, error_codes=[FIRST_ERROR, SECOND_ERROR],
        )


async def test_retry_unexpected_exception_is_internal_failure_without_third_save(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-19/25/26; AC-11/13/19/21/26/27/31/32: exception is safe and final."""
    sentinel = "private-second-save-exception"
    case = make_retry_case(RuntimeError(sentinel))
    reaction = describe_failure(kind="internal_failure")
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await invoke(case)
        assert_calls(case, attempts=2)
        assert isinstance(result, ApplicationInternalFailure)
        assert result.model_dump() == {
            "orch_status": "FAILURE", "handler_status": "SUCCESS",
            "context_status": "COMMIT_FAILED", "code": "INTERNAL_FAILURE",
            "detail_code": None, "user_message": reaction.user_message,
            "retryable": False, "run_id": case.run.run_id,
            "state_version": None,
        }
        assert sentinel not in result.user_message
        assert not hasattr(result, "artifact")
        assert_events(
            case, result, attempts=2, second_outcome="unexpected_failure",
            error_codes=[FIRST_ERROR], exception_text=sentinel,
        )
        exception_records = [
            record for record in caplog.records
            if record.exc_info is not None and record.name.startswith(LOGGER_NAME)
        ]
        assert len(exception_records) == 1
        assert str(case.run.run_id) in exception_records[0].getMessage()
        assert sentinel in "".join(traceback.format_exception(*exception_records[0].exc_info))


@pytest.mark.parametrize(
    ("deadline", "should_retry"),
    [
        (None, True),
        (STARTED_AT + timedelta(seconds=1), True),
        (STARTED_AT, False),
        (STARTED_AT - timedelta(seconds=1), False),
    ],
    ids=["none", "future", "equal", "past"],
)
async def test_deadline_controls_only_second_save(
    deadline: datetime | None, should_retry: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-19/21/26; AC-11/14/26/31/32: <= fake clock forbids only retry."""
    case = make_retry_case(Committed(state_version=23), deadline=deadline)
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await invoke(case)
        attempts = 2 if should_retry else 1
        assert_calls(case, attempts=attempts)
        if should_retry:
            assert isinstance(result, ApplicationCommitted)
            assert result.state_version == 23
            assert_events(
                case, result, attempts=2, second_outcome="committed",
                second_version=23, error_codes=[FIRST_ERROR],
            )
        else:
            reaction = describe_failure(kind="state_commit_failed", error_code=FIRST_ERROR)
            assert isinstance(result, ApplicationStateCommitFailure)
            assert result.model_dump() == {
                "orch_status": "FAILURE", "handler_status": "SUCCESS",
                "context_status": "COMMIT_FAILED", "code": "STATE_COMMIT_FAILED",
                "detail_code": FIRST_ERROR, "user_message": reaction.user_message,
                "retryable": True, "run_id": case.run.run_id,
                "state_version": None,
            }
            assert_events(case, result, attempts=1, error_codes=[FIRST_ERROR])
        if deadline is not None:
            assert case.clock.calls == 1


async def test_cancellation_after_first_save_entry_forbids_retry(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-19/20/26; AC-15–17/26/31/32: await first save, then cancel without retry."""
    case = make_retry_case(Committed(state_version=23), block_first=True)
    with capture_lifecycle(caplog, case.prepared.timeline):
        caller = asyncio.create_task(invoke(case))
        entered = asyncio.create_task(case.context.first_entered.wait())
        try:
            done, _ = await asyncio.wait(
                {caller, entered}, timeout=2, return_when=asyncio.FIRST_COMPLETED,
            )
            assert done, "first save was not entered"
            if caller in done:
                await caller
                pytest.fail("caller finished before entering save")
            assert entered in done and entered.result() is True
            assert [call.method for call in case.prepared.journal] == ["load", "handle", "save"]

            case.prepared.timeline.append("cancel_requested")
            caller.cancel()
            checkpoint = asyncio.Event()
            asyncio.get_running_loop().call_soon(checkpoint.set)
            await asyncio.wait_for(checkpoint.wait(), timeout=2)
            case.prepared.timeline.append("cancel_checkpoint")
            assert not caller.done()
            assert not case.context.save_cancelled
            assert not case.context.allow_first.is_set()

            case.context.allow_first.set()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(caller, timeout=2)
            assert_calls(case, attempts=1)
            reaction = describe_failure(kind="state_commit_failed", error_code=FIRST_ERROR)
            expected = ApplicationStateCommitFailure(
                code=reaction.code, detail_code=FIRST_ERROR,
                user_message=reaction.user_message, run_id=case.run.run_id,
            )
            assert_events(
                case, expected, attempts=1, error_codes=[FIRST_ERROR],
                delivery_cancelled=True,
            )
            timeline = case.prepared.timeline
            assert (
                timeline.index("save_1_entered")
                < timeline.index("cancel_requested")
                < timeline.index("cancel_checkpoint")
                < timeline.index("save_1_exited")
                < timeline.index("caller_cancelled")
            )
        finally:
            case.context.allow_first.set()
            if not entered.done():
                entered.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await entered
            if not caller.done():
                caller.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await caller
