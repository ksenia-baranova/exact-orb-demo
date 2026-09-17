"""R3.2 FR-26 / section 11.5: compact lifecycle logging function contracts.

These tests cover emitted records, not execute() ordering or cancellation.
The production module is introduced by implementation-plan step 1.4.
"""

from __future__ import annotations

from collections.abc import Iterator
import inspect
import json
import logging
import math
from uuid import UUID

import pytest
from pydantic import TypeAdapter

import exact_orb.application.operation_logging as operation_logging
from exact_orb.application.application_results import ApplicationResult
from exact_orb.application.failure_policy import describe_failure
from exact_orb.outcomes import Issue
from tests.fixtures.calculation import artifact
from tests.fixtures.telemetry import FORBIDDEN_PAYLOAD, RUN_ID, RUN_ID_B


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
