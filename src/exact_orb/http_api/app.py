"""Process-local HTTP composition, health and session reaper ownership."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import inspect
from ipaddress import ip_network
import logging
from math import isfinite
from numbers import Real
from time import monotonic
from typing import Any, Protocol, TypeVar
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from exact_orb.http_api.request_boundary import (
    BoundaryRejection, ClientDisconnected, RequestBoundary, error_response,
)
from exact_orb.http_api.routes.places import router as places_router
from exact_orb.http_api.routes.session import router as session_router


_LOG = logging.getLogger("exact_orb.http_api")
_T = TypeVar("_T")


class HttpAppConfigurationError(ValueError):
    """HTTP settings or required runtime metadata are invalid."""


class Scheduler(Protocol):
    def now(self) -> float: ...

    async def wait_until(self, deadline: float) -> None: ...


class MonotonicScheduler:
    """Production implementation of the shared absolute-deadline seam."""

    def now(self) -> float:
        return monotonic()

    async def wait_until(self, deadline: float) -> None:
        while (remaining := deadline - self.now()) > 0:
            await asyncio.sleep(remaining)


class LifecyclePhase(str, Enum):
    STARTING = "starting"
    READY = "ready"
    SHUTTING_DOWN = "shutting_down"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"


class _DisconnectedResponse(Response):
    """Finish the ASGI call after a peer disconnect without sending a response."""

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        return None


@dataclass(frozen=True, slots=True)
class _AppSettings:
    allowed_origins: tuple[str, ...]
    trusted_proxy_cidrs: tuple[str, ...]
    public_origin: str
    body_timeout_seconds: float
    build_timeout_seconds: float
    shutdown_grace_seconds: float
    reaper_interval_seconds: float
    max_body_bytes: int
    expose_schema: bool


def _positive_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise HttpAppConfigurationError(f"{name} must be a positive finite number")
    result = float(value)
    if not isfinite(result) or result <= 0:
        raise HttpAppConfigurationError(f"{name} must be a positive finite number")
    return result


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HttpAppConfigurationError(f"{name} must be a positive integer")
    return value


def _https_origin(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise HttpAppConfigurationError(f"{name} must be an HTTPS origin")
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme == "https" and bool(parsed.hostname)
            and parsed.port != 0 and not parsed.username and not parsed.password
            and not parsed.path and not parsed.query and not parsed.fragment
            and value == f"https://{parsed.netloc}"
            and "*" not in parsed.netloc
            and not any(character.isspace() for character in parsed.netloc)
        )
    except ValueError as exc:
        raise HttpAppConfigurationError(f"{name} must be an HTTPS origin") from exc
    if not valid:
        raise HttpAppConfigurationError(f"{name} must be an HTTPS origin")
    return value


def _validate_settings(settings: object) -> _AppSettings:
    try:
        origins = settings.allowed_origins
        proxies = settings.trusted_proxy_cidrs
        public_origin = settings.public_origin
        body_timeout = settings.body_timeout_seconds
        build_timeout = settings.build_timeout_seconds
        shutdown_grace = settings.shutdown_grace_seconds
        reaper_interval = settings.reaper_interval_seconds
        max_body = settings.max_body_bytes
        expose_schema = settings.expose_schema
    except AttributeError as exc:
        raise HttpAppConfigurationError("HTTP settings are incomplete") from exc

    if not isinstance(origins, tuple):
        raise HttpAppConfigurationError("allowed_origins must be a tuple")
    checked_origins = tuple(_https_origin(origin, "allowed_origins") for origin in origins)
    if len(set(checked_origins)) != len(checked_origins):
        raise HttpAppConfigurationError("allowed_origins must be unique")
    if not isinstance(proxies, tuple):
        raise HttpAppConfigurationError("trusted_proxy_cidrs must be a tuple")
    for cidr in proxies:
        if not isinstance(cidr, str):
            raise HttpAppConfigurationError("trusted_proxy_cidrs contains an invalid CIDR")
        try:
            ip_network(cidr, strict=False)
        except ValueError as exc:
            raise HttpAppConfigurationError("trusted_proxy_cidrs contains an invalid CIDR") from exc
    checked_origin = _https_origin(public_origin, "public_origin")
    if not isinstance(expose_schema, bool):
        raise HttpAppConfigurationError("expose_schema must be boolean")
    return _AppSettings(
        allowed_origins=checked_origins,
        trusted_proxy_cidrs=proxies,
        public_origin=checked_origin,
        body_timeout_seconds=_positive_seconds(body_timeout, "body_timeout_seconds"),
        build_timeout_seconds=_positive_seconds(build_timeout, "build_timeout_seconds"),
        shutdown_grace_seconds=_positive_seconds(shutdown_grace, "shutdown_grace_seconds"),
        reaper_interval_seconds=_positive_seconds(reaper_interval, "reaper_interval_seconds"),
        max_body_bytes=_positive_int(max_body, "max_body_bytes"),
        expose_schema=expose_schema,
    )


def _validate_limiter_policy(policy: object | None) -> None:
    if policy is None:
        return
    try:
        _positive_int(policy.active_builds, "active_builds")
        for name in (
            "session_create_ip", "build_session_hourly", "build_session_daily",
            "build_ip_hourly", "build_ip_daily", "place_search_ip",
        ):
            window = getattr(policy, name)
            _positive_int(window.limit, f"{name}.limit")
            _positive_seconds(window.seconds, f"{name}.seconds")
    except AttributeError as exc:
        raise HttpAppConfigurationError("limiter_policy is incomplete") from exc


async def _open(factory: Callable[[], _T | Awaitable[_T]]) -> _T:
    value = factory()
    if inspect.isawaitable(value):
        return await value
    return value


async def _reaper(
    runtime: Any,
    *,
    utc_clock: Callable[[], datetime],
    scheduler: Scheduler,
    interval: float,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        deadline = scheduler.now() + interval
        waiter = asyncio.create_task(scheduler.wait_until(deadline))
        stopper = asyncio.create_task(stop.wait())
        try:
            done, _ = await asyncio.wait({waiter, stopper}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in (waiter, stopper):
                if not task.done():
                    task.cancel()
            await asyncio.gather(waiter, stopper, return_exceptions=True)
        if stop.is_set():
            return
        if waiter not in done:
            continue
        waiter.result()

        run_id = str(uuid4())
        started = scheduler.now()
        _LOG.info("session_reaper_started reaper_run_id=%s schedule=%s", run_id, deadline)
        try:
            deleted = await runtime.reap_expired(now=utc_clock())
        except Exception as exc:
            _LOG.warning(
                "session_reaper_finished reaper_run_id=%s schedule=%s outcome=failed "
                "safe_error=%s duration_seconds=%s",
                run_id, deadline, type(exc).__name__, scheduler.now() - started,
            )
        else:
            _LOG.info(
                "session_reaper_finished reaper_run_id=%s schedule=%s outcome=success "
                "deleted_count=%s duration_seconds=%s",
                run_id, deadline, deleted, scheduler.now() - started,
            )


def create_app(
    *,
    settings: object,
    runtime_factory: Callable[[Any], Any],
    catalog_factory: Callable[[], Any],
    utc_clock: Callable[[], datetime],
    scheduler: Scheduler,
    limiter_policy: object | None = None,
) -> FastAPI:
    """Build one ASGI app; resources are opened and closed by its lifespan."""

    config = _validate_settings(settings)
    _validate_limiter_policy(limiter_policy)
    if not callable(runtime_factory) or not callable(catalog_factory):
        raise HttpAppConfigurationError("runtime and catalog factories must be callable")
    if not callable(utc_clock) or not callable(getattr(scheduler, "now", None)) or not callable(getattr(scheduler, "wait_until", None)):
        raise HttpAppConfigurationError("UTC clock and scheduler are required")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.lifecycle_phase = LifecyclePhase.STARTING
        app.state.shutdown_started = asyncio.Event()
        async with AsyncExitStack() as resources:
            catalog = await _open(catalog_factory)
            resources.push_async_callback(catalog.aclose)
            runtime = await _open(lambda: runtime_factory(catalog))
            resources.push_async_callback(runtime.aclose)
            if not isinstance(getattr(runtime, "calculation_version", None), str) or not runtime.calculation_version:
                raise HttpAppConfigurationError("runtime requires CalculationVersion")

            app.state.catalog = catalog
            app.state.runtime = runtime
            stop_reaper = asyncio.Event()
            reaper_task = asyncio.create_task(_reaper(
                runtime, utc_clock=utc_clock, scheduler=scheduler,
                interval=config.reaper_interval_seconds, stop=stop_reaper,
            ), name="exact_orb_session_reaper")

            def mark_reaper_failure(task: asyncio.Task[None]) -> None:
                if task.cancelled():
                    return
                error = task.exception()
                if error is not None and app.state.lifecycle_phase == LifecyclePhase.READY:
                    app.state.lifecycle_phase = LifecyclePhase.UNHEALTHY
                    _LOG.error("session_reaper_task_failed safe_error=%s", type(error).__name__)

            reaper_task.add_done_callback(mark_reaper_failure)
            app.state.lifecycle_phase = LifecyclePhase.READY
            try:
                yield
            finally:
                app.state.lifecycle_phase = LifecyclePhase.SHUTTING_DOWN
                app.state.shutdown_started.set()
                _LOG.info("http_shutdown_started")
                stop_reaper.set()
                try:
                    await reaper_task
                except Exception as exc:
                    # The task failure was observed by mark_reaper_failure while
                    # READY; shutdown still has to release its owned resources.
                    _LOG.warning(
                        "session_reaper_shutdown_join_failed safe_error=%s",
                        type(exc).__name__,
                    )
        app.state.lifecycle_phase = LifecyclePhase.STOPPED
        _LOG.info("http_shutdown_finished outcome=resources_released")

    app = FastAPI(
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json" if config.expose_schema else None,
    )
    app.state.settings = config
    app.state.scheduler = scheduler
    app.state.utc_clock = utc_clock
    app.state.limiter_policy = limiter_policy
    app.state.lifecycle_phase = LifecyclePhase.STARTING
    app.state.request_boundary = RequestBoundary(
        allowed_origins=config.allowed_origins,
        public_origin=config.public_origin,
        trusted_proxy_cidrs=config.trusted_proxy_cidrs,
        body_timeout_seconds=config.body_timeout_seconds,
        max_body_bytes=config.max_body_bytes,
        scheduler=scheduler,
        is_ready=lambda: app.state.lifecycle_phase == LifecyclePhase.READY,
    )

    def request_id_for(request: Request) -> str:
        request_id = getattr(request.state, "request_id", None)
        if request_id is None:
            request_id = str(uuid4())
            request.state.request_id = request_id
        return request_id

    def safe_error(request: Request, code: str) -> Response:
        rejection = BoundaryRejection(code)
        rejection.request_id = request_id_for(request)
        return error_response(rejection)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception(request: Request, exc: StarletteHTTPException) -> Response:
        if exc.status_code == 404:
            return safe_error(request, "NOT_FOUND")
        if exc.status_code == 405:
            response = safe_error(request, "METHOD_NOT_ALLOWED")
            for name, value in (exc.headers or {}).items():
                if name.lower() == "allow":
                    response.headers["Allow"] = value
                    break
            return response
        return safe_error(request, "INTERNAL_FAILURE")

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception(request: Request, _exc: RequestValidationError) -> Response:
        return safe_error(request, "INVALID_REQUEST")

    @app.exception_handler(ClientDisconnected)
    async def client_disconnected(_request: Request, _exc: ClientDisconnected) -> Response:
        return _DisconnectedResponse()

    @app.exception_handler(Exception)
    async def unexpected_exception(request: Request, exc: Exception) -> Response:
        request_id = request_id_for(request)
        _LOG.error("http_unhandled_exception request_id=%s safe_error=%s", request_id, type(exc).__name__)
        return safe_error(request, "INTERNAL_FAILURE")

    def health_response(status: int) -> Response:
        return Response(
            status_code=status,
            headers={"Cache-Control": "no-store", "X-Request-ID": str(uuid4())},
        )

    @app.api_route("/health/live", methods=["GET", "HEAD"], include_in_schema=False)
    async def live() -> Response:
        return health_response(503 if app.state.lifecycle_phase == LifecyclePhase.UNHEALTHY else 200)

    @app.api_route("/health/ready", methods=["GET", "HEAD"], include_in_schema=False)
    async def ready() -> Response:
        return health_response(200 if app.state.lifecycle_phase == LifecyclePhase.READY else 503)

    app.include_router(session_router)
    app.include_router(places_router)

    return app
