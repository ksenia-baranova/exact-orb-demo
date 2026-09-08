"""Application handler for building a base natal chart or cosmogram."""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter

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


LOGGER = logging.getLogger(__name__)


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
        started_at = perf_counter()
        stage = "resolve"
        _log_started(run)
        try:
            resolution = await self._resolver.resolve(command.birth_input, run=run)
            if isinstance(resolution, (InputRequired, ResolutionUnavailable)):
                _log_completed(run, resolution, None, started_at)
                return resolution

            stage = "build_spec"
            chart_kind = "cosmogram" if resolution.time_unknown else "natal"
            spec = NatalChartSpec(chart_kind=chart_kind)

            stage = "ensure_chart"
            try:
                artifact = await self._artifacts.ensure_chart(
                    spec,
                    resolution,
                    run=run,
                )
            except (ChartCalculationError, CalculationUnavailableError) as error:
                outcome = CalculationFailed(error_code=error.code)
                _log_completed(run, outcome, chart_kind, started_at)
                return outcome

            stage = "build_delta"
            delta = StateDelta(
                birth_input=command.birth_input,
                birth_resolved=resolution,
                base_chart_spec=spec,
            )

            stage = "build_result"
            outcome = BuildNatalSuccess(artifact=artifact, delta=delta)
            _log_completed(run, outcome, chart_kind, started_at)
            return outcome
        except BaseException as exc:
            _log_failed(run, stage, exc, started_at)
            raise


def _log_started(run: RunContext) -> None:
    LOGGER.debug("build_natal_started run_id=%s", str(run.run_id))


def _log_completed(
    run: RunContext,
    outcome: BuildNatalOutcome,
    chart_kind: str | None,
    started_at: float,
) -> None:
    run_id = str(run.run_id)
    duration_ms = _elapsed_ms(started_at)

    if isinstance(outcome, BuildNatalSuccess):
        LOGGER.info(
            "build_natal_completed run_id=%s outcome=success chart_kind=%s "
            "duration_ms=%.3f",
            run_id,
            chart_kind,
            duration_ms,
        )
        return

    if isinstance(outcome, InputRequired):
        LOGGER.info(
            "build_natal_completed run_id=%s outcome=input_required duration_ms=%.3f",
            run_id,
            duration_ms,
        )
        return

    if isinstance(outcome, ResolutionUnavailable):
        LOGGER.warning(
            "build_natal_completed run_id=%s outcome=resolution_unavailable "
            "error_code=%s duration_ms=%.3f",
            run_id,
            outcome.error_code,
            duration_ms,
        )
        return

    if outcome.error_code == "ENGINE_UNEXPECTED":
        LOGGER.error(
            "build_natal_completed run_id=%s outcome=calculation_failed "
            "chart_kind=%s error_code=%s duration_ms=%.3f",
            run_id,
            chart_kind,
            outcome.error_code,
            duration_ms,
        )
        return

    LOGGER.warning(
        "build_natal_completed run_id=%s outcome=calculation_failed "
        "chart_kind=%s error_code=%s duration_ms=%.3f",
        run_id,
        chart_kind,
        outcome.error_code,
        duration_ms,
    )


def _log_failed(
    run: RunContext,
    stage: str,
    exc: BaseException,
    started_at: float,
) -> None:
    cancelled = isinstance(exc, asyncio.CancelledError)
    log = LOGGER.warning if cancelled else LOGGER.error
    log(
        "build_natal_failed run_id=%s stage=%s exception_type=%s "
        "duration_ms=%.3f cancelled=%s",
        str(run.run_id),
        stage,
        type(exc).__name__,
        _elapsed_ms(started_at),
        "true" if cancelled else "false",
    )


def _elapsed_ms(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000.0


__all__ = ["BuildNatalHandler"]
