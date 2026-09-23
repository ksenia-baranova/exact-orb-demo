"""End-to-end acceptance for the process-local application runtime."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timezone
import json
import logging
from pathlib import Path
import threading
from typing import Any

import pytest

from exact_orb.application.application_results import ApplicationCommitted
from exact_orb.application.bootstrap import (
    ApplicationRuntime,
    BootstrapSettings,
    build_application_runtime,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.birth.places import LocalPlaceCatalog
from exact_orb.birth.types import BirthInput
from exact_orb.config import get_ephemeris_status, get_selena_method_name
from exact_orb.engine.charts.natal import NatalChart
from exact_orb.session.outcomes import SessionCreated
from exact_orb.session.persistence import SessionSnapshot
from tests.fixtures.calculation import RUN_ID_B, raw_chart, run_context


pytestmark = pytest.mark.asyncio

PLACES_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "places.jsonl"
FIXED_NOW = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)


def _clock() -> datetime:
    return FIXED_NOW


def _settings(tmp_path: Path, *, db_name: str) -> BootstrapSettings:
    status = get_ephemeris_status()
    return BootstrapSettings(
        ephemeris_path=Path(status.path),
        selena_method=get_selena_method_name(),
        session_db_path=tmp_path / db_name,
        sqlite_busy_timeout_ms=250,
        sqlite_max_workers=1,
        min_birth_date=date(1800, 1, 1),
        max_birth_date=date(2399, 12, 31),
        cache_max_entries=32,
        cache_ttl_seconds=None,
        engine_slow_threshold_ms=3_000.0,
        degraded_log_interval_s=60.0,
    )


def _command() -> BuildNatalCommand:
    return BuildNatalCommand(
        birth_input=BirthInput(
            birth_date=date(1990, 9, 2),
            birth_time=time(14, 30),
            place_id="524901",
        )
    )


async def _create_session(runtime: ApplicationRuntime, session_id: str) -> None:
    created = await runtime.context.create(session_id)
    assert isinstance(created, SessionCreated)
    assert created.state.session_id == session_id
    assert created.state.state_version == 0


class _BlockingNatalCalculator:
    """Synchronous calculator held in the real calculation executor."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self.entered = asyncio.Event()
        self.release = threading.Event()
        self.finished = threading.Event()
        self.calls = 0
        self.thread_ids: list[int] = []

    def __call__(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        **kwargs: Any,
    ) -> NatalChart:
        self.calls += 1
        self.thread_ids.append(threading.get_ident())
        self._loop.call_soon_threadsafe(self.entered.set)
        if not self.release.wait(timeout=5.0):
            raise TimeoutError("test calculator barrier was not released")
        try:
            return raw_chart(
                chart_kind=kwargs["chart_kind"],
                utc_datetime=birth_datetime,
                latitude=latitude,
                longitude=longitude,
                house_system=kwargs["house_system"],
                include=tuple(kwargs["include"]),
                birth_time_domain=kwargs["birth_time_domain"],
            )
        finally:
            self.finished.set()


