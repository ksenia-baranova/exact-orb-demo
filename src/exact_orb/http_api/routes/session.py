"""Bootstrap and read-only current-chart HTTP endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from exact_orb.application.session_view import session_view
from exact_orb.http_api.cookie import (
    clear_session_cookie, issue_session_cookie, new_session_id,
)
from exact_orb.http_api.dto import ErrorDTO
from exact_orb.http_api.projectors import project_bootstrap, project_session_view
from exact_orb.http_api.request_boundary import (
    BoundaryRejection, error_response, response_headers,
)
from exact_orb.session.outcomes import (
    SessionAbsent, SessionCreated, SessionIdConflict, StateCommitFailed,
    StateReadFailed,
)
from exact_orb.session.persistence import SessionSnapshot


router = APIRouter()
_LOG = logging.getLogger("exact_orb.http_api")


def _success(dto: object, request_id: str, session_id: str) -> JSONResponse:
    response = JSONResponse(dto.model_dump(mode="json"), headers=response_headers(request_id))
    issue_session_cookie(response, session_id)
    return response


def _error(
    *, request_id: str, code: str, detail_code: str | None,
    message: str, status: int, retryable: bool, retry_after: int | None = None,
    clear_cookie: bool = False, renew_cookie: str | None = None,
) -> JSONResponse:
    dto = ErrorDTO(
        code=code, detail_code=detail_code, user_message=message,
        retryable=retryable,
    )
    headers = response_headers(request_id)
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    response = JSONResponse(dto.model_dump(mode="json"), status_code=status, headers=headers)
    if clear_cookie:
        clear_session_cookie(response)
    if renew_cookie is not None:
        issue_session_cookie(response, renew_cookie)
    return response


def _read_failed(request_id: str, failure: StateReadFailed) -> JSONResponse:
    return _error(
        request_id=request_id, code="STATE_READ_FAILED",
        detail_code=failure.error_code,
        message="Не удалось загрузить данные сессии. Попробуйте ещё раз.",
        status=503, retryable=True, retry_after=5,
    )


@router.post("/session/bootstrap")
async def bootstrap(request: Request) -> JSONResponse:
    try:
        prepared = await request.app.state.request_boundary.prepare(
            request, body_kind="bootstrap", cookie_mode="optional",
        )
    except BoundaryRejection as rejected:
        return error_response(rejected)

    context = request.app.state.runtime.context
    cookie = prepared.cookie
    reason = cookie.status
    if cookie.status == "valid":
        assert cookie.value is not None
        loaded = await context.load(cookie.value)
        if isinstance(loaded, SessionSnapshot):
            return _success(
                project_bootstrap(loaded.state.state_version),
                prepared.request_id, cookie.value,
            )
        if isinstance(loaded, StateReadFailed):
            return _read_failed(prepared.request_id, loaded)
        if not isinstance(loaded, SessionAbsent):
            raise TypeError("unexpected session load outcome")
        reason = loaded.reason

    clear_old = reason != "missing"
    rejection = await request.app.state.admission.reserve_session_create(
        client_ip=prepared.client_ip,
    )
    if rejection is not None:
        return _error(
            request_id=prepared.request_id,
            code=rejection.code, detail_code=rejection.detail_code,
            message="Слишком много новых сессий. Попробуйте позже.",
            status=rejection.status_code, retryable=True,
            retry_after=rejection.retry_after, clear_cookie=clear_old,
        )
    for _ in range(3):
        session_id = new_session_id()
        created = await context.create(session_id)
        if isinstance(created, SessionCreated):
            return _success(
                project_bootstrap(created.state.state_version),
                prepared.request_id, session_id,
            )
        if isinstance(created, StateCommitFailed):
            return _error(
                request_id=prepared.request_id, code="SESSION_CREATE_FAILED",
                detail_code=created.error_code,
                message="Не удалось создать сессию. Попробуйте ещё раз.",
                status=503, retryable=True, retry_after=5, clear_cookie=clear_old,
            )
        if not isinstance(created, SessionIdConflict):
            raise TypeError("unexpected session create outcome")
    return _error(
        request_id=prepared.request_id, code="SESSION_CREATE_FAILED",
        detail_code="SESSION_ID_COLLISION_RETRY_EXHAUSTED",
        message="Не удалось создать сессию. Попробуйте ещё раз.",
        status=503, retryable=True, retry_after=5, clear_cookie=clear_old,
    )


@router.get("/charts/current")
async def current(request: Request) -> JSONResponse:
    try:
        prepared = await request.app.state.request_boundary.prepare(
            request, cookie_mode="required",
        )
    except BoundaryRejection as rejected:
        return error_response(rejected)

    session_id = prepared.cookie.value
    assert session_id is not None
    loaded = await request.app.state.runtime.context.load(session_id)
    if isinstance(loaded, SessionAbsent):
        return _error(
            request_id=prepared.request_id,
            code="SESSION_EXPIRED" if loaded.reason == "expired" else "SESSION_NOT_FOUND",
            detail_code=None,
            message=("Сессия истекла. Введите данные рождения заново."
                     if loaded.reason == "expired" else "Сессия не найдена. Начните заново."),
            status=409, retryable=False, clear_cookie=True,
        )
    if isinstance(loaded, StateReadFailed):
        return _read_failed(prepared.request_id, loaded)
    if not isinstance(loaded, SessionSnapshot):
        raise TypeError("unexpected session load outcome")

    try:
        dto = project_session_view(session_view(
            loaded, request.app.state.runtime.calculation_version,
        ))
    except Exception as exc:
        _LOG.error(
            "http_unhandled_exception request_id=%s safe_error=%s",
            prepared.request_id, type(exc).__name__,
        )
        return _error(
            request_id=prepared.request_id, code="INTERNAL_FAILURE",
            detail_code=None, message="Произошла внутренняя ошибка.",
            status=500, retryable=False, renew_cookie=session_id,
        )
    return _success(dto, prepared.request_id, session_id)
