"""Проверки моделей ApplicationResult из этапов 2.3 и 2.5.

Источник требований (от корня репозитория):
docs/requirements/component_responsibilities/exact-orb_application_orchestrator_requirements.md

В docstring каждого теста указаны пункты R3.2 и проверяемая часть требования.
FR — функциональное требование; AC — критерий приёмки из §15.
Эти тесты проверяют модели; выполнение execute() и события проверяются отдельно.
"""

from __future__ import annotations

from itertools import product
from typing import Any, NamedTuple, get_args
from uuid import UUID

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from exact_orb.application.application_results import (
    ApplicationAlreadyApplied,
    ApplicationCalculationFailure,
    ApplicationCommitted,
    ApplicationInputRequired,
    ApplicationInternalFailure,
    ApplicationResolutionFailure,
    ApplicationResult,
    ApplicationSessionAbsent,
    ApplicationStateCommitFailure,
    ApplicationStateReadFailure,
    ApplicationSuperseded,
)
from exact_orb.application.failure_policy import describe_failure
from exact_orb.calculation.types import ChartArtifact
from exact_orb.outcomes import Issue
from tests.fixtures.calculation import OTHER_VERSION, artifact
from tests.fixtures.telemetry import RUN_ID, RUN_ID_B


pytestmark = pytest.mark.no_ephemeris_autoinit
MODELS = (ApplicationCommitted, ApplicationAlreadyApplied, ApplicationSuperseded)
SUCCESS_MODELS = (ApplicationCommitted, ApplicationAlreadyApplied)
SUPERSEDED_MESSAGE = (
    "Результат этого запроса уже не актуален. Текущая карта не изменена."
)
COMMON_FIELDS = {
    "orch_status", "handler_status", "context_status", "code", "detail_code",
    "user_message", "retryable", "run_id", "state_version",
}
MISSING = object()

# Independent expectations from R3.2 sections 7-8, not production enums.
STATUS_VALUES = {
    "orch_status": (
        "SUCCESS", "INPUT_REQUIRED", "SUPERSEDED", "SESSION_ABSENT", "FAILURE",
    ),
    "handler_status": (
        "NOT_STARTED", "SUCCESS", "INPUT_REQUIRED", "RESOLUTION_UNAVAILABLE",
        "CALCULATION_FAILED", "UNEXPECTED_FAILURE",
    ),
    "context_status": (
        "NOT_ACCESSED", "LOADED", "READ_FAILED", "SESSION_ABSENT", "COMMITTED",
        "ALREADY_APPLIED", "SUPERSEDED", "COMMIT_FAILED",
    ),
}
STATUS_ROWS = (
    (ApplicationCommitted, ("SUCCESS", "SUCCESS", "COMMITTED")),
    (ApplicationAlreadyApplied, ("SUCCESS", "SUCCESS", "ALREADY_APPLIED")),
    (ApplicationSuperseded, ("SUPERSEDED", "SUCCESS", "SUPERSEDED")),
)


@pytest.fixture
def chart_artifact() -> ChartArtifact:
    """Build valid data without invoking the calculation engine."""
    return artifact()


def _valid_arguments(
    model: type[BaseModel],
    chart_artifact: ChartArtifact,
    *,
    run_id: UUID = RUN_ID,
    state_version: int = 7,
) -> dict[str, Any]:
    """Prepare explicit input; validation belongs to the tested models."""
    arguments: dict[str, Any] = {
        "orch_status": "SUCCESS",
        "handler_status": "SUCCESS",
        "context_status": "COMMITTED",
        "code": "OK",
        "detail_code": None,
        "user_message": None,
        "retryable": False,
        "run_id": run_id,
        "state_version": state_version,
    }
    if model is ApplicationSuperseded:
        reaction = describe_failure(kind="superseded")
        arguments.update(
            orch_status="SUPERSEDED",
            context_status="SUPERSEDED",
            code=reaction.code,
            detail_code=reaction.detail_code,
            user_message=reaction.user_message,
            retryable=reaction.retryable,
        )
    else:
        if model is ApplicationAlreadyApplied:
            arguments["context_status"] = "ALREADY_APPLIED"
        arguments["artifact"] = chart_artifact
    return arguments


def _assert_field_rejected(
    model: type[BaseModel],
    arguments: dict[str, Any],
    field: str,
    value: Any,
    *,
    allow_model_error: bool = False,
) -> None:
    """Prove the unmodified input works, then change exactly one field."""
    model(**arguments)
    changed = dict(arguments)
    if value is MISSING:
        del changed[field]
    else:
        changed[field] = value

    with pytest.raises(ValidationError) as exc_info:
        model(**changed)

    locations = {error["loc"][:1] for error in exc_info.value.errors()}
    allowed_locations = {(field,)}
    if allow_model_error:
        allowed_locations.add(())
    assert locations
    assert locations <= allowed_locations


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B], ids=["run-a", "run-b"])
@pytest.mark.parametrize(
    ("model", "expected_statuses", "expected_code", "expected_message"),
    [
        pytest.param(
            ApplicationCommitted, ("SUCCESS", "SUCCESS", "COMMITTED"),
            "OK", None, id="committed",
        ),
        pytest.param(
            ApplicationAlreadyApplied, ("SUCCESS", "SUCCESS", "ALREADY_APPLIED"),
            "OK", None, id="already-applied",
        ),
        pytest.param(
            ApplicationSuperseded, ("SUPERSEDED", "SUCCESS", "SUPERSEDED"),
            "RESULT_SUPERSEDED", SUPERSEDED_MESSAGE, id="superseded",
        ),
    ],
)
def test_valid_results_preserve_the_complete_contract(
    model: type[BaseModel],
    expected_statuses: tuple[str, str, str],
    expected_code: str,
    expected_message: str | None,
    run_id: UUID,
    chart_artifact: ChartArtifact,
) -> None:
    """Корректные успешные ответы и Superseded сохраняют переданные поля.

    Требования: R3.2, FR-22, §8–10, §12; AC-19, AC-26, AC-27 (модельная часть).
    Проверяется структура ответа; выбор результата в execute() и события не проверяются.
    """
    result = model(**_valid_arguments(model, chart_artifact, run_id=run_id))

    assert (result.orch_status, result.handler_status, result.context_status) == (
        expected_statuses
    )
    assert result.code == expected_code
    assert result.detail_code is None
    assert result.user_message == expected_message
    assert result.retryable is False
    assert result.run_id == run_id
    assert result.state_version == 7
    if model in SUCCESS_MODELS:
        assert isinstance(result.artifact, ChartArtifact)
        assert result.artifact == chart_artifact
    else:
        assert "artifact" not in result.model_dump()


