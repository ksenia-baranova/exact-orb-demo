"""Application handler for building a base natal chart or cosmogram."""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import Literal

from pydantic import ValidationError

from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.ports import BirthDataResolverPort, ChartArtifactPort
from exact_orb.application.results import BuildNatalOutcome, BuildNatalSuccess
from exact_orb.component_logging import log_component_message
from exact_orb.calculation.errors import (
    CalculationUnavailableError,
    ChartArtifactEncodingError,
    ChartCalculationError,
)
from exact_orb.calculation.spec import NatalChartSpec
from exact_orb.outcomes import CalculationFailed, InputRequired, ResolutionUnavailable
from exact_orb.run_context import RunContext
from exact_orb.session.state import SessionState, StateDelta, StoredChart


LOGGER = logging.getLogger(__name__)


StoredChartPreparationReason = Literal[
    "ENCODE_FAILED", "ENCODE_UNEXPECTED", "PAYLOAD_SIZE_INVALID", "ENVELOPE_INVALID"
]


class StoredChartPreparationError(Exception):
    """Safe internal failure while preparing a chart for session commit."""

    def __init__(
        self, reason: StoredChartPreparationReason, *, cause_type: str | None = None,
    ) -> None:
        self.reason = reason
        self.cause_type = cause_type
        super().__init__(
            f"reason={reason} cause_type={cause_type}"
            if cause_type is not None else f"reason={reason}"
        )


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
        from exact_orb.component_logging import log_async_component_call

        return await log_async_component_call(
            LOGGER,
            operation="build_natal",
            request_type="BuildNatalRequest",
            run_id=run.run_id,
            request={"command": command, "run": run},
            call=lambda: self._handle(command, run),
            result_calculation_key=_outcome_calculation_key,
        )

    async def _handle(
        self,
        command: BuildNatalCommand,
        run: RunContext,
    ) -> BuildNatalOutcome:
        started_at = perf_counter()
        stage = "resolve"
        _log_started(run)
        try:
            _log_message(
                run, direction="send", peer=type(self._resolver).__name__,
                operation="resolve_birth_data", message_type="BirthResolutionRequest",
            )
            resolution = await self._resolver.resolve(command.birth_input, run=run)
            _log_message(
                run, direction="receive", peer=type(self._resolver).__name__,
                operation="resolve_birth_data", message_type=type(resolution).__name__,
            )
            if isinstance(resolution, (InputRequired, ResolutionUnavailable)):
                _log_completed(run, resolution, None, started_at)
                return resolution

            stage = "build_spec"
            chart_kind = "cosmogram" if resolution.time_unknown else "natal"
            spec = NatalChartSpec(chart_kind=chart_kind)

            stage = "ensure_chart"
            try:
                _log_message(
                    run, direction="send", peer=type(self._artifacts).__name__,
                    operation="ensure_chart", message_type="EnsureChartRequest",
                )
                artifact = await self._artifacts.ensure_chart(
                    spec,
                    resolution,
                    run=run,
                )
                _log_message(
                    run, direction="receive", peer=type(self._artifacts).__name__,
                    operation="ensure_chart", message_type=type(artifact).__name__,
                )
            except (ChartCalculationError, CalculationUnavailableError) as error:
                outcome = CalculationFailed(error_code=error.code)
                _log_completed(run, outcome, chart_kind, started_at)
                return outcome

            stage = "to_stored"
            _log_message(
                run, direction="send", peer=type(self._artifacts).__name__,
                operation="to_stored", message_type="ToStoredRequest",
            )
            log_component_message(
                LOGGER, direction="in", operation="to_stored", run_id=run.run_id,
                message=artifact, message_type="ToStoredRequest",
            )
            try:
                payload_format, payload = self._artifacts.to_stored(artifact)
            except ChartArtifactEncodingError as exc:
                raise StoredChartPreparationError(
                    "ENCODE_FAILED", cause_type=exc.cause_type or type(exc).__name__,
                ) from None
            except MemoryError:
                raise
            except Exception as exc:
                raise StoredChartPreparationError(
                    "ENCODE_UNEXPECTED", cause_type=type(exc).__name__,
                ) from None
            _log_message(
                run, direction="receive", peer=type(self._artifacts).__name__,
                operation="to_stored", message_type="StoredChartEncoding",
            )
            log_component_message(
                LOGGER, direction="out", operation="to_stored", run_id=run.run_id,
                message={"payload_format": payload_format, "payload_size": len(payload)
                         if isinstance(payload, bytes) else None},
                message_type="StoredChartEncoding",
            )

            stage = "build_delta"
            if isinstance(payload, bytes) and not 1 <= len(payload) <= 1_048_576:
                raise StoredChartPreparationError("PAYLOAD_SIZE_INVALID") from None
            try:
                stored_chart = StoredChart(
                    payload_format=payload_format,
                    calculation_key=artifact.calculation_key,
                    calculation_version=artifact.calculation_version,
                    payload=payload,
                )
                delta = StateDelta(
                    birth_input=command.birth_input,
                    birth_resolved=resolution,
                    base_chart_spec=spec,
                    base_chart_payload=stored_chart,
                )
            except ValidationError:
                raise StoredChartPreparationError("ENVELOPE_INVALID") from None
            stage = "build_result"
            outcome = BuildNatalSuccess(artifact=artifact, delta=delta)
            _log_completed(run, outcome, chart_kind, started_at)
            return outcome
        except BaseException as exc:
            _log_failed(run, stage, exc, started_at)
            raise


def _log_message(
    run: RunContext, *, direction: str, peer: str, operation: str, message_type: str,
) -> None:
    LOGGER.info(
        "application_message direction=%s run_id=%s peer=%s operation=%s "
        "message_type=%s attempt=-",
        direction, run.run_id, peer, operation, message_type,
    )


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
            "calculation_key=%s duration_ms=%.3f",
            run_id,
            chart_kind,
            outcome.artifact.calculation_key,
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
    reason = exc.reason if isinstance(exc, StoredChartPreparationError) else "-"
    cause_type = exc.cause_type if isinstance(exc, StoredChartPreparationError) else None
    log(
        "build_natal_failed run_id=%s stage=%s exception_type=%s reason=%s cause_type=%s "
        "duration_ms=%.3f cancelled=%s",
        str(run.run_id),
        stage,
        type(exc).__name__,
        reason,
        cause_type or "-",
        _elapsed_ms(started_at),
        "true" if cancelled else "false",
    )


def _elapsed_ms(started_at: float) -> float:
    return (perf_counter() - started_at) * 1000.0


def _outcome_calculation_key(outcome: BuildNatalOutcome) -> str | None:
    if isinstance(outcome, BuildNatalSuccess):
        return outcome.artifact.calculation_key
    return None


__all__ = ["BuildNatalHandler", "StoredChartPreparationError"]
