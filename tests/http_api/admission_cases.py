"""Immutable small-window policy and independent arithmetic oracle for prompt 03.

This is test input to create_app, never an environment or public setting.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True, slots=True)
class WindowLimit:
    limit: int
    seconds: float


@dataclass(frozen=True, slots=True)
class SmallLimiterPolicy:
    session_create_ip: WindowLimit = WindowLimit(2, 11)
    build_session_hourly: WindowLimit = WindowLimit(2, 7)
    build_session_daily: WindowLimit = WindowLimit(3, 23)
    build_ip_hourly: WindowLimit = WindowLimit(3, 11)
    build_ip_daily: WindowLimit = WindowLimit(4, 29)
    place_search_ip: WindowLimit = WindowLimit(2, 5)
    active_builds: int = 5


@dataclass(frozen=True, slots=True)
class ExhaustedBucket:
    scope: str
    period: str
    next_allowed: float


def dominant_bucket(now: float, exhausted: tuple[ExhaustedBucket, ...]) -> tuple[str, str, int]:
    """Specification oracle: latest next admission, then session/day priority."""

    chosen = min(
        exhausted,
        key=lambda bucket: (
            -bucket.next_allowed,
            0 if bucket.scope == "session" else 1,
            0 if bucket.period == "daily" else 1,
        ),
    )
    return chosen.scope, chosen.period, max(1, ceil(chosen.next_allowed - now))


def next_allowed(now: float, events: tuple[float, ...], rule: WindowLimit) -> float | None:
    """Oldest live event determines the next opening; expiry is inclusive."""

    live = sorted(event for event in events if event + rule.seconds > now)
    if len(live) < rule.limit:
        return None
    return live[len(live) - rule.limit] + rule.seconds