@pytest.mark.parametrize(
    ("model", "field", "wrong_status"),
    [
        pytest.param(
            model, field, wrong_status,
            id=f"{model.__name__}-{field}-{wrong_status}",
        )
        for model, expected_statuses in STATUS_ROWS
        for field, expected in zip(STATUS_VALUES, expected_statuses, strict=True)
        for wrong_status in (*STATUS_VALUES[field], "UNKNOWN_STATUS")
        if wrong_status != expected
    ],
)
def test_results_reject_each_alternative_status(
    model: type[BaseModel],
    field: str,
    wrong_status: str,
    chart_artifact: ChartArtifact,
) -> None:
    """Три модели отклоняют статусы других вариантов и неизвестные статусы.

    Требования: R3.2, FR-22, §7–9; AC-22 (валидация отдельных моделей).
    Равенство полного множества троек проверяется отдельным тестом union.
    """
    _assert_field_rejected(
        model, _valid_arguments(model, chart_artifact), field, wrong_status,
        allow_model_error=True,
    )


@pytest.mark.parametrize(
    ("model", "field", "wrong_value"),
    [
        pytest.param(model, field, wrong_value, id=f"{model.__name__}-{field}-{label}")
        for model in MODELS
        for field, wrong_value, label in (
            (
                "code",
                "OK" if model is ApplicationSuperseded else "RESULT_SUPERSEDED",
                "other-result",
            ),
            ("code", "INTERNAL_FAILURE", "failure"),
            ("detail_code", "SYNTHETIC_ERROR", "technical-detail"),
            ("retryable", True, "retry"),
        )
    ],
)
def test_results_reject_contradictory_reaction_fields(
    model: type[BaseModel],
    field: str,
    wrong_value: Any,
    chart_artifact: ChartArtifact,
) -> None:
    """Код, техническая причина и возможность повторения согласованы с видом ответа.

    Требования: R3.2, FR-22, §9; AC-23.
    """
    _assert_field_rejected(
        model, _valid_arguments(model, chart_artifact), field, wrong_value,
        allow_model_error=True,
    )


@pytest.mark.parametrize(
    ("model", "state_version"),
    [
        pytest.param(ApplicationCommitted, 1, id="committed-lower-bound"),
        pytest.param(ApplicationCommitted, 42, id="committed-positive"),
        pytest.param(ApplicationAlreadyApplied, 0, id="already-applied-zero"),
        pytest.param(ApplicationAlreadyApplied, 42, id="already-applied-positive"),
        pytest.param(ApplicationSuperseded, 0, id="superseded-zero"),
        pytest.param(ApplicationSuperseded, 42, id="superseded-positive"),
    ],
)
def test_results_preserve_versions_including_the_lower_bound(
    model: type[BaseModel], state_version: int, chart_artifact: ChartArtifact,
) -> None:
    """Подтверждённая версия сохраняется, включая нижнюю границу каждой модели.

    Требования: R3.2, §9, §12; AC-27 (модельная часть).
    Получение версии из commit outcome и её актуальность здесь не проверяются.
    """
    result = model(**_valid_arguments(model, chart_artifact, state_version=state_version))

    assert result.state_version == state_version


@pytest.mark.parametrize(
    ("model", "wrong_version"),
    [
        pytest.param(model, value, id=f"{model.__name__}-{label}")
        for model in MODELS
        for value, label in (
            (-1, "negative"), (None, "none"), (MISSING, "missing"),
            (True, "bool"), ("3", "string"), (3.0, "float"),
        )
    ] + [pytest.param(ApplicationCommitted, 0, id="committed-zero")],
)
def test_results_require_a_version_within_the_model_bound(
    model: type[BaseModel], wrong_version: Any, chart_artifact: ChartArtifact,
) -> None:
    """Ответ требует версию в допустимых границах, без None или пропуска.

    Требования: R3.2, FR-22, §9, §12; AC-23, AC-27 (модельная часть).
    """
    _assert_field_rejected(
        model, _valid_arguments(model, chart_artifact), "state_version", wrong_version,
    )


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
@pytest.mark.parametrize(
    "wrong_run_id",
    [
        pytest.param(MISSING, id="missing"),
        pytest.param(None, id="none"),
        pytest.param("not-a-uuid", id="malformed"),
    ],
)
def test_results_require_a_valid_run_id(
    model: type[BaseModel], wrong_run_id: Any, chart_artifact: ChartArtifact,
) -> None:
    """Каждая из трёх моделей требует корректный UUID операции.

    Требования: R3.2, §12; AC-26 (обязательность поля в модели).
    Сквозная передача исходного run_id через execute() и события не проверяется.
    """
    _assert_field_rejected(
        model, _valid_arguments(model, chart_artifact), "run_id", wrong_run_id,
    )


