r"""Explicit one-time generator for full payload-format-1 golden fixtures.

Run from the repository root only for an intentional format fixture update:
    .\.venv\Scripts\python.exe -B -m scripts.generate_stored_chart_fixtures

pytest reads the committed bytes; it never calls this script.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from exact_orb.birth.tz import resolve_unknown_birth_time_for_migration
from exact_orb.calculation.chart_contract import calculation_input_from_chart
from exact_orb.calculation.codec import CHART_ARTIFACT_PAYLOAD_FORMAT, encode_chart_artifact
from exact_orb.calculation.keys import calculation_key
from exact_orb.calculation.spec import NatalChartSpec
from exact_orb.calculation.types import ChartArtifact
from exact_orb.config import configure_ephemeris
from exact_orb.engine.charts.natal import calculate_natal


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "golden"
LOCAL_DATE = date(1985, 9, 2)
LATITUDE = 55.7522
LONGITUDE = 37.6155
VERSION = "baseline-version"


def _write(name: str, spec: NatalChartSpec, chart, *, birth_time_local: str | None) -> None:
    artifact = ChartArtifact(
        calculation_key=calculation_key(
            calculation_input_from_chart(chart), spec, VERSION,
        ),
        spec=spec,
        calculation_version=VERSION,
        chart=chart,
    )
    payload = encode_chart_artifact(artifact)
    (GOLDEN / f"{name}.bin").write_bytes(payload)
    manifest = {
        "payload_format": CHART_ARTIFACT_PAYLOAD_FORMAT,
        "calculation_key": artifact.calculation_key,
        "calculation_version": artifact.calculation_version,
        "spec": spec.model_dump(mode="json"),
        "calculation_input": calculation_input_from_chart(chart).model_dump(mode="json"),
        "source": {
            "birth_date_local": LOCAL_DATE.isoformat(),
            "birth_time_local": birth_time_local,
            "place": "Москва",
            "tz_id": "Europe/Moscow",
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "reference": "natal_1985_human.txt",
        },
        "payload_sha256": sha256(payload).hexdigest(),
    }
    (GOLDEN / f"{name}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    configure_ephemeris(ROOT / "ephe", selena_method="true_perigee")

    natal_spec = NatalChartSpec(chart_kind="natal")
    natal = calculate_natal(
        datetime(1985, 9, 1, 20, 45, tzinfo=timezone.utc),
        LATITUDE,
        LONGITUDE,
        chart_kind="natal",
        house_system="P",
    )
    _write(
        "chart_artifact_format_1_natal_1985", natal_spec, natal,
        birth_time_local="00:45+04:00",
    )

    anchor, _offset, domain = resolve_unknown_birth_time_for_migration(
        LOCAL_DATE, "Europe/Moscow",
    )
    cosmogram_spec = NatalChartSpec(chart_kind="cosmogram")
    cosmogram = calculate_natal(
        anchor,
        LATITUDE,
        LONGITUDE,
        chart_kind="cosmogram",
        house_system="P",
        birth_time_domain=domain,
    )
    _write(
        "chart_artifact_format_1_cosmogram_1985", cosmogram_spec, cosmogram,
        birth_time_local=None,
    )


if __name__ == "__main__":
    main()
