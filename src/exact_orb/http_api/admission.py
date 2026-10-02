"""Process-local rolling limits and owned build permits for the HTTP boundary."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from math import ceil
from typing import Any


@dataclass(frozen=True, slots=True)
class WindowLimit:
    limit: int
    seconds: float


@dataclass(frozen=True, slots=True)
class LimiterPolicy:
    session_create_ip: WindowLimit = WindowLimit(300, 3600)
    build_session_hourly: WindowLimit = WindowLimit(20, 3600)
    build_session_daily: WindowLimit = WindowLimit(100, 86400)
    build_ip_hourly: WindowLimit = WindowLimit(300, 3600)
    build_ip_daily: WindowLimit = WindowLimit(1500, 86400)
    place_search_ip: WindowLimit = WindowLimit(120, 60)
    active_builds: int = 5


DEFAULT_POLICY = LimiterPolicy()


@dataclass(frozen=True, slots=True)
class AdmissionRejection:
    code: str
    detail_code: str | None
    retry_after: int
    scope: str
    kind: str = "rate"

    @property
    def status_code(self) -> int:
        return 503 if self.kind == "capacity" else 429


class AdmissionPermitError(RuntimeError):
    """A build permit was released by the wrong owner or more than once."""


class BuildPermit:
    """One accepted build's capacity ownership, released by its owner task."""

    __slots__ = ("_controller",)

    def __init__(self, controller: AdmissionController) -> None:
        self._controller = controller

    async def release(self) -> None:
        await self._controller.release_build(self)


class AdmissionController:
    """Atomically check rolling windows and reserve one build permit."""

    def __init__(self, *, policy: Any = DEFAULT_POLICY, now: Callable[[], float]) -> None:
        self.policy = policy
        self._now = now
        self._lock = asyncio.Lock()
        self._buckets: dict[tuple[str, str], deque[float]] = {}
        self._permits: set[BuildPermit] = set()

    @property
    def active_bucket_count(self) -> int:
        """Lifecycle introspection; keys with only expired events are pruned on admission."""

        return len(self._buckets)

    @property
    def active_build_count(self) -> int:
        return len(self._permits)

    def _prune(self, now: float) -> None:
        for key, events in tuple(self._buckets.items()):
            rule = getattr(self.policy, key[0])
            while events and events[0] + rule.seconds <= now:
                events.popleft()
            if not events:
                del self._buckets[key]

    def _next_allowed(self, bucket: str, identity: str, now: float) -> float | None:
        rule = getattr(self.policy, bucket)
        events = self._buckets.get((bucket, identity), ())
        if len(events) < rule.limit:
            return None
        return events[len(events) - rule.limit] + rule.seconds

    def _record(self, bucket: str, identity: str, now: float) -> None:
        self._buckets.setdefault((bucket, identity), deque()).append(now)

    async def reserve_session_create(self, *, client_ip: str) -> AdmissionRejection | None:
        async with self._lock:
            now = self._now()
            self._prune(now)
            next_time = self._next_allowed("session_create_ip", client_ip, now)
            if next_time is not None:
                return AdmissionRejection(
                    "SESSION_CREATE_RATE_LIMITED", "IP_HOURLY_LIMIT",
                    max(1, ceil(next_time - now)), "ip",
                )
            self._record("session_create_ip", client_ip, now)
            return None

    async def reserve_place_search(self, *, client_ip: str) -> AdmissionRejection | None:
        async with self._lock:
            now = self._now()
            self._prune(now)
            next_time = self._next_allowed("place_search_ip", client_ip, now)
            if next_time is not None:
                return AdmissionRejection(
                    "PLACE_SEARCH_RATE_LIMITED", "IP_MINUTE_LIMIT",
                    max(1, ceil(next_time - now)), "ip",
                )
            self._record("place_search_ip", client_ip, now)
            return None

    async def reserve_build(
        self, *, session_id: str, client_ip: str,
    ) -> BuildPermit | AdmissionRejection:
        async with self._lock:
            now = self._now()
            self._prune(now)
            specs = (
                ("build_session_hourly", session_id, "session", "hourly"),
                ("build_session_daily", session_id, "session", "daily"),
                ("build_ip_hourly", client_ip, "ip", "hourly"),
                ("build_ip_daily", client_ip, "ip", "daily"),
            )
            exhausted = [
                (next_time, scope, period)
                for bucket, identity, scope, period in specs
                if (next_time := self._next_allowed(bucket, identity, now)) is not None
            ]
            if exhausted:
                next_time, scope, period = min(
                    exhausted,
                    key=lambda item: (
                        -item[0], 0 if item[1] == "session" else 1,
                        0 if item[2] == "daily" else 1,
                    ),
                )
                return AdmissionRejection(
                    "BUILD_SESSION_RATE_LIMITED" if scope == "session" else "BUILD_IP_RATE_LIMITED",
                    f"{scope.upper()}_{period.upper()}_LIMIT",
                    max(1, ceil(next_time - now)), scope,
                )
            if len(self._permits) >= self.policy.active_builds:
                return AdmissionRejection(
                    "BUILD_CAPACITY_EXHAUSTED", None, 1, "process", "capacity",
                )
            for bucket, identity, _, _ in specs:
                self._record(bucket, identity, now)
            permit = BuildPermit(self)
            self._permits.add(permit)
            return permit

    async def release_build(self, permit: BuildPermit) -> None:
        async with self._lock:
            if permit not in self._permits:
                raise AdmissionPermitError("build permit is not active in this controller")
            self._permits.remove(permit)
