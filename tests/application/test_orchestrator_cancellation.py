"""Cancellation after save entry through the real ApplicationOrchestrator."""

from __future__ import annotations

import asyncio
from contextlib import suppress
import logging

import pytest

from exact_orb.application.application_results import ApplicationResult
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.session.outcomes import Committed, StateCommitFailed
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import StateDelta
from tests.application.orchestrator_fakes import Call, RecordingContext, SaveOutcome
from tests.application.test_orchestrator_commit import (
    CommitCase,
    EVENTS,
    SESSION_ID,
    assert_calls,
    assert_lifecycle,
    await_save_entry,
    capture_lifecycle,
    drain_case,
    fields,
    lifecycle,
    make_case,
)
from tests.fixtures.telemetry import STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit


async def test_cancel_after_save_entry_waits_for_commit_and_terminal(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """UC-15; FR-20/26; AC-16/17/26/29/31/32: commit and terminal precede cancellation."""
    case = make_case(loaded_version=7, committed_version=19)

    async def invoke() -> ApplicationResult:
        try:
            return await case.orchestrator.execute(
                case.command, session_id=SESSION_ID, run=case.run,
            )
        except asyncio.CancelledError:
            case.timeline.append("caller_cancelled")
            raise

    with capture_lifecycle(caplog, case.timeline):
        caller = asyncio.create_task(invoke())
        try:
            await await_save_entry(case, caller)
            assert_calls(case)
            assert not case.context.save_finished
            assert not case.context.save_cancelled

            case.timeline.append("cancel_requested")
            caller.cancel()
            checkpoint = asyncio.Event()
            # cancel() queues the caller first; this callback then wakes our
            # observer after the caller has had a chance to process cancellation.
            asyncio.get_running_loop().call_soon(checkpoint.set)
            await asyncio.wait_for(checkpoint.wait(), timeout=2)
            case.timeline.append("cancel_checkpoint")

            assert not caller.done()
            assert case.context.save_task is not None
            assert not case.context.save_task.done()
            assert not case.context.save_finished
            assert not case.context.save_cancelled
            assert not case.context.allow_save_finish.is_set()
            assert [record.getMessage().partition(" ")[0] for record in lifecycle(case.timeline)] == [
                EVENTS[0], EVENTS[1], EVENTS[1],
            ]
            assert_calls(case)

            case.context.allow_save_finish.set()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(caller, timeout=2)
            observed = tuple(case.timeline)  # before cleanup, when caller sees cancellation
            assert case.context.save_finished and not case.context.save_cancelled
            assert case.context.save_task is not None and case.context.save_task.done()
            assert_calls(case)
            assert_lifecycle(case, delivery_cancelled=True)

            save_finished = observed.index("save_finished")
            attempt = next(
                index for index, item in enumerate(observed)
                if isinstance(item, logging.LogRecord)
                and item.getMessage().startswith(EVENTS[2] + " ")
            )
            terminal = next(
                index for index, item in enumerate(observed)
                if isinstance(item, logging.LogRecord)
                and item.getMessage().startswith(EVENTS[3] + " ")
            )
            assert (
                observed.index("save_entered")
                < observed.index("cancel_requested")
                < observed.index("cancel_checkpoint")
                < save_finished < attempt < terminal
                < observed.index("caller_cancelled")
            )
            assert observed[-1] == "caller_cancelled"
        finally:
            await drain_case(case, caller)


class _GatedSaveContext(RecordingContext):
    """Expose both real save entries and hold one attempt until explicitly released."""

    def __init__(
        self, journal: list[Call], timeline: list[object], *,
        snapshot: SessionSnapshot, outcomes: tuple[SaveOutcome, ...],
        blocked_attempt: int,
    ) -> None:
        super().__init__(journal, load_result=snapshot)
        self.timeline = timeline
        self.outcomes = outcomes
        self.entered = tuple(asyncio.Event() for _ in outcomes)
        self.release = tuple(asyncio.Event() for _ in outcomes)
        self.save_tasks: list[asyncio.Task[object]] = []
        self.completed: list[int] = []
        self.cancelled: list[int] = []
        for number, event in enumerate(self.release, start=1):
            if number != blocked_attempt:
                event.set()

    async def save(
        self, session_id: str, expected_state_version: int, delta: StateDelta,
    ) -> SaveOutcome:
        attempt = len(self.save_tasks) + 1
        self.journal.append(Call(self, "save", (session_id, expected_state_version, delta)))
        assert attempt <= len(self.outcomes), "unexpected third save"
        task = asyncio.current_task()
        assert task is not None
        self.save_tasks.append(task)
        self.timeline.append(f"save_{attempt}_entered")
        self.entered[attempt - 1].set()
        try:
            await self.release[attempt - 1].wait()
            outcome = self.outcomes[attempt - 1]
            self.completed.append(attempt)
            self.timeline.append(f"save_{attempt}_finished")
            return outcome
        except asyncio.CancelledError:
            self.cancelled.append(attempt)
            self.timeline.append(f"save_{attempt}_cancelled")
            raise


def _make_gated_flow(
    outcomes: tuple[SaveOutcome, ...], *, blocked_attempt: int,
) -> tuple[CommitCase, _GatedSaveContext, ApplicationOrchestrator]:
    prepared = make_case(loaded_version=7, committed_version=19)
    context = _GatedSaveContext(
        prepared.journal, prepared.timeline, snapshot=prepared.snapshot,
        outcomes=outcomes, blocked_attempt=blocked_attempt,
    )
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={BuildNatalCommand: prepared.handler},
        clock=lambda: STARTED_AT,
    )
    return prepared, context, orchestrator


