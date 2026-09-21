"""Process-local assembly and lifecycle for the application runtime."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack
from datetime import date, datetime
from math import isfinite
from pathlib import Path
from types import TracebackType
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from exact_orb.application.composition import build_application_orchestrator
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.birth import PlaceCatalog, resolve_unknown_birth_time_for_migration
from exact_orb.birth.resolver import BirthDataResolver
from exact_orb.calculation.artifacts import ChartArtifactResolver
from exact_orb.calculation.cache import InMemoryCalculationCache
from exact_orb.calculation.engine import EngineService, NatalTechniqueAdapter
from exact_orb.calculation.version import (
    CalculationVersionRecord,
    calculation_version_of,
    compute_calculation_version_record,
    log_calculation_version,
)
from exact_orb.config import (
    EphemerisStatus,
    SelenaMethodName,
    configure_ephemeris,
    get_ephemeris_status,
    get_selena_method_name,
)
from exact_orb.engine.charts.natal import NatalChart, calculate_natal
from exact_orb.engine.ephemeris.types import (
    DEFAULT_BODY_IDS,
    DEFAULT_EPHEMERIS_FLAGS,
)
from exact_orb.session import require_utc
from exact_orb.session.adapters.sqlite import SqliteSessionPersistence
from exact_orb.session.context import ContextService


class BootstrapSettings(BaseModel):
    """Strict settings required to assemble one application runtime."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        revalidate_instances="always",
        strict=True,
    )

    ephemeris_path: Path
    selena_method: SelenaMethodName
    session_db_path: Path
    sqlite_busy_timeout_ms: int
    sqlite_max_workers: int
    min_birth_date: date
    max_birth_date: date
    cache_max_entries: int
    cache_ttl_seconds: float
    engine_slow_threshold_ms: float
    degraded_log_interval_s: float

    @field_validator("session_db_path")
    @classmethod
    def _session_db_path_must_be_file_backed(cls, value: Path) -> Path:
        raw_path = str(value)
        if raw_path == ":memory:" or raw_path.startswith("file:"):
            raise ValueError(
                "session_db_path must identify a file-backed SQLite database"
            )
        return value

    @field_validator("sqlite_busy_timeout_ms", mode="before")
    @classmethod
    def _busy_timeout_must_be_a_non_negative_int(cls, value: object) -> object:
        if type(value) is not int or value < 0:
            raise ValueError("sqlite_busy_timeout_ms must be a non-negative int")
        return value

    @field_validator("sqlite_max_workers", "cache_max_entries", mode="before")
    @classmethod
    def _positive_ints_must_be_strict(cls, value: object) -> object:
        if type(value) is not int or value <= 0:
            raise ValueError("value must be a positive int")
        return value

    @field_validator(
        "cache_ttl_seconds",
        "engine_slow_threshold_ms",
        "degraded_log_interval_s",
        mode="before",
    )
    @classmethod
    def _positive_numbers_must_be_finite(cls, value: object) -> object:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value <= 0
        ):
            raise ValueError("value must be a finite positive number")
        return value

    @model_validator(mode="after")
    def _birth_date_range_must_be_ordered(self) -> Self:
        if self.min_birth_date > self.max_birth_date:
            raise ValueError("min_birth_date must be <= max_birth_date")
        return self


