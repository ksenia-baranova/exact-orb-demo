"""FR-24 / AC-28: overlapping requests through one ApplicationOrchestrator."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

import pytest

from exact_orb.application.application_results import (
    ApplicationCommitted,
    ApplicationResult,
    ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand, Command
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.results import BuildNatalSuccess
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.run_context import RunContext
from exact_orb.session.outcomes import Committed, Superseded
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import SessionState, StateDelta, new_session
from tests.application.orchestrator_fakes import Call
from tests.application.test_orchestrator_commit import (
    EVENTS,
    capture_lifecycle,
    fields,
    lifecycle,
)
from tests.fixtures.calculation import artifact, chart_spec, resolved_birth_data
from tests.fixtures.telemetry import RUN_ID, RUN_ID_B, STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit


class _MarkedBuildNatalCommand(BuildNatalCommand):
    marker: str


@dataclass(frozen=True)
class _Operation:
    marker: str
    session_id: str
    command: _MarkedBuildNatalCommand
    run: RunContext
    snapshot: SessionSnapshot
    outcome: BuildNatalSuccess


def _operation(
    *, marker: str, session_id: str, loaded_version: int, run_id: UUID,
    latitude: float, longitude: float, place_id: str,
    snapshot: SessionSnapshot | None = None,
) -> _Operation:
    """Make different valid commands, chart artifacts and deltas without ephemeris."""
    resolved_fixture = resolved_birth_data(
        latitude=latitude, longitude=longitude, canonical_place=marker,
    )
    resolved = ResolvedBirthData.model_validate({
        **resolved_fixture.model_dump(),
        "utc_datetime": resolved_fixture.utc_datetime.replace(second=0, microsecond=0),
    })
    local_birth = resolved.utc_datetime + timedelta(seconds=resolved.utc_offset_seconds)
    birth_input = BirthInput(
        birth_date=local_birth.date(),
        birth_time=local_birth.time().replace(tzinfo=None),
        place_id=place_id,
    )
    spec = chart_spec()
    outcome = BuildNatalSuccess(
        artifact=artifact(spec=spec, resolved=resolved),
        delta=StateDelta(
            birth_input=birth_input, birth_resolved=resolved, base_chart_spec=spec,
        ),
    )
    if snapshot is None:
        state = SessionState.model_validate({
            **new_session(session_id, now=STARTED_AT).model_dump(),
            "state_version": loaded_version,
        })
        snapshot = SessionSnapshot(state=state, dialog=())
    assert snapshot.state.session_id == session_id
    assert snapshot.state.state_version == loaded_version
    return _Operation(
        marker=marker, session_id=session_id,
        command=_MarkedBuildNatalCommand(birth_input=birth_input, marker=marker),
        run=RunContext(run_id=run_id, started_at=STARTED_AT),
        snapshot=snapshot, outcome=outcome,
    )


class _BarrierContext:
    """Hold both loads and both saves so overlap is directly observable."""

    def __init__(
        self, operations: tuple[_Operation, _Operation],
        outcomes: dict[str, Committed | Superseded],
        journal: list[Call], timeline: list[object],
    ) -> None:
        self.operations = operations
        self.outcomes = outcomes
        self.journal = journal
        self.timeline = timeline
        self.snapshots = {op.session_id: op.snapshot for op in operations}
        self.loads_entered = 0
        self.both_loads_entered = asyncio.Event()
        self.release_loads = asyncio.Event()
        self.save_entered = {op.marker: asyncio.Event() for op in operations}
        self.release_save = {op.marker: asyncio.Event() for op in operations}
        self.both_saves_entered = asyncio.Event()
        self.save_markers: set[str] = set()

    async def load(self, session_id: str) -> SessionSnapshot:
        self.journal.append(Call(self, "load", (session_id,)))
        self.loads_entered += 1
        if self.loads_entered == 2:
            self.both_loads_entered.set()
        await self.release_loads.wait()
        return self.snapshots[session_id]

    async def save(
        self, session_id: str, expected_state_version: int, delta: StateDelta,
    ) -> Committed | Superseded:
        self.journal.append(Call(self, "save", (session_id, expected_state_version, delta)))
        matches = [op for op in self.operations if delta is op.outcome.delta]
        assert len(matches) == 1, "save must receive one operation's original delta"
        marker = matches[0].marker
        assert marker not in self.save_markers, "duplicate save for one operation"
        self.save_markers.add(marker)
        self.timeline.append(f"save_{marker}_entered")
        self.save_entered[marker].set()
        if len(self.save_markers) == 2:
            self.both_saves_entered.set()
        await self.release_save[marker].wait()
        self.timeline.append(f"save_{marker}_finished")
        return self.outcomes[marker]


class _BarrierHandler:
    def __init__(
        self, operations: tuple[_Operation, _Operation],
        journal: list[Call], timeline: list[object],
    ) -> None:
        self.operations = {op.marker: op for op in operations}
        self.journal = journal
        self.timeline = timeline
        self.entered = {marker: asyncio.Event() for marker in self.operations}
        self.release = {marker: asyncio.Event() for marker in self.operations}

    async def handle(
        self, command: Command, state: SessionState, run: RunContext,
    ) -> BuildNatalSuccess:
        assert isinstance(command, _MarkedBuildNatalCommand)
        self.journal.append(Call(self, "handle", (command, state, run)))
        marker = command.marker
        self.timeline.append(f"handler_{marker}_entered")
        self.entered[marker].set()
        await self.release[marker].wait()
        return self.operations[marker].outcome


@dataclass
class _Flow:
    operations: tuple[_Operation, _Operation]
    context: _BarrierContext
    handler: _BarrierHandler
    orchestrator: ApplicationOrchestrator
    journal: list[Call]
    timeline: list[object]


def _flow(
    *, same_session: bool,
) -> _Flow:
    session_a = "parallel-session-a" if not same_session else "contended-session"
    session_b = "parallel-session-b" if not same_session else session_a
    left = _operation(
        marker="a", session_id=session_a, loaded_version=7, run_id=RUN_ID,
        latitude=55.75, longitude=37.62, place_id="moscow-ru",
    )
    right = _operation(
        marker="b", session_id=session_b,
        loaded_version=7 if same_session else 13, run_id=RUN_ID_B,
        latitude=59.93, longitude=30.31, place_id="spb-ru",
        snapshot=left.snapshot if same_session else None,
    )
    operations = (left, right)
    assert left.command != right.command
    assert left.outcome.delta is not right.outcome.delta
    assert left.outcome.delta != right.outcome.delta
    assert left.outcome.artifact.calculation_key != right.outcome.artifact.calculation_key
    journal: list[Call] = []
    timeline: list[object] = []
    outcomes: dict[str, Committed | Superseded] = {
        "a": Committed(state_version=8),
        "b": (
            Superseded(actual=SessionState.model_validate({
                **new_session(session_b, now=STARTED_AT).model_dump(),
                "state_version": 8,
            }))
            if same_session else Committed(state_version=14)
        ),
    }
    context = _BarrierContext(operations, outcomes, journal, timeline)
    handler = _BarrierHandler(operations, journal, timeline)
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={_MarkedBuildNatalCommand: handler},
        clock=lambda: STARTED_AT,
    )
    return _Flow(operations, context, handler, orchestrator, journal, timeline)


async def _invoke(flow: _Flow, operation: _Operation) -> ApplicationResult:
    result = await flow.orchestrator.execute(
        operation.command, session_id=operation.session_id, run=operation.run,
    )
    flow.timeline.append(f"caller_{operation.marker}_returned")
    return result


async def _drain(flow: _Flow, tasks: tuple[asyncio.Task[ApplicationResult], ...]) -> None:
    flow.context.release_loads.set()
    for event in (*flow.handler.release.values(), *flow.context.release_save.values()):
        event.set()
    for task in tasks:
        if not task.done():
            with suppress(Exception, asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=2)


def _assert_calls(flow: _Flow) -> None:
    assert [call.method for call in flow.journal].count("load") == 2
    assert [call.method for call in flow.journal].count("handle") == 2
    assert [call.method for call in flow.journal].count("save") == 2
    for op in flow.operations:
        handle_calls = [
            call for call in flow.journal
            if call.method == "handle" and call.args[0] is op.command
        ]
        assert len(handle_calls) == 1
        assert handle_calls[0].target is flow.handler
        assert handle_calls[0].args[1] is op.snapshot.state
        assert handle_calls[0].args[2] is op.run
        save_calls = [
            call for call in flow.journal
            if call.method == "save" and call.args[2] is op.outcome.delta
        ]
        assert len(save_calls) == 1
        assert save_calls[0].target is flow.context
        assert save_calls[0].args[:2] == (op.session_id, op.snapshot.state.state_version)
        assert sum(
            call.method == "load" and call.args == (op.session_id,)
            for call in flow.journal
        ) == (2 if flow.operations[0].session_id == flow.operations[1].session_id else 1)


def _assert_result_and_events(
    flow: _Flow, op: _Operation, result: ApplicationResult,
) -> None:
    assert result.run_id == op.run.run_id
    per_run = [
        record for record in lifecycle(flow.timeline)
        if fields(record)["run_id"] == str(op.run.run_id)
    ]
    assert [record.getMessage().partition(" ")[0] for record in per_run] == [
        EVENTS[0], EVENTS[1], EVENTS[1], EVENTS[2], EVENTS[3],
    ]
    started, loaded, handled, attempt, terminal = map(fields, per_run)
    assert started == {
        "run_id": str(op.run.run_id), "command_type": "_MarkedBuildNatalCommand",
    }
    assert loaded["stage"] == "load" and loaded["outcome"] == "loaded"
    assert loaded["state_version"] == op.snapshot.state.state_version
    assert handled["stage"] == "handler" and handled["outcome"] == "success"
    assert handled["state_version"] == op.snapshot.state.state_version
    assert attempt["attempt"] == 1
    assert attempt["detail_code"] is None
    assert terminal["terminal_kind"] == "result"
    assert terminal["run_id"] == str(op.run.run_id)
    assert terminal["code"] == result.code
    assert terminal["state_version"] == result.state_version
    assert terminal["commit_attempts"] == 1
    assert terminal["commit_error_codes"] == []
    assert terminal["delivery_cancelled"] is False
    if isinstance(result, ApplicationCommitted):
        assert result.code == "OK"
        assert result.artifact == op.outcome.artifact
        assert attempt["outcome"] == "committed"
        assert attempt["state_version"] == result.state_version
    else:
        assert isinstance(result, ApplicationSuperseded)
        assert result.code == "RESULT_SUPERSEDED"
        assert not hasattr(result, "artifact")
        assert attempt["outcome"] == "superseded"
        assert attempt["state_version"] == result.state_version
    assert flow.timeline.index(f"save_{op.marker}_finished") < flow.timeline.index(
        per_run[3]
    ) < flow.timeline.index(per_run[4]) < flow.timeline.index(
        f"caller_{op.marker}_returned"
    )


async def test_two_sessions_overlap_without_mixing_request_state(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-24 / AC-28: one Orchestrator preserves two distinct request frames."""
    flow = _flow(same_session=False)
    left, right = flow.operations
    with capture_lifecycle(caplog, flow.timeline):
        tasks = (
            asyncio.create_task(_invoke(flow, left)),
            asyncio.create_task(_invoke(flow, right)),
        )
        try:
            await asyncio.wait_for(flow.context.both_loads_entered.wait(), timeout=2)
            assert all(not task.done() for task in tasks)
            assert not any(call.method == "handle" for call in flow.journal)
            flow.context.release_loads.set()
            await asyncio.wait_for(flow.handler.entered["a"].wait(), timeout=2)
            await asyncio.wait_for(flow.handler.entered["b"].wait(), timeout=2)
            assert all(not task.done() for task in tasks)
            flow.handler.release["a"].set()
            await asyncio.wait_for(flow.context.save_entered["a"].wait(), timeout=2)
            assert not flow.handler.release["b"].is_set()
            flow.handler.release["b"].set()
            await asyncio.wait_for(flow.context.both_saves_entered.wait(), timeout=2)
            assert flow.context.save_markers == {"a", "b"}
            assert all(not task.done() for task in tasks)
            assert not any(
                record.getMessage().startswith(EVENTS[3] + " ")
                for record in lifecycle(flow.timeline)
            )

            flow.context.release_save["b"].set()
            right_result = await asyncio.wait_for(tasks[1], timeout=2)
            assert not tasks[0].done()
            assert not flow.context.release_save["a"].is_set()
            assert isinstance(right_result, ApplicationCommitted)
            assert right_result.state_version == 14
            flow.context.release_save["a"].set()
            left_result = await asyncio.wait_for(tasks[0], timeout=2)
            assert isinstance(left_result, ApplicationCommitted)
            assert left_result.state_version == 8
            assert left_result.artifact.calculation_key != right_result.artifact.calculation_key
            _assert_calls(flow)
            _assert_result_and_events(flow, left, left_result)
            _assert_result_and_events(flow, right, right_result)
        finally:
            await _drain(flow, tasks)


