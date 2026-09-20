"""R3.2 section 10: pure failure descriptions, before implementation step 2.2.

These tests do not cover application statuses, retries, or exception handling.
"""

from __future__ import annotations

from collections.abc import Iterator
import inspect
import logging
from typing import Any

import pytest

from exact_orb.application.failure_policy import describe_failure


pytestmark = pytest.mark.no_ephemeris_autoinit
LOGGER_NAME = "exact_orb.application.failure_policy"
CALCULATION_FALLBACK = "Не удалось рассчитать карту."
EPHEMERIS_MESSAGE = "Расчёт временно недоступен. Попробуйте ещё раз."
COMMIT_MESSAGE = (
    "Не удалось подтвердить сохранение карты. "
    "Обновите страницу, чтобы проверить актуальное состояние."
)


def _assert_description(
    description: Any,
    expected: tuple[str, str | None, str, bool],
) -> None:
    """Compare public fields without requiring a particular result class."""
    code, detail_code, user_message, retryable = expected
    assert description.code == code
    assert description.detail_code == detail_code
    assert description.user_message == user_message
    assert description.retryable is retryable


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        pytest.param(
            {"kind": "input_required"},
            (
                "INPUT_REQUIRED", None,
                "Проверьте введённые данные и исправьте отмеченные поля.", False,
            ),
            id="input-required",
        ),
        pytest.param(
            {
                "kind": "resolution_unavailable",
                "error_code": "TZ_DATA_UNAVAILABLE", "retryable": True,
            },
            (
                "RESOLUTION_UNAVAILABLE", "TZ_DATA_UNAVAILABLE",
                "Не удалось определить данные места и времени. Попробуйте ещё раз.",
                True,
            ),
            id="resolution-retryable",
        ),
        pytest.param(
            {
                "kind": "resolution_unavailable",
                "error_code": "TZ_DATA_UNAVAILABLE", "retryable": False,
            },
            (
                "RESOLUTION_UNAVAILABLE", "TZ_DATA_UNAVAILABLE",
                "Не удалось определить данные места и времени для указанного ввода.",
                False,
            ),
            id="resolution-not-retryable",
        ),
        pytest.param(
            {"kind": "calculation_failed", "error_code": "EPHEMERIS_UNAVAILABLE"},
            ("CALCULATION_FAILED", "EPHEMERIS_UNAVAILABLE", EPHEMERIS_MESSAGE, True),
            id="ephemeris-unavailable",
        ),
        pytest.param(
            {"kind": "calculation_failed", "error_code": "HOUSES_DEGENERATE"},
            (
                "CALCULATION_FAILED", "HOUSES_DEGENERATE",
                "Для выбранных данных невозможно рассчитать дома в текущей системе домов.",
                False,
            ),
            id="houses-degenerate",
        ),
        pytest.param(
            {"kind": "calculation_failed", "error_code": "SPEC_INVALID"},
            (
                "CALCULATION_FAILED", "SPEC_INVALID",
                "Не удалось подготовить параметры расчёта карты.", False,
            ),
            id="spec-invalid",
        ),
        pytest.param(
            {"kind": "calculation_failed", "error_code": "GEOGRAPHY_INVALID"},
            (
                "CALCULATION_FAILED", "GEOGRAPHY_INVALID",
                "Не удалось выполнить расчёт карты для выбранного места.", False,
            ),
            id="geography-invalid",
        ),
        pytest.param(
            {"kind": "calculation_failed", "error_code": "ENGINE_UNEXPECTED"},
            (
                "CALCULATION_FAILED", "ENGINE_UNEXPECTED",
                "Не удалось рассчитать карту из-за внутренней ошибки.", False,
            ),
            id="engine-unexpected",
        ),
        pytest.param(
            {"kind": "calculation_failed", "error_code": "SYNTHETIC_CALC_FAILURE"},
            (
                "CALCULATION_FAILED", "SYNTHETIC_CALC_FAILURE",
                CALCULATION_FALLBACK, False,
            ),
            id="unknown-calculation-code",
        ),
        pytest.param(
            {"kind": "state_read_failed", "error_code": "SQLITE_BUSY"},
            (
                "STATE_READ_FAILED", "SQLITE_BUSY",
                "Не удалось загрузить данные сессии. Попробуйте ещё раз.", True,
            ),
            id="state-read-failed",
        ),
        pytest.param(
            {"kind": "state_commit_failed", "error_code": "SQLITE_BUSY"},
            ("STATE_COMMIT_FAILED", "SQLITE_BUSY", COMMIT_MESSAGE, True),
            id="final-state-commit-failed",
        ),
        pytest.param(
            {"kind": "session_absent", "stage": "load", "reason": "expired"},
            (
                "SESSION_EXPIRED", None,
                "Сессия истекла. Введите данные рождения заново.", False,
            ),
            id="session-expired-at-load",
        ),
        pytest.param(
            {"kind": "session_absent", "stage": "load", "reason": "not_found"},
            ("SESSION_NOT_FOUND", None, "Сессия не найдена. Начните заново.", False),
            id="session-not-found-at-load",
        ),
        pytest.param(
            {"kind": "session_absent", "stage": "commit", "reason": "expired"},
            (
                "SESSION_LOST_DURING_OPERATION", None,
                "Сессия была потеряна до сохранения карты. Введите данные рождения заново.",
                False,
            ),
            id="session-expired-at-commit",
        ),
        pytest.param(
            {"kind": "session_absent", "stage": "commit", "reason": "not_found"},
            (
                "SESSION_LOST_DURING_OPERATION", None,
                "Сессия была потеряна до сохранения карты. Введите данные рождения заново.",
                False,
            ),
            id="session-not-found-at-commit",
        ),
        pytest.param(
            {"kind": "superseded"},
            (
                "RESULT_SUPERSEDED", None,
                "Результат этого запроса уже не актуален. Текущая карта не изменена.",
                False,
            ),
            id="superseded",
        ),
        pytest.param(
            {"kind": "handler_not_registered"},
            (
                "HANDLER_NOT_REGISTERED", None,
                "Не удалось выполнить запрос из-за внутренней ошибки.", False,
            ),
            id="handler-not-registered",
        ),
        pytest.param(
            {"kind": "internal_failure"},
            ("INTERNAL_FAILURE", None, "Произошла внутренняя ошибка.", False),
            id="internal-failure",
        ),
    ],
)
def test_failure_reactions_match_requirement_rows(
    arguments: dict[str, object],
    expected: tuple[str, str | None, str, bool],
) -> None:
    _assert_description(describe_failure(**arguments), expected)


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        pytest.param(
            {"kind": "calculation_failed", "error_code": "SYNTHETIC_OTHER_CALC_FAILURE"},
            (
                "CALCULATION_FAILED", "SYNTHETIC_OTHER_CALC_FAILURE",
                CALCULATION_FALLBACK, False,
            ),
            id="second-unknown-calculation-code",
        ),
        pytest.param(
            {
                "kind": "resolution_unavailable",
                "error_code": "SYNTHETIC_RESOLVER_FAILURE", "retryable": True,
            },
            (
                "RESOLUTION_UNAVAILABLE", "SYNTHETIC_RESOLVER_FAILURE",
                "Не удалось определить данные места и времени. Попробуйте ещё раз.",
                True,
            ),
            id="unknown-resolution-retryable",
        ),
        pytest.param(
            {
                "kind": "resolution_unavailable",
                "error_code": "SYNTHETIC_RESOLVER_FAILURE", "retryable": False,
            },
            (
                "RESOLUTION_UNAVAILABLE", "SYNTHETIC_RESOLVER_FAILURE",
                "Не удалось определить данные места и времени для указанного ввода.",
                False,
            ),
            id="unknown-resolution-not-retryable",
        ),
        pytest.param(
            {"kind": "state_read_failed", "error_code": "SYNTHETIC_STORAGE_FAILURE"},
            (
                "STATE_READ_FAILED", "SYNTHETIC_STORAGE_FAILURE",
                "Не удалось загрузить данные сессии. Попробуйте ещё раз.", True,
            ),
            id="unknown-state-read-code",
        ),
        pytest.param(
            {"kind": "state_commit_failed", "error_code": "SYNTHETIC_STORAGE_FAILURE"},
            ("STATE_COMMIT_FAILED", "SYNTHETIC_STORAGE_FAILURE", COMMIT_MESSAGE, True),
            id="unknown-state-commit-code",
        ),
    ],
)
def test_open_error_codes_keep_details_and_safe_messages(
    arguments: dict[str, object],
    expected: tuple[str, str | None, str, bool],
) -> None:
    description = describe_failure(**arguments)

    _assert_description(description, expected)
    assert description.detail_code == arguments["error_code"]
    assert description.detail_code not in description.user_message


