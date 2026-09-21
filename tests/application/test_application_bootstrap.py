from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor as RealThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import exact_orb.application.bootstrap as bootstrap_module
from exact_orb.application.bootstrap import (
    ApplicationRuntime,
    BootstrapSettings,
    build_application_runtime,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.handlers.build_natal import BuildNatalHandler
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.birth import LocalPlaceCatalog, resolve_unknown_birth_time_for_migration
from exact_orb.birth.resolver import BirthDataResolver
from exact_orb.calculation.artifacts import ChartArtifactResolver
from exact_orb.calculation.engine import CalculationResult
from exact_orb.calculation.errors import ChartCalculationError
from exact_orb.calculation.version import (
    CalculationVersionRecord,
    calculation_version_of,
)
from exact_orb.config import (
    EphemerisPathMismatchError,
    EphemerisSelenaMethodMismatchError,
    get_ephemeris_status,
    get_selena_method_name,
)
from exact_orb.engine.ephemeris.types import (
    DEFAULT_BODY_IDS,
    DEFAULT_EPHEMERIS_FLAGS,
)
from exact_orb.session import StateWriteError
from exact_orb.session.context import ContextService
from tests.fixtures.calculation import chart_spec, resolved_birth_data, run_context


pytestmark = pytest.mark.asyncio


def _settings(tmp_path: Path, **overrides: object) -> BootstrapSettings:
    status = get_ephemeris_status()
    values: dict[str, object] = {
        "ephemeris_path": Path(status.path),
        "selena_method": get_selena_method_name(),
        "session_db_path": tmp_path / "sessions.sqlite3",
        "sqlite_busy_timeout_ms": 250,
        "sqlite_max_workers": 1,
        "min_birth_date": date(1800, 1, 1),
        "max_birth_date": date(2399, 12, 31),
        "cache_max_entries": 32,
        "cache_ttl_seconds": 300.0,
        "engine_slow_threshold_ms": 3_000.0,
        "degraded_log_interval_s": 60.0,
    }
    values.update(overrides)
    return BootstrapSettings.model_validate(values)


def _clock() -> datetime:
    return datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)


def _tracking_executor(
    *,
    created: list[str],
    shutdown: list[str],
) -> type[RealThreadPoolExecutor]:
    class TrackingExecutor(RealThreadPoolExecutor):
        def __init__(
            self,
            max_workers: int | None = None,
            thread_name_prefix: str = "",
            initializer: Any = None,
            initargs: tuple[Any, ...] = (),
        ) -> None:
            self._tracking_label = thread_name_prefix
            self._tracking_shutdown_recorded = False
            created.append(thread_name_prefix)
            super().__init__(
                max_workers=max_workers,
                thread_name_prefix=thread_name_prefix,
                initializer=initializer,
                initargs=initargs,
            )

        def shutdown(
            self,
            wait: bool = True,
            *,
            cancel_futures: bool = False,
        ) -> None:
            if not self._tracking_shutdown_recorded:
                shutdown.append(self._tracking_label)
                self._tracking_shutdown_recorded = True
            super().shutdown(wait=wait, cancel_futures=cancel_futures)

    return TrackingExecutor