@pytest.mark.parametrize("model", SUCCESS_MODELS, ids=lambda model: model.__name__)
@pytest.mark.parametrize(
    "wrong_artifact",
    [
        pytest.param(MISSING, id="missing"),
        pytest.param(None, id="none"),
        pytest.param({}, id="invalid-object"),
    ],
)
def test_success_results_require_a_valid_artifact(
    model: type[BaseModel], wrong_artifact: Any, chart_artifact: ChartArtifact,
) -> None:
    """Успешный ответ требует корректный расчётный артефакт.

    Требования: R3.2, FR-22, §9, §12; AC-23 (payload).
    """
    _assert_field_rejected(
        model, _valid_arguments(model, chart_artifact), "artifact", wrong_artifact,
    )


@pytest.mark.parametrize("model", SUCCESS_MODELS, ids=lambda model: model.__name__)
def test_success_results_reject_a_user_message(
    model: type[BaseModel], chart_artifact: ChartArtifact,
) -> None:
    """Две успешные модели сохраняют контракт user_message=None.

    Требования: R3.2, FR-22, §9, §12; AC-23 (согласованность полей ответа).
    """
    _assert_field_rejected(
        model, _valid_arguments(model, chart_artifact),
        "user_message", "Synthetic non-empty message.", allow_model_error=True,
    )


def test_superseded_requires_a_user_message(chart_artifact: ChartArtifact) -> None:
    """Ответ об устаревшем результате не принимает None вместо сообщения.

    Требования: R3.2, FR-23, §10, §12; AC-19 (поля модели).
    Проверка безопасной нормализации реального исключения в AC-21 сюда не входит.
    """
    _assert_field_rejected(
        ApplicationSuperseded,
        _valid_arguments(ApplicationSuperseded, chart_artifact),
        "user_message", None,
    )


@pytest.mark.parametrize("message", ["", "Безопасное сообщение приложения."])
def test_superseded_requires_exact_policy_message(chart_artifact: ChartArtifact, message: str) -> None:
    """3.R2; §10: Superseded также не принимает произвольный текст."""
    arguments = _valid_arguments(ApplicationSuperseded, chart_artifact)
    assert ApplicationSuperseded(**arguments).user_message == SUPERSEDED_MESSAGE
    _assert_field_rejected(
        ApplicationSuperseded, arguments, "user_message", message, allow_model_error=True,
    )


@pytest.mark.parametrize("with_artifact", [True, False], ids=["valid-artifact", "none"])
def test_superseded_rejects_an_artifact_argument(
    with_artifact: bool, chart_artifact: ChartArtifact,
) -> None:
    """Superseded отклоняет артефакт, в том числе явно переданный None.

    Требования: R3.2, FR-22, §9, §12; AC-23 (payload).
    """
    committed = ApplicationCommitted(
        **_valid_arguments(ApplicationCommitted, chart_artifact)
    )
    assert committed.artifact == chart_artifact

    _assert_field_rejected(
        ApplicationSuperseded,
        _valid_arguments(ApplicationSuperseded, chart_artifact),
        "artifact", chart_artifact if with_artifact else None,
        allow_model_error=True,
    )


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
@pytest.mark.parametrize("field", ["run_id", "state_version", "orch_status"])
def test_results_are_frozen_even_for_valid_field_assignments(
    model: type[BaseModel], field: str, chart_artifact: ChartArtifact,
) -> None:
    """Поля трёх созданных моделей нельзя заменить даже допустимыми значениями.

    Требования: R3.2, FR-22, §9; AC-24.
    """
    arguments = _valid_arguments(model, chart_artifact)
    result = model(**arguments)
    before = result.model_dump()
    replacement = {
        "run_id": RUN_ID_B,
        "state_version": 8,
        "orch_status": result.orch_status,
    }[field]
    # A fresh model accepts the same replacement, so validation is not the cause.
    control = model(**{**arguments, field: replacement})
    assert getattr(control, field) == replacement
    assert model.model_config.get("frozen") is True

    with pytest.raises(ValidationError) as exc_info:
        setattr(result, field, replacement)

    assert {error["type"] for error in exc_info.value.errors()} == {"frozen_instance"}
    assert result.model_dump() == before


@pytest.mark.parametrize("model", SUCCESS_MODELS, ids=lambda model: model.__name__)
def test_success_results_reject_replacing_a_valid_artifact(
    model: type[BaseModel], chart_artifact: ChartArtifact,
) -> None:
    """Артефакт успешного ответа нельзя заменить после создания модели.

    Требования: R3.2, FR-22, §9; AC-24.
    Глубокая неизменяемость вложенных данных артефакта здесь не проверяется.
    """
    arguments = _valid_arguments(model, chart_artifact)
    result = model(**arguments)
    before = result.model_dump()
    replacement = artifact(version=OTHER_VERSION)
    assert replacement != chart_artifact
    control = model(**{**arguments, "artifact": replacement})
    assert control.artifact == replacement

    with pytest.raises(ValidationError) as exc_info:
        result.artifact = replacement

    assert {error["type"] for error in exc_info.value.errors()} == {"frozen_instance"}
    assert result.model_dump() == before


@pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
def test_result_dump_contains_only_the_public_fields(
    model: type[BaseModel], chart_artifact: ChartArtifact,
) -> None:
    """Публичное представление трёх моделей содержит заданные поля и значения.

    Требования: R3.2, §9, §12; AC-19 (состав ответа), AC-23 (payload).
    Проверяется model_dump(), без проверки HTTP-сериализации.
    """
    arguments = _valid_arguments(model, chart_artifact)
    result = model(**arguments)

    dumped = result.model_dump()

    expected_fields = COMMON_FIELDS | ({"artifact"} if model in SUCCESS_MODELS else set())
    assert set(dumped) == expected_fields
    for field in COMMON_FIELDS:
        assert dumped[field] == arguments[field]
    assert dumped["detail_code"] is None
    assert dumped["retryable"] is False
    if model in SUCCESS_MODELS:
        assert dumped["user_message"] is None
        assert dumped["artifact"] == chart_artifact.model_dump()
    else:
        assert dumped["user_message"] == SUPERSEDED_MESSAGE