def test_describe_failure_has_a_synchronous_keyword_only_api() -> None:
    assert not inspect.iscoroutinefunction(describe_failure)
    parameters = inspect.signature(describe_failure).parameters
    assert set(parameters) == {
        "kind", "error_code", "retryable", "stage", "reason",
    }
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in parameters.values())
    assert parameters["kind"].default is inspect.Parameter.empty
    for name in ("error_code", "retryable", "stage", "reason"):
        assert parameters[name].default is None


@pytest.mark.parametrize(("valid", "irrelevant"), [
    ({"kind": "input_required"}, {"stage": "commit"}),
    ({"kind": "superseded"}, {"error_code": "UNUSED"}),
    ({"kind": "handler_not_registered"}, {"retryable": False}),
    ({"kind": "internal_failure"}, {"reason": "expired"}),
    ({"kind": "calculation_failed", "error_code": "SPEC_INVALID"}, {"reason": "expired"}),
    ({"kind": "calculation_failed", "error_code": "SPEC_INVALID"}, {"retryable": False}),
    ({"kind": "resolution_unavailable", "error_code": "TZ_UNAVAILABLE", "retryable": True},
     {"stage": "load"}),
    ({"kind": "state_read_failed", "error_code": "SQLITE_BUSY"}, {"retryable": True}),
    ({"kind": "state_commit_failed", "error_code": "SQLITE_BUSY"}, {"reason": "expired"}),
    ({"kind": "session_absent", "stage": "load", "reason": "expired"}, {"error_code": "UNUSED"}),
])
def test_irrelevant_policy_arguments_are_rejected(valid: dict, irrelevant: dict) -> None:
    """3.R2: ошибку выбора аргументов нельзя скрывать молчаливым игнорированием."""
    assert describe_failure(**valid).code
    with pytest.raises(ValueError, match="does not accept"):
        describe_failure(**valid, **irrelevant)
    assert describe_failure(**valid) == describe_failure(**valid, **dict.fromkeys(irrelevant))