async def test_build_runtime_wires_real_components_identity_and_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    startup_events: list[str] = []
    shutdown_events: list[str] = []
    executor_type = _tracking_executor(
        created=startup_events,
        shutdown=shutdown_events,
    )
    real_log_version = bootstrap_module.log_calculation_version
    real_compute_version = bootstrap_module.compute_calculation_version_record
    version_inputs: dict[str, object] = {}

    def tracked_log_version(record: CalculationVersionRecord) -> None:
        startup_events.append("calculation-version")
        real_log_version(record)

    def tracked_compute_version(**kwargs: object) -> CalculationVersionRecord:
        version_inputs.update(kwargs)
        return real_compute_version(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(bootstrap_module, "ThreadPoolExecutor", executor_type)
    monkeypatch.setattr(
        bootstrap_module,
        "log_calculation_version",
        tracked_log_version,
    )
    monkeypatch.setattr(
        bootstrap_module,
        "compute_calculation_version_record",
        tracked_compute_version,
    )
    places = LocalPlaceCatalog({})

    runtime = await build_application_runtime(
        settings=_settings(tmp_path),
        places=places,
        clock=_clock,
    )
    try:
        assert isinstance(runtime, ApplicationRuntime)
        assert isinstance(runtime.orchestrator, ApplicationOrchestrator)
        assert isinstance(runtime.context, ContextService)
        assert isinstance(runtime.artifacts, ChartArtifactResolver)
        assert runtime.ephemeris_status == get_ephemeris_status()
        assert runtime.calculation_version == calculation_version_of(
            runtime.calculation_version_record
        )
        assert runtime.calculation_version.startswith("eo:calcver:v1:")
        assert runtime.calculation_version_record.selena_method == (
            get_selena_method_name()
        )
        assert runtime.calculation_version_record.ephemeris_flags == (
            DEFAULT_EPHEMERIS_FLAGS
        )
        assert runtime.calculation_version_record.body_ids_digest
        assert runtime.artifacts.version == runtime.calculation_version

        handlers = runtime.orchestrator._handlers
        assert set(handlers) == {BuildNatalCommand}
        handler = handlers[BuildNatalCommand]
        assert isinstance(handler, BuildNatalHandler)
        resolver = handler._resolver
        assert isinstance(resolver, BirthDataResolver)
        assert resolver._places is places
        assert handler._artifacts is runtime.artifacts
        assert runtime.context._persistence is runtime._persistence
        assert (
            runtime._persistence._backend.unknown_time_migrator
            is resolve_unknown_birth_time_for_migration
        )
        assert runtime.artifacts.engine._executor._max_workers == 2
        assert runtime._persistence._backend.executor._max_workers == 1
        assert startup_events == [
            "calculation-version",
            "exact-orb-sqlite",
            "exact-orb-calculation",
        ]
        assert version_inputs == {
            "ephemeris_path": runtime.ephemeris_status.path,
            "selena_method": get_selena_method_name(),
            "body_ids": DEFAULT_BODY_IDS,
            "ephemeris_flags": DEFAULT_EPHEMERIS_FLAGS,
        }
    finally:
        await runtime.aclose()

    assert shutdown_events == ["exact-orb-calculation", "exact-orb-sqlite"]


@pytest.mark.parametrize(
    ("overrides", "error_fragment"),
    (
        ({"sqlite_busy_timeout_ms": True}, "non-negative int"),
        ({"sqlite_busy_timeout_ms": -1}, "non-negative int"),
        ({"sqlite_max_workers": False}, "positive int"),
        ({"sqlite_max_workers": 0}, "positive int"),
        ({"cache_max_entries": True}, "positive int"),
        ({"cache_ttl_seconds": 0.0}, "finite positive number"),
        ({"cache_ttl_seconds": float("nan")}, "finite positive number"),
        ({"engine_slow_threshold_ms": float("inf")}, "finite positive number"),
        ({"degraded_log_interval_s": False}, "finite positive number"),
        (
            {
                "min_birth_date": date(2026, 1, 2),
                "max_birth_date": date(2026, 1, 1),
            },
            "min_birth_date must be <= max_birth_date",
        ),
        ({"session_db_path": Path(":memory:")}, "file-backed SQLite"),
        ({"session_db_path": Path("file:sessions.sqlite3")}, "file-backed SQLite"),
    ),
)
async def test_bootstrap_settings_reject_component_invalid_values_strictly(
    tmp_path: Path,
    overrides: dict[str, object],
    error_fragment: str,
) -> None:
    with pytest.raises(ValidationError, match=error_fragment):
        _settings(tmp_path, **overrides)


async def test_bootstrap_settings_forbid_coercion_extra_fields_and_mutation(
    tmp_path: Path,
) -> None:
    valid = _settings(tmp_path)

    with pytest.raises(ValidationError):
        BootstrapSettings.model_validate(
            {**valid.model_dump(), "ephemeris_path": str(valid.ephemeris_path)}
        )
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BootstrapSettings.model_validate({**valid.model_dump(), "unexpected": 1})
    with pytest.raises(ValidationError, match="Instance is frozen"):
        valid.cache_max_entries = 64  # type: ignore[misc]


@pytest.mark.parametrize("invalid_kind", ("settings", "clock"))
async def test_invalid_startup_input_fails_before_executor_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    invalid_kind: str,
) -> None:
    created: list[str] = []
    shutdown: list[str] = []
    monkeypatch.setattr(
        bootstrap_module,
        "ThreadPoolExecutor",
        _tracking_executor(created=created, shutdown=shutdown),
    )
    settings = _settings(tmp_path)
    if invalid_kind == "settings":
        values = settings.model_dump()
        values["sqlite_max_workers"] = 0
        settings = BootstrapSettings.model_construct(**values)
        expected = ValidationError
        clock = _clock
    else:
        expected = ValueError
        clock = lambda: datetime(2026, 9, 21, 12, 0)

    with pytest.raises(expected):
        await build_application_runtime(
            settings=settings,
            places=LocalPlaceCatalog({}),
            clock=clock,
        )

    assert created == []
    assert shutdown == []


