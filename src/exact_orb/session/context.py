"""Application-facing coordination for one session persistence aggregate."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from exact_orb.session.dialog import DialogTurn
from exact_orb.session.errors import SessionPersistenceError
from exact_orb.session.outcomes import (
    AlreadyApplied,
    Committed,
    SessionAbsent,
    SessionCreated,
    SessionIdConflict,
    StateCommitFailed,
    StateReadFailed,
    Superseded,
    VersionConflict,
)
from exact_orb.session.persistence import SessionPersistence, SessionSnapshot
from exact_orb.session.state import RESET_DELTA, StateDelta, matches_intent, require_utc


def _classify_commit_result(
    result: int | VersionConflict | SessionAbsent,
    delta: StateDelta,
) -> Committed | AlreadyApplied | Superseded | SessionAbsent:
    if isinstance(result, int):
        return Committed(state_version=result)
    if isinstance(result, SessionAbsent):
        return result
    if matches_intent(result.actual, delta):
        return AlreadyApplied(state_version=result.actual.state_version)
    return Superseded(actual=result.actual)


class ContextService:
    """Coordinate session operations without owning persistence mechanics."""

    def __init__(
        self,
        *,
        persistence: SessionPersistence,
        clock: Callable[[], datetime],
    ) -> None:
        self._persistence = persistence
        self._clock = clock

    def _now(self) -> datetime:
        return require_utc(self._clock(), name="clock")

    async def create(
        self,
        session_id: str,
    ) -> SessionCreated | SessionIdConflict | StateCommitFailed:
        now = self._now()
        try:
            return await self._persistence.sessions.create(session_id, now=now)
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)

    async def load(
        self,
        session_id: str,
    ) -> SessionSnapshot | SessionAbsent | StateReadFailed:
        now = self._now()
        try:
            return await self._persistence.touch(session_id, now=now)
        except SessionPersistenceError as exc:
            return StateReadFailed(error_code=exc.error_code)

    async def save(
        self,
        session_id: str,
        expected_state_version: int,
        delta: StateDelta,
    ) -> Committed | AlreadyApplied | Superseded | SessionAbsent | StateCommitFailed:
        now = self._now()
        try:
            result = await self._persistence.sessions.compare_and_set(
                session_id,
                expected_state_version,
                delta,
                now=now,
            )
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)
        return _classify_commit_result(result, delta)

    async def append_turn(
        self,
        session_id: str,
        turn: DialogTurn,
    ) -> None | SessionAbsent | StateCommitFailed:
        now = self._now()
        try:
            return await self._persistence.dialogs.append(session_id, turn, now=now)
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)

    async def clear_dialog(
        self,
        session_id: str,
    ) -> None | SessionAbsent | StateCommitFailed:
        now = self._now()
        try:
            return await self._persistence.dialogs.clear(session_id, now=now)
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)

    async def reset_all(
        self,
        session_id: str,
        expected_state_version: int,
    ) -> Committed | AlreadyApplied | Superseded | SessionAbsent | StateCommitFailed:
        now = self._now()
        try:
            result = await self._persistence.reset(
                session_id,
                expected_state_version,
                now=now,
            )
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)
        return _classify_commit_result(result, RESET_DELTA)

    async def delete(self, session_id: str) -> None | StateCommitFailed:
        try:
            return await self._persistence.delete(session_id)
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)


__all__ = ["ContextService"]
