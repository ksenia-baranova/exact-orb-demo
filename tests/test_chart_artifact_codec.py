"""Chart artifact model and codec tests."""

from __future__ import annotations

from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from typing import Any

import pytest
from pydantic import ValidationError

from exact_orb.calculation.codec import (
    ChartArtifactDecodeError,
    decode_chart_artifact,
    encode_chart_artifact,
)
from exact_orb.calculation.keys import KEY_PREFIX, CalculationInput, calculation_key
from exact_orb.calculation.spec import NatalChartSpec
from exact_orb.calculation.types import (
    ArtifactEphemerisStatus,
    ArtifactNatalChart,
    ChartArtifact,
)
from exact_orb.config import EphemerisStatus, configure_ephemeris
from exact_orb.engine.charts.natal import NatalChart, calculate_natal
from exact_orb.engine.ephemeris.types import CalculationWarning
from tests.conftest import REPO_ROOT
from tests.fixtures.natal_1985 import REFERENCE


pytestmark = pytest.mark.no_ephemeris_autoinit


BASE_UTC = datetime(1990, 9, 2, 10, 30, 45, tzinfo=timezone.utc)
EPHE_FILES = ("sepl_18.se1", "semo_18.se1", "seas_18.se1")
SENSITIVE_WARNING = "sensitive warning for 55.7558 37.6173 at 1990-09-02"

# baseline: normalized ChartArtifact schema + vendored ephe/*.se1; recalculate
# only for an intentional ephemeris or serialized-schema update.
NATAL_ARTIFACT_JSON_BASELINE_SHA256 = "06eb12e35a3863f8b0cbeb733f5ca601ff526b5caf0b92cf40152b166a91bb49"


def test_chart_artifact_normalizes_raw_chart_to_artifact_safe_chart() -> None:
    artifact = _artifact()

    assert isinstance(artifact.chart, ArtifactNatalChart)
    assert isinstance(artifact.chart, NatalChart)
    assert isinstance(artifact.chart.ephemeris, ArtifactEphemerisStatus)
    assert artifact.chart.ephemeris.mode == "files"
    assert artifact.chart.ephemeris.required_files == EPHE_FILES
    assert artifact.chart.ephemeris.found_files == EPHE_FILES
    assert artifact.chart.ephemeris.missing_files == ()
    assert artifact.chart.ephemeris.using_files is True
    assert not hasattr(artifact.chart.ephemeris, "path")
    assert not hasattr(artifact.chart.ephemeris, "source")


def test_chart_artifact_accepts_already_normalized_chart() -> None:
    first = _artifact()
    second = _artifact(chart=first.chart)

    assert isinstance(second.chart, ArtifactNatalChart)
    assert second == first


def test_artifact_ephemeris_fields_track_runtime_status_minus_runtime_provenance() -> None:
    assert set(ArtifactEphemerisStatus.model_fields) == set(EphemerisStatus.model_fields) - {
        "path",
        "source",
    }


def test_chart_artifact_top_level_model_is_frozen() -> None:
    artifact = _artifact()

    with pytest.raises(ValidationError):
        artifact.calculation_version = "other-version"  # type: ignore[misc]


def test_chart_artifact_has_only_canonical_top_level_fields() -> None:
    artifact = _artifact()

    assert set(ChartArtifact.model_fields) == {
        "calculation_key",
        "spec",
        "calculation_version",
        "chart",
    }
    assert not hasattr(artifact, "chart_kind")
    assert not hasattr(artifact, "warnings")
    assert artifact.chart.chart_kind == "natal"
    assert artifact.chart.warnings == (_warning(SENSITIVE_WARNING),)


def test_chart_artifact_rejects_unknown_top_level_fields() -> None:
    payload = _artifact().model_dump(mode="python")
    payload["unexpected"] = "value"

    with pytest.raises(ValidationError, match="unexpected"):
        ChartArtifact.model_validate(payload)


def test_artifact_chart_identity_is_frozen() -> None:
    artifact = _artifact()

    with pytest.raises(ValidationError):
        artifact.chart.longitude = 0.0  # type: ignore[misc]