@pytest.mark.parametrize("kind", ["state_read_failed", "state_commit_failed"])
def test_persistence_policy_requires_nonempty_code(kind: str) -> None:
    """3.R2: внешний persistence detail сохраняет min_length=1 исходного outcome."""
    assert describe_failure(kind=kind, error_code="SQLITE_BUSY").detail_code == "SQLITE_BUSY"
    with pytest.raises(ValueError, match="nonempty"):
        describe_failure(kind=kind, error_code="")


def test_interleaved_calls_preserve_previous_descriptions() -> None:
    first = describe_failure(
        kind="calculation_failed", error_code="SYNTHETIC_CALC_FAILURE",
    )
    first_expected = (
        "CALCULATION_FAILED", "SYNTHETIC_CALC_FAILURE", CALCULATION_FALLBACK, False,
    )
    _assert_description(first, first_expected)

    known = describe_failure(
        kind="calculation_failed", error_code="EPHEMERIS_UNAVAILABLE",
    )
    second = describe_failure(
        kind="calculation_failed", error_code="SYNTHETIC_OTHER_CALC_FAILURE",
    )
    again = describe_failure(
        kind="calculation_failed", error_code="SYNTHETIC_CALC_FAILURE",
    )

    _assert_description(first, first_expected)
    _assert_description(again, first_expected)
    _assert_description(
        known, ("CALCULATION_FAILED", "EPHEMERIS_UNAVAILABLE", EPHEMERIS_MESSAGE, True),
    )
    _assert_description(
        second,
        (
            "CALCULATION_FAILED", "SYNTHETIC_OTHER_CALC_FAILURE",
            CALCULATION_FALLBACK, False,
        ),
    )


@pytest.fixture
def policy_logger(caplog: pytest.LogCaptureFixture) -> Iterator[logging.Logger]:
    """Capture the real policy logger and restore all local capture changes."""
    logger = logging.getLogger(LOGGER_NAME)
    handlers = logger.handlers[:]
    propagate, level, disabled = logger.propagate, logger.level, logger.disabled
    try:
        caplog.set_level(logging.DEBUG, logger=LOGGER_NAME)
        logger.handlers = [caplog.handler]
        logger.propagate = False
        logger.disabled = False
        yield logger
    finally:
        logger.handlers = handlers
        logger.propagate = propagate
        logger.setLevel(level)
        logger.disabled = disabled


@pytest.mark.parametrize(
    ("error_code", "message", "retryable"),
    [
        pytest.param(
            "EPHEMERIS_UNAVAILABLE", EPHEMERIS_MESSAGE, True, id="known-code",
        ),
        pytest.param(
            "SYNTHETIC_CALC_FAILURE", CALCULATION_FALLBACK, False, id="unknown-code",
        ),
    ],
)
def test_describe_failure_does_not_log(
    error_code: str,
    message: str,
    retryable: bool,
    caplog: pytest.LogCaptureFixture,
    policy_logger: logging.Logger,
) -> None:
    caplog.clear()
    policy_logger.debug("failure policy capture control")
    assert caplog.record_tuples == [
        (LOGGER_NAME, logging.DEBUG, "failure policy capture control"),
    ]
    caplog.clear()

    description = describe_failure(kind="calculation_failed", error_code=error_code)

    _assert_description(description, ("CALCULATION_FAILED", error_code, message, retryable))
    assert caplog.records == []
