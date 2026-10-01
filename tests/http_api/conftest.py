"""Deterministic HTTP contract seams shared by the pre-implementation tests."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from exact_orb.session.adapters.sqlite import SqliteSessionPersistence
from exact_orb.session.context import ContextService
from exact_orb.session.outcomes import SessionAbsent, SessionCreated, SessionIdConflict
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import new_session
from tests.fixtures.calculation import VERSION


NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def http_settings(**changes: object) -> SimpleNamespace:
    values = {
        "allowed_origins": ("https://testserver",),
        "trusted_proxy_cidrs": (),
        "public_origin": "https://testserver",
        "body_timeout_seconds": 5,
        "build_timeout_seconds": 30,
        "shutdown_grace_seconds": 30,
        "reaper_interval_seconds": 900,
        "max_body_bytes": 16 * 1024,
        "expose_schema": False,
    }
    values.update(changes)
    return SimpleNamespace(**values)


class UtcClock:
    def __init__(self) -> None:
        self.value = NOW

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += timedelta(seconds=seconds)


class ManualScheduler:
    """The same manually advanced monotonic scheduler for every HTTP deadline."""

    def __init__(self) -> None:
        self.value = 0.0
        self._condition = asyncio.Condition()
        self._waiting: list[float] = []

    def now(self) -> float:
        return self.value

    async def wait_until(self, deadline: float) -> None:
        async with self._condition:
            self._waiting.append(deadline)
            self._condition.notify_all()
            try:
                await self._condition.wait_for(lambda: self.value >= deadline)
            finally:
                self._waiting.remove(deadline)
                self._condition.notify_all()

    async def wait_registered(self, deadline: float) -> None:
        async with self._condition:
            await self._condition.wait_for(lambda: deadline in self._waiting)

    async def advance(self, seconds: float) -> None:
        async with self._condition:
            self.value += seconds
            self._condition.notify_all()


class ForbiddenComponent:
    """A leaf spy: session reads must never enter calculation or orchestration."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __getattr__(self, name: str) -> Callable[..., Any]:
        async def forbidden(*args: object, **kwargs: object) -> None:
            self.calls.append(name)
            raise AssertionError(f"session HTTP path called forbidden component: {name}")

        return forbidden


class ForbiddenCatalog(ForbiddenComponent):
    async def aclose(self) -> None:
        return None


class ScriptedContext:
    def __init__(self, clock: UtcClock) -> None:
        self.clock = clock
        self.snapshots: dict[str, SessionSnapshot] = {}
        self.create_results: deque[object] = deque()
        self.load_results: deque[object] = deque()
        self.create_calls: list[str] = []
        self.load_calls: list[str] = []
        self.save_calls: list[object] = []

    async def create(self, session_id: str) -> object:
        self.create_calls.append(session_id)
        result = self.create_results.popleft() if self.create_results else None
        if result == "conflict":
            return SessionIdConflict(session_id=session_id)
        if result is not None:
            return result
        state = new_session(session_id, now=self.clock())
        self.snapshots[session_id] = SessionSnapshot(state=state, dialog=(), chart=None)
        return SessionCreated(state=state)

    async def load(self, session_id: str) -> object:
        self.load_calls.append(session_id)
        if self.load_results:
            return self.load_results.popleft()
        return self.snapshots.get(session_id, SessionAbsent(reason="not_found"))

    async def save(self, *args: object, **kwargs: object) -> None:
        self.save_calls.append((args, kwargs))
        raise AssertionError("session HTTP read path called CAS")


class RuntimeSpy:
    def __init__(self, context: object) -> None:
        self.context = context
        self.calculation_version = VERSION
        self.orchestrator = ForbiddenComponent()
        self.artifacts = ForbiddenComponent()
        self.cache = ForbiddenComponent()
        self.engine = ForbiddenComponent()
        self.closed = False
        self.block_close = False
        self.close_entered = asyncio.Event()
        self.close_release = asyncio.Event()

    async def reap_expired(self, *, now: datetime | None = None) -> int:
        return 0

    async def drain(self) -> None:
        return None

    async def aclose(self) -> None:
        self.close_entered.set()
        if self.block_close:
            await self.close_release.wait()
        self.closed = True

    def assert_no_calculation(self) -> None:
        for component in (self.orchestrator, self.artifacts, self.cache, self.engine):
            assert component.calls == []


