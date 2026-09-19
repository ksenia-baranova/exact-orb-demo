"""Real application, Handler, calculation and session integration tests."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, time

import pytest

from exact_orb.application.application_results import (
    ApplicationAlreadyApplied,
    ApplicationCalculationFailure,
    ApplicationCommitted,
    ApplicationInputRequired,
    ApplicationResolutionFailure,
    ApplicationSessionAbsent,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.composition import build_application_orchestrator
from exact_orb.birth.places import LocalPlaceCatalog, ResolvedPlace
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.calculation.spec import ChartSpec
from exact_orb.calculation.types import ChartArtifact
from exact_orb.outcomes import Issue
from exact_orb.run_context import RunContext
from exact_orb.session.context import ContextService
from exact_orb.session.errors import StateWriteError
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


LOST_ACK_ERROR = "TEST_LOST_ACK_AFTER_APPLIED_CAS"


@dataclass(frozen=True)
class _CasCall:
    session_id: str
    expected_state_version: int
    delta: StateDelta
    now: datetime


class _LostAcknowledgementSessionStore:
    """Delegate real CAS, then lose exactly its first successful acknowledgement."""

    def __init__(self, delegate: SessionStore) -> None:
        self._delegate = delegate
        self._fault_armed = True
        self.calls: list[_CasCall] = []
        self.delegate_results: list[int | VersionConflict | SessionAbsent] = []

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
        self.delegate_results.append(result)
        if self._fault_armed:
            assert type(result) is int
            self._fault_armed = False
            raise StateWriteError(LOST_ACK_ERROR)
        return result


class _LostAcknowledgementPersistence:
    """Count aggregate reads while delegating every operation to real persistence."""

    def __init__(self, delegate: SessionPersistence) -> None:
        self._delegate = delegate
        self.sessions = _LostAcknowledgementSessionStore(delegate.sessions)
        self.dialogs = delegate.dialogs
        self.touch_calls: list[tuple[str, datetime]] = []

    async def touch(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionSnapshot | SessionAbsent:
        self.touch_calls.append((session_id, now))
        return await self._delegate.touch(session_id, now=now)

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


def _lifecycle_fields(record: logging.LogRecord) -> tuple[str, dict[str, object]]:
    event, separator, payload = record.getMessage().partition(" ")
    assert separator == " "
    return event, json.loads(payload)


def _command(
    *,
    birth_date: date = date(1990, 9, 2),
    birth_time: time | None = time(14, 30),
    place_id: str = "524901",
) -> BuildNatalCommand:
    return BuildNatalCommand(
        birth_input=BirthInput(
            birth_date=birth_date,
            birth_time=birth_time,
            place_id=place_id,
        )
    )


async def _create_session(stand: ApplicationTestStand, session_id: str) -> None:
    created = await stand.context.create(session_id)
    assert isinstance(created, SessionCreated)
    assert created.state.session_id == session_id
    assert created.state.state_version == 0


async def _load_snapshot(
    stand: ApplicationTestStand,
    session_id: str,
) -> SessionSnapshot:
    loaded = await stand.context.load(session_id)
    assert isinstance(loaded, SessionSnapshot)
    return loaded


async def test_real_natal_miss_then_hit_commits_two_session_states() -> None:
    command = _command()
    first_run = run_context()
    second_run = run_context(RUN_ID_B)

    with application_test_stand() as stand:
        await _create_session(stand, "natal-miss")
        first = await stand.orchestrator.execute(
            command,
            session_id="natal-miss",
            run=first_run,
        )

        assert isinstance(first, ApplicationCommitted)
        assert first.run_id == first_run.run_id
        assert first.state_version == 1
        assert first.artifact.chart.chart_kind == "natal"
        assert stand.artifacts.hits == 0
        assert stand.artifacts.misses == 1
        assert stand.artifacts.put_ok == 1

        first_snapshot = await _load_snapshot(stand, "natal-miss")
        assert first_snapshot.state.state_version == first.state_version
        assert first_snapshot.state.birth_input == command.birth_input
        assert first_snapshot.state.birth_resolved is not None
        assert first_snapshot.state.base_chart is not None
        assert first_snapshot.state.base_chart.state_version == first.state_version
        assert first_snapshot.state.base_chart.spec == first.artifact.spec

        await _create_session(stand, "natal-hit")
        second = await stand.orchestrator.execute(
            command,
            session_id="natal-hit",
            run=second_run,
        )

        assert isinstance(second, ApplicationCommitted)
        assert second.run_id == second_run.run_id
        assert second.state_version == 1
        assert second.artifact.calculation_key == first.artifact.calculation_key
        assert stand.artifacts.hits == 1
        assert stand.artifacts.misses == 1
        assert stand.artifacts.put_ok == 1
        assert len(stand.cache) == 1

        second_snapshot = await _load_snapshot(stand, "natal-hit")
        assert second_snapshot.state.state_version == second.state_version
        assert second_snapshot.state.birth_input == command.birth_input
        assert second_snapshot.state.base_chart is not None
        assert second_snapshot.state.base_chart.spec == second.artifact.spec


async def test_real_unknown_time_commits_cosmogram_state() -> None:
    command = _command(birth_time=None)
    run = run_context()

    with application_test_stand() as stand:
        await _create_session(stand, "cosmogram")
        result = await stand.orchestrator.execute(
            command,
            session_id="cosmogram",
            run=run,
        )

        assert isinstance(result, ApplicationCommitted)
        assert result.run_id == run.run_id
        assert result.state_version == 1
        assert result.artifact.spec.chart_kind == "cosmogram"
        assert result.artifact.chart.chart_kind == "cosmogram"
        assert result.artifact.chart.cusps is None
        assert result.artifact.chart.angles is None

        snapshot = await _load_snapshot(stand, "cosmogram")
        assert snapshot.state.state_version == result.state_version
        assert snapshot.state.birth_input is not None
        assert snapshot.state.birth_input.birth_time is None
        assert snapshot.state.birth_resolved is not None
        assert snapshot.state.birth_resolved.time_unknown is True
        assert snapshot.state.base_chart is not None
        assert snapshot.state.base_chart.spec == result.artifact.spec
        assert stand.artifacts.hits == 0
        assert stand.artifacts.misses == 1
        assert stand.artifacts.put_ok == 1


@pytest.mark.parametrize(
    ("place_id", "expected_type", "expected_detail"),
    [
        pytest.param("not-in-catalog", ApplicationInputRequired, None, id="input-required"),
        pytest.param(
            "9000001",
            ApplicationResolutionFailure,
            "UNKNOWN_TIMEZONE",
            id="resolution-unavailable",
        ),
    ],
)
async def test_real_resolution_non_success_does_not_save(
    place_id: str,
    expected_type: type[ApplicationInputRequired | ApplicationResolutionFailure],
    expected_detail: str | None,
) -> None:
    run = run_context()

    with application_test_stand() as stand:
        await _create_session(stand, "resolution-non-success")
        result = await stand.orchestrator.execute(
            _command(place_id=place_id),
            session_id="resolution-non-success",
            run=run,
        )

        assert isinstance(result, expected_type)
        assert result.run_id == run.run_id
        assert result.state_version == 0
        assert result.detail_code == expected_detail
        if isinstance(result, ApplicationInputRequired):
            assert result.issues == (Issue(field="birth.place", code="INVALID"),)
            assert result.user_message == (
                "Проверьте введённые данные и исправьте отмеченные поля."
            )
        else:
            assert result.retryable is False
            assert result.user_message == (
                "Не удалось определить данные места и времени для указанного ввода."
            )

        snapshot = await _load_snapshot(stand, "resolution-non-success")
        assert snapshot.state.state_version == 0
        assert snapshot.state.birth_input is None
        assert snapshot.state.birth_resolved is None
        assert snapshot.state.base_chart is None
        assert stand.artifacts.hits == 0
        assert stand.artifacts.misses == 0
        assert stand.artifacts.put_ok == 0
        assert len(stand.cache) == 0


async def test_real_calculation_failure_does_not_save_or_cache() -> None:
    polar_catalog = LocalPlaceCatalog(
        {
            "polar": ResolvedPlace(
                place_id="polar",
                canonical_name="Longyearbyen",
                latitude=78.2232,
                longitude=15.6469,
                tz_id="Arctic/Longyearbyen",
            )
        }
    )
    command = _command(
        birth_date=date(1985, 9, 1),
        birth_time=time(22, 45),
        place_id="polar",
    )
    run = run_context()

    with application_test_stand(places=polar_catalog) as stand:
        await _create_session(stand, "calculation-failure")
        result = await stand.orchestrator.execute(
            command,
            session_id="calculation-failure",
            run=run,
        )

        assert isinstance(result, ApplicationCalculationFailure)
        assert result.detail_code == "HOUSES_DEGENERATE"
        assert result.retryable is False
        assert result.user_message == (
            "Для выбранных данных невозможно рассчитать дома в текущей системе домов."
        )
        assert result.run_id == run.run_id
        assert result.state_version == 0

        snapshot = await _load_snapshot(stand, "calculation-failure")
        assert snapshot.state.state_version == 0
        assert snapshot.state.birth_input is None
        assert snapshot.state.birth_resolved is None
        assert snapshot.state.base_chart is None
        assert stand.artifacts.hits == 0
        assert stand.artifacts.misses == 1
        assert stand.artifacts.put_ok == 0
        assert len(stand.cache) == 0


async def test_missing_session_stops_before_handler_and_calculation() -> None:
    run = run_context()

    with application_test_stand() as stand:
        result = await stand.orchestrator.execute(
            _command(),
            session_id="missing-session",
            run=run,
        )

        assert isinstance(result, ApplicationSessionAbsent)
        assert result.handler_status == "NOT_STARTED"
        assert result.context_status == "SESSION_ABSENT"
        assert result.code == "SESSION_NOT_FOUND"
        assert result.reason == "not_found"
        assert result.run_id == run.run_id
        assert result.state_version is None
        assert stand.artifacts.hits == 0
        assert stand.artifacts.misses == 0
        assert stand.artifacts.put_ok == 0
        assert len(stand.cache) == 0


async def test_session_deleted_after_real_handler_is_reported_as_lost() -> None:
    session_id = "lost-before-commit"
    run = run_context()

    with application_test_stand() as stand:
        await _create_session(stand, session_id)

        class DeletingArtifactPort:
            async def ensure_chart(
                self,
                spec: ChartSpec,
                resolved: ResolvedBirthData,
                *,
                run: RunContext,
            ) -> ChartArtifact:
                artifact = await stand.artifacts.ensure_chart(spec, resolved, run=run)
                await stand.persistence.delete(session_id)
                return artifact

        orchestrator = build_application_orchestrator(
            context=stand.context,
            clock=stand.clock,
            resolver=stand.resolver,
            artifacts=DeletingArtifactPort(),
        )
        result = await orchestrator.execute(
            _command(),
            session_id=session_id,
            run=run,
        )

        assert isinstance(result, ApplicationSessionAbsent)
        assert result.handler_status == "SUCCESS"
        assert result.context_status == "SESSION_ABSENT"
        assert result.code == "SESSION_LOST_DURING_OPERATION"
        assert result.reason == "not_found"
        assert result.run_id == run.run_id
        assert result.state_version is None
        assert stand.artifacts.hits == 0
        assert stand.artifacts.misses == 1
        assert stand.artifacts.put_ok == 1
        assert len(stand.cache) == 1
        assert await stand.context.load(session_id) == SessionAbsent(reason="not_found")


async def test_lost_ack_after_applied_cas_retries_without_second_mutation(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A real applied CAS survives one lost acknowledgement and one exact retry."""
    session_id = "lost-applied-cas-ack"
    command = _command()
    run = run_context()

    with application_test_stand() as stand:
        await _create_session(stand, session_id)
        persistence = _LostAcknowledgementPersistence(stand.persistence)
        context = ContextService(persistence=persistence, clock=stand.clock)
        orchestrator = build_application_orchestrator(
            context=context,
            clock=stand.clock,
            resolver=stand.resolver,
            artifacts=stand.artifacts,
        )
        caplog.set_level(logging.DEBUG, logger="exact_orb.application")
        caplog.clear()

        result = await orchestrator.execute(
            command,
            session_id=session_id,
            run=run,
        )

        assert isinstance(result, ApplicationAlreadyApplied)
        assert result.context_status == "ALREADY_APPLIED"
        assert result.run_id == run.run_id
        assert result.state_version == 1
        assert result.artifact.chart.chart_kind == "natal"

        assert persistence.touch_calls == [(session_id, BASE_UTC)]
        assert len(persistence.sessions.calls) == 2
        first_call, second_call = persistence.sessions.calls
        assert first_call.session_id == second_call.session_id == session_id
        assert first_call.expected_state_version == second_call.expected_state_version == 0
        assert first_call.delta is second_call.delta
        assert first_call.now == second_call.now == BASE_UTC

        first_delegate_result, second_delegate_result = persistence.sessions.delegate_results
        assert first_delegate_result == 1
        assert isinstance(second_delegate_result, VersionConflict)
        assert second_delegate_result.actual.state_version == 1
        assert second_delegate_result.actual.birth_input == command.birth_input
        assert second_delegate_result.actual.base_chart is not None
        assert second_delegate_result.actual.base_chart.spec == result.artifact.spec
        assert stand.artifacts.hits == 0
        assert stand.artifacts.misses == 1
        assert stand.artifacts.put_ok == 1

        persisted = await stand.persistence.sessions.get(session_id, now=BASE_UTC)
        assert isinstance(persisted, SessionState)
        assert persisted.state_version == 1
        assert persisted.birth_input == command.birth_input
        assert persisted.birth_resolved is not None
        assert persisted.base_chart is not None
        assert persisted.base_chart.state_version == 1
        assert persisted.base_chart.spec == result.artifact.spec

        lifecycle = [
            _lifecycle_fields(record)
            for record in caplog.records
            if record.getMessage().partition(" ")[0]
            in {
                "application_operation_started",
                "application_stage_finished",
                "application_commit_attempt_finished",
                "application_operation_finished",
            }
        ]
        assert [event for event, _ in lifecycle] == [
            "application_operation_started",
            "application_stage_finished",
            "application_stage_finished",
            "application_commit_attempt_finished",
            "application_commit_attempt_finished",
            "application_operation_finished",
        ]
        stages = [fields for event, fields in lifecycle if event == "application_stage_finished"]
        assert [(stage["stage"], stage["outcome"]) for stage in stages] == [
            ("load", "loaded"),
            ("handler", "success"),
        ]
        attempts = [
            fields
            for event, fields in lifecycle
            if event == "application_commit_attempt_finished"
        ]
        assert [(attempt["attempt"], attempt["outcome"]) for attempt in attempts] == [
            (1, "state_commit_failed"),
            (2, "already_applied"),
        ]
        assert attempts[0]["detail_code"] == LOST_ACK_ERROR
        assert "state_version" not in attempts[0]
        assert attempts[1]["detail_code"] is None
        assert attempts[1]["state_version"] == 1
        terminal = lifecycle[-1][1]
        assert terminal["terminal_kind"] == "result"
        assert terminal["run_id"] == str(run.run_id)
        assert terminal["context_status"] == "ALREADY_APPLIED"
        assert terminal["state_version"] == 1
        assert terminal["commit_attempts"] == 2
        assert terminal["commit_error_codes"] == [LOST_ACK_ERROR]
