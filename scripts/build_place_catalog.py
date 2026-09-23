#!/usr/bin/env python3
"""Build a deterministic SQLite place catalog from local GeoNames dumps.

The three required inputs are ``cities1000.txt``, ``admin1CodesASCII.txt``,
and ``alternateNamesV2.txt`` from the GeoNames export. The builder performs no
network access and publishes the new database only after full validation.

GeoNames data is distributed under Creative Commons Attribution. Product UI
must show attribution, and the current license text must be reviewed before
release.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
from importlib import metadata, resources
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

from exact_orb.birth.places import (
    ALLOWED_ALTERNATE_LANGUAGES,
    normalize_place_query,
)


SCHEMA_VERSION = 1
COORDINATE_QUANT = Decimal("0.01")
DEFAULT_FULL_COUNTRIES = frozenset(
    {
        "RU",
        "UA",
        "BY",
        "KZ",
        "MD",
        "AM",
        "GE",
        "AZ",
        "KG",
        "UZ",
        "TJ",
        "TM",
        "LT",
        "LV",
        "EE",
    }
)
DEFAULT_OTHER_MIN_POPULATION = 100_000
POPULATED_PLACE_CLASS = "P"
EXCLUDED_FEATURE_CODES = frozenset({"PPLX", "PPLH", "PPLW"})

GEONAMEID = 0
NAME = 1
ASCIINAME = 2
LATITUDE = 4
LONGITUDE = 5
FEATURE_CLASS = 6
FEATURE_CODE = 7
COUNTRY_CODE = 8
ADMIN1_CODE = 10
POPULATION = 14
TIMEZONE = 17
CITY_COLUMN_COUNT = 19

ADMIN1_KEY = 0
ADMIN1_NAME = 1
ADMIN1_ASCII_NAME = 2
ADMIN1_GEONAMEID = 3
ADMIN1_COLUMN_COUNT = 4

ALTERNATE_NAME_ID = 0
ALTERNATE_GEONAMEID = 1
ALTERNATE_LANGUAGE = 2
ALTERNATE_NAME = 3
ALTERNATE_PREFERRED = 4
ALTERNATE_HISTORIC = 7
ALTERNATE_TO = 9
ALTERNATE_REQUIRED_COLUMN_COUNT = 8
ALTERNATE_LOGICAL_COLUMN_COUNT = 10

REQUIRED_TABLE_COLUMNS = {
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
REQUIRED_INDEXES = frozenset(
    {"idx_place_names_search_key", "idx_place_names_place_id"}
)


class CatalogBuildError(ValueError):
    """An input or output invariant prevents publishing a catalog."""


@dataclass(frozen=True, slots=True)
class Admin1Record:
    ascii_name: str
    geoname_id: str


@dataclass(frozen=True, slots=True)
class PlaceRecord:
    place_id: str
    source_name: str
    name_ascii: str
    country_code: str
    admin1_code: str
    admin1_geoname_id: str | None
    admin1_ascii_name: str | None
    latitude_e2: int
    longitude_e2: int
    tz_id: str
    population: int


@dataclass(frozen=True, slots=True)
class AlternateNameRecord:
    alternate_name_id: int
    name: str
    preferred: bool
    historic: bool


@dataclass(frozen=True, slots=True)
class PlaceNameRow:
    name: str
    search_key: str
    language: str | None
    preferred: int
    historic: int


@dataclass(slots=True)
class BuildStatistics:
    admin1_rows_read: int = 0
    cities_rows_read: int = 0
    alternate_names_rows_read: int = 0
    places_written: int = 0
    place_names_written: int = 0
    filtered_feature_class: int = 0
    filtered_feature_code: int = 0
    filtered_country_population: int = 0
    filtered_timezone: int = 0
    filtered_alternate_language: int = 0
    rejected_names: int = 0


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _statistics_json(statistics: BuildStatistics) -> str:
    return json.dumps(
        asdict(statistics),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _decode_line(raw_line: bytes, *, path: Path, line_number: int) -> str:
    try:
        return raw_line.decode("utf-8").rstrip("\r\n")
    except UnicodeDecodeError as exc:
        raise CatalogBuildError(
            f"{path}: line {line_number}: invalid UTF-8"
        ) from exc


def _require_columns(
    parts: list[str],
    *,
    minimum: int,
    path: Path,
    line_number: int,
) -> None:
    if len(parts) < minimum:
        raise CatalogBuildError(
            f"{path}: line {line_number}: expected at least {minimum} "
            f"tab-separated columns, got {len(parts)}"
        )


def _require_numeric_id(
    value: str,
    *,
    field: str,
    path: Path,
    line_number: int,
) -> str:
    if not value or not value.isascii() or not value.isdigit():
        raise CatalogBuildError(
            f"{path}: line {line_number}: {field} must contain ASCII digits"
        )
    return value


def _parse_non_negative_int(
    value: str,
    *,
    field: str,
    path: Path,
    line_number: int,
) -> int:
    try:
        parsed = int(value or "0")
    except ValueError as exc:
        raise CatalogBuildError(
            f"{path}: line {line_number}: invalid {field} {value!r}"
        ) from exc
    if parsed < 0:
        raise CatalogBuildError(
            f"{path}: line {line_number}: {field} must be non-negative"
        )
    return parsed


def _parse_flag(
    value: str,
    *,
    field: str,
    path: Path,
    line_number: int,
) -> bool:
    if value in ("", "0"):
        return False
    if value == "1":
        return True
    raise CatalogBuildError(
        f"{path}: line {line_number}: {field} must be empty, 0, or 1"
    )


def _coordinate_e2(
    value: str,
    *,
    field: str,
    minimum: Decimal,
    maximum: Decimal,
    path: Path,
    line_number: int,
) -> int:
    try:
        coordinate = Decimal(value)
    except InvalidOperation as exc:
        raise CatalogBuildError(
            f"{path}: line {line_number}: invalid {field} {value!r}"
        ) from exc
    if not coordinate.is_finite() or not minimum <= coordinate <= maximum:
        raise CatalogBuildError(
            f"{path}: line {line_number}: {field} outside {minimum}..{maximum}"
        )
    rounded = coordinate.quantize(COORDINATE_QUANT, rounding=ROUND_HALF_UP)
    return int(rounded * 100)


def _resolve_input_file(path: Path, *, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CatalogBuildError(f"missing required {label} file: {path}") from exc
    if not resolved.is_file():
        raise CatalogBuildError(f"required {label} path is not a file: {path}")
    return resolved


def _tzdata_context() -> tuple[str, frozenset[str]]:
    try:
        version = metadata.version("tzdata")
        zones_text = (
            resources.files("tzdata")
            .joinpath("zones")
            .read_text(encoding="utf-8")
        )
    except (
        metadata.PackageNotFoundError,
        FileNotFoundError,
        ModuleNotFoundError,
    ) as exc:
        raise CatalogBuildError(
            "installed Python distribution tzdata with its zones file is required"
        ) from exc

    zones = frozenset(line.strip() for line in zones_text.splitlines() if line.strip())
    if not zones:
        raise CatalogBuildError("installed tzdata distribution contains no zone keys")
    return version, zones


def _load_admin1(
    path: Path,
    *,
    statistics: BuildStatistics,
) -> tuple[dict[str, Admin1Record], str]:
    records: dict[str, Admin1Record] = {}
    checksum = hashlib.sha256()

    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            checksum.update(raw_line)
            statistics.admin1_rows_read += 1
            line = _decode_line(raw_line, path=path, line_number=line_number)
            if not line:
                continue
            parts = line.split("\t")
            _require_columns(
                parts,
                minimum=ADMIN1_COLUMN_COUNT,
                path=path,
                line_number=line_number,
            )
            key = parts[ADMIN1_KEY]
            if not key or "." not in key:
                raise CatalogBuildError(
                    f"{path}: line {line_number}: invalid admin1 key {key!r}"
                )
            geoname_id = _require_numeric_id(
                parts[ADMIN1_GEONAMEID],
                field="admin1 geoname_id",
                path=path,
                line_number=line_number,
            )
            ascii_name = parts[ADMIN1_ASCII_NAME] or parts[ADMIN1_NAME]
            if not ascii_name:
                raise CatalogBuildError(
                    f"{path}: line {line_number}: admin1 name is empty"
                )
            if key in records:
                raise CatalogBuildError(
                    f"{path}: line {line_number}: duplicate admin1 key {key!r}"
                )
            records[key] = Admin1Record(
                ascii_name=ascii_name,
                geoname_id=geoname_id,
            )

    return records, checksum.hexdigest()


def _load_places(
    path: Path,
    *,
    admin1: dict[str, Admin1Record],
    full_countries: frozenset[str],
    other_min_population: int,
    timezone_keys: frozenset[str],
    statistics: BuildStatistics,
) -> tuple[dict[str, PlaceRecord], str]:
    places: dict[str, PlaceRecord] = {}
    checksum = hashlib.sha256()

    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            checksum.update(raw_line)
            statistics.cities_rows_read += 1
            line = _decode_line(raw_line, path=path, line_number=line_number)
            if not line:
                continue
            parts = line.split("\t")
            _require_columns(
                parts,
                minimum=CITY_COLUMN_COUNT,
                path=path,
                line_number=line_number,
            )

            if parts[FEATURE_CLASS] != POPULATED_PLACE_CLASS:
                statistics.filtered_feature_class += 1
                continue
            if parts[FEATURE_CODE] in EXCLUDED_FEATURE_CODES:
                statistics.filtered_feature_code += 1
                continue

            timezone = parts[TIMEZONE]
            if not timezone or timezone not in timezone_keys:
                statistics.filtered_timezone += 1
                continue

            country_code = parts[COUNTRY_CODE].upper()
            if (
                len(country_code) != 2
                or not country_code.isascii()
                or not country_code.isalpha()
            ):
                raise CatalogBuildError(
                    f"{path}: line {line_number}: invalid country code "
                    f"{parts[COUNTRY_CODE]!r}"
                )
            population = _parse_non_negative_int(
                parts[POPULATION],
                field="population",
                path=path,
                line_number=line_number,
            )
            if (
                country_code not in full_countries
                and population < other_min_population
            ):
                statistics.filtered_country_population += 1
                continue

            place_id = _require_numeric_id(
                parts[GEONAMEID],
                field="place_id",
                path=path,
                line_number=line_number,
            )
            if place_id in places:
                raise CatalogBuildError(
                    f"{path}: line {line_number}: duplicate selected place_id "
                    f"{place_id}"
                )

            source_name = parts[NAME]
            name_ascii = parts[ASCIINAME]
            if not source_name or not name_ascii:
                raise CatalogBuildError(
                    f"{path}: line {line_number}: source and ASCII names are required"
                )

            admin1_code = parts[ADMIN1_CODE]
            admin1_record = admin1.get(f"{country_code}.{admin1_code}")
            places[place_id] = PlaceRecord(
                place_id=place_id,
                source_name=source_name,
                name_ascii=name_ascii,
                country_code=country_code,
                admin1_code=admin1_code,
                admin1_geoname_id=(
                    admin1_record.geoname_id if admin1_record is not None else None
                ),
                admin1_ascii_name=(
                    admin1_record.ascii_name if admin1_record is not None else None
                ),
                latitude_e2=_coordinate_e2(
                    parts[LATITUDE],
                    field="latitude",
                    minimum=Decimal("-90"),
                    maximum=Decimal("90"),
                    path=path,
                    line_number=line_number,
                ),
                longitude_e2=_coordinate_e2(
                    parts[LONGITUDE],
                    field="longitude",
                    minimum=Decimal("-180"),
                    maximum=Decimal("180"),
                    path=path,
                    line_number=line_number,
                ),
                tz_id=timezone,
                population=population,
            )

    return places, checksum.hexdigest()


def _load_alternate_names(
    path: Path,
    *,
    relevant_ids: frozenset[str],
    statistics: BuildStatistics,
) -> tuple[dict[str, list[AlternateNameRecord]], str]:
    names: dict[str, list[AlternateNameRecord]] = {}
    checksum = hashlib.sha256()

    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            checksum.update(raw_line)
            statistics.alternate_names_rows_read += 1
            line = _decode_line(raw_line, path=path, line_number=line_number)
            if not line:
                continue
            parts = line.split("\t")
            _require_columns(
                parts,
                minimum=ALTERNATE_REQUIRED_COLUMN_COUNT,
                path=path,
                line_number=line_number,
            )
            if len(parts) < ALTERNATE_LOGICAL_COLUMN_COUNT:
                parts.extend([""] * (ALTERNATE_LOGICAL_COLUMN_COUNT - len(parts)))

            geoname_id = parts[ALTERNATE_GEONAMEID]
            if geoname_id not in relevant_ids:
                continue
            if parts[ALTERNATE_LANGUAGE] not in ALLOWED_ALTERNATE_LANGUAGES:
                statistics.filtered_alternate_language += 1
                continue

            alternate_name_id_text = _require_numeric_id(
                parts[ALTERNATE_NAME_ID],
                field="alternate_name_id",
                path=path,
                line_number=line_number,
            )
            preferred = _parse_flag(
                parts[ALTERNATE_PREFERRED],
                field="isPreferredName",
                path=path,
                line_number=line_number,
            )
            historic_flag = _parse_flag(
                parts[ALTERNATE_HISTORIC],
                field="isHistoric",
                path=path,
                line_number=line_number,
            )
            names.setdefault(geoname_id, []).append(
                AlternateNameRecord(
                    alternate_name_id=int(alternate_name_id_text),
                    name=parts[ALTERNATE_NAME],
                    preferred=preferred,
                    historic=historic_flag or bool(parts[ALTERNATE_TO]),
                )
            )

    for records in names.values():
        records.sort(key=lambda record: record.alternate_name_id)
    return names, checksum.hexdigest()


def _is_valid_name(name: str) -> bool:
    return isinstance(normalize_place_query(name), str)


def _current_ru_names(
    records: list[AlternateNameRecord],
) -> list[AlternateNameRecord]:
    return [
        record
        for record in records
        if not record.historic and _is_valid_name(record.name)
    ]


def _select_display_name(
    place: PlaceRecord,
    records: list[AlternateNameRecord],
) -> str:
    current = _current_ru_names(records)
    preferred = [record for record in current if record.preferred]
    if preferred:
        return min(preferred, key=lambda record: record.alternate_name_id).name
    if current:
        return min(current, key=lambda record: record.alternate_name_id).name
    if _is_valid_name(place.source_name):
        return place.source_name
    if _is_valid_name(place.name_ascii):
        return place.name_ascii
    raise CatalogBuildError(f"place {place.place_id} has no valid display name")


def _select_admin1_name(
    place: PlaceRecord,
    alternate_names: dict[str, list[AlternateNameRecord]],
) -> str | None:
    if place.admin1_geoname_id is not None:
        current = _current_ru_names(
            alternate_names.get(place.admin1_geoname_id, [])
        )
        preferred = [record for record in current if record.preferred]
        if preferred:
            return min(preferred, key=lambda record: record.alternate_name_id).name
        if current:
            return min(current, key=lambda record: record.alternate_name_id).name
    if place.admin1_ascii_name and _is_valid_name(place.admin1_ascii_name):
        return place.admin1_ascii_name
    return None


def _place_name_rows(
    place: PlaceRecord,
    records: list[AlternateNameRecord],
    *,
    statistics: BuildStatistics,
) -> tuple[PlaceNameRow, ...]:
    candidates: list[tuple[str, str | None, bool, bool]] = [
        (place.source_name, None, False, False),
        (place.name_ascii, None, False, False),
    ]
    candidates.extend(
        (record.name, "ru", record.preferred, record.historic)
        for record in records
    )

    result: list[PlaceNameRow] = []
    seen: set[tuple[str, str, str | None, int, int]] = set()
    for name, language, preferred, historic in candidates:
        search_key = normalize_place_query(name)
        if not isinstance(search_key, str):
            statistics.rejected_names += 1
            continue
        identity = (
            name,
            search_key,
            language,
            int(preferred),
            int(historic),
        )
        if identity in seen:
            continue
        seen.add(identity)
        result.append(
            PlaceNameRow(
                name=name,
                search_key=search_key,
                language=language,
                preferred=int(preferred),
                historic=int(historic),
            )
        )
    if not result:
        raise CatalogBuildError(f"place {place.place_id} has no valid search names")
    return tuple(result)


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        f"""
        PRAGMA foreign_keys = ON;
        PRAGMA user_version = {SCHEMA_VERSION};

        CREATE TABLE places (
            place_id TEXT PRIMARY KEY NOT NULL
                CHECK (place_id <> '' AND place_id NOT GLOB '*[^0-9]*'),
            display_name TEXT NOT NULL CHECK (display_name <> ''),
            name_ascii TEXT NOT NULL CHECK (name_ascii <> ''),
            country_code TEXT NOT NULL CHECK (length(country_code) = 2),
            admin1_code TEXT NOT NULL,
            admin1_name TEXT,
            latitude_e2 INTEGER NOT NULL
                CHECK (latitude_e2 BETWEEN -9000 AND 9000),
            longitude_e2 INTEGER NOT NULL
                CHECK (longitude_e2 BETWEEN -18000 AND 18000),
            tz_id TEXT NOT NULL CHECK (tz_id <> ''),
            population INTEGER NOT NULL CHECK (population >= 0)
        ) WITHOUT ROWID;

        CREATE TABLE place_names (
            place_name_id INTEGER PRIMARY KEY,
            place_id TEXT NOT NULL,
            name TEXT NOT NULL CHECK (name <> ''),
            search_key TEXT COLLATE BINARY NOT NULL CHECK (search_key <> ''),
            language TEXT,
            preferred INTEGER NOT NULL CHECK (preferred IN (0, 1)),
            historic INTEGER NOT NULL CHECK (historic IN (0, 1)),
            FOREIGN KEY (place_id) REFERENCES places(place_id)
        );

        CREATE INDEX idx_place_names_search_key
            ON place_names(search_key COLLATE BINARY, place_id);
        CREATE INDEX idx_place_names_place_id
            ON place_names(place_id);

        CREATE TABLE catalog_metadata (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            schema_version INTEGER NOT NULL,
            source_checksums TEXT NOT NULL,
            build_parameters TEXT NOT NULL
        );
        """
    )


def _place_id_sort_key(place_id: str) -> tuple[int, str]:
    return int(place_id), place_id


def _write_catalog(
    connection: sqlite3.Connection,
    *,
    places: dict[str, PlaceRecord],
    alternate_names: dict[str, list[AlternateNameRecord]],
    source_checksums: dict[str, str],
    build_parameters: dict[str, object],
    statistics: BuildStatistics,
) -> None:
    _create_schema(connection)
    connection.execute(
        """
        INSERT INTO catalog_metadata(
            singleton,
            schema_version,
            source_checksums,
            build_parameters
        ) VALUES (1, ?, ?, ?)
        """,
        (
            SCHEMA_VERSION,
            _canonical_json(source_checksums),
            _canonical_json(build_parameters),
        ),
    )

    place_name_id = 0
    for place_id in sorted(places, key=_place_id_sort_key):
        place = places[place_id]
        records = alternate_names.get(place_id, [])
        connection.execute(
            """
            INSERT INTO places(
                place_id,
                display_name,
                name_ascii,
                country_code,
                admin1_code,
                admin1_name,
                latitude_e2,
                longitude_e2,
                tz_id,
                population
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                place.place_id,
                _select_display_name(place, records),
                place.name_ascii,
                place.country_code,
                place.admin1_code,
                _select_admin1_name(place, alternate_names),
                place.latitude_e2,
                place.longitude_e2,
                place.tz_id,
                place.population,
            ),
        )
        statistics.places_written += 1

        for row in _place_name_rows(place, records, statistics=statistics):
            place_name_id += 1
            connection.execute(
                """
                INSERT INTO place_names(
                    place_name_id,
                    place_id,
                    name,
                    search_key,
                    language,
                    preferred,
                    historic
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    place_name_id,
                    place.place_id,
                    row.name,
                    row.search_key,
                    row.language,
                    row.preferred,
                    row.historic,
                ),
            )
            statistics.place_names_written += 1


def _validate_catalog(
    connection: sqlite3.Connection,
    *,
    timezone_keys: frozenset[str],
    source_checksums: dict[str, str],
    build_parameters: dict[str, object],
    statistics: BuildStatistics,
) -> None:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()
    if integrity != ("ok",):
        raise CatalogBuildError(f"SQLite integrity_check failed: {integrity!r}")
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise CatalogBuildError(
            f"SQLite foreign_key_check failed: {foreign_key_errors!r}"
        )

    user_version = connection.execute("PRAGMA user_version").fetchone()
    if user_version != (SCHEMA_VERSION,):
        raise CatalogBuildError(
            f"unexpected SQLite user_version: {user_version!r}"
        )

    for table, expected_columns in REQUIRED_TABLE_COLUMNS.items():
        columns = tuple(
            row[1] for row in connection.execute(f"PRAGMA table_info({table})")
        )
        if columns != expected_columns:
            raise CatalogBuildError(
                f"unexpected {table} columns: {columns!r}"
            )

    indexes = {
        row[1]
        for row in connection.execute("PRAGMA index_list(place_names)")
    }
    missing_indexes = REQUIRED_INDEXES - indexes
    if missing_indexes:
        raise CatalogBuildError(
            f"missing required SQLite indexes: {sorted(missing_indexes)!r}"
        )
    search_index_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?",
        ("idx_place_names_search_key",),
    ).fetchone()
    if (
        search_index_sql is None
        or "search_key COLLATE BINARY" not in search_index_sql[0]
    ):
        raise CatalogBuildError("search index must use BINARY collation")

    metadata_row = connection.execute(
        """
        SELECT schema_version, source_checksums, build_parameters
        FROM catalog_metadata
        WHERE singleton = 1
        """
    ).fetchone()
    if metadata_row is None or connection.execute(
        "SELECT COUNT(*) FROM catalog_metadata"
    ).fetchone() != (1,):
        raise CatalogBuildError("catalog_metadata must contain one singleton row")
    if metadata_row[0] != SCHEMA_VERSION:
        raise CatalogBuildError("catalog metadata schema_version mismatch")
    try:
        stored_checksums = json.loads(metadata_row[1])
        stored_parameters = json.loads(metadata_row[2])
    except (TypeError, json.JSONDecodeError) as exc:
        raise CatalogBuildError("catalog metadata contains invalid JSON") from exc
    if stored_checksums != source_checksums:
        raise CatalogBuildError("catalog source_checksums mismatch")
    if stored_parameters != build_parameters:
        raise CatalogBuildError("catalog build_parameters mismatch")

    if connection.execute("SELECT COUNT(*) FROM places").fetchone() != (
        statistics.places_written,
    ):
        raise CatalogBuildError("written places count mismatch")
    if connection.execute("SELECT COUNT(*) FROM place_names").fetchone() != (
        statistics.place_names_written,
    ):
        raise CatalogBuildError("written place names count mismatch")
    missing_names = connection.execute(
        """
        SELECT p.place_id
        FROM places AS p
        LEFT JOIN place_names AS pn ON pn.place_id = p.place_id
        WHERE pn.place_id IS NULL
        LIMIT 1
        """
    ).fetchone()
    if missing_names is not None:
        raise CatalogBuildError(
            f"place {missing_names[0]} has no indexed search name"
        )

    unresolved_timezones = sorted(
        row[0]
        for row in connection.execute("SELECT DISTINCT tz_id FROM places")
        if row[0] not in timezone_keys
    )
    if unresolved_timezones:
        raise CatalogBuildError(
            f"catalog contains unresolved timezone keys: {unresolved_timezones!r}"
        )


def build(
    *,
    cities_path: Path,
    admin1_path: Path,
    alternate_names_path: Path,
    out_path: Path,
    full_countries: frozenset[str] = DEFAULT_FULL_COUNTRIES,
    other_min_population: int = DEFAULT_OTHER_MIN_POPULATION,
) -> BuildStatistics:
    """Build, validate, and atomically publish one SQLite catalog."""

    if other_min_population < 0:
        raise CatalogBuildError("other_min_population must be non-negative")
    normalized_countries = frozenset(code.strip().upper() for code in full_countries)
    if not normalized_countries or any(
        len(code) != 2 or not code.isascii() or not code.isalpha()
        for code in normalized_countries
    ):
        raise CatalogBuildError("full_countries must contain ISO alpha-2 codes")

    cities_path = _resolve_input_file(cities_path, label="cities")
    admin1_path = _resolve_input_file(admin1_path, label="admin1")
    alternate_names_path = _resolve_input_file(
        alternate_names_path,
        label="alternate-names",
    )
    resolved_inputs = {cities_path, admin1_path, alternate_names_path}
    resolved_out = out_path.resolve(strict=False)
    if resolved_out in resolved_inputs:
        raise CatalogBuildError("output path must differ from every input path")

    tzdata_version, timezone_keys = _tzdata_context()
    statistics = BuildStatistics()
    admin1, admin1_checksum = _load_admin1(
        admin1_path,
        statistics=statistics,
    )
    places, cities_checksum = _load_places(
        cities_path,
        admin1=admin1,
        full_countries=normalized_countries,
        other_min_population=other_min_population,
        timezone_keys=timezone_keys,
        statistics=statistics,
    )
    relevant_ids = frozenset(places) | frozenset(
        place.admin1_geoname_id
        for place in places.values()
        if place.admin1_geoname_id is not None
    )
    alternate_names, alternate_names_checksum = _load_alternate_names(
        alternate_names_path,
        relevant_ids=relevant_ids,
        statistics=statistics,
    )

    source_checksums = {
        "admin1": admin1_checksum,
        "alternate_names": alternate_names_checksum,
        "cities": cities_checksum,
    }
    build_parameters: dict[str, object] = {
        "allowed_alternate_languages": sorted(ALLOWED_ALTERNATE_LANGUAGES),
        "excluded_feature_codes": sorted(EXCLUDED_FEATURE_CODES),
        "feature_class": POPULATED_PLACE_CLASS,
        "full_countries": sorted(normalized_countries),
        "other_min_population": other_min_population,
        "tzdata_version": tzdata_version,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{out_path.name}.",
        suffix=".tmp",
        dir=out_path.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(temporary_path)
        connection.execute("PRAGMA foreign_keys = ON")
        _write_catalog(
            connection,
            places=places,
            alternate_names=alternate_names,
            source_checksums=source_checksums,
            build_parameters=build_parameters,
            statistics=statistics,
        )
        connection.commit()
        _validate_catalog(
            connection,
            timezone_keys=timezone_keys,
            source_checksums=source_checksums,
            build_parameters=build_parameters,
            statistics=statistics,
        )
        connection.close()
        connection = None
        os.replace(temporary_path, out_path)
    except BaseException:
        if connection is not None:
            connection.close()
        temporary_path.unlink(missing_ok=True)
        raise

    return statistics


def _non_negative_cli_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def _parse_full_countries(value: str) -> frozenset[str]:
    countries = frozenset(
        code.strip().upper() for code in value.split(",") if code.strip()
    )
    if not countries:
        raise argparse.ArgumentTypeError("must contain at least one country code")
    if any(
        len(code) != 2 or not code.isascii() or not code.isalpha()
        for code in countries
    ):
        raise argparse.ArgumentTypeError("must contain ISO alpha-2 country codes")
    return countries


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cities", type=Path, required=True, help="cities1000.txt")
    parser.add_argument(
        "--admin1",
        type=Path,
        required=True,
        help="admin1CodesASCII.txt",
    )
    parser.add_argument(
        "--alternate-names",
        type=Path,
        required=True,
        help="alternateNamesV2.txt",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="output places.sqlite",
    )
    parser.add_argument(
        "--full-countries",
        type=_parse_full_countries,
        default=DEFAULT_FULL_COUNTRIES,
        help="comma-separated countries included without population threshold",
    )
    parser.add_argument(
        "--other-min-population",
        type=_non_negative_cli_int,
        default=DEFAULT_OTHER_MIN_POPULATION,
        help="minimum population for countries outside --full-countries",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        statistics = build(
            cities_path=args.cities,
            admin1_path=args.admin1,
            alternate_names_path=args.alternate_names,
            out_path=args.out,
            full_countries=args.full_countries,
            other_min_population=args.other_min_population,
        )
    except (CatalogBuildError, OSError, sqlite3.Error) as exc:
        print(f"place catalog build failed: {exc}", file=sys.stderr)
        return 1

    print(_statistics_json(statistics))
    print(f"catalog={args.out}")
    print("GeoNames attribution (CC BY) is required in the product UI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
