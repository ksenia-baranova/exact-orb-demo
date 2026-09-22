from __future__ import annotations

import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import runpy
import shutil
import sqlite3
import threading
from typing import Any, Callable

import pytest

from exact_orb.birth.adapters import sqlite as sqlite_adapter
from exact_orb.birth.adapters.sqlite import SqlitePlaceCatalog
from exact_orb.birth.places import (
    InvalidPlaceQuery,
    PlaceCatalogUnavailableError,
    PlaceSuggestion,
    PlaceSuggestions,
    ResolvedPlace,
    normalize_place_query,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_place_catalog.py"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "place_catalog"
REAL_SQLITE_CONNECT = sqlite3.connect


@pytest.fixture(scope="module")
def builder() -> dict[str, Any]:
    return runpy.run_path(str(BUILDER_PATH))


@pytest.fixture(scope="module")
def catalog_path(
    builder: dict[str, Any],
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    path = tmp_path_factory.mktemp("place-catalog-search") / "places.sqlite"
    builder["build"](
        cities_path=FIXTURE_ROOT / "cities1000.txt",
        admin1_path=FIXTURE_ROOT / "admin1CodesASCII.txt",
        alternate_names_path=FIXTURE_ROOT / "alternateNamesV2.txt",
        out_path=path,
    )
    return path


class RecordingExecutor(ThreadPoolExecutor):
    """A real worker that records submissions and execution thread IDs."""

    def __init__(self) -> None:
        super().__init__(max_workers=1)
        self.submitted_names: list[str] = []
        self.worker_thread_ids: list[int] = []
        self._record_lock = threading.Lock()

    def submit(  # type: ignore[override]
        self,
        fn: Callable[..., Any],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]:
        with self._record_lock:
            self.submitted_names.append(getattr(fn, "__name__", type(fn).__name__))

        def recorded() -> Any:
            with self._record_lock:
                self.worker_thread_ids.append(threading.get_ident())
            return fn(*args, **kwargs)

        return super().submit(recorded)


def _copy_catalog(catalog_path: Path, target: Path) -> Path:
    shutil.copyfile(catalog_path, target)
    return target


def _place_row(
    place_id: str,
    display_name: str,
    *,
    admin1_name: str | None = "Region",
    country_code: str = "RU",
    population: int = 1,
) -> tuple[object, ...]:
    return (
        place_id,
        display_name,
        display_name,
        country_code,
        "01",
        admin1_name,
        0,
        0,
        "Europe/Moscow",
        population,
    )


def _name_row(
    place_name_id: int,
    place_id: str,
    name: str,
    *,
    preferred: bool = False,
    historic: bool = False,
) -> tuple[object, ...]:
    search_key = normalize_place_query(name)
    assert isinstance(search_key, str)
    return (
        place_name_id,
        place_id,
        name,
        search_key,
        "ru",
        int(preferred),
        int(historic),
    )


def _replace_rows(
    path: Path,
    *,
    places: list[tuple[object, ...]],
    names: list[tuple[object, ...]],
) -> None:
    with closing(REAL_SQLITE_CONNECT(path)) as connection:
        connection.execute("DELETE FROM place_names")
        connection.execute("DELETE FROM places")
        connection.executemany(
            """
            INSERT INTO places(
                place_id, display_name, name_ascii, country_code, admin1_code,
                admin1_name, latitude_e2, longitude_e2, tz_id, population
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            places,
        )
        connection.executemany(
            """
            INSERT INTO place_names(
                place_name_id, place_id, name, search_key, language,
                preferred, historic
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            names,
        )
        connection.commit()


async def test_moscow_variants_prefix_and_lookup_share_one_catalog(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        results = {
            query: await catalog.search(query)
            for query in ("Москва", "москва", "МОСКВА", "Moscow", "Моск")
        }

        for result in results.values():
            assert isinstance(result, PlaceSuggestions)
            assert [item.place_id for item in result.items] == ["524901"]
            suggestion = result.items[0]
            assert suggestion == PlaceSuggestion(
                place_id="524901",
                display_name="Москва",
                admin1_name="Москва",
                country_code="RU",
            )
            assert set(type(suggestion).model_fields) == {
                "place_id",
                "display_name",
                "admin1_name",
                "country_code",
            }
            resolved = await catalog.lookup(suggestion.place_id)
            assert resolved == ResolvedPlace(
                place_id="524901",
                canonical_name="Москва",
                latitude=55.75,
                longitude=37.62,
                tz_id="Europe/Moscow",
            )
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)


async def test_historical_alias_returns_canonical_current_label(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        current = await catalog.search("Санкт")
        historical = await catalog.search("Ленинград")
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert [item.place_id for item in current.items] == ["498817"]
    assert [item.place_id for item in historical.items] == ["498817"]
    assert historical.items[0].display_name == "Санкт-Петербург"
    assert historical.items[0].display_name != "Ленинград"


async def test_same_name_places_keep_region_and_country_distinct(
    catalog_path: Path,
    tmp_path: Path,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / "same-name.sqlite")
    _replace_rows(
        path,
        places=[
            _place_row(
                "100",
                "Springfield",
                admin1_name="Illinois",
                country_code="US",
                population=100,
            ),
            _place_row(
                "200",
                "Springfield",
                admin1_name="Ontario",
                country_code="CA",
                population=50,
            ),
        ],
        names=[
            _name_row(1, "100", "Springfield", preferred=True),
            _name_row(2, "200", "Springfield", preferred=True),
        ],
    )
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        result = await catalog.search("Springfield")
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert [
        (item.place_id, item.display_name, item.admin1_name, item.country_code)
        for item in result.items
    ] == [
        ("100", "Springfield", "Illinois", "US"),
        ("200", "Springfield", "Ontario", "CA"),
    ]


async def test_ranking_is_exact_preferred_current_population_id_then_historical(
    catalog_path: Path,
    tmp_path: Path,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / "ranking.sqlite")
    _replace_rows(
        path,
        places=[
            _place_row("100", "Exact", population=1),
            _place_row("200", "Preferred", population=1_000_000),
            _place_row("300", "Current High", population=900),
            _place_row("400", "Current Tie A", population=500),
            _place_row("500", "Current Tie B", population=500),
            _place_row("600", "Historical", population=2_000_000),
        ],
        names=[
            _name_row(1, "100", "Rank"),
            _name_row(2, "200", "Rank Preferred", preferred=True),
            _name_row(3, "300", "Rank Current High"),
            _name_row(4, "400", "Rank Current Tie A"),
            _name_row(5, "500", "Rank Current Tie B"),
            _name_row(6, "600", "Rank Historical", historic=True),
        ],
    )
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        result = await catalog.search("rank", limit=20)
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert [item.place_id for item in result.items] == [
        "100",
        "200",
        "300",
        "400",
        "500",
        "600",
    ]


async def test_limit_is_applied_after_alias_deduplication(
    catalog_path: Path,
    tmp_path: Path,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / "dedup-limit.sqlite")
    _replace_rows(
        path,
        places=[
            _place_row("100", "Atlas", population=1),
            _place_row("200", "Atlas Two", population=300),
            _place_row("300", "Atlas Three", population=200),
            _place_row("400", "Atlas Four", population=100),
        ],
        names=[
            _name_row(1, "100", "Atlas"),
            _name_row(2, "100", "Atlas Alpha"),
            _name_row(3, "100", "Atlas Beta"),
            _name_row(4, "100", "Atlas Gamma"),
            _name_row(5, "200", "Atlas Two"),
            _name_row(6, "300", "Atlas Three"),
            _name_row(7, "400", "Atlas Four"),
        ],
    )
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        result = await catalog.search("atlas", limit=3)
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert [item.place_id for item in result.items] == ["100", "200", "300"]
    assert len({item.place_id for item in result.items}) == 3


async def test_default_and_boundary_limits_apply_to_distinct_places(
    catalog_path: Path,
    tmp_path: Path,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / "default-limit.sqlite")
    places = [
        _place_row(str(100 + index), f"Bulk {index:02d}", population=100 - index)
        for index in range(12)
    ]
    names = [
        _name_row(index + 1, str(100 + index), f"Bulk {index:02d}")
        for index in range(12)
    ]
    _replace_rows(path, places=places, names=names)
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        default = await catalog.search("bulk")
        one = await catalog.search("bulk", limit=1)
        twenty = await catalog.search("bulk", limit=20)
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert len(default.items) == 10
    assert len(one.items) == 1
    assert len(twenty.items) == 12
    assert default.items == twenty.items[:10]


async def test_invalid_queries_skip_worker_with_valid_positive_control(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        before = len(executor.submitted_names)
        invalid_cases = (
            ("", "EMPTY"),
            ("x" * 201, "TOO_LONG"),
            ("Moscow\n", "CONTROL_CHARACTERS"),
            ("###@@@", "NO_SEARCHABLE_CHARACTERS"),
        )
        for query, code in invalid_cases:
            assert await catalog.search(query) == InvalidPlaceQuery(code=code)
        assert len(executor.submitted_names) == before

        unknown = await catalog.search("Definitely Unknown Place")
        assert unknown == PlaceSuggestions(items=())
        assert len(executor.submitted_names) == before + 1
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)


async def test_invalid_limits_and_query_type_skip_worker(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        before = len(executor.submitted_names)
        for limit in (0, -1, 21, True, 1.0, "10", None):
            with pytest.raises(ValueError, match="limit"):
                await catalog.search("Москва", limit=limit)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="query must be str"):
            await catalog.search(123)  # type: ignore[arg-type]
        assert len(executor.submitted_names) == before

        assert [
            item.place_id for item in (await catalog.search("Москва", limit=1)).items
        ] == ["524901"]
        assert len(executor.submitted_names) == before + 1
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)


@pytest.mark.parametrize(
    "query",
    ("моск%", "моск_", "моск' OR 1=1 --"),
)
async def test_sql_metacharacters_have_no_wildcard_or_executable_semantics(
    query: str,
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        result = await catalog.search(query)
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert result == PlaceSuggestions(items=())


def _set_trace_callback(
    connection: sqlite3.Connection,
    statements: list[str],
) -> None:
    connection.set_trace_callback(statements.append)


def _clear_trace_callback(connection: sqlite3.Connection) -> None:
    connection.set_trace_callback(None)


def _explain_statement(
    connection: sqlite3.Connection,
    statement: str,
) -> list[str]:
    return [
        row[3]
        for row in connection.execute(f"EXPLAIN QUERY PLAN {statement}").fetchall()
    ]


async def test_actual_search_statement_uses_binary_range_and_search_index(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    event_loop_thread_id = threading.get_ident()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        assert catalog._connection is not None
        statements: list[str] = []
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            executor,
            _set_trace_callback,
            catalog._connection,
            statements,
        )
        try:
            result = await catalog.search("Моск")
        finally:
            await loop.run_in_executor(
                executor,
                _clear_trace_callback,
                catalog._connection,
            )
        statement = next(
            sql for sql in statements if sql.lstrip().upper().startswith("WITH RANKED_PLACES")
        )
        plan = await loop.run_in_executor(
            executor,
            _explain_statement,
            catalog._connection,
            statement,
        )
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert [item.place_id for item in result.items] == ["524901"]
    assert "COLLATE BINARY" in statement
    assert "search_key >=" in statement
    assert "search_key <" in statement
    assert "LIKE" not in statement.upper()
    assert any("idx_place_names_search_key" in detail for detail in plan)
    assert len(set(executor.worker_thread_ids)) == 1
    assert executor.worker_thread_ids[0] != event_loop_thread_id


async def test_search_before_open_and_after_close_never_reaches_worker(
    catalog_path: Path,
) -> None:
    unopened_executor = RecordingExecutor()
    try:
        unopened = SqlitePlaceCatalog(executor=unopened_executor)
        with pytest.raises(PlaceCatalogUnavailableError, match="not open"):
            await unopened.search("Москва")
        assert unopened_executor.submitted_names == []
        await unopened.aclose()
    finally:
        unopened_executor.shutdown(wait=True)

    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        await catalog.aclose()
        before = len(executor.submitted_names)
        with pytest.raises(PlaceCatalogUnavailableError, match="not open"):
            await catalog.search("Москва")
        assert len(executor.submitted_names) == before
    finally:
        executor.shutdown(wait=True)


async def test_search_read_failure_after_startup_is_typed(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        assert catalog._connection is not None
        await asyncio.get_running_loop().run_in_executor(
            executor,
            catalog._connection.close,
        )
        with pytest.raises(PlaceCatalogUnavailableError) as caught:
            await catalog.search("Москва")
        assert isinstance(caught.value.__cause__, sqlite3.ProgrammingError)
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)


async def test_cancelled_search_propagates_and_worker_can_close_cleanly(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = RecordingExecutor()
    catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
    loop = asyncio.get_running_loop()
    search_started = asyncio.Event()
    release_worker = threading.Event()
    real_search = sqlite_adapter._sync_search

    def controlled_search(
        connection: sqlite3.Connection,
        search_key: str,
        limit: int,
    ) -> PlaceSuggestions:
        loop.call_soon_threadsafe(search_started.set)
        assert release_worker.wait(timeout=5)
        return real_search(connection, search_key, limit)

    monkeypatch.setattr(sqlite_adapter, "_sync_search", controlled_search)
    task = asyncio.create_task(catalog.search("Москва"))
    try:
        await asyncio.wait_for(search_started.wait(), timeout=5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        release_worker.set()

    try:
        await asyncio.wait_for(catalog.aclose(), timeout=5)
        assert executor.submitted_names[-1] == "_sync_close"
    finally:
        executor.shutdown(wait=True)


async def test_concurrent_search_and_lookup_return_fresh_models(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        search_one, search_two, lookup_one, lookup_two = await asyncio.gather(
            catalog.search("Москва"),
            catalog.search("Москва"),
            catalog.lookup("524901"),
            catalog.lookup("524901"),
        )
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert search_one == search_two
    assert search_one is not search_two
    assert search_one.items[0] is not search_two.items[0]
    assert lookup_one == lookup_two
    assert lookup_one is not lookup_two
    assert search_one.items[0].place_id == lookup_one.place_id == "524901"
    assert len(set(executor.worker_thread_ids)) == 1