async def _invoke_gated(
    prepared: CommitCase, orchestrator: ApplicationOrchestrator,
) -> ApplicationResult:
    try:
        return await orchestrator.execute(
            prepared.command, session_id=SESSION_ID, run=prepared.run,
        )
    except asyncio.CancelledError:
        prepared.timeline.append("caller_cancelled")
        raise


async def _await_save_entry(
    context: _GatedSaveContext, caller: asyncio.Task[ApplicationResult],
    attempt: int,
) -> None:
    entered = asyncio.create_task(context.entered[attempt - 1].wait())
    try:
        done, _ = await asyncio.wait(
            {caller, entered}, timeout=2, return_when=asyncio.FIRST_COMPLETED,
        )
        assert done, f"save attempt {attempt} was not entered"
        if caller in done:
            await caller
            pytest.fail("caller completed before the expected save attempt")
        assert entered in done and entered.result() is True
    finally:
        if not entered.done():
            entered.cancel()
            with suppress(asyncio.CancelledError):
                await entered


async def _cancel_and_checkpoint(
    caller: asyncio.Task[ApplicationResult], timeline: list[object], marker: str,
) -> None:
    timeline.append(f"{marker}_requested")
    assert caller.cancel(marker)
    checkpoint = asyncio.Event()
    asyncio.get_running_loop().call_soon(checkpoint.set)
    await asyncio.wait_for(checkpoint.wait(), timeout=2)
    timeline.append(f"{marker}_checkpoint")
    assert not caller.done()


async def _drain_gated(
    context: _GatedSaveContext, caller: asyncio.Task[ApplicationResult],
) -> None:
    for event in context.release:
        event.set()
    if not caller.done():
        caller.cancel("cleanup")
    with suppress(Exception, asyncio.CancelledError):
        await asyncio.wait_for(caller, timeout=2)
    for task in context.save_tasks:
        if not task.done():
            with suppress(Exception, asyncio.CancelledError):
                await asyncio.wait_for(asyncio.shield(task), timeout=2)


def _assert_save_arguments(
    prepared: CommitCase, context: _GatedSaveContext, attempts: int,
) -> None:
    calls = prepared.journal
    assert [call.method for call in calls] == ["load", "handle"] + ["save"] * attempts
    assert calls[0].target is context and calls[0].args == (SESSION_ID,)
    assert calls[1].target is prepared.handler
    assert calls[1].args == (prepared.command, prepared.snapshot.state, prepared.run)
    for call in calls[2:]:
        assert call.target is context
        assert call.args[:2] == (SESSION_ID, prepared.snapshot.state.state_version)
        assert call.args[2] is prepared.outcome.delta