# Step 2.5 keeps the preceding tests, helpers and parameter tables unchanged.
class _FailureCase(NamedTuple):
    name: str
    model: type[BaseModel]
    statuses: tuple[str, str, str]
    kind: str
    reaction: tuple[str, str | None, str, bool]
    state_version: int | None
    reason: str | None = None


_SIMPLE_FAILURE_CASES = (
    _FailureCase(
        "input-required", ApplicationInputRequired,
        ("INPUT_REQUIRED", "INPUT_REQUIRED", "LOADED"), "input_required",
        ("INPUT_REQUIRED", None,
         "Проверьте введённые данные и исправьте отмеченные поля.", False), 0,
    ),
    _FailureCase(
        "resolution-retryable", ApplicationResolutionFailure,
        ("FAILURE", "RESOLUTION_UNAVAILABLE", "LOADED"), "resolution_unavailable",
        ("RESOLUTION_UNAVAILABLE", "UNKNOWN_RESOLUTION",
         "Не удалось определить данные места и времени. Попробуйте ещё раз.", True), 0,
    ),
    _FailureCase(
        "resolution-final", ApplicationResolutionFailure,
        ("FAILURE", "RESOLUTION_UNAVAILABLE", "LOADED"), "resolution_unavailable",
        ("RESOLUTION_UNAVAILABLE", "UNKNOWN_RESOLUTION",
         "Не удалось определить данные места и времени для указанного ввода.", False), 0,
    ),
    _FailureCase(
        "read-failure", ApplicationStateReadFailure,
        ("FAILURE", "NOT_STARTED", "READ_FAILED"), "state_read_failed",
        ("STATE_READ_FAILED", "UNKNOWN_READ_ERROR",
         "Не удалось загрузить данные сессии. Попробуйте ещё раз.", True), None,
    ),
    _FailureCase(
        "commit-failure", ApplicationStateCommitFailure,
        ("FAILURE", "SUCCESS", "COMMIT_FAILED"), "state_commit_failed",
        ("STATE_COMMIT_FAILED", "UNKNOWN_COMMIT_ERROR",
         "Не удалось подтвердить сохранение карты. "
         "Обновите страницу, чтобы проверить актуальное состояние.", True), None,
    ),
)
_CALCULATION_CASES = tuple(
    _FailureCase(
        f"calculation-{error_code}", ApplicationCalculationFailure,
        ("FAILURE", "CALCULATION_FAILED", "LOADED"), "calculation_failed",
        ("CALCULATION_FAILED", error_code, message, retryable), 0,
    )
    for error_code, retryable, message in (
        ("EPHEMERIS_UNAVAILABLE", True, "Расчёт временно недоступен. Попробуйте ещё раз."),
        ("HOUSES_DEGENERATE", False,
         "Для выбранных данных невозможно рассчитать дома в текущей системе домов."),
        ("SPEC_INVALID", False, "Не удалось подготовить параметры расчёта карты."),
        ("GEOGRAPHY_INVALID", False,
         "Не удалось выполнить расчёт карты для выбранного места."),
        ("ENGINE_UNEXPECTED", False, "Не удалось рассчитать карту из-за внутренней ошибки."),
        ("UNKNOWN_CALCULATION_A", False, "Не удалось рассчитать карту."),
        ("UNKNOWN_CALCULATION_B", False, "Не удалось рассчитать карту."),
    )
)
_ABSENCE_CASES = tuple(
    _FailureCase(
        name, ApplicationSessionAbsent,
        ("SESSION_ABSENT", handler_status, "SESSION_ABSENT"), "session_absent",
        (code, None, message, False), None, reason,
    )
    for name, handler_status, reason, code, message in (
        ("absent-load-expired", "NOT_STARTED", "expired", "SESSION_EXPIRED",
         "Сессия истекла. Введите данные рождения заново."),
        ("absent-load-not-found", "NOT_STARTED", "not_found", "SESSION_NOT_FOUND",
         "Сессия не найдена. Начните заново."),
        ("absent-commit-expired", "SUCCESS", "expired", "SESSION_LOST_DURING_OPERATION",
         "Сессия была потеряна до сохранения карты. Введите данные рождения заново."),
        ("absent-commit-not-found", "SUCCESS", "not_found", "SESSION_LOST_DURING_OPERATION",
         "Сессия была потеряна до сохранения карты. Введите данные рождения заново."),
    )
)
_INTERNAL_CASES = (
    _FailureCase(
        "handler-not-registered", ApplicationInternalFailure,
        ("FAILURE", "NOT_STARTED", "NOT_ACCESSED"), "handler_not_registered",
        ("HANDLER_NOT_REGISTERED", None,
         "Не удалось выполнить запрос из-за внутренней ошибки.", False), None,
    ),
    _FailureCase(
        "internal-before-load", ApplicationInternalFailure,
        ("FAILURE", "NOT_STARTED", "NOT_ACCESSED"), "internal_failure",
        ("INTERNAL_FAILURE", None, "Произошла внутренняя ошибка.", False), None,
    ),
    _FailureCase(
        "internal-handler", ApplicationInternalFailure,
        ("FAILURE", "UNEXPECTED_FAILURE", "LOADED"), "internal_failure",
        ("INTERNAL_FAILURE", None, "Произошла внутренняя ошибка.", False), 0,
    ),
    _FailureCase(
        "internal-commit", ApplicationInternalFailure,
        ("FAILURE", "SUCCESS", "COMMIT_FAILED"), "internal_failure",
        ("INTERNAL_FAILURE", None, "Произошла внутренняя ошибка.", False), None,
    ),
)
_FAILURE_CASES = (
    _SIMPLE_FAILURE_CASES + _CALCULATION_CASES + _ABSENCE_CASES + _INTERNAL_CASES
)
_FAILURE_MODELS = (
    ApplicationInputRequired, ApplicationResolutionFailure, ApplicationCalculationFailure,
    ApplicationSessionAbsent, ApplicationStateReadFailure, ApplicationStateCommitFailure,
    ApplicationInternalFailure,
)
_REPRESENTATIVE_FAILURE_CASES = tuple(
    next(case for case in _FAILURE_CASES if case.model is model)
    for model in _FAILURE_MODELS
)
_LOADED_CASES = tuple(case for case in _FAILURE_CASES if case.statuses[2] == "LOADED")
_NO_VERSION_CASES = tuple(case for case in _FAILURE_CASES if case.state_version is None)
_TECHNICAL_CASES = tuple(
    case for case in _REPRESENTATIVE_FAILURE_CASES if case.reaction[1] is not None
)
_EXPECTED_UNION_TRIPLES = {
    ("SUCCESS", "SUCCESS", "COMMITTED"),
    ("SUCCESS", "SUCCESS", "ALREADY_APPLIED"),
    ("INPUT_REQUIRED", "INPUT_REQUIRED", "LOADED"),
    ("FAILURE", "RESOLUTION_UNAVAILABLE", "LOADED"),
    ("FAILURE", "CALCULATION_FAILED", "LOADED"),
    ("SESSION_ABSENT", "NOT_STARTED", "SESSION_ABSENT"),
    ("FAILURE", "NOT_STARTED", "READ_FAILED"),
    ("SESSION_ABSENT", "SUCCESS", "SESSION_ABSENT"),
    ("FAILURE", "SUCCESS", "COMMIT_FAILED"),
    ("SUPERSEDED", "SUCCESS", "SUPERSEDED"),
    ("FAILURE", "UNEXPECTED_FAILURE", "LOADED"),
    ("FAILURE", "NOT_STARTED", "NOT_ACCESSED"),
}


