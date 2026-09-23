from __future__ import annotations

import ast
import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import closing
from importlib import metadata
import json
import logging
from pathlib import Path
import runpy
import shutil
import sqlite3
import threading
from typing import Any, Callable

import pytest

from exact_orb.birth import places as place_contracts
from exact_orb.birth.adapters import sqlite as sqlite_adapter
from exact_orb.birth.adapters.sqlite import SqlitePlaceCatalog
from exact_orb.birth.places import (
    PlaceCatalogUnavailableError,
    PlaceNotFound,
    ResolvedPlace,
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
    path = tmp_path_factory.mktemp("place-catalog-sqlite") / "places.sqlite"
    builder["build"](
        cities_path=FIXTURE_ROOT / "cities1000.txt",
        admin1_path=FIXTURE_ROOT / "admin1CodesASCII.txt",
        alternate_names_path=FIXTURE_ROOT / "alternateNamesV2.txt",
        out_path=path,
    )
    return path


class RecordingExecutor(ThreadPoolExecutor):
    """A real single worker which records scheduling and execution identity."""

    def __init__(self, *, max_workers: int = 1) -> None:
        super().__init__(max_workers=max_workers)
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


def _execute_script(path: Path, sql: str) -> None:
    with closing(REAL_SQLITE_CONNECT(path)) as connection:
        connection.executescript(sql)
        connection.commit()


def _update_build_parameters(path: Path, **changes: object) -> None:
    with closing(REAL_SQLITE_CONNECT(path)) as connection:
        raw = connection.execute(
            "SELECT build_parameters FROM catalog_metadata WHERE singleton = 1"
        ).fetchone()[0]
        parameters = json.loads(raw)
        parameters.update(changes)
        connection.execute(
            "UPDATE catalog_metadata SET build_parameters = ? WHERE singleton = 1",
            (json.dumps(parameters, sort_keys=True, separators=(",", ":")),),
        )
        connection.commit()


async def _expect_open_unavailable(path: Path) -> PlaceCatalogUnavailableError:
    executor = RecordingExecutor()
    try:
        try:
            catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        except PlaceCatalogUnavailableError as exc:
            error = exc
        else:
            await catalog.aclose()
            pytest.fail("invalid catalog unexpectedly opened")
    finally:
        executor.shutdown(wait=True)

    if path.exists():
        moved = path.with_name(f"closed-{path.name}")
        path.rename(moved)
        moved.rename(path)
    return error


def _probe_read_only(connection: sqlite3.Connection) -> tuple[int, str]:
    query_only = connection.execute("PRAGMA query_only").fetchone()[0]
    try:
        connection.execute("CREATE TABLE forbidden_write(value INTEGER)")
    except sqlite3.OperationalError as exc:
        write_error = str(exc).lower()
    else:  # pragma: no cover - an assertion branch, not accepted behaviour
        write_error = ""
    return query_only, write_error


async def test_lookup_uses_one_worker_read_only_uri_and_returns_fresh_models(
    catalog_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _copy_catalog(
        catalog_path,
        tmp_path / "каталог с пробелом #1.sqlite",
    )
    connect_calls: list[tuple[str, dict[str, object], int]] = []

    def recording_connect(database: str, **kwargs: object) -> sqlite3.Connection:
        connect_calls.append((database, kwargs, threading.get_ident()))
        return REAL_SQLITE_CONNECT(database, **kwargs)

    monkeypatch.setattr(sqlite_adapter.sqlite3, "connect", recording_connect)
    executor = RecordingExecutor()
    event_loop_thread_id = threading.get_ident()
    try:
        catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        first = await catalog.lookup("524901")
        second = await catalog.lookup("524901")
        missing_first = await catalog.lookup("777777")
        missing_second = await catalog.lookup("777777")
        assert catalog._connection is not None
        query_only, write_error = await asyncio.get_running_loop().run_in_executor(
            executor,
            _probe_read_only,
            catalog._connection,
        )
        await catalog.aclose()
        submissions_after_close = len(executor.submitted_names)
        await catalog.aclose()

        probe_thread_id = executor.submit(threading.get_ident).result(timeout=5)
    finally:
        executor.shutdown(wait=True)

    assert first == ResolvedPlace(
        place_id="524901",
        canonical_name="Москва",
        latitude=55.75,
        longitude=37.62,
        tz_id="Europe/Moscow",
    )
    assert second == first
    assert second is not first
    assert missing_first == PlaceNotFound(place_id="777777")
    assert missing_second == missing_first
    assert missing_second is not missing_first

    assert connect_calls == [
        (
            f"{path.resolve().as_uri()}?mode=ro",
            {"uri": True, "check_same_thread": True},
            connect_calls[0][2],
        )
    ]
    assert "immutable=" not in connect_calls[0][0]
    assert query_only == 1
    assert "readonly" in write_error or "read-only" in write_error
    assert submissions_after_close == len(executor.submitted_names) - 1
    assert executor.submitted_names.count("_sync_close") == 1
    assert {connect_calls[0][2], *executor.worker_thread_ids} == {probe_thread_id}
    assert probe_thread_id != event_loop_thread_id


async def test_invalid_lookup_ids_do_not_reach_executor(
    catalog_path: Path,
) -> None:
    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        before = len(executor.submitted_names)
        invalid_ids = (
            "",
            "1" * 10_000,
            "abc",
            "123-456",
            "１２３",
            "١٢٣",
            "123é",
        )
        results = [await catalog.lookup(place_id) for place_id in invalid_ids]
        assert len(executor.submitted_names) == before

        with pytest.raises(TypeError, match="place_id must be str"):
            await catalog.lookup(524901)  # type: ignore[arg-type]
        assert len(executor.submitted_names) == before

        assert await catalog.lookup("000000") == PlaceNotFound(place_id="000000")
        assert len(executor.submitted_names) == before + 1
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    assert results == [PlaceNotFound(place_id=value) for value in invalid_ids]


async def test_unopened_and_closed_lifecycle_rejects_lookup_without_sql(
    catalog_path: Path,
) -> None:
    unopened_executor = RecordingExecutor()
    try:
        unopened = SqlitePlaceCatalog(executor=unopened_executor)
        with pytest.raises(PlaceCatalogUnavailableError, match="not open"):
            await unopened.lookup("524901")
        await unopened.aclose()
        await unopened.aclose()
        assert unopened_executor.submitted_names == []
    finally:
        unopened_executor.shutdown(wait=True)

    executor = RecordingExecutor()
    try:
        catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
        await catalog.aclose()
        before = len(executor.submitted_names)
        with pytest.raises(PlaceCatalogUnavailableError, match="not open"):
            await catalog.lookup("524901")
        assert len(executor.submitted_names) == before
    finally:
        executor.shutdown(wait=True)


async def test_concurrent_close_schedules_one_worker_operation(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = RecordingExecutor()
    catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
    loop = asyncio.get_running_loop()
    close_started = asyncio.Event()
    release_close = threading.Event()
    real_close = sqlite_adapter._sync_close

    def controlled_close(connection: sqlite3.Connection) -> None:
        loop.call_soon_threadsafe(close_started.set)
        assert release_close.wait(timeout=5)
        real_close(connection)

    monkeypatch.setattr(sqlite_adapter, "_sync_close", controlled_close)
    first = asyncio.create_task(catalog.aclose())
    try:
        await asyncio.wait_for(close_started.wait(), timeout=5)
        second = asyncio.create_task(catalog.aclose())
        with pytest.raises(PlaceCatalogUnavailableError, match="not open"):
            await catalog.lookup("524901")
        assert executor.submitted_names.count("controlled_close") == 1
    finally:
        release_close.set()

    try:
        await asyncio.wait_for(asyncio.gather(first, second), timeout=5)
        assert executor.submitted_names.count("controlled_close") == 1
    finally:
        executor.shutdown(wait=True)


def test_executor_contract_is_validated_before_io(catalog_path: Path) -> None:
    with pytest.raises(TypeError, match="ThreadPoolExecutor"):
        SqlitePlaceCatalog(executor=object())  # type: ignore[arg-type]

    executor = RecordingExecutor(max_workers=2)
    try:
        with pytest.raises(ValueError, match="max_workers=1"):
            SqlitePlaceCatalog(executor=executor)
        assert executor.submitted_names == []
    finally:
        executor.shutdown(wait=True)


@pytest.mark.parametrize("db_path", ["", ":memory:", "file:places.sqlite"])
async def test_memory_and_raw_uri_paths_are_rejected_before_io(db_path: str) -> None:
    executor = RecordingExecutor()
    try:
        with pytest.raises(ValueError, match="file-backed"):
            await SqlitePlaceCatalog.open(db_path, executor=executor)
        assert executor.submitted_names == []
    finally:
        executor.shutdown(wait=True)


async def test_non_path_argument_is_rejected_before_io() -> None:
    executor = RecordingExecutor()
    try:
        with pytest.raises(TypeError, match="str or Path"):
            await SqlitePlaceCatalog.open(123, executor=executor)  # type: ignore[arg-type]
        assert executor.submitted_names == []
    finally:
        executor.shutdown(wait=True)


@pytest.mark.parametrize("case", ["missing", "directory", "malformed"])
async def test_path_and_sqlite_open_failures_are_typed_and_do_not_leak_files(
    case: str,
    tmp_path: Path,
) -> None:
    path = tmp_path / "places.sqlite"
    if case == "directory":
        path.mkdir()
    elif case == "malformed":
        path.write_bytes(b"not a sqlite database")

    error = await _expect_open_unavailable(path)

    assert error.__cause__ is not None
    if case == "missing":
        assert not path.exists()


DRIFT_CASES = (
    (
        "user-version",
        "PRAGMA user_version = 2;",
    ),
    (
        "columns",
        "ALTER TABLE places ADD COLUMN unexpected TEXT;",
    ),
    (
        "index",
        "DROP INDEX idx_place_names_search_key;",
    ),
    (
        "metadata-json",
        "UPDATE catalog_metadata SET source_checksums = '{';",
    ),
    (
        "metadata-shape",
        "UPDATE catalog_metadata SET build_parameters = '{}';",
    ),
    (
        "metadata-cardinality",
        """
        ALTER TABLE catalog_metadata RENAME TO old_catalog_metadata;
        CREATE TABLE catalog_metadata (
            singleton INTEGER PRIMARY KEY,
            schema_version INTEGER NOT NULL,
            source_checksums TEXT NOT NULL,
            build_parameters TEXT NOT NULL
        );
        INSERT INTO catalog_metadata
            SELECT singleton, schema_version, source_checksums, build_parameters
            FROM old_catalog_metadata;
        INSERT INTO catalog_metadata
            SELECT 2, schema_version, source_checksums, build_parameters
            FROM old_catalog_metadata;
        DROP TABLE old_catalog_metadata;
        """,
    ),
)


@pytest.mark.parametrize(("case", "sql"), DRIFT_CASES, ids=[row[0] for row in DRIFT_CASES])
async def test_startup_rejects_schema_index_and_metadata_drift(
    case: str,
    sql: str,
    catalog_path: Path,
    tmp_path: Path,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / f"{case}.sqlite")
    _execute_script(path, sql)

    error = await _expect_open_unavailable(path)

    assert type(error.__cause__).__name__ == "_CatalogValidationError"


async def test_tzdata_version_mismatch_warns_once_and_allows_open(
    catalog_path: Path,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / "version-mismatch.sqlite")
    catalog_version = "0.test-mismatch"
    runtime_version = metadata.version("tzdata")
    assert catalog_version != runtime_version
    _update_build_parameters(path, tzdata_version=catalog_version)

    executor = RecordingExecutor()
    caplog.set_level(logging.WARNING, logger=sqlite_adapter.__name__)
    try:
        catalog = await SqlitePlaceCatalog.open(path, executor=executor)
        assert await catalog.lookup("524901") == ResolvedPlace(
            place_id="524901",
            canonical_name="Москва",
            latitude=55.75,
            longitude=37.62,
            tz_id="Europe/Moscow",
        )
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)

    records = [
        record
        for record in caplog.records
        if record.getMessage().startswith("place_catalog_tzdata_version_mismatch ")
    ]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    assert records[0].catalog_tzdata_version == catalog_version
    assert records[0].runtime_tzdata_version == runtime_version
    assert records[0].getMessage() == (
        "place_catalog_tzdata_version_mismatch "
        f"catalog_tzdata_version={catalog_version} "
        f"runtime_tzdata_version={runtime_version}"
    )
    assert "524901" not in records[0].getMessage()
    assert "Москва" not in records[0].getMessage()


async def test_missing_tzdata_distribution_stops_startup(
    catalog_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / "missing-tzdata.sqlite")

    def missing_version(distribution_name: str) -> str:
        assert distribution_name == "tzdata"
        raise metadata.PackageNotFoundError(distribution_name)

    monkeypatch.setattr(sqlite_adapter.metadata, "version", missing_version)

    error = await _expect_open_unavailable(path)

    assert isinstance(error.__cause__, metadata.PackageNotFoundError)


@pytest.mark.parametrize("tz_id", ["", "Nowhere/Fake"])
async def test_unresolvable_timezone_stops_startup(
    tz_id: str,
    catalog_path: Path,
    tmp_path: Path,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / f"bad-zone-{len(tz_id)}.sqlite")
    with closing(REAL_SQLITE_CONNECT(path)) as connection:
        connection.execute("PRAGMA ignore_check_constraints = ON")
        connection.execute(
            "UPDATE places SET tz_id = ? WHERE place_id = '524901'",
            (tz_id,),
        )
        connection.commit()

    error = await _expect_open_unavailable(path)

    assert type(error.__cause__).__name__ == "_CatalogValidationError"


async def test_read_failure_after_startup_is_typed(
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
            await catalog.lookup("524901")
        assert isinstance(caught.value.__cause__, sqlite3.ProgrammingError)
        await catalog.aclose()
    finally:
        executor.shutdown(wait=True)


async def test_lookup_scheduling_failure_is_typed(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = RecordingExecutor()
    catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
    real_submit = executor.submit

    def reject_submission(
        fn: Callable[..., Any],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]:
        raise RuntimeError("executor is unavailable")

    try:
        monkeypatch.setattr(executor, "submit", reject_submission)
        with pytest.raises(
            PlaceCatalogUnavailableError,
            match="lookup could not be scheduled",
        ) as caught:
            await catalog.lookup("524901")
        assert isinstance(caught.value.__cause__, RuntimeError)
    finally:
        monkeypatch.setattr(executor, "submit", real_submit)
        await catalog.aclose()
        executor.shutdown(wait=True)


async def test_unexpected_lookup_worker_failure_is_not_retryable_unavailable(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = RecordingExecutor()
    catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)

    def fail_lookup(
        connection: sqlite3.Connection,
        place_id: str,
    ) -> object:
        raise AssertionError("injected lookup defect")

    monkeypatch.setattr(sqlite_adapter, "_sync_lookup", fail_lookup)
    try:
        with pytest.raises(AssertionError, match="injected lookup defect"):
            await catalog.lookup("524901")
        assert executor.submitted_names[-1] == "fail_lookup"
    finally:
        await catalog.aclose()
        executor.shutdown(wait=True)


async def test_cancelled_open_closes_created_connection_on_worker(
    catalog_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _copy_catalog(catalog_path, tmp_path / "cancel-open.sqlite")
    executor = RecordingExecutor()
    loop = asyncio.get_running_loop()
    connection_ready = asyncio.Event()
    release_worker = threading.Event()
    real_open = sqlite_adapter._sync_open_and_validate

    def controlled_open(db_path: Path) -> sqlite3.Connection:
        connection = real_open(db_path)
        loop.call_soon_threadsafe(connection_ready.set)
        assert release_worker.wait(timeout=5)
        return connection

    monkeypatch.setattr(sqlite_adapter, "_sync_open_and_validate", controlled_open)
    task = asyncio.create_task(SqlitePlaceCatalog.open(path, executor=executor))
    try:
        await asyncio.wait_for(connection_ready.wait(), timeout=5)
        task.cancel()
        release_worker.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=5)
        assert executor.submitted_names == ["controlled_open", "_sync_close"]
        assert len(set(executor.worker_thread_ids)) == 1
        assert executor.worker_thread_ids[0] != threading.get_ident()
        assert executor.submit(lambda: "still-owned").result(timeout=5) == "still-owned"
    finally:
        release_worker.set()
        executor.shutdown(wait=True)

    moved = path.with_name("cancel-open-moved.sqlite")
    path.rename(moved)


async def test_cancelled_lookup_propagates_and_worker_can_close_cleanly(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = RecordingExecutor()
    catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
    loop = asyncio.get_running_loop()
    lookup_started = asyncio.Event()
    release_worker = threading.Event()
    real_lookup = sqlite_adapter._sync_lookup

    def controlled_lookup(
        connection: sqlite3.Connection,
        place_id: str,
    ) -> object:
        loop.call_soon_threadsafe(lookup_started.set)
        assert release_worker.wait(timeout=5)
        return real_lookup(connection, place_id)

    monkeypatch.setattr(sqlite_adapter, "_sync_lookup", controlled_lookup)
    task = asyncio.create_task(catalog.lookup("524901"))
    try:
        await asyncio.wait_for(lookup_started.wait(), timeout=5)
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


async def test_cancelled_close_finishes_before_propagating(
    catalog_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = RecordingExecutor()
    catalog = await SqlitePlaceCatalog.open(catalog_path, executor=executor)
    loop = asyncio.get_running_loop()
    close_started = asyncio.Event()
    close_finished = asyncio.Event()
    release_worker = threading.Event()
    real_close = sqlite_adapter._sync_close

    def controlled_close(connection: sqlite3.Connection) -> None:
        loop.call_soon_threadsafe(close_started.set)
        assert release_worker.wait(timeout=5)
        real_close(connection)
        loop.call_soon_threadsafe(close_finished.set)

    monkeypatch.setattr(sqlite_adapter, "_sync_close", controlled_close)
    task = asyncio.create_task(catalog.aclose())
    try:
        await asyncio.wait_for(close_started.wait(), timeout=5)
        task.cancel()
        release_worker.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=5)
        assert close_finished.is_set()
        with pytest.raises(PlaceCatalogUnavailableError, match="not open"):
            await catalog.lookup("524901")
        assert executor.submit(lambda: "still-owned").result(timeout=5) == "still-owned"
    finally:
        release_worker.set()
        executor.shutdown(wait=True)


def test_sqlite_adapter_uses_canonical_normalizer() -> None:
    path = PROJECT_ROOT / "src" / "exact_orb" / "birth" / "adapters" / "sqlite.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "exact_orb.birth.places"
        for alias in node.names
    }
    local_normalizers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "normalize_place_query"
    ]

    assert "normalize_place_query" in imported_names
    assert local_normalizers == []
    assert sqlite_adapter.normalize_place_query is place_contracts.normalize_place_query
