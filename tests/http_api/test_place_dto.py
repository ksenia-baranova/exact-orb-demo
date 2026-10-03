"""AS-HTTP-08..15, validation priority, and public transport mappings."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
import json
from pathlib import Path
import runpy
from uuid import UUID

import pytest

from exact_orb.application.application_results import (
    ApplicationCalculationFailure,
    ApplicationCommitted,
    ApplicationInputRequired,
    ApplicationInternalFailure,
    ApplicationResolutionFailure,
    ApplicationStateCommitFailure,
    ApplicationStateReadFailure,
)
from exact_orb.application.commands import BuildNatalCommand
from exact_orb.application.failure_policy import describe_failure
from exact_orb.application.handlers.build_natal import BuildNatalHandler
from exact_orb.application.orchestrator import ApplicationOrchestrator
from exact_orb.application.session_view import ChartReadySessionView, session_view
from exact_orb.birth.adapters.sqlite import SqlitePlaceCatalog
from exact_orb.birth.places import (
    InvalidPlaceQuery,
    PlaceCatalogUnavailableError,
    PlaceSuggestion,
    PlaceSuggestions,
)
from exact_orb.birth.types import BirthInput, ResolvedBirthData
from exact_orb.calculation.codec import decode_chart_artifact, encode_chart_artifact
from exact_orb.outcomes import InputRequired, Issue
from exact_orb.session.persistence import SessionSnapshot
from exact_orb.session.state import StateDelta, StoredChart, apply_delta, new_session
from tests.application.stubs import StubBirthDataResolver, StubChartArtifactPort
from tests.http_api.chart_samples import natal_sample
from tests.http_api.conftest import NOW, RuntimeSpy, ScriptedContext
from tests.http_api.shared import (
    COOKIE, VALID_BUILD, PUBLIC_ITEM, ScriptedCatalog, ScriptedOrchestrator,
    application_failure as _application_failure,
    committed as _committed, input_required as _input_required,
    issued_cookie,
)


pytestmark = pytest.mark.asyncio
SENSITIVE = "private-internal-detail-55.7558"


def _headers(response) -> None:
    assert response.headers["Cache-Control"] == "no-store"
    assert UUID(response.headers["X-Request-ID"])


def _safe_internal(response) -> None:
    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_FAILURE"
    assert body["detail_code"] is None
    assert body["retryable"] is False
    assert SENSITIVE not in json.dumps(body)
    assert all(field not in body for field in
               ("orch_status", "handler_status", "context_status", "run_id"))
    _headers(response)


async def test_places_success_and_empty_have_exact_whitelist_without_session_access(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog) as client:
        found = await client.get("/places", params={"query": "Москва"})
        assert found.status_code == 200
        assert found.json() == {"items": [PUBLIC_ITEM]}
        assert found.headers.get_list("set-cookie") == []
        empty = await client.get("/places", params={"query": "Без совпадений"})
        assert empty.status_code == 200
        assert empty.json() == {"items": []}
        assert catalog.calls == [("Москва", 10), ("Без совпадений", 10)]
    assert context.load_calls == context.create_calls == []
    runtime.assert_no_calculation()


async def test_places_uses_real_sqlite_search_and_ignores_invalid_session_cookie(
    tmp_path: Path, app_client, runtime: RuntimeSpy, context: ScriptedContext,
) -> None:
    tests_root = Path(__file__).resolve().parents[1]
    fixtures = tests_root / "fixtures" / "place_catalog"
    build = runpy.run_path(str(tests_root.parent / "scripts" / "build_place_catalog.py"))["build"]
    db_path = tmp_path / "places.sqlite"
    build(
        cities_path=fixtures / "cities1000.txt",
        admin1_path=fixtures / "admin1CodesASCII.txt",
        alternate_names_path=fixtures / "alternateNamesV2.txt",
        out_path=db_path,
    )
    with ThreadPoolExecutor(max_workers=1) as executor:
        catalog = await SqlitePlaceCatalog.open(db_path, executor=executor)
        async with app_client(runtime, catalog=catalog) as client:
            response = await client.get(
                "/places", params={"query": "МОСКВА"},
                headers={"Cookie": "__Host-exact_orb_session=invalid"},
            )
            assert response.status_code == 200
            assert response.json() == {"items": [{
                "place_id": "524901", "display_name": "Москва",
                "admin1_name": "Москва", "country_code": "RU",
            }]}
            assert response.headers.get_list("set-cookie") == []
    assert context.create_calls == context.load_calls == context.save_calls == []
    runtime.assert_no_calculation()


@pytest.mark.parametrize("limit", (None, "1", "20"))
async def test_place_limit_boundaries_and_default_reach_search(
    limit: str | None, app_client, runtime: RuntimeSpy
) -> None:
    catalog = ScriptedCatalog()
    params = {"query": "Москва"}
    if limit is not None:
        params["limit"] = limit
    async with app_client(runtime, catalog=catalog) as client:
        response = await client.get("/places", params=params)
        assert response.status_code == 200
        assert catalog.calls == [("Москва", 10 if limit is None else int(limit))]


@pytest.mark.parametrize("limit", ("010", "+5", "5.0", " ", "0", "21", "-1"))
async def test_invalid_limit_grammar_stops_before_catalog_with_positive_control(
    limit: str, app_client, runtime: RuntimeSpy
) -> None:
    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog) as client:
        invalid = await client.get("/places", params={"query": "Москва", "limit": limit})
        assert invalid.status_code == 422
        assert invalid.json()["code"] == "INVALID_REQUEST"
        assert invalid.json()["detail_code"] == "LIMIT_INVALID"
        assert catalog.calls == []
        valid = await client.get("/places", params={"query": "Москва", "limit": "20"})
        assert valid.status_code == 200
        assert catalog.calls == [("Москва", 20)]


@pytest.mark.parametrize("query_string,detail", (
    ("limit=10", "QUERY_REQUIRED"),
    ("query=Москва&query=Москва", "QUERY_REQUIRED"),
    ("query=Москва&limit=1&limit=2", "LIMIT_INVALID"),
    ("query=Москва&extra=1", "INVALID_REQUEST"),
))
async def test_missing_duplicate_or_extra_query_parameter_stops_before_catalog(
    query_string: str, detail: str, app_client, runtime: RuntimeSpy
) -> None:
    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog) as client:
        response = await client.get("/places?" + query_string)
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_REQUEST"
        if detail != "INVALID_REQUEST":
            assert response.json()["detail_code"] == detail
        assert catalog.calls == []
        control = await client.get("/places?query=Москва")
        assert control.status_code == 200
        assert catalog.calls == [("Москва", 10)]


async def test_raw_query_length_is_checked_in_unicode_code_points_before_catalog(
    app_client, runtime: RuntimeSpy
) -> None:
    catalog = ScriptedCatalog()
    async with app_client(runtime, catalog=catalog) as client:
        response = await client.get("/places", params={"query": "Ж" * 513})
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_REQUEST"
        assert response.json()["detail_code"] == "QUERY_TOO_LONG"
        assert catalog.calls == []
        control = await client.get("/places", params={"query": "Москва"})
        assert control.status_code == 200
        assert catalog.calls == [("Москва", 10)]


@pytest.mark.parametrize("result,status,code,detail", (
    (InvalidPlaceQuery(code="CONTROL_CHARACTERS"), 422, "INVALID_PLACE_QUERY", "CONTROL_CHARACTERS"),
    (PlaceCatalogUnavailableError(SENSITIVE), 503, "PLACE_CATALOG_UNAVAILABLE", None),
    (RuntimeError(SENSITIVE), 500, "INTERNAL_FAILURE", None),
))
async def test_place_component_outcomes_map_to_safe_http_and_keep_positive_control(
    result: object, status: int, code: str, detail: str | None,
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    catalog = ScriptedCatalog()
    catalog.results.append(result)
    async with app_client(runtime, catalog=catalog) as client:
        failed = await client.get("/places", params={"query": "Москва"})
        assert failed.status_code == status
        assert failed.json()["code"] == code
        assert failed.json()["detail_code"] == detail
        assert SENSITIVE not in json.dumps(failed.json())
        if status == 503:
            assert failed.headers["Retry-After"] == "5"
            assert failed.json()["retryable"] is True
        if status == 500:
            _safe_internal(failed)
        control = await client.get("/places", params={"query": "Москва"})
        assert control.status_code == 200
        assert control.json() == {"items": [PUBLIC_ITEM]}
        assert catalog.calls == [("Москва", 10), ("Москва", 10)]
    assert context.load_calls == context.create_calls == []
    runtime.assert_no_calculation()


async def test_wrong_origin_blocks_current_and_places_but_not_health(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    catalog = ScriptedCatalog()
    context.snapshots["A" * 43] = SessionSnapshot(
        state=new_session("A" * 43, now=NOW), dialog=(), chart=None
    )
    async with app_client(runtime, catalog=catalog) as client:
        bad_origin = {"Origin": "https://elsewhere.invalid", "Cookie": COOKIE}
        current = await client.get("/charts/current", headers=bad_origin)
        places = await client.get("/places?query=Москва", headers=bad_origin)
        for response in (current, places):
            assert response.status_code == 403
            assert response.json()["code"] == "ORIGIN_NOT_ALLOWED"
        assert context.load_calls == []
        assert catalog.calls == []
        live = await client.get("/health/live", headers=bad_origin)
        ready = await client.get("/health/ready", headers=bad_origin)
        assert live.status_code == ready.status_code == 200
        assert (await client.get("/charts/current", headers={"Cookie": COOKIE})).status_code == 200
        assert (await client.get("/places?query=Москва")).status_code == 200
        assert context.load_calls == ["A" * 43]
        assert catalog.calls == [("Москва", 10)]


@pytest.mark.parametrize("content_type,accepted", (
    ("application/json", True),
    ("application/json; charset=utf-8", True),
    ("application/json; charset=utf-16", False),
    ("text/plain", False),
))
async def test_post_media_and_charset_are_strict_with_valid_control(
    content_type: str, accepted: bool,
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    async with app_client(runtime) as client:
        client.cookies.clear()
        response = await client.post(
            "/session/bootstrap", content=b"{}", headers={"Content-Type": content_type}
        )
        assert response.status_code == (200 if accepted else 415)
        assert len(context.create_calls) == (1 if accepted else 0)
        if not accepted:
            assert response.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"
            control = await client.post(
                "/session/bootstrap", content=b"{}",
                headers={"Content-Type": "application/json"},
            )
            assert control.status_code == 200
            assert len(context.create_calls) == 1


@pytest.mark.parametrize("encoding", ("identity", "gzip", "br"))
async def test_any_content_encoding_is_rejected_before_session_create(
    encoding: str, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    async with app_client(runtime) as client:
        failed = await client.post(
            "/session/bootstrap", content=b"{}",
            headers={"Content-Type": "application/json", "Content-Encoding": encoding},
        )
        assert failed.status_code == 415
        assert failed.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"
        assert context.create_calls == []
        control = await client.post("/session/bootstrap", json={})
        assert control.status_code == 200
        assert len(context.create_calls) == 1


@pytest.mark.parametrize("case,status,code", (
    ("shutdown_over_xff", 503, "SERVICE_SHUTTING_DOWN"),
    ("xff_over_origin", 400, "FORWARDED_HEADER_INVALID"),
    ("origin_over_encoding", 403, "ORIGIN_NOT_ALLOWED"),
    ("encoding_over_size", 415, "UNSUPPORTED_MEDIA_TYPE"),
    ("encoding_over_timeout", 415, "UNSUPPORTED_MEDIA_TYPE"),
    ("size_over_schema", 413, "REQUEST_TOO_LARGE"),
    ("timeout_over_schema", 408, "REQUEST_TIMEOUT"),
    ("schema_over_cookie", 422, "INVALID_REQUEST"),
))
async def test_matched_route_validation_priority_stops_before_lower_layers(
    case: str, status: int, code: str, app_client, raw_asgi, scheduler,
    runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    orchestrator = ScriptedOrchestrator(lambda run: _input_required(run))
    runtime.orchestrator = orchestrator
    proxy = case in {"shutdown_over_xff", "xff_over_origin"}
    valid_proxy = {"X-Forwarded-For": "198.51.100.10", "X-Forwarded-Proto": "https"}
    bad_proxy = {"X-Forwarded-For": "bad-hostname", "X-Forwarded-Proto": "https"}
    async with app_client(
        runtime,
        during_shutdown=case == "shutdown_over_xff",
        trusted_proxy_cidrs=("127.0.0.1/32",) if proxy else (),
    ) as client:
        if case in {"shutdown_over_xff", "xff_over_origin"}:
            headers = dict(bad_proxy)
            if case == "xff_over_origin":
                headers["Origin"] = "https://elsewhere.invalid"
            failed = await client.post("/session/bootstrap", json={}, headers=headers)
        elif case == "origin_over_encoding":
            failed = await client.post(
                "/session/bootstrap", content=b"{}",
                headers={"Origin": "https://elsewhere.invalid",
                         "Content-Type": "application/json", "Content-Encoding": "gzip"},
            )
        elif case == "encoding_over_size":
            failed = await client.post(
                "/session/bootstrap", content=b"{" * 16385,
                headers={"Content-Type": "application/json", "Content-Encoding": "gzip"},
            )
        elif case == "encoding_over_timeout":
            sent = await asyncio.wait_for(raw_asgi(
                client.asgi_app, method="POST", path="/session/bootstrap",
                headers=[(b"content-type", b"application/json"),
                         (b"content-encoding", b"gzip")],
                chunks=[{"type": "http.request", "body": b"{", "more_body": True}],
            ), timeout=1.0)
            failed_status = next(message for message in sent
                                 if message["type"] == "http.response.start")["status"]
            assert failed_status == status
            failed_body = b"".join(message.get("body", b"") for message in sent
                                   if message["type"] == "http.response.body")
            assert json.loads(failed_body)["code"] == code
            failed = None
        elif case == "size_over_schema":
            failed = await client.post(
                "/session/bootstrap", content=b"{" * 16385,
                headers={"Content-Type": "application/json"},
            )
        elif case == "timeout_over_schema":
            task = asyncio.create_task(raw_asgi(
                client.asgi_app, method="POST", path="/session/bootstrap",
                headers=[(b"content-type", b"application/json")],
                chunks=[{"type": "http.request", "body": b"{", "more_body": True}],
            ))
            await asyncio.wait_for(scheduler.wait_registered(5.0), timeout=1.0)
            await scheduler.advance(5.0)
            sent = await asyncio.wait_for(task, timeout=1.0)
            failed_status = next(message for message in sent
                                 if message["type"] == "http.response.start")["status"]
            assert failed_status == status
            failed_body = b"".join(message.get("body", b"") for message in sent
                                   if message["type"] == "http.response.body")
            assert json.loads(failed_body)["code"] == code
            failed = None
        else:
            failed = await client.post(
                "/charts/natal", content=b"{",
                headers={"Content-Type": "application/json"},
            )
        if failed is not None:
            assert failed.status_code == status
            assert failed.json()["code"] == code
            _headers(failed)
        assert context.create_calls == context.load_calls == context.save_calls == []
        assert orchestrator.calls == []

    # Same registered route succeeds past the boundary under a valid request.
    fresh_context = ScriptedContext(context.clock)
    fresh_runtime = RuntimeSpy(fresh_context)
    control_orchestrator = ScriptedOrchestrator(lambda run: _input_required(run))
    fresh_runtime.orchestrator = control_orchestrator
    async with app_client(
        fresh_runtime, trusted_proxy_cidrs=("127.0.0.1/32",) if proxy else ()
    ) as client:
        if case == "schema_over_cookie":
            control = await client.post(
                "/charts/natal", json=VALID_BUILD, headers={"Cookie": COOKIE}
            )
            assert control.status_code == 422
            assert control.json()["code"] == "INPUT_REQUIRED"
            assert len(control_orchestrator.calls) == 1
        else:
            control = await client.post(
                "/session/bootstrap", json={}, headers=valid_proxy if proxy else {}
            )
            assert control.status_code == 200
            assert len(fresh_context.create_calls) == 1


@pytest.mark.parametrize("value,valid", (("", False), ("Ж", True), ("Ж" * 128, True),
                                         ("Ж" * 129, False)),
                         ids=("empty", "one", "max", "too-long"))
async def test_place_id_code_point_boundaries_and_positive_build_path(
    value: str, valid: bool, app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    orchestrator = ScriptedOrchestrator(lambda run: _input_required(run))
    runtime.orchestrator = orchestrator
    body = {**VALID_BUILD, "place_id": value}
    async with app_client(runtime) as client:
        response = await client.post("/charts/natal", json=body, headers={"Cookie": COOKIE})
        if valid:
            assert response.status_code == 422
            assert response.json()["code"] == "INPUT_REQUIRED"
            assert len(orchestrator.calls) == 1
            assert orchestrator.calls[0][0].birth_input.place_id == value
        else:
            assert response.status_code == 422
            assert response.json()["code"] == "INVALID_REQUEST"
            assert {issue["field"] for issue in response.json()["issues"]} == {"birth.place"}
            assert orchestrator.calls == []
            control = await client.post(
                "/charts/natal", json=VALID_BUILD, headers={"Cookie": COOKIE}
            )
            assert control.json()["code"] == "INPUT_REQUIRED"
            assert len(orchestrator.calls) == 1
        assert context.load_calls == context.save_calls == []


@pytest.mark.parametrize("overrides,expected_field", (
    ({"birth_date": "1990-02-30"}, "birth.date"),
    ({"birth_date": "1990-9-2"}, "birth.date"),
    ({"birth_time": "14:30:00"}, "birth.time"),
    ({"birth_time": "14:30+03:00"}, "birth.time"),
    # AS-HTTP-12/13: combined malformed inputs are rejected before execution.
    pytest.param({"birth_date": "1990-02-30", "birth_time": "24:00"},
                 "birth.date", id="invalid-date-and-time"),
    ({"state_version": 0}, "request.state_version"),
))
async def test_build_schema_rejects_malformed_or_extra_fields_before_orchestrator(
    overrides: dict[str, object], expected_field: str,
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    orchestrator = ScriptedOrchestrator(lambda run: _input_required(run))
    runtime.orchestrator = orchestrator
    body = {**VALID_BUILD, **overrides}
    async with app_client(runtime) as client:
        rejected = await client.post("/charts/natal", json=body, headers={"Cookie": COOKIE})
        assert rejected.status_code == 422
        assert rejected.json()["code"] == "INVALID_REQUEST"
        assert expected_field in {issue["field"] for issue in rejected.json()["issues"]}
        assert orchestrator.calls == []
        assert context.load_calls == context.save_calls == []
        control = await client.post("/charts/natal", json=VALID_BUILD, headers={"Cookie": COOKIE})
        assert control.status_code == 422
        assert control.json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 1


@pytest.mark.parametrize("body", (b"{", b"[]", b"true"))
async def test_malformed_or_nonobject_json_precedes_missing_cookie(
    body: bytes, app_client, runtime: RuntimeSpy
) -> None:
    orchestrator = ScriptedOrchestrator(lambda run: _input_required(run))
    runtime.orchestrator = orchestrator
    async with app_client(runtime) as client:
        invalid = await client.post(
            "/charts/natal", content=body, headers={"Content-Type": "application/json"}
        )
        assert invalid.status_code == 422
        assert invalid.json()["code"] == "INVALID_REQUEST"
        assert orchestrator.calls == []
        valid = await client.post("/charts/natal", json=VALID_BUILD)
        assert valid.status_code == 409
        assert valid.json()["code"] == "SESSION_REQUIRED"
        assert orchestrator.calls == []
        control = await client.post("/charts/natal", json=VALID_BUILD,
                                    headers={"Cookie": COOKIE})
        assert control.json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 1


@pytest.mark.parametrize("field,value,issue_field", (
    ("birth_date", 19850902, "birth.date"),
    ("birth_time", True, "birth.time"),
    ("place_id", ["524901"], "birth.place"),
))
async def test_build_never_coerces_nonstring_json_values(
    field: str, value: object, issue_field: str, app_client, runtime: RuntimeSpy
) -> None:
    orchestrator = ScriptedOrchestrator(lambda run: _input_required(run))
    runtime.orchestrator = orchestrator
    async with app_client(runtime) as client:
        rejected = await client.post(
            "/charts/natal", json={**VALID_BUILD, field: value}, headers={"Cookie": COOKIE}
        )
        assert rejected.status_code == 422
        assert rejected.json()["code"] == "INVALID_REQUEST"
        assert issue_field in {issue["field"] for issue in rejected.json()["issues"]}
        assert orchestrator.calls == []
        control = await client.post(
            "/charts/natal", json=VALID_BUILD, headers={"Cookie": COOKIE}
        )
        assert control.json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 1


@pytest.mark.parametrize("requested_date,issue_code", (
    ("3000-01-01", "UNSUPPORTED"),
    ("1700-01-01", "UNSUPPORTED"),
    ("2011-12-30", "INVALID"),
))
async def test_calendar_valid_domain_dates_reach_application_as_typed_issues(
    requested_date: str, issue_code: str, app_client, runtime: RuntimeSpy
) -> None:
    constraints = ({"min": "1800-01-01", "max": "2399-12-31"}
                   if issue_code == "UNSUPPORTED" else None)
    orchestrator = ScriptedOrchestrator(
        lambda run: _input_required(
            run, field="birth.date", code=issue_code, constraints=constraints
        )
    )
    runtime.orchestrator = orchestrator
    async with app_client(runtime) as client:
        response = await client.post(
            "/charts/natal", json={**VALID_BUILD, "birth_date": requested_date},
            headers={"Cookie": COOKIE},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "INPUT_REQUIRED"
        assert len(response.json()["issues"]) == 1
        assert response.json()["issues"][0]["field"] == "birth.date"
        assert response.json()["issues"][0]["code"] == issue_code
        if constraints is not None:
            assert response.json()["issues"][0]["constraints"] == constraints
        assert len(orchestrator.calls) == 1
        assert orchestrator.calls[0][0].birth_input.birth_date.isoformat() == requested_date
        control = await client.post(
            "/charts/natal", json={**VALID_BUILD, "birth_date": "2399-12-31"},
            headers={"Cookie": COOKIE},
        )
        assert control.status_code == 422
        assert control.json()["code"] == "INPUT_REQUIRED"
        assert len(orchestrator.calls) == 2


async def test_valid_ephemeris_boundary_dates_reach_stub_resolver_after_schema(
    app_client, sqlite_restart, utc_clock
) -> None:
    resolver = StubBirthDataResolver(InputRequired(
        issues=(Issue(field="birth.place", code="INVALID"),)
    ))
    artifacts = StubChartArtifactPort()
    async with sqlite_restart() as runtime:
        session_id = "A" * 43
        await runtime.context.create(session_id)
        runtime.orchestrator = ApplicationOrchestrator(
            context=runtime.context,
            handlers={BuildNatalCommand: BuildNatalHandler(
                resolver=resolver, artifacts=artifacts,
            )},
            clock=utc_clock,
        )
        async with app_client(runtime) as client:
            malformed = await client.post(
                "/charts/natal", json={**VALID_BUILD, "birth_date": "1990-02-30"},
                headers={"Cookie": COOKIE},
            )
            assert malformed.status_code == 422
            assert malformed.json()["code"] == "INVALID_REQUEST"
            assert resolver.calls == 0
            for index, boundary in enumerate(("1800-01-01", "2399-12-31"), start=1):
                response = await client.post(
                    "/charts/natal", json={**VALID_BUILD, "birth_date": boundary},
                    headers={"Cookie": COOKIE},
                )
                assert response.status_code == 422
                assert response.json()["code"] == "INPUT_REQUIRED"
                assert resolver.calls == index
                assert resolver.received_birth_input.birth_date.isoformat() == boundary
            loaded = await runtime.context.load(session_id)
            assert isinstance(loaded, SessionSnapshot)
            assert loaded.state.state_version == 0
            assert loaded.chart is None
            assert artifacts.calls == artifacts.to_stored_calls == 0


@pytest.mark.parametrize("field,code", (("birth.place", "INVALID"),
                                        ("birth.time", "AMBIGUOUS")))
async def test_input_required_keeps_typed_issues_and_renews_cookie(
    field: str, code: str, app_client, runtime: RuntimeSpy
) -> None:
    orchestrator = ScriptedOrchestrator(
        lambda run: _input_required(run, field=field, code=code)
    )
    runtime.orchestrator = orchestrator
    async with app_client(runtime) as client:
        response = await client.post("/charts/natal", json=VALID_BUILD,
                                     headers={"Cookie": COOKIE})
        assert response.status_code == 422
        assert response.json()["code"] == "INPUT_REQUIRED"
        assert response.json()["state_version"] == 0
        assert response.json()["issues"][0]["field"] == field
        assert response.json()["issues"][0]["code"] == code
        assert issued_cookie(response) == COOKIE.split("=", 1)[1]
        assert len(orchestrator.calls) == 1


@pytest.mark.parametrize("kind,status,public_code,detail,retryable,cookie", (
    ("resolution_retryable", 503, "RESOLUTION_UNAVAILABLE", "PLACE_CATALOG_UNAVAILABLE", True, "renew"),
    ("resolution_terminal", 500, "RESOLUTION_UNAVAILABLE", "TIMEZONE_DATA_INVALID", False, "renew"),
    ("ephemeris", 503, "CALCULATION_FAILED", "EPHEMERIS_UNAVAILABLE", True, "renew"),
    ("calculation_terminal", 500, "CALCULATION_FAILED", "HOUSES_DEGENERATE", False, "renew"),
    ("read", 503, "STATE_READ_FAILED", "SESSION_SQLITE_READ_FAILED", True, "unchanged"),
    ("commit", 503, "STATE_COMMIT_FAILED", "SESSION_SQLITE_WRITE_FAILED", True, "renew"),
))
async def test_application_typed_failures_keep_allowed_fields_and_cookie_policy(
    kind: str, status: int, public_code: str, detail: str, retryable: bool,
    cookie: str, app_client, runtime: RuntimeSpy
) -> None:
    orchestrator = ScriptedOrchestrator()
    orchestrator.results.append(lambda run: _application_failure(kind, run))
    orchestrator.results.append(_committed)
    runtime.orchestrator = orchestrator
    async with app_client(runtime) as client:
        response = await client.post("/charts/natal", json=VALID_BUILD,
                                     headers={"Cookie": COOKIE})
        assert response.status_code == status
        body = response.json()
        assert (body["code"], body["detail_code"], body["retryable"]) == (
            public_code, detail, retryable
        )
        assert body["user_message"] == _application_failure(kind, orchestrator.calls[0][2]).user_message
        assert all(name not in body for name in ("orch_status", "handler_status", "context_status", "run_id"))
        if cookie == "renew":
            assert issued_cookie(response) == COOKIE.split("=", 1)[1]
        else:
            assert response.headers.get_list("set-cookie") == []
        _headers(response)
        control = await client.post("/charts/natal", json=VALID_BUILD,
                                    headers={"Cookie": COOKIE})
        assert control.status_code == 200
        assert control.json()["status"] == "chart_ready"
        assert len(orchestrator.calls) == 2


@pytest.mark.parametrize("kind", ("unregistered", "internal_loaded"))
async def test_internal_application_subtypes_are_hidden_by_safe_500(
    kind: str, app_client, runtime: RuntimeSpy
) -> None:
    orchestrator = ScriptedOrchestrator()
    orchestrator.results.append(lambda run: _application_failure(kind, run))
    orchestrator.results.append(lambda run: _application_failure("calculation_terminal", run))
    runtime.orchestrator = orchestrator
    async with app_client(runtime) as client:
        failed = await client.post("/charts/natal", json=VALID_BUILD,
                                   headers={"Cookie": COOKIE})
        _safe_internal(failed)
        assert "HANDLER_NOT_REGISTERED" not in json.dumps(failed.json())
        typed = await client.post("/charts/natal", json=VALID_BUILD,
                                  headers={"Cookie": COOKIE})
        assert typed.status_code == 500
        assert typed.json()["code"] == "CALCULATION_FAILED"
        assert typed.json()["detail_code"] == "HOUSES_DEGENERATE"
        assert len(orchestrator.calls) == 2


async def test_forbidden_angle_aspect_in_stored_chart_is_safe_500_with_valid_control(
    app_client, runtime: RuntimeSpy, context: ScriptedContext
) -> None:
    valid = natal_sample()
    aspect = valid.chart.aspects[0]
    bad_ref = aspect.from_point.model_copy(update={"body": "dsc"})
    bad_aspect = aspect.model_copy(update={"from_point": bad_ref})
    invalid = valid.model_copy(update={
        "chart": valid.chart.model_copy(update={"aspects": (bad_aspect,)})
    })
    chart = valid.chart
    resolved = ResolvedBirthData(
        utc_datetime=chart.datetime_utc, latitude=chart.latitude,
        longitude=chart.longitude, tz_id="Europe/Moscow",
        utc_offset_seconds=14400, canonical_place="Москва",
        time_unknown=False, birth_time_domain=None, warnings=(),
    )
    birth = BirthInput(
        birth_date=date(1985, 9, 2), birth_time=time(0, 45), place_id="524901"
    )

    def snapshot(artifact):
        stored = StoredChart(
            payload_format=1, calculation_key=artifact.calculation_key,
            calculation_version=artifact.calculation_version,
            payload=encode_chart_artifact(artifact),
        )
        state = apply_delta(
            new_session("A" * 43, now=NOW),
            StateDelta(
                birth_input=birth, birth_resolved=resolved,
                base_chart_spec=artifact.spec, base_chart_payload=stored,
            ),
            now=NOW,
        )
        return SessionSnapshot(state=state, dialog=(), chart=stored)

    invalid_snapshot = snapshot(invalid)
    valid_snapshot = snapshot(valid)
    runtime.calculation_version = valid.calculation_version
    assert isinstance(session_view(invalid_snapshot, runtime.calculation_version),
                      ChartReadySessionView)
    assert isinstance(session_view(valid_snapshot, runtime.calculation_version),
                      ChartReadySessionView)
    context.snapshots["A" * 43] = invalid_snapshot
    async with app_client(runtime) as client:
        failed = await client.get("/charts/current", headers={"Cookie": COOKIE})
        _safe_internal(failed)
        context.snapshots["A" * 43] = valid_snapshot
        control = await client.get("/charts/current", headers={"Cookie": COOKIE})
        assert control.status_code == 200
        assert control.json()["chart"]["chart_identity"] == valid.calculation_key
        assert context.load_calls == ["A" * 43, "A" * 43]
    runtime.assert_no_calculation()


@pytest.mark.parametrize("kind", ("natal", "cosmogram"))
async def test_http_build_commits_state_and_stored_chart_atomically_with_real_orchestrator(
    kind: str, app_client, sqlite_restart, utc_clock
) -> None:
    baseline = decode_chart_artifact(
        (Path(__file__).resolve().parents[1] / "golden" /
         f"chart_artifact_format_1_{kind}_1985.bin").read_bytes()
    )
    chart = baseline.chart
    resolved = ResolvedBirthData(
        utc_datetime=chart.datetime_utc,
        latitude=chart.latitude,
        longitude=chart.longitude,
        tz_id="Europe/Moscow",
        utc_offset_seconds=14400,
        canonical_place="Москва",
        time_unknown=kind == "cosmogram",
        birth_time_domain=(chart.time_uncertainty.domain
                           if chart.time_uncertainty is not None else None),
        warnings=(),
    )
    resolver = StubBirthDataResolver(resolved)
    artifacts = StubChartArtifactPort(baseline)
    async with sqlite_restart() as runtime:
        runtime.calculation_version = baseline.calculation_version
        runtime.orchestrator = ApplicationOrchestrator(
            context=runtime.context,
            handlers={BuildNatalCommand: BuildNatalHandler(
                resolver=resolver, artifacts=artifacts,
            )},
            clock=utc_clock,
        )
        session_id = "A" * 43
        created = await runtime.context.create(session_id)
        assert created.state.state_version == 0
        async with app_client(runtime) as client:
            rejected = await client.post(
                "/charts/natal", json={**VALID_BUILD, "birth_date": "1985-02-30"},
                headers={"Cookie": COOKIE},
            )
            assert rejected.status_code == 422
            assert rejected.json()["code"] == "INVALID_REQUEST"
            before = await runtime.context.load(session_id)
            assert isinstance(before, SessionSnapshot)
            assert before.state.state_version == 0
            assert before.chart is None
            assert resolver.calls == artifacts.calls == artifacts.to_stored_calls == 0
            accepted = await client.post(
                "/charts/natal",
                json={**VALID_BUILD, "birth_time": "00:45" if kind == "natal" else None},
                headers={"Cookie": COOKIE},
            )
            assert accepted.status_code == 200
            assert accepted.json()["status"] == "chart_ready"
            assert accepted.json()["chart"]["chart_identity"] == baseline.calculation_key
            assert accepted.json()["chart"]["kind"] == kind
            after = await runtime.context.load(session_id)
            assert isinstance(after, SessionSnapshot)
            assert after.state.state_version == 1
            assert after.state.base_chart is not None
            assert after.chart is not None
            assert decode_chart_artifact(after.chart.payload) == baseline
            assert after.chart.calculation_key == baseline.calculation_key
            assert resolver.calls == artifacts.calls == artifacts.to_stored_calls == 1
