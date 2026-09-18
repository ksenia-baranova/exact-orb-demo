"""R3.2 FR-26 / section 11.5: lifecycle records and execute ordering."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
import inspect
import json
import logging
import math
from uuid import UUID

import pytest
from pydantic import TypeAdapter

import exact_orb.application.operation_logging as operation_logging
import exact_orb.application.orchestrator as orchestrator_module
from exact_orb.application.application_results import ApplicationResult
from exact_orb.application.commands import BuildNatalCommand, Command
from exact_orb.application.failure_policy import describe_failure
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.results import BuildNatalOutcome
from exact_orb.outcomes import CalculationFailed, InputRequired, Issue
from exact_orb.run_context import RunContext
from exact_orb.session.outcomes import Committed, SessionAbsent, StateCommitFailed
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import SessionState, StateDelta
from tests.application.orchestrator_fakes import (
    Call,
    LoadOutcome,
    RecordingContext,
    RecordingHandler,
    SaveOutcome,
)
from tests.application.test_orchestrator_commit import SESSION_ID, make_case
from tests.fixtures.calculation import artifact
from tests.fixtures.telemetry import FORBIDDEN_PAYLOAD, RUN_ID, RUN_ID_B, STARTED_AT


pytestmark = pytest.mark.no_ephemeris_autoinit
LOGGER_NAME = "exact_orb.application.operation_logging"


@pytest.fixture(autouse=True)
def _capture_operation_logging(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Capture real records without propagating into configured file handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    handlers = logger.handlers[:]
    propagate, level, disabled = logger.propagate, logger.level, logger.disabled
    try:
        caplog.set_level(logging.DEBUG, logger=LOGGER_NAME)
        logger.handlers = [caplog.handler]
        logger.propagate = False
        logger.disabled = False
        yield
    finally:
        logger.handlers = handlers
        logger.propagate = propagate
        logger.setLevel(level)
        logger.disabled = disabled


def _records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [record for record in caplog.records if record.name == LOGGER_NAME]


def _assert_record(
    caplog: pytest.LogCaptureFixture,
    event: str,
    level: int,
    expected: dict[str, object],
) -> None:
    records = _records(caplog)
    assert len(records) == 1
    record = records[0]
    assert record.levelno == level
    assert record.exc_info is None
    assert record.stack_info is None

    # Read the rendered message: fields hidden only in LogRecord.extra fail.
    message = record.getMessage()
    assert len(message.splitlines()) == 1
    name, body = message.split(maxsplit=1)
    assert name == event
    actual = json.loads(body)

    # Exact application field sets also exclude payloads and invented fields.
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        observed = actual[key]
        if value is None:
            assert observed is None, key
        elif key.endswith("duration_ms"):
            assert type(observed) in (int, float), key
            assert math.isfinite(observed) and observed >= 0, key
            assert observed == pytest.approx(value), key
        elif key == "commit_error_codes":
            assert isinstance(observed, (tuple, list)), key
            assert tuple(observed) == value, key
        elif isinstance(value, UUID):
            assert observed == str(value), key
        else:
            assert type(observed) is type(value), key
            assert observed == value, key


def _terminal_arguments(values: dict[str, object]) -> dict[str, object]:
    """Build a real result; the flat expected event fields remain independent."""
    fields = {name: values[name] for name in (
        "run_id", "orch_status", "handler_status", "context_status", "code",
        "detail_code", "state_version",
    )}
    code = fields["code"]
    if code == "OK":
        fields.update(artifact=artifact(), user_message=None, retryable=False)
    else:
        kinds = {
            "INPUT_REQUIRED": "input_required", "RESULT_SUPERSEDED": "superseded",
            "STATE_COMMIT_FAILED": "state_commit_failed", "STATE_READ_FAILED": "state_read_failed",
            "SESSION_EXPIRED": "session_absent", "SESSION_NOT_FOUND": "session_absent",
            "SESSION_LOST_DURING_OPERATION": "session_absent",
            "HANDLER_NOT_REGISTERED": "handler_not_registered", "INTERNAL_FAILURE": "internal_failure",
            "CALCULATION_FAILED": "calculation_failed", "RESOLUTION_UNAVAILABLE": "resolution_unavailable",
        }
        kind = kinds[code]
        arguments = {"kind": kind, "error_code": fields["detail_code"]}
        if kind == "session_absent":
            fields["reason"] = "not_found" if code == "SESSION_NOT_FOUND" else "expired"
            arguments.update(
                reason=fields["reason"],
                stage="load" if fields["handler_status"] == "NOT_STARTED" else "commit",
            )
        if kind == "resolution_unavailable":
            arguments["retryable"] = True
        reaction = describe_failure(**arguments)
        fields.update(user_message=reaction.user_message, retryable=reaction.retryable)
        if kind == "input_required":
            fields["issues"] = (Issue(field="date", code="MISSING"),)
    result = TypeAdapter(ApplicationResult).validate_python(fields)
    return {"result": result, **{name: values[name] for name in (
        "load_duration_ms", "handler_duration_ms", "commit_duration_ms",
        "commit_attempts", "commit_error_codes", "delivery_cancelled",
    )}}


def _result_arguments(**overrides: object) -> dict[str, object]:
    """A consistent committed result, with explicit per-scenario overrides."""
    return {
        "run_id": RUN_ID,
        "orch_status": "SUCCESS",
        "handler_status": "SUCCESS",
        "context_status": "COMMITTED",
        "code": "OK",
        "detail_code": None,
        "state_version": 4,
        "load_duration_ms": 0.0,
        "handler_duration_ms": 1.25,
        "commit_duration_ms": 2.5,
        "commit_attempts": 1,
        "commit_error_codes": (),
        "delivery_cancelled": False,
        **overrides,
    }


@pytest.mark.parametrize("function_name", [
    "log_operation_started", "log_stage_finished", "log_commit_attempt_finished",
    "log_operation_finished", "log_operation_cancelled",
])
def test_logging_api_accepts_only_explicit_keyword_arguments(function_name: str) -> None:
    """Карточки 1.3–1.4; R3.2 FR-27, §11.5: явные именованные аргументы.

    Проверяет форму API; отсутствие лишних полей записи проверяется отдельно.
    """
    parameters = inspect.signature(getattr(operation_logging, function_name)).parameters
    assert parameters
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters.values())


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B])
@pytest.mark.parametrize("command_type", ["BuildNatalCommand", "ExampleCommand"])
def test_started_records_command_type_and_run_id_at_info(
    caplog: pytest.LogCaptureFixture, run_id: UUID, command_type: str
) -> None:
    """R3.2 FR-26–27, §11.5; AC-26/29/33 частично: формат начала операции.

    Проверяет run_id, поля и INFO одного вызова, не число событий на execute.
    """
    assert operation_logging.log_operation_started(
        run_id=run_id, command_type=command_type
    ) is None
    _assert_record(
        caplog, "application_operation_started", logging.INFO,
        {"run_id": run_id, "command_type": command_type},
    )


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B])
@pytest.mark.parametrize(
    ("stage", "outcome", "state_version", "level"),
    [
        ("load", "loaded", 0, logging.DEBUG),
        ("load", "session_absent", None, logging.DEBUG),
        ("load", "state_read_failed", None, logging.DEBUG),
        ("handler", "success", 4, logging.DEBUG),
        ("handler", "input_required", 0, logging.DEBUG),
        ("handler", "resolution_unavailable", 4, logging.DEBUG),
        ("handler", "calculation_failed", 4, logging.DEBUG),
        ("load", "invalid_outcome", None, logging.WARNING),
        ("load", "unexpected_failure", None, logging.WARNING),
        ("handler", "invalid_outcome", 4, logging.WARNING),
        ("handler", "unexpected_failure", 4, logging.WARNING),
    ],
)
def test_stage_records_typed_and_unexpected_outcomes(
    caplog: pytest.LogCaptureFixture,
    run_id: UUID,
    stage: str,
    outcome: str,
    state_version: int | None,
    level: int,
) -> None:
    """R3.2 FR-26, §11.5; AC-26/30 частично: поля и уровни load/Handler.

    Проверяет известную версию, включая 0; завершение реальной стадии не моделирует.
    """
    expected = {
        "run_id": run_id, "stage": stage, "outcome": outcome, "duration_ms": 1.25,
    }
    assert operation_logging.log_stage_finished(
        **expected, state_version=state_version
    ) is None
    if state_version is not None:
        expected["state_version"] = state_version
    _assert_record(caplog, "application_stage_finished", level, expected)


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B])
@pytest.mark.parametrize(
    ("attempt", "outcome", "detail_code", "state_version", "level"),
    [
        (1, "committed", None, 4, logging.DEBUG),
        (1, "already_applied", None, 0, logging.DEBUG),
        (1, "state_commit_failed", "STORE_WRITE_FAILED", None, logging.WARNING),
        (1, "unexpected_failure", "UNEXPECTED_EXCEPTION", None, logging.WARNING),
        (2, "committed", None, 4, logging.WARNING),
        (2, "already_applied", None, 0, logging.WARNING),
        (2, "superseded", None, 5, logging.WARNING),
        (2, "session_absent", None, None, logging.WARNING),
        (2, "state_commit_failed", "STORE_WRITE_FAILED", None, logging.WARNING),
        (2, "unexpected_failure", "UNEXPECTED_EXCEPTION", None, logging.WARNING),
    ],
)
def test_commit_attempt_fields_and_warning_for_every_second_attempt(
    caplog: pytest.LogCaptureFixture,
    run_id: UUID,
    attempt: int,
    outcome: str,
    detail_code: str | None,
    state_version: int | None,
    level: int,
) -> None:
    """R3.2 FR-26, §11.5; AC-26/31 частично: формат попытки сохранения.

    Проверяет номер, WARNING повторной попытки и поля, не разрешение retry или save.
    """
    expected = {
        "run_id": run_id, "attempt": attempt, "outcome": outcome,
        "detail_code": detail_code, "duration_ms": 2.5,
    }
    assert operation_logging.log_commit_attempt_finished(
        **expected, state_version=state_version
    ) is None
    if state_version is not None:
        expected["state_version"] = state_version
    _assert_record(caplog, "application_commit_attempt_finished", level, expected)


@pytest.mark.parametrize("duration_ms", [0.0, 1.25, 2.5])
@pytest.mark.parametrize(
    ("function_name", "event", "arguments"),
    [
        ("log_stage_finished", "application_stage_finished",
         {"stage": "load", "outcome": "state_read_failed"}),
        ("log_commit_attempt_finished", "application_commit_attempt_finished",
         {"attempt": 1, "outcome": "state_commit_failed", "detail_code": "STORE_WRITE_FAILED"}),
    ],
)
def test_duration_values_and_default_omission_of_unknown_version(
    caplog: pytest.LogCaptureFixture,
    duration_ms: float,
    function_name: str,
    event: str,
    arguments: dict[str, object],
) -> None:
    """R3.2 FR-26, §11.5: передача длительности и отсутствие неизвестной версии.

    Проверяет готовые допустимые значения; измерение времени остаётся в execute.
    """
    values = {"run_id": RUN_ID, "duration_ms": duration_ms, **arguments}
    assert getattr(operation_logging, function_name)(**values) is None
    level = logging.DEBUG if function_name == "log_stage_finished" else logging.WARNING
    _assert_record(caplog, event, level, values)


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B])
@pytest.mark.parametrize(
    ("overrides", "level"),
    [
        pytest.param({}, logging.INFO, id="committed"),
        pytest.param(
            {"orch_status": "INPUT_REQUIRED", "handler_status": "INPUT_REQUIRED",
             "context_status": "LOADED", "code": "INPUT_REQUIRED", "state_version": 0,
             "commit_attempts": 0, "commit_duration_ms": None},
            logging.INFO, id="input-required",
        ),
        pytest.param(
            {"orch_status": "SUPERSEDED", "context_status": "SUPERSEDED",
             "code": "RESULT_SUPERSEDED", "state_version": 5},
            logging.INFO, id="superseded",
        ),
        pytest.param(
            {"orch_status": "SESSION_ABSENT", "handler_status": "NOT_STARTED",
             "context_status": "SESSION_ABSENT", "code": "SESSION_EXPIRED",
             "state_version": None, "handler_duration_ms": None,
             "commit_attempts": 0, "commit_duration_ms": None},
            logging.INFO, id="session-absent",
        ),
        pytest.param(
            {"orch_status": "FAILURE", "context_status": "COMMIT_FAILED",
             "code": "STATE_COMMIT_FAILED", "detail_code": "STORE_WRITE_FAILED",
             "state_version": None, "commit_error_codes": ("STORE_WRITE_FAILED",)},
            logging.WARNING, id="commit-failed",
        ),
    ],
)
def test_result_terminal_fields_and_levels_for_consistent_statuses(
    caplog: pytest.LogCaptureFixture,
    run_id: UUID,
    overrides: dict[str, object],
    level: int,
) -> None:
    """R3.2 FR-26, §11.5; AC-26/29 частично: итоговая запись с результатом.

    Проверяет поля, run_id и уровень, не валидацию модели и не порядок финализации.
    """
    arguments = _result_arguments(run_id=run_id, **overrides)
    assert operation_logging.log_operation_finished(**_terminal_arguments(arguments)) is None
    _assert_record(
        caplog, "application_operation_finished", level,
        {"terminal_kind": "result", **arguments},
    )


@pytest.mark.parametrize(
    ("error_codes", "context_status", "code", "detail_code", "state_version", "level"),
    [
        pytest.param(
            ("WRITE_ACK_LOST",), "ALREADY_APPLIED", "OK", None, 4,
            logging.INFO, id="retry-succeeded",
        ),
        pytest.param(
            ("WRITE_ACK_LOST", "STORE_UNAVAILABLE"), "COMMIT_FAILED",
            "STATE_COMMIT_FAILED", "STORE_UNAVAILABLE", None,
            logging.WARNING, id="two-different-errors",
        ),
        pytest.param(
            ("STORE_UNAVAILABLE", "STORE_UNAVAILABLE"), "COMMIT_FAILED",
            "STATE_COMMIT_FAILED", "STORE_UNAVAILABLE", None,
            logging.WARNING, id="duplicate-errors-preserved",
        ),
    ],
)
def test_result_preserves_retry_history_and_supplied_total_duration(
    caplog: pytest.LogCaptureFixture,
    error_codes: tuple[str, ...],
    context_status: str,
    code: str,
    detail_code: str | None,
    state_version: int | None,
    level: int,
) -> None:
    """R3.2 FR-26, §11.5: сохранение порядка ошибок и готовой суммы длительностей.

    Повторяющиеся коды не теряются; накопление истории и вычисление суммы не проверяются.
    """
    arguments = _result_arguments(
        orch_status="SUCCESS" if code == "OK" else "FAILURE",
        context_status=context_status, code=code, detail_code=detail_code,
        state_version=state_version, commit_attempts=2,
        commit_error_codes=error_codes, commit_duration_ms=3.75,
    )
    assert operation_logging.log_operation_finished(**_terminal_arguments(arguments)) is None
    _assert_record(
        caplog, "application_operation_finished", level,
        {"terminal_kind": "result", **arguments},
    )


@pytest.mark.parametrize("delivery_cancelled", [False, True])
def test_delivery_cancellation_keeps_successful_result_terminal(
    caplog: pytest.LogCaptureFixture, delivery_cancelled: bool
) -> None:
    """R3.2 FR-26, §11.5: отменённая доставка сохраняет вид и статусы результата.

    Проверяет переданный флаг; shield и проброс CancelledError здесь не выполняются.
    """
    arguments = _result_arguments(delivery_cancelled=delivery_cancelled)
    assert operation_logging.log_operation_finished(**_terminal_arguments(arguments)) is None
    _assert_record(
        caplog, "application_operation_finished", logging.INFO,
        {"terminal_kind": "result", **arguments},
    )


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B])
@pytest.mark.parametrize(
    ("cancelled_stage", "load_duration_ms"), [("load", None), ("handler", 1.25)]
)
def test_cancelled_terminal_omits_result_fields_with_result_positive_control(
    caplog: pytest.LogCaptureFixture,
    run_id: UUID,
    cancelled_stage: str,
    load_duration_ms: float | None,
) -> None:
    """R3.2 FR-26, §11.5; AC-26/29 частично: отдельная форма отмены до commit.

    Проверяет отсутствие полей результата с позитивным контролем, не реальную отмену.
    """
    result_arguments = _result_arguments(run_id=run_id)
    assert operation_logging.log_operation_finished(**_terminal_arguments(result_arguments)) is None
    _assert_record(
        caplog, "application_operation_finished", logging.INFO,
        {"terminal_kind": "result", **result_arguments},
    )
    caplog.clear()

    cancelled_arguments = {
        "run_id": run_id, "cancelled_stage": cancelled_stage,
        "load_duration_ms": load_duration_ms, "handler_duration_ms": None,
    }
    assert operation_logging.log_operation_cancelled(**cancelled_arguments) is None
    _assert_record(
        caplog, "application_operation_finished", logging.INFO,
        {"terminal_kind": "cancelled", "commit_attempts": 0, **cancelled_arguments},
    )


@pytest.mark.parametrize("forbidden_field", [
    "session_id", "birth_input", "command", "delta", "artifact", "payload",
])
@pytest.mark.parametrize(
    ("function_name", "arguments"),
    [
        ("log_operation_started", {"command_type": "BuildNatalCommand"}),
        ("log_stage_finished", {"stage": "handler", "outcome": "success", "duration_ms": 1.25}),
        ("log_commit_attempt_finished",
         {"attempt": 1, "outcome": "committed", "detail_code": None, "duration_ms": 2.5,
          "state_version": 1}),
        ("log_operation_finished", _result_arguments()),
        ("log_operation_cancelled",
         {"cancelled_stage": "load", "load_duration_ms": None, "handler_duration_ms": None}),
    ],
)
def test_payload_keywords_are_rejected_after_valid_call_positive_control(
    caplog: pytest.LogCaptureFixture,
    forbidden_field: str,
    function_name: str,
    arguments: dict[str, object],
) -> None:
    """R3.2 FR-27, §11.5; AC-33 частично: API отклоняет payload-аргументы.

    TypeError не создаёт запись; проверка не доказывает отсутствие PII во всём flow.
    """
    writer = getattr(operation_logging, function_name)
    values = (
        _terminal_arguments(arguments) if function_name == "log_operation_finished"
        else {"run_id": RUN_ID, **arguments}
    )
    assert writer(**values) is None
    assert len(_records(caplog)) == 1
    caplog.clear()

    with pytest.raises(TypeError):
        writer(**values, **{forbidden_field: FORBIDDEN_PAYLOAD})
    assert _records(caplog) == []


def _valid_writer_arguments(function_name: str) -> dict[str, object]:
    if function_name == "log_operation_finished":
        return _terminal_arguments(_result_arguments())
    if function_name == "log_stage_finished":
        return {"run_id": RUN_ID, "stage": "handler", "outcome": "success", "duration_ms": 1.0}
    if function_name == "log_commit_attempt_finished":
        return {"run_id": RUN_ID, "attempt": 1, "outcome": "committed",
                "detail_code": None, "duration_ms": 1.0, "state_version": 1}
    return {"run_id": RUN_ID, "cancelled_stage": "handler",
            "load_duration_ms": 1.0, "handler_duration_ms": None}


@pytest.mark.parametrize(("function_name", "field"), [
    ("log_stage_finished", "duration_ms"),
    ("log_commit_attempt_finished", "duration_ms"),
    ("log_operation_finished", "load_duration_ms"),
    ("log_operation_finished", "handler_duration_ms"),
    ("log_operation_finished", "commit_duration_ms"),
    ("log_operation_cancelled", "load_duration_ms"),
    ("log_operation_cancelled", "handler_duration_ms"),
])
@pytest.mark.parametrize("invalid", [-5.0, float("nan"), float("inf"), -float("inf"), True])
def test_invalid_durations_are_rejected_before_logging(
    caplog: pytest.LogCaptureFixture, function_name: str, field: str, invalid: object,
) -> None:
    """3.R2; §11.5: запрещённая длительность не попадает в поток метрик."""
    writer = getattr(operation_logging, function_name)
    arguments = _valid_writer_arguments(function_name)
    writer(**arguments)
    assert len(_records(caplog)) == 1
    caplog.clear()
    with pytest.raises(operation_logging.LifecycleEventError):
        writer(**{**arguments, field: invalid})
    assert _records(caplog) == []


@pytest.mark.parametrize(("function_name", "field", "invalid"), [
    ("log_commit_attempt_finished", "attempt", value)
    for value in (0, 3, -1, True, "1", 1.0)
] + [
    ("log_operation_finished", "commit_attempts", value)
    for value in (-1, 3, True, "1", 1.0)
])
def test_attempt_numbers_are_checked_at_runtime(
    caplog: pytest.LogCaptureFixture, function_name: str, field: str, invalid: object,
) -> None:
    """3.R2: Literal ограничивает не только аннотацию, но и реальные записи."""
    writer = getattr(operation_logging, function_name)
    arguments = _valid_writer_arguments(function_name)
    writer(**arguments)
    assert len(_records(caplog)) == 1
    caplog.clear()
    with pytest.raises(operation_logging.LifecycleEventError):
        writer(**{**arguments, field: invalid})
    assert _records(caplog) == []


@pytest.mark.parametrize(("outcome", "valid", "invalid"), [
    ("committed", 1, value) for value in (None, 0, -1, True, "1", 1.0)
] + [
    ("already_applied", 0, None), ("already_applied", 0, -1),
    ("superseded", 0, None), ("superseded", 0, -1),
    ("state_commit_failed", None, 0), ("unexpected_failure", None, 0),
    ("session_absent", None, 0),
])
def test_attempt_version_matches_its_outcome(
    caplog: pytest.LogCaptureFixture, outcome: str, valid: int | None, invalid: object,
) -> None:
    """3.R2; §9/11.5: committed не имеет версии 0, отказ не выдумывает версию."""
    arguments = {**_valid_writer_arguments("log_commit_attempt_finished"),
                 "outcome": outcome, "state_version": valid}
    operation_logging.log_commit_attempt_finished(**arguments)
    assert len(_records(caplog)) == 1
    caplog.clear()
    with pytest.raises(operation_logging.LifecycleEventError):
        operation_logging.log_commit_attempt_finished(**{**arguments, "state_version": invalid})
    assert _records(caplog) == []


@pytest.mark.parametrize("kind", ["started", "stage", "attempt", "result"])
def test_strings_cannot_inject_fields_or_physical_records(
    caplog: pytest.LogCaptureFixture, kind: str,
) -> None:
    """3.R2: JSON сохраняет открытую строку целиком, включая поддельные поля/события."""
    text = 'SYNTHETIC state_version=999\nFAKE application_operation_finished run_id=x\r\t"\\\u2028'
    if kind == "started":
        expected = {"run_id": RUN_ID, "command_type": text}
        operation_logging.log_operation_started(**expected)
        _assert_record(caplog, "application_operation_started", logging.INFO, expected)
    elif kind == "stage":
        expected = {"run_id": RUN_ID, "stage": "handler", "outcome": text, "duration_ms": 1.0}
        operation_logging.log_stage_finished(**expected)
        _assert_record(caplog, "application_stage_finished", logging.DEBUG, expected)
    elif kind == "attempt":
        expected = {"run_id": RUN_ID, "attempt": 1, "outcome": "state_commit_failed",
                    "detail_code": text, "duration_ms": 1.0}
        operation_logging.log_commit_attempt_finished(**expected)
        _assert_record(caplog, "application_commit_attempt_finished", logging.WARNING, expected)
    else:
        expected = _result_arguments(
            orch_status="FAILURE", context_status="COMMIT_FAILED", code="STATE_COMMIT_FAILED",
            detail_code=text, state_version=None, commit_error_codes=(text,),
        )
        operation_logging.log_operation_finished(**_terminal_arguments(expected))
        _assert_record(caplog, "application_operation_finished", logging.WARNING,
                       {"terminal_kind": "result", **expected})


@pytest.mark.parametrize("field", [
    "run_id", "orch_status", "handler_status", "context_status", "code", "detail_code", "state_version",
])
def test_terminal_cannot_override_the_returned_result(
    caplog: pytest.LogCaptureFixture, field: str,
) -> None:
    """3.R2: отдельный аргумент не может разойтись с уже созданным ответом."""
    expected = _result_arguments()
    arguments = _terminal_arguments(expected)
    operation_logging.log_operation_finished(**arguments)
    _assert_record(caplog, "application_operation_finished", logging.INFO,
                   {"terminal_kind": "result", **expected})
    caplog.clear()
    with pytest.raises(TypeError):
        operation_logging.log_operation_finished(**arguments, **{field: "forged"})
    assert _records(caplog) == []


_START = "application_operation_started"
_STAGE = "application_stage_finished"
_ATTEMPT = "application_commit_attempt_finished"
_FINISH = "application_operation_finished"


@contextmanager
def _observe_execute(timeline: list[object]) -> Iterator[None]:
    """Put real lifecycle records beside dependency and caller markers."""
    logger = logging.getLogger(LOGGER_NAME)

    class Observer(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            timeline.append(record)

    observer = Observer()
    logger.addHandler(observer)
    try:
        yield
    finally:
        logger.removeHandler(observer)
        observer.close()


class _TraceContext(RecordingContext):
    def __init__(
        self, journal: list[Call], timeline: list[object], *,
        load_result: LoadOutcome, save_outcomes: tuple[SaveOutcome, ...],
        block_load: bool = False,
    ) -> None:
        super().__init__(journal, load_result=load_result)
        self.timeline = timeline
        self.save_outcomes = save_outcomes
        self.load_entered = asyncio.Event()
        self.release_load = asyncio.Event()
        if not block_load:
            self.release_load.set()

    async def load(self, session_id: str) -> LoadOutcome:
        self.journal.append(Call(self, "load", (session_id,)))
        self.timeline.append("load_entered")
        self.load_entered.set()
        try:
            await self.release_load.wait()
        except asyncio.CancelledError:
            self.timeline.append("load_cancelled")
            raise
        self.timeline.append("load_done")
        return self.load_result

    async def save(
        self, session_id: str, expected_state_version: int, delta: StateDelta,
    ) -> SaveOutcome:
        attempt = sum(call.method == "save" for call in self.journal) + 1
        self.journal.append(Call(self, "save", (session_id, expected_state_version, delta)))
        self.timeline.append(f"save_{attempt}_entered")
        outcome = self.save_outcomes[attempt - 1]
        self.timeline.append(f"save_{attempt}_done")
        return outcome


class _TraceHandler(RecordingHandler):
    def __init__(
        self, journal: list[Call], timeline: list[object], *,
        result: BuildNatalOutcome, block_handle: bool = False,
    ) -> None:
        super().__init__(journal, result=result)
        self.timeline = timeline
        self.handle_entered = asyncio.Event()
        self.release_handle = asyncio.Event()
        if not block_handle:
            self.release_handle.set()

    async def handle(
        self, command: Command, state: SessionState, run: RunContext,
    ) -> BuildNatalOutcome:
        self.journal.append(Call(self, "handle", (command, state, run)))
        self.timeline.append("handler_entered")
        self.handle_entered.set()
        try:
            await self.release_handle.wait()
        except asyncio.CancelledError:
            self.timeline.append("handler_cancelled")
            raise
        self.timeline.append("handler_done")
        return self.result


@dataclass
class _TraceFlow:
    command: BuildNatalCommand
    run: RunContext
    context: _TraceContext
    handler: _TraceHandler
    orchestrator: ApplicationOrchestrator
    journal: list[Call]


def _make_execute_flow(scenario: str, timeline: list[object]) -> _TraceFlow:
    prepared = make_case(loaded_version=7, committed_version=19)
    journal: list[Call] = []
    load_result: LoadOutcome = (
        SessionAbsent(reason="expired") if scenario == "load_absent" else prepared.snapshot
    )
    handler_result: BuildNatalOutcome = (
        InputRequired(issues=(Issue(field="date", code="MISSING"),))
        if scenario == "handler_input" else prepared.outcome
    )
    if scenario == "unknown_calculation":
        handler_result = CalculationFailed(error_code="SYNTHETIC_UNKNOWN_CALCULATION_CODE")
    save_outcomes: tuple[SaveOutcome, ...] = {
        "commit": (Committed(state_version=19),),
        "commit_denied": (StateCommitFailed(error_code="UNCONFIRMED"),),
        "retry": (StateCommitFailed(error_code="UNCONFIRMED"), Committed(state_version=23)),
        "retry_double_failure": (
            StateCommitFailed(error_code="FIRST_WRITE_UNCONFIRMED"),
            StateCommitFailed(error_code="SECOND_WRITE_UNCONFIRMED"),
        ),
    }.get(scenario, ())
    context = _TraceContext(
        journal, timeline, load_result=load_result, save_outcomes=save_outcomes,
        block_load=scenario == "cancel_load",
    )
    handler = _TraceHandler(
        journal, timeline, result=handler_result,
        block_handle=scenario == "cancel_handler",
    )
    run = (
        RunContext(run_id=prepared.run.run_id, started_at=prepared.run.started_at,
                   deadline=STARTED_AT)
        if scenario == "commit_denied" else prepared.run
    )
    orchestrator = ApplicationOrchestrator(
        context=context,
        handlers={} if scenario == "routing" else {BuildNatalCommand: handler},
        clock=lambda: STARTED_AT,
    )
    return _TraceFlow(prepared.command, run, context, handler, orchestrator, journal)


async def _invoke_execute(flow: _TraceFlow, timeline: list[object]) -> ApplicationResult:
    try:
        result = await flow.orchestrator.execute(
            flow.command, session_id=SESSION_ID, run=flow.run,
        )
    except asyncio.CancelledError:
        timeline.append("caller_cancelled")
        raise
    timeline.append("caller_returned")
    return result


def _event(record: logging.LogRecord) -> tuple[str, dict[str, object]]:
    name, payload = record.getMessage().split(" ", 1)
    fields = json.loads(payload)
    assert isinstance(fields, dict)
    return name, fields


@pytest.mark.parametrize(
    ("scenario", "methods", "stages", "attempts", "code"),
    [
        ("routing", (), (), (), "HANDLER_NOT_REGISTERED"),
        ("load_absent", ("load",), ("load",), (), "SESSION_EXPIRED"),
        ("handler_input", ("load", "handle"), ("load", "handler"), (), "INPUT_REQUIRED"),
        ("commit", ("load", "handle", "save"), ("load", "handler"), (1,), "OK"),
        ("commit_denied", ("load", "handle", "save"),
         ("load", "handler"), (1,), "STATE_COMMIT_FAILED"),
        ("retry", ("load", "handle", "save", "save"),
         ("load", "handler"), (1, 2), "OK"),
    ],
    ids=["routing", "load_absent", "handler_input", "commit", "commit_denied", "retry"],
)
async def test_execute_debug_lifecycle_is_bounded_per_invocation(
    scenario: str, methods: tuple[str, ...], stages: tuple[str, ...],
    attempts: tuple[int, ...], code: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-26/29–32: two calls with the same run_id each own one full lifecycle."""
    segments: list[list[logging.LogRecord]] = []
    for _ in range(2):
        timeline: list[object] = []
        flow = _make_execute_flow(scenario, timeline)
        before = len(_records(caplog))
        with _observe_execute(timeline):
            result = await _invoke_execute(flow, timeline)
        segment = _records(caplog)[before:]
        segments.append(segment)
        events = [_event(record) for record in segment]
        names = [name for name, _ in events]
        assert names == [_START, *([_STAGE] * len(stages)),
                         *([_ATTEMPT] * len(attempts)), _FINISH]
        assert [call.method for call in flow.journal] == list(methods)
        assert result.run_id == RUN_ID_B and result.code == code
        assert all(fields["run_id"] == str(flow.run.run_id) for _, fields in events)
        assert [fields["stage"] for name, fields in events if name == _STAGE] == list(stages)
        assert [fields["attempt"] for name, fields in events if name == _ATTEMPT] == list(attempts)
        assert events[-1][1]["terminal_kind"] == "result"
        assert events[-1][1]["commit_attempts"] == len(attempts)
        assert events[-1][1]["code"] == result.code
        assert [item for item in timeline if isinstance(item, logging.LogRecord)] == segment
        assert timeline[0] is segment[0] and timeline[-1] == "caller_returned"
        assert timeline.index(segment[-1]) < timeline.index("caller_returned")
        for stage, record in zip(stages, segment[1:]):
            marker = "load_done" if stage == "load" else "handler_done"
            assert timeline.index(marker) < timeline.index(record)
        attempt_records = [record for record in segment if _event(record)[0] == _ATTEMPT]
        for number, record in zip(attempts, attempt_records):
            assert timeline.index(f"save_{number}_done") < timeline.index(record)
        if len(attempts) == 2:
            assert timeline.index(attempt_records[0]) < timeline.index("save_2_entered")
    assert _records(caplog) == segments[0] + segments[1]


