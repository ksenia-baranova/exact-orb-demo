"""AS-HTTP-23..27/29: deterministic receive, ownership and lifecycle contracts.

App-dependent cases are intentionally RED until prompts 05/06/08-12. No network,
wall-clock sleeps, or production route stubs are used.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import logging
from pathlib import Path
import runpy
import threading
from typing import Any
from urllib.parse import quote
from uuid import UUID

import pytest

from exact_orb.birth.adapters import sqlite as place_sqlite
from exact_orb.birth.adapters.sqlite import SqlitePlaceCatalog
from exact_orb.birth.places import PlaceCatalogUnavailableError
from exact_orb.session.adapters import sqlite as session_sqlite
from exact_orb.session.errors import StateReadError
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import new_session
from tests.http_api.admission_cases import SmallLimiterPolicy, WindowLimit
from tests.http_api.build_support import (
    BlockedOrchestrator, TerminalHeldOrchestrator,
    real_orchestrator as _real_orchestrator,
)
from tests.http_api.conftest import ForbiddenCatalog, RuntimeSpy, ScriptedContext, http_settings
from tests.http_api.shared import (
    COOKIE, SESSION_ID, ScriptedCatalog, ScriptedOrchestrator,
    application_failure as _application_failure, build as _build,
    cookie as _cookie, input_required as _input_required,
)


pytestmark = pytest.mark.asyncio

BODY = b'{"birth_date":"1985-09-02","birth_time":"00:45","place_id":"524901"}'
BOOTSTRAP_BODY = b"{}"
GUARD = 3.0  # Only a hang guard; scheduler/Event/barrier establishes order.


def _create_app(*, runtime: object, catalog: object | None, utc_clock,
                scheduler, settings: object | None = None,
                limiter_policy: object | None = None):
    # Local import keeps collection and pure controls independent of transport.
    from exact_orb.http_api.app import create_app

    return create_app(
        settings=settings if settings is not None else http_settings(),
        runtime_factory=lambda opened_catalog: runtime,
        catalog_factory=lambda: catalog if catalog is not None else ForbiddenCatalog(),
        utc_clock=utc_clock,
        scheduler=scheduler,
        limiter_policy=limiter_policy,
    )


def _scope(method: str, path: str, *,
           headers: list[tuple[bytes, bytes]] | None = None,
           peer: tuple[str, int] = ("127.0.0.1", 12345),
           query: bytes = b"") -> dict[str, Any]:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "scheme": "https",
        "method": method,
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": query,
        "root_path": "",
        "headers": headers or [],
        "client": peer,
        "server": ("testserver", 443),
    }


def _response(messages: list[dict[str, Any]]) -> tuple[int, dict[str, str], bytes]:
    start = [message for message in messages if message["type"] == "http.response.start"]
    assert len(start) == 1
    headers = {name.decode("latin1").lower(): value.decode("latin1")
               for name, value in start[0]["headers"]}
    body = b"".join(message.get("body", b"") for message in messages
                    if message["type"] == "http.response.body")
    return start[0]["status"], headers, body


async def _raw(app: Any, method: str, path: str, *,
               body: bytes = b"",
               headers: list[tuple[bytes, bytes]] | None = None,
               query: bytes = b"",
               peer: tuple[str, int] = ("127.0.0.1", 12345)
               ) -> tuple[int, dict[str, str], bytes]:
    messages: list[dict[str, Any]] = []

    delivered = False

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(_scope(method, path, headers=headers, peer=peer, query=query),
              receive, send)
    return _response(messages)


class RawConversation:
    """Queue-driven ASGI receive, with independent response and disconnect events."""

    def __init__(self, app: Any, scope: dict[str, Any]) -> None:
        self.app = app
        self.scope = scope
        self.incoming: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.messages: list[dict[str, Any]] = []
        self.receive_waiting = asyncio.Event()
        self.received = asyncio.Event()
        self.disconnected = asyncio.Event()
        self.response_started = asyncio.Event()
        self.task: asyncio.Task[None] | None = None

    async def receive(self) -> dict[str, Any]:
        self.receive_waiting.set()
        message = await self.incoming.get()
        self.received.set()
        if message["type"] == "http.disconnect":
            self.disconnected.set()
        return message

    async def send(self, message: dict[str, Any]) -> None:
        self.messages.append(message)
        if message["type"] == "http.response.start":
            self.response_started.set()

    def start(self) -> None:
        assert self.task is None
        self.task = asyncio.create_task(self.app(
            self.scope, self.receive, self.send,
        ))

    def put_body(self, body: bytes, *, more: bool) -> None:
        self.incoming.put_nowait({
            "type": "http.request", "body": body, "more_body": more,
        })

    def disconnect(self) -> None:
        self.incoming.put_nowait({"type": "http.disconnect"})

    async def finish(self) -> None:
        assert self.task is not None
        await asyncio.wait_for(self.task, timeout=GUARD)


async def test_scheduler_control_has_exact_deadline_and_no_wall_clock(scheduler) -> None:
    waiter = asyncio.create_task(scheduler.wait_until(5.0))
    await asyncio.wait_for(scheduler.wait_registered(5.0), timeout=GUARD)
    await scheduler.advance(4.999)
    assert not waiter.done()
    await scheduler.advance(0.001)
    await asyncio.wait_for(waiter, timeout=GUARD)
    assert scheduler.now() == 5.0


async def test_slow_body_uses_first_event_deadline_and_fast_same_size_succeeds(
    app_client, runtime: RuntimeSpy, context: ScriptedContext, scheduler
) -> None:
    async with app_client(runtime) as client:
        exchange = RawConversation(client.asgi_app, _scope(
            "POST", "/session/bootstrap",
            headers=[(b"content-type", b"application/json")],
        ))
        exchange.start()
        await asyncio.wait_for(exchange.receive_waiting.wait(), timeout=GUARD)
        await scheduler.advance(100)
        assert not exchange.response_started.is_set()
        exchange.put_body(b"{", more=True)
        await asyncio.wait_for(exchange.received.wait(), timeout=GUARD)
        await asyncio.wait_for(scheduler.wait_registered(105.0), timeout=GUARD)
        assert context.create_calls == []
        assert not exchange.response_started.is_set()
        await scheduler.advance(5)
        await exchange.finish()
        status, headers, payload = _response(exchange.messages)
        assert status == 408
        assert json.loads(payload)["code"] == "REQUEST_TIMEOUT"
        assert headers["retry-after"] == "1"
        assert headers["cache-control"] == "no-store"
        assert UUID(headers["x-request-id"])
        assert context.create_calls == []

        fast = await _raw(
            client.asgi_app, "POST", "/session/bootstrap",
            headers=[(b"content-type", b"application/json")],
            body=BOOTSTRAP_BODY,
        )
        assert fast[0] == 200
        assert len(context.create_calls) == 1


class ReaperRuntime(RuntimeSpy):
    def __init__(self, context: object) -> None:
        super().__init__(context)
        self.entered = asyncio.Condition()
        self.calls = 0
        self.active = 0
        self.max_active = 0
        self.release_first = asyncio.Event()
        self.release_fourth = asyncio.Event()
        self.events: list[tuple[str, int]] = []

    async def reap_expired(self, *, now=None) -> int:
        self.calls += 1
        number = self.calls
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.events.append(("start", number))
        async with self.entered:
            self.entered.notify_all()
        try:
            if number == 1:
                await self.release_first.wait()
            elif number == 2:
                raise StateReadError("SESSION_SQLITE_READ_FAILED")
            elif number == 3:
                raise RuntimeError("unexpected reaper failure")
            elif number == 4:
                await self.release_fourth.wait()
            return number
        finally:
            self.active -= 1
            self.events.append(("finish", number))

    async def wait_calls(self, count: int) -> None:
        async with self.entered:
            await self.entered.wait_for(lambda: self.calls >= count)


async def test_reaper_waits_from_completion_survives_failures_and_shutdown_waits(
    context: ScriptedContext, utc_clock, scheduler, caplog
) -> None:
    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    runtime = ReaperRuntime(context)
    catalog = ScriptedCatalog()
    app = _create_app(runtime=runtime, catalog=catalog,
                      utc_clock=utc_clock, scheduler=scheduler)
    lifespan = app.router.lifespan_context(app)
    await lifespan.__aenter__()
    shutdown: asyncio.Task[object] | None = None
    try:
        await asyncio.wait_for(scheduler.wait_registered(900), timeout=GUARD)
        await scheduler.advance(900)
        await asyncio.wait_for(runtime.wait_calls(1), timeout=GUARD)
        assert runtime.active == 1
        await scheduler.advance(60)
        assert runtime.calls == 1
        runtime.release_first.set()
        await asyncio.wait_for(scheduler.wait_registered(1860), timeout=GUARD)
        assert runtime.max_active == 1
        await scheduler.advance(900)
        await asyncio.wait_for(runtime.wait_calls(2), timeout=GUARD)
        await asyncio.wait_for(scheduler.wait_registered(2760), timeout=GUARD)
        await scheduler.advance(900)
        await asyncio.wait_for(runtime.wait_calls(3), timeout=GUARD)
        await asyncio.wait_for(scheduler.wait_registered(3660), timeout=GUARD)
        await scheduler.advance(900)
        await asyncio.wait_for(runtime.wait_calls(4), timeout=GUARD)
        shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
        await asyncio.wait_for(app.state.shutdown_started.wait(), timeout=GUARD)
        assert (await _raw(app, "GET", "/health/ready"))[0] == 503
        assert not runtime.closed
        assert not catalog.closed
        assert not shutdown.done()
        runtime.release_fourth.set()
        await asyncio.wait_for(shutdown, timeout=GUARD)
        assert runtime.max_active == 1
        assert runtime.calls == 4
        assert runtime.active == 0
        assert runtime.closed and catalog.closed
        assert runtime.events == [
            ("start", 1), ("finish", 1), ("start", 2), ("finish", 2),
            ("start", 3), ("finish", 3), ("start", 4), ("finish", 4),
        ]
        reaper_logs = [
            record for record in caplog.records
            if record.name.startswith("exact_orb.http_api")
            and record.getMessage().startswith("session_reaper_")
        ]
        assert sum("session_reaper_started" in r.getMessage() for r in reaper_logs) == 4
        assert sum("session_reaper_finished" in r.getMessage() for r in reaper_logs) == 4
        assert sum(r.levelno == logging.WARNING for r in reaper_logs) >= 2
    finally:
        runtime.release_first.set()
        runtime.release_fourth.set()
        if shutdown is None:
            await lifespan.__aexit__(None, None, None)
        elif not shutdown.done():
            await asyncio.wait_for(shutdown, timeout=GUARD)


async def test_reaper_scheduler_failure_does_not_abort_shutdown_cleanup(
    utc_clock, caplog,
) -> None:
    class FailingScheduler:
        def __init__(self) -> None:
            self.entered = asyncio.Event()
            self.release = asyncio.Event()

        def now(self) -> float:
            return 0.0

        async def wait_until(self, deadline: float) -> None:
            self.entered.set()
            await self.release.wait()
            raise RuntimeError("private scheduler failure")

    class FailureSignal(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.reached = asyncio.Event()

        def emit(self, record: logging.LogRecord) -> None:
            if record.getMessage().startswith("session_reaper_task_failed "):
                self.reached.set()

    from exact_orb.http_api.app import LifecyclePhase

    scheduler = FailingScheduler()
    runtime = RuntimeSpy(ScriptedContext(utc_clock))
    catalog = ScriptedCatalog()
    app = _create_app(runtime=runtime, catalog=catalog,
                      utc_clock=utc_clock, scheduler=scheduler)
    logger = logging.getLogger("exact_orb.http_api")
    signal = FailureSignal()
    logger.addHandler(signal)
    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    lifespan = app.router.lifespan_context(app)
    try:
        await lifespan.__aenter__()
        await asyncio.wait_for(scheduler.entered.wait(), timeout=GUARD)
        scheduler.release.set()
        await asyncio.wait_for(signal.reached.wait(), timeout=GUARD)
        await asyncio.wait_for(lifespan.__aexit__(None, None, None), timeout=GUARD)
        assert app.state.lifecycle_phase == LifecyclePhase.STOPPED
        assert runtime.closed and catalog.closed
        messages = [record.getMessage() for record in caplog.records]
        assert any(message.startswith("session_reaper_shutdown_join_failed ")
                   for message in messages)
        assert any(message.startswith(
            "http_shutdown_finished outcome=resources_released active_count=0 duration_ms="
        )
                   for message in messages)
        assert all("private scheduler failure" not in message for message in messages)
    finally:
        scheduler.release.set()
        logger.removeHandler(signal)


@pytest.mark.parametrize("changes", (
    {"public_origin": "http://testserver"},
    {"allowed_origins": ("*",)},
    {"allowed_origins": ("https://*",)},
    {"public_origin": "https://bad host"},
    {"trusted_proxy_cidrs": ("not-a-cidr",)},
    {"body_timeout_seconds": 0},
    {"build_timeout_seconds": 0},
    {"shutdown_grace_seconds": 0},
    {"reaper_interval_seconds": 0},
    {"max_body_bytes": 0},
))
async def test_invalid_settings_fail_before_any_resource_opens(
    changes: dict[str, object], utc_clock, scheduler
) -> None:
    opened: list[str] = []

    def make_catalog() -> object:
        opened.append("catalog")
        return ForbiddenCatalog()

    def make_runtime(opened_catalog: object) -> object:
        opened.append("runtime")
        return RuntimeSpy(ScriptedContext(utc_clock))

    from exact_orb.http_api.app import HttpAppConfigurationError, create_app

    with pytest.raises(HttpAppConfigurationError):
        app = create_app(
            settings=http_settings(**changes),
            runtime_factory=make_runtime,
            catalog_factory=make_catalog,
            utc_clock=utc_clock,
            scheduler=scheduler,
            limiter_policy=None,
        )
        async with app.router.lifespan_context(app):
            pytest.fail("invalid settings accepted")
    assert opened == []


class CloseSpyCatalog(ScriptedCatalog):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events

    async def aclose(self) -> None:
        self.events.append("catalog.close")
        await super().aclose()


class CloseSpyRuntime(RuntimeSpy):
    def __init__(self, context: object, events: list[str]) -> None:
        super().__init__(context)
        self.events = events

    async def aclose(self) -> None:
        self.events.append("runtime.close")
        await super().aclose()


async def test_runtime_startup_failure_closes_previously_opened_catalog(
    utc_clock, scheduler
) -> None:
    from exact_orb.http_api.app import create_app

    events: list[str] = []
    catalog = CloseSpyCatalog(events)

    def make_catalog() -> object:
        events.append("catalog.open")
        return catalog

    def fail_runtime(opened_catalog: object) -> object:
        assert opened_catalog is catalog
        events.append("runtime.open")
        raise RuntimeError("runtime composition failed")

    app = create_app(
        settings=http_settings(), runtime_factory=fail_runtime,
        catalog_factory=make_catalog, utc_clock=utc_clock,
        scheduler=scheduler, limiter_policy=None,
    )
    with pytest.raises(RuntimeError, match="runtime composition failed"):
        async with app.router.lifespan_context(app):
            pytest.fail("startup accepted a failed dependency")
    assert events == ["catalog.open", "runtime.open", "catalog.close"]
    assert catalog.closed


async def test_async_runtime_factory_reuses_open_catalog_and_closes_in_reverse_order(
    utc_clock, scheduler
) -> None:
    from exact_orb.http_api.app import create_app

    events: list[str] = []
    catalog = CloseSpyCatalog(events)
    runtime = CloseSpyRuntime(ScriptedContext(utc_clock), events)

    async def make_catalog() -> object:
        events.append("catalog.open")
        return catalog

    async def make_runtime(opened_catalog: object) -> object:
        assert opened_catalog is catalog
        assert events == ["catalog.open"]
        events.append("runtime.open")
        return runtime

    app = create_app(
        settings=http_settings(), runtime_factory=make_runtime,
        catalog_factory=make_catalog, utc_clock=utc_clock,
        scheduler=scheduler,
    )
    async with app.router.lifespan_context(app):
        assert app.state.catalog is catalog
        assert app.state.runtime is runtime
        assert (await _raw(app, "GET", "/health/ready"))[0] == 200
    assert events == [
        "catalog.open", "runtime.open", "runtime.close", "catalog.close",
    ]


async def test_missing_calculation_version_fails_startup_and_closes_resources(
    utc_clock, scheduler
) -> None:
    from exact_orb.http_api.app import HttpAppConfigurationError, create_app

    events: list[str] = []
    catalog = CloseSpyCatalog(events)
    runtime = CloseSpyRuntime(ScriptedContext(utc_clock), events)
    runtime.calculation_version = ""
    app = create_app(
        settings=http_settings(), runtime_factory=lambda opened_catalog: runtime,
        catalog_factory=lambda: catalog, utc_clock=utc_clock,
        scheduler=scheduler, limiter_policy=None,
    )
    with pytest.raises(HttpAppConfigurationError):
        async with app.router.lifespan_context(app):
            pytest.fail("startup accepted absent CalculationVersion")
    assert runtime.closed and catalog.closed
    assert events == ["runtime.close", "catalog.close"]


async def test_catalog_startup_failure_never_opens_runtime(
    utc_clock, scheduler
) -> None:
    from exact_orb.http_api.app import create_app

    opened: list[str] = []

    def fail_catalog() -> object:
        opened.append("catalog")
        raise PlaceCatalogUnavailableError("catalog cannot open")

    def make_runtime(opened_catalog: object) -> object:
        opened.append("runtime")
        return RuntimeSpy(ScriptedContext(utc_clock))

    app = create_app(
        settings=http_settings(), runtime_factory=make_runtime,
        catalog_factory=fail_catalog, utc_clock=utc_clock,
        scheduler=scheduler, limiter_policy=None,
    )
    with pytest.raises(PlaceCatalogUnavailableError, match="catalog cannot open"):
        async with app.router.lifespan_context(app):
            pytest.fail("startup accepted failed catalog")
    assert opened == ["catalog"]


async def test_invalid_admission_limit_fails_before_resources_open(
    utc_clock, scheduler
) -> None:
    from exact_orb.http_api.app import HttpAppConfigurationError, create_app

    opened: list[str] = []
    with pytest.raises(HttpAppConfigurationError):
        app = create_app(
            settings=http_settings(),
            runtime_factory=lambda opened_catalog: opened.append("runtime"),
            catalog_factory=lambda: opened.append("catalog"),
            utc_clock=utc_clock, scheduler=scheduler,
            limiter_policy=replace(SmallLimiterPolicy(), active_builds=0),
        )
        async with app.router.lifespan_context(app):
            pytest.fail("startup accepted zero build capacity")
    assert opened == []


async def test_health_tracks_startup_shutdown_and_does_not_touch_dependencies(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    from exact_orb.http_api.app import LifecyclePhase

    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog) as client:
        for path in ("/health/live", "/health/ready"):
            get = await client.get(path)
            head = await client.head(path)
            assert get.status_code == head.status_code == 200
            assert get.headers["Cache-Control"] == head.headers["Cache-Control"] == "no-store"
            assert UUID(get.headers["X-Request-ID"])
            assert UUID(head.headers["X-Request-ID"])
            assert head.content == b""
        assert catalog.calls == []
        assert context.load_calls == context.create_calls == []
        client.asgi_app.state.lifecycle_phase = LifecyclePhase.UNHEALTHY
        assert (await client.get("/health/live")).status_code == 503
        assert (await client.get("/health/ready")).status_code == 503
    assert runtime.closed and catalog.closed

    stopping = RuntimeSpy(context)
    stopping_catalog = ScriptedCatalog()
    async with app_client(stopping, catalog=stopping_catalog,
                          during_shutdown=True) as client:
        assert (await client.get("/health/live")).status_code == 200
        ready = await client.get("/health/ready")
        head = await client.head("/health/ready")
        assert ready.status_code == head.status_code == 503
        assert head.content == b""
        assert UUID(ready.headers["X-Request-ID"])
        assert stopping_catalog.calls == []
        assert context.load_calls == context.create_calls == []


async def test_health_ready_and_shutdown_gate_have_real_business_control(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog) as client:
        ready = await client.get("/health/ready")
        live = await client.get("/health/live")
        assert ready.status_code == live.status_code == 200
        control = await client.get("/places", params={"query": "Москва"})
        assert control.status_code == 200
        assert catalog.calls == [("Москва", 10)]
    assert runtime.closed and catalog.closed
    async with app_client(RuntimeSpy(context), catalog=ScriptedCatalog(),
                          during_shutdown=True) as client:
        assert (await client.get("/health/ready")).status_code == 503
        denied = await client.get("/places", params={"query": "Москва"})
        assert denied.status_code == 503
        assert denied.json()["code"] == "SERVICE_SHUTTING_DOWN"
        assert denied.headers["Retry-After"] == "30"
        head = await client.head("/health/ready")
        assert head.status_code == 503
        assert head.content == b""


async def test_route_method_head_options_and_hidden_schema_are_exact(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog) as client:
        unknown = await client.get("/not-a-route")
        assert unknown.status_code == 404
        assert unknown.headers["Cache-Control"] == "no-store"
        assert isinstance(unknown.json(), dict)

        for path, allowed in (
            ("/session/bootstrap", "POST"),
            ("/charts/natal", "POST"),
            ("/charts/current", "GET"),
            ("/places", "GET"),
        ):
            wrong = await client.request(
                "GET" if allowed == "POST" else "POST", path,
            )
            assert wrong.status_code == 405
            assert set(wrong.headers["Allow"].split(", ")) == {allowed}
            head = await client.head(path)
            assert head.status_code == 405
            assert head.content == b""
            assert set(head.headers["Allow"].split(", ")) == {allowed}
            options = await client.options(path)
            assert options.status_code == 405
            assert set(options.headers["Allow"].split(", ")) == {allowed}

        for path in ("/health/live", "/health/ready"):
            get = await client.get(path)
            head = await client.head(path)
            assert get.status_code == head.status_code == 200
            assert head.content == b""
            assert head.headers["Cache-Control"] == get.headers["Cache-Control"]
            assert UUID(head.headers["X-Request-ID"])
        for path in ("/docs", "/redoc", "/openapi.json"):
            assert (await client.get(path)).status_code == 404

        schema = client.asgi_app.openapi()
        assert all(path in schema["paths"] for path in (
            "/session/bootstrap", "/charts/current", "/places", "/charts/natal",
        ))
        assert (await client.get("/places", params={"query": "Москва"})).status_code == 200
        assert catalog.calls == [("Москва", 10)]
    assert context.load_calls == context.create_calls == []


async def test_local_schema_flag_exposes_only_explicitly_enabled_route(
    runtime: RuntimeSpy, utc_clock, scheduler
) -> None:
    app = _create_app(
        runtime=runtime, catalog=ScriptedCatalog(),
        utc_clock=utc_clock, scheduler=scheduler,
        settings=http_settings(expose_schema=True),
    )
    async with app.router.lifespan_context(app):
        status, headers, body = await _raw(app, "GET", "/openapi.json")
        assert status == 200
        assert headers["cache-control"] == "no-store"
        assert "/charts/natal" in json.loads(body)["paths"]


@pytest.mark.parametrize("bad_headers", (
    [(b"x-forwarded-for", b"bad-hostname"), (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1:1234"), (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"2001:db8::1%eth0"), (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1,,198.51.100.2"),
     (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1, " * 10 + b"198.51.100.2"),
     (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1")],
    [(b"x-forwarded-for", b"198.51.100.1"), (b"x-forwarded-proto", b"http")],
    [(b"x-forwarded-for", b"198.51.100.1"),
     (b"x-forwarded-for", b"198.51.100.2"),
     (b"x-forwarded-proto", b"https")],
))
async def test_malformed_trusted_forwarding_stops_before_catalog_and_quota(
    bad_headers: list[tuple[bytes, bytes]], app_client, runtime: RuntimeSpy
) -> None:
    catalog = ScriptedCatalog()
    policy = replace(SmallLimiterPolicy(), place_search_ip=WindowLimit(1, 7))
    peer = ("10.0.0.2", 12345)
    query = b"query=" + quote("Москва").encode("ascii")
    async with app_client(runtime, catalog=catalog, limiter_policy=policy,
                          trusted_proxy_cidrs=("10.0.0.0/8",)) as client:
        bad = await _raw(client.asgi_app, "GET", "/places", query=query,
                         headers=bad_headers, peer=peer)
        assert bad[0] == 400
        assert json.loads(bad[2])["code"] == "FORWARDED_HEADER_INVALID"
        assert catalog.calls == []
        good_headers = [
            (b"x-forwarded-for", b"198.51.100.7, 10.0.0.1"),
            (b"x-forwarded-proto", b"https"),
        ]
        good = await _raw(client.asgi_app, "GET", "/places", query=query,
                          headers=good_headers, peer=peer)
        assert good[0] == 200
        assert catalog.calls == [("Москва", 10)]


async def test_trusted_chain_and_mapped_ipv6_share_canonical_ip_bucket(
    app_client, runtime: RuntimeSpy
) -> None:
    catalog = ScriptedCatalog()
    policy = replace(SmallLimiterPolicy(), place_search_ip=WindowLimit(1, 7))
    query = b"query=" + quote("Москва").encode("ascii")
    async with app_client(runtime, catalog=catalog, limiter_policy=policy,
                          trusted_proxy_cidrs=("10.0.0.0/8",)) as client:
        first = await _raw(client.asgi_app, "GET", "/places", query=query,
                           peer=("10.0.0.2", 1), headers=[
                               (b"x-forwarded-for",
                                b"::ffff:198.51.100.7, 10.0.0.1"),
                               (b"x-forwarded-proto", b"https"),
                           ])
        assert first[0] == 200
        second = await _raw(client.asgi_app, "GET", "/places", query=query,
                            peer=("10.0.0.3", 1), headers=[
                                (b"x-forwarded-for", b"198.51.100.7"),
                                (b"x-forwarded-proto", b"https"),
                            ])
        assert second[0] == 429
        assert json.loads(second[2])["code"] == "PLACE_SEARCH_RATE_LIMITED"
        assert second[1]["retry-after"] == "7"
        assert catalog.calls == [("Москва", 10)]


async def test_untrusted_spoofed_forwarding_uses_each_direct_peer_bucket(
    app_client, runtime: RuntimeSpy
) -> None:
    catalog = ScriptedCatalog()
    policy = replace(SmallLimiterPolicy(), place_search_ip=WindowLimit(1, 7))
    headers = [(b"x-forwarded-for", b"203.0.113.200"),
               (b"x-forwarded-proto", b"http")]
    query = b"query=" + quote("Москва").encode("ascii")
    async with app_client(runtime, catalog=catalog, limiter_policy=policy,
                          trusted_proxy_cidrs=("10.0.0.0/8",)) as client:
        statuses = [
            (await _raw(client.asgi_app, "GET", "/places", headers=headers,
                        query=query, peer=(peer, 12345)))[0]
            for peer in ("198.51.100.1", "198.51.100.2", "198.51.100.1")
        ]
        assert statuses == [200, 200, 429]
        assert catalog.calls == [("Москва", 10), ("Москва", 10)]


@pytest.mark.parametrize("case,status,retry_after", (
    ("ok", 200, None),
    ("origin", 403, None),
    ("session", 409, None),
    ("size", 413, None),
    ("media", 415, None),
    ("schema", 422, None),
    ("rate", 429, "5"),
    ("internal", 500, None),
    ("dependency", 503, "5"),
    ("commit", 503, "1"),
    ("timeout", 504, "5"),
))
async def test_required_headers_matrix_and_exact_retry_after(
    case: str, status: int, retry_after: str | None,
    app_client, runtime: RuntimeSpy, scheduler
) -> None:
    catalog = ScriptedCatalog()
    policy = replace(SmallLimiterPolicy(), place_search_ip=WindowLimit(1, 5))
    held: TerminalHeldOrchestrator | None = None
    if case == "internal":
        catalog.results.append(RuntimeError("internal sentinel"))
    elif case == "dependency":
        catalog.results.append(PlaceCatalogUnavailableError("catalog sentinel"))
    elif case == "timeout":
        held = TerminalHeldOrchestrator(None)
        runtime.orchestrator = held
    elif case == "commit":
        runtime.orchestrator = ScriptedOrchestrator(
            lambda run: _application_failure("commit", run),
        )
    async with app_client(runtime, catalog=catalog, limiter_policy=policy) as client:
        client.headers["X-Request-ID"] = "client-sentinel-id"
        try:
            if case == "ok":
                response = await client.get("/places", params={"query": "Москва"})
            elif case == "origin":
                response = await client.get("/places", params={"query": "Москва"},
                                            headers={"Origin": "https://elsewhere.test"})
            elif case == "session":
                response = await client.get("/charts/current")
            elif case == "size":
                response = await client.post("/session/bootstrap",
                    content=b"x" * (16 * 1024 + 1),
                    headers={"Content-Type": "application/json"})
            elif case == "media":
                response = await client.post("/session/bootstrap",
                    content=BOOTSTRAP_BODY, headers={"Content-Type": "text/plain"})
            elif case == "schema":
                response = await client.post("/session/bootstrap",
                    content=b"{bad", headers={"Content-Type": "application/json"})
            elif case == "rate":
                assert (await client.get("/places",
                                        params={"query": "Москва"})).status_code == 200
                response = await client.get("/places", params={"query": "Москва"})
            elif case in ("internal", "dependency"):
                response = await client.get("/places", params={"query": "Москва"})
            elif case == "commit":
                response = await client.post(
                    "/charts/natal", json=_build(), headers={"Cookie": COOKIE},
                )
            else:
                assert held is not None
                pending = asyncio.create_task(client.post(
                    "/charts/natal", json=_build(), headers={"Cookie": COOKIE}))
                await asyncio.wait_for(held.entered.wait(), timeout=GUARD)
                await asyncio.wait_for(scheduler.wait_registered(30), timeout=GUARD)
                await scheduler.advance(30)
                response = await asyncio.wait_for(pending, timeout=GUARD)
            assert response.status_code == status
            assert response.headers["Cache-Control"] == "no-store"
            assert UUID(response.headers["X-Request-ID"])
            assert response.headers["X-Request-ID"] != "client-sentinel-id"
            if retry_after is None:
                assert "Retry-After" not in response.headers
            else:
                assert response.headers["Retry-After"] == retry_after
        finally:
            if held is not None:
                held.release.set()


def _http_records(caplog, request_id: str) -> list[logging.LogRecord]:
    return [
        record for record in caplog.records
        if record.name.startswith("exact_orb.http_api")
        and f"request_id={request_id}" in record.getMessage()
    ]


def _assert_exchange(records: list[logging.LogRecord], operation: str,
                     result_type: str) -> None:
    messages = [record.getMessage() for record in records]
    sends = [i for i, message in enumerate(messages)
             if message.startswith("http_message ")
             and "direction=send" in message
             and f"operation={operation}" in message]
    receives = [i for i, message in enumerate(messages)
                if message.startswith("http_message ")
                and "direction=receive" in message
                and f"operation={operation}" in message
                and f"message_type={result_type}" in message]
    assert len(sends) == len(receives) == 1
    assert sends[0] < receives[0]
    for index in sends + receives:
        assert "peer=" in messages[index]
        assert "message_type=" in messages[index]


async def test_four_http_sequences_emit_ordered_messages_and_one_safe_terminal(
    app_client, runtime: RuntimeSpy, context: ScriptedContext, caplog
) -> None:
    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    catalog = ScriptedCatalog()
    runtime.orchestrator = ScriptedOrchestrator(_input_required)
    private_session = "Z" * 43
    context.snapshots[private_session] = SessionSnapshot(
        state=new_session(private_session, now=context.clock()), dialog=(), chart=None,
    )
    async with app_client(runtime, catalog=catalog) as client:
        bootstrap = await client.post("/session/bootstrap", json={})
        current = await client.get("/charts/current", headers={
            "Cookie": f"__Host-exact_orb_session={private_session}"})
        places = await _raw(
            client.asgi_app, "GET", "/places",
            query=b"query=SensitivePlaceQueryXYZ",
            peer=("198.51.100.99", 12345),
        )
        build = await client.post("/charts/natal", json=_build(), headers={
            "Cookie": f"__Host-exact_orb_session={private_session}"})
        assert (bootstrap.status_code, current.status_code,
                places[0], build.status_code) == (200, 200, 200, 422)
        assert context.create_calls and private_session in context.load_calls
        assert catalog.calls == [("SensitivePlaceQueryXYZ", 10)]
        assert len(runtime.orchestrator.calls) == 1
        assert str(runtime.orchestrator.calls[0][2].run_id) == build.headers["X-Request-ID"]

    ids = [
        bootstrap.headers["X-Request-ID"], current.headers["X-Request-ID"],
        places[1]["x-request-id"], build.headers["X-Request-ID"],
    ]
    assert len(set(ids)) == 4
    for request_id, method, route in zip(
        ids,
        ("POST", "GET", "GET", "POST"),
        ("/session/bootstrap", "/charts/current", "/places", "/charts/natal"),
    ):
        records = _http_records(caplog, request_id)
        starts = [r for r in records if r.getMessage().startswith("http_request_started ")]
        terminals = [r for r in records
                     if r.getMessage().startswith("http_request_finished ")]
        assert len(starts) == len(terminals) == 1
        assert starts[0].levelno == terminals[0].levelno == logging.INFO
        assert f"method={method}" in starts[0].getMessage()
        assert f"route={route}" in starts[0].getMessage()
        assert caplog.records.index(starts[0]) < caplog.records.index(terminals[0])
    _assert_exchange(_http_records(caplog, ids[0]), "create", "SessionCreated")
    _assert_exchange(_http_records(caplog, ids[1]), "load", "SessionSnapshot")
    _assert_exchange(_http_records(caplog, ids[1]), "session_view", "EmptySessionView")
    _assert_exchange(_http_records(caplog, ids[2]), "search", "PlaceSuggestions")
    _assert_exchange(_http_records(caplog, ids[3]), "reserve", "AdmissionPermit")
    _assert_exchange(_http_records(caplog, ids[3]), "execute", "ApplicationInputRequired")
    _assert_exchange(_http_records(caplog, ids[3]), "release", "AdmissionReleased")
    assert all(f"run_id={ids[3]}" in record.getMessage()
               for record in _http_records(caplog, ids[3])
               if record.getMessage().startswith("http_message "))
    info = "\n".join(record.getMessage() for record in caplog.records
                     if record.name.startswith("exact_orb.http_api")
                     and record.levelno == logging.INFO)
    for sentinel in (private_session, "198.51.100.99", "1985-09-02",
                     "SensitivePlaceQueryXYZ"):
        assert sentinel not in info


async def test_5xx_timeout_and_disconnect_have_one_warning_terminal_each(
    app_client, runtime: RuntimeSpy, caplog, scheduler
) -> None:
    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    catalog = ScriptedCatalog()
    catalog.results.append(PlaceCatalogUnavailableError("private path"))
    held = TerminalHeldOrchestrator(None)
    runtime.orchestrator = held
    async with app_client(runtime, catalog=catalog) as client:
        failure = await client.get("/places", params={"query": "Москва"})
        assert failure.status_code == 503
        catalog.results.append(RuntimeError("private unexpected failure"))
        unexpected = await client.get("/places", params={"query": "Москва"})
        assert unexpected.status_code == 500
        request = asyncio.create_task(client.post(
            "/charts/natal", json=_build(), headers={"Cookie": COOKIE}))
        try:
            await asyncio.wait_for(held.entered.wait(), timeout=GUARD)
            await asyncio.wait_for(scheduler.wait_registered(30), timeout=GUARD)
            await scheduler.advance(30)
            timeout = await asyncio.wait_for(request, timeout=GUARD)
            assert timeout.status_code == 504
        finally:
            held.release.set()

    for response in (failure, unexpected, timeout):
        records = _http_records(caplog, response.headers["X-Request-ID"])
        terminals = [r for r in records
                     if r.getMessage().startswith("http_request_finished ")]
        assert len(terminals) == 1
        assert terminals[0].levelno == logging.WARNING

    caplog.clear()
    blocked = BlockedOrchestrator()
    other_runtime = RuntimeSpy(ScriptedContext(runtime.context.clock))
    other_runtime.orchestrator = blocked
    async with app_client(other_runtime, catalog=ScriptedCatalog()) as client:
        exchange = RawConversation(client.asgi_app, _scope(
            "POST", "/charts/natal",
            headers=[(b"content-type", b"application/json"),
                     (b"cookie", COOKIE.encode("ascii"))],
        ))
        exchange.start()
        exchange.put_body(BODY, more=False)
        try:
            await asyncio.wait_for(blocked.wait_count(1), timeout=GUARD)
            exchange.disconnect()
            await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
            assert exchange.messages == []
        finally:
            blocked.release_all()
            await exchange.finish()
    terminal = [r for r in caplog.records
                if r.name.startswith("exact_orb.http_api")
                and r.getMessage().startswith("http_request_finished ")]
    assert len(terminal) == 1
    assert terminal[0].levelno == logging.WARNING


@pytest.mark.parametrize("deadline_first", (False, True))
async def test_watchdog_wins_after_firing_even_if_owner_is_done_at_waiter_resume(
    deadline_first: bool, app_client, runtime: RuntimeSpy, scheduler,
    monkeypatch, caplog,
) -> None:
    from exact_orb.http_api.routes import build as build_module

    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    held = TerminalHeldOrchestrator(None)
    runtime.orchestrator = held
    route_wait_ready = asyncio.Event()
    resume_route = asyncio.Event()
    original_wait = asyncio.wait

    async def wait_with_delayed_route_resume(tasks, *, return_when):
        done, pending = await original_wait(tasks, return_when=return_when)
        if (deadline_first and len(tasks) == 3
                and any(task.get_name().startswith("exact_orb_build_")
                        for task in tasks)):
            route_wait_ready.set()
            await resume_route.wait()
            return {task for task in tasks if task.done()}, {
                task for task in tasks if not task.done()
            }
        return done, pending

    with monkeypatch.context() as patcher:
        patcher.setattr(build_module.asyncio, "wait", wait_with_delayed_route_resume)
        async with app_client(runtime, catalog=ScriptedCatalog()) as client:
            request = asyncio.create_task(client.post(
                "/charts/natal", json=_build(), headers={"Cookie": COOKIE},
            ))
            try:
                await asyncio.wait_for(held.entered.wait(), timeout=GUARD)
                if deadline_first:
                    await asyncio.wait_for(scheduler.wait_registered(30), timeout=GUARD)
                    await scheduler.advance(30)
                    await asyncio.wait_for(route_wait_ready.wait(), timeout=GUARD)
                    assert (await client.get("/health/live")).status_code == 503
                    owner = next(iter(client.asgi_app.state.build_owners))
                    held.release.set()
                    await asyncio.wait_for(owner, timeout=GUARD)
                    resume_route.set()
                else:
                    held.release.set()
                response = await asyncio.wait_for(request, timeout=GUARD)
                assert response.status_code == (504 if deadline_first else 422)
                assert (await client.get("/health/live")).status_code == (
                    503 if deadline_first else 200
                )
                if deadline_first:
                    assert response.json()["code"] == "BUILD_TIMEOUT"
                    assert response.headers["Retry-After"] == "5"
                    assert response.headers.get_list("set-cookie") == []
                terminals = _http_records(caplog, response.headers["X-Request-ID"])
                assert sum(record.getMessage().startswith("http_request_finished ")
                           for record in terminals) == 1
            finally:
                held.release.set()
                resume_route.set()
                if not request.done():
                    await asyncio.wait_for(request, timeout=GUARD)


class BlockingContext(ScriptedContext):
    def __init__(self, clock, operation: str) -> None:
        super().__init__(clock)
        self.operation = operation
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def create(self, session_id: str) -> object:
        if self.operation == "create":
            self.entered.set()
            await self.release.wait()
        return await super().create(session_id)

    async def load(self, session_id: str) -> object:
        if self.operation == "load":
            self.entered.set()
            await self.release.wait()
        return await super().load(session_id)


class BlockingCatalog(CloseSpyCatalog):
    def __init__(self, events: list[str]) -> None:
        super().__init__(events)
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def search(self, query: str, *, limit: int = 10):
        self.entered.set()
        await self.release.wait()
        return await super().search(query, limit=limit)


@pytest.mark.parametrize("route", ("bootstrap", "current", "places"))
async def test_nonbuild_pending_leaf_has_no_deadline_or_health_probe(
    route: str, utc_clock, scheduler,
) -> None:
    events: list[str] = []
    context = BlockingContext(utc_clock, "create" if route == "bootstrap" else "load")
    context.snapshots[SESSION_ID] = SessionSnapshot(
        state=new_session(SESSION_ID, now=utc_clock()), dialog=(), chart=None,
    )
    runtime = CloseSpyRuntime(context, events)
    catalog = BlockingCatalog(events)
    app = _create_app(runtime=runtime, catalog=catalog,
                      utc_clock=utc_clock, scheduler=scheduler)
    lifespan = app.router.lifespan_context(app)
    await lifespan.__aenter__()
    if route == "bootstrap":
        scope = _scope("POST", "/session/bootstrap",
                       headers=[(b"content-type", b"application/json")])
    elif route == "current":
        scope = _scope("GET", "/charts/current", headers=[
            (b"cookie", COOKIE.encode("ascii"))])
    else:
        scope = _scope("GET", "/places", query=b"query=Moscow")
    exchange = RawConversation(app, scope)
    exchange.start()
    exchange.put_body(BOOTSTRAP_BODY if route == "bootstrap" else b"", more=False)
    blocker = catalog if route == "places" else context
    try:
        await asyncio.wait_for(blocker.entered.wait(), timeout=GUARD)
        await scheduler.advance(31)
        assert exchange.task is not None and not exchange.task.done()
        assert (await _raw(app, "GET", "/health/live"))[0] == 200
        assert (await _raw(app, "GET", "/health/ready"))[0] == 200
        blocker.release.set()
        await exchange.finish()
        assert _response(exchange.messages)[0] == 200
    finally:
        blocker.release.set()
        if exchange.task is not None and not exchange.task.done():
            await exchange.finish()
        await lifespan.__aexit__(None, None, None)


@pytest.mark.parametrize("route", ("bootstrap", "current", "places"))
async def test_shutdown_waits_accepted_nonbuild_request_before_runtime_and_catalog(
    route: str, utc_clock, scheduler
) -> None:
    events: list[str] = []
    context = BlockingContext(utc_clock, "create" if route == "bootstrap" else "load")
    context.snapshots[SESSION_ID] = SessionSnapshot(
        state=new_session(SESSION_ID, now=utc_clock()), dialog=(), chart=None,
    )
    runtime = CloseSpyRuntime(context, events)
    catalog = BlockingCatalog(events)
    app = _create_app(runtime=runtime, catalog=catalog,
                      utc_clock=utc_clock, scheduler=scheduler)
    lifespan = app.router.lifespan_context(app)
    await lifespan.__aenter__()
    if route == "bootstrap":
        scope = _scope("POST", "/session/bootstrap",
                       headers=[(b"content-type", b"application/json")])
    elif route == "current":
        scope = _scope("GET", "/charts/current", headers=[
            (b"cookie", COOKIE.encode("ascii"))])
    else:
        scope = _scope("GET", "/places",
                       query=b"query=" + quote("Москва").encode("ascii"))
    exchange = RawConversation(app, scope)
    exchange.start()
    exchange.put_body(BOOTSTRAP_BODY if route == "bootstrap" else b"", more=False)
    blocker = catalog if route == "places" else context
    shutdown: asyncio.Task[object] | None = None
    try:
        await asyncio.wait_for(blocker.entered.wait(), timeout=GUARD)
        shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
        await asyncio.wait_for(app.state.shutdown_started.wait(), timeout=GUARD)
        ready = await _raw(app, "GET", "/health/ready")
        assert ready[0] == 503
        assert not shutdown.done()
        assert not runtime.close_entered.is_set()
        assert not catalog.closed
        blocker.release.set()
        await exchange.finish()
        assert _response(exchange.messages)[0] == 200
        await asyncio.wait_for(shutdown, timeout=GUARD)
        assert events == ["runtime.close", "catalog.close"]
        assert context.create_calls or context.load_calls or catalog.calls
    finally:
        blocker.release.set()
        if shutdown is None:
            await lifespan.__aexit__(None, None, None)
        elif not shutdown.done():
            await asyncio.wait_for(shutdown, timeout=GUARD)


async def test_shutdown_grace_fail_fast_preserves_active_build_and_open_resources(
    utc_clock, scheduler
) -> None:
    from exact_orb.http_api.app import LifecyclePhase

    events: list[str] = []
    runtime = CloseSpyRuntime(ScriptedContext(utc_clock), events)
    catalog = CloseSpyCatalog(events)
    held = TerminalHeldOrchestrator(None)
    runtime.orchestrator = held
    app = _create_app(
        runtime=runtime, catalog=catalog, utc_clock=utc_clock, scheduler=scheduler,
        settings=http_settings(shutdown_grace_seconds=20),
    )
    lifespan = app.router.lifespan_context(app)
    await lifespan.__aenter__()
    exchange = RawConversation(app, _scope(
        "POST", "/charts/natal", headers=[
            (b"content-type", b"application/json"),
            (b"cookie", COOKIE.encode("ascii")),
        ],
    ))
    exchange.start()
    exchange.put_body(BODY, more=False)
    shutdown: asyncio.Task[object] | None = None
    try:
        await asyncio.wait_for(held.entered.wait(), timeout=GUARD)
        shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
        await asyncio.wait_for(app.state.shutdown_started.wait(), timeout=GUARD)
        await asyncio.wait_for(scheduler.wait_registered(20), timeout=GUARD)
        assert app.state.admission.active_build_count == 1
        assert not runtime.close_entered.is_set()
        await scheduler.advance(20)
        await asyncio.wait_for(shutdown, timeout=GUARD)
        assert app.state.lifecycle_phase == LifecyclePhase.UNHEALTHY
        assert (await _raw(app, "GET", "/health/live"))[0] == 503
        assert app.state.admission.active_build_count == 1
        assert not runtime.closed and not catalog.closed
        assert events == []
    finally:
        held.release.set()
        assert exchange.task is not None
        await asyncio.wait_for(
            asyncio.gather(exchange.task, return_exceptions=True), timeout=GUARD,
        )
        if shutdown is None:
            await lifespan.__aexit__(None, None, None)
        elif not shutdown.done():
            await asyncio.wait_for(shutdown, timeout=GUARD)
        retained = getattr(app.state, "retained_resources", None)
        if retained is not None:
            await retained.aclose()


async def test_shutdown_grace_cancelable_place_request_closes_in_order(
    utc_clock, scheduler, caplog,
) -> None:
    from exact_orb.http_api.app import LifecyclePhase

    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    events: list[str] = []
    runtime = CloseSpyRuntime(ScriptedContext(utc_clock), events)
    catalog = BlockingCatalog(events)
    app = _create_app(
        runtime=runtime, catalog=catalog, utc_clock=utc_clock, scheduler=scheduler,
        settings=http_settings(shutdown_grace_seconds=20),
    )
    lifespan = app.router.lifespan_context(app)
    await lifespan.__aenter__()
    exchange = RawConversation(app, _scope("GET", "/places", query=b"query=Moscow"))
    exchange.start()
    shutdown: asyncio.Task[object] | None = None
    try:
        await asyncio.wait_for(catalog.entered.wait(), timeout=GUARD)
        shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
        await asyncio.wait_for(app.state.shutdown_started.wait(), timeout=GUARD)
        await asyncio.wait_for(scheduler.wait_registered(20), timeout=GUARD)
        await scheduler.advance(20)
        await asyncio.wait_for(shutdown, timeout=GUARD)
        assert app.state.lifecycle_phase == LifecyclePhase.STOPPED
        assert events == ["runtime.close", "catalog.close"]
        assert exchange.task is not None and exchange.task.done()
        terminals = [record for record in caplog.records
                     if record.getMessage().startswith("http_request_finished ")]
        starts = [record for record in caplog.records
                  if record.getMessage().startswith("http_request_started ")]
        assert len(starts) == 1
        assert len(terminals) == 1
        started_id = starts[0].getMessage().split("request_id=", 1)[1].split()[0]
        assert f"request_id={started_id}" in terminals[0].getMessage()
        assert "outcome=cancelled" in terminals[0].getMessage()
    finally:
        catalog.release.set()
        if exchange.task is not None:
            await asyncio.wait_for(
                asyncio.gather(exchange.task, return_exceptions=True), timeout=GUARD,
            )
        if shutdown is None:
            await lifespan.__aexit__(None, None, None)
        elif not shutdown.done():
            await asyncio.wait_for(shutdown, timeout=GUARD)
        retained = getattr(app.state, "retained_resources", None)
        if retained is not None:
            await retained.aclose()


async def test_build_owner_cancelled_before_first_step_releases_permit(
    utc_clock, scheduler, monkeypatch
) -> None:
    runtime = RuntimeSpy(ScriptedContext(utc_clock))
    catalog = ScriptedCatalog()
    app = _create_app(runtime=runtime, catalog=catalog,
                      utc_clock=utc_clock, scheduler=scheduler)
    lifespan = app.router.lifespan_context(app)
    await lifespan.__aenter__()
    exchange = RawConversation(app, _scope(
        "POST", "/charts/natal", headers=[
            (b"content-type", b"application/json"),
            (b"cookie", COOKIE.encode("ascii")),
        ],
    ))
    original_create_task = asyncio.create_task

    def cancel_new_owner(coroutine, *, name=None):
        task = original_create_task(coroutine, name=name)
        if name is not None and name.startswith("exact_orb_build_"):
            task.cancel()
        return task

    try:
        with monkeypatch.context() as patcher:
            patcher.setattr(asyncio, "create_task", cancel_new_owner)
            exchange.start()
            exchange.put_body(BODY, more=False)
            await exchange.finish()
        assert exchange.messages == []
        assert runtime.orchestrator.calls == []
        await asyncio.wait_for(
            asyncio.gather(*app.state.build_owners, return_exceptions=True),
            timeout=GUARD,
        )
        assert app.state.admission.active_build_count == 0
        runtime.orchestrator = ScriptedOrchestrator(_input_required)
        accepted = await _raw(app, "POST", "/charts/natal", body=BODY, headers=[
            (b"content-type", b"application/json"),
            (b"cookie", COOKIE.encode("ascii")),
        ])
        assert accepted[0] == 422
        assert len(runtime.orchestrator.calls) == 1
    finally:
        await lifespan.__aexit__(None, None, None)


class SaveBarrier:
    """Only the leaf save is held; the actual SQLite CAS remains the oracle."""

    def __init__(self, inner: object) -> None:
        self.inner = inner
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    async def save(self, *args: object, **kwargs: object) -> object:
        self.entered.set()
        await self.release.wait()
        return await self.inner.save(*args, **kwargs)


async def test_disconnect_before_commit_cancels_without_sqlite_mutation(
    app_client, sqlite_restart, utc_clock
) -> None:
    async with sqlite_restart() as old_runtime:
        await old_runtime.context.create(SESSION_ID)
        _, observed, _, handler = _real_orchestrator(
            old_runtime, utc_clock, barrier=True,
        )
        handler.expected = 1
        async with app_client(old_runtime) as client:
            exchange = RawConversation(client.asgi_app, _scope(
                "POST", "/charts/natal", headers=[
                    (b"content-type", b"application/json"),
                    (b"cookie", COOKIE.encode("ascii")),
                ],
            ))
            exchange.start()
            exchange.put_body(BODY, more=False)
            try:
                await asyncio.wait_for(handler.wait_entered(), timeout=GUARD)
                exchange.disconnect()
                await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
                await exchange.finish()
                assert exchange.messages == []
                assert observed.save_expected == []
            finally:
                handler.release.set()
                if exchange.task is not None and not exchange.task.done():
                    await exchange.finish()
        async with sqlite_restart() as fresh_runtime:
            assert fresh_runtime is not old_runtime
            async with app_client(fresh_runtime) as client:
                current = await client.get("/charts/current", headers={"Cookie": COOKIE})
                assert current.status_code == 200
                assert current.json()["status"] == "empty"
                assert current.json()["state_version"] == 0


async def test_disconnect_during_protected_commit_is_visible_after_restart(
    app_client, sqlite_restart, utc_clock
) -> None:
    async with sqlite_restart() as old_runtime:
        await old_runtime.context.create(SESSION_ID)
        save_gate = SaveBarrier(old_runtime.context)
        old_runtime.context = save_gate
        _, observed, orchestrator, _ = _real_orchestrator(old_runtime, utc_clock)
        async with app_client(old_runtime) as client:
            exchange = RawConversation(client.asgi_app, _scope(
                "POST", "/charts/natal", headers=[
                    (b"content-type", b"application/json"),
                    (b"cookie", COOKIE.encode("ascii")),
                ],
            ))
            exchange.start()
            exchange.put_body(BODY, more=False)
            try:
                await asyncio.wait_for(save_gate.entered.wait(), timeout=GUARD)
                exchange.disconnect()
                await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
                assert exchange.messages == []
                assert len(orchestrator.calls) == 1
                assert observed.save_expected == [0]
                save_gate.release.set()
                await exchange.finish()
                assert exchange.messages == []
            finally:
                save_gate.release.set()
                if exchange.task is not None and not exchange.task.done():
                    await exchange.finish()
        async with sqlite_restart() as fresh_runtime:
            assert fresh_runtime is not old_runtime
            async with app_client(fresh_runtime) as client:
                restored = await client.post("/session/bootstrap", json={},
                                             headers={"Cookie": COOKIE})
                assert restored.status_code == 200
                current = await client.get("/charts/current", headers={"Cookie": COOKIE})
                assert current.status_code == 200
                assert current.json()["status"] == "chart_ready"
                assert current.json()["state_version"] == 1


class JoinSignal(logging.Handler):
    def __init__(self, expected: int) -> None:
        super().__init__()
        self.expected = expected
        self.count = 0
        self.reached = asyncio.Event()

    def emit(self, record: logging.LogRecord) -> None:
        if record.getMessage().startswith("singleflight_join "):
            self.count += 1
            if self.count >= self.expected:
                self.reached.set()


async def test_two_waiters_one_real_leader_keep_separate_permits_after_disconnect(
    app_client, tmp_path: Path, utc_clock
) -> None:
    from exact_orb.application.bootstrap import build_application_runtime
    from exact_orb.birth.places import LocalPlaceCatalog
    from exact_orb.calculation.codec import decode_chart_artifact
    from tests.application.test_application_bootstrap_integration import (
        PLACES_PATH, _BlockingNatalCalculator, _settings as runtime_settings,
    )
    from tests.http_api.build_support import GOLDEN_DIR

    class ClosableLocalCatalog:
        def __init__(self) -> None:
            self.inner = LocalPlaceCatalog.from_file(PLACES_PATH)

        async def lookup(self, place_id: str):
            return await self.inner.lookup(place_id)

        async def aclose(self) -> None:
            return None

    catalog = ClosableLocalCatalog()
    golden_chart = decode_chart_artifact(
        (GOLDEN_DIR / "chart_artifact_format_1_natal_1985.bin").read_bytes()
    ).chart

    class ProjectableCalculator(_BlockingNatalCalculator):
        def __call__(self, birth_datetime, latitude, longitude, **kwargs):
            super().__call__(birth_datetime, latitude, longitude, **kwargs)
            return golden_chart.model_copy(update={
                "datetime_utc": birth_datetime,
                "latitude": latitude,
                "longitude": longitude,
            })

    calculator = ProjectableCalculator(asyncio.get_running_loop())
    runtime = await build_application_runtime(
        settings=runtime_settings(tmp_path, db_name="shared-leader-http.sqlite3"),
        places=catalog,
        clock=utc_clock,
        natal_calculator=calculator,
    )
    for number in range(1, 8):
        await runtime.context.create(_cookie(number).split("=", 1)[1])
    permissive = WindowLimit(100, 3600)
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=permissive, build_session_daily=permissive,
        build_ip_hourly=permissive, build_ip_daily=permissive,
        active_builds=5,
    )
    logger = logging.getLogger("exact_orb.calculation.artifacts")
    old_level = logger.level
    signal = JoinSignal(expected=4)
    logger.addHandler(signal)
    logger.setLevel(logging.DEBUG)
    tasks: list[asyncio.Task[Any]] = []
    exchange: RawConversation | None = None
    try:
        async with app_client(runtime, catalog=catalog, limiter_policy=policy) as client:
            tasks.append(asyncio.create_task(client.post(
                "/charts/natal", json=_build(),
                headers={"Cookie": _cookie(1)},
            )))
            await asyncio.wait_for(calculator.entered.wait(), timeout=GUARD)
            exchange = RawConversation(client.asgi_app, _scope(
                "POST", "/charts/natal", headers=[
                    (b"content-type", b"application/json"),
                    (b"cookie", _cookie(2).encode("ascii")),
                ],
            ))
            exchange.start()
            exchange.put_body(BODY, more=False)
            for number in (3, 4, 5):
                tasks.append(asyncio.create_task(client.post(
                    "/charts/natal", json=_build(),
                    headers={"Cookie": _cookie(number)},
                )))
            await asyncio.wait_for(signal.reached.wait(), timeout=GUARD)
            assert signal.count == 4
            assert calculator.calls == 1
            exchange.disconnect()
            await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
            assert exchange.messages == []
            sixth = await asyncio.wait_for(client.post(
                "/charts/natal", json=_build(),
                headers={"Cookie": _cookie(6)},
            ), timeout=GUARD)
            assert sixth.status_code == 503
            assert sixth.json()["code"] == "BUILD_CAPACITY_EXHAUSTED"
            assert sixth.headers["Retry-After"] == "1"
            assert calculator.calls == 1
            calculator.release.set()
            await exchange.finish()
            assert exchange.messages == []
            results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=GUARD)
            assert all(result.status_code == 200 for result in results)
            assert calculator.finished.is_set()
            assert runtime.artifacts.misses == 5  # Each waiter missed; one leader calculated.
            after_release = await client.post(
                "/charts/natal", json=_build(),
                headers={"Cookie": _cookie(7)},
            )
            assert after_release.status_code == 200
            assert calculator.calls == 1
    finally:
        calculator.release.set()
        logger.removeHandler(signal)
        logger.setLevel(old_level)
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if exchange is not None and exchange.task is not None and not exchange.task.done():
            await exchange.finish()
        await runtime.aclose()


async def test_cancelled_sqlite_session_load_future_blocks_shutdown_close(
    app_client, sqlite_restart, utc_clock, scheduler, monkeypatch
) -> None:
    async with sqlite_restart() as runtime:
        await runtime.context.create(SESSION_ID)
        loop = asyncio.get_running_loop()
        worker_entered = asyncio.Event()
        worker_release = threading.Event()
        worker_finished = asyncio.Event()
        real_touch = session_sqlite._sync_touch

        def held_touch(*args: object) -> object:
            loop.call_soon_threadsafe(worker_entered.set)
            assert worker_release.wait(timeout=5)
            try:
                return real_touch(*args)
            finally:
                loop.call_soon_threadsafe(worker_finished.set)

        monkeypatch.setattr(session_sqlite, "_sync_touch", held_touch)
        app = _create_app(runtime=runtime, catalog=ScriptedCatalog(),
                          utc_clock=utc_clock, scheduler=scheduler)
        lifespan = app.router.lifespan_context(app)
        await lifespan.__aenter__()
        exchange = RawConversation(app, _scope(
            "GET", "/charts/current",
            headers=[(b"cookie", COOKIE.encode("ascii"))],
        ))
        exchange.start()
        exchange.put_body(b"", more=False)
        shutdown: asyncio.Task[object] | None = None
        try:
            await asyncio.wait_for(worker_entered.wait(), timeout=GUARD)
            exchange.disconnect()
            await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
            shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
            await asyncio.wait_for(app.state.shutdown_started.wait(), timeout=GUARD)
            assert (await _raw(app, "GET", "/health/ready"))[0] == 503
            assert not runtime.close_entered.is_set()
            assert not worker_finished.is_set()
            assert not shutdown.done()
            worker_release.set()
            await asyncio.wait_for(worker_finished.wait(), timeout=GUARD)
            await exchange.finish()
            await asyncio.wait_for(shutdown, timeout=GUARD)
            assert runtime.closed
        finally:
            worker_release.set()
            if shutdown is None:
                await lifespan.__aexit__(None, None, None)
            elif not shutdown.done():
                await asyncio.wait_for(shutdown, timeout=GUARD)
            if exchange.task is not None and not exchange.task.done():
                await exchange.finish()

    async with sqlite_restart() as fresh_runtime:
        assert fresh_runtime is not runtime
        async with app_client(fresh_runtime) as client:
            current = await client.get("/charts/current", headers={"Cookie": COOKIE})
            assert current.status_code == 200
            assert current.json()["status"] == "empty"


async def test_disconnected_bootstrap_can_persist_without_delivered_cookie(
    app_client, sqlite_restart, monkeypatch,
) -> None:
    loop = asyncio.get_running_loop()
    worker_entered = asyncio.Event()
    worker_release = threading.Event()
    created_ids: list[str] = []
    real_create = session_sqlite._sync_create

    def held_create(backend: object, session_id: str, now: object) -> object:
        created_ids.append(session_id)
        loop.call_soon_threadsafe(worker_entered.set)
        assert worker_release.wait(timeout=5)
        return real_create(backend, session_id, now)

    monkeypatch.setattr(session_sqlite, "_sync_create", held_create)
    exchange: RawConversation | None = None
    try:
        async with sqlite_restart() as runtime:
            async with app_client(runtime, limiter_policy=SmallLimiterPolicy(
                session_create_ip=WindowLimit(1, 11),
            )) as client:
                exchange = RawConversation(client.asgi_app, _scope(
                    "POST", "/session/bootstrap",
                    headers=[(b"content-type", b"application/json")],
                ))
                exchange.start()
                exchange.put_body(BOOTSTRAP_BODY, more=False)
                await asyncio.wait_for(worker_entered.wait(), timeout=GUARD)
                exchange.disconnect()
                await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
                worker_release.set()
                await exchange.finish()
                assert exchange.messages == []
                assert len(created_ids) == 1

                denied = await client.post("/session/bootstrap", json={})
                assert denied.status_code == 429
                assert denied.json()["code"] == "SESSION_CREATE_RATE_LIMITED"
            async with sqlite_restart() as fresh_runtime:
                loaded = await fresh_runtime.context.load(created_ids[0])
                assert isinstance(loaded, SessionSnapshot)
                assert loaded.state.state_version == 0
    finally:
        worker_release.set()
        if exchange is not None and exchange.task is not None and not exchange.task.done():
            await exchange.finish()


def _build_catalog_db(tmp_path: Path) -> Path:
    tests_root = Path(__file__).resolve().parents[1]
    fixtures = tests_root / "fixtures" / "place_catalog"
    builder = runpy.run_path(str(tests_root.parent / "scripts" / "build_place_catalog.py"))
    path = tmp_path / "places.sqlite"
    builder["build"](
        cities_path=fixtures / "cities1000.txt",
        admin1_path=fixtures / "admin1CodesASCII.txt",
        alternate_names_path=fixtures / "alternateNamesV2.txt",
        out_path=path,
    )
    return path


class CatalogOwner:
    def __init__(self, inner: SqlitePlaceCatalog, events: list[str]) -> None:
        self.inner = inner
        self.events = events
        self.close_entered = asyncio.Event()
        self.closed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    async def aclose(self) -> None:
        self.events.append("catalog.close")
        self.close_entered.set()
        await self.inner.aclose()
        self.closed = True


class RuntimeOwner:
    def __init__(self, inner: object, events: list[str]) -> None:
        self.inner = inner
        self.events = events
        self.close_entered = asyncio.Event()
        self.closed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    async def aclose(self) -> None:
        self.events.append("runtime.close")
        self.close_entered.set()
        await self.inner.aclose()
        self.closed = True


async def test_cancelled_catalog_search_future_blocks_shutdown_close(
    tmp_path: Path, utc_clock, scheduler, monkeypatch
) -> None:
    db_path = _build_catalog_db(tmp_path)
    loop = asyncio.get_running_loop()
    worker_entered = asyncio.Event()
    worker_finished = asyncio.Event()
    worker_release = threading.Event()
    real_search = place_sqlite._sync_search

    def held_search(*args: object) -> object:
        loop.call_soon_threadsafe(worker_entered.set)
        assert worker_release.wait(timeout=5)
        try:
            return real_search(*args)
        finally:
            loop.call_soon_threadsafe(worker_finished.set)

    events: list[str] = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        catalog = CatalogOwner(
            await SqlitePlaceCatalog.open(db_path, executor=executor), events,
        )
        runtime = CloseSpyRuntime(ScriptedContext(utc_clock), events)
        monkeypatch.setattr(place_sqlite, "_sync_search", held_search)
        try:
            app = _create_app(runtime=runtime, catalog=catalog,
                              utc_clock=utc_clock, scheduler=scheduler)
            lifespan = app.router.lifespan_context(app)
            await lifespan.__aenter__()
        except BaseException:
            worker_release.set()
            await runtime.aclose()
            await catalog.aclose()
            raise
        exchange = RawConversation(app, _scope(
            "GET", "/places", query=b"query=" + quote("Москва").encode("ascii"),
        ))
        exchange.start()
        exchange.put_body(b"", more=False)
        shutdown: asyncio.Task[object] | None = None
        try:
            await asyncio.wait_for(worker_entered.wait(), timeout=GUARD)
            exchange.disconnect()
            await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
            shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
            await asyncio.wait_for(app.state.shutdown_started.wait(), timeout=GUARD)
            assert (await _raw(app, "GET", "/health/ready"))[0] == 503
            assert not worker_finished.is_set()
            assert not runtime.close_entered.is_set()
            assert not catalog.close_entered.is_set()
            assert not shutdown.done()
            worker_release.set()
            await asyncio.wait_for(worker_finished.wait(), timeout=GUARD)
            await exchange.finish()
            await asyncio.wait_for(shutdown, timeout=GUARD)
            assert events == ["runtime.close", "catalog.close"]
            assert runtime.closed and catalog.closed
        finally:
            worker_release.set()
            if shutdown is None:
                await lifespan.__aexit__(None, None, None)
            elif not shutdown.done():
                await asyncio.wait_for(shutdown, timeout=GUARD)
            if exchange.task is not None and not exchange.task.done():
                await exchange.finish()


async def test_cancelled_catalog_lookup_keeps_five_permits_and_shutdown_owner(
    app_client, tmp_path: Path, utc_clock, scheduler, monkeypatch
) -> None:
    from exact_orb.application.bootstrap import build_application_runtime
    from tests.application.test_application_bootstrap_integration import (
        _settings as runtime_settings,
    )

    db_path = _build_catalog_db(tmp_path)
    events: list[str] = []
    worker_release = threading.Event()
    loop = asyncio.get_running_loop()
    worker_entered = asyncio.Event()
    worker_finished = asyncio.Event()
    real_lookup = place_sqlite._sync_lookup

    def held_lookup(*args: object) -> object:
        loop.call_soon_threadsafe(worker_entered.set)
        assert worker_release.wait(timeout=5)
        try:
            return real_lookup(*args)
        finally:
            loop.call_soon_threadsafe(worker_finished.set)

    with ThreadPoolExecutor(max_workers=1) as executor:
        catalog = CatalogOwner(
            await SqlitePlaceCatalog.open(db_path, executor=executor), events,
        )
        real_runtime = await build_application_runtime(
            settings=runtime_settings(tmp_path, db_name="lookup-http.sqlite3"),
            places=catalog, clock=utc_clock,
        )
        for number in range(1, 7):
            await real_runtime.context.create(_cookie(number).split("=", 1)[1])
        runtime = RuntimeOwner(real_runtime, events)
        class CountingExecute:
            def __init__(self, inner: object) -> None:
                self.inner = inner
                self.calls = 0
                self.reached = asyncio.Event()

            async def execute(self, command, *, session_id, run):
                self.calls += 1
                if self.calls == 5:
                    self.reached.set()
                return await self.inner.execute(command, session_id=session_id, run=run)

        counted = CountingExecute(real_runtime.orchestrator)
        runtime.orchestrator = counted
        monkeypatch.setattr(place_sqlite, "_sync_lookup", held_lookup)
        permissive = WindowLimit(100, 3600)
        policy = replace(
            SmallLimiterPolicy(),
            build_session_hourly=permissive, build_session_daily=permissive,
            build_ip_hourly=permissive, build_ip_daily=permissive,
            active_builds=5,
        )
        try:
            app = _create_app(runtime=runtime, catalog=catalog,
                              utc_clock=utc_clock, scheduler=scheduler,
                              limiter_policy=policy)
            lifespan = app.router.lifespan_context(app)
            await lifespan.__aenter__()
        except BaseException:
            worker_release.set()
            await runtime.aclose()
            await catalog.aclose()
            raise
        tasks: list[asyncio.Task[Any]] = []
        shutdown: asyncio.Task[object] | None = None
        exchange = RawConversation(app, _scope(
            "POST", "/charts/natal", headers=[
                (b"content-type", b"application/json"),
                (b"cookie", _cookie(1).encode("ascii")),
            ],
        ))
        exchange.start()
        exchange.put_body(json.dumps(_build(place_id="99999999")).encode("utf-8"),
                          more=False)
        try:
            await asyncio.wait_for(worker_entered.wait(), timeout=GUARD)
            # Use raw ASGI for all five, so the same app/lifespan and peer are observed.
            for number in (2, 3, 4, 5):
                other = RawConversation(app, _scope(
                    "POST", "/charts/natal", headers=[
                        (b"content-type", b"application/json"),
                        (b"cookie", _cookie(number).encode("ascii")),
                    ],
                ))
                other.start()
                other.put_body(json.dumps(_build(place_id="99999999")).encode("utf-8"),
                               more=False)
                tasks.append(other.task)
            await asyncio.wait_for(counted.reached.wait(), timeout=GUARD)
            assert counted.calls == 5
            exchange.disconnect()
            await asyncio.wait_for(exchange.disconnected.wait(), timeout=GUARD)
            denied = await _raw(
                app, "POST", "/charts/natal",
                body=json.dumps(_build(place_id="99999999")).encode("utf-8"),
                headers=[(b"content-type", b"application/json"),
                         (b"cookie", _cookie(6).encode("ascii"))],
            )
            assert denied[0] == 503
            assert json.loads(denied[2])["code"] == "BUILD_CAPACITY_EXHAUSTED"
            assert denied[1]["retry-after"] == "1"
            assert not worker_finished.is_set()
            shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
            await asyncio.wait_for(app.state.shutdown_started.wait(), timeout=GUARD)
            assert (await _raw(app, "GET", "/health/ready"))[0] == 503
            assert not runtime.close_entered.is_set()
            assert not catalog.close_entered.is_set()
            assert not shutdown.done()
            worker_release.set()
            await asyncio.wait_for(worker_finished.wait(), timeout=GUARD)
            await exchange.finish()
            assert exchange.messages == []
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=GUARD)
            await asyncio.wait_for(shutdown, timeout=GUARD)
            assert events == ["runtime.close", "catalog.close"]
            assert runtime.closed and catalog.closed
        finally:
            worker_release.set()
            if shutdown is None:
                await lifespan.__aexit__(None, None, None)
            elif not shutdown.done():
                await asyncio.wait_for(shutdown, timeout=GUARD)
            if exchange.task is not None and not exchange.task.done():
                await exchange.finish()
            await asyncio.gather(*tasks, return_exceptions=True)
            await real_runtime.aclose()

    # Fake supervisor creates a different runtime/cache over the same SQLite file.
    with ThreadPoolExecutor(max_workers=1) as executor:
        new_catalog = await SqlitePlaceCatalog.open(db_path, executor=executor)
        new_runtime = await build_application_runtime(
            settings=runtime_settings(tmp_path, db_name="lookup-http.sqlite3"),
            places=new_catalog, clock=utc_clock,
        )
        assert new_runtime is not real_runtime
        assert new_runtime.artifacts is not real_runtime.artifacts
        async with app_client(new_runtime, catalog=new_catalog) as client:
            assert (await client.get("/health/ready")).status_code == 200
            current = await client.get("/charts/current", headers={"Cookie": _cookie(1)})
            assert current.status_code == 200
            assert current.json()["status"] == "empty"
