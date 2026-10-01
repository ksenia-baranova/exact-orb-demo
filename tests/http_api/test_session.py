"""AS-HTTP-01..07 and the SessionViewDTO part of AS-HTTP-28."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timezone
import base64
import json
import logging
from pathlib import Path
import re
import sqlite3

import pytest

from exact_orb.application.session_view import (
    ChartReadySessionView,
    ChartUnavailableSessionView,
    session_view,
)
from exact_orb.birth.types import (
    BirthInput,
    BirthTimeDomain,
    ResolutionWarning,
    UtcMinuteRange,
)
from exact_orb.session.outcomes import (
    SessionAbsent,
    StateCommitFailed,
    StateReadFailed,
)
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import StateDelta, apply_delta, new_session
from tests.fixtures.calculation import VERSION, artifact, chart_spec, resolved_birth_data
from tests.fixtures.stored_chart import stored_chart_for
from tests.http_api.conftest import NOW, RuntimeSpy, ScriptedContext, UtcClock


pytestmark = pytest.mark.asyncio
COOKIE_NAME = "__Host-exact_orb_session"
COOKIE_VALUE = "A" * 43
GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "session_view.json").read_text(encoding="utf-8")
)


def _cookie(value: str = COOKIE_VALUE) -> str:
    return f"{COOKIE_NAME}={value}"


def _set_cookie(response) -> str:
    values = response.headers.get_list("set-cookie")
    assert len(values) == 1
    return values[0]


def _issued_cookie(response) -> str:
    raw = _set_cookie(response)
    match = re.search(rf"(?:^|;\s*){re.escape(COOKIE_NAME)}=([A-Za-z0-9_-]{{43}})(?:;|$)", raw)
    assert match, raw
    assert "httponly" in raw.lower()
    assert "secure" in raw.lower()
    assert "samesite=lax" in raw.lower()
    assert "path=/" in raw.lower()
    assert "max-age=604800" in raw.lower()
    assert "domain=" not in raw.lower()
    assert len(base64.urlsafe_b64decode(match.group(1) + "=")) == 32
    return match.group(1)


def _cleared_cookie(response) -> None:
    raw = _set_cookie(response).lower()
    assert f"{COOKIE_NAME.lower()}=" in raw
    assert "max-age=0" in raw


def _no_set_cookie(response) -> None:
    assert response.headers.get_list("set-cookie") == []


def _snapshot(session_id: str, *, known: bool, unavailable: bool = False) -> SessionSnapshot:
    if known:
        birth = BirthInput(
            birth_date=date(1960, 9, 2), birth_time=time(14, 30), place_id="524901"
        )
        resolved = resolved_birth_data().model_copy(update={
            "utc_datetime": datetime(1960, 9, 2, 10, 30, tzinfo=timezone.utc),
            "utc_offset_seconds": 14400,
            "warnings": (
                ResolutionWarning(source="time", code="pre_1970_offset_unverified", message="private"),
                ResolutionWarning(source="time", code="noon_anchor_adjusted", message="private"),
                ResolutionWarning(source="place", code="future_private_code", message="private"),
            ),
        })
        spec = chart_spec()
    else:
        noon = datetime(1990, 9, 2, 9, 0, tzinfo=timezone.utc)
        domain = BirthTimeDomain(ranges=(UtcMinuteRange(first_utc=noon, count=1),))
        birth = BirthInput(birth_date=date(1990, 9, 2), birth_time=None, place_id="524901")
        resolved = resolved_birth_data().model_copy(update={
            "utc_datetime": noon,
            "time_unknown": True,
            "birth_time_domain": domain,
            "warnings": (
                ResolutionWarning(source="time", code="noon_anchor_ambiguous", message="private"),
            ),
        })
        spec = chart_spec(chart_kind="cosmogram")
    chart = artifact(spec=spec, resolved=resolved)
    stored = stored_chart_for(chart)
    if unavailable:
        stored = stored.model_copy(update={"payload_format": 99})
    state = apply_delta(
        new_session(session_id, now=NOW),
        StateDelta(
            birth_input=birth,
            birth_resolved=resolved,
            base_chart_spec=spec,
            base_chart_payload=stored,
        ),
        now=NOW,
    )
    return SessionSnapshot(state=state, dialog=(), chart=stored)


def _assert_no_read_side_effects(runtime: RuntimeSpy) -> None:
    runtime.assert_no_calculation()
    if isinstance(runtime.context, ScriptedContext):
        assert runtime.context.save_calls == []


async def test_chart_fixture_has_distinct_ready_and_unavailable_pure_views() -> None:
    """A passing unit control validates the test data before any HTTP app exists."""
    for known in (True, False):
        ready = _snapshot("fixture", known=known)
        unavailable = _snapshot("fixture", known=known, unavailable=True)
        before = (ready.model_copy(deep=True), unavailable.model_copy(deep=True))
        assert isinstance(session_view(ready, VERSION), ChartReadySessionView)
        assert isinstance(session_view(unavailable, VERSION), ChartUnavailableSessionView)
        assert (ready, unavailable) == before


async def test_scheduler_is_manually_advanced_without_wall_time(scheduler) -> None:
    entered = asyncio.Event()

    async def wait_for_deadline() -> None:
        entered.set()
        await scheduler.wait_until(5.0)

    task = asyncio.create_task(wait_for_deadline())
    await entered.wait()
    assert not task.done()
    await scheduler.advance(4.0)
    assert not task.done()
    await scheduler.advance(1.0)
    await task
    assert scheduler.now() == 5.0


async def test_sqlite_restart_harness_preserves_chart_without_http(sqlite_restart) -> None:
    session_id = COOKIE_VALUE
    snapshot = _snapshot(session_id, known=True)
    async with sqlite_restart() as first:
        created = await first.context.create(session_id)
        assert created.state.state_version == 0
        saved = await first.context.save(
            session_id, 0,
            StateDelta(
                birth_input=snapshot.state.birth_input,
                birth_resolved=snapshot.state.birth_resolved,
                base_chart_spec=snapshot.state.base_chart.spec,
                base_chart_payload=snapshot.chart,
            ),
        )
        assert saved.state_version == 1
    async with sqlite_restart() as second:
        assert second is not first
        assert second.cache is not first.cache
        loaded = await second.context.load(session_id)
        assert isinstance(loaded, SessionSnapshot)
        assert loaded.chart == snapshot.chart
        assert loaded.state.state_version == 1
        _assert_no_read_side_effects(second)


async def test_first_bootstrap_then_empty_current_has_exact_cookie_and_no_calculation(
    app_client, runtime: RuntimeSpy, context: ScriptedContext, caplog
) -> None:
    caplog.set_level(logging.INFO)
    async with app_client(runtime) as client:
        created = await client.post("/session/bootstrap", json={})
        assert created.status_code == 200
        assert created.json() == {"status": "ready", "state_version": 0}
        session_id = _issued_cookie(created)
        assert context.create_calls == [session_id]
        assert context.load_calls == []
        assert any("http_cookie_replaced" in record.message and "missing" in record.message
                   for record in caplog.records)
        client.cookies.clear()
        current = await client.get("/charts/current", headers={"Cookie": _cookie(session_id)})
        assert current.status_code == 200
        assert current.json() == GOLDEN["empty"]
        assert _issued_cookie(current) == session_id
        assert context.load_calls == [session_id]
    _assert_no_read_side_effects(runtime)


async def test_restart_uses_same_sqlite_file_with_new_runtime_and_empty_cache(
    app_client, sqlite_restart
) -> None:
    async with sqlite_restart() as first:
        async with app_client(first) as client:
            created = await client.post("/session/bootstrap", json={})
            assert created.status_code == 200
            session_id = _issued_cookie(created)
            snapshot = _snapshot(session_id, known=True)
            saved = await first.context.save(
                session_id, 0,
                StateDelta(
                    birth_input=snapshot.state.birth_input,
                    birth_resolved=snapshot.state.birth_resolved,
                    base_chart_spec=snapshot.state.base_chart.spec,
                    base_chart_payload=snapshot.chart,
                ),
            )
            assert saved.state_version == 1
        _assert_no_read_side_effects(first)
    async with sqlite_restart() as second:
        assert second is not first
        assert second.cache is not first.cache
        async with app_client(second) as client:
            headers = {"Cookie": _cookie(session_id)}
            restored = await client.post("/session/bootstrap", json={}, headers=headers)
            assert restored.status_code == 200
            assert restored.json() == {"status": "ready", "state_version": 1}
            assert _issued_cookie(restored) == session_id
            assert "chart" not in restored.json()
            current = await client.get("/charts/current", headers=headers)
            assert current.status_code == 200
            assert current.json()["status"] == "chart_ready"
            assert current.json()["state_version"] == 1
            assert current.json()["chart"]["chart_identity"] == snapshot.chart.calculation_key
            assert _issued_cookie(current) == session_id
            loaded = await second.context.load(session_id)
            assert loaded.state.state_version == 1
        _assert_no_read_side_effects(second)


@pytest.mark.parametrize("kind", ("stale", "unavailable", "empty"))
async def test_current_projects_stale_unavailable_or_empty_without_mutation(
    kind: str, app_client, runtime: RuntimeSpy, context: ScriptedContext, caplog
) -> None:
    if kind == "empty":
        context.snapshots[COOKIE_VALUE] = SessionSnapshot(
            state=new_session(COOKIE_VALUE, now=NOW), dialog=(), chart=None
        )
    else:
        context.snapshots[COOKIE_VALUE] = _snapshot(
            COOKIE_VALUE, known=True, unavailable=kind == "unavailable"
        )
    before = context.snapshots[COOKIE_VALUE].model_copy(deep=True)
    if kind == "stale":
        runtime.calculation_version = "later-version"
    async with app_client(runtime) as client:
        result = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert result.status_code == 200
        body = result.json()
        assert body["status"] == ("chart_ready" if kind == "stale" else
                                  "chart_unavailable" if kind == "unavailable" else "empty")
        assert body["chart_stale"] is (True if kind == "stale" else None)
        if kind == "stale":
            assert isinstance(body["chart"], dict)
        else:
            assert body["chart"] is None
        assert _issued_cookie(result) == COOKIE_VALUE
        if kind == "unavailable":
            assert any(record.levelname == "ERROR" and "chart_unavailable" in record.message
                       for record in caplog.records)
            assert "safe_reason" not in body
        assert context.snapshots[COOKIE_VALUE] == before
        assert context.load_calls == [COOKIE_VALUE]
    _assert_no_read_side_effects(runtime)


async def test_structural_sqlite_chart_corruption_is_503_not_unavailable(
    app_client, sqlite_restart, tmp_path: Path
) -> None:
    async with sqlite_restart() as runtime:
        session_id = COOKIE_VALUE
        await runtime.context.create(session_id)
        snapshot = _snapshot(session_id, known=True)
        saved = await runtime.context.save(
            session_id, 0,
            StateDelta(
                birth_input=snapshot.state.birth_input,
                birth_resolved=snapshot.state.birth_resolved,
                base_chart_spec=snapshot.state.base_chart.spec,
                base_chart_payload=snapshot.chart,
            ),
        )
        assert saved.state_version == 1
        db_path = tmp_path / "http-session-restart.sqlite3"
        with sqlite3.connect(db_path) as connection:
            connection.execute("DELETE FROM session_charts WHERE session_id = ?", (session_id,))
        async with app_client(runtime) as client:
            response = await client.get("/charts/current", headers={"Cookie": _cookie()})
            assert response.status_code == 503
            assert response.json()["code"] == "STATE_READ_FAILED"
            assert response.json().get("status") != "chart_unavailable"
            _no_set_cookie(response)
            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    "INSERT INTO session_charts "
                    "(session_id, payload_format, calculation_key, calculation_version, payload) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        session_id,
                        snapshot.chart.payload_format,
                        snapshot.chart.calculation_key,
                        snapshot.chart.calculation_version,
                        snapshot.chart.payload,
                    ),
                )
            control = await client.get("/charts/current", headers={"Cookie": _cookie()})
            assert control.status_code == 200
            assert control.json()["status"] == "chart_ready"
        _assert_no_read_side_effects(runtime)


@pytest.mark.parametrize("reason,code", (("expired", "SESSION_EXPIRED"), ("not_found", "SESSION_NOT_FOUND")))
async def test_absent_current_clears_cookie_and_bootstrap_replaces_it(
    reason: str, code: str, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    context.load_results.extend((SessionAbsent(reason=reason), SessionAbsent(reason=reason)))
    async with app_client(runtime) as client:
        current = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert current.status_code == 409
        assert current.json()["code"] == code
        _cleared_cookie(current)
        restored = await client.post("/session/bootstrap", json={}, headers={"Cookie": _cookie()})
        assert restored.status_code == 200
        new_id = _issued_cookie(restored)
        assert new_id != COOKIE_VALUE
        assert context.create_calls == [new_id]
        assert context.load_calls == [COOKIE_VALUE, COOKIE_VALUE]
    _assert_no_read_side_effects(runtime)


@pytest.mark.parametrize("operation", ("current", "bootstrap"))
async def test_state_read_failure_preserves_cookie_and_never_creates_session(
    operation: str, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    context.load_results.append(StateReadFailed(error_code="SESSION_SQLITE_READ_FAILED"))
    async with app_client(runtime) as client:
        response = (await client.get("/charts/current", headers={"Cookie": _cookie()})
                    if operation == "current" else
                    await client.post("/session/bootstrap", json={}, headers={"Cookie": _cookie()}))
        assert response.status_code == 503
        assert response.json()["code"] == "STATE_READ_FAILED"
        assert response.headers["Retry-After"] == "5"
        _no_set_cookie(response)
        assert context.create_calls == []
        assert context.load_calls == [COOKIE_VALUE]
        context.snapshots[COOKIE_VALUE] = SessionSnapshot(
            state=new_session(COOKIE_VALUE, now=NOW), dialog=(), chart=None
        )
        successful = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert successful.status_code == 200
        assert successful.json() == GOLDEN["empty"]
    _assert_no_read_side_effects(runtime)


@pytest.mark.parametrize("failure", ("rate", "create"))
async def test_absent_cookie_is_cleared_even_when_bootstrap_creation_fails(
    failure: str, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    context.load_results.append(SessionAbsent(reason="not_found"))
    if failure == "create":
        context.create_results.append(StateCommitFailed(error_code="SESSION_SQLITE_WRITE_FAILED"))
    async with app_client(runtime) as client:
        if failure == "rate":
            for _ in range(300):
                client.cookies.clear()
                accepted = await client.post("/session/bootstrap", json={})
                assert accepted.status_code == 200
            client.cookies.clear()
        response = await client.post("/session/bootstrap", json={}, headers={"Cookie": _cookie()})
        assert response.status_code == (429 if failure == "rate" else 503)
        assert response.json()["code"] == ("SESSION_CREATE_RATE_LIMITED" if failure == "rate"
                                           else "SESSION_CREATE_FAILED")
        _cleared_cookie(response)
        assert context.load_calls == [COOKIE_VALUE]
        assert len(context.create_calls) == (300 if failure == "rate" else 1)
        if failure == "create":
            client.cookies.clear()
            successful = await client.post("/session/bootstrap", json={})
            assert successful.status_code == 200
            assert len(context.create_calls) == 2
    _assert_no_read_side_effects(runtime)


@pytest.mark.parametrize("header", (None, _cookie("invalid"), f"{_cookie()}; {_cookie('B' * 43)}"))
async def test_missing_invalid_or_duplicate_cookie_requires_session_for_current(
    header: str | None, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    async with app_client(runtime) as client:
        headers = {} if header is None else {"Cookie": header}
        response = await client.get("/charts/current", headers=headers)
        assert response.status_code == 409
        assert response.json()["code"] == "SESSION_REQUIRED"
        if header is None:
            _no_set_cookie(response)
        else:
            _cleared_cookie(response)
        assert context.load_calls == []
        assert context.create_calls == []
        context.snapshots[COOKIE_VALUE] = SessionSnapshot(
            state=new_session(COOKIE_VALUE, now=NOW), dialog=(), chart=None
        )
        control = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert control.status_code == 200
        assert context.load_calls == [COOKIE_VALUE]
    _assert_no_read_side_effects(runtime)


async def test_duplicate_raw_cookie_is_replaced_by_bootstrap_without_loading_it(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    raw = [("Cookie", _cookie()), ("Cookie", _cookie("B" * 43))]
    async with app_client(runtime) as client:
        client.cookies.clear()
        response = await client.post("/session/bootstrap", json={}, headers={"Cookie": raw})
        assert response.status_code == 200
        new_id = _issued_cookie(response)
        assert new_id not in {COOKIE_VALUE, "B" * 43}
        assert context.load_calls == []
        assert context.create_calls == [new_id]
    _assert_no_read_side_effects(runtime)


async def test_invalid_cookie_bootstrap_creates_fresh_id_without_load(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    async with app_client(runtime) as client:
        response = await client.post(
            "/session/bootstrap", json={}, headers={"Cookie": _cookie("invalid")}
        )
        assert response.status_code == 200
        session_id = _issued_cookie(response)
        assert session_id != "invalid"
        assert context.create_calls == [session_id]
        assert context.load_calls == []
    _assert_no_read_side_effects(runtime)


async def test_live_bootstrap_does_not_project_unavailable_chart(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    context.snapshots[COOKIE_VALUE] = _snapshot(COOKIE_VALUE, known=True, unavailable=True)
    async with app_client(runtime) as client:
        restored = await client.post("/session/bootstrap", json={}, headers={"Cookie": _cookie()})
        assert restored.status_code == 200
        assert restored.json() == {"status": "ready", "state_version": 1}
        assert _issued_cookie(restored) == COOKIE_VALUE
        assert context.create_calls == []
        current = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert current.status_code == 200
        assert current.json()["status"] == "chart_unavailable"
        assert context.load_calls == [COOKIE_VALUE, COOKIE_VALUE]
    _assert_no_read_side_effects(runtime)


async def test_three_id_conflicts_stop_without_foreign_load_or_fourth_id(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    context.create_results.extend(("conflict", "conflict", "conflict"))
    async with app_client(runtime) as client:
        failed = await client.post("/session/bootstrap", json={})
        assert failed.status_code == 503
        assert failed.json()["code"] == "SESSION_CREATE_FAILED"
        assert failed.json()["detail_code"] == "SESSION_ID_COLLISION_RETRY_EXHAUSTED"
        _no_set_cookie(failed)
        assert len(context.create_calls) == 3
        assert len(set(context.create_calls)) == 3
        assert context.load_calls == []
        succeeded = await client.post("/session/bootstrap", json={})
        assert succeeded.status_code == 200
        assert context.create_calls[-1] == _issued_cookie(succeeded)
    _assert_no_read_side_effects(runtime)


async def test_create_storage_failure_does_not_issue_cookie_and_success_is_control(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    context.create_results.append(StateCommitFailed(error_code="SESSION_SQLITE_WRITE_FAILED"))
    async with app_client(runtime) as client:
        failed = await client.post("/session/bootstrap", json={})
        assert failed.status_code == 503
        assert failed.json()["code"] == "SESSION_CREATE_FAILED"
        _no_set_cookie(failed)
        succeeded = await client.post("/session/bootstrap", json={})
        assert succeeded.status_code == 200
        assert len(context.create_calls) == 2
        assert _issued_cookie(succeeded) == context.create_calls[-1]
    _assert_no_read_side_effects(runtime)


async def test_creation_rolling_hour_limit_restore_and_exact_expiry_boundary(
    app_client, runtime: RuntimeSpy, context: ScriptedContext, scheduler
) -> None:
    async with app_client(runtime) as client:
        first_cookie = None
        for index in range(300):
            client.cookies.clear()
            response = await client.post("/session/bootstrap", json={})
            assert response.status_code == 200, index
            first_cookie = first_cookie or _issued_cookie(response)
        assert len(context.create_calls) == 300
        client.cookies.clear()
        rejected = await client.post("/session/bootstrap", json={})
        assert rejected.status_code == 429
        assert rejected.json()["code"] == "SESSION_CREATE_RATE_LIMITED"
        assert rejected.json()["detail_code"] == "IP_HOURLY_LIMIT"
        assert rejected.headers["Retry-After"] == "3600"
        _no_set_cookie(rejected)
        assert len(context.create_calls) == 300
        live = await client.post("/session/bootstrap", json={}, headers={"Cookie": _cookie(first_cookie)})
        assert live.status_code == 200
        assert _issued_cookie(live) == first_cookie
        assert len(context.create_calls) == 300
        await scheduler.advance(3600)
        client.cookies.clear()
        fresh = await client.post("/session/bootstrap", json={})
        assert fresh.status_code == 200
        assert len(context.create_calls) == 301
    _assert_no_read_side_effects(runtime)


async def test_collision_attempts_consume_one_creation_quota_for_http_request(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    async with app_client(runtime) as client:
        for index in range(299):
            client.cookies.clear()
            response = await client.post("/session/bootstrap", json={})
            assert response.status_code == 200, index
        context.create_results.extend(("conflict", "conflict"))
        client.cookies.clear()
        accepted = await client.post("/session/bootstrap", json={})
        assert accepted.status_code == 200
        assert len(context.create_calls) == 302
        client.cookies.clear()
        rejected = await client.post("/session/bootstrap", json={})
        assert rejected.status_code == 429
        assert len(context.create_calls) == 302
    _assert_no_read_side_effects(runtime)


@pytest.mark.parametrize("known,unavailable", ((True, False), (True, True), (False, False), (False, True)))
async def test_session_view_birth_golden_exact_whitelist(
    known: bool, unavailable: bool, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    snapshot = _snapshot(COOKIE_VALUE, known=known, unavailable=unavailable)
    context.snapshots[COOKIE_VALUE] = snapshot
    key = ("known" if known else "unknown") + ("_unavailable" if unavailable else "_ready")
    async with app_client(runtime) as client:
        response = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert response.status_code == 200
        body = response.json()
        if not unavailable:
            assert isinstance(body["chart"], dict)
            assert body["chart"]["chart_identity"] == snapshot.chart.calculation_key
            # Prompt 02 fixes the complete ChartDTO golden. This normalization
            # keeps the SessionViewDTO and BirthViewDTO golden exact in prompt 01.
            body["chart"] = "<ChartDTO>"
        assert body == GOLDEN[key]
        assert "noon_anchor" not in json.dumps(response.json())
        assert "private" not in json.dumps(response.json())
    _assert_no_read_side_effects(runtime)


@pytest.mark.parametrize("defect", ("unknown_flag", "nonzero_seconds"))
async def test_invalid_saved_birth_projection_is_safe_500_with_renew_and_success_control(
    defect: str, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    valid = _snapshot(COOKIE_VALUE, known=True)
    bad_birth = valid.state.birth_input.model_copy(update={
        "birth_time": time(14, 30, 1) if defect == "nonzero_seconds" else None
    })
    bad_state = valid.state.model_copy(update={"birth_input": bad_birth})
    context.snapshots[COOKIE_VALUE] = valid.model_copy(update={"state": bad_state})
    async with app_client(runtime) as client:
        failed = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert failed.status_code == 500
        assert failed.json()["code"] == "INTERNAL_FAILURE"
        assert failed.json()["retryable"] is False
        assert _issued_cookie(failed) == COOKIE_VALUE
        context.snapshots[COOKIE_VALUE] = valid
        successful = await client.get("/charts/current", headers={"Cookie": _cookie()})
        assert successful.status_code == 200
        assert successful.json()["status"] == "chart_ready"
    _assert_no_read_side_effects(runtime)