async def test_same_ephemeris_configuration_is_repeatable(
    tmp_path: Path,
) -> None:
    first = await build_application_runtime(
        settings=_settings(tmp_path, session_db_path=tmp_path / "first.sqlite3"),
        places=LocalPlaceCatalog({}),
        clock=_clock,
    )
    second = await build_application_runtime(
        settings=_settings(tmp_path, session_db_path=tmp_path / "second.sqlite3"),
        places=LocalPlaceCatalog({}),
        clock=_clock,
    )
    try:
        assert first.ephemeris_status == second.ephemeris_status
        assert first.calculation_version == second.calculation_version
    finally:
        await second.aclose()
        await first.aclose()


@pytest.mark.parametrize(
    ("overrides", "expected_error"),
    (
        ({"ephemeris_path": Path("different-ephe")}, EphemerisPathMismatchError),
        ({"selena_method": "mean_perigee"}, EphemerisSelenaMethodMismatchError),
    ),
)
async def test_ephemeris_mismatch_fails_before_owned_resources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
    expected_error: type[Exception],
) -> None:
    created: list[str] = []
    shutdown: list[str] = []
    monkeypatch.setattr(
        bootstrap_module,
        "ThreadPoolExecutor",
        _tracking_executor(created=created, shutdown=shutdown),
    )

    with pytest.raises(expected_error):
        await build_application_runtime(
            settings=_settings(tmp_path, **overrides),
            places=LocalPlaceCatalog({}),
            clock=_clock,
        )

    assert created == []
    assert shutdown == []


async def test_sqlite_open_failure_closes_only_acquired_executor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[str] = []
    shutdown: list[str] = []
    monkeypatch.setattr(
        bootstrap_module,
        "ThreadPoolExecutor",
        _tracking_executor(created=created, shutdown=shutdown),
    )
    db_path = tmp_path / "missing-parent" / "session.sqlite3"

    with pytest.raises(StateWriteError) as captured:
        await build_application_runtime(
            settings=_settings(tmp_path, session_db_path=db_path),
            places=LocalPlaceCatalog({}),
            clock=_clock,
        )

    assert captured.value.error_code == "SESSION_SQLITE_OPEN_FAILED"
    assert created == ["exact-orb-sqlite"]
    assert shutdown == ["exact-orb-sqlite"]
    assert not db_path.parent.exists()


async def test_aclose_orders_drain_and_executors_and_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[str] = []
    lifecycle: list[str] = []
    monkeypatch.setattr(
        bootstrap_module,
        "ThreadPoolExecutor",
        _tracking_executor(created=created, shutdown=lifecycle),
    )
    runtime = await build_application_runtime(
        settings=_settings(tmp_path),
        places=LocalPlaceCatalog({}),
        clock=_clock,
    )
    real_drain = runtime.artifacts.drain

    async def tracked_drain() -> None:
        lifecycle.append("drain")
        await real_drain()

    monkeypatch.setattr(runtime.artifacts, "drain", tracked_drain)

    await runtime.aclose()
    await runtime.aclose()

    assert created == ["exact-orb-sqlite", "exact-orb-calculation"]
    assert lifecycle == [
        "drain",
        "exact-orb-calculation",
        "exact-orb-sqlite",
    ]