def test_chart_artifact_validates_identity_fields() -> None:
    chart = _raw_chart()

    with pytest.raises(ValidationError, match="calculation_key"):
        _artifact(chart=chart, key="bad-prefix")

    with pytest.raises(ValidationError, match="calculation_key"):
        _artifact(chart=chart, key=KEY_PREFIX + "f" * 64)

    with pytest.raises(ValidationError, match="calculation_version"):
        _artifact(chart=chart, version="")

    with pytest.raises(ValidationError, match="chart.chart_kind"):
        _artifact(
            chart=chart,
            spec=NatalChartSpec(chart_kind="cosmogram", include=("positions",)),
        )

    with pytest.raises(ValidationError, match="chart block 'positions'"):
        _artifact(chart=chart.model_copy(update={"bodies": None}))

    with pytest.raises(ValidationError, match="house_system"):
        _artifact(chart=chart.model_copy(update={"house_system": "K"}))


def test_chart_artifact_accepts_key_derived_from_chart_spec_and_version() -> None:
    artifact = _artifact()

    expected = calculation_key(
        CalculationInput(
            utc_datetime=artifact.chart.datetime_utc,
            latitude=artifact.chart.latitude,
            longitude=artifact.chart.longitude,
        ),
        artifact.spec,
        artifact.calculation_version,
    )

    assert artifact.calculation_key == expected


def test_encode_returns_deterministic_gzip_bytes_with_utf8_json_payload() -> None:
    artifact = _artifact()

    first = encode_chart_artifact(artifact)
    second = encode_chart_artifact(artifact)
    raw = gzip.decompress(first)
    payload = json.loads(raw.decode("utf-8"))

    assert isinstance(first, bytes)
    assert first == second
    assert payload["calculation_key"] == artifact.calculation_key
    assert "chart_kind" not in payload
    assert "warnings" not in payload
    assert payload["chart"]["ephemeris"]["mode"] == "files"
    assert "path" not in payload["chart"]["ephemeris"]
    assert "source" not in payload["chart"]["ephemeris"]


def test_reference_natal_artifact_json_matches_normalized_schema_baseline() -> None:
    configure_ephemeris(REPO_ROOT / "ephe", selena_method="true_perigee")
    chart = calculate_natal(
        REFERENCE["datetime_utc"],
        REFERENCE["latitude"],
        REFERENCE["longitude"],
        chart_kind="natal",
        house_system=REFERENCE["house_system"],
    )
    spec = NatalChartSpec(chart_kind="natal")
    version = "baseline-version"
    artifact = ChartArtifact(
        calculation_key=calculation_key(
            CalculationInput(
                utc_datetime=chart.datetime_utc,
                latitude=chart.latitude,
                longitude=chart.longitude,
            ),
            spec,
            version,
        ),
        spec=spec,
        calculation_version=version,
        chart=chart,
    )

    digest = sha256(artifact.model_dump_json().encode("utf-8")).hexdigest()

    assert digest == NATAL_ARTIFACT_JSON_BASELINE_SHA256


def test_codec_round_trip_returns_equal_new_instance() -> None:
    artifact = _artifact()
    encoded = encode_chart_artifact(artifact)

    decoded = decode_chart_artifact(encoded)

    assert decoded == artifact
    assert decoded is not artifact
    assert encode_chart_artifact(decode_chart_artifact(encoded)) == encoded


def test_mutating_decoded_nested_chart_does_not_affect_next_decode() -> None:
    artifact = _artifact()
    encoded = encode_chart_artifact(artifact)
    first = decode_chart_artifact(encoded)

    first.chart.warnings[0].message = "changed"
    second = decode_chart_artifact(encoded)

    assert second.chart.warnings[0].message == SENSITIVE_WARNING


@pytest.mark.parametrize(
    ("payload", "reason"),
    (
        (b"", "gzip"),
        (b"not gzip", "gzip"),
    ),
)
def test_decode_reports_gzip_reason_for_empty_or_non_gzip_payloads(
    payload: bytes,
    reason: str,
) -> None:
    with pytest.raises(ChartArtifactDecodeError) as exc_info:
        decode_chart_artifact(payload)

    assert exc_info.value.reason == reason


def test_decode_reports_gzip_reason_for_truncated_gzip() -> None:
    payload = encode_chart_artifact(_artifact())[:8]

    with pytest.raises(ChartArtifactDecodeError) as exc_info:
        decode_chart_artifact(payload)

    assert exc_info.value.reason == "gzip"


