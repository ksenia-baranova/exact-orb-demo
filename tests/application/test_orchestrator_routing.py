"""Тесты входа и routing ApplicationOrchestrator, карточка 3.1.

Источник: docs/requirements/component_responsibilities/
exact-orb_application_orchestrator_requirements.md, R3.2.
Отказы проверяются после 3.2; положительные ветки — после 5.2 и 6.4.
Прямой импорт намеренно требует production API, без тестовой подмены.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import timedelta
import inspect
import logging
from uuid import UUID

import pytest

from exact_orb.application.application_results import (
    ApplicationCommitted,
    ApplicationInputRequired,
    ApplicationInternalFailure,
)
from exact_orb.application.commands import BuildNatalCommand, Command
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.results import BuildNatalSuccess
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.outcomes import InputRequired, Issue
from exact_orb.run_context import RunContext
from exact_orb.session.outcomes import Committed, SessionAbsent
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import SessionState, StateDelta, new_session
from tests.application.orchestrator_fakes import Call, RecordingContext, RecordingHandler
from tests.fixtures.telemetry import RUN_ID, RUN_ID_B, STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit
SESSION_ID = "routing-session"
LOGGER_NAME = "exact_orb.application.operation_logging"
LIFECYCLE_EVENTS = {
    "application_operation_started",
    "application_stage_finished",
    "application_commit_attempt_finished",
    "application_operation_finished",
}


class RoutedCommand(Command):
    """A test-only command with an explicit handler assignment."""


class ChildCommand(RoutedCommand):
    """Inheritance alone must not select the parent's handler."""


class OtherCommand(Command):
    """An unrelated command, initially absent from the mapping."""


@pytest.fixture
def journal() -> list[Call]:
    return []


@pytest.fixture
def run() -> RunContext:
    return RunContext(run_id=RUN_ID, started_at=STARTED_AT)


@pytest.fixture
def snapshot() -> SessionSnapshot:
    # A nonzero empty state is valid after reset and detects a hardcoded zero.
    state = SessionState.model_validate({
        **new_session(SESSION_ID, now=STARTED_AT).model_dump(),
        "state_version": 7,
    })
    return SessionSnapshot(state=state, dialog=())


@pytest.fixture
def context(journal: list[Call], snapshot: SessionSnapshot) -> RecordingContext:
    return RecordingContext(journal, load_result=snapshot)


@pytest.fixture
def handler(journal: list[Call]) -> RecordingHandler:
    return RecordingHandler(
        journal,
        result=InputRequired(issues=(Issue(field="place_id", code="MISSING"),)),
    )


