"""T-18/22/30: real HTTP -> application -> resolver/engine/cache/session path."""
import logging

import pytest

from exact_orb.calculation.codec import decode_chart_artifact
from exact_orb.http_api.dto import BuildNatalRequestDTO
from exact_orb.session.persistence import SessionSnapshot
from tests.fixtures.application import application_test_stand
from tests.http_api.conftest import app_client, scheduler, utc_clock, RuntimeSpy
from tests.http_api.shared import VALID_BUILD, issued_cookie

HEADERS = {"Origin": "https://testserver"}


@pytest.mark.req("REQ-UI-03")
@pytest.mark.parametrize("extra", [None, "acknowledged", "consent_id", "terms_version"])
async def test_validation_before_cookie(extra, app_client, utc_clock):
    # Given подготовлен прямой публичный HTTP-запрос без cookie
    with application_test_stand(clock=utc_clock) as stand:
        runtime = RuntimeSpy(stand.context)
        runtime.orchestrator = stand.orchestrator
        payload = {**VALID_BUILD, "birth_time": "24:00"} if extra is None else {**VALID_BUILD, extra: True}
        async with app_client(runtime) as client:
            # When сервер отвергает ввод по публичному контракту
            invalid = await client.post("/charts/natal", json=payload, headers=HEADERS)
            valid = await client.post("/charts/natal", json=VALID_BUILD, headers=HEADERS)
            # Then невалидный body без cookie даёт 422 INVALID_REQUEST, а не 409
            assert invalid.status_code == 422
            assert invalid.json()["code"] == "INVALID_REQUEST"
            assert valid.status_code == 409  # Positive control: schema passed, cookie is now required.
            assert valid.json()["code"] == "SESSION_REQUIRED"


def _keys(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(_keys(v) for v in value.values()), set())
    if isinstance(value, (list, tuple)):
        return set().union(*(_keys(v) for v in value), set())
    return set()


@pytest.mark.req("REQ-UI-03", "REQ-TERMS-05", "REQ-TERMS-07")
async def test_no_consent_persistence_and_build_trace(app_client, utc_clock, caplog):
    # Given захват журнала подключён до действия и business-запросы отделены baseline
    caplog.set_level(logging.INFO, logger="exact_orb")
    with application_test_stand(clock=utc_clock) as stand:
        runtime = RuntimeSpy(stand.context)
        runtime.orchestrator = stand.orchestrator
        async with app_client(runtime) as client:
            boot = await client.post("/session/bootstrap", json={}, headers=HEADERS)
            assert boot.status_code == 200
            session_id = issued_cookie(boot)
            before = await stand.context.load(session_id)
            assert isinstance(before, SessionSnapshot) and before.chart is None
            caplog.clear()
            # When пользователь читает условия и затем отдельно явно строит карту
            page = await client.get("/")
            assert page.status_code == 200 and 'id="terms-content"' in page.text
            assert not any("http_message" in r.message or "component_message" in r.message for r in caplog.records)
            result = await client.post("/charts/natal", json=VALID_BUILD, headers=HEADERS)
            assert result.status_code == 200, result.text
            assert result.json()["status"] == "chart_ready"
            request_id = result.headers["X-Request-ID"]
            build_records = [r.message for r in caplog.records if f"request_id={request_id}" in r.message]
            # Then журнал показывает фактическую передачу управления построения с действующей корреляцией
            assert all(f"run_id={request_id}" in text for text in build_records if "http_message" in text)
            messages = [text for text in build_records if "http_message" in text]
            for peer in ["AdmissionControl", "ApplicationOrchestrator"]:
                calls = [i for i, text in enumerate(messages) if f"peer={peer} " in text and "direction=send " in text]
                returns = [i for i, text in enumerate(messages) if f"peer={peer} " in text and "direction=receive " in text]
                assert calls and returns and calls[0] < returns[0], messages
            assert sum("http_request_finished" in text for text in build_records) == 1
            application = [r.message for r in caplog.records if "application_message" in r.message and f"run_id={request_id}" in r.message]
            previous = -1
            for peer, operation in [("ContextService", "load"), ("BuildNatalHandler", "handle"), ("ContextService", "save")]:
                sent = next(i for i, text in enumerate(application) if f"peer={peer} operation={operation} " in text and "direction=send " in text)
                received = next(i for i, text in enumerate(application) if f"peer={peer} operation={operation} " in text and "direction=receive " in text)
                assert previous < sent < received, application
                previous = received
            current = await client.get("/charts/current")
            assert current.status_code == 200
            assert current.json()["chart"]["chart_identity"] == result.json()["chart"]["chart_identity"]
            current_id = current.headers["X-Request-ID"]
            assert current_id != request_id
            assert any(f"request_id={current_id}" in r.message and "http_message" in r.message for r in caplog.records)
            # And сохраняются только нормативные данные построения без записи подтверждения ознакомления
            after = await stand.context.load(session_id)
            assert isinstance(after, SessionSnapshot) and after.chart is not None
            artifact = decode_chart_artifact(after.chart.payload)
            assert after.state.state_version > before.state.state_version
            assert after.state.birth_input.place_id == VALID_BUILD["place_id"]
            assert artifact.chart.bodies and artifact.spec
            keys = _keys(after.state.model_dump(mode="json")) | _keys(artifact.model_dump(mode="json"))
            assert not keys & {"acknowledged", "checkbox", "consent_id", "consent_timestamp", "terms_version", "account"}
            assert set(BuildNatalRequestDTO.model_fields) == {"birth_date", "birth_time", "place_id"}
            assert not any("consent_record" in r.message or "terms_acknowledged" in r.message for r in caplog.records)
