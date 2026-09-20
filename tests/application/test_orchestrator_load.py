"""Загрузка сессии и original expected: карточка 4.1, ApplicationOrchestrator R3.2.

Отказы ожидают 4.2, snapshot -> Handler — 5.2, исходная версия на save — 6.4.
Тесты вызывают настоящий execute; CAS и расчётный движок здесь не исполняются.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
import json
import logging
import math

import pytest

from exact_orb.application.application_results import (
    ApplicationInputRequired,
    ApplicationInternalFailure,
    ApplicationResult,
    ApplicationSessionAbsent,
    ApplicationStateReadFailure,
    ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand, Command
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.results import BuildNatalOutcome, BuildNatalSuccess
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.outcomes import InputRequired, Issue
from exact_orb.run_context import RunContext
from exact_orb.session.outcomes import SessionAbsent, StateCommitFailed, StateReadFailed, Superseded
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import SessionState, StateDelta, new_session
from tests.application.orchestrator_fakes import Call, RecordingContext, RecordingHandler
from tests.fixtures.calculation import artifact, chart_spec, resolved_birth_data
from tests.fixtures.telemetry import RUN_ID_B, STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit
SESSION_ID = "load-session"
START = "application_operation_started"
STAGE = "application_stage_finished"
ATTEMPT = "application_commit_attempt_finished"
FINISH = "application_operation_finished"
EVENTS = {START, STAGE, ATTEMPT, FINISH}


class LoadCommand(Command):
    """An explicitly registered command for isolated load scenarios."""


@pytest.fixture
def journal() -> list[Call]:
    return []


@pytest.fixture
def run() -> RunContext:
    return RunContext(run_id=RUN_ID_B, started_at=STARTED_AT)


@pytest.fixture
def handler(journal: list[Call]) -> RecordingHandler:
    return RecordingHandler(
        journal, result=InputRequired(issues=(Issue(field="place_id", code="MISSING"),)),
    )


@pytest.fixture(autouse=True)
def application_records(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture lifecycle and exception records, preserving the logger configuration."""
    logger = logging.getLogger("exact_orb.application")
    handlers = logger.handlers[:]
    propagate, level, disabled = logger.propagate, logger.level, logger.disabled
    try:
        caplog.set_level(logging.DEBUG, logger=logger.name)
        logger.handlers = [caplog.handler]
        logger.propagate = False
        logger.disabled = False
        # Keep caplog itself: setup and call have different record lists.
        yield caplog
    finally:
        logger.handlers = handlers
        logger.propagate = propagate
        logger.setLevel(level)
        logger.disabled = disabled


def _snapshot(version: int) -> SessionSnapshot:
    state = SessionState.model_validate({
        **new_session(SESSION_ID, now=STARTED_AT).model_dump(),
        "state_version": version,
    })
    return SessionSnapshot(state=state, dialog=())


def _orchestrator(context: RecordingContext, command: Command, handler: RecordingHandler) -> ApplicationOrchestrator:
    return ApplicationOrchestrator(
        context=context, handlers={type(command): handler}, clock=lambda: STARTED_AT,
    )


def _fields(record: logging.LogRecord) -> dict[str, object]:
    message = record.getMessage()
    assert len(message.splitlines()) == 1
    fields = json.loads(message.partition(" ")[2])
    assert isinstance(fields, dict)
    return fields


def _events(
    caplog: pytest.LogCaptureFixture, command: Command, run: RunContext, names: list[str],
) -> list[logging.LogRecord]:
    records = [record for record in caplog.records if record.getMessage().partition(" ")[0] in EVENTS]
    assert [record.getMessage().partition(" ")[0] for record in records] == names
    assert records[0].levelno == logging.INFO
    assert _fields(records[0]) == {"run_id": str(run.run_id), "command_type": type(command).__name__}
    assert all(_fields(record)["run_id"] == str(run.run_id) for record in records)
    assert all(SESSION_ID not in record.getMessage() for record in records)
    return records


