"""Track business request tasks until their component work is terminal."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import Request
# FastAPI resolves postponed annotations of wrapped routes in this module.
from starlette.responses import JSONResponse

from exact_orb.http_api.request_boundary import ClientDisconnected


_T = TypeVar("_T")


def track_request(handler: Callable[[Request], Awaitable[_T]]) -> Callable[[Request], Awaitable[_T]]:
    """Register before validation so shutdown cannot miss an admitted request."""

    @wraps(handler)
    async def tracked(request: Request) -> _T:
        task = asyncio.current_task()
        assert task is not None
        active: set[asyncio.Task[Any]] = request.app.state.active_requests
        active.add(task)
        try:
            return await handler(request)
        except asyncio.CancelledError:
            if getattr(request.state, "peer_disconnected", False):
                raise ClientDisconnected from None
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
