"""End-to-end acceptance for the process-local application runtime."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timezone
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
) -> None:
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
