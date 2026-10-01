"""AS-HTTP-16..22: build races, recovery, rolling admission, and capacity."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import date, time
from typing import Any

import pytest

from exact_orb.application.application_results import (
    ApplicationAlreadyApplied,
    ApplicationCommitted,
    ApplicationSessionAbsent,
    ApplicationStateCommitFailure,
    ApplicationSuperseded,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.failure_policy import describe_failure
from exact_orb.birth.types import BirthInput
from exact_orb.session.persistence import SessionSnapshot
from tests.fixtures.calculation import run_context
from tests.http_api.admission_cases import (
    ExhaustedBucket,
    SmallLimiterPolicy,
    WindowLimit,
    dominant_bucket,
    next_allowed,
)
from tests.http_api.conftest import RuntimeSpy
from tests.http_api.chart_samples import natal_sample
from tests.http_api.build_support import (
    BlockedOrchestrator, RetainedBlockedOrchestrator, TerminalHeldOrchestrator,
    real_orchestrator as _real_orchestrator,
)
from tests.http_api.shared import (
    COOKIE, SESSION_ID, ScriptedCatalog,
    build as _build, cookie as _cookie,
    committed as _committed, input_required as _input_required,
    issued_cookie, cleared_cookie,
)


def _assert_headers(response) -> None:
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"]


def _assert_rate(response, code: str, detail: str, delay: int) -> None:
    assert response.status_code == 429
    assert response.json()["code"] == code
    assert response.json()["detail_code"] == detail
    assert response.json()["retryable"] is True
    assert response.headers["Retry-After"] == str(delay)
    _assert_headers(response)


def test_window_oracle_is_inclusive_and_selects_latest_bucket_with_ties() -> None:
    rule = WindowLimit(2, 7)
    assert next_allowed(6.999, (0, 0), rule) == 7
    assert next_allowed(7, (0, 0), rule) is None
    assert next_allowed(4, (0, 2, 3), rule) == 9
    assert dominant_bucket(4, (
        ExhaustedBucket("session", "hourly", 9),
        ExhaustedBucket("ip", "daily", 11.2),
    )) == ("ip", "daily", 8)
    assert dominant_bucket(4, (
        ExhaustedBucket("ip", "daily", 9),
        ExhaustedBucket("session", "hourly", 9),
        ExhaustedBucket("session", "daily", 9),
    )) == ("session", "daily", 5)
    assert dominant_bucket(9, (ExhaustedBucket("ip", "hourly", 9.01),)) == (
        "ip", "hourly", 1
    )
    with pytest.raises(FrozenInstanceError):
        SmallLimiterPolicy().active_builds = 6


def test_recovery_result_samples_are_real_typed_application_models() -> None:
    run = run_context()
    artifact = natal_sample()
    committed = ApplicationCommitted(run_id=run.run_id, state_version=1,
                                     artifact=artifact)
    already = ApplicationAlreadyApplied(run_id=run.run_id, state_version=1,
                                        artifact=artifact)
    superseded = ApplicationSuperseded(
        run_id=run.run_id, state_version=1,
        user_message=describe_failure(kind="superseded").user_message,
    )
    absent = ApplicationSessionAbsent(
        run_id=run.run_id, handler_status="SUCCESS", reason="expired",
        code="SESSION_LOST_DURING_OPERATION",
        user_message=describe_failure(kind="session_absent", reason="expired",
                                      stage="commit").user_message,
    )
    absent_at_load = ApplicationSessionAbsent(
        run_id=run.run_id, handler_status="NOT_STARTED", reason="not_found",
        code="SESSION_NOT_FOUND",
        user_message=describe_failure(kind="session_absent", reason="not_found",
                                      stage="load").user_message,
    )
    commit_failed = ApplicationStateCommitFailure(
        run_id=run.run_id, detail_code="SESSION_SQLITE_WRITE_FAILED",
        user_message=describe_failure(kind="state_commit_failed",
                                      error_code="SESSION_SQLITE_WRITE_FAILED").user_message,
    )
    assert (committed.context_status, already.context_status,
            superseded.context_status, absent.context_status,
            commit_failed.context_status) == (
        "COMMITTED", "ALREADY_APPLIED", "SUPERSEDED", "SESSION_ABSENT", "COMMIT_FAILED"
    )
    assert absent_at_load.code == "SESSION_NOT_FOUND"


def test_production_admission_defaults_match_approved_windows() -> None:
    # Import is local so pure arithmetic and HTTP test collection work before prompt 10.
    from exact_orb.http_api.admission import DEFAULT_POLICY

    expected = {
        "session_create_ip": (300, 3600),
        "build_session_hourly": (20, 3600),
        "build_session_daily": (100, 86400),
        "build_ip_hourly": (300, 3600),
        "build_ip_daily": (1500, 86400),
        "place_search_ip": (120, 60),
    }
    assert {key: (getattr(DEFAULT_POLICY, key).limit,
                  getattr(DEFAULT_POLICY, key).seconds) for key in expected} == expected
    assert DEFAULT_POLICY.active_builds == 5


@pytest.mark.asyncio
async def test_pure_limiter_window_arithmetic_without_app_factory(scheduler) -> None:
    from exact_orb.http_api.admission import AdmissionController, AdmissionRejection

    controller = AdmissionController(policy=SmallLimiterPolicy(), now=scheduler.now)
    first = await controller.reserve_build(session_id=SESSION_ID, client_ip="127.0.0.1")
    second = await controller.reserve_build(session_id=SESSION_ID, client_ip="127.0.0.1")
    assert not isinstance(first, AdmissionRejection)
    assert not isinstance(second, AdmissionRejection)
    await scheduler.advance(0.2)
    hourly = await controller.reserve_build(session_id=SESSION_ID, client_ip="127.0.0.1")
    assert isinstance(hourly, AdmissionRejection)
    assert (hourly.code, hourly.detail_code, hourly.retry_after) == (
        "BUILD_SESSION_RATE_LIMITED", "SESSION_HOURLY_LIMIT", 7
    )
    await scheduler.advance(6.8)
    at_boundary = await controller.reserve_build(session_id=SESSION_ID,
                                                 client_ip="127.0.0.1")
    assert not isinstance(at_boundary, AdmissionRejection)
    daily = await controller.reserve_build(session_id=SESSION_ID, client_ip="127.0.0.1")
    assert isinstance(daily, AdmissionRejection)
    assert (daily.code, daily.detail_code, daily.retry_after) == (
        "BUILD_SESSION_RATE_LIMITED", "SESSION_DAILY_LIMIT", 16
    )

    tie = replace(
        SmallLimiterPolicy(),
        build_session_hourly=WindowLimit(2, 7),
        build_session_daily=WindowLimit(2, 7),
        build_ip_hourly=WindowLimit(2, 7),
        build_ip_daily=WindowLimit(2, 7),
    )
    equal = AdmissionController(policy=tie, now=scheduler.now)
    assert not isinstance(await equal.reserve_build(
        session_id=SESSION_ID, client_ip="127.0.0.1"
    ), AdmissionRejection)
    assert not isinstance(await equal.reserve_build(
        session_id=SESSION_ID, client_ip="127.0.0.1"
    ), AdmissionRejection)
    rejected = await equal.reserve_build(session_id=SESSION_ID, client_ip="127.0.0.1")
    assert isinstance(rejected, AdmissionRejection)
    assert (rejected.code, rejected.detail_code, rejected.retry_after) == (
        "BUILD_SESSION_RATE_LIMITED", "SESSION_DAILY_LIMIT", 7
    )




@dataclass(frozen=True, slots=True)
class FakeSupervisor:
    """Replace process-local runtime/cache while preserving the SQLite file."""

    open_runtime: Any
    old_runtime: RuntimeSpy

    @asynccontextmanager
    async def replacement(self):
        async with self.open_runtime() as new_runtime:
            assert new_runtime is not self.old_runtime
            yield new_runtime




@pytest.mark.asyncio
async def test_real_sqlite_orchestrator_fixture_commits_without_http(
    sqlite_restart, utc_clock
) -> None:
    async with sqlite_restart() as runtime:
        await runtime.context.create(SESSION_ID)
        artifact, observed, orchestrator, _ = _real_orchestrator(runtime, utc_clock)
        command = BuildNatalCommand(birth_input=BirthInput(
            birth_date=date(1985, 9, 2), birth_time=time(0, 45), place_id="524901"
        ))
        result = await orchestrator.execute(command, session_id=SESSION_ID,
                                            run=run_context())
        assert isinstance(result, ApplicationCommitted)
        assert result.artifact == artifact
        assert observed.save_expected == [0]
        loaded = await runtime.context.load(SESSION_ID)
        assert isinstance(loaded, SessionSnapshot)
        assert loaded.state.state_version == 1
        assert loaded.chart is not None


@pytest.mark.asyncio
async def test_explicit_rebuild_uses_fresh_version_and_does_not_echo_old_chart_on_failure(
    app_client, sqlite_restart, utc_clock
) -> None:
    async with sqlite_restart() as runtime:
        await runtime.context.create(SESSION_ID)
        artifact, observed, orchestrator, _ = _real_orchestrator(runtime, utc_clock)
        from exact_orb.http_api.projectors import project_chart

        projected = project_chart(artifact)
        expected_chart = (projected.model_dump(mode="json")
                          if hasattr(projected, "model_dump") else projected)
        async with app_client(runtime) as client:
            first = await client.post("/charts/natal", json=_build(), headers={"Cookie": COOKIE})
            second = await client.post("/charts/natal", json=_build(place_id="other"),
                                       headers={"Cookie": COOKIE})
            assert first.json() == {"status": "chart_ready", "state_version": 1,
                                    "chart": expected_chart}
            assert second.json() == {"status": "chart_ready", "state_version": 2,
                                     "chart": expected_chart}
            assert observed.save_expected == [0, 1]
            assert len(orchestrator.calls) == 2
            bad = await client.post("/charts/natal", json={**_build(), "birth_date": "bad"},
                                    headers={"Cookie": COOKIE})
            assert bad.status_code == 422
            assert "chart" not in bad.json()
            observed.lost_commit = False
            unconfirmed = await client.post("/charts/natal", json=_build(place_id="third"),
                                             headers={"Cookie": COOKIE})
            assert unconfirmed.status_code == 503
            assert unconfirmed.json()["code"] == "STATE_COMMIT_FAILED"
            assert "chart" not in unconfirmed.json()
            assert observed.load_versions == [0, 1, 2]
            current = await client.get("/charts/current", headers={"Cookie": COOKIE})
            assert current.json()["state_version"] == 2
            assert current.json()["chart"] == expected_chart
            assert observed.save_expected == [0, 1, 2, 2]
            assert len(orchestrator.calls) == 3


@pytest.mark.asyncio
async def test_late_tab_post_fresh_loads_newer_version_without_client_precondition(
    app_client, sqlite_restart, utc_clock
) -> None:
    async with sqlite_restart() as runtime:
        await runtime.context.create(SESSION_ID)
        _, observed, orchestrator, _ = _real_orchestrator(runtime, utc_clock)
        async with app_client(runtime) as client:
            initial = await client.post("/charts/natal", json=_build(),
                                        headers={"Cookie": COOKIE})
            assert initial.json()["state_version"] == 1
            tab_a = await client.get("/charts/current", headers={"Cookie": COOKIE})
            tab_b = await client.get("/charts/current", headers={"Cookie": COOKIE})
            assert tab_a.json()["state_version"] == tab_b.json()["state_version"] == 1
            later_b = await client.post("/charts/natal", json=_build(place_id="B"),
                                        headers={"Cookie": COOKIE})
            later_a = await client.post("/charts/natal", json=_build(place_id="A"),
                                        headers={"Cookie": COOKIE})
            assert (later_b.json()["state_version"], later_a.json()["state_version"]) == (2, 3)
            assert observed.save_expected == [0, 1, 2]
            assert [call[0].birth_input.place_id for call in orchestrator.calls] == [
                "524901", "B", "A"
            ]
            current = await client.get("/charts/current", headers={"Cookie": COOKIE})
            assert current.json()["state_version"] == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("same_intent", (True, False))
async def test_concurrent_sqlite_intents_map_committed_already_applied_and_superseded(
    same_intent: bool, app_client, sqlite_restart, utc_clock
) -> None:
    async with sqlite_restart() as runtime:
        await runtime.context.create(SESSION_ID)
        artifact, observed, orchestrator, handler = _real_orchestrator(
            runtime, utc_clock, barrier=True
        )
        async with app_client(runtime) as client:
            first = asyncio.create_task(client.post(
                "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
            ))
            second = asyncio.create_task(client.post(
                "/charts/natal", json=_build(place_id="524901" if same_intent else "other"),
                headers={"Cookie": COOKIE},
            ))
            await asyncio.wait_for(handler.wait_entered(), timeout=1.0)
            assert handler.entered == [0, 0]
            handler.release.set()
            responses = await asyncio.wait_for(asyncio.gather(first, second), timeout=2.0)
            assert sorted(response.status_code for response in responses) == (
                [200, 200] if same_intent else [200, 409]
            )
            committed = next(response for response in responses
                             if response.json().get("status") == "chart_ready")
            assert committed.json()["state_version"] == 1
            other = next(response for response in responses if response is not committed)
            if same_intent:
                assert other.json() == {"status": "already_applied", "state_version": 1}
            else:
                assert other.json()["code"] == "RESULT_SUPERSEDED"
                assert other.json()["state_version"] == 1
                assert "chart" not in other.json()
            current = await client.get("/charts/current", headers={"Cookie": COOKIE})
            assert current.json()["chart"]["chart_identity"] == artifact.calculation_key
            assert current.json()["state_version"] == 1
            assert observed.save_expected == [0, 0]
            assert len(orchestrator.calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("commit_happened", (True, False))
async def test_lost_commit_ack_requires_current_then_explicit_fresh_post_after_restart(
    commit_happened: bool, app_client, sqlite_restart, utc_clock
) -> None:
    first_calls: int
    first_saves: list[int]
    async with sqlite_restart() as first_runtime:
        await first_runtime.context.create(SESSION_ID)
        _, observed, orchestrator, _ = _real_orchestrator(
            first_runtime, utc_clock, lost_commit=commit_happened
        )
        async with app_client(first_runtime) as client:
            response = await client.post("/charts/natal", json=_build(),
                                         headers={"Cookie": COOKIE})
            assert response.status_code == 503
            assert response.json()["code"] == "STATE_COMMIT_FAILED"
            assert response.json()["retryable"] is True
            assert response.headers["Retry-After"] == "1"
            assert "chart" not in response.json()
            assert issued_cookie(response) == SESSION_ID
            first_calls = len(orchestrator.calls)
            first_saves = observed.save_expected.copy()
            assert first_calls == 1
            assert first_saves == [0, 0]  # One execute may retry save internally.
    async with FakeSupervisor(sqlite_restart, first_runtime).replacement() as second_runtime:
        _, observed, orchestrator, _ = _real_orchestrator(second_runtime, utc_clock)
        async with app_client(second_runtime) as client:
            restored = await client.post("/session/bootstrap", json={},
                                          headers={"Cookie": COOKIE})
            assert restored.status_code == 200
            current = await client.get("/charts/current", headers={"Cookie": COOKIE})
            assert current.json()["status"] == (
                "chart_ready" if commit_happened else "empty"
            )
            assert current.json()["state_version"] == (1 if commit_happened else 0)
            assert len(orchestrator.calls) == 0
            explicit = await client.post("/charts/natal", json=_build(),
                                          headers={"Cookie": COOKIE})
            assert explicit.status_code == 200
            assert explicit.json()["state_version"] == (2 if commit_happened else 1)
            assert observed.save_expected == [1 if commit_happened else 0]
            assert len(orchestrator.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("stage,reason,code", (
    ("NOT_STARTED", "not_found", "SESSION_NOT_FOUND"),
    ("SUCCESS", "expired", "SESSION_LOST_DURING_OPERATION"),
))
async def test_build_session_absent_clears_cookie_without_creating_or_replaying_build(
    stage: str, reason: str, code: str, app_client, runtime: RuntimeSpy, context
) -> None:
    class Scripted:
        def __init__(self) -> None:
            self.calls = []

        async def execute(self, command, *, session_id, run):
            self.calls.append(command)
            if len(self.calls) == 1:
                reaction = describe_failure(
                    kind="session_absent", reason=reason,
                    stage="load" if stage == "NOT_STARTED" else "commit",
                )
                return ApplicationSessionAbsent(
                    run_id=run.run_id, handler_status=stage, reason=reason, code=code,
                    user_message=reaction.user_message,
                )
            return _committed(run)

    scripted = Scripted()
    runtime.orchestrator = scripted
    async with app_client(runtime) as client:
        failed = await client.post("/charts/natal", json=_build(),
                                   headers={"Cookie": COOKIE})
        assert failed.status_code == 409
        assert failed.json()["code"] == code
        assert "max-age=0" in failed.headers["set-cookie"].lower()
        assert context.create_calls == []
        client.cookies.clear()
        bootstrap = await client.post("/session/bootstrap", json={})
        assert bootstrap.status_code == 200
        assert len(context.create_calls) == 1
        assert len(scripted.calls) == 1
        control = await client.post("/charts/natal", json=_build())
        assert control.status_code == 200
        assert len(scripted.calls) == 2


@pytest.mark.asyncio
async def test_invalid_or_duplicate_build_cookie_stops_before_admission_and_execute(
    app_client, runtime: RuntimeSpy, context
) -> None:
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=WindowLimit(1, 7),
        build_session_daily=WindowLimit(1, 7),
        build_ip_hourly=WindowLimit(1, 7),
        build_ip_daily=WindowLimit(1, 7),
    )
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    async with app_client(runtime, limiter_policy=policy) as client:
        client.cookies.clear()
        invalid = await client.post("/charts/natal", json=_build(),
                                    headers={"Cookie": "__Host-exact_orb_session=invalid"})
        assert invalid.status_code == 409
        assert invalid.json()["code"] == "SESSION_REQUIRED"
        cleared_cookie(invalid)
        client.cookies.clear()
        duplicate = await client.post("/charts/natal", json=_build(), headers=[
            ("Cookie", COOKIE), ("Cookie", _cookie(2)),
        ])
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "SESSION_REQUIRED"
        cleared_cookie(duplicate)
        assert orchestrator.calls == context.load_calls == []
        client.cookies.clear()
        valid = await client.post("/charts/natal", json=_build(),
                                  headers={"Cookie": COOKIE})
        assert valid.status_code == 422
        assert valid.json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 1


class QuickOrchestrator:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, str, Any]] = []

    async def execute(self, command, *, session_id: str, run):
        self.calls.append((command, session_id, run))
        return _input_required(run)




@pytest.mark.asyncio
async def test_small_session_hour_and_day_windows_have_exact_inclusive_boundaries(
    app_client, runtime: RuntimeSpy, scheduler
) -> None:
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    async with app_client(runtime, limiter_policy=SmallLimiterPolicy()) as client:
        for _ in range(2):
            assert (await client.post("/charts/natal", json=_build(),
                                      headers={"Cookie": COOKIE})).json()["code"] == "INPUT_REQUIRED"
        await scheduler.advance(0.2)
        hour = await client.post("/charts/natal", json=_build(), headers={"Cookie": COOKIE})
        _assert_rate(hour, "BUILD_SESSION_RATE_LIMITED", "SESSION_HOURLY_LIMIT", 7)
        assert len(orchestrator.calls) == 2
        await scheduler.advance(6.8)
        boundary = await client.post("/charts/natal", json=_build(),
                                     headers={"Cookie": COOKIE})
        assert boundary.json()["code"] == "INPUT_REQUIRED"
        day = await client.post("/charts/natal", json=_build(), headers={"Cookie": COOKIE})
        _assert_rate(day, "BUILD_SESSION_RATE_LIMITED", "SESSION_DAILY_LIMIT", 16)
        assert len(orchestrator.calls) == 3
        await scheduler.advance(16)
        assert (await client.post("/charts/natal", json=_build(),
                                  headers={"Cookie": COOKIE})).json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 4


@pytest.mark.asyncio
async def test_small_ip_hour_and_day_windows_share_ip_across_sessions(
    app_client, runtime: RuntimeSpy, scheduler
) -> None:
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    async with app_client(runtime, limiter_policy=SmallLimiterPolicy()) as client:
        for index in range(1, 4):
            accepted = await client.post("/charts/natal", json=_build(),
                                         headers={"Cookie": _cookie(index)})
            assert accepted.json()["code"] == "INPUT_REQUIRED"
        hour = await client.post("/charts/natal", json=_build(),
                                 headers={"Cookie": _cookie(4)})
        _assert_rate(hour, "BUILD_IP_RATE_LIMITED", "IP_HOURLY_LIMIT", 11)
        assert len(orchestrator.calls) == 3
        await scheduler.advance(11)
        assert (await client.post("/charts/natal", json=_build(),
                                  headers={"Cookie": _cookie(4)})).json()["code"] == "INPUT_REQUIRED"
        day = await client.post("/charts/natal", json=_build(),
                                headers={"Cookie": _cookie(5)})
        _assert_rate(day, "BUILD_IP_RATE_LIMITED", "IP_DAILY_LIMIT", 18)
        assert len(orchestrator.calls) == 4
        await scheduler.advance(18)
        assert (await client.post("/charts/natal", json=_build(),
                                  headers={"Cookie": _cookie(5)})).json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 5


@pytest.mark.asyncio
async def test_later_ip_daily_bucket_dominates_session_hourly_and_recovers_at_boundary(
    app_client, runtime: RuntimeSpy, scheduler
) -> None:
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    async with app_client(runtime, limiter_policy=SmallLimiterPolicy()) as client:
        for _ in range(2):
            assert (await client.post("/charts/natal", json=_build(),
                                      headers={"Cookie": _cookie(1)})).status_code == 422
        await scheduler.advance(11)
        for _ in range(2):
            assert (await client.post("/charts/natal", json=_build(),
                                      headers={"Cookie": _cookie(2)})).status_code == 422
        await scheduler.advance(1)
        rejected = await client.post("/charts/natal", json=_build(),
                                     headers={"Cookie": _cookie(2)})
        _assert_rate(rejected, "BUILD_IP_RATE_LIMITED", "IP_DAILY_LIMIT", 17)
        assert len(orchestrator.calls) == 4
        await scheduler.advance(17)
        at_boundary = await client.post("/charts/natal", json=_build(),
                                        headers={"Cookie": _cookie(2)})
        assert at_boundary.json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("daily_tie", (False, True))
async def test_equal_admission_time_chooses_session_then_daily(
    daily_tie: bool, app_client, runtime: RuntimeSpy, scheduler
) -> None:
    rule = WindowLimit(2, 7)
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=rule,
        build_session_daily=rule if daily_tie else WindowLimit(3, 23),
        build_ip_hourly=rule,
        build_ip_daily=rule if daily_tie else WindowLimit(3, 29),
    )
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    async with app_client(runtime, limiter_policy=policy) as client:
        for _ in range(2):
            assert (await client.post("/charts/natal", json=_build(),
                                      headers={"Cookie": COOKIE})).status_code == 422
        denied = await client.post("/charts/natal", json=_build(),
                                   headers={"Cookie": COOKIE})
        _assert_rate(denied, "BUILD_SESSION_RATE_LIMITED",
                     "SESSION_DAILY_LIMIT" if daily_tie else "SESSION_HOURLY_LIMIT", 7)
        assert len(orchestrator.calls) == 2
        await scheduler.advance(7)
        assert (await client.post("/charts/natal", json=_build(),
                                  headers={"Cookie": COOKIE})).status_code == 422
        assert len(orchestrator.calls) == 3


@pytest.mark.asyncio
async def test_place_and_creation_ip_windows_reject_without_consuming_quota(
    app_client, runtime: RuntimeSpy, context, scheduler
) -> None:
    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog,
                          limiter_policy=SmallLimiterPolicy()) as client:
        for _ in range(2):
            assert (await client.get("/places?query=Москва")).status_code == 200
        denied = await client.get("/places?query=Москва")
        _assert_rate(denied, "PLACE_SEARCH_RATE_LIMITED", "IP_MINUTE_LIMIT", 5)
        assert len(catalog.calls) == 2
        await scheduler.advance(5)
        assert (await client.get("/places?query=Москва")).status_code == 200
        assert len(catalog.calls) == 3
        for _ in range(2):
            client.cookies.clear()
            assert (await client.post("/session/bootstrap", json={})).status_code == 200
        client.cookies.clear()
        limited = await client.post("/session/bootstrap", json={})
        _assert_rate(limited, "SESSION_CREATE_RATE_LIMITED", "IP_HOURLY_LIMIT", 11)
        assert len(context.create_calls) == 2
        await scheduler.advance(11)
        client.cookies.clear()
        assert (await client.post("/session/bootstrap", json={})).status_code == 200
        assert len(context.create_calls) == 3


@pytest.mark.asyncio
async def test_later_rejections_do_not_shift_build_place_or_creation_window(
    app_client, runtime: RuntimeSpy, scheduler, context
) -> None:
    window = WindowLimit(1, 7)
    policy = replace(
        SmallLimiterPolicy(),
        session_create_ip=window,
        build_session_hourly=window,
        build_session_daily=window,
        build_ip_hourly=window,
        build_ip_daily=window,
        place_search_ip=window,
    )
    catalog = ScriptedCatalog()
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator

    async with app_client(runtime, catalog=catalog, limiter_policy=policy) as client:
        async def attempt():
            client.cookies.clear()
            build = await client.post("/charts/natal", json=_build(),
                                      headers={"Cookie": COOKIE})
            places = await client.get("/places?query=Москва")
            client.cookies.clear()
            create = await client.post("/session/bootstrap", json={})
            return build, places, create

        first = await attempt()
        assert [response.status_code for response in first] == [422, 200, 200]
        await scheduler.advance(3)
        rejected = await attempt()
        assert [response.status_code for response in rejected] == [429, 429, 429]
        assert [response.headers["Retry-After"] for response in rejected] == ["4"] * 3
        assert len(orchestrator.calls) == len(catalog.calls) == len(context.create_calls) == 1
        await scheduler.advance(4)
        boundary = await attempt()
        assert [response.status_code for response in boundary] == [422, 200, 200]
        assert len(orchestrator.calls) == len(catalog.calls) == len(context.create_calls) == 2


@pytest.mark.asyncio
async def test_two_concurrent_builds_reserve_one_remaining_quota_slot(
    app_client, runtime: RuntimeSpy, scheduler
) -> None:
    window = WindowLimit(1, 7)
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=window, build_session_daily=window,
        build_ip_hourly=window, build_ip_daily=window,
    )
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    barrier = asyncio.Barrier(3)

    async with app_client(runtime, limiter_policy=policy) as client:
        async def post():
            await barrier.wait()
            return await client.post("/charts/natal", json=_build(),
                                     headers={"Cookie": COOKIE})

        requests = [asyncio.create_task(post()) for _ in range(2)]
        await asyncio.wait_for(barrier.wait(), timeout=1.0)
        responses = await asyncio.wait_for(asyncio.gather(*requests), timeout=2.0)
        assert sorted(response.status_code for response in responses) == [422, 429]
        assert len(orchestrator.calls) == 1
        await scheduler.advance(7)
        control = await client.post("/charts/natal", json=_build(),
                                    headers={"Cookie": COOKIE})
        assert control.status_code == 422
        assert len(orchestrator.calls) == 2


@pytest.mark.asyncio
async def test_default_cgnat_many_sessions_and_three_hundred_ip_builds(
    app_client, runtime: RuntimeSpy
) -> None:
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    async with app_client(runtime) as client:
        for index in range(1, 11):
            for _ in range(5):
                response = await client.post("/charts/natal", json=_build(),
                                             headers={"Cookie": _cookie(index)})
                assert response.json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 50
        # New process-local limiter, same direct peer: 15 sessions x 20 = 300.
    second_runtime = RuntimeSpy(runtime.context)
    second_orchestrator = QuickOrchestrator()
    second_runtime.orchestrator = second_orchestrator
    async with app_client(second_runtime) as client:
        for index in range(1, 16):
            for _ in range(20):
                response = await client.post("/charts/natal", json=_build(),
                                             headers={"Cookie": _cookie(index)})
                assert response.json()["code"] == "INPUT_REQUIRED"
        denied = await client.post("/charts/natal", json=_build(),
                                   headers={"Cookie": _cookie(16)})
        _assert_rate(denied, "BUILD_IP_RATE_LIMITED", "IP_HOURLY_LIMIT", 3600)
        assert len(second_orchestrator.calls) == 300


@pytest.mark.asyncio
async def test_direct_peer_ip_buckets_are_independent(
    app_client, runtime: RuntimeSpy, raw_asgi
) -> None:
    policy = replace(SmallLimiterPolicy(), build_ip_hourly=WindowLimit(1, 11),
                     build_ip_daily=WindowLimit(2, 29))
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator

    async def request(app, ip: str, cookie: str):
        sent = await raw_asgi(
            app, method="POST", path="/charts/natal",
            headers=[(b"content-type", b"application/json"),
                     (b"cookie", cookie.encode("ascii"))],
            body=b'{"birth_date":"1985-09-02","birth_time":"00:45","place_id":"524901"}',
            peer=(ip, 12345),
        )
        start = next(message for message in sent if message["type"] == "http.response.start")
        return start["status"]

    async with app_client(runtime, limiter_policy=policy) as client:
        assert await request(client.asgi_app, "127.0.0.1", _cookie(1)) == 422
        assert await request(client.asgi_app, "127.0.0.1", _cookie(2)) == 429
        assert await request(client.asgi_app, "127.0.0.2", _cookie(3)) == 422
        assert len(orchestrator.calls) == 2


@pytest.mark.asyncio
async def test_rate_wins_over_full_capacity_and_neither_rejection_spends_quota(
    app_client, runtime: RuntimeSpy, scheduler
) -> None:
    rule = WindowLimit(5, 7)
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=rule, build_session_daily=rule,
        build_ip_hourly=rule, build_ip_daily=rule, active_builds=5,
    )
    blocked = BlockedOrchestrator()
    runtime.orchestrator = blocked
    async with app_client(runtime, limiter_policy=policy) as client:
        tasks = [asyncio.create_task(client.post(
            "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
        )) for _ in range(5)]
        admitted: asyncio.Task | None = None
        try:
            await asyncio.wait_for(blocked.wait_count(5), timeout=1.0)
            assert all(not task.done() for task in tasks)
            sixth = await asyncio.wait_for(client.post(
                "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
            ), timeout=1.0)
            _assert_rate(sixth, "BUILD_SESSION_RATE_LIMITED", "SESSION_DAILY_LIMIT", 7)
            assert len(blocked.calls) == 5
            await scheduler.advance(7)
            capacity = await asyncio.wait_for(client.post(
                "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
            ), timeout=1.0)
            assert capacity.status_code == 503
            assert capacity.json()["code"] == "BUILD_CAPACITY_EXHAUSTED"
            assert capacity.headers["Retry-After"] == "1"
            assert len(blocked.calls) == 5
            blocked.releases[0].set()
            assert (await asyncio.wait_for(tasks[0], timeout=1.0)).json()["code"] == "INPUT_REQUIRED"
            admitted = asyncio.create_task(client.post(
                "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
            ))
            await asyncio.wait_for(blocked.wait_count(6), timeout=1.0)
            assert not admitted.done()
            blocked.release_all()
            responses = await asyncio.wait_for(asyncio.gather(*tasks[1:], admitted),
                                               timeout=2.0)
            assert all(response.json()["code"] == "INPUT_REQUIRED"
                       for response in responses)
            assert len(blocked.calls) == 6
        finally:
            blocked.release_all()
            for task in tasks:
                if not task.done():
                    task.cancel()
            if admitted is not None and not admitted.done():
                admitted.cancel()
            await asyncio.gather(*tasks, *((admitted,) if admitted is not None else ()),
                                 return_exceptions=True)


@pytest.mark.asyncio
async def test_inactive_admission_bucket_storage_is_reaped_after_max_window(
    app_client, runtime: RuntimeSpy, scheduler, raw_asgi
) -> None:
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=WindowLimit(1, 3),
        build_session_daily=WindowLimit(1, 7),
        build_ip_hourly=WindowLimit(1, 3),
        build_ip_daily=WindowLimit(1, 7),
    )
    orchestrator = QuickOrchestrator()
    runtime.orchestrator = orchestrator
    body = b'{"birth_date":"1985-09-02","birth_time":"00:45","place_id":"524901"}'
    async with app_client(runtime, limiter_policy=policy) as client:
        for index in range(1, 31):
            sent = await raw_asgi(
                client.asgi_app, method="POST", path="/charts/natal",
                headers=[(b"content-type", b"application/json"),
                         (b"cookie", _cookie(index).encode("ascii"))],
                body=body, peer=(f"198.51.100.{index}", 12345),
            )
            assert next(message for message in sent
                        if message["type"] == "http.response.start")["status"] == 422
        admission = client.asgi_app.state.admission
        assert admission.active_bucket_count >= 30
        await scheduler.advance(7)
        sent = await raw_asgi(
            client.asgi_app, method="POST", path="/charts/natal",
            headers=[(b"content-type", b"application/json"),
                     (b"cookie", _cookie(1).encode("ascii"))],
            body=body, peer=("198.51.100.1", 12345),
        )
        assert next(message for message in sent
                    if message["type"] == "http.response.start")["status"] == 422
        assert admission.active_bucket_count <= 4
        assert len(orchestrator.calls) == 31




@pytest.mark.asyncio
@pytest.mark.parametrize("commit_before_timeout", (False, True))
async def test_timeout_is_one_execute_and_restarts_against_same_sqlite_state(
    commit_before_timeout: bool, app_client, sqlite_restart, utc_clock, scheduler
) -> None:
    async with sqlite_restart() as old_runtime:
        await old_runtime.context.create(SESSION_ID)
        _, _, real, _ = _real_orchestrator(old_runtime, utc_clock)
        held = TerminalHeldOrchestrator(real if commit_before_timeout else None)
        old_runtime.orchestrator = held
        async with app_client(old_runtime) as client:
            request = asyncio.create_task(client.post(
                "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
            ))
            try:
                await asyncio.wait_for(held.entered.wait(), timeout=1.0)
                await asyncio.wait_for(scheduler.wait_registered(30.0), timeout=1.0)
                await scheduler.advance(30)
                timeout = await asyncio.wait_for(request, timeout=1.0)
                assert timeout.status_code == 504
                assert timeout.json()["code"] == "BUILD_TIMEOUT"
                assert timeout.json()["detail_code"] == "OPERATION_DEADLINE_EXCEEDED"
                assert timeout.json()["retryable"] is False
                assert timeout.headers["Retry-After"] == "5"
                assert timeout.headers.get_list("set-cookie") == []
                assert held.calls == 1
                assert not held.completed.is_set()
                assert (await client.get("/health/live")).status_code == 503
                assert (await client.get("/health/ready")).status_code == 503
                denied = await client.post("/charts/natal", json=_build(),
                                           headers={"Cookie": COOKIE})
                assert denied.status_code == 503
                assert denied.json()["code"] == "SERVICE_SHUTTING_DOWN"
                assert denied.headers["Retry-After"] == "30"
                assert held.calls == 1
                # Fake supervisor replacement: a fresh app/runtime/cache opens
                # the same SQLite file while old work remains non-terminal.
                async with FakeSupervisor(sqlite_restart, old_runtime).replacement() as new_runtime:
                    _, observed, new_orchestrator, _ = _real_orchestrator(
                        new_runtime, utc_clock
                    )
                    async with app_client(new_runtime) as new_client:
                        assert (await new_client.get("/health/ready")).status_code == 200
                        restored = await new_client.post(
                            "/session/bootstrap", json={}, headers={"Cookie": COOKIE}
                        )
                        assert restored.status_code == 200
                        current = await new_client.get("/charts/current",
                                                       headers={"Cookie": COOKIE})
                        assert current.json()["status"] == (
                            "chart_ready" if commit_before_timeout else "empty"
                        )
                        assert current.json()["state_version"] == (
                            1 if commit_before_timeout else 0
                        )
                        assert len(new_orchestrator.calls) == 0
                        explicit = await new_client.post("/charts/natal", json=_build(),
                                                          headers={"Cookie": COOKIE})
                        assert explicit.status_code == 200
                        assert explicit.json()["state_version"] == (
                            2 if commit_before_timeout else 1
                        )
                        assert observed.save_expected == [1 if commit_before_timeout else 0]
                        assert not held.completed.is_set()
            finally:
                held.release.set()
                if not request.done():
                    request.cancel()
                await asyncio.gather(request, return_exceptions=True)


@pytest.mark.asyncio
async def test_disconnect_sends_no_headers_and_keeps_owned_permit_until_work_finishes(
    app_client, runtime: RuntimeSpy
) -> None:
    policy = replace(SmallLimiterPolicy(), active_builds=1)
    blocked = RetainedBlockedOrchestrator()
    runtime.orchestrator = blocked
    body = b'{"birth_date":"1985-09-02","birth_time":"00:45","place_id":"524901"}'
    body_sent = asyncio.Event()
    disconnect_seen = asyncio.Event()
    trigger_disconnect = asyncio.Event()
    sent: list[dict[str, Any]] = []

    async def receive():
        if not body_sent.is_set():
            body_sent.set()
            return {"type": "http.request", "body": body, "more_body": False}
        if disconnect_seen.is_set():
            await asyncio.Event().wait()
        await trigger_disconnect.wait()
        disconnect_seen.set()
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    async with app_client(runtime, limiter_policy=policy) as client:
        scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1", "scheme": "https", "method": "POST",
            "path": "/charts/natal", "raw_path": b"/charts/natal",
            "query_string": b"", "root_path": "",
            "headers": [(b"content-type", b"application/json"),
                        (b"cookie", COOKIE.encode("ascii"))],
            "client": ("127.0.0.1", 12345), "server": ("testserver", 443),
        }
        request = asyncio.create_task(client.asgi_app(scope, receive, send))
        try:
            await asyncio.wait_for(blocked.wait_count(1), timeout=1.0)
            trigger_disconnect.set()
            await asyncio.wait_for(disconnect_seen.wait(), timeout=1.0)
            denied = await asyncio.wait_for(client.post(
                "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
            ), timeout=1.0)
            assert denied.status_code == 503
            assert denied.json()["code"] == "BUILD_CAPACITY_EXHAUSTED"
            assert sent == []
            assert len(blocked.calls) == 1
        finally:
            blocked.release_all()
            await asyncio.wait_for(request, timeout=1.0)
        control_task = asyncio.create_task(client.post(
            "/charts/natal", json=_build(), headers={"Cookie": COOKIE}
        ))
        await asyncio.wait_for(blocked.wait_count(2), timeout=1.0)
        blocked.releases[1].set()
        control = await asyncio.wait_for(control_task, timeout=1.0)
        assert control.status_code == 422
        assert len(blocked.calls) == 2
