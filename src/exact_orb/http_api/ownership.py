"""Track business request tasks until their component work is terminal."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar
from uuid import uuid4

from fastapi import Request
# FastAPI resolves postponed annotations of wrapped routes in this module.
from starlette.responses import JSONResponse

from exact_orb.http_api.operation_logging import request_finished, request_started
from exact_orb.http_api.request_boundary import ClientDisconnected


_T = TypeVar("_T")


def track_request(handler: Callable[[Request], Awaitable[_T]]) -> Callable[[Request], Awaitable[_T]]:
    """Register before validation so shutdown cannot miss an admitted request."""

    @wraps(handler)
    async def tracked(request: Request) -> _T:
        task = asyncio.current_task()
        assert task is not None
        active: set[asyncio.Task[Any]] = request.app.state.active_requests
        request_id = str(uuid4())
        request.state.request_id = request_id
        route = getattr(request.scope.get("route"), "path", "unknown")
        run_id = request_id if route == "/charts/natal" else None
        started_at = request.app.state.scheduler.now()
        active.add(task)
        request_started(request_id, request.method, route, run_id=run_id)
        try:
            response = await handler(request)
            request_finished(
                request_id, run_id=run_id, started_at=started_at,
                now=request.app.state.scheduler.now(), response=response,
            )
            return response
        except ClientDisconnected:
            request_finished(
                request_id, run_id=run_id, started_at=started_at,
                now=request.app.state.scheduler.now(), outcome="disconnected",
            )
            raise
        except asyncio.CancelledError:
            peer_disconnected = getattr(request.state, "peer_disconnected", False)
            request_finished(
                request_id, run_id=run_id, started_at=started_at,
                now=request.app.state.scheduler.now(),
                outcome="disconnected" if peer_disconnected else "cancelled",
            )
            if peer_disconnected:
                raise ClientDisconnected from None
            raise
        except Exception:
            request_finished(
                request_id, run_id=run_id, started_at=started_at,
                now=request.app.state.scheduler.now(), outcome="failed",
                status_code=500, public_code="INTERNAL_FAILURE",
            )
            raise
        finally:
            observer = getattr(request.state, "disconnect_observer", None)
            if observer is not None:
                observer.cancel()
                await asyncio.gather(observer, return_exceptions=True)
            active.discard(task)

    return tracked


def observe_disconnect(request: Request) -> None:
    """Cancel the request waiter after its body has been fully parsed."""

    waiter = asyncio.current_task()
    assert waiter is not None

    async def listen() -> None:
        while True:
            message = await request.receive()
            if message["type"] == "http.disconnect":
                request.state.peer_disconnected = True
                waiter.cancel()
                return

    request.state.disconnect_observer = asyncio.create_task(listen())
