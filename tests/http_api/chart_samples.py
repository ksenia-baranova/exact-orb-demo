"""Small, model-validated samples cut from the existing artifact goldens."""

from __future__ import annotations

from pathlib import Path

from exact_orb.calculation.codec import decode_chart_artifact
from exact_orb.calculation.types import ChartArtifact


_GOLDEN = Path(__file__).resolve().parents[1] / "golden"


def _base(kind: str) -> ChartArtifact:
    return decode_chart_artifact(
        (_GOLDEN / f"chart_artifact_format_1_{kind}_1985.bin").read_bytes()
    )


def natal_sample() -> ChartArtifact:
    base = _base("natal")
    chart = base.chart.model_dump(mode="python")
    # Deliberately scramble input maps/house order. Public order is fixed by §7.2.
    chart["bodies"] = {name: chart["bodies"][name]
                       for name in ("mercury", "moon", "sun")}
    chart["cusps"] = (chart["cusps"][2], chart["cusps"][0], chart["cusps"][1])
    chart["aspects"] = tuple(chart["aspects"][index] for index in (1, 13, 23))
    chart["configurations"] = ()
    chart["house_rulers"] = ()
    chart["interceptions"] = ()
    return ChartArtifact.model_validate({
        "calculation_key": base.calculation_key,
        "calculation_version": base.calculation_version,
        "spec": base.spec,
        "chart": chart,
    })


def cosmogram_sample() -> ChartArtifact:
    base = _base("cosmogram")
    chart = base.chart.model_dump(mode="python")
    chart["bodies"] = {name: chart["bodies"][name] for name in ("chiron", "uranus")}
    chart["aspects"] = (chart["aspects"][0],)
    chart["configurations"] = ()
    chart["time_uncertainty"]["excluded_aspects"] = ()
    return ChartArtifact.model_validate({
        "calculation_key": base.calculation_key,
        "calculation_version": base.calculation_version,
        "spec": base.spec,
        "chart": chart,
    })
