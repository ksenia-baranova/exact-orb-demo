"""Unit and narrow integration tests for the session context boundary."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from inspect import Parameter, iscoroutinefunction, signature

import pytest
from pydantic import ValidationError

from exact_orb.session.adapters import InMemorySessionPersistence
from exact_orb.session.context import ContextService
from exact_orb.session.dialog import DialogStore, DialogTurn
from exact_orb.session.errors import (
    SessionPersistenceError,
    StateReadError,
    StateWriteError,
)
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
from exact_orb.session.state import (
    RESET_DELTA,
    SessionState,
    StateDelta,
    apply_delta,
    new_session,
)
from exact_orb.session.store import SessionStore
from tests.session.conformance import (
    BIRTH_INPUT,
    DELTA,
    NOW,
    OTHER_BIRTH_INPUT,
    OTHER_DELTA,
    RESOLVED,
    SPEC,
    create_session,
    make_turn,
)


pytestmark = pytest.mark.no_ephemeris_autoinit


@dataclass(frozen=True)
class _Call:
    name: str
    args: tuple[object, ...]
    kwargs: dict[str, object]


class _Script:
    def __init__(self) -> None:
        self._responses: dict[str, list[object]] = {}
        self.calls: list[_Call] = []

    def expect(self, name: str, *responses: object) -> None:
        self._responses[name] = list(responses)

    def invoke(
        self,
        name: str,
        *args: object,
        **kwargs: object,
    ) -> object:
        self.calls.append(_Call(name=name, args=args, kwargs=kwargs))
        responses = self._responses.get(name)
        if not responses:
            raise AssertionError(f"unexpected call: {name}")
        response = responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class _RecordingSessionStore:
    def __init__(self, script: _Script) -> None:
        self._script = script

    async def create(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionCreated | SessionIdConflict:
        return self._script.invoke("sessions.create", session_id, now=now)  # type: ignore[return-value]

    async def get(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionState | SessionAbsent:
        return self._script.invoke("sessions.get", session_id, now=now)  # type: ignore[return-value]

    async def compare_and_set(
        self,
        session_id: str,
        expected_state_version: int,
        delta: StateDelta,
        *,
        now: datetime,
    ) -> int | VersionConflict | SessionAbsent:
        return self._script.invoke(  # type: ignore[return-value]
            "sessions.compare_and_set",
            session_id,
            expected_state_version,
            delta,
            now=now,
        )


class _RecordingDialogStore:
    def __init__(self, script: _Script) -> None:
        self._script = script

    async def append(
        self,
        session_id: str,
        turn: DialogTurn,
        *,
        now: datetime,
    ) -> None | SessionAbsent:
        return self._script.invoke("dialogs.append", session_id, turn, now=now)  # type: ignore[return-value]

    async def read(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> tuple[DialogTurn, ...] | SessionAbsent:
        return self._script.invoke("dialogs.read", session_id, now=now)  # type: ignore[return-value]

    async def clear(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> None | SessionAbsent:
        return self._script.invoke("dialogs.clear", session_id, now=now)  # type: ignore[return-value]


class _RecordingPersistence:
    def __init__(self, script: _Script) -> None:
        self._script = script
        self.sessions = _RecordingSessionStore(script)
        self.dialogs = _RecordingDialogStore(script)

    async def touch(
        self,
        session_id: str,
        *,
        now: datetime,
    ) -> SessionSnapshot | SessionAbsent:
        return self._script.invoke("persistence.touch", session_id, now=now)  # type: ignore[return-value]

    async def reset(
        self,
        session_id: str,
        expected_state_version: int,
        *,
        now: datetime,
    ) -> int | VersionConflict | SessionAbsent:
        return self._script.invoke(  # type: ignore[return-value]
            "persistence.reset",
            session_id,
            expected_state_version,
            now=now,
        )

    async def delete(self, session_id: str) -> None:
        return self._script.invoke("persistence.delete", session_id)  # type: ignore[return-value]


class _RecordingClock:
    def __init__(self, result: datetime | BaseException = NOW) -> None:
        self.result = result
        self.calls = 0

    def __call__(self) -> datetime:
        self.calls += 1
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


def _service(
    *,
    clock_result: datetime | BaseException = NOW,
) -> tuple[ContextService, _RecordingPersistence, _RecordingClock, _Script]:
    script = _Script()
    persistence = _RecordingPersistence(script)
    clock = _RecordingClock(clock_result)
    return (
        ContextService(persistence=persistence, clock=clock),
        persistence,
        clock,
        script,
    )


def _empty_state(session_id: str = "session-1") -> SessionState:
    return new_session(session_id, now=NOW)


def _populated_state(
    delta: StateDelta = DELTA,
    *,
    session_id: str = "session-1",
) -> SessionState:
    return apply_delta(_empty_state(session_id), delta, now=NOW)


_PUBLIC_PARAMETERS = {
    "create": ("self", "session_id"),
    "load": ("self", "session_id"),
    "save": ("self", "session_id", "expected_state_version", "delta"),
    "append_turn": ("self", "session_id", "turn"),
    "clear_dialog": ("self", "session_id"),
    "reset_all": ("self", "session_id", "expected_state_version"),
    "delete": ("self", "session_id"),
}


def test_constructor_has_exact_keyword_only_dependencies() -> None:
    parameters = signature(ContextService.__init__).parameters

    assert tuple(parameters) == ("self", "persistence", "clock")
    assert parameters["self"].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["persistence"].kind is Parameter.KEYWORD_ONLY
    assert parameters["clock"].kind is Parameter.KEYWORD_ONLY


@pytest.mark.parametrize(("method_name", "parameter_names"), _PUBLIC_PARAMETERS.items())
def test_public_methods_are_async_and_do_not_accept_now(
    method_name: str,
    parameter_names: tuple[str, ...],
) -> None:
    method = getattr(ContextService, method_name)
    parameters = signature(method).parameters

    assert iscoroutinefunction(method)
    assert tuple(parameters) == parameter_names
    assert "now" not in parameters


def test_recording_fakes_satisfy_runtime_ports() -> None:
    _, persistence, _, _ = _service()

    assert isinstance(persistence, SessionPersistence)
    assert isinstance(persistence.sessions, SessionStore)
    assert isinstance(persistence.dialogs, DialogStore)


_CLOCK_OPERATIONS = (
    "create",
    "load",
    "save",
    "append_turn",
    "clear_dialog",
    "reset_all",
)


def _method_for(operation: str) -> str:
    return {
        "create": "sessions.create",
        "load": "persistence.touch",
        "save": "sessions.compare_and_set",
        "append_turn": "dialogs.append",
        "clear_dialog": "dialogs.clear",
        "reset_all": "persistence.reset",
        "delete": "persistence.delete",
    }[operation]


def _response_for(operation: str) -> object:
    if operation == "create":
        return SessionIdConflict(session_id="session-1")
    if operation in {"load", "save", "append_turn", "clear_dialog", "reset_all"}:
        return SessionAbsent(reason="not_found")
    assert operation == "delete"
    return None


async def _invoke(service: ContextService, operation: str) -> object:
    if operation == "create":
        return await service.create("session-1")
    if operation == "load":
        return await service.load("session-1")
    if operation == "save":
        return await service.save("session-1", 0, DELTA)
    if operation == "append_turn":
        return await service.append_turn("session-1", make_turn())
    if operation == "clear_dialog":
        return await service.clear_dialog("session-1")
    if operation == "reset_all":
        return await service.reset_all("session-1", 0)
    assert operation == "delete"
    return await service.delete("session-1")


@pytest.mark.parametrize("operation", _CLOCK_OPERATIONS)
async def test_each_now_bearing_call_reads_clock_once_and_passes_same_object(
    operation: str,
) -> None:
    service, _, clock, script = _service()
    script.expect(_method_for(operation), _response_for(operation))

    await _invoke(service, operation)

    assert clock.calls == 1
    assert len(script.calls) == 1
    assert script.calls[0].kwargs["now"] is NOW


async def test_delete_does_not_read_clock_or_call_facets() -> None:
    service, _, clock, script = _service()
    script.expect("persistence.delete", None)

    assert await service.delete("session-1") is None

    assert clock.calls == 0
    assert script.calls == [_Call("persistence.delete", ("session-1",), {})]


@pytest.mark.parametrize("operation", _CLOCK_OPERATIONS)
async def test_clock_exception_escapes_before_persistence(operation: str) -> None:
    failure = RuntimeError("clock failed")
    service, _, clock, script = _service(clock_result=failure)

    with pytest.raises(RuntimeError) as caught:
        await _invoke(service, operation)

    assert caught.value is failure
    assert clock.calls == 1
    assert script.calls == []


@pytest.mark.parametrize(
    "invalid_now",
    [
        datetime(2026, 9, 5, 12),
        datetime(2026, 9, 5, 15, tzinfo=timezone(timedelta(hours=3))),
    ],
    ids=["naive", "non-zero-offset"],
)
@pytest.mark.parametrize("operation", _CLOCK_OPERATIONS)
async def test_invalid_clock_result_is_rejected_before_persistence(
    operation: str,
    invalid_now: datetime,
) -> None:
    service, _, clock, script = _service(clock_result=invalid_now)

    with pytest.raises(ValueError) as caught:
        await _invoke(service, operation)

    assert type(caught.value) is ValueError
    assert "clock" in str(caught.value)
    assert clock.calls == 1
    assert script.calls == []


@pytest.mark.parametrize(
    "outcome",
    [
        SessionCreated(state=_empty_state()),
        SessionIdConflict(session_id="session-1"),
    ],
    ids=["created", "conflict"],
)
async def test_create_returns_lifecycle_outcome_without_extra_calls(outcome: object) -> None:
    service, _, _, script = _service()
    script.expect("sessions.create", outcome)

    result = await service.create("session-1")

    assert result is outcome
    assert script.calls == [_Call("sessions.create", ("session-1",), {"now": NOW})]


_PERSISTENCE_ERRORS = (SessionPersistenceError, StateReadError, StateWriteError)
_MUTATING_OPERATIONS = (
    "create",
    "save",
    "append_turn",
    "clear_dialog",
    "reset_all",
    "delete",
)


@pytest.mark.parametrize("error_type", _PERSISTENCE_ERRORS)
@pytest.mark.parametrize("operation", _MUTATING_OPERATIONS)
async def test_all_mutating_operations_map_any_persistence_error_to_commit_failed(
    operation: str,
    error_type: type[SessionPersistenceError],
) -> None:
    service, _, _, script = _service()
    script.expect(_method_for(operation), error_type("PERSISTENCE_UNAVAILABLE"))

    result = await _invoke(service, operation)

    assert result == StateCommitFailed(error_code="PERSISTENCE_UNAVAILABLE")
    assert len(script.calls) == 1


async def test_load_returns_snapshot_by_identity_without_facet_reads() -> None:
    service, _, _, script = _service()
    snapshot = SessionSnapshot(state=_empty_state(), dialog=())
    script.expect("persistence.touch", snapshot)

    result = await service.load("session-1")

    assert result is snapshot
    assert script.calls == [_Call("persistence.touch", ("session-1",), {"now": NOW})]


@pytest.mark.parametrize("reason", ["not_found", "expired"])
async def test_load_preserves_absence(reason: str) -> None:
    service, _, _, script = _service()
    absent = SessionAbsent(reason=reason)  # type: ignore[arg-type]
    script.expect("persistence.touch", absent)

    result = await service.load("session-1")

    assert result is absent


@pytest.mark.parametrize("error_type", _PERSISTENCE_ERRORS)
async def test_load_maps_any_persistence_error_to_read_failed(
    error_type: type[SessionPersistenceError],
) -> None:
    service, _, _, script = _service()
    script.expect("persistence.touch", error_type("TOUCH_FAILED"))

    result = await service.load("session-1")

    assert result == StateReadFailed(error_code="TOUCH_FAILED")
    assert script.calls == [_Call("persistence.touch", ("session-1",), {"now": NOW})]


async def test_failed_touch_never_returns_a_previous_snapshot() -> None:
    service, _, _, script = _service()
    previous = SessionSnapshot(state=_empty_state(), dialog=())
    script.expect(
        "persistence.touch",
        previous,
        StateWriteError("RENEW_FAILED"),
    )

    first = await service.load("session-1")
    failed = await service.load("session-1")

    assert first is previous
    assert failed == StateReadFailed(error_code="RENEW_FAILED")
    assert len(script.calls) == 2


async def test_save_passes_original_expected_delta_and_now_by_identity() -> None:
    service, _, _, script = _service()
    script.expect("sessions.compare_and_set", 4)

    result = await service.save("session-1", 3, DELTA)

    assert result == Committed(state_version=4)
    assert len(script.calls) == 1
    call = script.calls[0]
    assert call.name == "sessions.compare_and_set"
    assert call.args[:2] == ("session-1", 3)
    assert call.args[2] is DELTA
    assert call.kwargs["now"] is NOW


@pytest.mark.parametrize("reason", ["not_found", "expired"])
async def test_save_preserves_absence(reason: str) -> None:
    service, _, _, script = _service()
    absent = SessionAbsent(reason=reason)  # type: ignore[arg-type]
    script.expect("sessions.compare_and_set", absent)

    result = await service.save("session-1", 0, DELTA)

    assert result is absent
    assert len(script.calls) == 1


async def test_save_classifies_same_intent_without_an_extra_get() -> None:
    service, _, _, script = _service()
    actual = _populated_state()
    script.expect("sessions.compare_and_set", VersionConflict(actual=actual))

    result = await service.save("session-1", 0, DELTA)

    assert result == AlreadyApplied(state_version=1)
    assert [call.name for call in script.calls] == ["sessions.compare_and_set"]


async def test_save_ignores_birth_input_spelling_when_matching_intent() -> None:
    equivalent = StateDelta(
        birth_input=OTHER_BIRTH_INPUT,
        birth_resolved=RESOLVED,
        base_chart_spec=SPEC,
    )
    service, _, _, script = _service()
    actual = _populated_state(equivalent)
    script.expect("sessions.compare_and_set", VersionConflict(actual=actual))

    result = await service.save("session-1", 0, DELTA)

    assert result == AlreadyApplied(state_version=1)


async def test_save_classifies_different_intent_as_neutral_superseded() -> None:
    service, _, _, script = _service()
    actual = _populated_state(OTHER_DELTA)
    script.expect("sessions.compare_and_set", VersionConflict(actual=actual))

    result = await service.save("session-1", 0, DELTA)

    assert result == Superseded(actual=actual)
    assert [call.name for call in script.calls] == ["sessions.compare_and_set"]


async def test_fresh_version_zero_reset_intent_is_already_applied() -> None:
    service, _, _, script = _service()
    actual = _empty_state()
    script.expect("sessions.compare_and_set", VersionConflict(actual=actual))

    result = await service.save("session-1", 1, RESET_DELTA)

    assert result == AlreadyApplied(state_version=0)


async def test_fresh_version_zero_populated_intent_is_superseded_mismatch() -> None:
    service, _, _, script = _service()
    actual = _empty_state()
    script.expect("sessions.compare_and_set", VersionConflict(actual=actual))

    result = await service.save("session-1", 1, DELTA)

    assert result == Superseded(actual=actual)


@pytest.mark.parametrize(
    "persistence_result",
    [
        2,
        SessionAbsent(reason="not_found"),
        VersionConflict(actual=_empty_state()),
        VersionConflict(actual=_populated_state()),
    ],
    ids=["committed", "absent", "same-reset-intent", "different-intent"],
)
async def test_save_reset_delta_and_reset_all_have_equivalent_classification(
    persistence_result: object,
) -> None:
    save_service, _, _, save_script = _service()
    reset_service, _, _, reset_script = _service()
    save_script.expect("sessions.compare_and_set", persistence_result)
    reset_script.expect("persistence.reset", persistence_result)

    saved = await save_service.save("session-1", 1, RESET_DELTA)
    reset = await reset_service.reset_all("session-1", 1)

    assert saved == reset
    assert save_script.calls[0].args[2] is RESET_DELTA
    assert [call.name for call in reset_script.calls] == ["persistence.reset"]


async def test_two_same_intent_saves_commit_once_without_rebase() -> None:
    persistence = InMemorySessionPersistence()
    await create_session(persistence, "concurrent")
    clock = _RecordingClock()
    service = ContextService(persistence=persistence, clock=clock)
    barrier = asyncio.Barrier(2)

    async def save() -> object:
        await barrier.wait()
        return await service.save("concurrent", 0, DELTA)

    results = await asyncio.gather(save(), save())
    stored = await persistence.sessions.get("concurrent", now=NOW)

    assert {type(result) for result in results} == {Committed, AlreadyApplied}
    assert isinstance(stored, SessionState)
    assert stored.state_version == 1
    assert clock.calls == 2


async def test_sequential_retry_keeps_original_expected_and_commits_once() -> None:
    persistence = InMemorySessionPersistence()
    await create_session(persistence, "retry")
    clock = _RecordingClock()
    service = ContextService(persistence=persistence, clock=clock)

    first = await service.save("retry", 0, DELTA)
    retry = await service.save("retry", 0, DELTA)
    stored = await persistence.sessions.get("retry", now=NOW)

    assert first == Committed(state_version=1)
    assert retry == AlreadyApplied(state_version=1)
    assert isinstance(stored, SessionState)
    assert stored.state_version == 1
    assert clock.calls == 2


async def test_old_retry_is_superseded_after_a_different_intent() -> None:
    persistence = InMemorySessionPersistence()
    await create_session(persistence, "old-retry")
    clock = _RecordingClock()
    service = ContextService(persistence=persistence, clock=clock)

    assert await service.save("old-retry", 0, DELTA) == Committed(state_version=1)
    assert await service.save("old-retry", 1, OTHER_DELTA) == Committed(
        state_version=2
    )
    retry = await service.save("old-retry", 0, DELTA)

    assert isinstance(retry, Superseded)
    assert retry.actual.state_version == 2
    assert clock.calls == 3


async def test_append_passes_original_turn_without_read_or_cas() -> None:
    service, _, _, script = _service()
    turn = make_turn(marker=99)
    script.expect("dialogs.append", None)

    result = await service.append_turn("session-1", turn)

    assert result is None
    assert len(script.calls) == 1
    call = script.calls[0]
    assert call.name == "dialogs.append"
    assert call.args == ("session-1", turn)
    assert call.args[1] is turn


@pytest.mark.parametrize("operation", ["append_turn", "clear_dialog"])
@pytest.mark.parametrize("reason", ["not_found", "expired"])
async def test_dialog_mutations_preserve_absence(operation: str, reason: str) -> None:
    service, _, _, script = _service()
    absent = SessionAbsent(reason=reason)  # type: ignore[arg-type]
    script.expect(_method_for(operation), absent)

    result = await _invoke(service, operation)

    assert result is absent
    assert len(script.calls) == 1


async def test_clear_calls_only_dialog_facet() -> None:
    service, _, _, script = _service()
    script.expect("dialogs.clear", None)

    assert await service.clear_dialog("session-1") is None

    assert [call.name for call in script.calls] == ["dialogs.clear"]


@pytest.mark.parametrize(
    ("persistence_result", "expected"),
    [
        (2, Committed(state_version=2)),
        (SessionAbsent(reason="expired"), SessionAbsent(reason="expired")),
        (
            VersionConflict(actual=_empty_state()),
            AlreadyApplied(state_version=0),
        ),
        (
            VersionConflict(actual=_populated_state()),
            Superseded(actual=_populated_state()),
        ),
    ],
    ids=["committed", "absent", "same-reset-intent", "different-intent"],
)
async def test_reset_all_routes_once_and_classifies(
    persistence_result: object,
    expected: object,
) -> None:
    service, _, _, script = _service()
    script.expect("persistence.reset", persistence_result)

    result = await service.reset_all("session-1", 1)

    assert result == expected
    assert script.calls == [
        _Call("persistence.reset", ("session-1", 1), {"now": NOW})
    ]


@pytest.mark.parametrize(
    ("operation", "error_type"),
    [
        ("load", StateWriteError),
        ("save", StateReadError),
    ],
)
async def test_opposite_persistence_error_subclass_is_mapped_by_operation(
    operation: str,
    error_type: type[SessionPersistenceError],
) -> None:
    service, _, _, script = _service()
    script.expect(_method_for(operation), error_type("CROSS_CATEGORY"))

    result = await _invoke(service, operation)

    if operation == "load":
        assert result == StateReadFailed(error_code="CROSS_CATEGORY")
    else:
        assert result == StateCommitFailed(error_code="CROSS_CATEGORY")


@pytest.mark.parametrize("operation", ["load", "save"])
async def test_empty_error_code_is_not_replaced_with_a_fallback(operation: str) -> None:
    service, _, _, script = _service()
    script.expect(_method_for(operation), StateWriteError(""))

    with pytest.raises(ValidationError):
        await _invoke(service, operation)

    assert len(script.calls) == 1


@pytest.mark.parametrize("operation", ["load", "save"])
async def test_cancellation_is_not_mapped_to_a_persistence_outcome(operation: str) -> None:
    service, _, _, script = _service()
    script.expect(_method_for(operation), asyncio.CancelledError())

    with pytest.raises(asyncio.CancelledError):
        await _invoke(service, operation)
