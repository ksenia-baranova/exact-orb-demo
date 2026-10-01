"""Pure projection of a stored session chart for the future transport boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Literal, TypeAlias

from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.calculation.chart_contract import calculation_input_from_chart
from exact_orb.calculation.codec import (
    SUPPORTED_CHART_ARTIFACT_PAYLOAD_FORMATS,
    ChartArtifactDecodeError,
    decode_chart_artifact,
)
from exact_orb.calculation.keys import calculation_input_from
from exact_orb.calculation.types import ChartArtifact
from exact_orb.session.persistence import SessionSnapshot


SafeReason: TypeAlias = Literal[
    "UNSUPPORTED_PAYLOAD_FORMAT",
    "DECODE_GZIP_FAILED",
    "DECODE_UTF8_FAILED",
    "DECODE_VALIDATION_FAILED",
    "CALCULATION_KEY_MISMATCH",
    "CALCULATION_VERSION_MISMATCH",
    "SPEC_MISMATCH",
    "CALCULATION_INPUT_MISMATCH",
]


@dataclass(frozen=True, slots=True)
class EmptySessionView:
    state_version: int
    status: Literal["empty"] = field(default="empty", init=False)


@dataclass(frozen=True, slots=True)
class SessionBirthWarning:
    source: Literal["place", "time"]
    code: str


@dataclass(frozen=True, slots=True)
class SessionBirthView:
    """Birth facts from one saved snapshot, without transport types or I/O."""

    birth_date: date
    birth_time: time | None
    place_id: str
    canonical_place: str
    tz_id: str
    utc_offset_seconds: int
    time_unknown: bool
    warnings: tuple[SessionBirthWarning, ...]


@dataclass(frozen=True, slots=True)
class ChartReadySessionView:
    state_version: int
    birth_input: BirthInput
    canonical_place: str
    birth: SessionBirthView
    artifact: ChartArtifact
    chart_stale: bool
    status: Literal["chart_ready"] = field(default="chart_ready", init=False)


@dataclass(frozen=True, slots=True)
class ChartUnavailableSessionView:
    state_version: int
    birth_input: BirthInput
    canonical_place: str
    birth: SessionBirthView
    safe_reason: SafeReason
    status: Literal["chart_unavailable"] = field(default="chart_unavailable", init=False)


SessionView: TypeAlias = (
    EmptySessionView | ChartReadySessionView | ChartUnavailableSessionView
)


def _birth_view(birth_input: BirthInput, resolved: ResolvedBirthData) -> SessionBirthView:
    return SessionBirthView(
        birth_date=birth_input.birth_date,
        birth_time=birth_input.birth_time,
        place_id=birth_input.place_id,
        canonical_place=resolved.canonical_place,
        tz_id=resolved.tz_id,
        utc_offset_seconds=resolved.utc_offset_seconds,
        time_unknown=resolved.time_unknown,
        warnings=tuple(
            SessionBirthWarning(source=warning.source, code=warning.code)
            for warning in resolved.warnings
        ),
    )


def _unavailable(snapshot: SessionSnapshot, reason: SafeReason) -> ChartUnavailableSessionView:
    state = snapshot.state
    assert state.birth_input is not None and state.birth_resolved is not None
    return ChartUnavailableSessionView(
        state_version=state.state_version,
        birth_input=state.birth_input,
        canonical_place=state.birth_resolved.canonical_place,
        birth=_birth_view(state.birth_input, state.birth_resolved),
        safe_reason=reason,
    )


def session_view(snapshot: SessionSnapshot, current_calculation_version: str) -> SessionView:
    """Validate stored bytes and project a snapshot without I/O or recalculation."""

    state = snapshot.state
    stored = snapshot.chart
    if stored is None:
        return EmptySessionView(state_version=state.state_version)

    # SessionSnapshot and SessionState reject one-sided or partial aggregates.
    assert state.base_chart is not None
    assert state.birth_input is not None and state.birth_resolved is not None

    if stored.payload_format not in SUPPORTED_CHART_ARTIFACT_PAYLOAD_FORMATS:
        return _unavailable(snapshot, "UNSUPPORTED_PAYLOAD_FORMAT")

    try:
        artifact = decode_chart_artifact(stored.payload)
    except ChartArtifactDecodeError as exc:
        return _unavailable(snapshot, {
            "gzip": "DECODE_GZIP_FAILED",
            "utf8": "DECODE_UTF8_FAILED",
            "validation": "DECODE_VALIDATION_FAILED",
        }[exc.reason])

    if artifact.calculation_key != stored.calculation_key:
        return _unavailable(snapshot, "CALCULATION_KEY_MISMATCH")
    if artifact.calculation_version != stored.calculation_version:
        return _unavailable(snapshot, "CALCULATION_VERSION_MISMATCH")
    if artifact.spec != state.base_chart.spec:
        return _unavailable(snapshot, "SPEC_MISMATCH")
    if calculation_input_from_chart(artifact.chart) != calculation_input_from(
        state.birth_resolved
    ):
        return _unavailable(snapshot, "CALCULATION_INPUT_MISMATCH")

    return ChartReadySessionView(
        state_version=state.state_version,
        birth_input=state.birth_input,
        canonical_place=state.birth_resolved.canonical_place,
        birth=_birth_view(state.birth_input, state.birth_resolved),
        artifact=artifact,
        chart_stale=artifact.calculation_version != current_calculation_version,
    )


__all__ = [
    "ChartReadySessionView",
    "ChartUnavailableSessionView",
    "EmptySessionView",
    "SessionBirthView",
    "SessionBirthWarning",
    "SafeReason",
    "SessionView",
    "session_view",
]
