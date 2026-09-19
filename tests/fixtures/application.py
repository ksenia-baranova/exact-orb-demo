"""Shared real-component stand for Build Natal application integration."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from exact_orb.application.composition import build_application_orchestrator
from exact_orb.application.handlers.build_natal import BuildNatalHandler
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.birth.places import LocalPlaceCatalog
from exact_orb.birth.resolver import BirthDataResolver
from exact_orb.calculation.artifacts import ChartArtifactResolver
from exact_orb.calculation.cache import InMemoryCalculationCache
from exact_orb.calculation.engine import EngineService, NatalTechniqueAdapter
from exact_orb.session.adapters.in_memory import InMemorySessionPersistence
from exact_orb.session.context import ContextService
from tests.fixtures.calculation import BASE_UTC, VERSION


PLACES_PATH = Path(__file__).resolve().parent / "places.jsonl"
FIXED_TODAY = date(2026, 9, 8)


@dataclass(frozen=True)
class ApplicationTestStand:
    """Expose the real components and observable stores used by integration tests."""

    resolver: BirthDataResolver
    handler: BuildNatalHandler
    artifacts: ChartArtifactResolver
    cache: InMemoryCalculationCache
    persistence: InMemorySessionPersistence
    context: ContextService
    orchestrator: ApplicationOrchestrator
    clock: Callable[[], datetime]


@contextmanager
def application_test_stand(
    *,
    places: LocalPlaceCatalog | None = None,
    clock: Callable[[], datetime] | None = None,
) -> Iterator[ApplicationTestStand]:
    """Build one process-local application flow with a bounded real executor."""
    catalog = places or LocalPlaceCatalog.from_file(PLACES_PATH)
    resolver = BirthDataResolver(
        places=catalog,
        min_birth_date=date(1900, 1, 1),
        max_birth_date=FIXED_TODAY,
        today_provider=lambda: FIXED_TODAY,
    )
    cache = InMemoryCalculationCache(max_entries=10, ttl_seconds=None)
    operation_clock = clock or (lambda: BASE_UTC)
    persistence = InMemorySessionPersistence()
    context = ContextService(persistence=persistence, clock=operation_clock)
    with ThreadPoolExecutor(max_workers=2) as executor:
        engine = EngineService(
            executor=executor,
            techniques={"natal": NatalTechniqueAdapter()},
            slow_threshold_ms=3000.0,
        )
        artifacts = ChartArtifactResolver(
            cache=cache,
            engine=engine,
            version=VERSION,
            degraded_log_interval_s=60.0,
        )
        handler = BuildNatalHandler(resolver=resolver, artifacts=artifacts)
        orchestrator = build_application_orchestrator(
            context=context,
            clock=operation_clock,
            resolver=resolver,
            artifacts=artifacts,
        )
        yield ApplicationTestStand(
            resolver=resolver,
            handler=handler,
            artifacts=artifacts,
            cache=cache,
            persistence=persistence,
            context=context,
            orchestrator=orchestrator,
            clock=operation_clock,
        )


__all__ = ["ApplicationTestStand", "application_test_stand"]
