"""Aggregate persistence contract for one session lifecycle."""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, Self, runtime_checkable

from pydantic import BaseModel, ConfigDict, model_validator

from exact_orb.session.dialog import DialogStore, DialogTurn
from exact_orb.session.outcomes import SessionAbsent, VersionConflict
from exact_orb.session.state import SessionState, StoredChart
from exact_orb.session.store import SessionStore
from exact_orb.birth.types import BirthTimeDomain


class SessionSnapshot(BaseModel):
    """Consistent state, dialog, and chart from one aggregate operation."""

    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

    state: SessionState
    dialog: tuple[DialogTurn, ...]
    chart: StoredChart | None

    @model_validator(mode="after")
    def _chart_matches_state(self) -> Self:
        if (self.state.base_chart is None) != (self.chart is None):
            raise ValueError("state.base_chart and chart must be present together")
        return self


@runtime_checkable
class UnknownTimeStateMigrator(Protocol):
    """Birth-owned synchronous seam used only for legacy unknown-time state."""

    def __call__(
        self,
        birth_date: date,
        tz_id: str,
    ) -> tuple[datetime, int, BirthTimeDomain]: ...


@runtime_checkable
class SessionPersistence(Protocol):
    """Aggregate exposing co-located state, dialog, and chart persistence.

    Implementations of ``reset`` delegate to
    ``sessions.compare_and_set(session_id, expected_state_version,
    RESET_DELTA, now=now)``. The facet CAS owns the atomic state transition,
    dialog/chart clear, and shared TTL update; aggregate adapters must not
    implement a second reset algorithm.
    """

    sessions: SessionStore
    dialogs: DialogStore

    async def touch(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionSnapshot | SessionAbsent:
        """Atomically renew live state TTL and load its dialog and chart."""

        ...

    async def reset(
        self,
        session_id: str,
        expected_state_version: int,
        *,
        now: datetime,
    ) -> int | VersionConflict | SessionAbsent:
        """Delegate the canonical reset delta to the state facet CAS."""

        ...

    async def delete(self, session_id: str) -> None:
        """Idempotently delete state, dialog, and chart atomically."""

        ...


__all__ = [
    "SessionPersistence",
    "SessionSnapshot",
    "UnknownTimeStateMigrator",
]
