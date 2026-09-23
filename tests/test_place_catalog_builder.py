from __future__ import annotations

import ast
from contextlib import closing
from dataclasses import asdict
import hashlib
from importlib import metadata
import json
from pathlib import Path
import runpy
import sqlite3
from typing import Any

import pytest

from exact_orb.birth import places as place_contracts


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_place_catalog.py"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "place_catalog"
CITIES_PATH = FIXTURE_ROOT / "cities1000.txt"
ADMIN1_PATH = FIXTURE_ROOT / "admin1CodesASCII.txt"
ALTERNATE_NAMES_PATH = FIXTURE_ROOT / "alternateNamesV2.txt"

EXPECTED_STATISTICS = {
    "admin1_rows_read": 4,
    "cities_rows_read": 10,
    "alternate_names_rows_read": 15,
    "places_written": 5,
    "place_names_written": 13,
    "filtered_feature_class": 1,
    "filtered_feature_code": 1,
    "filtered_country_population": 1,
    "filtered_timezone": 2,
    "filtered_alternate_language": 2,
    "rejected_names": 1,
}
EXPECTED_PLACE_IDS = {"498817", "524901", "900001", "900003", "900005"}
EXPECTED_FULL_COUNTRIES = [
    "AM",
    "AZ",
    "BY",
    "EE",
    "GE",
    "KG",
    "KZ",
    "LT",
    "LV",
    "MD",
    "RU",
    "TJ",
    "TM",
    "UA",
    "UZ",
]
STATISTICS_FIELD_ORDER = list(EXPECTED_STATISTICS)


@pytest.fixture(scope="module")
def builder() -> dict[str, Any]:
    return runpy.run_path(str(BUILDER_PATH))


def _build(builder: dict[str, Any], output: Path) -> Any:
    return builder["build"](
        cities_path=CITIES_PATH,
        admin1_path=ADMIN1_PATH,
        alternate_names_path=ALTERNATE_NAMES_PATH,
        out_path=output,
    )


def _tsv_rows(path: Path, *, logical_columns: int | None = None) -> list[list[str]]:
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines()]
    if logical_columns is not None:
        for row in rows:
            row.extend([""] * (logical_columns - len(row)))
    return rows


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _logical_snapshot(path: Path) -> tuple[list[tuple[Any, ...]], ...]:
    queries = (
        """
        SELECT place_id, display_name, name_ascii, country_code, admin1_code,
               admin1_name, latitude_e2, longitude_e2, tz_id, population
        FROM places
        ORDER BY CAST(place_id AS INTEGER), place_id
        """,
        """
        SELECT place_name_id, place_id, name, search_key, language, preferred,
               historic
        FROM place_names
        ORDER BY place_name_id
        """,
        """
        SELECT singleton, schema_version, source_checksums, build_parameters
        FROM catalog_metadata
        ORDER BY singleton
        """,
    )
    with closing(sqlite3.connect(path)) as connection:
        return tuple(connection.execute(query).fetchall() for query in queries)


def test_synthetic_fixtures_contain_every_required_positive_control() -> None:
    admin1 = {row[0]: row for row in _tsv_rows(ADMIN1_PATH)}
    cities = {row[0]: row for row in _tsv_rows(CITIES_PATH)}
    alternate_names = _tsv_rows(ALTERNATE_NAMES_PATH, logical_columns=10)

    assert admin1["RU.48"][3] == "524894"
    assert admin1["KZ.75"][2:] == ["Almaty Oblysy", "1526396"]

    assert cities["524901"][1:4] == ["Moscow", "Moscow", "Məskeү,Москва"]
    assert cities["900001"][4:6] == ["12.345", "-45.675"]
    assert cities["900002"][17] == "Nowhere/Fake"
    assert cities["900008"][17] == ""
    assert cities["900003"][8:15:6] == ["US", "100000"]
    assert cities["900004"][8:15:6] == ["US", "99999"]
    assert cities["900005"][8:15:6] == ["KZ", "1"]
    assert cities["900006"][7] == "PPLX"
    assert cities["900007"][6] == "A"

    moscow_names = [row for row in alternate_names if row[1] == "524901"]
    assert ("ky", "Məskeү") in {(row[2], row[3]) for row in moscow_names}
    assert ("link", "https://example.invalid/moscow") in {
        (row[2], row[3]) for row in moscow_names
    }
    assert ("1001", "Москва-Сити", "0") in {
        (row[0], row[3], row[4]) for row in moscow_names
    }
    assert {row[0] for row in moscow_names if row[2] == "ru" and row[4] == "1"} == {
        "1000",
        "1002",
    }
    assert any(row[3] == "Московия" and row[7] == "1" for row in moscow_names)
    assert any(row[3] == "Старая Москва" and row[9] for row in moscow_names)
    assert any(row[1:4] == ["524894", "ru", "Москва"] for row in alternate_names)
    assert not any(row[1] == "1526396" for row in alternate_names)