async def test_same_session_race_keeps_distinct_intents_and_results(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """FR-24 / AC-28: same expected version, separate deltas and typed outcomes."""
    flow = _flow(same_session=True)
    left, right = flow.operations
    assert left.snapshot is right.snapshot
    assert left.session_id == right.session_id
    with capture_lifecycle(caplog, flow.timeline):
        tasks = (
            asyncio.create_task(_invoke(flow, left)),
            asyncio.create_task(_invoke(flow, right)),
        )
        try:
            await asyncio.wait_for(flow.context.both_loads_entered.wait(), timeout=2)
            assert all(not task.done() for task in tasks)
            flow.context.release_loads.set()
            await asyncio.wait_for(flow.handler.entered["a"].wait(), timeout=2)
            await asyncio.wait_for(flow.handler.entered["b"].wait(), timeout=2)
            flow.handler.release["a"].set()
            flow.handler.release["b"].set()
            await asyncio.wait_for(flow.context.both_saves_entered.wait(), timeout=2)
            assert flow.context.save_markers == {"a", "b"}
            assert all(not task.done() for task in tasks)
            flow.context.release_save["a"].set()
            left_result = await asyncio.wait_for(tasks[0], timeout=2)
            assert isinstance(left_result, ApplicationCommitted)
            assert left_result.state_version == 8
            assert not tasks[1].done()
            flow.context.release_save["b"].set()
            right_result = await asyncio.wait_for(tasks[1], timeout=2)
            assert isinstance(right_result, ApplicationSuperseded)
            assert right_result.state_version == 8
            _assert_calls(flow)
            _assert_result_and_events(flow, left, left_result)
            _assert_result_and_events(flow, right, right_result)
        finally:
            await _drain(flow, tasks)
