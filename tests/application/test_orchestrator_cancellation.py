"""Cancellation after save entry through the real ApplicationOrchestrator."""

from __future__ import annotations

import asyncio
import logging

import pytest

from exact_orb.application.application_results import ApplicationResult
from tests.application.test_orchestrator_commit import (
    EVENTS,
    SESSION_ID,
    assert_calls,
    assert_lifecycle,
    await_save_entry,
    capture_lifecycle,
    drain_case,
    lifecycle,
    make_case,
)


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