def test_builder_uses_the_canonical_normalizer_and_language_allow_list(
    builder: dict[str, Any],
) -> None:
    tree = ast.parse(BUILDER_PATH.read_text(encoding="utf-8"), filename=str(BUILDER_PATH))
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

    assert {
        "normalize_place_query",
        "ALLOWED_ALTERNATE_LANGUAGES",
    } <= imported_names
    assert local_normalizers == []
    assert builder["normalize_place_query"] is place_contracts.normalize_place_query
    assert (
        builder["ALLOWED_ALTERNATE_LANGUAGES"]
        is place_contracts.ALLOWED_ALTERNATE_LANGUAGES
    )
    assert builder["ALLOWED_ALTERNATE_LANGUAGES"] == frozenset({"ru"})


def test_builder_applies_filters_rounding_and_name_rules(
    builder: dict[str, Any],
    tmp_path: Path,
) -> None:
    path = tmp_path / "places.sqlite"
    statistics = asdict(_build(builder, path))
    assert statistics == EXPECTED_STATISTICS

    with closing(sqlite3.connect(path)) as connection:
        places = {
            row[0]: row[1:]
            for row in connection.execute(
                """
                SELECT place_id, display_name, admin1_name, latitude_e2,
                       longitude_e2, tz_id, population
                FROM places
                """
            )
        }
        moscow_names = connection.execute(
            """
            SELECT name, search_key, language, preferred, historic
            FROM place_names
            WHERE place_id = '524901'
            ORDER BY place_name_id
            """
        ).fetchall()

    assert set(places) == EXPECTED_PLACE_IDS
    assert places["524901"] == (
        "Москва",
        "Москва",
        5575,
        3762,
        "Europe/Moscow",
        10_381_222,
    )
    assert places["900001"][2:4] == (1235, -4568)
    assert places["900003"][-1] == 100_000
    assert places["900005"][1] == "Almaty Oblysy"

    assert "900002" not in places
    assert "900004" not in places
    assert "900006" not in places
    assert "900007" not in places
    assert "900008" not in places

    names = {row[0]: row[1:] for row in moscow_names}
    assert [row[0] for row in moscow_names].count("Moscow") == 1
    assert names["Москва"] == ("москва", "ru", 1, 0)
    assert names["Москва-Сити"] == ("москва-сити", "ru", 0, 0)
    assert names["Москва-город"] == ("москва-город", "ru", 1, 0)
    assert names["Московия"][-1] == 1
    assert names["Старая Москва"][-1] == 1
    assert "Məskeү" not in names
    assert "https://example.invalid/moscow" not in names
    assert "###@@@" not in names


