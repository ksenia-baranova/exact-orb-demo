"""Pure application failure descriptions from the R3.2 reaction policy."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal


FailureKind = Literal[
    "input_required",
    "resolution_unavailable",
    "calculation_failed",
    "state_read_failed",
    "state_commit_failed",
    "session_absent",
    "superseded",
    "handler_not_registered",
    "internal_failure",
]


@dataclass(frozen=True, slots=True)
class FailureDescription:
    """An immutable reaction, without application status or operation state."""

    code: str
    detail_code: str | None
    user_message: str
    retryable: bool


_STATIC_REACTIONS = MappingProxyType({
    "input_required": FailureDescription(
        "INPUT_REQUIRED", None,
        "Проверьте введённые данные и исправьте отмеченные поля.", False,
    ),
    "superseded": FailureDescription(
        "RESULT_SUPERSEDED", None,
        "Результат этого запроса уже не актуален. Текущая карта не изменена.", False,
    ),
    "handler_not_registered": FailureDescription(
        "HANDLER_NOT_REGISTERED", None,
        "Не удалось выполнить запрос из-за внутренней ошибки.", False,
    ),
    "internal_failure": FailureDescription(
        "INTERNAL_FAILURE", None, "Произошла внутренняя ошибка.", False,
    ),
})

_CALCULATION_REACTIONS = MappingProxyType({
    "EPHEMERIS_UNAVAILABLE": (
        "Расчёт временно недоступен. Попробуйте ещё раз.", True,
    ),
    "HOUSES_DEGENERATE": (
        "Для выбранных данных невозможно рассчитать дома в текущей системе домов.",
        False,
    ),
    "SPEC_INVALID": ("Не удалось подготовить параметры расчёта карты.", False),
    "GEOGRAPHY_INVALID": (
        "Не удалось выполнить расчёт карты для выбранного места.", False,
    ),
    "ENGINE_UNEXPECTED": (
        "Не удалось рассчитать карту из-за внутренней ошибки.", False,
    ),
})
_CALCULATION_FALLBACK = ("Не удалось рассчитать карту.", False)

_PERSISTENCE_REACTIONS = MappingProxyType({
    "state_read_failed": (
        "STATE_READ_FAILED",
        "Не удалось загрузить данные сессии. Попробуйте ещё раз.",
    ),
    "state_commit_failed": (
        "STATE_COMMIT_FAILED",
        "Не удалось подтвердить сохранение карты. "
        "Обновите страницу, чтобы проверить актуальное состояние.",
    ),
})

_SESSION_LOAD_REACTIONS = MappingProxyType({
    "expired": FailureDescription(
        "SESSION_EXPIRED", None,
        "Сессия истекла. Введите данные рождения заново.", False,
    ),
    "not_found": FailureDescription(
        "SESSION_NOT_FOUND", None, "Сессия не найдена. Начните заново.", False,
    ),
})
_SESSION_LOST = FailureDescription(
    "SESSION_LOST_DURING_OPERATION", None,
    "Сессия была потеряна до сохранения карты. Введите данные рождения заново.", False,
)


def describe_failure(
    *,
    kind: FailureKind,
    error_code: str | None = None,
    retryable: bool | None = None,
    stage: Literal["load", "commit"] | None = None,
    reason: Literal["expired", "not_found"] | None = None,
) -> FailureDescription:
    """Describe a normalized failure without logging or executing recovery.

    The caller classifies the outcome and supplies its relevant arguments.
    Error codes remain open strings; unknown calculation codes use a fallback.
    """
    if kind in _STATIC_REACTIONS:
        return _STATIC_REACTIONS[kind]

    if kind == "resolution_unavailable":
        detail_code = _require_error_code(error_code)
        if not isinstance(retryable, bool):
            raise ValueError("resolution_unavailable requires a boolean retryable")
        message = (
            "Не удалось определить данные места и времени. Попробуйте ещё раз."
            if retryable
            else "Не удалось определить данные места и времени для указанного ввода."
        )
        return FailureDescription(
            "RESOLUTION_UNAVAILABLE", detail_code, message, retryable,
        )

    if kind == "calculation_failed":
        detail_code = _require_error_code(error_code)
        message, can_retry = _CALCULATION_REACTIONS.get(
            detail_code, _CALCULATION_FALLBACK,
        )
        return FailureDescription("CALCULATION_FAILED", detail_code, message, can_retry)

    if kind in _PERSISTENCE_REACTIONS:
        detail_code = _require_error_code(error_code)
        code, message = _PERSISTENCE_REACTIONS[kind]
        return FailureDescription(code, detail_code, message, True)

    if kind == "session_absent":
        if reason not in _SESSION_LOAD_REACTIONS:
            raise ValueError("session_absent requires expired or not_found reason")
        if stage == "load":
            return _SESSION_LOAD_REACTIONS[reason]
        if stage == "commit":
            return _SESSION_LOST
        raise ValueError("session_absent requires load or commit stage")

    raise ValueError("Unsupported failure kind")


def _require_error_code(error_code: str | None) -> str:
    if not isinstance(error_code, str):
        raise ValueError("This failure kind requires a string error_code")
    return error_code


__all__ = ["FailureDescription", "FailureKind", "describe_failure"]
