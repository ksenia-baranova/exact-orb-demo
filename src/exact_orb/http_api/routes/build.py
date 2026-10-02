"""Explicit natal build, owned execution and public ApplicationResult mapping."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from exact_orb.application.application_results import (
    ApplicationAlreadyApplied, ApplicationCalculationFailure, ApplicationCommitted,
    ApplicationInputRequired, ApplicationInternalFailure, ApplicationResolutionFailure,
    ApplicationResult, ApplicationSessionAbsent, ApplicationStateCommitFailure,
    ApplicationStateReadFailure, ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.birth.types import BirthInput
from exact_orb.http_api.admission import AdmissionRejection, BuildPermit
from exact_orb.http_api.cookie import clear_session_cookie, issue_session_cookie
from exact_orb.http_api.dto import ErrorDTO, IssueDTO
from exact_orb.http_api.ownership import track_request
from exact_orb.http_api.projectors import project_build_already_applied, project_build_ready
from exact_orb.http_api.request_boundary import (
    BoundaryRejection, BuildPayload, ClientDisconnected, error_response, response_headers,
)
from exact_orb.run_context import RunContext


router = APIRouter()
_LOG = logging.getLogger("exact_orb.http_api")
_ADMISSION_MESSAGES = {
    "BUILD_SESSION_RATE_LIMITED": "Лимит построений для этой сессии исчерпан.",
    "BUILD_IP_RATE_LIMITED": "Слишком много построений из этой сети. Попробуйте позже.",
    "BUILD_CAPACITY_EXHAUSTED": "Все слоты расчёта заняты. Попробуйте позже.",
}


async def _await_terminal(task: asyncio.Task[Any]) -> Any:
    """Keep a retained owner operation referenced through repeated cancellation."""

    while True:
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            if task.done():
                return task.result()


async def _watch_owner(app: Any, owner: asyncio.Task[Any], deadline: float) -> bool:
    timer = asyncio.create_task(app.state.scheduler.wait_until(deadline))
    try:
        done, _ = await asyncio.wait({owner, timer}, return_when=asyncio.FIRST_COMPLETED)
        if owner in done:
            return False
        timer.result()
        app.state.mark_build_timeout()
        return True
    finally:
        if not timer.done():
            timer.cancel()
            await asyncio.gather(timer, return_exceptions=True)


async def _listen_disconnect(request: Request) -> None:
    while True:
        message = await request.receive()
        if message["type"] == "http.disconnect":
            return


def _json(dto: Any, request_id: str, *, status: int = 200,
          session_id: str | None = None, clear_cookie: bool = False,
          retry_after: int | None = None) -> JSONResponse:
    headers = response_headers(request_id)
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    response = JSONResponse(dto.model_dump(mode="json"), status_code=status, headers=headers)
    if session_id is not None:
        issue_session_cookie(response, session_id)
    if clear_cookie:
        clear_session_cookie(response)
    return response


def _failure(request_id: str, *, code: str, detail_code: str | None,
             message: str, retryable: bool, status: int,
             state_version: int | None = None, issues: tuple[IssueDTO, ...] | None = None,
             include_version: bool = False, session_id: str | None = None,
             clear_cookie: bool = False, retry_after: int | None = None) -> JSONResponse:
    fields: dict[str, Any] = dict(
        code=code, detail_code=detail_code, user_message=message, retryable=retryable,
    )
    if include_version:
        fields["state_version"] = state_version
    if issues is not None:
        fields["issues"] = issues
    return _json(ErrorDTO(**fields), request_id, status=status,
                 session_id=session_id, clear_cookie=clear_cookie,
                 retry_after=retry_after)


def _internal(request_id: str, *, session_id: str | None = None) -> JSONResponse:
    return _failure(
        request_id, code="INTERNAL_FAILURE", detail_code=None,
        message="Произошла внутренняя ошибка.", retryable=False,
        status=500, session_id=session_id,
    )


async def _execute_owned(
    app: Any, *, permit: BuildPermit, payload: BuildPayload,
    session_id: str, request_id: str, started_execution: asyncio.Event,
) -> ApplicationResult | None:
    """Own a permit until one accepted execute reaches an ordinary terminal result."""

    started_execution.set()
    try:
        started = app.state.utc_clock()
        run = RunContext(
            run_id=UUID(request_id), started_at=started,
            deadline=started + timedelta(seconds=app.state.settings.build_timeout_seconds),
        )
        command = BuildNatalCommand(birth_input=BirthInput(
            birth_date=payload.birth_date, birth_time=payload.birth_time,
            place_id=payload.place_id,
        ))
        result = await app.state.runtime.orchestrator.execute(
            command, session_id=session_id, run=run,
        )
    except asyncio.CancelledError as cancelled:
        # execute owns protected commit and submitted executor futures; the
        # runtime snapshot additionally owns any shielded single-flight leader.
        try:
            drain = asyncio.create_task(app.state.runtime.drain())
            await _await_terminal(drain)
        except Exception as exc:
            app.state.mark_build_timeout()
            _LOG.error(
                "http_build_drain_failed request_id=%s safe_error=%s",
                request_id, type(exc).__name__,
            )
            raise cancelled
        release = asyncio.create_task(permit.release())
        await _await_terminal(release)
        raise cancelled
    except Exception as exc:
        _LOG.error(
            "http_unhandled_exception request_id=%s safe_error=%s",
            request_id, type(exc).__name__,
        )
        result = None
    release = asyncio.create_task(permit.release())
    await _await_terminal(release)
    return result


def _map_result(result: ApplicationResult | None, *, request_id: str,
                session_id: str) -> JSONResponse:
    if isinstance(result, ApplicationCommitted):
        return _json(project_build_ready(result.state_version, result.artifact),
                     request_id, session_id=session_id)
    if isinstance(result, ApplicationAlreadyApplied):
        return _json(project_build_already_applied(result.state_version),
                     request_id, session_id=session_id)
    if isinstance(result, ApplicationSessionAbsent):
        return _failure(
            request_id, code=result.code, detail_code=None,
            message=result.user_message, retryable=False, status=409,
            clear_cookie=True,
        )
    if isinstance(result, ApplicationStateReadFailure):
        return _failure(
            request_id, code=result.code, detail_code=result.detail_code,
            message=result.user_message, retryable=True, status=503,
            retry_after=5,
        )
    if isinstance(result, ApplicationStateCommitFailure):
        return _failure(
            request_id, code=result.code, detail_code=result.detail_code,
            message=result.user_message, retryable=True, status=503,
            session_id=session_id, retry_after=1,
        )
    if isinstance(result, ApplicationInputRequired):
        issues = tuple(IssueDTO(
            field=item.field, code=item.code,
            candidates=item.candidates, constraints=item.constraints,
        ) for item in result.issues)
        return _failure(
            request_id, code=result.code, detail_code=None,
            message=result.user_message, retryable=False, status=422,
            state_version=result.state_version, include_version=True,
            issues=issues, session_id=session_id,
        )
    if isinstance(result, (ApplicationResolutionFailure, ApplicationCalculationFailure)):
        return _failure(
            request_id, code=result.code, detail_code=result.detail_code,
            message=result.user_message, retryable=result.retryable,
            status=503 if result.retryable else 500,
            state_version=result.state_version, include_version=True,
            session_id=session_id, retry_after=5 if result.retryable else None,
        )
    if isinstance(result, ApplicationSuperseded):
        return _failure(
            request_id, code=result.code, detail_code=None,
            message=result.user_message, retryable=False, status=409,
            state_version=result.state_version, include_version=True,
            session_id=session_id,
        )
    if isinstance(result, ApplicationInternalFailure):
        return _internal(
            request_id,
            session_id=(session_id if result.context_status in {"LOADED", "COMMIT_FAILED"}
                        else None),
        )
    return _internal(request_id)


@router.post("/charts/natal")
@track_request
async def build(request: Request) -> JSONResponse:
    try:
        prepared = await request.app.state.request_boundary.prepare(
            request, body_kind="build", cookie_mode="required",
        )
    except BoundaryRejection as rejected:
        return error_response(rejected)

    session_id = prepared.cookie.value
    payload = prepared.body
    assert session_id is not None and isinstance(payload, BuildPayload)
    admission = await request.app.state.admission.reserve_build(
        session_id=session_id, client_ip=prepared.client_ip,
    )
    if isinstance(admission, AdmissionRejection):
        return _failure(
            prepared.request_id, code=admission.code,
            detail_code=admission.detail_code,
            message=_ADMISSION_MESSAGES[admission.code], retryable=True,
            status=admission.status_code, retry_after=admission.retry_after,
        )

    started_execution = asyncio.Event()
    owner = asyncio.create_task(_execute_owned(
        request.app, permit=admission, payload=payload,
        session_id=session_id, request_id=prepared.request_id,
        started_execution=started_execution,
    ), name=f"exact_orb_build_{prepared.request_id}")
    owners: set[asyncio.Task[Any]] = request.app.state.build_owners
    owners.add(owner)
    watchdog = asyncio.create_task(_watch_owner(
        request.app, owner,
        request.app.state.scheduler.now() + request.app.state.settings.build_timeout_seconds,
    ))
    watchdogs: set[asyncio.Task[Any]] = request.app.state.build_watchdogs
    watchdogs.add(watchdog)

    def forget_owner(task: asyncio.Task[Any]) -> None:
        owners.discard(task)
        if task.cancelled() and not started_execution.is_set():
            # A task cancelled before its first coroutine step never enters
            # _execute_owned, so no leaf work exists and the permit is ours.
            release = asyncio.create_task(admission.release())
            owners.add(release)
            release.add_done_callback(owners.discard)
            return
        if not task.cancelled():
            error = task.exception()
            if error is not None:
                _LOG.error(
                    "http_build_owner_failed request_id=%s safe_error=%s",
                    prepared.request_id, type(error).__name__,
                )

    owner.add_done_callback(forget_owner)
    watchdog.add_done_callback(watchdogs.discard)
    disconnect = asyncio.create_task(_listen_disconnect(request))
    try:
        done, _ = await asyncio.wait(
            {owner, watchdog, disconnect}, return_when=asyncio.FIRST_COMPLETED,
        )
        if disconnect in done:
            disconnect.result()
            owner.cancel()
            try:
                await asyncio.shield(owner)
            except asyncio.CancelledError:
                pass
            raise ClientDisconnected
        if owner in done or (watchdog in done and not watchdog.result()):
            try:
                result = owner.result()
            except asyncio.CancelledError:
                raise ClientDisconnected from None
            return _map_result(result, request_id=prepared.request_id, session_id=session_id)
        return _failure(
            prepared.request_id, code="BUILD_TIMEOUT",
            detail_code="OPERATION_DEADLINE_EXCEEDED",
            message="Расчёт не завершился вовремя. Проверьте текущую карту.",
            retryable=False, status=504, retry_after=5,
        )
    except asyncio.CancelledError:
        owner.cancel()
        raise
    except ClientDisconnected:
        raise
    except Exception as exc:
        _LOG.error(
            "http_unhandled_exception request_id=%s safe_error=%s",
            prepared.request_id, type(exc).__name__,
        )
        return _internal(prepared.request_id, session_id=session_id)
    finally:
        disconnect.cancel()
        await asyncio.gather(disconnect, return_exceptions=True)