class ApplicationRuntime:
    """Own the assembled application boundary and its process-local resources."""

    __slots__ = (
        "_artifacts",
        "_calculation_version",
        "_calculation_version_record",
        "_clock",
        "_close_lock",
        "_closed",
        "_context",
        "_ephemeris_status",
        "_orchestrator",
        "_persistence",
        "_resources",
    )

    def __init__(
        self,
        *,
        orchestrator: ApplicationOrchestrator,
        context: ContextService,
        artifacts: ChartArtifactResolver,
        ephemeris_status: EphemerisStatus,
        calculation_version_record: CalculationVersionRecord,
        calculation_version: str,
        persistence: SqliteSessionPersistence,
        clock: Callable[[], datetime],
        resources: AsyncExitStack,
    ) -> None:
        self._orchestrator = orchestrator
        self._context = context
        self._artifacts = artifacts
        self._ephemeris_status = ephemeris_status
        self._calculation_version_record = calculation_version_record
        self._calculation_version = calculation_version
        self._persistence = persistence
        self._clock = clock
        self._resources = resources
        self._close_lock = asyncio.Lock()
        self._closed = False

    @property
    def orchestrator(self) -> ApplicationOrchestrator:
        return self._orchestrator

    @property
    def context(self) -> ContextService:
        return self._context

    @property
    def artifacts(self) -> ChartArtifactResolver:
        return self._artifacts

    @property
    def ephemeris_status(self) -> EphemerisStatus:
        return self._ephemeris_status

    @property
    def calculation_version_record(self) -> CalculationVersionRecord:
        return self._calculation_version_record

    @property
    def calculation_version(self) -> str:
        return self._calculation_version

    async def drain(self) -> None:
        """Wait for calculation leaders active when draining begins."""

        await self._artifacts.drain()

    async def reap_expired(self, *, now: datetime | None = None) -> int:
        """Delete expired sessions using the runtime clock by default."""

        effective_now = self._clock() if now is None else require_utc(now, name="now")
        return await self._persistence.reap_expired(now=effective_now)

    async def aclose(self) -> None:
        """Drain calculation work and release owned resources once."""

        async with self._close_lock:
            if self._closed:
                return
            await self.drain()
            await self._resources.aclose()
            self._closed = True

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()


async def build_application_runtime(
    *,
    settings: BootstrapSettings,
    places: PlaceCatalog,
    clock: Callable[[], datetime],
    natal_calculator: Callable[..., NatalChart] = calculate_natal,
) -> ApplicationRuntime:
    """Assemble the production application graph and transfer resource ownership."""

    settings = BootstrapSettings.model_validate(settings, strict=True)

    def checked_clock() -> datetime:
        return require_utc(clock(), name="clock")

    checked_clock()
    configure_ephemeris(
        settings.ephemeris_path,
        selena_method=settings.selena_method,
    )
    ephemeris_status = get_ephemeris_status()
    selena_method = get_selena_method_name()
    version_record = compute_calculation_version_record(
        ephemeris_path=ephemeris_status.path,
        selena_method=selena_method,
        body_ids=DEFAULT_BODY_IDS,
        ephemeris_flags=DEFAULT_EPHEMERIS_FLAGS,
    )
    calculation_version = calculation_version_of(version_record)
    log_calculation_version(version_record)

    resources = AsyncExitStack()
    try:
        sqlite_executor = resources.enter_context(
            ThreadPoolExecutor(
                max_workers=settings.sqlite_max_workers,
                thread_name_prefix="exact-orb-sqlite",
            )
        )
        persistence = await SqliteSessionPersistence.open(
            settings.session_db_path,
            executor=sqlite_executor,
            busy_timeout_ms=settings.sqlite_busy_timeout_ms,
            unknown_time_migrator=resolve_unknown_birth_time_for_migration,
        )
        calculation_executor = resources.enter_context(
            ThreadPoolExecutor(
                max_workers=2,
                thread_name_prefix="exact-orb-calculation",
            )
        )
        engine = EngineService(
            executor=calculation_executor,
            techniques={
                "natal": NatalTechniqueAdapter(calculator=natal_calculator),
            },
            slow_threshold_ms=settings.engine_slow_threshold_ms,
        )
        cache = InMemoryCalculationCache(
            max_entries=settings.cache_max_entries,
            ttl_seconds=settings.cache_ttl_seconds,
        )
        artifacts = ChartArtifactResolver(
            cache=cache,
            engine=engine,
            version=calculation_version,
            degraded_log_interval_s=settings.degraded_log_interval_s,
        )
        resolver = BirthDataResolver(
            places=places,
            min_birth_date=settings.min_birth_date,
            max_birth_date=settings.max_birth_date,
            today_provider=lambda: checked_clock().date(),
        )
        context = ContextService(persistence=persistence, clock=checked_clock)
        orchestrator = build_application_orchestrator(
            context=context,
            clock=checked_clock,
            resolver=resolver,
            artifacts=artifacts,
        )
        return ApplicationRuntime(
            orchestrator=orchestrator,
            context=context,
            artifacts=artifacts,
            ephemeris_status=ephemeris_status,
            calculation_version_record=version_record,
            calculation_version=calculation_version,
            persistence=persistence,
            clock=checked_clock,
            resources=resources,
        )
    except BaseException:
        await resources.aclose()
        raise


__all__ = [
    "ApplicationRuntime",
    "BootstrapSettings",
    "build_application_runtime",
]