@pytest.fixture
def utc_clock() -> UtcClock:
    return UtcClock()


@pytest.fixture
def scheduler() -> ManualScheduler:
    return ManualScheduler()


@pytest.fixture
def context(utc_clock: UtcClock) -> ScriptedContext:
    return ScriptedContext(utc_clock)


@pytest.fixture
def runtime(context: ScriptedContext) -> RuntimeSpy:
    return RuntimeSpy(context)


@pytest.fixture
def app_client(utc_clock: UtcClock, scheduler: ManualScheduler):
    @asynccontextmanager
    async def open_client(
        runtime: RuntimeSpy,
        *,
        catalog: object | None = None,
        during_shutdown: bool = False,
        trusted_proxy_cidrs: tuple[str, ...] = (),
        limiter_policy: object | None = None,
    ) -> AsyncIterator[httpx.AsyncClient]:
        # Import only when the fixture is used: collection and pure unit slices
        # remain independent of the as-yet absent transport package.
        from exact_orb.http_api.app import create_app

        settings = http_settings(trusted_proxy_cidrs=trusted_proxy_cidrs)
        app = create_app(
            settings=settings,
            runtime_factory=lambda: runtime,
            catalog_factory=lambda: catalog if catalog is not None else ForbiddenCatalog(),
            utc_clock=utc_clock,
            scheduler=scheduler,
            limiter_policy=limiter_policy,
        )
        lifespan = app.router.lifespan_context(app)
        await lifespan.__aenter__()
        shutdown_task: asyncio.Task[object] | None = None
        try:
            if during_shutdown:
                runtime.block_close = True
                shutdown_task = asyncio.create_task(lifespan.__aexit__(None, None, None))
                await asyncio.wait_for(runtime.close_entered.wait(), timeout=1.0)
            transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
            async with httpx.AsyncClient(
                transport=transport, base_url="https://testserver"
            ) as client:
                client.asgi_app = app  # Explicit raw-ASGI test seam, not a production API.
                yield client
        finally:
            if shutdown_task is not None:
                runtime.close_release.set()
                await asyncio.wait_for(shutdown_task, timeout=1.0)
            else:
                await lifespan.__aexit__(None, None, None)

    return open_client


@pytest.fixture
def raw_asgi():
    """Send byte-preserving headers and a raw peer without a cookie jar."""

    async def request(
        app: Any,
        *,
        method: str,
        path: str,
        headers: list[tuple[bytes, bytes]] | None = None,
        body: bytes = b"",
        chunks: list[dict[str, Any]] | None = None,
        peer: tuple[str, int] = ("127.0.0.1", 12345),
        query: bytes = b"",
    ) -> list[dict[str, Any]]:
        incoming = deque(chunks if chunks is not None else
                         [{"type": "http.request", "body": body, "more_body": False}])
        sent: list[dict[str, Any]] = []

        async def receive() -> dict[str, Any]:
            if incoming:
                return incoming.popleft()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

        async def send(message: dict[str, Any]) -> None:
            sent.append(message)

        await app(
            {
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
            },
            receive,
            send,
        )
        return sent

    return request


@pytest.fixture
def sqlite_restart(tmp_path: Path, utc_clock: UtcClock):
    """Separate persistence/runtime instances over one file, never a fake load."""

    db_path = tmp_path / "http-session-restart.sqlite3"

    @asynccontextmanager
    async def open_runtime() -> AsyncIterator[RuntimeSpy]:
        with ThreadPoolExecutor(max_workers=1) as executor:
            persistence = await SqliteSessionPersistence.open(
                db_path, executor=executor, busy_timeout_ms=250
            )
            runtime = RuntimeSpy(ContextService(persistence=persistence, clock=utc_clock))
            yield runtime

    return open_runtime