def _input_issues() -> tuple[Issue, ...]:
    return (
        Issue(field="birth_time", code="MISSING"),
        Issue(
            field="birth_date", code="INVALID", candidates=("2000-01-01",),
            constraints={"min": "1800-01-01"},
        ),
    )


def _failure_arguments(case: _FailureCase, *, run_id: UUID = RUN_ID) -> dict[str, Any]:
    """Prepare policy output; expected fields stay in the independent case table."""
    stage = None
    if case.model is ApplicationSessionAbsent:
        stage = "load" if case.statuses[1] == "NOT_STARTED" else "commit"
    reaction = describe_failure(
        kind=case.kind, error_code=case.reaction[1],
        retryable=case.reaction[3] if case.kind == "resolution_unavailable" else None,
        stage=stage, reason=case.reason,
    )
    arguments = {
        "orch_status": case.statuses[0], "handler_status": case.statuses[1],
        "context_status": case.statuses[2], "code": reaction.code,
        "detail_code": reaction.detail_code, "user_message": reaction.user_message,
        "retryable": reaction.retryable, "state_version": case.state_version,
        "run_id": run_id,
    }
    if case.model is ApplicationInputRequired:
        arguments["issues"] = _input_issues()[:1]
    if case.model is ApplicationSessionAbsent:
        arguments["reason"] = case.reason
    return arguments


def _union_examples(chart_artifact: ChartArtifact) -> list[tuple[type[BaseModel], dict[str, Any]]]:
    examples = [(model, _valid_arguments(model, chart_artifact)) for model in MODELS]
    examples.extend((case.model, _failure_arguments(case)) for case in _FAILURE_CASES)
    # Each seed is proved valid before testing the union or altering statuses.
    return [(model, model(**arguments).model_dump()) for model, arguments in examples]


@pytest.mark.parametrize("run_id", [RUN_ID, RUN_ID_B], ids=["run-a", "run-b"])
@pytest.mark.parametrize("case", _FAILURE_CASES, ids=lambda case: case.name)
def test_failure_models_preserve_complete_records(case: _FailureCase, run_id: UUID) -> None:
    """Семь моделей принимают согласованные ответы и сохраняют их содержимое.

    Требования: R3.2, FR-22–23, §8–10, §12; AC-19, AC-20, AC-25–27
    (поля моделей, включая тексты, причины отсутствия сессии, UUID и версии).
    Нормализация outcomes в execute(), события и WARN здесь не проверяются.
    """
    result = case.model(**_failure_arguments(case, run_id=run_id))

    assert (result.orch_status, result.handler_status, result.context_status) == case.statuses
    code, detail_code, message, retryable = case.reaction
    assert result.code == code
    assert result.detail_code == detail_code
    assert result.user_message == message
    assert result.retryable is retryable
    assert result.state_version == case.state_version
    assert result.run_id == run_id
    if case.model is ApplicationInputRequired:
        assert result.issues == _input_issues()[:1]
    if case.model is ApplicationSessionAbsent:
        assert result.reason == case.reason


@pytest.mark.parametrize("count", [1, 2])
def test_input_required_preserves_ordered_structured_issues(count: int) -> None:
    """Ошибки полей сохраняют порядок, коды, варианты выбора и ограничения.

    Требования: R3.2, §9, §11.3, §12; AC-19 (содержимое ответа InputRequired).
    """
    arguments = _failure_arguments(_SIMPLE_FAILURE_CASES[0])
    issues = _input_issues()[:count]
    arguments["issues"] = issues

    result = ApplicationInputRequired(**arguments)

    assert isinstance(result.issues, tuple)
    assert [issue.model_dump() for issue in result.issues] == [
        issue.model_dump() for issue in issues
    ]