def test_catalog_schema_and_metadata_are_complete_and_canonical(
    builder: dict[str, Any],
    tmp_path: Path,
) -> None:
    path = tmp_path / "places.sqlite"
    _build(builder, path)
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        indexes = {
            row[1] for row in connection.execute("PRAGMA index_list(place_names)")
        }
        search_index = connection.execute(
            "PRAGMA index_xinfo(idx_place_names_search_key)"
        ).fetchall()
        metadata_rows = connection.execute(
            """
            SELECT schema_version, source_checksums, build_parameters
            FROM catalog_metadata
            ORDER BY singleton
            """
        ).fetchall()

    assert tables == {"places", "place_names", "catalog_metadata"}
    assert {
        "idx_place_names_search_key",
        "idx_place_names_place_id",
    } <= indexes
    assert search_index[0][2] == "search_key"
    assert search_index[0][4] == "BINARY"
    assert search_index[0][5] == 1
    assert len(metadata_rows) == 1

    schema_version, source_checksums_json, build_parameters_json = metadata_rows[0]
    source_checksums = json.loads(source_checksums_json)
    build_parameters = json.loads(build_parameters_json)

    assert schema_version == 1
    assert source_checksums_json == _canonical_json(source_checksums)
    assert build_parameters_json == _canonical_json(build_parameters)
    assert source_checksums == {
        "admin1": _sha256(ADMIN1_PATH),
        "alternate_names": _sha256(ALTERNATE_NAMES_PATH),
        "cities": _sha256(CITIES_PATH),
    }
    assert build_parameters == {
        "allowed_alternate_languages": ["ru"],
        "excluded_feature_codes": ["PPLH", "PPLW", "PPLX"],
        "feature_class": "P",
        "full_countries": EXPECTED_FULL_COUNTRIES,
        "other_min_population": 100_000,
        "tzdata_version": metadata.version("tzdata"),
    }


def test_two_builds_have_identical_logical_rows_and_metadata(
    builder: dict[str, Any],
    tmp_path: Path,
) -> None:
    first = tmp_path / "first" / "places.sqlite"
    second = tmp_path / "second" / "places.sqlite"

    first_statistics = asdict(_build(builder, first))
    second_statistics = asdict(_build(builder, second))

    assert first_statistics == EXPECTED_STATISTICS
    assert second_statistics == EXPECTED_STATISTICS
    assert _logical_snapshot(first) == _logical_snapshot(second)


@pytest.mark.parametrize("missing_input", ["cities", "admin1", "alternate_names"])
def test_every_required_input_is_checked_before_output_creation(
    builder: dict[str, Any],
    tmp_path: Path,
    missing_input: str,
) -> None:
    output = tmp_path / "places.sqlite"
    paths = {
        "cities_path": CITIES_PATH,
        "admin1_path": ADMIN1_PATH,
        "alternate_names_path": ALTERNATE_NAMES_PATH,
    }
    paths[f"{missing_input}_path"] = tmp_path / f"missing-{missing_input}.txt"

    with pytest.raises(builder["CatalogBuildError"], match="missing required"):
        builder["build"](**paths, out_path=output)

    assert not output.exists()
    assert list(tmp_path.glob(".*.tmp")) == []


def test_publish_failure_preserves_target_and_removes_adjacent_temp(
    builder: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "places.sqlite"
    original = b"previous catalog release"
    output.write_bytes(original)
    observed: dict[str, Path] = {}

    def fail_replace(source: Path, destination: Path) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        observed["source"] = source_path
        observed["destination"] = destination_path
        assert source_path.parent == output.parent
        assert destination_path == output
        connection = sqlite3.connect(source_path)
        try:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        finally:
            connection.close()
        raise OSError("injected publish failure")

    monkeypatch.setattr(builder["os"], "replace", fail_replace)

    with pytest.raises(OSError, match="injected publish failure"):
        _build(builder, output)

    assert observed["destination"] == output
    assert output.read_bytes() == original
    assert not observed["source"].exists()
    assert list(tmp_path.glob(f".{output.name}.*.tmp")) == []


def test_cli_reports_statistics_in_contract_order(
    builder: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    output = tmp_path / "places.sqlite"
    exit_code = builder["main"](
        [
            "--cities",
            str(CITIES_PATH),
            "--admin1",
            str(ADMIN1_PATH),
            "--alternate-names",
            str(ALTERNATE_NAMES_PATH),
            "--out",
            str(output),
        ]
    )
    captured = capsys.readouterr()
    output_lines = captured.out.splitlines()
    statistics_pairs = json.loads(output_lines[0], object_pairs_hook=list)

    assert exit_code == 0
    assert [key for key, _ in statistics_pairs] == STATISTICS_FIELD_ORDER
    assert dict(statistics_pairs) == EXPECTED_STATISTICS
    assert output_lines[1] == f"catalog={output}"
    assert output_lines[2] == "GeoNames attribution (CC BY) is required in the product UI."
    assert captured.err == ""