def _assert_stage(
    record: logging.LogRecord, run: RunContext, *, stage: str, outcome: str,
    version: int | None, level: int = logging.DEBUG,
) -> float:
    fields = _fields(record)
    duration = fields["duration_ms"]
    assert type(duration) in (int, float)
    assert math.isfinite(duration) and duration >= 0
    expected = {"run_id": str(run.run_id), "stage": stage, "outcome": outcome, "duration_ms": duration}
    # The load prompt requires the loaded version; Handler's field is optional
    # in §11.5, but must be truthful whenever it is emitted.
    if version is not None and (stage == "load" or "state_version" in fields):
        expected["state_version"] = version
    assert fields == expected
    assert record.levelno == level
    return duration


def _assert_terminal(
    record: logging.LogRecord, result: ApplicationResult, *, load_duration: float,
    handler_duration: float | None = None, commit_duration: float | None = None,
    commit_attempts: int = 0,
) -> None:
    assert record.levelno == (logging.WARNING if result.orch_status == "FAILURE" else logging.INFO)
    assert _fields(record) == {
        "terminal_kind": "result", "run_id": str(result.run_id),
        "orch_status": result.orch_status, "handler_status": result.handler_status,
        "context_status": result.context_status, "code": result.code,
        "detail_code": result.detail_code, "state_version": result.state_version,
        "load_duration_ms": load_duration, "handler_duration_ms": handler_duration,
        "commit_duration_ms": commit_duration, "commit_attempts": commit_attempts,
        "commit_error_codes": [], "delivery_cancelled": False,
    }


def _assert_load_refusal(
    journal: list[Call], context: RecordingContext, caplog: pytest.LogCaptureFixture,
    command: Command, run: RunContext, result: ApplicationResult, *, outcome: str,
) -> None:
    # The snapshot and save tests below are positive controls for these absences.
    assert journal == [Call(context, "load", (SESSION_ID,))]
    records = _events(caplog, command, run, [START, STAGE, FINISH])
    duration = _assert_stage(
        records[1], run, stage="load", outcome=outcome, version=None,
        level=logging.WARNING if outcome in {"unexpected_failure", "invalid_outcome"} else logging.DEBUG,
    )
    _assert_terminal(records[-1], result, load_duration=duration)


def _assert_internal_failure(result: ApplicationResult, run: RunContext) -> None:
    assert isinstance(result, ApplicationInternalFailure)
    assert result.model_dump() == {
        "orch_status": "FAILURE", "handler_status": "NOT_STARTED", "context_status": "NOT_ACCESSED",
        "code": "INTERNAL_FAILURE", "detail_code": None, "user_message": "Произошла внутренняя ошибка.",
        "retryable": False, "run_id": run.run_id, "state_version": None,
    }


@pytest.mark.parametrize(("reason", "code", "message"), [
    ("expired", "SESSION_EXPIRED", "Сессия истекла. Введите данные рождения заново."),
    ("not_found", "SESSION_NOT_FOUND", "Сессия не найдена. Начните заново."),
], ids=["expired", "not_found"])
async def test_absent_load_returns_reason_without_handler_or_save(
    reason: str, code: str, message: str, journal: list[Call], handler: RecordingHandler,
    run: RunContext, application_records: pytest.LogCaptureFixture,
) -> None:
    """Отсутствие сессии при load сохраняет причину и завершает запрос до Handler.

    R3.2 FR-06/26, §8–12; AC-5/6/19/20/26/27/29/30 частично. После 4.2.
    Положительные пары: snapshot reaches handler и save uses original version.
    """
    context = RecordingContext(journal, load_result=SessionAbsent(reason=reason))
    command = LoadCommand()
    result = await _orchestrator(context, command, handler).execute(command, session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationSessionAbsent)
    assert result.model_dump() == {
        "orch_status": "SESSION_ABSENT", "handler_status": "NOT_STARTED", "context_status": "SESSION_ABSENT",
        "code": code, "detail_code": None, "user_message": message, "retryable": False,
        "run_id": run.run_id, "state_version": None, "reason": reason,
    }
    _assert_load_refusal(journal, context, application_records, command, run, result, outcome="session_absent")


