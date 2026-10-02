"""Reusable HTTP contract data and leaf stubs; no test-module imports."""

from __future__ import annotations

import base64
import re
from collections import deque
from typing import Callable

from exact_orb.application.application_results import (
    ApplicationCalculationFailure,
    ApplicationCommitted,
    ApplicationInputRequired,
    ApplicationInternalFailure,
    ApplicationResolutionFailure,
    ApplicationStateCommitFailure,
    ApplicationStateReadFailure,
)
from exact_orb.application.failure_policy import describe_failure
from exact_orb.birth.places import PlaceSuggestion, PlaceSuggestions
from exact_orb.outcomes import Issue
from tests.http_api.chart_samples import natal_sample


COOKIE_VALUE = "A" * 43
COOKIE = "__Host-exact_orb_session=" + COOKIE_VALUE
SESSION_ID = COOKIE_VALUE
VALID_BUILD = {"birth_date": "1985-09-02", "birth_time": "00:45", "place_id": "524901"}
PUBLIC_ITEM = {
    "place_id": "524901", "display_name": "Москва, Россия",
    "admin1_name": "Москва", "country_code": "RU",
}


def cookie(index: int) -> str:
    token = base64.urlsafe_b64encode(bytes([index]) * 32).rstrip(b"=").decode("ascii")
    return f"__Host-exact_orb_session={token}"


def build(*, place_id: str = "524901") -> dict[str, object]:
    return {**VALID_BUILD, "place_id": place_id}


def set_cookie(response) -> str:
    values = response.headers.get_list("set-cookie")
    assert len(values) == 1
    return values[0]


def issued_cookie(response) -> str:
    raw = set_cookie(response)
    match = re.search(r"(?:^|;\s*)__Host-exact_orb_session=([A-Za-z0-9_-]{43})(?:;|$)", raw)
    assert match, raw
    lower = raw.lower()
    assert "httponly" in lower
    assert "secure" in lower
    assert "samesite=lax" in lower
    assert "path=/" in lower
    assert "max-age=604800" in lower
    assert "domain=" not in lower
    assert len(base64.urlsafe_b64decode(match.group(1) + "=")) == 32
    return match.group(1)


def cleared_cookie(response) -> None:
    raw = set_cookie(response).lower()
    assert "__host-exact_orb_session=" in raw
    assert "max-age=0" in raw
    assert "secure" in raw
    assert "path=/" in raw
    assert "domain=" not in raw


def no_set_cookie(response) -> None:
    assert response.headers.get_list("set-cookie") == []


class ScriptedCatalog:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []
        self.results: deque[object] = deque()
        self.closed = False

    async def search(self, query: str, *, limit: int = 10):
        self.calls.append((query, limit))
        if self.results:
            result = self.results.popleft()
            if isinstance(result, BaseException):
                raise result
            return result
        if query == "Москва":
            return PlaceSuggestions(items=(PlaceSuggestion(**PUBLIC_ITEM),))
        return PlaceSuggestions(items=())

    async def aclose(self) -> None:
        self.closed = True


class ScriptedOrchestrator:
    def __init__(self, result_factory: Callable | None = None) -> None:
        self.calls: list[tuple[object, str, object]] = []
        self.result_factory = result_factory or committed
        self.results: deque[Callable] = deque()

    async def execute(self, command, *, session_id: str, run):
        self.calls.append((command, session_id, run))
        factory = self.results.popleft() if self.results else self.result_factory
        return factory(run)


def committed(run):
    return ApplicationCommitted(run_id=run.run_id, state_version=1, artifact=natal_sample())


def input_required(run, *, field: str = "birth.place", code: str = "INVALID",
                   constraints: dict | None = None):
    return ApplicationInputRequired(
        run_id=run.run_id, state_version=0,
        issues=(Issue(field=field, code=code, constraints=constraints),),
        user_message=describe_failure(kind="input_required").user_message,
    )


def application_failure(kind: str, run):
    if kind in {"resolution_retryable", "resolution_terminal"}:
        retryable = kind == "resolution_retryable"
        detail = "PLACE_CATALOG_UNAVAILABLE" if retryable else "TIMEZONE_DATA_INVALID"
        reaction = describe_failure(
            kind="resolution_unavailable", error_code=detail, retryable=retryable
        )
        return ApplicationResolutionFailure(
            run_id=run.run_id, state_version=0, detail_code=detail,
            user_message=reaction.user_message, retryable=retryable,
        )
    if kind in {"ephemeris", "calculation_terminal"}:
        detail = "EPHEMERIS_UNAVAILABLE" if kind == "ephemeris" else "HOUSES_DEGENERATE"
        reaction = describe_failure(kind="calculation_failed", error_code=detail)
        return ApplicationCalculationFailure(
            run_id=run.run_id, state_version=0, detail_code=detail,
            user_message=reaction.user_message, retryable=reaction.retryable,
        )
    if kind == "read":
        detail = "SESSION_SQLITE_READ_FAILED"
        reaction = describe_failure(kind="state_read_failed", error_code=detail)
        return ApplicationStateReadFailure(
            run_id=run.run_id, detail_code=detail, user_message=reaction.user_message
        )
    if kind == "commit":
        detail = "SESSION_SQLITE_WRITE_FAILED"
        reaction = describe_failure(kind="state_commit_failed", error_code=detail)
        return ApplicationStateCommitFailure(
            run_id=run.run_id, detail_code=detail, user_message=reaction.user_message
        )
    if kind in {"unregistered", "internal_loaded"}:
        if kind == "unregistered":
            return ApplicationInternalFailure(
                run_id=run.run_id, handler_status="NOT_STARTED",
                context_status="NOT_ACCESSED", code="HANDLER_NOT_REGISTERED",
                user_message=describe_failure(kind="handler_not_registered").user_message,
            )
        return ApplicationInternalFailure(
            run_id=run.run_id, handler_status="UNEXPECTED_FAILURE",
            context_status="LOADED", code="INTERNAL_FAILURE", state_version=0,
            user_message=describe_failure(kind="internal_failure").user_message,
        )
    raise AssertionError(kind)