async def test_async_context_manager_closes_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[str] = []
    shutdown: list[str] = []
    monkeypatch.setattr(
        bootstrap_module,
        "ThreadPoolExecutor",
        _tracking_executor(created=created, shutdown=shutdown),
    )

    async with await build_application_runtime(
        settings=_settings(tmp_path),
        places=LocalPlaceCatalog({}),
        clock=_clock,
    ) as runtime:
        assert runtime.orchestrator is not None

    assert shutdown == ["exact-orb-calculation", "exact-orb-sqlite"]


async def test_reaper_and_birth_resolver_use_checked_runtime_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = {
        "now": datetime(2026, 9, 21, 23, 59, tzinfo=timezone.utc),
    }
    runtime = await build_application_runtime(
        settings=_settings(tmp_path),
        places=LocalPlaceCatalog({}),
        clock=lambda: current["now"],
    )
    observed: list[datetime] = []

    async def tracked_reap(self: object, *, now: datetime) -> int:
        observed.append(now)
        return 7

    monkeypatch.setattr(type(runtime._persistence), "reap_expired", tracked_reap)
    try:
        current["now"] = datetime(2026, 9, 22, 0, 1, tzinfo=timezone.utc)
        assert await runtime.reap_expired() == 7
        handler = runtime.orchestrator._handlers[BuildNatalCommand]
        resolver = handler._resolver
        assert isinstance(resolver, BirthDataResolver)
        assert resolver._today_provider() == date(2026, 9, 22)
        assert runtime.context._clock() == current["now"]

        explicit = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
        assert await runtime.reap_expired(now=explicit) == 7
        with pytest.raises(ValueError, match="now must be timezone-aware UTC"):
            await runtime.reap_expired(now=datetime(2026, 9, 20, 10, 0))
    finally:
        await runtime.aclose()

    assert observed == [current["now"], explicit]


async def test_cancelled_close_with_failing_leader_has_no_loop_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BlockingFailingEngine:
        def __init__(self) -> None:
            self.entered = asyncio.Event()
            self.release = asyncio.Event()
            self.error = ChartCalculationError(
                "ENGINE_UNEXPECTED",
                run_id=str(run_context().run_id),
            )

        async def calculate(self, *args: object, **kwargs: object) -> CalculationResult:
            self.entered.set()
            await self.release.wait()
            raise self.error

    runtime = await build_application_runtime(
        settings=_settings(tmp_path),
        places=LocalPlaceCatalog({}),
        clock=_clock,
    )
    engine = BlockingFailingEngine()
    runtime.artifacts.engine = engine
    waiter = asyncio.create_task(
        runtime.artifacts.ensure_chart(
            chart_spec(),
            resolved_birth_data(),
            run=run_context(),
        )
    )
    await asyncio.wait_for(engine.entered.wait(), timeout=1.0)
    leader_task = next(iter(runtime.artifacts._inflight.values())).task
    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter

    drain_entered = asyncio.Event()
    real_drain = runtime.artifacts.drain

    async def observed_drain() -> None:
        drain_entered.set()
        await real_drain()

    monkeypatch.setattr(runtime.artifacts, "drain", observed_drain)
    loop = asyncio.get_running_loop()
    old_handler = loop.get_exception_handler()
    contexts: list[dict[str, object]] = []
    loop.set_exception_handler(lambda _loop, context: contexts.append(context))
    try:
        close_task = asyncio.create_task(runtime.aclose())
        await drain_entered.wait()
        assert not close_task.done()
        close_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await close_task

        leader_done = asyncio.Event()
        leader_task.add_done_callback(lambda _task: leader_done.set())
        engine.release.set()
        await asyncio.wait_for(leader_done.wait(), timeout=1.0)
        checkpoint = asyncio.Event()
        loop.call_soon(checkpoint.set)
        await checkpoint.wait()

        assert leader_task.done()
        assert contexts == []
        assert leader_task.exception() is engine.error
        await runtime.aclose()
    finally:
        loop.set_exception_handler(old_handler)
        if not runtime._closed:
            await runtime.aclose()

    assert contexts == []
