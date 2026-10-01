"""Prompt 06: matched-route validation through test-only ASGI routes."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
from typing import Any
from uuid import UUID

import httpx
import pytest
from fastapi import Request
from starlette.responses import JSONResponse

from exact_orb.http_api.app import create_app
from exact_orb.http_api.request_boundary import (
    BoundaryRejection, PreparedRequest, error_response, response_headers,
    session_cookie,
)
from tests.http_api.conftest import ForbiddenCatalog, RuntimeSpy, ScriptedContext, http_settings


pytestmark = pytest.mark.asyncio
_BUILD = b'{"birth_date":"1985-09-02","birth_time":"00:45","place_id":"524901"}'
_COOKIE = b"__Host-exact_orb_session=" + b"A" * 43
_POST_HEADERS = [(b"content-type", b"application/json"), (b"cookie", _COOKIE)]
_GUARD = 2.0  # A hang guard; ManualScheduler/Event establishes ordering.


def _sent(messages: list[dict[str, Any]]) -> tuple[int, dict[str, str], dict[str, Any]]:
    starts = [message for message in messages if message["type"] == "http.response.start"]
    assert len(starts) == 1
    headers = {key.decode("ascii").lower(): value.decode("latin1")
               for key, value in starts[0]["headers"]}
    body = b"".join(message.get("body", b"") for message in messages
                    if message["type"] == "http.response.body")
    return starts[0]["status"], headers, json.loads(body)


@pytest.fixture
def probe(utc_clock, scheduler):
    @asynccontextmanager
    async def open_probe(*, trusted_proxy_cidrs: tuple[str, ...] = (),
                         during_shutdown: bool = False):
        runtime = RuntimeSpy(ScriptedContext(utc_clock))
        app = create_app(
            settings=http_settings(trusted_proxy_cidrs=trusted_proxy_cidrs),
            runtime_factory=lambda: runtime,
            catalog_factory=ForbiddenCatalog,
            utc_clock=utc_clock,
            scheduler=scheduler,
        )
        passed: list[PreparedRequest] = []

        def route(*, body_kind="none", query_kind="none", cookie_mode="ignore"):
            async def endpoint(request: Request):
                try:
                    prepared = await app.state.request_boundary.prepare(
                        request, body_kind=body_kind, query_kind=query_kind,
                        cookie_mode=cookie_mode,
                    )
                except BoundaryRejection as rejected:
                    return error_response(rejected)
                passed.append(prepared)
                return JSONResponse(
                    {"client_ip": prepared.client_ip, "cookie_status": prepared.cookie.status},
                    headers=response_headers(prepared.request_id),
                )
            return endpoint

        app.add_api_route("/_probe/build", route(body_kind="build", cookie_mode="required"),
                          methods=["POST"], include_in_schema=False)
        app.add_api_route("/_probe/bootstrap", route(body_kind="bootstrap", cookie_mode="optional"),
                          methods=["POST"], include_in_schema=False)
        app.add_api_route("/_probe/places", route(query_kind="places"),
                          methods=["GET"], include_in_schema=False)
        app.add_api_route("/_probe/current", route(cookie_mode="required"),
                          methods=["GET"], include_in_schema=False)

        lifespan = app.router.lifespan_context(app)
        await lifespan.__aenter__()
        shutdown = None
        try:
            if during_shutdown:
                runtime.block_close = True
                shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
                await asyncio.wait_for(runtime.close_entered.wait(), timeout=_GUARD)
            transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
            async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
                yield app, client, passed
        finally:
            if shutdown is None:
                await lifespan.__aexit__(None, None, None)
            else:
                runtime.close_release.set()
                await asyncio.wait_for(shutdown, timeout=_GUARD)

    return open_probe


async def test_matched_route_uses_server_id_and_resolves_before_boundary(probe) -> None:
    async with probe() as (app, client, passed):
        unknown = await client.post("/_probe/missing", content=b"{",
                                    headers={"Origin": "https://foreign.invalid"})
        wrong_method = await client.get("/_probe/build", headers={
            "Origin": "https://foreign.invalid"})
        head = await client.head("/_probe/build")
        options = await client.options("/_probe/build")
        assert unknown.status_code == 404
        for response in (wrong_method, head, options):
            assert response.status_code == 405
            assert response.headers["Allow"] == "POST"
        assert head.content == b""
        assert passed == []

        valid = await client.post(
            "/_probe/build", content=_BUILD,
            headers={"Content-Type": "application/json", "Cookie": _COOKIE.decode(),
                     "X-Request-ID": "client-sentinel"},
        )
        assert valid.status_code == 200
        assert valid.headers["Cache-Control"] == "no-store"
        assert UUID(valid.headers["X-Request-ID"])
        assert valid.headers["X-Request-ID"] != "client-sentinel"
        assert len(passed) == 1
        assert passed[0].body.place_id == "524901"
        assert app.state.request_boundary is not None


@pytest.mark.parametrize("case,status,code", (
    ("xff_over_origin", 400, "FORWARDED_HEADER_INVALID"),
    ("origin_over_encoding", 403, "ORIGIN_NOT_ALLOWED"),
    ("encoding_over_size", 415, "UNSUPPORTED_MEDIA_TYPE"),
    ("encoding_over_timeout", 415, "UNSUPPORTED_MEDIA_TYPE"),
    ("size_over_schema", 413, "REQUEST_TOO_LARGE"),
    ("schema_over_cookie", 422, "INVALID_REQUEST"),
))
async def test_validation_priority_rejects_before_test_component(
    case: str, status: int, code: str, probe, raw_asgi,
) -> None:
    trusted = ("10.0.0.0/8",) if case == "xff_over_origin" else ()
    async with probe(trusted_proxy_cidrs=trusted) as (app, _client, passed):
        headers = list(_POST_HEADERS)
        peer = ("10.0.0.2", 12345) if trusted else ("127.0.0.1", 12345)
        body = _BUILD
        if case == "xff_over_origin":
            headers.extend([
                (b"x-forwarded-for", b"bad-hostname"),
                (b"x-forwarded-proto", b"https"),
                (b"origin", b"https://foreign.invalid"),
            ])
        elif case == "origin_over_encoding":
            headers.extend([
                (b"origin", b"https://foreign.invalid"),
                (b"content-encoding", b"gzip"),
            ])
        elif case in {"encoding_over_size", "encoding_over_timeout"}:
            headers.append((b"content-encoding", b"identity"))
            body = b"{" * 16385 if case == "encoding_over_size" else b"{"
        elif case == "size_over_schema":
            body = b"{" * 16385
        else:
            headers = [(b"content-type", b"application/json")]
            body = b"{"
        chunks = ([{"type": "http.request", "body": body, "more_body": True}]
                  if case == "encoding_over_timeout" else None)
        sent = await asyncio.wait_for(raw_asgi(
            app, method="POST", path="/_probe/build",
            headers=headers, body=body, peer=peer, chunks=chunks,
        ), timeout=_GUARD)
        failed_status, failed_headers, payload = _sent(sent)
        assert failed_status == status
        assert payload["code"] == code
        assert failed_headers["cache-control"] == "no-store"
        assert UUID(failed_headers["x-request-id"])
        assert passed == []

        good_headers = list(_POST_HEADERS)
        if trusted:
            good_headers.extend([
                (b"x-forwarded-for", b"198.51.100.7, 10.0.0.1"),
                (b"x-forwarded-proto", b"https"),
            ])
        control = await raw_asgi(app, method="POST", path="/_probe/build",
                                 headers=good_headers, body=_BUILD, peer=peer)
        assert _sent(control)[0] == 200
        assert len(passed) == 1


async def test_shutdown_precedes_malformed_trusted_forwarding(probe, raw_asgi) -> None:
    async with probe(trusted_proxy_cidrs=("10.0.0.0/8",),
                     during_shutdown=True) as (app, _client, passed):
        sent = await raw_asgi(
            app, method="POST", path="/_probe/bootstrap", body=b"{}",
            peer=("10.0.0.2", 12345),
            headers=[(b"content-type", b"application/json"),
                     (b"x-forwarded-for", b"bad-hostname"),
                     (b"x-forwarded-proto", b"https")],
        )
        status, headers, payload = _sent(sent)
        assert status == 503
        assert payload["code"] == "SERVICE_SHUTTING_DOWN"
        assert headers["retry-after"] == "30"
        assert passed == []


@pytest.mark.parametrize("content_type,accepted", (
    (b"application/json", True),
    (b"application/json; charset=utf-8", True),
    (b"application/json; charset=UTF-8", True),
    (b"text/plain", False),
    (b"application/json; charset=utf-16", False),
    (b"application/json; boundary=x", False),
))
async def test_post_media_type_and_charset_before_body_and_component(
    content_type: bytes, accepted: bool, probe, raw_asgi,
) -> None:
    async with probe() as (app, _client, passed):
        result = await raw_asgi(app, method="POST", path="/_probe/bootstrap",
                                body=b"{}", headers=[(b"content-type", content_type)])
        assert _sent(result)[0] == (200 if accepted else 415)
        assert len(passed) == int(accepted)
        if not accepted:
            control = await raw_asgi(
                app, method="POST", path="/_probe/bootstrap", body=b"{}",
                headers=[(b"content-type", b"application/json")],
            )
            assert _sent(control)[0] == 200
            assert len(passed) == 1


async def test_first_body_event_starts_shared_deadline_and_size_precedes_json(
    probe, raw_asgi, scheduler,
) -> None:
    async with probe() as (app, _client, passed):
        task = asyncio.create_task(raw_asgi(
            app, method="POST", path="/_probe/bootstrap",
            headers=[(b"content-type", b"application/json")],
            chunks=[{"type": "http.request", "body": b"{", "more_body": True}],
        ))
        await asyncio.wait_for(scheduler.wait_registered(5.0), timeout=_GUARD)
        await scheduler.advance(4.999)
        assert not task.done()
        await scheduler.advance(0.001)
        status, headers, payload = _sent(await asyncio.wait_for(task, timeout=_GUARD))
        assert status == 408
        assert payload["code"] == "REQUEST_TIMEOUT"
        assert payload["detail_code"] == "BODY_RECEIVE_TIMEOUT"
        assert headers["retry-after"] == "1"
        assert passed == []

        control = await raw_asgi(
            app, method="POST", path="/_probe/bootstrap",
            headers=[(b"content-type", b"application/json")], body=b"{}",
        )
        assert _sent(control)[0] == 200
        assert len(passed) == 1


async def test_body_deadline_begins_at_first_receive_event_not_request_start(
    probe, scheduler,
) -> None:
    async with probe() as (app, _client, passed):
        incoming: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        waiting = asyncio.Event()
        sent: list[dict[str, Any]] = []

        async def receive() -> dict[str, Any]:
            waiting.set()
            return await incoming.get()

        async def send(message: dict[str, Any]) -> None:
            sent.append(message)

        scope = {
            "type": "http", "asgi": {"version": "3.0"},
            "http_version": "1.1", "scheme": "https", "method": "POST",
            "path": "/_probe/bootstrap", "raw_path": b"/_probe/bootstrap",
            "query_string": b"", "root_path": "", "server": ("testserver", 443),
            "client": ("127.0.0.1", 12345),
            "headers": [(b"content-type", b"application/json")],
        }
        task = asyncio.create_task(app(scope, receive, send))
        await asyncio.wait_for(waiting.wait(), timeout=_GUARD)
        await scheduler.advance(100)
        assert not sent
        incoming.put_nowait({"type": "http.request", "body": b"{", "more_body": True})
        await asyncio.wait_for(scheduler.wait_registered(105), timeout=_GUARD)
        await scheduler.advance(5)
        await asyncio.wait_for(task, timeout=_GUARD)
        assert _sent(sent)[0] == 408
        assert passed == []


@pytest.mark.parametrize("bad_headers", (
    [(b"x-forwarded-for", b"bad-hostname"), (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1:1234"), (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"2001:db8::1%eth0"), (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1,,198.51.100.2"),
     (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1, " * 10 + b"198.51.100.2"),
     (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1")],
    [(b"x-forwarded-for", b"198.51.100.1"), (b"x-forwarded-proto", b"http")],
    [(b"x-forwarded-for", b"198.51.100.1"),
     (b"x-forwarded-for", b"198.51.100.2"),
     (b"x-forwarded-proto", b"https")],
    [(b"x-forwarded-for", b"198.51.100.1"),
     (b"x-forwarded-proto", b"https"),
     (b"x-forwarded-proto", b"https")],
))
async def test_trusted_forwarding_rejects_malformed_raw_chain_with_control(
    bad_headers, probe, raw_asgi,
) -> None:
    async with probe(trusted_proxy_cidrs=("10.0.0.0/8",)) as (app, _client, passed):
        bad = await raw_asgi(app, method="GET", path="/_probe/places",
                             query=b"query=Place", headers=bad_headers,
                             peer=("10.0.0.2", 12345))
        assert _sent(bad)[0] == 400
        assert _sent(bad)[2]["code"] == "FORWARDED_HEADER_INVALID"
        assert passed == []
        good = await raw_asgi(app, method="GET", path="/_probe/places",
                              query=b"query=Place", headers=[
                                  (b"x-forwarded-for", b"198.51.100.7, 10.0.0.1"),
                                  (b"x-forwarded-proto", b"https"),
                              ], peer=("10.0.0.2", 12345))
        assert _sent(good)[0] == 200
        assert passed[0].client_ip == "198.51.100.7"


async def test_mapped_ipv6_and_untrusted_spoof_use_canonical_peer_keys(
    probe, raw_asgi,
) -> None:
    async with probe(trusted_proxy_cidrs=("10.0.0.0/8",)) as (app, _client, passed):
        for xff, expected in (
            (b"::ffff:198.51.100.7, 10.0.0.1", "198.51.100.7"),
            (b"198.51.100.7", "198.51.100.7"),
        ):
            result = await raw_asgi(app, method="GET", path="/_probe/places",
                                    query=b"query=Place", peer=("10.0.0.2", 1),
                                    headers=[(b"x-forwarded-for", xff),
                                             (b"x-forwarded-proto", b"https")])
            assert _sent(result)[0] == 200
            assert passed[-1].client_ip == expected

        spoofed = [(b"x-forwarded-for", b"203.0.113.200"),
                   (b"x-forwarded-proto", b"http")]
        for peer in ("198.51.100.1", "198.51.100.2"):
            result = await raw_asgi(app, method="GET", path="/_probe/places",
                                    query=b"query=Place", peer=(peer, 1),
                                    headers=spoofed)
            assert _sent(result)[0] == 200
            assert passed[-1].client_ip == peer


async def test_empty_trusted_allowlist_is_direct_mode(probe, raw_asgi) -> None:
    async with probe() as (app, _client, passed):
        result = await raw_asgi(
            app, method="GET", path="/_probe/places", query=b"query=Place",
            peer=("::ffff:198.51.100.7", 1),
            headers=[(b"x-forwarded-for", b"bad-hostname"),
                     (b"x-forwarded-proto", b"http")],
        )
        assert _sent(result)[0] == 200
        assert passed[0].client_ip == "198.51.100.7"


@pytest.mark.parametrize("query,detail", (
    (b"limit=10", "QUERY_REQUIRED"),
    (b"query=Place&query=Place", "QUERY_REQUIRED"),
    (b"query=Place&limit=1&limit=2", "LIMIT_INVALID"),
    (b"query=Place&limit=010", "LIMIT_INVALID"),
    (b"query=Place&extra=1", None),
    (b"query=" + b"%D0%96" * 513, "QUERY_TOO_LONG"),
))
async def test_place_query_grammar_blocks_before_test_component(
    query: bytes, detail: str | None, probe, raw_asgi,
) -> None:
    async with probe() as (app, _client, passed):
        bad = await raw_asgi(app, method="GET", path="/_probe/places", query=query)
        assert _sent(bad)[0] == 422
        assert _sent(bad)[2]["detail_code"] == detail
        assert passed == []
        good = await raw_asgi(app, method="GET", path="/_probe/places",
                              query=b"query=Place&limit=20")
        assert _sent(good)[0] == 200
        assert passed[0].query.limit == 20


@pytest.mark.parametrize("bad_body,field", (
    (b"{", "request.body"),
    (b"[]", "request.body"),
    (b"[" * 1100 + b"]" * 1100, "request.body"),
    (b'{"birth_date":"1990-02-30","birth_time":null,"place_id":"1"}', "birth.date"),
    (b'{"birth_date":"1985-09-02","birth_time":true,"place_id":"1"}', "birth.time"),
    (b'{"birth_date":"1985-09-02","birth_time":null,"place_id":[]}', "birth.place"),
    (b'{"birth_date":"1985-09-02","birth_time":null,"place_id":"1","state_version":0}',
     "request.state_version"),
))
async def test_build_schema_rejects_before_cookie_with_positive_control(
    bad_body: bytes, field: str, probe, raw_asgi,
) -> None:
    async with probe() as (app, _client, passed):
        bad = await raw_asgi(app, method="POST", path="/_probe/build", body=bad_body,
                             headers=[(b"content-type", b"application/json")])
        status, _, payload = _sent(bad)
        assert status == 422
        assert field in {issue["field"] for issue in payload["issues"]}
        assert passed == []
        missing_cookie = await raw_asgi(
            app, method="POST", path="/_probe/build", body=_BUILD,
            headers=[(b"content-type", b"application/json")],
        )
        assert _sent(missing_cookie)[0] == 409
        control = await raw_asgi(app, method="POST", path="/_probe/build",
                                 body=_BUILD, headers=_POST_HEADERS)
        assert _sent(control)[0] == 200
        assert len(passed) == 1


async def test_duplicate_cookie_is_seen_across_raw_fields_after_schema(
    probe, raw_asgi,
) -> None:
    async with probe() as (app, _client, passed):
        duplicate = await raw_asgi(app, method="POST", path="/_probe/build",
                                   body=_BUILD, headers=[
                                       (b"content-type", b"application/json"),
                                       (b"cookie", _COOKIE), (b"cookie", _COOKIE),
                                   ])
        assert _sent(duplicate)[0] == 409
        assert _sent(duplicate)[2]["code"] == "SESSION_REQUIRED"
        assert passed == []
        valid = await raw_asgi(app, method="POST", path="/_probe/build",
                               body=_BUILD, headers=_POST_HEADERS)
        assert _sent(valid)[0] == 200
        assert len(passed) == 1
        assert session_cookie({"headers": [(b"cookie", _COOKIE),
                                            (b"cookie", _COOKIE)]}).status == "duplicate"


async def test_health_ignores_origin_while_business_get_rejects_it(probe) -> None:
    async with probe() as (_app, client, passed):
        headers = {"Origin": "https://foreign.invalid"}
        denied = await client.get("/_probe/places?query=Place", headers=headers)
        assert denied.status_code == 403
        assert denied.json()["code"] == "ORIGIN_NOT_ALLOWED"
        assert (await client.get("/health/live", headers=headers)).status_code == 200
        assert (await client.head("/health/ready", headers=headers)).status_code == 200
        assert passed == []
        control = await client.get("/_probe/places?query=Place")
        assert control.status_code == 200
        assert len(passed) == 1
