"""Real application concurrency over two SQLite persistence handles."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

import pytest

from exact_orb.application.application_results import (
    ApplicationAlreadyApplied,
    ApplicationCommitted,
    ApplicationResult,
    ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.composition import build_application_orchestrator
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.birth.types import BirthInput
from exact_orb.run_context import RunContext
from exact_orb.session.adapters.sqlite import SqliteSessionPersistence
from exact_orb.session.context import ContextService
from exact_orb.session.outcomes import (
    SessionAbsent,
    SessionCreated,
    SessionIdConflict,
    VersionConflict,
)
from exact_orb.session.persistence import SessionPersistence, SessionSnapshot
from exact_orb.session.state import SessionState, StateDelta
from exact_orb.session.store import SessionStore
from tests.fixtures.application import ApplicationTestStand, application_test_stand
from tests.fixtures.calculation import BASE_UTC, RUN_ID_B, run_context


SESSION_ID = "sqlite-application-cas-race"
RACE_TIMEOUT_SECONDS = 10
LIFECYCLE_EVENTS = {
    "application_operation_started",
    "application_stage_finished",
    "application_commit_attempt_finished",
    "application_operation_finished",
}


@dataclass(frozen=True)
class _CasCall:
    session_id: str
    expected_state_version: int
    delta: StateDelta
    now: datetime


class _RecordingSessionStore:
    """Record arguments and outcomes while delegating every call to SQLite."""

    def __init__(self, delegate: SessionStore) -> None:
        self._delegate = delegate
        self.calls: list[_CasCall] = []
        self.results: list[int | VersionConflict | SessionAbsent] = []

    async def create(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionCreated | SessionIdConflict:
        return await self._delegate.create(session_id, now=now)

    async def get(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionState | SessionAbsent:
        return await self._delegate.get(session_id, now=now)

    async def compare_and_set(
        self,
        session_id: str,
        expected_state_version: int,
        delta: StateDelta,
        *,
        now: datetime,
    ) -> int | VersionConflict | SessionAbsent:
        self.calls.append(_CasCall(session_id, expected_state_version, delta, now))
        result = await self._delegate.compare_and_set(
            session_id,
            expected_state_version,
            delta,
            now=now,
        )
        self.results.append(result)
        return result


class _LoadBarrierPersistence:
    """Release both real SQLite loads before either execute can reach Handler."""

    def __init__(self, delegate: SessionPersistence, barrier: asyncio.Barrier) -> None:
        self._delegate = delegate
        self._barrier = barrier
        self.sessions = _RecordingSessionStore(delegate.sessions)
        self.dialogs = delegate.dialogs
        self.touch_calls: list[tuple[str, datetime]] = []
        self.touch_results: list[SessionSnapshot | SessionAbsent] = []

    async def touch(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionSnapshot | SessionAbsent:
        self.touch_calls.append((session_id, now))
        result = await self._delegate.touch(session_id, now=now)
        self.touch_results.append(result)
        await self._barrier.wait()
        return result

    async def reset(
        self,
        session_id: str,
        expected_state_version: int,
        *,
        now: datetime,
    ) -> int | VersionConflict | SessionAbsent:
        return await self._delegate.reset(
            session_id,
            expected_state_version,
            now=now,
        )

    async def delete(self, session_id: str) -> None:
        await self._delegate.delete(session_id)


@dataclass(frozen=True)
class _SqliteApplicationPair:
    components: ApplicationTestStand
    primary: SqliteSessionPersistence
    left_persistence: _LoadBarrierPersistence
    right_persistence: _LoadBarrierPersistence
    left_orchestrator: ApplicationOrchestrator
    right_orchestrator: ApplicationOrchestrator


@asynccontextmanager
async def _sqlite_application_pair(path: Path) -> AsyncIterator[_SqliteApplicationPair]:
    with (
        application_test_stand() as components,
        ThreadPoolExecutor(max_workers=4) as sqlite_executor,
    ):
        primary = await SqliteSessionPersistence.open(
            path,
            executor=sqlite_executor,
        )
        peer = await SqliteSessionPersistence.open(
            path,
            executor=sqlite_executor,
        )
        barrier = asyncio.Barrier(2)
        left_persistence = _LoadBarrierPersistence(primary, barrier)
        right_persistence = _LoadBarrierPersistence(peer, barrier)
        left_context = ContextService(
            persistence=left_persistence,
            clock=components.clock,
        )
        right_context = ContextService(
            persistence=right_persistence,
            clock=components.clock,
        )
        yield _SqliteApplicationPair(
            components=components,
            primary=primary,
            left_persistence=left_persistence,
            right_persistence=right_persistence,
            left_orchestrator=build_application_orchestrator(
                context=left_context,
                clock=components.clock,
                resolver=components.resolver,
                artifacts=components.artifacts,
            ),
            right_orchestrator=build_application_orchestrator(
                context=right_context,
                clock=components.clock,
                resolver=components.resolver,
                artifacts=components.artifacts,
            ),
        )


def _command(
    *,
    birth_date: date = date(1990, 9, 2),
    birth_time: time = time(14, 30),
) -> BuildNatalCommand:
    return BuildNatalCommand(
        birth_input=BirthInput(
            birth_date=birth_date,
            birth_time=birth_time,
            place_id="524901",
        )
    )


async def _execute_race(
    pair: _SqliteApplicationPair,
    commands: tuple[BuildNatalCommand, BuildNatalCommand],
    runs: tuple[RunContext, RunContext],
) -> tuple[ApplicationResult, ApplicationResult]:
    return tuple(
        await asyncio.wait_for(
            asyncio.gather(
                pair.left_orchestrator.execute(
                    commands[0],
                    session_id=SESSION_ID,
                    run=runs[0],
                ),
                pair.right_orchestrator.execute(
                    commands[1],
                    session_id=SESSION_ID,
                    run=runs[1],
                ),
            ),
            timeout=RACE_TIMEOUT_SECONDS,
        )
    )  # type: ignore[return-value]


def _assert_real_race_inputs(pair: _SqliteApplicationPair) -> tuple[StateDelta, StateDelta]:
    wrappers = (pair.left_persistence, pair.right_persistence)
    for wrapper in wrappers:
        assert wrapper.touch_calls == [(SESSION_ID, BASE_UTC)]
        assert len(wrapper.touch_results) == 1
        snapshot = wrapper.touch_results[0]
        assert isinstance(snapshot, SessionSnapshot)
        assert snapshot.state.state_version == 0
        assert len(wrapper.sessions.calls) == 1
        call = wrapper.sessions.calls[0]
        assert call.session_id == SESSION_ID
        assert call.expected_state_version == 0
        assert call.now == BASE_UTC
        assert len(wrapper.sessions.results) == 1
    return (
        pair.left_persistence.sessions.calls[0].delta,
        pair.right_persistence.sessions.calls[0].delta,
    )


def _assert_store_outcomes(
    pair: _SqliteApplicationPair,
    stored: SessionState,
) -> None:
    outcomes = [
        *pair.left_persistence.sessions.results,
        *pair.right_persistence.sessions.results,
    ]
    committed = [outcome for outcome in outcomes if type(outcome) is int]
    conflicts = [outcome for outcome in outcomes if isinstance(outcome, VersionConflict)]
    assert committed == [1]
    assert len(conflicts) == 1
    assert conflicts[0].actual == stored


def _lifecycle(record: logging.LogRecord) -> tuple[str, dict[str, object]] | None:
    event, separator, payload = record.getMessage().partition(" ")
    if event not in LIFECYCLE_EVENTS:
        return None
    assert separator == " "
    return event, json.loads(payload)


def _assert_lifecycle_per_run(
    records: Sequence[logging.LogRecord],
    runs: tuple[RunContext, RunContext],
    results: tuple[ApplicationResult, ApplicationResult],
) -> None:
    lifecycle = [parsed for record in records if (parsed := _lifecycle(record)) is not None]
    for run, result in zip(runs, results, strict=True):
        correlated = [
            (event, fields)
            for event, fields in lifecycle
            if fields["run_id"] == str(run.run_id)
        ]
        assert [event for event, _ in correlated] == [
            "application_operation_started",
            "application_stage_finished",
            "application_stage_finished",
            "application_commit_attempt_finished",
            "application_operation_finished",
        ]
        stages = [fields for event, fields in correlated if event == "application_stage_finished"]
        assert [(fields["stage"], fields["outcome"]) for fields in stages] == [
            ("load", "loaded"),
            ("handler", "success"),
        ]
        attempt = next(
            fields
            for event, fields in correlated
            if event == "application_commit_attempt_finished"
        )
        expected_outcome = {
            ApplicationCommitted: "committed",
            ApplicationAlreadyApplied: "already_applied",
            ApplicationSuperseded: "superseded",
        }[type(result)]
        assert attempt["attempt"] == 1
        assert attempt["outcome"] == expected_outcome
        assert attempt["state_version"] == 1
        terminal = correlated[-1][1]
        assert terminal["context_status"] == result.context_status
        assert terminal["state_version"] == result.state_version
        assert terminal["commit_attempts"] == 1


async def test_same_intent_sqlite_cas_race_commits_once_and_reports_already_applied(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """N7: two real application requests apply one identical SQLite mutation."""
    commands = (_command(), _command())
    runs = (run_context(), run_context(RUN_ID_B))
    assert commands[0] == commands[1]
    assert commands[0] is not commands[1]

    async with _sqlite_application_pair(tmp_path / "same-intent.sqlite3") as pair:
        created = await pair.primary.sessions.create(SESSION_ID, now=BASE_UTC)
        assert isinstance(created, SessionCreated)
        assert created.state.state_version == 0
        caplog.set_level(logging.DEBUG, logger="exact_orb.application")
        caplog.clear()

        results = await _execute_race(pair, commands, runs)

        assert [result.run_id for result in results] == [run.run_id for run in runs]
        committed = [result for result in results if isinstance(result, ApplicationCommitted)]
        already_applied = [
            result for result in results if isinstance(result, ApplicationAlreadyApplied)
        ]
        assert len(committed) == len(already_applied) == 1
        assert committed[0].state_version == already_applied[0].state_version == 1
        assert (
            committed[0].artifact.calculation_key
            == already_applied[0].artifact.calculation_key
        )

        left_delta, right_delta = _assert_real_race_inputs(pair)
        assert left_delta == right_delta
        assert left_delta is not right_delta
        stored = await pair.primary.sessions.get(SESSION_ID, now=BASE_UTC)
        assert isinstance(stored, SessionState)
        assert stored.state_version == 1
        assert stored.birth_input == commands[0].birth_input
        assert stored.birth_resolved is not None
        assert stored.base_chart is not None
        assert stored.base_chart.state_version == 1
        assert stored.base_chart.spec == committed[0].artifact.spec
        _assert_store_outcomes(pair, stored)
        _assert_lifecycle_per_run(caplog.records, runs, results)


async def test_different_intent_sqlite_cas_race_preserves_winner_and_reports_superseded(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Different real application intents preserve the SQLite winner without rebase."""
    commands = (
        _command(),
        _command(birth_date=date(1990, 9, 3), birth_time=time(9, 15)),
    )
    runs = (run_context(), run_context(RUN_ID_B))
    assert commands[0] != commands[1]

    async with _sqlite_application_pair(tmp_path / "different-intent.sqlite3") as pair:
        created = await pair.primary.sessions.create(SESSION_ID, now=BASE_UTC)
        assert isinstance(created, SessionCreated)
        assert created.state.state_version == 0
        caplog.set_level(logging.DEBUG, logger="exact_orb.application")
        caplog.clear()

        results = await _execute_race(pair, commands, runs)

        assert [result.run_id for result in results] == [run.run_id for run in runs]
        committed = [result for result in results if isinstance(result, ApplicationCommitted)]
        superseded = [result for result in results if isinstance(result, ApplicationSuperseded)]
        assert len(committed) == len(superseded) == 1
        assert committed[0].state_version == superseded[0].state_version == 1
        assert not hasattr(superseded[0], "artifact")

        left_delta, right_delta = _assert_real_race_inputs(pair)
        assert left_delta != right_delta
        stored = await pair.primary.sessions.get(SESSION_ID, now=BASE_UTC)
        assert isinstance(stored, SessionState)
        winner = next(
            index
            for index, result in enumerate(results)
            if isinstance(result, ApplicationCommitted)
        )
        assert stored.state_version == 1
        assert stored.birth_input == commands[winner].birth_input
        assert stored.birth_resolved is not None
        assert stored.base_chart is not None
        assert stored.base_chart.state_version == 1
        assert stored.base_chart.spec == committed[0].artifact.spec
        _assert_store_outcomes(pair, stored)
        _assert_lifecycle_per_run(caplog.records, runs, results)
