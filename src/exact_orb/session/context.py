"""Application-facing coordination for one session persistence aggregate."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import wraps
from inspect import signature
import json
import logging
from typing import ParamSpec, TypeVar

from pydantic import BaseModel

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


LOGGER = logging.getLogger(__name__)
P = ParamSpec("P")
R = TypeVar("R")


def _json_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", warnings=False)
    if isinstance(value, BaseException):
        return {"exception_type": type(value).__name__, "message": str(value)}
    return repr(value)


def _log_boundary(
    *, direction: str, operation: str, message: object,
    message_type: str | None = None, error: bool = False,
) -> None:
    if not LOGGER.isEnabledFor(logging.DEBUG):
        return
    LOGGER.debug(
        "component_message direction=%s operation=context_%s run_id=- "
        "calculation_key=- status=%s payload_mode=%s message_type=%s message=%s",
        direction, operation, "error" if error else "ok",
        "error" if error else "full", message_type or type(message).__name__,
        json.dumps(
            message, default=_json_value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ),
    )


def _context_boundary(
    operation: str,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Trace one public ContextService call without changing its signature."""
    request_type = "Context" + "".join(part.title() for part in operation.split("_")) + "Request"

    def decorate(method: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        method_signature = signature(method)

        @wraps(method)
        async def traced(*args: P.args, **kwargs: P.kwargs) -> R:
            if LOGGER.isEnabledFor(logging.DEBUG):
                request = {
                    key: value
                    for key, value in method_signature.bind(*args, **kwargs).arguments.items()
                    if key != "self"
                }
                _log_boundary(
                    direction="in", operation=operation, message=request,
                    message_type=request_type,
                )
            try:
                result = await method(*args, **kwargs)
            except BaseException as exc:
                _log_boundary(direction="out", operation=operation, message=exc, error=True)
                raise
            _log_boundary(direction="out", operation=operation, message=result)
            return result

        return traced

    return decorate


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

    @_context_boundary("create")
    async def create(
        self,
        session_id: str,
    ) -> SessionCreated | SessionIdConflict | StateCommitFailed:
        now = self._now()
        try:
            return await self._persistence.sessions.create(session_id, now=now)
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)

    @_context_boundary("load")
    async def load(
        self,
        session_id: str,
    ) -> SessionSnapshot | SessionAbsent | StateReadFailed:
        now = self._now()
        try:
            return await self._persistence.touch(session_id, now=now)
        except SessionPersistenceError as exc:
            return StateReadFailed(error_code=exc.error_code)

    @_context_boundary("save")
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

    @_context_boundary("append_turn")
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

    @_context_boundary("clear_dialog")
    async def clear_dialog(
        self,
        session_id: str,
    ) -> None | SessionAbsent | StateCommitFailed:
        now = self._now()
        try:
            return await self._persistence.dialogs.clear(session_id, now=now)
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)

    @_context_boundary("reset_all")
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

    @_context_boundary("delete")
    async def delete(self, session_id: str) -> None | StateCommitFailed:
        try:
            return await self._persistence.delete(session_id)
        except SessionPersistenceError as exc:
            return StateCommitFailed(error_code=exc.error_code)


__all__ = ["ContextService"]
