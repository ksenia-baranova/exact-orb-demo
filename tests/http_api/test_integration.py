"""Final HTTP schema, coordination events, and local composition evidence."""

from __future__ import annotations

from dataclasses import replace
import logging
import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest
from pydantic import ValidationError

from exact_orb import http_server
from exact_orb.http_api.dto import BuildNatalRequestDTO
from exact_orb.http_api.request_boundary import BoundaryRejection, _build_body
from tests.http_api.admission_cases import SmallLimiterPolicy, WindowLimit
from tests.http_api.conftest import RuntimeSpy, ScriptedContext
from tests.http_api.shared import ScriptedCatalog


LOCAL_ENV = {
    "EXACT_ORB_HTTP_ORIGIN": "https://exact-orb.localhost",
    "EXACT_ORB_PLACES_DB": "unused-places.sqlite",
    "EXACT_ORB_SESSION_DB": "unused-sessions.sqlite3",
    "EXACT_ORB_EPHEMERIS_PATH": "ephe",
    "EXACT_ORB_SELENA_METHOD": "true_perigee",
}


def test_local_logging_config_records_package_info_and_debug_payload(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    config = repo / "docs/runbooks/http_api_local_logging.json"
    (tmp_path / "logs/http-api").mkdir(parents=True)
    source = """
import json
import logging
import logging.config
from pathlib import Path
import sys
from exact_orb.http_api.operation_logging import request_started, message

logging.config.dictConfig(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
request_started('request-1', 'GET', '/places', run_id=None)
message('request-1', direction='send', peer='PlaceSearch', operation='search', message_type='Call')
logging.getLogger('exact_orb.application.handlers.build_natal').info('public_component_transition')
logging.getLogger('exact_orb.application.handlers.build_natal').debug('private_birth_payload')
logging.getLogger('exact_orb.http_api').info(
    'http_request_finished request_id=request-1 outcome=success status=200')
logging.getLogger('exact_orb.http_api').info(
    'http_shutdown_finished outcome=fail_fast active_count=1 duration_ms=30000')
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repo / "src") + os.pathsep + environment.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, "-c", source, str(config)], cwd=tmp_path,
        env=environment, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    log = (tmp_path / "logs/http-api/local.log").read_text(encoding="utf-8")
    for event in (
        "http_request_started", "http_message", "public_component_transition",
        "http_request_finished", "http_shutdown_finished outcome=fail_fast",
    ):
        assert event in log
    assert "private_birth_payload" in log


def _response_schema(operation: dict, status: int) -> dict:
    return operation["responses"][str(status)]["content"]["application/json"]["schema"]


@pytest.mark.parametrize("payload,accepted", (
    ({"birth_date": "2024-02-29", "birth_time": None, "place_id": "A"}, True),
    ({"birth_date": "2024-02-29", "birth_time": "23:59", "place_id": "A" * 128}, True),
    ({"birth_date": "2024-02-29", "birth_time": "24:00", "place_id": "A"}, False),
    ({"birth_date": "2024-02-29", "birth_time": None, "place_id": ""}, False),
    ({"birth_date": "2024-02-29", "birth_time": None, "place_id": "A" * 129}, False),
    ({"birth_date": "2024-02-29", "place_id": "A"}, False),
    ({"birth_date": "2024-02-29", "birth_time": None, "place_id": "A", "extra": 1}, False),
))
def test_openapi_build_shape_and_runtime_boundary_share_structural_grammar(
    payload: dict, accepted: bool,
) -> None:
    try:
        BuildNatalRequestDTO.model_validate(payload)
        schema_accepts = True
    except ValidationError:
        schema_accepts = False
    try:
        _build_body(payload)
        runtime_accepts = True
    except BoundaryRejection:
        runtime_accepts = False
    assert schema_accepts is runtime_accepts is accepted


def test_calendar_reality_is_runtime_validation_beyond_openapi_shape() -> None:
    payload = {"birth_date": "2026-02-31", "birth_time": None, "place_id": "A"}
    assert BuildNatalRequestDTO.model_validate(payload).birth_date == "2026-02-31"
    with pytest.raises(BoundaryRejection):
        _build_body(payload)


def test_openapi_exact_public_shapes_and_response_variants() -> None:
    app = http_server.create_local_app(LOCAL_ENV)
    schema = app.openapi()
    paths = schema["paths"]
    assert {path: set(methods) for path, methods in paths.items()} == {
        "/session/bootstrap": {"post"},
        "/charts/current": {"get"},
        "/places": {"get"},
        "/charts/natal": {"post"},
    }
    expected_responses = {
        "/session/bootstrap": {200, 400, 403, 408, 413, 415, 422, 429, 500, 503},
        "/charts/current": {200, 400, 403, 409, 422, 500, 503},
        "/places": {200, 400, 403, 422, 429, 500, 503},
        "/charts/natal": {200, 400, 403, 408, 409, 413, 415, 422, 429, 500, 503, 504},
    }
    for path, expected in expected_responses.items():
        operation = next(iter(paths[path].values()))
        assert set(map(int, operation["responses"])) == expected
        for status in expected - {200}:
            assert _response_schema(operation, status) == {
                "$ref": "#/components/schemas/ErrorDTO",
            }

    assert _response_schema(paths["/session/bootstrap"]["post"], 200) == {
        "$ref": "#/components/schemas/SessionBootstrapDTO",
    }
    assert _response_schema(paths["/places"]["get"], 200) == {
        "$ref": "#/components/schemas/PlaceSuggestionsDTO",
    }
    for path, method, names in (
        ("/charts/current", "get", {"SessionEmptyDTO", "SessionReadyDTO", "SessionUnavailableDTO"}),
        ("/charts/natal", "post", {"BuildReadyDTO", "BuildAlreadyAppliedDTO"}),
    ):
        variants = _response_schema(paths[path][method], 200)["anyOf"]
        assert {entry["$ref"].rsplit("/", 1)[-1] for entry in variants} == names

    components = schema["components"]["schemas"]
    for name in (
        "ErrorDTO", "IssueDTO", "SessionBootstrapDTO", "SessionEmptyDTO",
        "SessionReadyDTO", "SessionUnavailableDTO", "BuildReadyDTO",
        "BuildAlreadyAppliedDTO", "BirthViewDTO", "BirthPlaceDTO",
        "BirthWarningDTO", "ChartDTO", "PointDTO", "AnglesDTO", "AngleDTO",
        "HouseDTO", "AspectDTO", "PlaceSuggestionsDTO", "PlaceSuggestionDTO",
    ):
        assert components[name]["additionalProperties"] is False
    assert set(components["ChartDTO"]["properties"]) == {
        "chart_identity", "kind", "zodiac", "house_system", "points",
        "angles", "houses", "aspects",
    }
    assert set(components["AngleDTO"]["properties"]) == {
        "longitude", "sign", "degree", "minute",
    }
    assert {"from", "to"} <= set(components["AspectDTO"]["properties"])
    assert set(components["BirthViewDTO"]["properties"]) == {
        "birth_date", "birth_time", "place", "tz_id", "utc_offset_seconds",
        "time_unknown", "warnings",
    }
    bootstrap_body = paths["/session/bootstrap"]["post"]["requestBody"]
    build_body = paths["/charts/natal"]["post"]["requestBody"]
    assert bootstrap_body["required"] is build_body["required"] is True
    assert bootstrap_body["content"]["application/json"]["schema"]["additionalProperties"] is False
    build_shape = build_body["content"]["application/json"]["schema"]
    assert build_shape["additionalProperties"] is False
    assert set(build_shape["required"]) == {"birth_date", "birth_time", "place_id"}
    assert {item["name"] for item in paths["/places"]["get"]["parameters"]} == {
        "query", "limit",
    }


@pytest.mark.asyncio
async def test_local_factory_passes_one_open_catalog_to_runtime_and_route(
    monkeypatch, utc_clock
) -> None:
    inner_catalog = ScriptedCatalog()
    runtime = RuntimeSpy(ScriptedContext(utc_clock))
    received: list[object] = []

    async def open_catalog(_path, *, executor):
        assert executor is not None
        return inner_catalog

    async def build_runtime(*, settings, places, clock):
        received.append(places)
        assert settings.session_db_path.name == "unused-sessions.sqlite3"
        assert clock().tzinfo is not None
        return runtime

    monkeypatch.setattr(http_server.SqlitePlaceCatalog, "open", open_catalog)
    monkeypatch.setattr(http_server, "build_application_runtime", build_runtime)
    app = http_server.create_local_app(LOCAL_ENV)
    async with app.router.lifespan_context(app):
        assert received == [app.state.catalog]
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="https://exact-orb.localhost",
        ) as client:
            response = await client.get(
                "/places", params={"query": "Москва"},
                headers={"X-Forwarded-For": "198.51.100.7",
                         "X-Forwarded-Proto": "https"},
            )
            assert response.status_code == 200
            assert inner_catalog.calls == [("Москва", 10)]
    assert runtime.closed and inner_catalog.closed


@pytest.mark.asyncio
async def test_admission_rejection_event_is_correlated_and_payload_free(
    app_client, runtime: RuntimeSpy, caplog
) -> None:
    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    catalog = ScriptedCatalog()
    policy = replace(SmallLimiterPolicy(), place_search_ip=WindowLimit(1, 7))
    async with app_client(runtime, catalog=catalog, limiter_policy=policy) as client:
        first = await client.get("/places", params={"query": "SecretPlaceXYZ"})
        rejected = await client.get("/places", params={"query": "SecretPlaceXYZ"})
        assert first.status_code == 200
        assert rejected.status_code == 429
        assert catalog.calls == [("SecretPlaceXYZ", 10)]
    messages = [record.getMessage() for record in caplog.records
                if record.name.startswith("exact_orb.http_api")]
    events = [message for message in messages
              if message.startswith("http_admission_rejected ")]
    assert len(events) == 1
    event = events[0]
    assert f"request_id={rejected.headers['X-Request-ID']}" in event
    assert "class=rate" in event and "scope=ip" in event
    assert "code=PLACE_SEARCH_RATE_LIMITED" in event
    assert "retry_after=7" in event
    assert "SecretPlaceXYZ" not in "\n".join(messages)