@pytest.mark.parametrize("effective_level", [logging.DEBUG, logging.INFO], ids=["debug", "info"])
@pytest.mark.parametrize("stage", ["load", "handler"])
async def test_execute_cancelled_stage_has_no_completion_event(
    stage: str, effective_level: int, caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-29/30/32: only completed stages appear before caller sees cancellation."""
    timeline: list[object] = []
    flow = _make_execute_flow(f"cancel_{stage}", timeline)
    entered = flow.context.load_entered if stage == "load" else flow.handler.handle_entered
    before = len(_records(caplog))
    logger = logging.getLogger(LOGGER_NAME)
    original_level = logger.level
    try:
        logger.setLevel(effective_level)
        with _observe_execute(timeline):
            caller = asyncio.create_task(_invoke_execute(flow, timeline))
            waiter = asyncio.create_task(entered.wait())
            try:
                done, _ = await asyncio.wait(
                    {caller, waiter}, timeout=2, return_when=asyncio.FIRST_COMPLETED,
                )
                assert done, "execute did not enter the controlled stage"
                if caller in done:
                    await caller
                    pytest.fail("caller completed before the controlled stage")
                assert waiter in done and waiter.result() is True
                assert not caller.done()
                caller.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await asyncio.wait_for(caller, timeout=2)
            finally:
                flow.context.release_load.set()
                flow.handler.release_handle.set()
                if not waiter.done():
                    waiter.cancel()
                    with suppress(asyncio.CancelledError):
                        await waiter
                if not caller.done():
                    caller.cancel()
                    with suppress(asyncio.CancelledError):
                        await caller
    finally:
        logger.setLevel(original_level)
    segment = _records(caplog)[before:]
    events = [_event(record) for record in segment]
    assert [name for name, _ in events] == (
        [_START, _STAGE, _FINISH]
        if stage == "handler" and effective_level == logging.DEBUG
        else [_START, _FINISH]
    )
    assert [call.method for call in flow.journal] == (
        ["load"] if stage == "load" else ["load", "handle"]
    )
    assert [item for item in timeline if isinstance(item, logging.LogRecord)] == segment
    assert timeline[-1] == "caller_cancelled"
    assert timeline.index(segment[-1]) < timeline.index("caller_cancelled")
    assert events[-1][1]["terminal_kind"] == "cancelled"
    assert events[-1][1]["cancelled_stage"] == stage
    assert events[-1][1]["commit_attempts"] == 0
    assert all(fields["run_id"] == str(flow.run.run_id) for _, fields in events)
    if stage == "load":
        assert "load_done" not in timeline
        assert timeline.index("load_cancelled") < timeline.index(segment[-1])
    else:
        assert "load_done" in timeline and "handler_done" not in timeline
        assert timeline.index("load_done") < timeline.index(
            segment[1] if effective_level == logging.DEBUG else segment[-1]
        )
        assert timeline.index("handler_cancelled") < timeline.index(segment[-1])


@pytest.mark.parametrize(
    ("scenario", "names", "levels"),
    [
        ("routing", (_START, _FINISH), (logging.INFO, logging.WARNING)),
        ("commit", (_START, _FINISH), (logging.INFO, logging.INFO)),
        ("retry", (_START, _ATTEMPT, _ATTEMPT, _FINISH),
         (logging.INFO, logging.WARNING, logging.WARNING, logging.INFO)),
    ],
    ids=["routing", "commit", "retry"],
)
async def test_execute_effective_info_keeps_invocation_boundaries(
    scenario: str, names: tuple[str, ...], levels: tuple[int, ...],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-29/31/32: INFO keeps start/terminal, and visible WARN retries."""
    logger = logging.getLogger(LOGGER_NAME)
    original_level = logger.level
    timeline: list[object] = []
    flow = _make_execute_flow(scenario, timeline)
    before = len(_records(caplog))
    try:
        logger.setLevel(logging.INFO)
        with _observe_execute(timeline):
            result = await _invoke_execute(flow, timeline)
    finally:
        logger.setLevel(original_level)
    segment = _records(caplog)[before:]
    events = [_event(record) for record in segment]
    assert tuple(name for name, _ in events) == names
    assert tuple(record.levelno for record in segment) == levels
    assert sum(name == _START for name, _ in events) == 1
    assert sum(name == _FINISH for name, _ in events) == 1
    assert all(fields["run_id"] == str(flow.run.run_id) for _, fields in events)
    assert events[-1][1]["terminal_kind"] == "result"
    assert events[-1][1]["code"] == result.code
    assert [item for item in timeline if isinstance(item, logging.LogRecord)] == segment
    assert timeline[-1] == "caller_returned"
    assert timeline.index(segment[-1]) < timeline.index("caller_returned")
    expected_methods = {
        "routing": [],
        "commit": ["load", "handle", "save"],
        "retry": ["load", "handle", "save", "save"],
    }
    assert [call.method for call in flow.journal] == expected_methods[scenario]


class _DurationTicks:
    """Replace only the Orchestrator's duration source, never its deadline clock."""

    def __init__(self, ticks: tuple[float, ...]) -> None:
        self.ticks = ticks
        self.calls = 0

    def perf_counter(self) -> float:
        assert self.calls < len(self.ticks), "unexpected duration measurement"
        tick = self.ticks[self.calls]
        self.calls += 1
        return tick


def _install_duration_ticks(
    monkeypatch: pytest.MonkeyPatch, ticks: tuple[float, ...],
) -> _DurationTicks:
    counter = _DurationTicks(ticks)
    monkeypatch.setattr(orchestrator_module, "time", counter)
    return counter


def _assert_event_fields(
    record: logging.LogRecord, event: str, level: int,
    fields: dict[str, object],
) -> None:
    assert record.levelno == level
    assert record.exc_info is None and record.stack_info is None
    assert len(record.getMessage().splitlines()) == 1
    actual_event, actual_fields = _event(record)
    assert actual_event == event
    assert actual_fields.keys() == fields.keys()
    for key, expected in fields.items():
        actual = actual_fields[key]
        if key.endswith("duration_ms") and expected is not None:
            assert type(actual) in (int, float)
            assert math.isfinite(actual) and actual >= 0
            assert actual == pytest.approx(expected)
        else:
            assert actual == expected, key


@pytest.mark.parametrize(
    ("scenario", "ticks", "load_outcome", "handler_outcome", "attempt_outcome",
     "attempt_level", "attempt_version", "terminal_level", "error_codes"),
    [
        ("routing", (), None, None, None, None, None, logging.WARNING, ()),
        ("load_absent", (0.0, 0.004), "session_absent", None, None,
         None, None, logging.INFO, ()),
        ("handler_input", (0.0, 0.004, 0.010, 0.017), "loaded", "input_required",
         None, None, None, logging.INFO, ()),
        ("commit", (0.0, 0.004, 0.010, 0.017, 0.020, 0.031), "loaded", "success",
         "committed", logging.DEBUG, 19, logging.INFO, ()),
        ("commit_denied", (0.0, 0.004, 0.010, 0.017, 0.020, 0.031),
         "loaded", "success", "state_commit_failed", logging.WARNING, None,
         logging.WARNING, ("UNCONFIRMED",)),
    ],
    ids=["routing", "load_absent", "handler_input", "commit", "commit_denied"],
)
async def test_execute_projects_exact_fields_levels_and_measured_durations(
    scenario: str, ticks: tuple[float, ...], load_outcome: str | None,
    handler_outcome: str | None, attempt_outcome: str | None,
    attempt_level: int | None, attempt_version: int | None,
    terminal_level: int, error_codes: tuple[str, ...],
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-26/27: execute's real records reflect only completed work and result."""
    timeline: list[object] = []
    flow = _make_execute_flow(scenario, timeline)
    counter = _install_duration_ticks(monkeypatch, ticks)
    result = await _invoke_execute(flow, timeline)
    assert counter.calls == len(ticks)
    records = _records(caplog)
    index = 0
    _assert_event_fields(records[index], _START, logging.INFO, {
        "run_id": str(flow.run.run_id), "command_type": "BuildNatalCommand",
    })
    index += 1
    if load_outcome is not None:
        load_fields: dict[str, object] = {
            "run_id": str(flow.run.run_id), "stage": "load", "outcome": load_outcome,
            "duration_ms": 4.0,
        }
        if load_outcome == "loaded":
            load_fields["state_version"] = 7
        _assert_event_fields(records[index], _STAGE, logging.DEBUG, load_fields)
        index += 1
    if handler_outcome is not None:
        _assert_event_fields(records[index], _STAGE, logging.DEBUG, {
            "run_id": str(flow.run.run_id), "stage": "handler",
            "outcome": handler_outcome, "duration_ms": 7.0, "state_version": 7,
        })
        index += 1
    if attempt_outcome is not None:
        attempt_fields: dict[str, object] = {
            "run_id": str(flow.run.run_id), "attempt": 1,
            "outcome": attempt_outcome,
            "detail_code": error_codes[0] if error_codes else None,
            "duration_ms": 11.0,
        }
        if attempt_version is not None:
            attempt_fields["state_version"] = attempt_version
        assert attempt_level is not None
        _assert_event_fields(records[index], _ATTEMPT, attempt_level, attempt_fields)
        index += 1
    _assert_event_fields(records[index], _FINISH, terminal_level, {
        "run_id": str(flow.run.run_id), "terminal_kind": "result",
        "orch_status": result.orch_status,
        "handler_status": result.handler_status,
        "context_status": result.context_status,
        "code": result.code, "detail_code": result.detail_code,
        "state_version": result.state_version,
        "load_duration_ms": 4.0 if load_outcome is not None else None,
        "handler_duration_ms": 7.0 if handler_outcome is not None else None,
        "commit_duration_ms": 11.0 if attempt_outcome is not None else None,
        "commit_attempts": 1 if attempt_outcome is not None else 0,
        "commit_error_codes": list(error_codes), "delivery_cancelled": False,
    })
    assert len(records) == index + 1
    assert sum(call.method == "save" for call in flow.journal) == int(
        attempt_outcome is not None
    )


async def test_execute_preserves_distinct_commit_errors_and_sums_attempt_durations(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-31/32: two real saves retain distinct codes and measured times."""
    timeline: list[object] = []
    flow = _make_execute_flow("retry_double_failure", timeline)
    counter = _install_duration_ticks(
        monkeypatch, (0.0, 0.004, 0.010, 0.017, 0.020, 0.031, 0.040, 0.053),
    )
    result = await _invoke_execute(flow, timeline)
    assert counter.calls == 8
    assert [call.method for call in flow.journal] == ["load", "handle", "save", "save"]
    records = _records(caplog)
    assert len(records) == 6
    errors = ("FIRST_WRITE_UNCONFIRMED", "SECOND_WRITE_UNCONFIRMED")
    for index, (error, duration) in enumerate(zip(errors, (11.0, 13.0)), start=1):
        _assert_event_fields(records[index + 2], _ATTEMPT, logging.WARNING, {
            "run_id": str(flow.run.run_id), "attempt": index,
            "outcome": "state_commit_failed", "detail_code": error,
            "duration_ms": duration,
        })
    assert result.detail_code == errors[1]
    _assert_event_fields(records[-1], _FINISH, logging.WARNING, {
        "run_id": str(flow.run.run_id), "terminal_kind": "result",
        "orch_status": result.orch_status,
        "handler_status": result.handler_status,
        "context_status": result.context_status,
        "code": "STATE_COMMIT_FAILED", "detail_code": errors[1],
        "state_version": None, "load_duration_ms": 4.0,
        "handler_duration_ms": 7.0, "commit_duration_ms": 24.0,
        "commit_attempts": 2, "commit_error_codes": list(errors),
        "delivery_cancelled": False,
    })
    attempt_durations = [_event(record)[1]["duration_ms"] for record in records[3:5]]
    assert _event(records[-1])[1]["commit_duration_ms"] == pytest.approx(
        sum(attempt_durations)
    )


@pytest.mark.parametrize("stage", ["load", "handler"])
async def test_execute_cancelled_terminal_has_only_completed_durations(
    stage: str, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-26: interrupted stage has no duration or result fields."""
    timeline: list[object] = []
    flow = _make_execute_flow(f"cancel_{stage}", timeline)
    ticks = (0.0,) if stage == "load" else (0.0, 0.004, 0.010)
    counter = _install_duration_ticks(monkeypatch, ticks)
    caller = asyncio.create_task(_invoke_execute(flow, timeline))
    try:
        entered = flow.context.load_entered if stage == "load" else flow.handler.handle_entered
        await asyncio.wait_for(entered.wait(), timeout=2)
        caller.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(caller, timeout=2)
    finally:
        flow.context.release_load.set()
        flow.handler.release_handle.set()
    assert counter.calls == len(ticks)
    records = _records(caplog)
    assert len(records) == (2 if stage == "load" else 3)
    if stage == "handler":
        _assert_event_fields(records[1], _STAGE, logging.DEBUG, {
            "run_id": str(flow.run.run_id), "stage": "load",
            "outcome": "loaded", "duration_ms": 4.0, "state_version": 7,
        })
    _assert_event_fields(records[-1], _FINISH, logging.INFO, {
        "run_id": str(flow.run.run_id), "terminal_kind": "cancelled",
        "cancelled_stage": stage, "load_duration_ms": 4.0 if stage == "handler" else None,
        "handler_duration_ms": None, "commit_attempts": 0,
    })


class _SensitiveBuildNatalCommand(BuildNatalCommand):
    private_note: str


async def test_execute_compact_messages_exclude_real_input_and_session_payload(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-33: positive input/Handler/save controls guard the absence checks."""
    prepared = make_case(loaded_version=7, committed_version=19)
    command = _SensitiveBuildNatalCommand(
        birth_input=prepared.command.birth_input, private_note=FORBIDDEN_PAYLOAD,
    )
    journal: list[Call] = []
    timeline: list[object] = []
    context = _TraceContext(
        journal, timeline, load_result=prepared.snapshot,
        save_outcomes=(Committed(state_version=19),),
    )
    handler = _TraceHandler(journal, timeline, result=prepared.outcome)
    orchestrator = ApplicationOrchestrator(
        context=context, handlers={_SensitiveBuildNatalCommand: handler},
        clock=lambda: STARTED_AT,
    )
    result = await orchestrator.execute(command, session_id=SESSION_ID, run=prepared.run)
    assert result.code == "OK"
    assert [call.method for call in journal] == ["load", "handle", "save"]
    assert journal[1].args[0] is command
    assert journal[0].args[0] == journal[2].args[0] == SESSION_ID
    assert command.private_note == FORBIDDEN_PAYLOAD
    birth = command.birth_input
    payload_markers = (
        FORBIDDEN_PAYLOAD, SESSION_ID, birth.birth_date.isoformat(),
        birth.birth_time.isoformat(), birth.place_id,
    )
    assert all(marker for marker in payload_markers)
    assert all(marker in command.model_dump_json() for marker in payload_markers
               if marker != SESSION_ID)
    records = _records(caplog)
    assert [_event(record)[0] for record in records] == [
        _START, _STAGE, _STAGE, _ATTEMPT, _FINISH,
    ]
    for record in records:
        message = record.getMessage()
        fields = _event(record)[1]
        assert fields["run_id"] == str(prepared.run.run_id)
        assert all(marker not in message for marker in payload_markers)
        assert all(marker not in json.dumps(fields) for marker in payload_markers)


async def test_execute_unknown_calculation_code_warns_without_payload(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-21/25: fallback result and separate diagnostic WARN survive execute."""
    timeline: list[object] = []
    flow = _make_execute_flow("unknown_calculation", timeline)
    diagnostic_logger = logging.getLogger("exact_orb.application.orchestrator")
    result = await _invoke_execute(flow, timeline)
    records = _records(caplog)
    assert [record.levelno for record in records] == [
        logging.INFO, logging.DEBUG, logging.DEBUG, logging.WARNING,
    ]
    assert result.code == "CALCULATION_FAILED"
    assert result.detail_code == "SYNTHETIC_UNKNOWN_CALCULATION_CODE"
    assert result.user_message == "Не удалось рассчитать карту."
    assert [call.method for call in flow.journal] == ["load", "handle"]
    diagnostics = [record for record in caplog.records if record.name == diagnostic_logger.name]
    assert len(diagnostics) == 1
    assert diagnostics[0].levelno == logging.WARNING
    assert result.detail_code in diagnostics[0].getMessage()
    assert result.user_message not in diagnostics[0].getMessage()
    assert all(SESSION_ID not in record.getMessage() for record in records + diagnostics)