@pytest.mark.parametrize("error_code", ["SQLITE_BUSY", "SYNTHETIC_READ_FAILURE"])
async def test_read_failed_preserves_code_without_handler_or_retry(
    error_code: str, journal: list[Call], handler: RecordingHandler, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """Ошибка чтения не означает потерю сессии; открытый код сохраняется без retry load.

    R3.2 FR-06/26, §8–12; AC-5/6/19/26/27/29/30 частично. После 4.2.
    Положительный контроль вызова Handler — test_snapshot_reaches_handler_with_loaded_version.
    """
    context = RecordingContext(journal, load_result=StateReadFailed(error_code=error_code))
    command = LoadCommand()
    result = await _orchestrator(context, command, handler).execute(command, session_id=SESSION_ID, run=run)

    assert isinstance(result, ApplicationStateReadFailure)
    assert result.model_dump() == {
        "orch_status": "FAILURE", "handler_status": "NOT_STARTED", "context_status": "READ_FAILED",
        "code": "STATE_READ_FAILED", "detail_code": error_code,
        "user_message": "Не удалось загрузить данные сессии. Попробуйте ещё раз.", "retryable": True,
        "run_id": run.run_id, "state_version": None,
    }
    _assert_load_refusal(journal, context, application_records, command, run, result, outcome="state_read_failed")


async def test_unexpected_load_exception_is_logged_and_normalized(
    journal: list[Call], handler: RecordingHandler, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """Исключение load журналируется с traceback, наружу выходит фиксированный текст.

    R3.2 FR-25/26, §8–12; AC-19/21/26/27/29/30 частично. После 4.2.
    Snapshot-контроль подтверждает, что отсутствие handle/save не безусловно.
    """
    error = RuntimeError("synthetic read exception /private/session.db")

    class RaisingContext(RecordingContext):
        async def load(self, session_id: str) -> SessionSnapshot:
            await super().load(session_id)
            raise error

    context = RaisingContext(journal, load_result=_snapshot(7))
    command = LoadCommand()
    result = await _orchestrator(context, command, handler).execute(command, session_id=SESSION_ID, run=run)

    _assert_internal_failure(result, run)
    assert str(error) not in result.user_message
    diagnostics = [record for record in application_records.records if record.exc_info]
    assert any(record.exc_info[1] is error and record.exc_info[2] is not None for record in diagnostics)
    _assert_load_refusal(journal, context, application_records, command, run, result, outcome="unexpected_failure")


@pytest.mark.parametrize("invalid", [None, StateCommitFailed(error_code="NOT_A_LOAD_OUTCOME")], ids=["none", "foreign_outcome"])
async def test_unexpected_invalid_outcome_from_load_is_internal_failure(
    invalid: object, journal: list[Call], handler: RecordingHandler, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """None и чужой typed outcome не передаются Handler и не становятся session absence.

    R3.2 FR-25/26, §7–12; AC-19/21/26/27/29/30 частично. После 4.2.
    Валидные SessionSnapshot/SessionAbsent/StateReadFailed проверяются отдельными сценариями.
    """
    class InvalidContext(RecordingContext):
        async def load(self, session_id: str) -> object:
            await super().load(session_id)
            return invalid

    context = InvalidContext(journal, load_result=_snapshot(7))
    command = LoadCommand()
    result = await _orchestrator(context, command, handler).execute(command, session_id=SESSION_ID, run=run)

    _assert_internal_failure(result, run)
    assert any(
        record.exc_info and isinstance(record.exc_info[1], Exception) and record.exc_info[2] is not None
        for record in application_records.records
    )
    _assert_load_refusal(journal, context, application_records, command, run, result, outcome="invalid_outcome")


@pytest.mark.parametrize("version", [0, 7])
async def test_snapshot_reaches_handler_with_loaded_version(
    version: int, journal: list[Call], handler: RecordingHandler, run: RunContext,
    application_records: pytest.LogCaptureFixture,
) -> None:
    """Snapshot передаётся по identity после единственного load; версии 0 и 7 не теряются.

    R3.2 FR-06–08/26; AC-5/7/26/27/29/30 частично. После 5.2.
    Положительная пара ко всем отказам load; непустой InputRequired не закрывает K3.
    """
    snapshot = _snapshot(version)
    context = RecordingContext(journal, load_result=snapshot)
    command = LoadCommand()
    result = await _orchestrator(context, command, handler).execute(command, session_id=SESSION_ID, run=run)

    assert [call.method for call in journal] == ["load", "handle"]
    assert journal[0] == Call(context, "load", (SESSION_ID,))
    handled = journal[1]
    assert handled.target is handler
    assert len(handled.args) == 3
    assert handled.args[0] is command and handled.args[1] is snapshot.state and handled.args[2] is run
    assert isinstance(result, ApplicationInputRequired)
    assert isinstance(handler.result, InputRequired)
    assert result.issues == handler.result.issues
    assert result.state_version == version and result.run_id == run.run_id
    records = _events(application_records, command, run, [START, STAGE, STAGE, FINISH])
    loaded = _assert_stage(records[1], run, stage="load", outcome="loaded", version=version)
    handled_duration = _assert_stage(records[2], run, stage="handler", outcome="input_required", version=version)
    _assert_terminal(records[-1], result, load_duration=loaded, handler_duration=handled_duration)


@pytest.mark.parametrize("version", [0, 7])
async def test_save_uses_original_version_when_available_snapshot_changes(
    version: int, journal: list[Call], run: RunContext, application_records: pytest.LogCaptureFixture,
) -> None:
    """Save получает исходную версию и ту же delta, хотя доступный snapshot уже новее.

    R3.2 FR-07/11/13/16/26; AC-5/7/19/26/27/29/30 частично. После 6.4.
    Положительный контроль настоящего вызова save через execute; не тест реального CAS.
    """
    snapshot, newer = _snapshot(version), _snapshot(version + 2)
    original_version = snapshot.state.state_version
    original_state = snapshot.state.model_dump()
    context = RecordingContext(journal, load_result=snapshot, save_result=Superseded(actual=newer.state))
    spec, fixture_birth = chart_spec(), resolved_birth_data()
    resolved = ResolvedBirthData.model_validate({
        **fixture_birth.model_dump(),
        "utc_datetime": fixture_birth.utc_datetime.replace(second=0, microsecond=0),
    })
    local_birth = resolved.utc_datetime + timedelta(seconds=resolved.utc_offset_seconds)
    birth_input = BirthInput(
        birth_date=local_birth.date(), birth_time=local_birth.time().replace(tzinfo=None), place_id="moscow-ru",
    )
    command = BuildNatalCommand(birth_input=birth_input)
    outcome = BuildNatalSuccess(
        artifact=artifact(spec=spec, resolved=resolved),
        delta=StateDelta(birth_input=birth_input, birth_resolved=resolved, base_chart_spec=spec),
    )

    class ReplacingHandler(RecordingHandler):
        async def handle(self, command: Command, state: SessionState, run: RunContext) -> BuildNatalOutcome:
            result = await super().handle(command, state, run)
            context.load_result = newer
            return result

    handler = ReplacingHandler(journal, result=outcome)
    result = await _orchestrator(context, command, handler).execute(command, session_id=SESSION_ID, run=run)

    assert context.load_result is newer
    assert snapshot.state.model_dump() == original_state
    assert [call.method for call in journal] == ["load", "handle", "save"]
    assert journal[0] == Call(context, "load", (SESSION_ID,))
    handled, saved = journal[1:]
    assert handled.target is handler and len(handled.args) == 3
    assert handled.args[0] is command and handled.args[1] is snapshot.state and handled.args[2] is run
    assert saved.target is context and len(saved.args) == 3
    assert saved.args[:2] == (SESSION_ID, original_version)
    assert saved.args[1] != newer.state.state_version
    assert saved.args[2] is outcome.delta
    assert isinstance(result, ApplicationSuperseded)
    assert result.state_version == newer.state.state_version and result.run_id == run.run_id
    records = _events(application_records, command, run, [START, STAGE, STAGE, ATTEMPT, FINISH])
    loaded = _assert_stage(records[1], run, stage="load", outcome="loaded", version=original_version)
    handled_duration = _assert_stage(records[2], run, stage="handler", outcome="success", version=original_version)
    attempt = _fields(records[3])
    duration = attempt["duration_ms"]
    assert type(duration) in (int, float) and math.isfinite(duration) and duration >= 0
    assert records[3].levelno == logging.DEBUG
    assert attempt == {
        "run_id": str(run.run_id), "attempt": 1, "outcome": "superseded", "detail_code": None,
        "duration_ms": duration, "state_version": newer.state.state_version,
    }
    _assert_terminal(
        records[-1], result, load_duration=loaded, handler_duration=handled_duration,
        commit_duration=duration, commit_attempts=1,
    )
