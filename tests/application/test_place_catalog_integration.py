"""End-to-end acceptance for the built SQLite place catalog."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timezone
from pathlib import Path
import runpy
from typing import Any

import pytest

from exact_orb.application.application_results import (
    ApplicationCommitted,
    ApplicationInputRequired,
    ApplicationResolutionFailure,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.birth import resolver as birth_resolver_module
from exact_orb.birth.adapters.sqlite import SqlitePlaceCatalog
from exact_orb.birth.places import PlaceResolution, PlaceSuggestions, ResolvedPlace
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.outcomes import Issue
from exact_orb.session.outcomes import SessionCreated
from exact_orb.session.persistence import SessionSnapshot
from tests.fixtures.application import ApplicationTestStand, application_test_stand
from tests.fixtures.calculation import run_context


pytestmark = pytest.mark.asyncio

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_place_catalog.py"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "place_catalog"
MOSCOW_ID = "524901"


@pytest.fixture(scope="module")
def catalog_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build one real schema-v1 release for all end-to-end scenarios."""
    path = tmp_path_factory.mktemp("place-catalog-integration") / "places.sqlite"
    builder: dict[str, Any] = runpy.run_path(str(BUILDER_PATH))
    statistics = builder["build"](
        cities_path=FIXTURE_ROOT / "cities1000.txt",
        admin1_path=FIXTURE_ROOT / "admin1CodesASCII.txt",
        alternate_names_path=FIXTURE_ROOT / "alternateNamesV2.txt",
        out_path=path,
    )
    assert statistics.places_written == 5
    return path


@asynccontextmanager
async def _opened_catalog(
    path: Path,
) -> AsyncIterator[tuple[SqlitePlaceCatalog, ThreadPoolExecutor]]:
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        try:
            yield catalog, executor
        finally:
            await catalog.aclose()
    finally:
        executor.shutdown(wait=True)


def _birth_input(*, place_id: str) -> BirthInput:
    return BirthInput(
        birth_date=date(1990, 9, 2),
        birth_time=time(14, 30),
        place_id=place_id,
    )


def _command(*, place_id: str) -> BuildNatalCommand:
    return BuildNatalCommand(birth_input=_birth_input(place_id=place_id))


async def _create_session(stand: ApplicationTestStand, session_id: str) -> None:
    created = await stand.context.create(session_id)
    assert isinstance(created, SessionCreated)
    assert created.state.state_version == 0


async def _load_snapshot(
    stand: ApplicationTestStand,
    session_id: str,
) -> SessionSnapshot:
    loaded = await stand.context.load(session_id)
    assert isinstance(loaded, SessionSnapshot)
    return loaded


def _assert_uncommitted(
    stand: ApplicationTestStand,
    snapshot: SessionSnapshot,
) -> None:
    assert snapshot.state.state_version == 0
    assert snapshot.state.birth_input is None
    assert snapshot.state.birth_resolved is None
    assert snapshot.state.base_chart is None
    assert stand.artifacts.hits == 0
    assert stand.artifacts.misses == 0
    assert stand.artifacts.put_ok == 0
    assert len(stand.cache) == 0


