"""Regression coverage for internal commit-flow failures and terminal events."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import NoReturn

import pytest

from exact_orb.application.application_results import ApplicationInternalFailure
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.session.outcomes import Committed
from tests.application.test_orchestrator_commit import (
    EVENTS,
    EXPECTED_EVENTS,
    capture_lifecycle,
    fields,
    lifecycle,
    make_case,
)
from tests.application.test_orchestrator_retry import FIRST_ERROR, make_retry_case
from tests.fixtures.telemetry import STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit
_SENTINEL = "internal sentinel must stay out of the response"


def _event_names(records: list[object]) -> list[str]:
    return [record.getMessage().partition(" ")[0] for record in records]


def _assert_internal_commit_failure(
    result: ApplicationInternalFailure, *, run_id: object,
) -> None:
    assert result.orch_status == "FAILURE"
    assert result.handler_status == "SUCCESS"
    assert result.context_status == "COMMIT_FAILED"
    assert result.code == "INTERNAL_FAILURE"
    assert result.detail_code is None
    assert result.retryable is False
    assert result.state_version is None
    assert result.run_id == run_id
    assert not hasattr(result, "artifact")
    assert _SENTINEL not in result.user_message


@pytest.mark.parametrize("failure", ["save_raises", "non_awaitable"])
async def test_commit_task_start_failure_returns_one_terminal_internal_failure(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    """UC-13, FR-25/26, AC-29/31/32: task start errors remain observable."""
    case = make_case(loaded_version=7, committed_version=8)
    calls: list[tuple[object, ...]] = []

    def broken_save(*args: object) -> object:
        calls.append(args)
        if failure == "save_raises":
            raise RuntimeError(_SENTINEL)
        return object()

    monkeypatch.setattr(case.context, "save", broken_save)
    caplog.set_level("DEBUG")
    with capture_lifecycle(caplog, case.timeline):
        result = await case.orchestrator.execute(
            case.command, session_id=case.snapshot.state.session_id, run=case.run,
        )

    assert isinstance(result, ApplicationInternalFailure)
    _assert_internal_commit_failure(result, run_id=case.run.run_id)
    assert len(calls) == 1
    assert calls[0][:2] == (
        case.snapshot.state.session_id, case.snapshot.state.state_version,
    )
    assert calls[0][2] is case.outcome.delta
    assert [call.method for call in case.journal] == ["load", "handle"]

    records = lifecycle(case.timeline)
    assert _event_names(records) == list(EXPECTED_EVENTS)
    attempt = fields(records[-2])
    assert attempt == {
        "run_id": str(case.run.run_id),
        "attempt": 1,
        "outcome": "unexpected_failure",
        "detail_code": None,
        "duration_ms": attempt["duration_ms"],
    }
    terminal = fields(records[-1])
    assert terminal["terminal_kind"] == "result"
    assert terminal["code"] == "INTERNAL_FAILURE"
    assert terminal["commit_attempts"] == 1
    assert terminal["commit_error_codes"] == []
    assert terminal["delivery_cancelled"] is False
    assert sum(name == EVENTS[-1] for name in _event_names(records)) == 1
    assert any(
        record.name == "exact_orb.application.orchestrator"
        and record.getMessage().startswith("Commit save failed")
        and record.exc_info is not None
        for record in caplog.records
    )


@pytest.mark.parametrize("failure", ["raises", "naive", "not_datetime"])
async def test_retry_clock_failure_returns_one_terminal_without_second_save(
    caplog: pytest.LogCaptureFixture,
    failure: str,
) -> None:
    """UC-13, FR-19/21/25/26: invalid retry clock cannot strand an operation."""
    case = make_retry_case(
        Committed(state_version=8), deadline=STARTED_AT + timedelta(seconds=1),
    )
    clock_calls = 0

    def broken_clock() -> object:
        nonlocal clock_calls
        clock_calls += 1
        if failure == "raises":
            _raise_clock_error()
        if failure == "naive":
            return datetime(2026, 1, 1)
        return 1

    orchestrator = ApplicationOrchestrator(
        context=case.context,
        handlers={BuildNatalCommand: case.prepared.handler},
        clock=broken_clock,  # type: ignore[arg-type] - deliberate contract violation
    )
    caplog.set_level("DEBUG")
    with capture_lifecycle(caplog, case.prepared.timeline):
        result = await orchestrator.execute(
            case.prepared.command,
            session_id=case.prepared.snapshot.state.session_id,
            run=case.run,
        )

    assert isinstance(result, ApplicationInternalFailure)
    _assert_internal_commit_failure(result, run_id=case.run.run_id)
    assert clock_calls == 1
    assert [call.method for call in case.prepared.journal] == ["load", "handle", "save"]
    assert len(case.context.save_tasks) == 1

    records = lifecycle(case.prepared.timeline)
    assert _event_names(records) == list(EXPECTED_EVENTS)
    attempt = fields(records[-2])
    assert attempt["attempt"] == 1
    assert attempt["outcome"] == "state_commit_failed"
    assert attempt["detail_code"] == FIRST_ERROR
    assert "state_version" not in attempt
    terminal = fields(records[-1])
    assert terminal["terminal_kind"] == "result"
    assert terminal["code"] == "INTERNAL_FAILURE"
    assert terminal["commit_attempts"] == 1
    assert terminal["commit_error_codes"] == [FIRST_ERROR]
    assert terminal["delivery_cancelled"] is False
    assert sum(name == EVENTS[-1] for name in _event_names(records)) == 1
    assert any(
        record.name == "exact_orb.application.orchestrator"
        and record.getMessage().startswith("Commit retry decision failed")
        and record.exc_info is not None
        for record in caplog.records
    )


def _raise_clock_error() -> NoReturn:
    raise RuntimeError(_SENTINEL)