@pytest.mark.parametrize(
    "issues", [MISSING, None, (), ({},)],
    ids=["missing", "none", "empty", "invalid-item"],
)
def test_input_required_rejects_missing_empty_or_invalid_issues(issues: Any) -> None:
    """InputRequired требует непустой tuple корректных Issue.

    Требования: R3.2, FR-22, §9; AC-23 (payload).
    K3: преобразование пустого issues от Handler остаётся отдельным решением.
    """
    _assert_field_rejected(
        ApplicationInputRequired, _failure_arguments(_SIMPLE_FAILURE_CASES[0]),
        "issues", issues, allow_model_error=True,
    )


@pytest.mark.parametrize("case", _CALCULATION_CASES, ids=lambda case: case.name)
def test_calculation_failure_rejects_retryability_inconsistent_with_code(
    case: _FailureCase,
) -> None:
    """Возможность повторения согласована с известным или неизвестным кодом расчёта.

    Требования: R3.2, FR-22–23, §9–10; AC-23 (retryable).
    Фактический повтор операции и запись WARN не проверяются.
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "retryable", not case.reaction[3],
        allow_model_error=True,
    )


@pytest.mark.parametrize(
    "case",
    tuple(case for case in _FAILURE_CASES if case.model not in (
        ApplicationResolutionFailure, ApplicationCalculationFailure,
    )),
    ids=lambda case: case.name,
)
def test_failure_models_reject_contradictory_fixed_retryability(case: _FailureCase) -> None:
    """Модели с фиксированным retryable отклоняют противоположное значение.

    Требования: R3.2, FR-22, §9–10; AC-23.
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "retryable", not case.reaction[3],
        allow_model_error=True,
    )


@pytest.mark.parametrize("case", [
    case for case in _FAILURE_CASES
    if case.model in (ApplicationStateReadFailure, ApplicationStateCommitFailure)
], ids=lambda case: case.name)
def test_persistence_failure_rejects_empty_detail_code(case: _FailureCase) -> None:
    """3.R2: min_length=1 исходных persistence outcomes сохраняется во внешнем ответе."""
    arguments = _failure_arguments(case)
    assert case.model(**arguments).detail_code == case.reaction[1]
    _assert_field_rejected(case.model, arguments, "detail_code", "")


@pytest.mark.parametrize("detail_code", [MISSING, None], ids=["missing", "none"])
@pytest.mark.parametrize("case", _TECHNICAL_CASES, ids=lambda case: case.name)
def test_technical_failure_models_require_a_detail_code(
    case: _FailureCase, detail_code: Any,
) -> None:
    """Технические отказы требуют detail_code, без пропуска или None.

    Требования: R3.2, FR-22–23, §9; AC-23 (detail_code).
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "detail_code", detail_code,
        allow_model_error=True,
    )


@pytest.mark.parametrize(
    "case", tuple(case for case in _FAILURE_CASES if case.reaction[1] is None),
    ids=lambda case: case.name,
)
def test_failure_models_without_technical_reason_reject_detail_code(case: _FailureCase) -> None:
    """Ответы без технической причины отклоняют посторонний detail_code.

    Требования: R3.2, FR-22, §9; AC-23.
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "detail_code", "SYNTHETIC_ERROR",
        allow_model_error=True,
    )


@pytest.mark.parametrize("case", _FAILURE_CASES, ids=lambda case: case.name)
def test_failure_models_reject_success_code(case: _FailureCase) -> None:
    """Ответы, требующие реакции, отклоняют код успешного завершения OK.

    Требования: R3.2, FR-22, §9; AC-23 (code).
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "code", "OK", allow_model_error=True,
    )


@pytest.mark.parametrize("case", _FAILURE_CASES, ids=lambda case: case.name)
def test_failure_models_reject_incompatible_and_unknown_statuses(case: _FailureCase) -> None:
    """Каждая из семи моделей отклоняет несовместимые и неизвестные статусы.

    Требования: R3.2, FR-22, §7–9; AC-22 (валидация отдельных моделей).
    Точное множество допустимых троек проверяется отдельным тестом union.
    """
    arguments = _failure_arguments(case)
    incompatible = {
        "orch_status": "SUCCESS",
        "handler_status": (
            "NOT_STARTED" if case.model is ApplicationInputRequired else "INPUT_REQUIRED"
        ),
        "context_status": "COMMITTED",
    }
    for field, value in incompatible.items():
        _assert_field_rejected(case.model, arguments, field, value, allow_model_error=True)
        _assert_field_rejected(
            case.model, arguments, field, "UNKNOWN_STATUS", allow_model_error=True,
        )


@pytest.mark.parametrize("version", [0, 9], ids=["zero", "positive"])
@pytest.mark.parametrize("case", _LOADED_CASES, ids=lambda case: case.name)
def test_loaded_failures_preserve_known_nonnegative_version(
    case: _FailureCase, version: int,
) -> None:
    """Ответ после загрузки сохраняет прочитанную версию, включая ноль.

    Требования: R3.2, §9, §12; AC-27 (модельная часть).
    Передача версии из реального snapshot здесь не проверяется.
    """
    arguments = _failure_arguments(case)
    arguments["state_version"] = version
    assert case.model(**arguments).state_version == version


@pytest.mark.parametrize(
    "version", [MISSING, None, -1, True, "3", 3.0],
    ids=["missing", "none", "negative", "bool", "string", "float"],
)
@pytest.mark.parametrize("case", _LOADED_CASES, ids=lambda case: case.name)
def test_loaded_failures_require_known_nonnegative_version(
    case: _FailureCase, version: Any,
) -> None:
    """Варианты LOADED требуют неотрицательную версию вместо пропуска или None.

    Требования: R3.2, FR-22, §9, §12; AC-23, AC-27 (модельная часть).
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "state_version", version,
        allow_model_error=True,
    )


