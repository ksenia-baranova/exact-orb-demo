"""Portable evidence benchmark for the file-backed session SQLite adapter.

The timings in this script are machine-specific observations, not an SLA.  It
keeps lifecycle setup outside timed intervals and exercises the public session
ports for all full-operation measurements.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import contextmanager
import json
import math
import os
import platform
import shutil
import sqlite3
import sys
import uuid
from collections.abc import Awaitable, Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from time import perf_counter_ns
from typing import TYPE_CHECKING, Any, Iterator, TypeVar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from exact_orb.birth.types import (  # noqa: E402
    BirthInput,
    ResolutionWarning,
    ResolvedBirthData,
)
from exact_orb.calculation.spec import NatalChartSpec  # noqa: E402
from exact_orb.session.dialog import DialogTurn, Selection  # noqa: E402
from exact_orb.session.errors import StateWriteError  # noqa: E402
from exact_orb.session.outcomes import (  # noqa: E402
    SessionCreated,
    VersionConflict,
)
from exact_orb.session.persistence import SessionSnapshot  # noqa: E402
from exact_orb.session.state import StateDelta  # noqa: E402

if TYPE_CHECKING:
    from exact_orb.session.adapters.sqlite import SqliteSessionPersistence


T = TypeVar("T")

BASE_NOW = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
BUSY_ERROR_CODE = "SESSION_SQLITE_BUSY"

BIRTH_INPUT = BirthInput(
    birth_date=date(1990, 9, 2),
    birth_time=time(12, 30),
    place_id="moscow",
)
RESOLVED_BIRTH = ResolvedBirthData(
    utc_datetime=datetime(1990, 9, 2, 8, 30, tzinfo=UTC),
    latitude=55.75,
    longitude=37.62,
    tz_id="Europe/Moscow",
    utc_offset_seconds=14_400,
    canonical_place="Moscow",
    time_unknown=False,
    warnings=(
        ResolutionWarning(
            source="place",
            code="NORMALIZED",
            message="normalized",
        ),
    ),
)
OTHER_BIRTH_INPUT = BirthInput(
    birth_date=date(1991, 10, 3),
    birth_time=time(7, 45),
    place_id="saint-petersburg",
)
OTHER_RESOLVED_BIRTH = ResolvedBirthData(
    utc_datetime=datetime(1991, 10, 3, 4, 45, tzinfo=UTC),
    latitude=59.93,
    longitude=30.32,
    tz_id="Europe/Moscow",
    utc_offset_seconds=10_800,
    canonical_place="Saint Petersburg",
    time_unknown=False,
)

DELTA = StateDelta(
    birth_input=BIRTH_INPUT,
    birth_resolved=RESOLVED_BIRTH,
    base_chart_spec=NatalChartSpec(chart_kind="natal"),
)
OTHER_DELTA = StateDelta(
    birth_input=OTHER_BIRTH_INPUT,
    birth_resolved=OTHER_RESOLVED_BIRTH,
    base_chart_spec=NatalChartSpec(chart_kind="cosmogram"),
)
SELECTION = Selection(topic="natal", focus="relationships")
DIALOG_TEXT = "benchmark dialog payload " * 128


class BenchmarkInvariantError(RuntimeError):
    """The adapter did not produce the outcome required by a benchmark case."""


def _integer_at_least(minimum: int) -> Callable[[str], int]:
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if parsed < minimum:
            raise argparse.ArgumentTypeError(f"must be >= {minimum}")
        return parsed

    return parse


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark the production file-backed session SQLite path.",
    )
    parser.add_argument(
        "--samples",
        type=_integer_at_least(100),
        default=200,
        help="recorded samples per series (default: 200, minimum: 100)",
    )
    parser.add_argument(
        "--workers",
        type=_integer_at_least(2),
        default=4,
        help="injected executor worker count (default: 4, minimum: 2)",
    )
    parser.add_argument(
        "--warmup",
        type=_integer_at_least(0),
        default=20,
        help="discarded warmup samples per series (default: 20)",
    )
    parser.add_argument(
        "--busy-timeout-ms",
        type=_integer_at_least(0),
        default=5_000,
        help="SQLite busy timeout in milliseconds (default: 5000)",
    )
    parser.add_argument(
        "--database-dir",
        type=Path,
        help="existing parent directory for the isolated temporary database",
    )
    args = parser.parse_args(argv)
    if args.database_dir is not None:
        args.database_dir = args.database_dir.expanduser().resolve()
        if not args.database_dir.is_dir():
            parser.error("--database-dir must name an existing directory")
    return args


def _percentile(samples_ns: Sequence[int], quantile: float) -> float:
    """Return a linearly interpolated percentile in milliseconds."""

    if not samples_ns:
        raise BenchmarkInvariantError("cannot summarize an empty timing series")
    ordered = sorted(samples_ns)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    value = ordered[lower]
    if upper != lower:
        value += (ordered[upper] - ordered[lower]) * (position - lower)
    return value / 1_000_000


def _summary(samples_ns: Sequence[int]) -> dict[str, int | float]:
    return {
        "count": len(samples_ns),
        "p50_ms": round(_percentile(samples_ns, 0.50), 6),
        "p95_ms": round(_percentile(samples_ns, 0.95), 6),
    }


async def _timed(awaitable: Awaitable[T]) -> tuple[int, T]:
    started_ns = perf_counter_ns()
    result = await awaitable
    return perf_counter_ns() - started_ns, result


def _remove_sqlite_files(database_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        database_path.with_name(database_path.name + suffix).unlink(missing_ok=True)


@contextmanager
def _benchmark_directory(parent: Path | None) -> Iterator[Path]:
    """Create an inherited-ACL directory and tolerate delayed Windows unlocks."""

    selected_parent = parent or PROJECT_ROOT / "logs"
    selected_parent.mkdir(parents=True, exist_ok=True)
    root = selected_parent / f"exact-orb-session-sqlite-{uuid.uuid4().hex}"
    root.mkdir(exist_ok=False)
    try:
        yield root.resolve()
    finally:
        shutil.rmtree(root, ignore_errors=True)


async def _benchmark_initialization(
    root: Path,
    executor: ThreadPoolExecutor,
    persistence_type: type[SqliteSessionPersistence],
    *,
    busy_timeout_ms: int,
    warmup: int,
    samples: int,
) -> list[int]:
    timings: list[int] = []
    for index in range(warmup + samples):
        database_path = root / f"initialization-{index:06d}.sqlite3"
        if database_path.exists():
            raise BenchmarkInvariantError(
                f"benchmark refuses to overwrite {database_path}"
            )
        elapsed_ns, persistence = await _timed(
            persistence_type.open(
                database_path,
                executor=executor,
                busy_timeout_ms=busy_timeout_ms,
            )
        )
        del persistence
        if index >= warmup:
            timings.append(elapsed_ns)
        _remove_sqlite_files(database_path)
    return timings


def _connect_configure_close(database_path: Path, busy_timeout_ms: int) -> None:
    connection = sqlite3.connect(
        str(database_path),
        timeout=0,
        isolation_level=None,
    )
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        if foreign_keys != 1:
            raise BenchmarkInvariantError("PRAGMA foreign_keys read-back failed")

        connection.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
        if busy_timeout != busy_timeout_ms:
            raise BenchmarkInvariantError("PRAGMA busy_timeout read-back failed")

        connection.execute("PRAGMA synchronous = NORMAL")
        synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]
        if synchronous != 1:
            raise BenchmarkInvariantError("PRAGMA synchronous read-back failed")
    finally:
        connection.close()


async def _benchmark_steady_connection(
    database_path: Path,
    executor: ThreadPoolExecutor,
    *,
    busy_timeout_ms: int,
    warmup: int,
    samples: int,
) -> list[int]:
    loop = asyncio.get_running_loop()
    timings: list[int] = []
    for index in range(warmup + samples):
        started_ns = perf_counter_ns()
        await loop.run_in_executor(
            executor,
            _connect_configure_close,
            database_path,
            busy_timeout_ms,
        )
        elapsed_ns = perf_counter_ns() - started_ns
        if index >= warmup:
            timings.append(elapsed_ns)
    return timings


def _turn(index: int) -> DialogTurn:
    return DialogTurn(
        turn_id=f"turn-{index}",
        created_at=BASE_NOW + timedelta(microseconds=index),
        selection=SELECTION,
        state_version_at_answer=1,
        status="complete",
        text=DIALOG_TEXT,
    )


async def _create_empty(
    persistence: SqliteSessionPersistence,
    session_id: str,
) -> None:
    created = await persistence.sessions.create(session_id, now=BASE_NOW)
    if not isinstance(created, SessionCreated):
        raise BenchmarkInvariantError(f"create did not insert {session_id}")


async def _create_populated(
    persistence: SqliteSessionPersistence,
    session_id: str,
) -> None:
    await _create_empty(persistence, session_id)
    committed = await persistence.sessions.compare_and_set(
        session_id,
        0,
        DELTA,
        now=BASE_NOW,
    )
    if committed != 1:
        raise BenchmarkInvariantError(f"populate CAS did not commit {session_id}")


async def _create_with_dialog(
    persistence: SqliteSessionPersistence,
    session_id: str,
    index: int,
) -> None:
    await _create_populated(persistence, session_id)
    appended = await persistence.dialogs.append(
        session_id,
        _turn(index),
        now=BASE_NOW,
    )
    if appended is not None:
        raise BenchmarkInvariantError(f"append setup failed for {session_id}")


async def _delete(persistence: SqliteSessionPersistence, session_id: str) -> None:
    await persistence.delete(session_id)


async def _run_operation_series(
    *,
    name: str,
    persistence: SqliteSessionPersistence,
    warmup: int,
    samples: int,
    setup: Callable[[str, int], Awaitable[None]],
    operation: Callable[[str, int], Awaitable[Any]],
    validate: Callable[[Any], bool],
    cleanup: Callable[[str], Awaitable[None]] | None = None,
) -> list[int]:
    timings: list[int] = []
    for index in range(warmup + samples):
        session_id = f"bench-{name}-{index}"
        await setup(session_id, index)
        elapsed_ns, result = await _timed(operation(session_id, index))
        if not validate(result):
            raise BenchmarkInvariantError(
                f"unexpected result in {name} sample {index}: {result!r}"
            )
        if index >= warmup:
            timings.append(elapsed_ns)
        if cleanup is not None:
            await cleanup(session_id)
    return timings


async def _benchmark_public_operations(
    persistence: SqliteSessionPersistence,
    *,
    warmup: int,
    samples: int,
) -> dict[str, list[int]]:
    async def empty(session_id: str, _: int) -> None:
        await _create_empty(persistence, session_id)

    async def populated(session_id: str, _: int) -> None:
        await _create_populated(persistence, session_id)

    async def with_dialog(session_id: str, index: int) -> None:
        await _create_with_dialog(persistence, session_id, index)

    async def cleanup(session_id: str) -> None:
        await _delete(persistence, session_id)

    series: dict[str, list[int]] = {}
    series["successful_cas"] = await _run_operation_series(
        name="successful-cas",
        persistence=persistence,
        warmup=warmup,
        samples=samples,
        setup=empty,
        operation=lambda session_id, _: persistence.sessions.compare_and_set(
            session_id,
            0,
            DELTA,
            now=BASE_NOW,
        ),
        validate=lambda result: result == 1,
        cleanup=cleanup,
    )
    series["version_conflict"] = await _run_operation_series(
        name="version-conflict",
        persistence=persistence,
        warmup=warmup,
        samples=samples,
        setup=populated,
        operation=lambda session_id, _: persistence.sessions.compare_and_set(
            session_id,
            0,
            OTHER_DELTA,
            now=BASE_NOW,
        ),
        validate=lambda result: isinstance(result, VersionConflict),
        cleanup=cleanup,
    )
    series["append"] = await _run_operation_series(
        name="append",
        persistence=persistence,
        warmup=warmup,
        samples=samples,
        setup=populated,
        operation=lambda session_id, index: persistence.dialogs.append(
            session_id,
            _turn(index),
            now=BASE_NOW,
        ),
        validate=lambda result: result is None,
        cleanup=cleanup,
    )
    series["clear"] = await _run_operation_series(
        name="clear",
        persistence=persistence,
        warmup=warmup,
        samples=samples,
        setup=with_dialog,
        operation=lambda session_id, _: persistence.dialogs.clear(
            session_id,
            now=BASE_NOW,
        ),
        validate=lambda result: result is None,
        cleanup=cleanup,
    )
    series["touch"] = await _run_operation_series(
        name="touch",
        persistence=persistence,
        warmup=warmup,
        samples=samples,
        setup=with_dialog,
        operation=lambda session_id, _: persistence.touch(
            session_id,
            now=BASE_NOW,
        ),
        validate=lambda result: isinstance(result, SessionSnapshot),
        cleanup=cleanup,
    )
    series["reset"] = await _run_operation_series(
        name="reset",
        persistence=persistence,
        warmup=warmup,
        samples=samples,
        setup=with_dialog,
        operation=lambda session_id, _: persistence.reset(
            session_id,
            1,
            now=BASE_NOW,
        ),
        validate=lambda result: result == 2,
        cleanup=cleanup,
    )
    series["delete"] = await _run_operation_series(
        name="delete",
        persistence=persistence,
        warmup=warmup,
        samples=samples,
        setup=with_dialog,
        operation=lambda session_id, _: persistence.delete(session_id),
        validate=lambda result: result is None,
    )
    return series


async def _timed_competing_cas(
    persistence: SqliteSessionPersistence,
    session_id: str,
    barrier: asyncio.Barrier,
) -> tuple[int, int | StateWriteError]:
    await barrier.wait()
    started_ns = perf_counter_ns()
    try:
        result = await persistence.sessions.compare_and_set(
            session_id,
            0,
            DELTA,
            now=BASE_NOW,
        )
    except StateWriteError as exc:
        return perf_counter_ns() - started_ns, exc
    return perf_counter_ns() - started_ns, result


async def _benchmark_competing_writers(
    primary: SqliteSessionPersistence,
    peer: SqliteSessionPersistence,
    *,
    warmup: int,
    samples: int,
) -> tuple[list[int], int]:
    timings: list[int] = []
    typed_busy_count = 0
    total_observations = warmup + samples
    pair_index = 0
    observed = 0

    while observed < total_observations:
        first_id = f"bench-competing-{pair_index}-a"
        second_id = f"bench-competing-{pair_index}-b"
        await _create_empty(primary, first_id)
        await _create_empty(primary, second_id)

        barrier = asyncio.Barrier(2)
        results = await asyncio.gather(
            _timed_competing_cas(primary, first_id, barrier),
            _timed_competing_cas(peer, second_id, barrier),
        )

        for elapsed_ns, result in results:
            if observed >= total_observations:
                break
            if isinstance(result, StateWriteError):
                if result.error_code != BUSY_ERROR_CODE:
                    raise BenchmarkInvariantError(
                        "competing writer returned a non-BUSY StateWriteError"
                    )
                if observed >= warmup:
                    typed_busy_count += 1
            elif result != 1:
                raise BenchmarkInvariantError(
                    f"unexpected competing-writer result: {result!r}"
                )
            if observed >= warmup:
                timings.append(elapsed_ns)
            observed += 1

        await primary.delete(first_id)
        await primary.delete(second_id)
        pair_index += 1

    return timings, typed_busy_count


def _read_effective_pragmas(
    database_path: Path,
    busy_timeout_ms: int,
) -> dict[str, str | int]:
    connection = sqlite3.connect(str(database_path), timeout=0, isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
        connection.execute("PRAGMA synchronous = NORMAL")
        return {
            "foreign_keys": connection.execute("PRAGMA foreign_keys").fetchone()[0],
            "busy_timeout_ms": connection.execute(
                "PRAGMA busy_timeout"
            ).fetchone()[0],
            "journal_mode": connection.execute("PRAGMA journal_mode").fetchone()[0],
            "synchronous": connection.execute("PRAGMA synchronous").fetchone()[0],
        }
    finally:
        connection.close()


def _read_payload_sizes(database_path: Path, session_id: str) -> dict[str, int]:
    connection = sqlite3.connect(str(database_path), timeout=0, isolation_level=None)
    try:
        row = connection.execute(
            """
            SELECT
                length(CAST(states.state_json AS BLOB)),
                length(CAST(dialogs.turns_json AS BLOB))
            FROM session_states AS states
            JOIN session_dialogs AS dialogs USING (session_id)
            WHERE states.session_id = ?
            """,
            (session_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise BenchmarkInvariantError("representative payload row was not persisted")
    return {
        "state_json_bytes": row[0],
        "dialog_json_bytes": row[1],
        "dialog_text_characters": len(DIALOG_TEXT),
    }


async def _run_benchmark(
    args: argparse.Namespace,
    root: Path,
    executor: ThreadPoolExecutor,
) -> dict[str, Any]:
    from exact_orb.session.adapters.sqlite import SqliteSessionPersistence

    initialization = await _benchmark_initialization(
        root,
        executor,
        SqliteSessionPersistence,
        busy_timeout_ms=args.busy_timeout_ms,
        warmup=args.warmup,
        samples=args.samples,
    )

    database_path = root / "session-benchmark.sqlite3"
    if database_path.exists():
        raise BenchmarkInvariantError(f"benchmark refuses to overwrite {database_path}")

    primary = await SqliteSessionPersistence.open(
        database_path,
        executor=executor,
        busy_timeout_ms=args.busy_timeout_ms,
    )
    peer = await SqliteSessionPersistence.open(
        database_path,
        executor=executor,
        busy_timeout_ms=args.busy_timeout_ms,
    )

    effective_pragmas = await asyncio.get_running_loop().run_in_executor(
        executor,
        _read_effective_pragmas,
        database_path,
        args.busy_timeout_ms,
    )
    steady_connection = await _benchmark_steady_connection(
        database_path,
        executor,
        busy_timeout_ms=args.busy_timeout_ms,
        warmup=args.warmup,
        samples=args.samples,
    )

    representative_id = "bench-representative-payload"
    await _create_with_dialog(primary, representative_id, 0)
    payload_sizes = await asyncio.get_running_loop().run_in_executor(
        executor,
        _read_payload_sizes,
        database_path,
        representative_id,
    )

    operation_timings = await _benchmark_public_operations(
        primary,
        warmup=args.warmup,
        samples=args.samples,
    )
    competing_timings, typed_busy_count = await _benchmark_competing_writers(
        primary,
        peer,
        warmup=args.warmup,
        samples=args.samples,
    )
    await primary.delete(representative_id)

    completed_series = {
        "initialization": initialization,
        "steady_connect_configure_close": steady_connection,
        **operation_timings,
        "competing_writers": competing_timings,
    }
    incomplete = {
        name: len(values)
        for name, values in completed_series.items()
        if len(values) != args.samples
    }
    if incomplete:
        raise BenchmarkInvariantError(
            f"incomplete timing series (expected {args.samples}): {incomplete}"
        )

    metrics = {
        "initialization": _summary(initialization),
        "steady_connect_configure_close": _summary(steady_connection),
        **{
            f"full_{name}": _summary(values)
            for name, values in operation_timings.items()
        },
        "full_competing_writers": {
            **_summary(competing_timings),
            "typed_busy_count": typed_busy_count,
        },
    }

    return {
        "metadata": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "sqlite": sqlite3.sqlite_version,
            "os": platform.platform(),
            "process_id": os.getpid(),
            "workers": args.workers,
            "samples": args.samples,
            "warmup": args.warmup,
            "busy_timeout_ms": args.busy_timeout_ms,
            "path_class": "isolated_temporary_file_backed",
            "database_parent": str(root.parent),
        },
        "connection_configuration": {
            "initialization_statements": [
                "PRAGMA foreign_keys = ON",
                "PRAGMA foreign_keys",
                f"PRAGMA busy_timeout = {args.busy_timeout_ms}",
                "PRAGMA busy_timeout",
                "PRAGMA journal_mode",
                "PRAGMA journal_mode = WAL",
                "PRAGMA synchronous = NORMAL",
                "PRAGMA synchronous",
            ],
            "steady_statements": [
                "PRAGMA foreign_keys = ON",
                "PRAGMA foreign_keys",
                f"PRAGMA busy_timeout = {args.busy_timeout_ms}",
                "PRAGMA busy_timeout",
                "PRAGMA synchronous = NORMAL",
                "PRAGMA synchronous",
            ],
            "effective": effective_pragmas,
        },
        "payload": payload_sizes,
        "metrics": metrics,
        "limitations": [
            "Machine-specific evidence; these measurements are not an SLA.",
            "Steady connection timing includes executor scheduling and the "
            "production connect/configure/read-back/close sequence, but no SQL "
            "transaction or public-port work.",
            "Competing writers use two public aggregate handles and distinct "
            "session rows; scheduler and filesystem behavior remain host-specific.",
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        with _benchmark_directory(args.database_dir) as root:
            with ThreadPoolExecutor(
                max_workers=args.workers,
                thread_name_prefix="session-sqlite-benchmark",
            ) as executor:
                result = asyncio.run(_run_benchmark(args, root, executor))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (KeyboardInterrupt, Exception) as exc:
        print(
            f"session SQLite benchmark failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