async def test_runtime_build_natal_miss_then_hit_commits_same_session(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="exact_orb.application.orchestrator")
    caplog.set_level(logging.DEBUG, logger="exact_orb.application.handlers.build_natal")
    caplog.set_level(logging.DEBUG, logger="exact_orb.session.context")
    caplog.set_level(logging.DEBUG, logger="exact_orb.calculation")
    caplog.set_level(logging.DEBUG, logger="exact_orb.engine.charts.natal")
    runtime = await build_application_runtime(
        settings=_settings(tmp_path, db_name="build-natal.sqlite3"),
        places=LocalPlaceCatalog.from_file(PLACES_PATH),
        clock=_clock,
    )
    session_id = "runtime-build-natal"
    command = _command()
    first_run = run_context()
    second_run = run_context(RUN_ID_B)

    try:
        await _create_session(runtime, session_id)

        first = await runtime.orchestrator.execute(
            command,
            session_id=session_id,
            run=first_run,
        )

        assert isinstance(first, ApplicationCommitted)
        assert first.run_id == first_run.run_id
        assert first.state_version == 1
        assert first.artifact.calculation_version == runtime.calculation_version
        assert first.artifact.chart.chart_kind == "natal"
        assert runtime.artifacts.hits == 0
        assert runtime.artifacts.misses == 1
        assert runtime.artifacts.put_ok == 1

        second = await runtime.orchestrator.execute(
            command,
            session_id=session_id,
            run=second_run,
        )

        assert isinstance(second, ApplicationCommitted)
        assert second.run_id == second_run.run_id
        assert second.state_version == 2
        assert second.artifact.calculation_key == first.artifact.calculation_key
        assert second.artifact.calculation_version == first.artifact.calculation_version
        assert runtime.artifacts.hits == 1
        assert runtime.artifacts.misses == 1
        assert runtime.artifacts.put_ok == 1

        messages = [record.getMessage() for record in caplog.records]
        for run_number, run in enumerate((first_run, second_run)):
            correlated = [
                (index, message) for index, message in enumerate(messages)
                if f"run_id={run.run_id} " in message
            ]
            exchanges = [
                (index, message) for index, message in correlated
                if message.startswith("application_message ")
                and caplog.records[index].name == "exact_orb.application.orchestrator"
            ]
            assert [message for _, message in exchanges] == [
                f"application_message direction=send run_id={run.run_id} "
                "peer=ContextService operation=load message_type=ContextLoadRequest attempt=-",
                f"application_message direction=receive run_id={run.run_id} "
                "peer=ContextService operation=load message_type=SessionSnapshot attempt=-",
                f"application_message direction=send run_id={run.run_id} "
                "peer=BuildNatalHandler operation=handle message_type=BuildNatalRequest attempt=-",
                f"application_message direction=receive run_id={run.run_id} "
                "peer=BuildNatalHandler operation=handle message_type=BuildNatalSuccess attempt=-",
                f"application_message direction=send run_id={run.run_id} "
                "peer=ContextService operation=save message_type=ContextSaveRequest attempt=1",
                f"application_message direction=receive run_id={run.run_id} "
                "peer=ContextService operation=save message_type=Committed attempt=1",
            ]
            assert all(caplog.records[index].levelno == logging.INFO for index, _ in exchanges)
            handler_exchanges = [
                (index, message) for index, message in correlated
                if message.startswith("application_message ")
                and caplog.records[index].name == "exact_orb.application.handlers.build_natal"
            ]
            assert [message for _, message in handler_exchanges] == [
                f"application_message direction=send run_id={run.run_id} "
                "peer=BirthDataResolver operation=resolve_birth_data "
                "message_type=BirthResolutionRequest attempt=-",
                f"application_message direction=receive run_id={run.run_id} "
                "peer=BirthDataResolver operation=resolve_birth_data "
                "message_type=ResolvedBirthData attempt=-",
                f"application_message direction=send run_id={run.run_id} "
                "peer=ChartArtifactResolver operation=ensure_chart "
                "message_type=EnsureChartRequest attempt=-",
                f"application_message direction=receive run_id={run.run_id} "
                "peer=ChartArtifactResolver operation=ensure_chart "
                "message_type=ChartArtifact attempt=-",
            ]
            assert all(
                caplog.records[index].levelno == logging.INFO
                for index, _ in handler_exchanges
            )
            calculation_exchanges = [
                (index, message)
                for index, message in enumerate(messages)
                if handler_exchanges[2][0] < index < handler_exchanges[3][0]
                and message.startswith("calculation_message ")
            ]
            if run_number == 0:
                key = first.artifact.calculation_key
                assert [message for _, message in calculation_exchanges] == [
                    f"calculation_message direction=send run_id={run.run_id} "
                    "sender=ChartArtifactResolver peer=EngineService "
                    f"operation=calculate_chart message_type=CalculationRequest calculation_key={key}",
                    f"calculation_message direction=send run_id={run.run_id} "
                    "sender=EngineService peer=NatalTechniqueAdapter "
                    "operation=calculate message_type=TechniqueCalculationRequest "
                    "calculation_key=-",
                    "calculation_message direction=send run_id=- "
                    "sender=NatalTechniqueAdapter peer=calculate_natal "
                    "operation=calculate_natal message_type=NatalCalculationRequest "
                    "calculation_key=-",
                    "calculation_message direction=receive run_id=- "
                    "sender=NatalTechniqueAdapter peer=calculate_natal "
                    "operation=calculate_natal message_type=NatalChart calculation_key=-",
                    f"calculation_message direction=receive run_id={run.run_id} "
                    "sender=EngineService peer=NatalTechniqueAdapter "
                    "operation=calculate message_type=CalculationResult calculation_key=-",
                    f"calculation_message direction=receive run_id={run.run_id} "
                    "sender=ChartArtifactResolver peer=EngineService "
                    f"operation=calculate_chart message_type=CalculationResult calculation_key={key}",
                ]
                assert all(
                    caplog.records[index].levelno == logging.INFO
                    for index, _ in calculation_exchanges
                )
                engine_input = next(
                    index for index, message in enumerate(messages)
                    if "component_message direction=in operation=calculate_chart " in message
                )
                natal_input = next(
                    index for index, message in enumerate(messages)
                    if "component_message direction=in operation=calculate_natal " in message
                )
                assert calculation_exchanges[0][0] < engine_input
                assert calculation_exchanges[2][0] < natal_input < calculation_exchanges[3][0]
            else:
                assert calculation_exchanges == []
            input_index, input_message = next(
                (index, message) for index, message in correlated
                if "component_message direction=in operation=application_execute " in message
            )
            handler_index, _ = next(
                (index, message) for index, message in correlated
                if "component_message direction=in operation=build_natal " in message
            )
            handler_output_index, _ = next(
                (index, message) for index, message in correlated
                if "component_message direction=out operation=build_natal " in message
            )
            assert input_index < exchanges[0][0] < exchanges[1][0]
            assert exchanges[2][0] < handler_index < handler_output_index < exchanges[3][0]
            assert exchanges[3][0] < exchanges[4][0] < exchanges[5][0]
            assert handler_index < handler_exchanges[0][0]
            assert handler_exchanges[0][0] < handler_exchanges[1][0]
            assert handler_exchanges[1][0] < handler_exchanges[2][0]
            assert handler_exchanges[2][0] < handler_exchanges[3][0]
            assert handler_exchanges[3][0] < handler_output_index

            context_records = [
                (index, message) for index, message in enumerate(messages)
                if caplog.records[index].name == "exact_orb.session.context"
            ]
            for operation, send_index, receive_index, expected_type in (
                ("load", exchanges[0][0], exchanges[1][0], "SessionSnapshot"),
                ("save", exchanges[4][0], exchanges[5][0], "Committed"),
            ):
                inputs = [
                    (index, message) for index, message in context_records
                    if f"direction=in operation=context_{operation} " in message
                ]
                outputs = [
                    (index, message) for index, message in context_records
                    if f"direction=out operation=context_{operation} " in message
                ]
                assert len(inputs) == len(outputs) == 2
                assert send_index < inputs[run_number][0] < outputs[run_number][0]
                assert outputs[run_number][0] < receive_index
                assert f"message_type={expected_type}" in outputs[run_number][1]
            assert "message_type=ApplicationExecuteRequest" in input_message
            assert json.loads(input_message.split(" message=", 1)[1]) == {
                "command_type": "BuildNatalCommand",
                "command": command.model_dump(mode="json"),
                "session_id": session_id,
                "run": run.model_dump(mode="json"),
            }

        loaded = await runtime.context.load(session_id)
        assert isinstance(loaded, SessionSnapshot)
        assert loaded.state.state_version == 2
        assert loaded.state.birth_input == command.birth_input
        assert loaded.state.birth_resolved is not None
        assert loaded.state.base_chart is not None
        assert loaded.state.base_chart.state_version == 2
        assert loaded.state.base_chart.spec == second.artifact.spec
    finally:
        await runtime.aclose()