def test_decode_reports_gzip_reason_for_corrupt_deflate_body() -> None:
    payload = bytes.fromhex("1f8b0800000000000003") + b"bad-deflate" + (b"\x00" * 8)

    with pytest.raises(ChartArtifactDecodeError) as exc_info:
        decode_chart_artifact(payload)

    assert exc_info.value.reason == "gzip"


def test_decode_reports_utf8_reason_for_non_utf8_uncompressed_payload() -> None:
    payload = gzip.compress(b"\xff", compresslevel=6, mtime=0)

    with pytest.raises(ChartArtifactDecodeError) as exc_info:
        decode_chart_artifact(payload)

    assert exc_info.value.reason == "utf8"


@pytest.mark.parametrize(
    "raw",
    (
        b"not json",
        b"{}",
    ),
)
def test_decode_reports_validation_reason_for_utf8_payloads_that_are_not_artifacts(
    raw: bytes,
) -> None:
    payload = gzip.compress(raw, compresslevel=6, mtime=0)

    with pytest.raises(ChartArtifactDecodeError) as exc_info:
        decode_chart_artifact(payload)

    assert exc_info.value.reason == "validation"


def test_decode_validation_error_text_does_not_expose_payload_or_pydantic_details() -> None:
    artifact = _artifact()
    payload = _decoded_json_payload(artifact)
    del payload["calculation_version"]
    corrupt = gzip.compress(
        json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        compresslevel=6,
        mtime=0,
    )

    with pytest.raises(ChartArtifactDecodeError) as exc_info:
        decode_chart_artifact(corrupt)

    error = exc_info.value
    text = str(error)
    assert error.reason == "validation"
    assert error.__cause__ is None
    assert "1990-09-02" not in text
    assert "55.7558" not in text
    assert "37.6173" not in text
    assert SENSITIVE_WARNING not in text
    assert "calculation_version" not in text
    assert "ValidationError" not in text


def test_decode_rejects_legacy_duplicate_top_level_fields() -> None:
    artifact = _artifact()
    payload = _decoded_json_payload(artifact)
    payload["chart_kind"] = artifact.chart.chart_kind
    payload["warnings"] = [warning.model_dump(mode="json") for warning in artifact.chart.warnings]
    legacy = gzip.compress(
        json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        compresslevel=6,
        mtime=0,
    )

    with pytest.raises(ChartArtifactDecodeError) as exc_info:
        decode_chart_artifact(legacy)

    assert exc_info.value.reason == "validation"


def _raw_chart(
    *,
    chart_kind: str = "natal",
    warnings: tuple[CalculationWarning, ...] | None = None,
    path: str = r"C:\Users\KateUser\secret\ephe",
    source: str = "argument",
) -> NatalChart:
    return NatalChart(
        chart_kind=chart_kind,
        datetime_utc=BASE_UTC,
        julian_day_ut=2448136.0,
        latitude=55.7558,
        longitude=37.6173,
        house_system="P",
        ephemeris_flags=0,
        ephemeris=EphemerisStatus(
            path=path,
            source=source,
            mode="files",
            required_files=EPHE_FILES,
            found_files=EPHE_FILES,
            missing_files=(),
        ),
        selena_method="true_perigee",
        bodies={},
        cusps=(),
        angles={},
        house_rulers=None,
        interceptions=None,
        aspects=None,
        configurations=None,
        strength=None,
        warnings=warnings if warnings is not None else (_warning(SENSITIVE_WARNING),),
    )


def _artifact(
    *,
    chart: NatalChart | ArtifactNatalChart | None = None,
    spec: NatalChartSpec | None = None,
    key: str | None = None,
    version: str = "test-version-1",
) -> ChartArtifact:
    chart = chart or _raw_chart()
    spec = spec or NatalChartSpec(
        chart_kind=chart.chart_kind,
        include=("houses", "positions") if chart.chart_kind == "natal" else ("positions",),
    )
    key = key or calculation_key(
        CalculationInput(
            utc_datetime=chart.datetime_utc,
            latitude=chart.latitude,
            longitude=chart.longitude,
        ),
        spec,
        version,
    )
    return ChartArtifact(
        calculation_key=key,
        spec=spec,
        calculation_version=version,
        chart=chart,
    )


def _warning(message: str) -> CalculationWarning:
    return CalculationWarning(source="fixture", message=message, retflags=None)


def _decoded_json_payload(artifact: ChartArtifact) -> dict[str, Any]:
    return json.loads(gzip.decompress(encode_chart_artifact(artifact)).decode("utf-8"))