@pytest.mark.parametrize(
    ("first", "outcome", "code", "error_codes", "terminal_level"),
    [
        (Committed(state_version=19), "committed", "OK", [], logging.INFO),
        (StateCommitFailed(error_code="FIRST_WRITE_UNCONFIRMED"),
         "state_commit_failed", "STATE_COMMIT_FAILED",
         ["FIRST_WRITE_UNCONFIRMED"], logging.WARNING),
    ],
    ids=["committed", "commit_failed"],
)
async def test_repeated_cancel_waits_for_first_save_and_forbids_retry(
    first: SaveOutcome, outcome: str, code: str, error_codes: list[str],
    terminal_level: int, caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-15–18/29/31/32: repeated cancellation cannot detach the first save."""
    prepared, context, orchestrator = _make_gated_flow((first,), blocked_attempt=1)
    with capture_lifecycle(caplog, prepared.timeline):
        caller = asyncio.create_task(_invoke_gated(prepared, orchestrator))
        try:
            await _await_save_entry(context, caller, 1)
            _assert_save_arguments(prepared, context, 1)
            for marker in ("first_cancel", "repeat_cancel"):
                await _cancel_and_checkpoint(caller, prepared.timeline, marker)
                assert not context.save_tasks[0].done()
                assert context.completed == context.cancelled == []
                assert not context.release[0].is_set()
                assert [record.getMessage().partition(" ")[0]
                        for record in lifecycle(prepared.timeline)] == list(EVENTS[:2]) + [EVENTS[1]]

            context.release[0].set()
            with pytest.raises(asyncio.CancelledError) as observed:
                await asyncio.wait_for(caller, timeout=2)
            assert observed.value.args == ("first_cancel",)
            assert context.completed == [1] and context.cancelled == []
            assert len(context.save_tasks) == 1
            assert context.save_tasks[0].done()
            assert context.save_tasks[0].result() is first
            _assert_save_arguments(prepared, context, 1)

            records = lifecycle(prepared.timeline)
            assert [record.getMessage().partition(" ")[0] for record in records] == [
                EVENTS[0], EVENTS[1], EVENTS[1], EVENTS[2], EVENTS[3],
            ]
            assert [record.levelno for record in records] == [
                logging.INFO, logging.DEBUG, logging.DEBUG,
                logging.DEBUG if outcome == "committed" else logging.WARNING,
                terminal_level,
            ]
            attempt_event, terminal = map(fields, records[-2:])
            assert attempt_event["attempt"] == 1
            assert attempt_event["outcome"] == outcome
            assert terminal["code"] == code
            assert terminal["detail_code"] == (
                first.error_code if isinstance(first, StateCommitFailed) else None
            )
            assert terminal["state_version"] == (
                first.state_version if isinstance(first, Committed) else None
            )
            assert terminal["commit_attempts"] == 1
            assert terminal["commit_error_codes"] == error_codes
            assert terminal["delivery_cancelled"] is True
            assert terminal["terminal_kind"] == "result"
            assert all(fields(record)["run_id"] == str(prepared.run.run_id)
                       for record in records)
            timeline = prepared.timeline
            assert (
                timeline.index("save_1_entered")
                < timeline.index("first_cancel_requested")
                < timeline.index("first_cancel_checkpoint")
                < timeline.index("repeat_cancel_requested")
                < timeline.index("repeat_cancel_checkpoint")
                < timeline.index("save_1_finished")
                < timeline.index(records[-2])
                < timeline.index(records[-1])
                < timeline.index("caller_cancelled")
            )
            assert timeline[-1] == "caller_cancelled"
        finally:
            await _drain_gated(context, caller)


@pytest.mark.parametrize(
    ("second", "second_outcome", "code", "error_codes", "terminal_level"),
    [
        (Committed(state_version=23), "committed", "OK",
         ["FIRST_WRITE_UNCONFIRMED"], logging.INFO),
        (StateCommitFailed(error_code="SECOND_WRITE_UNCONFIRMED"),
         "state_commit_failed", "STATE_COMMIT_FAILED",
         ["FIRST_WRITE_UNCONFIRMED", "SECOND_WRITE_UNCONFIRMED"], logging.WARNING),
    ],
    ids=["committed", "commit_failed"],
)
async def test_cancel_after_second_save_entry_waits_for_its_outcome(
    second: SaveOutcome, second_outcome: str, code: str,
    error_codes: list[str], terminal_level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-16–18/29/31/32: an already-started retry completes before cancellation."""
    first = StateCommitFailed(error_code="FIRST_WRITE_UNCONFIRMED")
    prepared, context, orchestrator = _make_gated_flow(
        (first, second), blocked_attempt=2,
    )
    with capture_lifecycle(caplog, prepared.timeline):
        caller = asyncio.create_task(_invoke_gated(prepared, orchestrator))
        try:
            await _await_save_entry(context, caller, 2)
            _assert_save_arguments(prepared, context, 2)
            assert context.completed == [1] and context.cancelled == []
            assert context.save_tasks[0].done()
            assert context.save_tasks[0].result() is first
            assert not context.save_tasks[1].done()
            before_cancel = lifecycle(prepared.timeline)
            assert [record.getMessage().partition(" ")[0]
                    for record in before_cancel] == [
                EVENTS[0], EVENTS[1], EVENTS[1], EVENTS[2],
            ]
            assert prepared.timeline.index("save_1_finished") < prepared.timeline.index(
                before_cancel[-1]
            ) < prepared.timeline.index("save_2_entered")

            for marker in ("first_cancel", "repeat_cancel"):
                await _cancel_and_checkpoint(caller, prepared.timeline, marker)
                assert not context.save_tasks[1].done()
                assert context.completed == [1] and context.cancelled == []
                assert not context.release[1].is_set()
                assert lifecycle(prepared.timeline) == before_cancel

            context.release[1].set()
            with pytest.raises(asyncio.CancelledError) as observed:
                await asyncio.wait_for(caller, timeout=2)
            assert observed.value.args == ("first_cancel",)
            assert context.completed == [1, 2] and context.cancelled == []
            assert len(context.save_tasks) == 2
            assert all(task.done() for task in context.save_tasks)
            assert context.save_tasks[1].result() is second
            _assert_save_arguments(prepared, context, 2)

            records = lifecycle(prepared.timeline)
            assert [record.getMessage().partition(" ")[0] for record in records] == [
                EVENTS[0], EVENTS[1], EVENTS[1], EVENTS[2], EVENTS[2], EVENTS[3],
            ]
            assert [record.levelno for record in records] == [
                logging.INFO, logging.DEBUG, logging.DEBUG,
                logging.WARNING, logging.WARNING, terminal_level,
            ]
            first_attempt, second_attempt, terminal = map(fields, records[-3:])
            assert first_attempt["attempt"] == 1
            assert first_attempt["outcome"] == "state_commit_failed"
            assert first_attempt["detail_code"] == "FIRST_WRITE_UNCONFIRMED"
            assert second_attempt["attempt"] == 2
            assert second_attempt["outcome"] == second_outcome
            assert second_attempt["detail_code"] == (
                "SECOND_WRITE_UNCONFIRMED" if second_outcome == "state_commit_failed" else None
            )
            assert terminal["terminal_kind"] == "result"
            assert terminal["code"] == code
            assert terminal["detail_code"] == (
                second.error_code if isinstance(second, StateCommitFailed) else None
            )
            assert terminal["state_version"] == (
                second.state_version if isinstance(second, Committed) else None
            )
            assert terminal["commit_attempts"] == 2
            assert terminal["commit_error_codes"] == error_codes
            assert terminal["delivery_cancelled"] is True
            assert all(fields(record)["run_id"] == str(prepared.run.run_id)
                       for record in records)
            timeline = prepared.timeline
            assert (
                timeline.index("save_2_entered")
                < timeline.index("first_cancel_requested")
                < timeline.index("first_cancel_checkpoint")
                < timeline.index("repeat_cancel_requested")
                < timeline.index("repeat_cancel_checkpoint")
                < timeline.index("save_2_finished")
                < timeline.index(records[-2])
                < timeline.index(records[-1])
                < timeline.index("caller_cancelled")
            )
            assert timeline[-1] == "caller_cancelled"
        finally:
            await _drain_gated(context, caller)