async def test_runtime_close_waits_for_cancelled_waiter_live_leader(
    tmp_path: Path,
) -> None:
    loop = asyncio.get_running_loop()
    calculator = _BlockingNatalCalculator(loop)
    runtime = await build_application_runtime(
        settings=_settings(tmp_path, db_name="cancelled-waiter.sqlite3"),
        places=LocalPlaceCatalog.from_file(PLACES_PATH),
        clock=_clock,
        natal_calculator=calculator,
    )
    session_id = "runtime-cancelled-waiter"
    request_task: asyncio.Task[object] | None = None
    close_task: asyncio.Task[None] | None = None

    try:
        await _create_session(runtime, session_id)
        request_task = asyncio.create_task(
            runtime.orchestrator.execute(
                _command(),
                session_id=session_id,
                run=run_context(),
            )
        )
        await asyncio.wait_for(calculator.entered.wait(), timeout=1.0)

        assert calculator.calls == 1
        assert len(calculator.thread_ids) == 1
        assert calculator.thread_ids[0] != threading.get_ident()
        assert not request_task.done()

        request_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await request_task

        loaded = await runtime.context.load(session_id)
        assert isinstance(loaded, SessionSnapshot)
        assert loaded.state.state_version == 0
        assert loaded.state.base_chart is None
        assert runtime.artifacts.put_ok == 0

        close_task = asyncio.create_task(runtime.aclose())
        checkpoint = asyncio.Event()
        loop.call_soon(checkpoint.set)
        await checkpoint.wait()

        assert not close_task.done()
        assert not calculator.finished.is_set()

        calculator.release.set()
        await asyncio.wait_for(close_task, timeout=2.0)

        assert calculator.finished.is_set()
        assert runtime.artifacts.hits == 0
        assert runtime.artifacts.misses == 1
        assert runtime.artifacts.put_ok == 1
    finally:
        calculator.release.set()
        if request_task is not None and not request_task.done():
            request_task.cancel()
            await asyncio.gather(request_task, return_exceptions=True)
        if close_task is not None and not close_task.done():
            await asyncio.wait_for(close_task, timeout=2.0)
        await runtime.aclose()
