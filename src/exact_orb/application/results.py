"""Typed outcomes produced by application handlers."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from exact_orb.calculation.chart_contract import calculation_input_from_chart
from exact_orb.calculation.keys import calculation_input_from, calculation_key
from exact_orb.calculation.types import ChartArtifact
from exact_orb.outcomes import CalculationFailed, InputRequired, ResolutionUnavailable
from exact_orb.session.state import StateDelta


class BuildNatalSuccess(BaseModel):
    """A chart artifact paired with the state delta prepared for commit."""

    model_config = ConfigDict(frozen=True)

    artifact: ChartArtifact
    delta: StateDelta

    @model_validator(mode="after")
    def _result_must_be_consistent(self) -> Self:
        delta = self.delta

        # This check must precede access to base_chart_spec.chart_kind:
        # a successful build cannot carry RESET_DELTA.
        if (
            delta.birth_input is None
            or delta.birth_resolved is None
            or delta.base_chart_spec is None
        ):
            raise ValueError("successful build requires a fully populated StateDelta")

        birth_input = delta.birth_input
        birth_resolved = delta.birth_resolved
        base_chart_spec = delta.base_chart_spec

        if self.artifact.spec != base_chart_spec:
            raise ValueError("artifact.spec must equal delta.base_chart_spec")

        expected_chart_kind = (
            "cosmogram" if birth_resolved.time_unknown else "natal"
        )
        if base_chart_spec.chart_kind != expected_chart_kind:
            raise ValueError(
                "delta.base_chart_spec.chart_kind must match "
                "delta.birth_resolved.time_unknown"
            )

        if (birth_input.birth_time is None) != birth_resolved.time_unknown:
            raise ValueError(
                "delta.birth_input.birth_time must match "
                "delta.birth_resolved.time_unknown"
            )

        resolved_input = calculation_input_from(birth_resolved)
        chart_input = calculation_input_from_chart(self.artifact.chart)
        if chart_input != resolved_input:
            raise ValueError(
                "artifact.chart calculation input must equal "
                "delta.birth_resolved calculation input"
            )

        expected_key = calculation_key(
            resolved_input,
            base_chart_spec,
            self.artifact.calculation_version,
        )
        if self.artifact.calculation_key != expected_key:
            raise ValueError(
                "artifact.calculation_key must match delta birth data, spec, "
                "and calculation version"
            )

        return self


BuildNatalOutcome = (
    BuildNatalSuccess | InputRequired | ResolutionUnavailable | CalculationFailed
)


__all__ = ["BuildNatalOutcome", "BuildNatalSuccess"]