@pytest.mark.parametrize("version", [0, 9], ids=["zero", "positive"])
@pytest.mark.parametrize("case", _NO_VERSION_CASES, ids=lambda case: case.name)
def test_failures_without_known_state_reject_numeric_version(
    case: _FailureCase, version: int,
) -> None:
    """Ответ с неизвестной версией состояния допускает только None.

    Требования: R3.2, FR-22, §9, §12; AC-23, AC-27 (модельная часть).
    Фактический исход записи при COMMIT_FAILED этим тестом не устанавливается.
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "state_version", version,
        allow_model_error=True,
    )


@pytest.mark.parametrize("run_id", [MISSING, None, "not-a-uuid"], ids=["missing", "none", "invalid"])
@pytest.mark.parametrize("case", _REPRESENTATIVE_FAILURE_CASES, ids=lambda case: case.name)
def test_failure_models_require_a_valid_run_id(case: _FailureCase, run_id: Any) -> None:
    """Семь моделей требуют корректный UUID операции.

    Требования: R3.2, §12; AC-26 (обязательность поля в модели).
    Передача исходного run_id через execute() и события не проверяется.
    """
    _assert_field_rejected(case.model, _failure_arguments(case), "run_id", run_id)


@pytest.mark.parametrize("case", _REPRESENTATIVE_FAILURE_CASES, ids=lambda case: case.name)
@pytest.mark.parametrize("message", [
    None, "Безопасное сообщение приложения.",
    "Traceback: sqlite3.OperationalError /synthetic/db", "",
])
def test_failure_models_require_the_policy_message(case: _FailureCase, message: Any) -> None:
    """3.R2; FR-23, §10: сообщение определяется реакцией, а не произвольным вводом.

    Положительный контроль использует независимый текст таблицы сценариев.
    Выбор правильной реакции в execute остаётся отдельным контрактом.
    """
    arguments = _failure_arguments(case)
    assert case.model(**arguments).user_message == case.reaction[2]
    _assert_field_rejected(
        case.model, arguments, "user_message", message, allow_model_error=True,
    )


@pytest.mark.parametrize("case", _ABSENCE_CASES, ids=lambda case: case.name)
def test_session_absent_rejects_code_for_other_reason_or_stage(case: _FailureCase) -> None:
    """Код отсутствия сессии согласован с причиной и стадией операции.

    Требования: R3.2, FR-22, §9; AC-20 (модельная часть), AC-23.
    Реальное исчезновение сессии между load и commit не моделируется.
    """
    arguments = _failure_arguments(case)
    for code in ("SESSION_EXPIRED", "SESSION_NOT_FOUND", "SESSION_LOST_DURING_OPERATION"):
        if code != case.reaction[0]:
            _assert_field_rejected(
                case.model, arguments, "code", code, allow_model_error=True,
            )
    other_handler_status = "SUCCESS" if case.statuses[1] == "NOT_STARTED" else "NOT_STARTED"
    _assert_field_rejected(
        case.model, arguments, "handler_status", other_handler_status, allow_model_error=True,
    )
    if case.statuses[1] == "NOT_STARTED":
        other_reason = "not_found" if case.reason == "expired" else "expired"
        _assert_field_rejected(
            case.model, arguments, "reason", other_reason, allow_model_error=True,
        )


@pytest.mark.parametrize("reason", [MISSING, None, "unknown"], ids=["missing", "none", "unknown"])
@pytest.mark.parametrize("case", _ABSENCE_CASES, ids=lambda case: case.name)
def test_session_absent_requires_a_known_reason(case: _FailureCase, reason: Any) -> None:
    """Ответ об отсутствии сессии требует причину expired или not_found.

    Требования: R3.2, FR-22, §9, §12; AC-23 (reason).
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "reason", reason, allow_model_error=True,
    )


