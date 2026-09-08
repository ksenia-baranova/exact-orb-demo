"""Application handler for building a base natal chart or cosmogram."""

from __future__ import annotations

from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.ports import BirthDataResolverPort, ChartArtifactPort
from exact_orb.application.results import BuildNatalOutcome, BuildNatalSuccess
from exact_orb.calculation.errors import (
    CalculationUnavailableError,
    ChartCalculationError,
)
from exact_orb.calculation.spec import NatalChartSpec
from exact_orb.outcomes import CalculationFailed, InputRequired, ResolutionUnavailable
from exact_orb.run_context import RunContext
from exact_orb.session.state import SessionState, StateDelta


class BuildNatalHandler:
    """Coordinate resolution, chart retrieval, and state-delta construction."""

    def __init__(
        self,
        *,
        resolver: BirthDataResolverPort,
        artifacts: ChartArtifactPort,
    ) -> None:
        self._resolver = resolver
        self._artifacts = artifacts

    async def handle(
        self,
        command: BuildNatalCommand,
        state: SessionState,
        run: RunContext,
    ) -> BuildNatalOutcome:
        resolution = await self._resolver.resolve(command.birth_input, run=run)
        if isinstance(resolution, (InputRequired, ResolutionUnavailable)):
            return resolution

        chart_kind = "cosmogram" if resolution.time_unknown else "natal"
        spec = NatalChartSpec(chart_kind=chart_kind)

        try:
            artifact = await self._artifacts.ensure_chart(spec, resolution, run=run)
        except (ChartCalculationError, CalculationUnavailableError) as error:
            return CalculationFailed(error_code=error.code)

        delta = StateDelta(
            birth_input=command.birth_input,
            birth_resolved=resolution,
            base_chart_spec=spec,
        )
        return BuildNatalSuccess(artifact=artifact, delta=delta)


__all__ = ["BuildNatalHandler"]