@pytest.fixture(autouse=True)
def operation_records(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture real lifecycle messages and restore all temporary logger settings."""
    logger = logging.getLogger(LOGGER_NAME)
    handlers = logger.handlers[:]
    propagate, level, disabled = logger.propagate, logger.level, logger.disabled
    try:
        caplog.set_level(logging.DEBUG, logger=LOGGER_NAME)
        logger.handlers = [caplog.handler]
        logger.propagate = False
        logger.disabled = False
        yield caplog
    finally:
        logger.handlers = handlers
        logger.propagate = propagate
        logger.setLevel(level)
        logger.disabled = disabled


def _orchestrator(
    context: RecordingContext, handlers: dict[type[Command], RecordingHandler],
) -> ApplicationOrchestrator:
    return ApplicationOrchestrator(
        context=context, handlers=handlers, clock=lambda: STARTED_AT,
    )


def _assert_routing_failure(result: object, run: RunContext) -> None:
    assert isinstance(result, ApplicationInternalFailure)
    assert result.model_dump() == {
        "orch_status": "FAILURE",
        "handler_status": "NOT_STARTED",
        "context_status": "NOT_ACCESSED",
        "code": "HANDLER_NOT_REGISTERED",
        "detail_code": None,
        "user_message": "Не удалось выполнить запрос из-за внутренней ошибки.",
        "retryable": False,
        "run_id": run.run_id,
        "state_version": None,
    }


def _assert_selected(
    journal: list[Call], context: RecordingContext, handler: RecordingHandler,
    command: Command, snapshot: SessionSnapshot, run: RunContext,
) -> None:
    assert [call.method for call in journal] == ["load", "handle"]
    loaded, handled = journal
    assert loaded.target is context
    assert loaded.args == (SESSION_ID,)
    assert handled.target is handler
    assert len(handled.args) == 3
    assert handled.args[0] is command
    assert handled.args[1] is snapshot.state
    assert handled.args[2] is run


def _assert_input_required(
    result: object, handler: RecordingHandler, snapshot: SessionSnapshot, run: RunContext,
) -> None:
    assert isinstance(result, ApplicationInputRequired)
    assert isinstance(handler.result, InputRequired)
    assert result.issues == handler.result.issues
    assert result.state_version == snapshot.state.state_version
    assert result.run_id == run.run_id


def _fields(record: logging.LogRecord) -> dict[str, object]:
    """Read the rendered JSON object, preserving strings as single values."""
    _, _, body = record.getMessage().partition(" ")
    assert len(record.getMessage().splitlines()) == 1
    return json.loads(body)


def test_execute_requires_run(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call],
) -> None:
    """run обязателен по сигнатуре: координатор не создаёт запасной контекст.

    Позитивная пара — test_exact_type_reaches_handler с явным run.
    Требования: R3.2, §1.3, FR-01; AC-1. Вызов без run ещё не начат.
    """
    orchestrator = _orchestrator(context, {RoutedCommand: handler})
    parameter = inspect.signature(orchestrator.execute).parameters["run"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        orchestrator.execute(RoutedCommand(), session_id=SESSION_ID)
    assert journal == []


async def test_unknown_command_returns_failure_before_load(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call], run: RunContext,
) -> None:
    """Неизвестная команда не читает сессию и не выбирает чужой Handler.

    Отсутствие сессии не должно маскировать ошибку конфигурации.
    Позитивная пара — test_exact_type_reaches_handler.
    Требования: R3.2, UC-11, FR-03–04; AC-4, routing-часть AC-5 и AC-26.
    """
    context.load_result = SessionAbsent(reason="not_found")
    orchestrator = _orchestrator(context, {RoutedCommand: handler})

    result = await orchestrator.execute(OtherCommand(), session_id=SESSION_ID, run=run)

    _assert_routing_failure(result, run)
    assert journal == []


async def test_subclass_without_exact_registration_is_rejected(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call], run: RunContext,
) -> None:
    """Подкласс без назначения не попадает к обработчику базового типа.

    Это обнаруживает isinstance/MRO fallback. Положительные пары:
    test_exact_type_reaches_handler и test_explicit_child_registration_selects_own_handler.
    Требования: R3.2, FR-03–04; AC-3–4, routing-часть AC-5.
    """
    orchestrator = _orchestrator(context, {RoutedCommand: handler})

    result = await orchestrator.execute(ChildCommand(), session_id=SESSION_ID, run=run)

    _assert_routing_failure(result, run)
    assert journal == []


async def test_registry_addition_does_not_change_existing_instance(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call], run: RunContext,
) -> None:
    """Добавление во внешний mapping не меняет уже созданный координатор.

    Позитивная пара — test_new_instance_accepts_added_type: новый экземпляр
    получает добавленное назначение. Здесь только отрицательная часть FR-05.
    Требования: R3.2, FR-05; AC-4 для отклонённой команды.
    """
    handlers = {RoutedCommand: handler}
    orchestrator = _orchestrator(context, handlers)
    handlers[OtherCommand] = RecordingHandler(journal, result=handler.result)

    result = await orchestrator.execute(OtherCommand(), session_id=SESSION_ID, run=run)

    _assert_routing_failure(result, run)
    assert journal == []


async def test_exact_type_reaches_handler(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call],
    snapshot: SessionSnapshot, run: RunContext,
) -> None:
    """Зарегистрированная команда доходит до своего Handler после load.

    Позитивный контроль unknown/subclass отказов: запреты не должны
    достигаться полным отключением обработки. Готовность после 4.2/5.2.
    Требования: R3.2, FR-02–04, FR-06–08; AC-2–3, часть AC-5 и AC-26.
    """
    command = RoutedCommand()
    orchestrator = _orchestrator(context, {RoutedCommand: handler})

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    _assert_selected(journal, context, handler, command, snapshot, run)
    _assert_input_required(result, handler, snapshot, run)


@pytest.mark.parametrize("command_type", [RoutedCommand, ChildCommand], ids=["base", "child"])
async def test_explicit_child_registration_selects_own_handler(
    command_type: type[Command], context: RecordingContext, handler: RecordingHandler,
    journal: list[Call], snapshot: SessionSnapshot, run: RunContext,
) -> None:
    """Оба явно зарегистрированных типа выбирают собственный Handler.

    Обнаруживает запрет всех дочерних команд и выбор первого подходящего
    базового Handler. Пара к test_subclass_without_exact_registration_is_rejected.
    Требования: R3.2, FR-02, FR-04, FR-06–08; AC-2–3, часть AC-5. После 5.2.
    """
    child_handler = RecordingHandler(
        journal, result=InputRequired(issues=(Issue(field="birth_time", code="MISSING"),)),
    )
    handlers = {RoutedCommand: handler, ChildCommand: child_handler}
    selected = handlers[command_type]
    command = command_type()
    orchestrator = _orchestrator(context, handlers)

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    _assert_selected(journal, context, selected, command, snapshot, run)
    _assert_input_required(result, selected, snapshot, run)


async def test_external_mapping_removal_keeps_original_handler(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call],
    snapshot: SessionSnapshot, run: RunContext,
) -> None:
    """Удаление внешнего назначения не отключает ранее принятую команду.

    Положительный вызов исходного Handler доказывает защитную копию состава
    реестра; приватное представление не проверяется. Готовность после 5.2.
    Требования: R3.2, FR-05; вспомогательный контроль AC-3 и части AC-5.
    """
    handlers = {RoutedCommand: handler}
    orchestrator = _orchestrator(context, handlers)
    del handlers[RoutedCommand]
    command = RoutedCommand()

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    _assert_selected(journal, context, handler, command, snapshot, run)
    _assert_input_required(result, handler, snapshot, run)


async def test_external_mapping_replacement_keeps_original_handler(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call],
    snapshot: SessionSnapshot, run: RunContext,
) -> None:
    """Замена во внешнем mapping не перенаправляет запрос другому Handler.

    Журнал подтверждает вызов исходного объекта и отсутствие вызова нового,
    без требования глубоко копировать Handler. Готовность после 5.2.
    Требования: R3.2, FR-05; вспомогательный контроль AC-3 и части AC-5.
    """
    handlers = {RoutedCommand: handler}
    orchestrator = _orchestrator(context, handlers)
    replacement = RecordingHandler(
        journal, result=InputRequired(issues=(Issue(field="birth_date", code="INVALID"),)),
    )
    handlers[RoutedCommand] = replacement
    command = RoutedCommand()

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    _assert_selected(journal, context, handler, command, snapshot, run)
    _assert_input_required(result, handler, snapshot, run)
    assert all(call.target is not replacement for call in journal)


async def test_new_instance_accepts_added_type(
    context: RecordingContext, handler: RecordingHandler, journal: list[Call],
    snapshot: SessionSnapshot, run: RunContext,
) -> None:
    """Новый координатор принимает назначение из обновлённого mapping.

    Пара к test_registry_addition_does_not_change_existing_instance исключает
    ложный успех при полном игнорировании реестра. Готовность после 5.2.
    Требования: R3.2, FR-04–05; положительный контроль AC-3.
    """
    handlers = {RoutedCommand: handler}
    _orchestrator(context, handlers)
    added = RecordingHandler(
        journal, result=InputRequired(issues=(Issue(field="birth_time", code="INVALID"),)),
    )
    handlers[OtherCommand] = added
    orchestrator = _orchestrator(context, handlers)
    command = OtherCommand()

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    _assert_selected(journal, context, added, command, snapshot, run)
    _assert_input_required(result, added, snapshot, run)


async def test_known_command_completes_with_commit(
    context: RecordingContext, journal: list[Call], snapshot: SessionSnapshot, run: RunContext,
) -> None:
    """Известная команда проходит load, Handler и save до успешного ответа.

    Это полный положительный unit-контроль routing после 6.4; настоящий CAS,
    запись в хранилище и расчётный движок не исполняются.
    Требования: R3.2, §1.4, FR-02–08, FR-11; AC-3, AC-5, часть AC-10 и AC-26.
    """
    from tests.fixtures.calculation import artifact, chart_spec, resolved_birth_data

    spec, fixture_birth = chart_spec(), resolved_birth_data()
    resolved = ResolvedBirthData.model_validate({
        **fixture_birth.model_dump(),
        "utc_datetime": fixture_birth.utc_datetime.replace(second=0, microsecond=0),
    })
    local_birth = resolved.utc_datetime + timedelta(seconds=resolved.utc_offset_seconds)
    birth_input = BirthInput(
        birth_date=local_birth.date(), birth_time=local_birth.time().replace(tzinfo=None),
        place_id="moscow-ru",
    )
    command = BuildNatalCommand(birth_input=birth_input)
    outcome = BuildNatalSuccess(
        artifact=artifact(spec=spec, resolved=resolved),
        delta=StateDelta(
            birth_input=birth_input, birth_resolved=resolved, base_chart_spec=spec,
        ),
    )
    handler = RecordingHandler(journal, result=outcome)
    committed = Committed(state_version=snapshot.state.state_version + 1)
    context.save_result = committed
    orchestrator = _orchestrator(context, {BuildNatalCommand: handler})

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)

    assert [call.method for call in journal] == ["load", "handle", "save"]
    _assert_selected(journal[:2], context, handler, command, snapshot, run)
    saved = journal[2]
    assert saved.target is context
    assert len(saved.args) == 3
    assert saved.args[:2] == (SESSION_ID, snapshot.state.state_version)
    assert saved.args[2] is outcome.delta
    assert isinstance(result, ApplicationCommitted)
    assert result.state_version == committed.state_version
    assert result.artifact == outcome.artifact
    assert result.run_id == run.run_id


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B], ids=["first-run", "second-run"])
async def test_unknown_command_logs_one_start_and_terminal_before_return(
    run_id: UUID, context: RecordingContext, handler: RecordingHandler,
    journal: list[Call], operation_records: pytest.LogCaptureFixture,
) -> None:
    """Отказ имеет один старт и terminal до возврата с исходным UUID.

    Два UUID исключают привязку к одному тестовому идентификатору. Позитивный
    контроль отсутствующих стадий — test_known_command_completes_with_commit.
    Требования: R3.2, FR-26, §11.5, §12; routing-часть AC-26 и AC-29.
    Проверяет только routing failure, не сквозную наблюдаемость всех веток.
    """
    run = RunContext(run_id=run_id, started_at=STARTED_AT)
    command = OtherCommand()
    orchestrator = _orchestrator(context, {RoutedCommand: handler})

    result = await orchestrator.execute(command, session_id=SESSION_ID, run=run)
    # Inspect immediately on return, without yielding to let deferred logging run.
    records = [
        record for record in operation_records.records
        if record.name == LOGGER_NAME
        and record.getMessage().partition(" ")[0] in LIFECYCLE_EVENTS
    ]

    _assert_routing_failure(result, run)
    assert journal == []
    assert [record.getMessage().partition(" ")[0] for record in records] == [
        "application_operation_started", "application_operation_finished",
    ]
    started, finished = records
    assert started.levelno == logging.INFO
    assert finished.levelno == logging.WARNING
    start_fields, terminal = _fields(started), _fields(finished)
    assert start_fields["command_type"] == type(command).__name__
    assert UUID(str(start_fields["run_id"])) == run.run_id == result.run_id
    assert UUID(str(terminal["run_id"])) == run.run_id
    for field in (
        "orch_status", "handler_status", "context_status", "code", "detail_code", "state_version",
    ):
        assert terminal[field] == getattr(result, field)
    assert terminal["terminal_kind"] == "result"
    assert terminal["commit_attempts"] == 0
    assert terminal["commit_error_codes"] == []
    assert terminal["delivery_cancelled"] is False
    for field in ("load_duration_ms", "handler_duration_ms", "commit_duration_ms"):
        assert terminal[field] is None