@pytest.mark.parametrize("case", _INTERNAL_CASES[2:], ids=lambda case: case.name)
def test_handler_not_registered_code_is_rejected_after_load(case: _FailureCase) -> None:
    """HANDLER_NOT_REGISTERED недопустим в вариантах ошибки Handler или commit.

    Требования: R3.2, FR-22, §9; AC-23 (связь code и статусов).
    Routing и запрет вызова load по AC-4 здесь не проверяются.
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "code", "HANDLER_NOT_REGISTERED",
        allow_model_error=True,
    )


@pytest.mark.parametrize(
    ("case", "handler_status"),
    [
        pytest.param(_INTERNAL_CASES[2], "SUCCESS", id="success-loaded"),
        pytest.param(_INTERNAL_CASES[2], "NOT_STARTED", id="not-started-loaded"),
        pytest.param(_INTERNAL_CASES[3], "UNEXPECTED_FAILURE", id="unexpected-commit-failed"),
    ],
)
def test_internal_failure_rejects_incompatible_status_pairs(
    case: _FailureCase, handler_status: str,
) -> None:
    """InternalFailure отклоняет несогласованные статусы Handler и session-стадии.

    Требования: R3.2, FR-22, §8–9; AC-22 (валидация InternalFailure).
    Обработка настоящего исключения и выбор ответа в execute() не проверяются.
    """
    _assert_field_rejected(
        case.model, _failure_arguments(case), "handler_status", handler_status,
        allow_model_error=True,
    )


@pytest.mark.parametrize("include_artifact", [True, False], ids=["artifact", "none"])
@pytest.mark.parametrize("case", _REPRESENTATIVE_FAILURE_CASES, ids=lambda case: case.name)
def test_failure_models_reject_artifact_even_when_none(
    case: _FailureCase, include_artifact: bool, chart_artifact: ChartArtifact,
) -> None:
    """Семь моделей без карты отклоняют artifact, включая явно переданный None.

    Требования: R3.2, FR-22, §9, §12; AC-23 (payload).
    """
    assert ApplicationCommitted(**_valid_arguments(ApplicationCommitted, chart_artifact)).artifact == (
        chart_artifact
    )
    _assert_field_rejected(
        case.model, _failure_arguments(case), "artifact",
        chart_artifact if include_artifact else None,
    )


@pytest.mark.parametrize("case", _REPRESENTATIVE_FAILURE_CASES, ids=lambda case: case.name)
def test_failure_models_are_frozen_for_valid_field_assignments(case: _FailureCase) -> None:
    """Созданные модели запрещают замену run_id другим корректным UUID.

    Требования: R3.2, FR-22, §9; AC-24.
    """
    assert case.model.model_config.get("frozen") is True
    arguments = _failure_arguments(case)
    result = case.model(**arguments)
    before = result.model_dump()
    # The new UUID is independently valid; rejection must be due to freezing.
    assert case.model(**{**arguments, "run_id": RUN_ID_B}).run_id == RUN_ID_B

    with pytest.raises(ValidationError) as exc_info:
        result.run_id = RUN_ID_B

    assert {error["type"] for error in exc_info.value.errors()} == {"frozen_instance"}
    assert result.model_dump() == before


@pytest.mark.parametrize("field", ["issues", "reason"])
def test_failure_specific_fields_cannot_be_replaced_with_valid_values(field: str) -> None:
    """Поля issues и reason нельзя заменить после создания модели.

    Требования: R3.2, FR-22, §9; AC-24.
    Глубокая неизменяемость вложенных Issue здесь не проверяется.
    """
    if field == "issues":
        case, replacement = _SIMPLE_FAILURE_CASES[0], _input_issues()
    else:
        # Both reasons are valid with the commit-stage SESSION_LOST code.
        case, replacement = _ABSENCE_CASES[2], "not_found"
    arguments = _failure_arguments(case)
    result = case.model(**arguments)
    before = result.model_dump()
    assert getattr(case.model(**{**arguments, field: replacement}), field) == replacement

    with pytest.raises(ValidationError) as exc_info:
        setattr(result, field, replacement)

    assert {error["type"] for error in exc_info.value.errors()} == {"frozen_instance"}
    assert result.model_dump() == before


@pytest.mark.parametrize("case", _FAILURE_CASES, ids=lambda case: case.name)
def test_failure_dump_contains_exact_public_fields_including_none(case: _FailureCase) -> None:
    """Публичное представление сохраняет обязательные поля, payload и None.

    Требования: R3.2, §9, §12; AC-19 (состав ответа), AC-23 (payload).
    Проверяется model_dump(), без проверки HTTP-сериализации.
    """
    arguments = _failure_arguments(case)
    dumped = case.model(**arguments).model_dump()
    expected = dict(arguments)
    if case.model is ApplicationInputRequired:
        expected["issues"] = tuple(issue.model_dump() for issue in arguments["issues"])
    expected_fields = COMMON_FIELDS | (
        {"issues"} if case.model is ApplicationInputRequired
        else {"reason"} if case.model is ApplicationSessionAbsent else set()
    )

    assert set(dumped) == expected_fields
    assert dumped == expected
    assert "artifact" not in dumped


def test_application_result_union_contains_exactly_ten_models() -> None:
    """ApplicationResult объединяет ровно десять предусмотренных моделей.

    Требования: R3.2, §9; AC-22 (состав проверяемого union).
    Равенство множества допустимых троек подтверждает отдельный тест.
    """
    members = get_args(ApplicationResult)
    assert len(members) == 10
    assert set(members) == set(MODELS + _FAILURE_MODELS)


def test_application_result_union_selects_concrete_models_and_preserves_records(
    chart_artifact: ChartArtifact,
) -> None:
    """Union выбирает конкретную модель и сохраняет полную запись ответа.

    Требования: R3.2, FR-22, §8–9, §12; AC-19 (валидация ответа).
    Преобразование Handler и commit outcomes в execute() не проверяется.
    """
    adapter = TypeAdapter(ApplicationResult)
    for expected_model, payload in _union_examples(chart_artifact):
        result = adapter.validate_python(payload)
        assert type(result) is expected_model, payload
        assert result.model_dump() == payload


def test_application_result_union_accepts_exactly_the_required_status_triples(
    chart_artifact: ChartArtifact,
) -> None:
    """Фактически принимаемые union тройки точно совпадают с таблицей требований.

    Требования: R3.2, FR-22, §8–9; AC-22.
    Перебор использует полные корректные записи всех предусмотренных вариантов.
    """
    adapter = TypeAdapter(ApplicationResult)
    accepted = set()
    for expected_model, payload in _union_examples(chart_artifact):
        assert type(adapter.validate_python(payload)) is expected_model
        for statuses in product(
            STATUS_VALUES["orch_status"], STATUS_VALUES["handler_status"],
            STATUS_VALUES["context_status"],
        ):
            changed = {**payload, **dict(zip(STATUS_VALUES, statuses))}
            try:
                result = adapter.validate_python(changed)
            except ValidationError:
                continue
            actual = (result.orch_status, result.handler_status, result.context_status)
            assert actual == statuses, changed
            accepted.add(statuses)

    assert accepted == _EXPECTED_UNION_TRIPLES


@pytest.mark.parametrize("field", tuple(STATUS_VALUES))
def test_application_result_union_rejects_unknown_status_values(
    field: str, chart_artifact: ChartArtifact,
) -> None:
    """Union отклоняет неизвестное значение каждого из трёх статусов.

    Требования: R3.2, FR-22, §7–9; AC-22 (замкнутость множества статусов).
    """
    adapter = TypeAdapter(ApplicationResult)
    for expected_model, payload in _union_examples(chart_artifact):
        assert type(adapter.validate_python(payload)) is expected_model
        with pytest.raises(ValidationError):
            adapter.validate_python({**payload, field: "UNKNOWN_STATUS"})
