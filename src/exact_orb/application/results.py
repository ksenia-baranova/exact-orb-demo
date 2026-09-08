"""Typed outcomes produced by application handlers."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

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

        if self.artifact.spec != delta.base_chart_spec:
            raise ValueError("artifact.spec must equal delta.base_chart_spec")

        # Unreachable through validated ChartArtifact construction: its identity
        # validator equates chart_kind with spec.chart_kind, and specs match above.
        # Keep this as defense-in-depth if the artifact invariant changes later.
        if self.artifact.chart_kind != delta.base_chart_spec.chart_kind:
            raise ValueError(
                "artifact.chart_kind must equal delta.base_chart_spec.chart_kind"
            )

        return self


BuildNatalOutcome = (
    BuildNatalSuccess | InputRequired | ResolutionUnavailable | CalculationFailed
)


__all__ = ["BuildNatalOutcome", "BuildNatalSuccess"]