async def test_search_lookup_and_resolver_share_one_built_release(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with _opened_catalog(catalog_path) as (catalog, _executor):
        with application_test_stand(places=catalog) as stand:
            application_calls: list[str] = []
            real_execute = stand.orchestrator.execute
            real_load = stand.context.load
            real_save = stand.context.save

            async def recording_execute(*args: Any, **kwargs: Any) -> Any:
                application_calls.append("orchestrator.execute")
                return await real_execute(*args, **kwargs)

            async def recording_load(*args: Any, **kwargs: Any) -> Any:
                application_calls.append("context.load")
                return await real_load(*args, **kwargs)

            async def recording_save(*args: Any, **kwargs: Any) -> Any:
                application_calls.append("context.save")
                return await real_save(*args, **kwargs)

            monkeypatch.setattr(stand.orchestrator, "execute", recording_execute)
            monkeypatch.setattr(stand.context, "load", recording_load)
            monkeypatch.setattr(stand.context, "save", recording_save)

            suggestions = await catalog.search("Москва")
            assert isinstance(suggestions, PlaceSuggestions)
            assert [item.place_id for item in suggestions.items] == [MOSCOW_ID]
            assert application_calls == []

            looked_up = [
                await catalog.lookup(item.place_id) for item in suggestions.items
            ]
            assert all(isinstance(place, ResolvedPlace) for place in looked_up)
            moscow = looked_up[0]
            assert isinstance(moscow, ResolvedPlace)
            assert moscow == ResolvedPlace(
                place_id=MOSCOW_ID,
                canonical_name="Москва",
                latitude=55.75,
                longitude=37.62,
                tz_id="Europe/Moscow",
            )

            resolved = await stand.resolver.resolve(_birth_input(place_id=MOSCOW_ID))
            assert isinstance(resolved, ResolvedBirthData)
            assert resolved.utc_offset_seconds == 14_400
            assert resolved.utc_datetime == datetime(
                1990,
                9,
                2,
                10,
                30,
                tzinfo=timezone.utc,
            )
            assert resolved.canonical_place == "Москва"
            assert application_calls == []


async def test_selected_suggestion_flows_through_application_and_commits(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with _opened_catalog(catalog_path) as (catalog, _executor):
        suggestions = await catalog.search("Москва")
        assert isinstance(suggestions, PlaceSuggestions)
        selected_id = suggestions.items[0].place_id

        lookup_calls: list[str] = []
        real_lookup = catalog.lookup

        async def recording_lookup(place_id: str) -> PlaceResolution:
            lookup_calls.append(place_id)
            return await real_lookup(place_id)

        monkeypatch.setattr(catalog, "lookup", recording_lookup)

        with application_test_stand(places=catalog) as stand:
            await _create_session(stand, "place-catalog-success")
            result = await stand.orchestrator.execute(
                _command(place_id=selected_id),
                session_id="place-catalog-success",
                run=run_context(),
            )

            assert isinstance(result, ApplicationCommitted)
            assert result.state_version == 1
            assert lookup_calls == [selected_id]

            snapshot = await _load_snapshot(stand, "place-catalog-success")
            assert snapshot.state.state_version == 1
            assert snapshot.state.birth_input == _birth_input(place_id=selected_id)
            resolved = snapshot.state.birth_resolved
            assert resolved is not None
            assert resolved.canonical_place == "Москва"
            assert resolved.latitude == 55.75
            assert resolved.longitude == 37.62
            assert resolved.tz_id == "Europe/Moscow"
            assert resolved.utc_offset_seconds == 14_400
            assert resolved.utc_datetime == datetime(
                1990,
                9,
                2,
                10,
                30,
                tzinfo=timezone.utc,
            )
            assert snapshot.state.base_chart is not None
            assert snapshot.state.base_chart.spec == result.artifact.spec


async def test_unknown_id_stops_before_timezone_calculation_and_commit(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with _opened_catalog(catalog_path) as (catalog, _executor):
        with application_test_stand(places=catalog) as stand:
            await _create_session(stand, "place-catalog-unknown")

            def unexpected_timezone_call(*args: Any, **kwargs: Any) -> None:
                pytest.fail("timezone resolution must not run for an unknown place ID")

            monkeypatch.setattr(
                birth_resolver_module,
                "resolve_historical_tz",
                unexpected_timezone_call,
            )
            result = await stand.orchestrator.execute(
                _command(place_id="999999999"),
                session_id="place-catalog-unknown",
                run=run_context(),
            )

            assert isinstance(result, ApplicationInputRequired)
            assert result.issues == (Issue(field="birth.place", code="INVALID"),)
            assert result.state_version == 0
            snapshot = await _load_snapshot(stand, "place-catalog-unknown")
            _assert_uncommitted(stand, snapshot)


async def test_runtime_read_failure_is_retryable_and_not_input_required(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with _opened_catalog(catalog_path) as (catalog, executor):
        with application_test_stand(places=catalog) as stand:
            await _create_session(stand, "place-catalog-read-failure")
            connection = catalog._connection
            assert connection is not None
            await asyncio.get_running_loop().run_in_executor(
                executor,
                connection.close,
            )

            def unexpected_timezone_call(*args: Any, **kwargs: Any) -> None:
                pytest.fail("timezone resolution must not run after a catalog failure")

            monkeypatch.setattr(
                birth_resolver_module,
                "resolve_historical_tz",
                unexpected_timezone_call,
            )
            result = await stand.orchestrator.execute(
                _command(place_id=MOSCOW_ID),
                session_id="place-catalog-read-failure",
                run=run_context(),
            )

            assert isinstance(result, ApplicationResolutionFailure)
            assert not isinstance(result, ApplicationInputRequired)
            assert result.detail_code == "PLACE_CATALOG_UNAVAILABLE"
            assert result.retryable is True
            assert result.state_version == 0
            snapshot = await _load_snapshot(stand, "place-catalog-read-failure")
            _assert_uncommitted(stand, snapshot)
