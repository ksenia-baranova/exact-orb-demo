"""Typed artifact payload models.

This module imports engine result models and therefore also imports the native
calculation stack transitively. Keep contract-only imports on
``exact_orb.calculation`` or its ``spec``, ``keys`` and ``cache`` modules.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from exact_orb.engine.charts.natal import NatalChart

from .chart_contract import calculation_input_from_chart, validate_chart_against_spec
from .keys import calculation_key
from .spec import ChartSpec


class ArtifactEphemerisStatus(BaseModel):
    """Artifact-safe ephemeris audit data without runtime provenance."""

    mode: Literal["files", "fallback"]
    required_files: tuple[str, ...]
    found_files: tuple[str, ...]
    missing_files: tuple[str, ...]

    @property
    def using_files(self) -> bool:
        return self.mode == "files"


class ArtifactNatalChart(NatalChart):
    """Natal chart payload with artifact-safe ephemeris status."""

    model_config = ConfigDict(frozen=True)

    ephemeris: ArtifactEphemerisStatus

    @field_validator("ephemeris", mode="before")
    @classmethod
    def _normalize_ephemeris(cls, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="python")
        return value


class ChartArtifact(BaseModel):
    """Serialized chart artifact identity plus deterministic chart payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    calculation_key: str
    spec: ChartSpec
    calculation_version: str = Field(..., min_length=1)
    chart: ArtifactNatalChart

    @model_validator(mode="before")
    @classmethod
    def _normalize_chart(cls, data: Any) -> Any:
        if not isinstance(data, Mapping):
            return data

        values = dict(data)
        chart = values.get("chart")
        if isinstance(chart, NatalChart) and not isinstance(chart, ArtifactNatalChart):
            values["chart"] = ArtifactNatalChart.model_validate(chart.model_dump(mode="python"))
        return values

    @model_validator(mode="after")
    def _validate_identity(self) -> "ChartArtifact":
        validate_chart_against_spec(self.chart, self.spec)
        expected_key = calculation_key(
            calculation_input_from_chart(self.chart),
            self.spec,
            self.calculation_version,
        )
        if self.calculation_key != expected_key:
            raise ValueError("calculation_key must match chart, spec, and calculation_version")
        return self


__all__ = [
    "ArtifactEphemerisStatus",
    "ArtifactNatalChart",
    "ChartArtifact",
]
