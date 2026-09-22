"""Read-only SQLite adapter for place lookup lifecycle and startup checks."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from importlib import metadata
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from exact_orb.birth.places import (
    PlaceCatalogUnavailableError,
    PlaceNotFound,
    PlaceResolution,
    ResolvedPlace,
    normalize_place_query,
)


_LOGGER = logging.getLogger(__name__)

_SCHEMA_VERSION = 1
_MAX_PLACE_ID_LENGTH = 32
_REQUIRED_TABLE_COLUMNS = {
    "places": (
        "place_id",
        "display_name",
        "name_ascii",
        "country_code",
        "admin1_code",
        "admin1_name",
        "latitude_e2",
        "longitude_e2",
        "tz_id",
        "population",
    ),
    "place_names": (
        "place_name_id",
        "place_id",
        "name",
        "search_key",
        "language",
        "preferred",
        "historic",
    ),
    "catalog_metadata": (
        "singleton",
        "schema_version",
        "source_checksums",
        "build_parameters",
    ),
}
_REQUIRED_INDEXES = frozenset(
    {"idx_place_names_search_key", "idx_place_names_place_id"}
)
_SOURCE_CHECKSUM_KEYS = frozenset({"admin1", "alternate_names", "cities"})
_BUILD_PARAMETER_KEYS = frozenset(
    {
        "allowed_alternate_languages",
        "excluded_feature_codes",
        "feature_class",
        "full_countries",
        "other_min_population",
        "tzdata_version",
    }
)
_LOWERCASE_HEX = frozenset("0123456789abcdef")


class _CatalogValidationError(RuntimeError):
    """The opened SQLite artifact does not satisfy schema v1."""


class SqlitePlaceCatalog:
    """One read-only place catalog bound to one caller-owned worker."""

    def __init__(self, *, executor: ThreadPoolExecutor) -> None:
        self._executor = _validate_executor(executor)
        self._connection: sqlite3.Connection | None = None
        self._opened = False
        self._closed = False
        self._close_future: asyncio.Future[None] | None = None

    @classmethod
    async def open(
        cls,
        db_path: str | Path,
        /,
        *,
        executor: ThreadPoolExecutor,
    ) -> Self:
        path = _validate_db_path_argument(db_path)
        catalog = cls(executor=executor)
        loop = asyncio.get_running_loop()
        try:
            open_future = loop.run_in_executor(
                catalog._executor,
                _sync_open_and_validate,
                path,
            )
        except Exception as exc:
            raise PlaceCatalogUnavailableError(
                "place catalog open could not be scheduled"
            ) from exc

        try:
            connection = await asyncio.shield(open_future)
        except asyncio.CancelledError as cancelled:
            await _finish_cancelled_open(open_future, catalog._executor)
            raise cancelled
        except Exception as exc:
            raise PlaceCatalogUnavailableError(
                "place catalog could not be opened"
            ) from exc

        catalog._connection = connection
        catalog._opened = True
        return catalog

    async def lookup(self, place_id: str) -> PlaceResolution:
        if not isinstance(place_id, str):
            raise TypeError("place_id must be str")
        connection = self._require_open_connection()
        if not _is_valid_place_id(place_id):
            return PlaceNotFound(place_id=place_id)

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                self._executor,
                _sync_lookup,
                connection,
                place_id,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise PlaceCatalogUnavailableError(
                "place catalog lookup failed"
            ) from exc

    async def aclose(self) -> None:
        close_future = self._close_future
        if close_future is None:
            connection = self._connection
            self._closed = True
            self._opened = False
            if connection is None:
                return

            loop = asyncio.get_running_loop()
            try:
                close_future = loop.run_in_executor(
                    self._executor,
                    _sync_close,
                    connection,
                )
            except Exception as exc:
                raise PlaceCatalogUnavailableError(
                    "place catalog close could not be scheduled"
                ) from exc
            self._connection = None
            self._close_future = close_future

        try:
            await asyncio.shield(close_future)
        except asyncio.CancelledError as cancelled:
            await _finish_cancelled_close(close_future)
            raise cancelled
        except Exception as exc:
            raise PlaceCatalogUnavailableError(
                "place catalog close failed"
            ) from exc

    def _require_open_connection(self) -> sqlite3.Connection:
        if self._closed or not self._opened or self._connection is None:
            raise PlaceCatalogUnavailableError("place catalog is not open")
        return self._connection


def _validate_executor(executor: ThreadPoolExecutor) -> ThreadPoolExecutor:
    if not isinstance(executor, ThreadPoolExecutor):
        raise TypeError("executor must be ThreadPoolExecutor")
    if getattr(executor, "_max_workers", None) != 1:
        raise ValueError("executor must have max_workers=1")
    return executor


def _validate_db_path_argument(db_path: str | Path) -> Path:
    if not isinstance(db_path, (str, Path)):
        raise TypeError("db_path must be str or Path")
    raw_path = str(db_path)
    if raw_path == "" or raw_path == ":memory:" or raw_path.startswith("file:"):
        raise ValueError("db_path must identify a file-backed SQLite database")
    return Path(db_path)


async def _finish_cancelled_open(
    open_future: asyncio.Future[sqlite3.Connection],
    executor: ThreadPoolExecutor,
) -> None:
    try:
        connection = await asyncio.shield(open_future)
    except Exception:
        return

    loop = asyncio.get_running_loop()
    try:
        close_future = loop.run_in_executor(executor, _sync_close, connection)
        await asyncio.shield(close_future)
    except Exception:
        _LOGGER.warning(
            "place catalog connection cleanup failed after cancelled open",
            exc_info=True,
        )


async def _finish_cancelled_close(close_future: asyncio.Future[None]) -> None:
    try:
        await asyncio.shield(close_future)
    except Exception:
        return


def _sync_open_and_validate(db_path: Path) -> sqlite3.Connection:
    resolved_path = db_path.resolve(strict=True)
    if not resolved_path.is_file():
        raise _CatalogValidationError("place catalog path is not a file")

    uri = f"{resolved_path.as_uri()}?mode=ro"
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(
            uri,
            uri=True,
            check_same_thread=True,
        )
        connection.execute("PRAGMA query_only = ON")
        _validate_catalog(connection)
        return connection
    except BaseException:
        if connection is not None:
            connection.close()
        raise


def _validate_catalog(connection: sqlite3.Connection) -> None:
    if connection.execute("PRAGMA user_version").fetchone() != (_SCHEMA_VERSION,):
        raise _CatalogValidationError("unexpected catalog user_version")

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing_tables = set(_REQUIRED_TABLE_COLUMNS) - tables
    if missing_tables:
        raise _CatalogValidationError(
            f"missing catalog tables: {sorted(missing_tables)!r}"
        )

    for table, expected_columns in _REQUIRED_TABLE_COLUMNS.items():
        columns = tuple(
            row[1] for row in connection.execute(f"PRAGMA table_info({table})")
        )
        if columns != expected_columns:
            raise _CatalogValidationError(
                f"unexpected columns for catalog table {table}"
            )

    _validate_indexes(connection)
    catalog_tzdata_version = _validate_metadata(connection)
    runtime_tzdata_version = metadata.version("tzdata")
    if catalog_tzdata_version != runtime_tzdata_version:
        _LOGGER.warning(
            "place_catalog_tzdata_version_mismatch",
            extra={
                "catalog_tzdata_version": catalog_tzdata_version,
                "runtime_tzdata_version": runtime_tzdata_version,
            },
        )
    _validate_timezone_keys(connection)


def _validate_indexes(connection: sqlite3.Connection) -> None:
    indexes = {
        row[1] for row in connection.execute("PRAGMA index_list(place_names)")
    }
    missing_indexes = _REQUIRED_INDEXES - indexes
    if missing_indexes:
        raise _CatalogValidationError(
            f"missing catalog indexes: {sorted(missing_indexes)!r}"
        )

    search_columns = [
        (row[2], row[4])
        for row in connection.execute(
            "PRAGMA index_xinfo(idx_place_names_search_key)"
        )
        if row[5] == 1
    ]
    if search_columns != [("search_key", "BINARY"), ("place_id", "BINARY")]:
        raise _CatalogValidationError("unexpected place-name search index")

    place_id_columns = [
        row[2]
        for row in connection.execute("PRAGMA index_xinfo(idx_place_names_place_id)")
        if row[5] == 1
    ]
    if place_id_columns != ["place_id"]:
        raise _CatalogValidationError("unexpected place-name place_id index")


def _validate_metadata(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        """
        SELECT singleton, schema_version, source_checksums, build_parameters
        FROM catalog_metadata
        ORDER BY singleton
        """
    ).fetchall()
    if len(rows) != 1 or rows[0][0] != 1 or rows[0][1] != _SCHEMA_VERSION:
        raise _CatalogValidationError("invalid catalog metadata singleton")

    try:
        source_checksums = json.loads(rows[0][2])
        build_parameters = json.loads(rows[0][3])
    except (TypeError, json.JSONDecodeError) as exc:
        raise _CatalogValidationError("catalog metadata is not valid JSON") from exc

    if not isinstance(source_checksums, dict) or set(source_checksums) != set(
        _SOURCE_CHECKSUM_KEYS
    ):
        raise _CatalogValidationError("invalid catalog source checksums")
    if not all(_is_lowercase_sha256(value) for value in source_checksums.values()):
        raise _CatalogValidationError("invalid catalog source checksum value")

    if not isinstance(build_parameters, dict) or set(build_parameters) != set(
        _BUILD_PARAMETER_KEYS
    ):
        raise _CatalogValidationError("invalid catalog build parameters")
    if build_parameters["allowed_alternate_languages"] != ["ru"]:
        raise _CatalogValidationError("invalid alternate-language allow-list")
    if build_parameters["excluded_feature_codes"] != ["PPLH", "PPLW", "PPLX"]:
        raise _CatalogValidationError("invalid excluded feature codes")
    if build_parameters["feature_class"] != "P":
        raise _CatalogValidationError("invalid feature class")

    countries = build_parameters["full_countries"]
    if (
        not isinstance(countries, list)
        or not countries
        or countries != sorted(set(countries))
        or any(
            not isinstance(code, str)
            or len(code) != 2
            or not code.isascii()
            or not code.isalpha()
            or code != code.upper()
            for code in countries
        )
    ):
        raise _CatalogValidationError("invalid full-country filter")

    population = build_parameters["other_min_population"]
    if type(population) is not int or population < 0:
        raise _CatalogValidationError("invalid population filter")

    tzdata_version = build_parameters["tzdata_version"]
    if not isinstance(tzdata_version, str) or not tzdata_version:
        raise _CatalogValidationError("invalid catalog tzdata version")
    return tzdata_version


def _validate_timezone_keys(connection: sqlite3.Connection) -> None:
    for (tz_id,) in connection.execute(
        "SELECT DISTINCT tz_id FROM places ORDER BY tz_id"
    ):
        if not isinstance(tz_id, str) or not tz_id:
            raise _CatalogValidationError("invalid catalog timezone key")
        try:
            ZoneInfo(tz_id)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise _CatalogValidationError(
                "catalog contains an unresolved timezone key"
            ) from exc


def _is_lowercase_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in _LOWERCASE_HEX for character in value)
    )


def _is_valid_place_id(place_id: str) -> bool:
    return (
        0 < len(place_id) <= _MAX_PLACE_ID_LENGTH
        and place_id.isascii()
        and place_id.isdigit()
    )


def _sync_lookup(
    connection: sqlite3.Connection,
    place_id: str,
) -> PlaceResolution:
    row = connection.execute(
        """
        SELECT display_name, latitude_e2, longitude_e2, tz_id
        FROM places
        WHERE place_id = ?
        """,
        (place_id,),
    ).fetchone()
    if row is None:
        return PlaceNotFound(place_id=place_id)
    return ResolvedPlace(
        place_id=place_id,
        canonical_name=row[0],
        latitude=row[1] / 100,
        longitude=row[2] / 100,
        tz_id=row[3],
    )


def _sync_close(connection: sqlite3.Connection) -> None:
    connection.close()


__all__ = ["SqlitePlaceCatalog"]
